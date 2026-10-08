from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path


def _write_index(path: Path, **overrides) -> None:
    payload = {
        "meta": {"source_path": "kept"},
        "unique": {"cild": "cīld"},
        "ambiguous": {"ac": ["ac", "āc"]},
        "ambiguous_completed": ["ac"],
        "ambiguous_metadata": {},
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def index_path(temp_dir) -> Path:
    path = temp_dir / "index.json"
    _write_index(path)
    return path


def _run(runner, *args: str):
    return runner.invoke(cli, ["diacritic", *args])


def test_add_stores_pair_and_updates_counts(runner, index_path):
    result = _run(runner, "add", "hlāford", "hlāford", "--index-path", str(index_path))

    assert result.exit_code == 0, result.output
    payload = _read(index_path)
    assert payload["unique"]["hlaford"] == "hlāford"
    assert payload["unique"]["cild"] == "cīld"
    assert payload["meta"]["unique_count"] == 2
    assert payload["meta"]["ambiguous_count"] == 1
    assert payload["meta"]["source_path"] == "kept"
    assert payload["ambiguous_completed"] == ["ac"]


def test_add_normalizes_the_key_but_stores_the_form_as_given(runner, index_path):
    result = _run(runner, "add", "Ðæt-Sum", "ðæt-sum", "--index-path", str(index_path))

    assert result.exit_code == 0, result.output
    assert _read(index_path)["unique"]["þætsum"] == "ðæt-sum"


def test_add_refuses_existing_key_without_force(runner, index_path):
    result = _run(runner, "add", "cild", "ċild", "--index-path", str(index_path))

    assert result.exit_code != 0
    assert "already exists" in result.output
    assert _read(index_path)["unique"]["cild"] == "cīld"


def test_add_force_overwrites_existing_key(runner, index_path):
    result = _run(
        runner, "add", "cild", "ċild", "--force", "--index-path", str(index_path)
    )

    assert result.exit_code == 0, result.output
    assert _read(index_path)["unique"]["cild"] == "ċild"


def test_add_refuses_ambiguous_key_even_with_force(runner, index_path):
    result = _run(runner, "add", "ac", "āc", "--force", "--index-path", str(index_path))

    assert result.exit_code != 0
    assert "ambiguous" in result.output
    payload = _read(index_path)
    assert "ac" not in payload["unique"]
    assert payload["ambiguous"]["ac"] == ["ac", "āc"]


def test_add_rejects_key_that_normalizes_to_empty(runner, index_path):
    result = _run(runner, "add", "   ", "x", "--index-path", str(index_path))

    assert result.exit_code != 0
    assert "empty" in result.output
    assert _read(index_path)["unique"] == {"cild": "cīld"}


def test_add_reports_missing_index_file(runner, temp_dir):
    result = _run(
        runner, "add", "a", "ā", "--index-path", str(temp_dir / "missing.json")
    )

    assert result.exit_code != 0
    assert "not found" in result.output


def test_add_reports_invalid_index_payload(runner, temp_dir):
    bad = temp_dir / "bad.json"
    bad.write_text(json.dumps({"unique": "nope"}), encoding="utf-8")

    result = _run(runner, "add", "a", "ā", "--index-path", str(bad))

    assert result.exit_code != 0
    assert "Invalid macron index payload" in result.output


def test_delete_with_yes_removes_pair_and_updates_counts(runner, index_path):
    result = _run(runner, "delete", "CILD", "--yes", "--index-path", str(index_path))

    assert result.exit_code == 0, result.output
    payload = _read(index_path)
    assert "cild" not in payload["unique"]
    assert payload["meta"]["unique_count"] == 0
    assert payload["ambiguous"]["ac"] == ["ac", "āc"]


def test_delete_prompts_and_cancels_by_default(runner, index_path):
    result = runner.invoke(
        cli,
        ["diacritic", "delete", "cild", "--index-path", str(index_path)],
        input="\n",
    )

    assert result.exit_code == 0, result.output
    assert "Remove pair" in result.output
    assert _read(index_path)["unique"]["cild"] == "cīld"


def test_delete_prompts_and_confirms(runner, index_path):
    result = runner.invoke(
        cli,
        ["diacritic", "delete", "cild", "--index-path", str(index_path)],
        input="y\n",
    )

    assert result.exit_code == 0, result.output
    assert "cild" not in _read(index_path)["unique"]


def test_delete_unknown_key_fails(runner, index_path):
    result = _run(runner, "delete", "nothere", "--yes", "--index-path", str(index_path))

    assert result.exit_code != 0
    assert "not found in unique list" in result.output


def test_delete_ambiguous_key_is_not_in_unique_list(runner, index_path):
    result = _run(runner, "delete", "ac", "--yes", "--index-path", str(index_path))

    assert result.exit_code != 0
    assert _read(index_path)["ambiguous"]["ac"] == ["ac", "āc"]


def test_add_mismatching_form_prompts_and_declines_by_default(runner, index_path):
    before = index_path.read_text(encoding="utf-8")

    result = runner.invoke(
        cli,
        ["diacritic", "add", "blac", "blǣc", "--index-path", str(index_path)],
        input="\n",
    )

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    assert index_path.read_text(encoding="utf-8") == before


def test_add_mismatching_form_is_stored_when_confirmed(runner, index_path):
    result = runner.invoke(
        cli,
        ["diacritic", "add", "blac", "blǣc", "--index-path", str(index_path)],
        input="y\n",
    )

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    assert _read(index_path)["unique"]["blac"] == "blǣc"


def test_add_mismatching_form_with_yes_skips_the_prompt(runner, index_path):
    result = _run(
        runner, "add", "blac", "blǣc", "--yes", "--index-path", str(index_path)
    )

    assert result.exit_code == 0, result.output
    assert "Store it anyway" not in result.output
    assert _read(index_path)["unique"]["blac"] == "blǣc"


@pytest.mark.parametrize(
    ("key", "form"),
    [
        ("þætsum", "ðæt-sum"),
        ("lac", "l\u0101\u010b"),
        ("lac", "la\u0304c"),
        ("hlaford", "Hlāford"),
    ],
)
def test_add_form_that_normalizes_to_its_key_does_not_prompt(
    runner, index_path, key, form
):
    result = _run(runner, "add", key, form, "--index-path", str(index_path))

    assert result.exit_code == 0, result.output
    assert "does not match its key" not in result.output
