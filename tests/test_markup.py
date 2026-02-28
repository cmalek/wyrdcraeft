from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.markup import (
    DEFAULT_MACRON_INDEX_PATH,
    CPalatalizer,
    DiacriticRestorer,
    GPalatalizer,
    MacronApplicator,
    normalize_old_english,
)

if TYPE_CHECKING:
    from pathlib import Path

#: Expected line number in ambiguity assertions.
EXPECTED_LINE_NUMBER = 3
#: Expected word number in ambiguity assertions.
EXPECTED_WORD_NUMBER = 5
#: Expected ambiguity word index in line 1.
EXPECTED_FIRST_LINE_WORD_NUMBER = 3


def _write_index(
    path: Path,
    *,
    unique: dict[str, str],
    ambiguous: dict[str, list[str]],
    ambiguous_metadata: dict[str, dict[str, dict[str, str]]] | None = None,
) -> None:
    payload = {
        "unique": unique,
        "ambiguous": ambiguous,
        "ambiguous_metadata": ambiguous_metadata or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_normalize_old_english_parity_rules():
    assert normalize_old_english("  Hēaþ-Þegn  ") == "heaþþegn"
    assert normalize_old_english("byð") == "byþ"
    assert normalize_old_english(None) is None


def test_g_palatalizer_handles_compounds_and_exceptions():
    palatalizer = GPalatalizer()
    assert palatalizer.palatalize("giefu-giefu") == "ġiefu-ġiefu"
    assert palatalizer.palatalize("gēar") == "gēar"
    assert palatalizer.palatalize("weg") == "weġ"


def test_c_palatalizer_core_rules_and_force_exception(tmp_path: Path):
    force_palatalize = tmp_path / "force_palatalize.txt"
    force_non_palatalize = tmp_path / "force_non_palatalize.txt"
    force_palatalize.write_text("hwelc\n", encoding="utf-8")
    force_non_palatalize.write_text("cuman\n", encoding="utf-8")

    palatalizer = CPalatalizer(
        force_palatalize_path=force_palatalize,
        force_non_palatalize_path=force_non_palatalize,
    )
    assert palatalizer.palatalize("cild") == "ċild"
    assert palatalizer.palatalize("mislic") == "misliċ"
    assert palatalizer.palatalize("rice") == "riċe"
    assert palatalizer.palatalize("hwelc") == "hwelċ"
    assert palatalizer.palatalize("cuman") == "cuman"


def test_macron_applicator_single_and_ambiguous(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={"cild": "cīld"},
        ambiguous={"wegas": ["wegas", "wēgas"]},
    )
    applicator = MacronApplicator(index_path)

    marked, ambiguity = applicator.apply("Cild", line_number=1, word_number=1)
    assert marked == "Cīld"
    assert ambiguity is None

    unchanged, ambiguity = applicator.apply("wegas", line_number=3, word_number=5)
    assert unchanged == "wegas"
    assert ambiguity is not None
    assert ambiguity.line_number == EXPECTED_LINE_NUMBER
    assert ambiguity.word_number == EXPECTED_WORD_NUMBER
    assert ambiguity.word == "wegas"
    assert ambiguity.options == ["wegas", "wēgas"]


def test_diacritic_restorer_preserves_layout_and_reports_ambiguity(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={"cild": "cīld", "rice": "rīce"},
        ambiguous={"wegas": ["wegas", "wēgas"]},
    )
    restorer = DiacriticRestorer(macron_index_path=index_path)

    source = "Cild   and wegas.\nrice\n"
    result = restorer.restore_text(source)

    assert result.marked_text == "Ċīld   and weġas.\nrīċe\n"
    assert len(result.ambiguities) == 1
    ambiguity = result.ambiguities[0]
    assert ambiguity.line_number == 1
    assert ambiguity.word_number == EXPECTED_FIRST_LINE_WORD_NUMBER
    assert ambiguity.word == "wegas"
    assert ambiguity.options == ["wegas", "wēgas"]


def test_default_macron_index_path_points_to_package_data():
    assert DEFAULT_MACRON_INDEX_PATH.as_posix().endswith(
        "wyrdcraeft/etc/diacritic/oe_bt_macron_index.json"
    )
    assert DEFAULT_MACRON_INDEX_PATH.exists()


def test_macron_applicator_loads_ambiguous_metadata(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={"cild": "cīld"},
        ambiguous={"ac": ["ac", "āc"]},
        ambiguous_metadata={
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
    )
    applicator = MacronApplicator(index_path)

    assert "ac" in applicator.index.ambiguous_metadata
    assert (
        applicator.index.ambiguous_metadata["ac"]["ac"].part_of_speech_code == "CONJ"
    )


def test_macron_applicator_rejects_invalid_pos_code_metadata(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"ac": ["ac", "āc"]},
        ambiguous_metadata={
            "ac": {
                "ac": {
                    "part_of_speech_code": "BAD",
                    "modern_english_meaning": "invalid",
                }
            }
        },
    )

    with pytest.raises(TypeError):
        MacronApplicator(index_path)
