from __future__ import annotations

import importlib
import json
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.services.bosworthtoller import BTSearchEntry

if TYPE_CHECKING:
    from pathlib import Path

cli_module = importlib.import_module("wyrdcraeft.cli.cli")


def _write_index(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture(autouse=True)
def _mock_bt_lookup(monkeypatch):
    monkeypatch.setattr(cli_module, "fetch_bt_search_entries", lambda _q: [])


def test_diacritic_disambiguate_choose_commits_selection(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="c\n2\ny\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert "ac" not in payload["ambiguous"]
    assert payload["unique"]["ac"] == "āc"


def test_diacritic_disambiguate_choose_decline_keeps_state(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="c\n1\nn\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "āc"]
    assert "ac" not in payload["unique"]


def test_diacritic_disambiguate_subcommand_q_returns_to_main_menu(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"], "adlig": ["adlig", "ādlig"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "--index-path",
            str(index_path),
        ],
        input="c\nq\ns\nq\n",
    )

    assert result.exit_code == 0
    assert "normalized form: adlig" in result.output


def test_diacritic_disambiguate_replace_commits_explicit_unique(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {
                "ac": {
                    "ac": {
                        "part_of_speech_code": "CONJ",
                        "modern_english_meaning": "but",
                    }
                }
            },
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="r\nāċ\ny\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["unique"]["ac"] == "āċ"
    assert "ac" not in payload["ambiguous"]
    assert "ac" not in payload["ambiguous_metadata"]


def test_diacritic_disambiguate_define_persists_metadata(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="d\n6\nbut\nn\n1\noak\nn\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    annotations = payload["ambiguous_metadata"]["ac"]
    assert annotations["ac"]["part_of_speech_code"] == "CONJ"
    assert annotations["ac"]["modern_english_meaning"] == "but"
    assert annotations["āc"]["part_of_speech_code"] == "N"
    assert annotations["āc"]["modern_english_meaning"] == "oak"
    assert payload["ambiguous"]["ac"] == ["ac", "āc"]


def test_diacritic_disambiguate_define_allows_multiple_senses(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="d\n6\nbut\ny\n5\nwhy\nn\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    entry = payload["ambiguous_metadata"]["ac"]["ac"]
    expected_sense_count = 2
    assert entry["part_of_speech_code"] == "CONJ"
    assert entry["modern_english_meaning"] == "but"
    assert len(entry["senses"]) == expected_sense_count
    assert entry["senses"][0]["part_of_speech_code"] == "CONJ"
    assert entry["senses"][0]["modern_english_meaning"] == "but"
    assert entry["senses"][1]["part_of_speech_code"] == "ADV"
    assert entry["senses"][1]["modern_english_meaning"] == "why"


def test_diacritic_disambiguate_define_stays_on_same_key_after_save(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"], "adlig": ["adlig", "ādlig"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "--index-path",
            str(index_path),
        ],
        input="d\n6\nbut\nn\n1\noak\nn\nc\n1\ny\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["unique"]["ac"] == "ac"
    assert "ac" not in payload["ambiguous"]
    assert "adlig" in payload["ambiguous"]


def test_diacritic_disambiguate_mark_completed_commits(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {
                "ac": {
                    "ac": {
                        "part_of_speech_code": "CONJ",
                        "modern_english_meaning": "but",
                    },
                    "āc": {
                        "part_of_speech_code": "N",
                        "modern_english_meaning": "oak",
                    },
                }
            },
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="m\ny\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "āc"]
    assert "ac" in payload["ambiguous_completed"]


def test_diacritic_disambiguate_mark_completed_requires_annotations(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {
                "ac": {
                    "ac": {
                        "part_of_speech_code": "CONJ",
                        "modern_english_meaning": "but",
                    }
                }
            },
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="m\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert "ac" not in payload.get("ambiguous_completed", [])


def test_diacritic_disambiguate_default_iteration_skips_completed(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"], "adlig": ["adlig", "ādlig"]},
            "ambiguous_completed": ["ac"],
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "--index-path",
            str(index_path),
        ],
        input="q\n",
    )

    assert result.exit_code == 0
    assert "normalized form: adlig" in result.output
    assert "normalized form: ac" not in result.output


def test_diacritic_disambiguate_add_entry_and_annotate_all_forms(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="a\nax\n2\nadded gloss\nn\n6\nbut\nn\n1\noak\nn\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "āc", "ax"]
    annotations = payload["ambiguous_metadata"]["ac"]
    assert annotations["ax"]["part_of_speech_code"] == "V"
    assert annotations["ax"]["modern_english_meaning"] == "added gloss"
    assert annotations["ac"]["part_of_speech_code"] == "CONJ"
    assert annotations["ac"]["modern_english_meaning"] == "but"
    assert annotations["āc"]["part_of_speech_code"] == "N"
    assert annotations["āc"]["modern_english_meaning"] == "oak"


def test_diacritic_disambiguate_add_stays_on_same_key_after_save(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"], "adlig": ["adlig", "ādlig"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "--index-path",
            str(index_path),
        ],
        input="a\nax\n2\nadded gloss\nn\n6\nbut\nn\n1\noak\nn\nc\n3\ny\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["unique"]["ac"] == "ax"
    assert "ac" not in payload["ambiguous"]
    assert "adlig" in payload["ambiguous"]


def test_diacritic_disambiguate_add_entry_accepts_unicode_form(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    combining_a_macron = "a\u0304"
    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input=f"a\n{combining_a_macron}\n2\nlong a\nn\n6\nbut\nn\n1\noak\nn\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "āc", "ā"]
    assert (
        payload["ambiguous_metadata"]["ac"]["ā"]["modern_english_meaning"] == "long a"
    )


def test_diacritic_disambiguate_add_entry_accepts_option_escape_sequence(
    runner, temp_dir
):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"aflian": ["aflian", "āflian"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "aflian",
            "--index-path",
            str(index_path),
        ],
        input="a\n^[aa-flian\n2\nto afflict\nn\n1\naflian\nn\n2\nafflict\nn\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["aflian"] == ["aflian", "āflian", "ā-flian"]
    assert (
        payload["ambiguous_metadata"]["aflian"]["ā-flian"]["modern_english_meaning"]
        == "to afflict"
    )


def test_diacritic_disambiguate_delete_entry_with_confirmation(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc", "ax"]},
            "ambiguous_metadata": {
                "ac": {
                    "ac": {
                        "part_of_speech_code": "CONJ",
                        "modern_english_meaning": "but",
                    },
                    "āc": {
                        "part_of_speech_code": "N",
                        "modern_english_meaning": "oak",
                    },
                    "ax": {
                        "part_of_speech_code": "V",
                        "modern_english_meaning": "add",
                    },
                }
            },
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="x\n2\ny\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "ax"]
    annotations = payload["ambiguous_metadata"]["ac"]
    assert "āc" not in annotations
    assert annotations["ac"]["modern_english_meaning"] == "but"
    assert annotations["ax"]["modern_english_meaning"] == "add"


def test_diacritic_disambiguate_delete_stays_on_same_key_after_save(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {
                "ac": ["ac", "āc", "ax"],
                "adlig": ["adlig", "ādlig"],
            },
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "--index-path",
            str(index_path),
        ],
        input="x\n3\ny\nc\n2\ny\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["unique"]["ac"] == "āc"
    assert "ac" not in payload["ambiguous"]
    assert "adlig" in payload["ambiguous"]


def test_diacritic_disambiguate_delete_entry_requires_two_or_more(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="x\nq\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac"]


def test_diacritic_disambiguate_skip_keeps_state(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="s\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "āc"]
    assert payload["unique"] == {}
    assert payload["ambiguous_metadata"] == {}


def test_diacritic_disambiguate_layout_shows_existing_annotations(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {
                "ac": {
                    "ac": {
                        "part_of_speech_code": "CONJ",
                        "modern_english_meaning": "but",
                    },
                    "āc": {
                        "part_of_speech_code": "N",
                        "modern_english_meaning": "oak tree",
                    },
                }
            },
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="s\n",
    )

    assert result.exit_code == 0
    assert "CONJ" in result.output
    assert "but" in result.output
    assert "oak tree" in result.output


def test_diacritic_disambiguate_layout_shows_bt_assist_content(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )
    monkeypatch.setattr(
        cli_module,
        "fetch_bt_search_entries",
        lambda query: [
            BTSearchEntry(
                headword_raw="AC",
                headword_macronized="AC",
                pos="con.",
                meanings=["but", "for"],
                entry_url="https://bosworthtoller.com/134",
                order_index=0,
            )
        ]
        if query == "ac"
        else [
            BTSearchEntry(
                headword_raw="ÁC",
                headword_macronized="ĀC",
                pos="n.",
                meanings=["oak"],
                entry_url="https://bosworthtoller.com/137",
                order_index=0,
            )
        ],
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="s\n",
    )

    assert result.exit_code == 0
    assert "Bosworth-Toller Assist" in result.output
    assert "AC" in result.output
    assert "con." in result.output
    assert "but" in result.output
    assert "for" in result.output
    assert "ĀC" in result.output
    assert "oak" in result.output


def test_diacritic_disambiguate_looks_up_normalized_and_attested_forms(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )
    queries: list[str] = []

    def _capture_queries(query: str) -> list[BTSearchEntry]:
        queries.append(query)
        return []

    monkeypatch.setattr(
        cli_module,
        "fetch_bt_search_entries",
        _capture_queries,
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="s\n",
    )

    assert result.exit_code == 0
    assert queries == ["ac", "āc"]


def test_diacritic_disambiguate_bt_fetch_failure_is_non_blocking(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )

    def _raise_lookup(_query: str):
        error_message = "network unavailable"
        raise RuntimeError(error_message)

    monkeypatch.setattr(
        cli_module,
        "fetch_bt_search_entries",
        _raise_lookup,
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
        input="s\n",
    )

    assert result.exit_code == 0
    assert "lookup unavailable" in result.output
    assert "'ac'" in result.output
    assert "'āc'" in result.output


def test_diacritic_disambiguate_close_exits_cleanly(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"], "adlig": ["adlig", "ādlig"]},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        ["diacritic", "disambiguate", "--index-path", str(index_path)],
        input="q\n",
    )

    assert result.exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert "ac" in payload["ambiguous"]
    assert "adlig" in payload["ambiguous"]


def test_diacritic_disambiguate_single_key_not_ambiguous_errors(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 1, "ambiguous_count": 0},
            "unique": {"ac": "āc"},
            "ambiguous": {},
            "ambiguous_metadata": {},
        },
    )

    result = runner.invoke(
        cli,
        [
            "diacritic",
            "disambiguate",
            "ac",
            "--index-path",
            str(index_path),
        ],
    )

    assert result.exit_code != 0
    assert "is not present in ambiguous entries" in result.output
