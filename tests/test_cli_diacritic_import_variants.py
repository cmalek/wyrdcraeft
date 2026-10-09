from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

import wyrdcraeft.cli.diacritic as diacritic_module
from wyrdcraeft.cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path

BT_LINES = [
    "tilung@<B>tilung,</B> teolung, tiolung; <I>f.</I> striving.@tilung",
    "wege@<B>wege,</B> wēg; <I>m.</I> a way.@wege",
]


@pytest.fixture
def files(temp_dir: Path) -> dict[str, Path]:
    source = temp_dir / "oe_bt.txt"
    source.write_text("\n".join(BT_LINES) + "\n", encoding="utf-8")
    index = temp_dir / "index.json"
    index.write_text(
        json.dumps(
            {
                "meta": {"source_path": "kept"},
                "unique": {"weg": "weg"},
                "ambiguous": {},
                "ambiguous_completed": [],
                "ambiguous_metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"source": source, "index": index, "report": temp_dir / "report.json"}


def _run(runner, files, monkeypatch, *extra: str):
    # print_info writes to a stderr console CliRunner does not capture.
    messages: list[str] = []
    monkeypatch.setattr(diacritic_module, "print_info", messages.append)
    result = runner.invoke(
        cli,
        [
            "diacritic",
            "import-variants",
            "--source-path",
            str(files["source"]),
            "--index-path",
            str(files["index"]),
            "--report-output",
            str(files["report"]),
            *extra,
        ],
    )
    return result, messages


def test_dry_run_writes_the_report_but_not_the_index(runner, files, monkeypatch):
    before = files["index"].read_text(encoding="utf-8")

    result, messages = _run(runner, files, monkeypatch)

    assert result.exit_code == 0, result.output
    assert files["index"].read_text(encoding="utf-8") == before
    report = json.loads(files["report"].read_text(encoding="utf-8"))
    assert report["additions"] == {"teolung": "teolung", "tiolung": "tiolung"}
    assert [c["reason"] for c in report["collisions"]] == ["more_marks"]
    assert any(m.startswith("Would add 2") for m in messages)


def test_apply_adds_new_keys_and_keeps_everything_else(runner, files, monkeypatch):
    result, messages = _run(runner, files, monkeypatch, "--apply")

    assert result.exit_code == 0, result.output
    written = json.loads(files["index"].read_text(encoding="utf-8"))
    assert written["unique"] == {
        "weg": "weg",
        "teolung": "teolung",
        "tiolung": "tiolung",
    }
    assert written["meta"]["source_path"] == "kept"
    assert written["meta"]["unique_count"] == 3
    assert any(m.startswith("Added 2") for m in messages)


def test_apply_twice_adds_nothing_the_second_time(runner, files, monkeypatch):
    _run(runner, files, monkeypatch, "--apply")
    first = files["index"].read_text(encoding="utf-8")

    result, messages = _run(runner, files, monkeypatch, "--apply")

    assert result.exit_code == 0, result.output
    assert files["index"].read_text(encoding="utf-8") == first
    assert any(m.startswith("Added 0") for m in messages)


def test_missing_source_is_a_clean_error(runner, files, monkeypatch):
    files["source"].unlink()

    result, _ = _run(runner, files, monkeypatch)

    assert result.exit_code != 0
    assert "Traceback" not in result.output


def test_missing_index_is_a_clean_error(runner, files, monkeypatch):
    files["index"].unlink()

    result, _ = _run(runner, files, monkeypatch)

    assert result.exit_code == 1
    assert "Macron index file not found" in result.output
