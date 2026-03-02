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


def test_c_palatalizer_medial_c_before_e_ae_y_not_palatalized():
    """Medial c before e/æ/y (non-i) does not palatalize (Rule B)."""
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("specan") == "specan"
    assert palatalizer.palatalize("weorc") == "weorc"


def test_c_palatalizer_wicu_stays_velar():
    """C after i/ī does not palatalize when a back vowel follows (Rule D)."""
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("wicu") == "wicu"


def test_c_palatalizer_c_before_i_palatalizes():
    """C before i/ī in any position palatalizes (Rule C)."""
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("cild") == "ċild"
    assert palatalizer.palatalize("micel") == "miċel"
    assert palatalizer.palatalize("cidan") == "ċidan"


def test_c_palatalizer_blocklist_i_mutation_exceptions():
    """Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)."""
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("cyning") == "cyning"
    assert palatalizer.palatalize("cemban") == "cemban"
    assert palatalizer.palatalize("cynn") == "cynn"


def test_g_palatalizer_ges_exception():
    """gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar."""
    palatalizer = GPalatalizer()
    assert palatalizer.palatalize("gēs") == "gēs"


def test_c_palatalizer_force_palatalize_canonical_forms():
    """Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc."""
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("hwelc") == "hwelċ"
    assert palatalizer.palatalize("hwilc") == "hwilċ"
    assert palatalizer.palatalize("swelc") == "swelċ"
    assert palatalizer.palatalize("swilc") == "swilċ"
    assert palatalizer.palatalize("swylc") == "swylċ"
    assert palatalizer.palatalize("ǣlc") == "ǣlċ"
    assert palatalizer.palatalize("þylc") == "þylċ"


def test_c_palatalizer_pre_iumlaut_cyning_unchanged():
    """Cyning (c + y from u) remains non-palatalized; blocklist and only-back."""
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("cyning") == "cyning"


def test_macron_applicator_single_and_ambiguous(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={"cild": "cīld"},
        ambiguous={"wegas": ["wegas", "wēgas"]},
    )
    applicator = MacronApplicator(index_path)

    marked, ambiguity, is_unknown = applicator.apply(
        "Cild", line_number=1, word_number=1
    )
    assert marked == "Cīld"
    assert ambiguity is None
    assert is_unknown is False

    unchanged, ambiguity, is_unknown = applicator.apply(
        "wegas", line_number=3, word_number=5
    )
    assert unchanged == "wegas"
    assert ambiguity is not None
    assert is_unknown is False
    assert ambiguity.line_number == EXPECTED_LINE_NUMBER
    assert ambiguity.word_number == EXPECTED_WORD_NUMBER
    assert ambiguity.word == "wegas"
    assert [o.form for o in ambiguity.options] == ["wegas", "wēgas"]

    # Token not in index is returned unchanged with is_unknown=True
    unknown_word, no_ambiguity, is_unknown = applicator.apply(
        "xyzword", line_number=2, word_number=1
    )
    assert unknown_word == "xyzword"
    assert no_ambiguity is None
    assert is_unknown is True


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
    assert [o.form for o in ambiguity.options] == ["wegas", "wēgas"]
    # "and" is not in the index, so it is reported as unknown
    assert len(result.unknowns) == 1
    assert result.unknowns[0].word == "and"
    assert result.unknowns[0].line_number == 1


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

    _, ambiguity, is_unknown = applicator.apply("ac", line_number=1, word_number=1)
    assert is_unknown is False
    assert ambiguity is not None
    expected_option_count = 2
    assert len(ambiguity.options) == expected_option_count
    assert ambiguity.options[0].form == "ac"
    assert ambiguity.options[0].part_of_speech == "conjunction"
    assert ambiguity.options[0].definitions == ["but"]
    assert ambiguity.options[1].form == "āc"
    assert ambiguity.options[1].part_of_speech == "noun"
    assert ambiguity.options[1].definitions == ["oak"]


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
