from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.markup import (
    DEFAULT_G_FRONTAL_PATH,
    DEFAULT_MACRON_INDEX_PATH,
    CPalatalizer,
    DiacriticRestorer,
    DiacriticTransfer,
    GPalatalizer,
    MacronApplicator,
    _load_folded_word_list,
    normalize_morphology_title,
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


def test_normalize_morphology_title_preserves_macrons_and_dots():
    assert normalize_morphology_title("  Abbōd-hād  ") == "abbōdhād"
    assert normalize_morphology_title("byð") == "byþ"
    assert normalize_morphology_title("ċild") == "ċild"
    assert normalize_morphology_title(None) == ""
    assert normalize_old_english("abbōd") == "abbod"
    assert normalize_morphology_title("abbōd") == "abbōd"
    assert normalize_morphology_title("beōn") == "bēon"
    assert normalize_morphology_title("bēon") == "bēon"
    assert normalize_morphology_title("æt-beōn") == "ætbēon"


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

    marked, ambiguity, is_unknown, unaligned = applicator.apply(
        "Cild", line_number=1, word_number=1
    )
    assert marked == "Cīld"
    assert unaligned is None
    assert ambiguity is None
    assert is_unknown is False

    unchanged, ambiguity, is_unknown, _ = applicator.apply(
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
    unknown_word, no_ambiguity, is_unknown, _ = applicator.apply(
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

    assert result.marked_text == "Ċīld   and wegas.\nrīċe\n"
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
    assert applicator.index.ambiguous_metadata["ac"]["ac"].part_of_speech_code == "CONJ"

    _, ambiguity, is_unknown, _ = applicator.apply("ac", line_number=1, word_number=1)
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


def test_diacritic_transfer_preserves_source_letters_hyphens_and_case():
    t = DiacriticTransfer.transfer
    # eth/thorn stay as written, in both directions
    assert t("ðā", "þā") == "ðā"
    assert t("Þa", "ðā") == "Þā"
    # no hyphen added; hyphen kept where the source has one and index has none
    assert t("aælan", "ā-ǣlan") == "āǣlan"
    assert t("a-ælan", "āǣlan") == "ā-ǣlan"
    # en/em dashes are kept and treated as hyphens
    assert t("a—ælan", "ā-ǣlan") == "ā—ǣlan"
    # mixed case preserved
    assert t("GeCynde", "ge-cynde") == "GeCynde"
    assert t("HLaford", "hlāford") == "HLāford"
    # existing marks are never removed or replaced
    assert t("ǣ", "æ") == "ǣ"
    assert t("ā", "ǣ") is None  # different letters
    assert t("hlāford", "hlaford") == "hlāford"


def test_diacritic_transfer_unalignable_returns_none():
    assert DiacriticTransfer.transfer("ærþling", "ǣrst") is None
    assert DiacriticTransfer.transfer("barr", "bār") is None
    assert DiacriticTransfer.transfer("aet", "æt") is None


def test_macron_applicator_reports_unaligned_and_leaves_token(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"ærþling": "ǣrst", "ðā": "þā"}, ambiguous={})
    applicator = MacronApplicator(index_path)

    token, ambiguity, is_unknown, unaligned = applicator.apply(
        "ærþling", line_number=1, word_number=1
    )
    assert (token, ambiguity, is_unknown, unaligned) == ("ærþling", None, False, "ǣrst")

    marked, *_ = applicator.apply("ðā", line_number=1, word_number=2)
    assert marked == "ðā"


def test_restorer_unaligned_report_and_no_source_changes(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={"ærþling": "ǣrst", "aælan": "ā-ǣlan", "hlaford": "hlāford"},
        ambiguous={},
    )
    restorer = DiacriticRestorer(macron_index_path=index_path)

    result = restorer.restore_text("ærþling aælan HLaford\n")

    assert result.marked_text == "ærþling āǣlan HLāford\n"
    assert [(u.word, u.index_form) for u in result.unaligned] == [("ærþling", "ǣrst")]


def test_restorer_handles_decomposed_input_without_shredding(tmp_path: Path):
    import unicodedata

    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"hlaford": "hlāford"}, ambiguous={})
    restorer = DiacriticRestorer(macron_index_path=index_path)

    source = unicodedata.normalize("NFD", "hlāford")
    result = restorer.restore_text(source)

    assert result.marked_text == source
    assert result.unknowns == []
    assert result.unaligned == []


def test_c_palatalizer_never_dots_sc():
    palatalizer = CPalatalizer()
    assert palatalizer.palatalize("scip") == "scip"
    assert palatalizer.palatalize("scīr") == "scīr"
    assert palatalizer.palatalize("Scip") == "Scip"
    assert palatalizer.palatalize("fisc") == "fisc"
    # c after a hyphen is not preceded by s
    assert palatalizer.palatalize("is-cild") == "is-ċild"
    # existing dot is kept
    assert palatalizer.palatalize("sċip") == "sċip"


def test_palatalizers_only_add_dots_and_keep_case():
    assert GPalatalizer().palatalize("ǢGhwā") == "ǢĠhwā"
    assert GPalatalizer().palatalize("GECYNDE") == "ĠECYNDE"
    assert GPalatalizer().palatalize("Giefan") == "Ġiefan"
    assert CPalatalizer().palatalize("CILD") == "ĊILD"
    assert CPalatalizer().palatalize("Cild") == "Ċild"
    assert CPalatalizer().palatalize("cild—cild") == "ċild—ċild"


def test_g_palatalizer_velar_before_back_vowel_and_folded_exceptions():
    palatalizer = GPalatalizer()
    assert palatalizer.palatalize("stīgan") == "stīgan"
    assert palatalizer.palatalize("wiga") == "wiga"
    assert palatalizer.palatalize("hige") == "hiġe"
    assert palatalizer.palatalize("þegn") == "þeġn"
    # exception list compares with ð≡þ folded
    assert palatalizer.palatalize("gēoguð") == "gēoguð"
    assert palatalizer.palatalize("gēoguþ") == "gēoguþ"


def test_mark_pattern_shape_for_a_diphthong():
    macron = "\u0304"
    assert DiacriticTransfer.mark_pattern("lēast") == (
        ("l", frozenset()),
        ("e", frozenset({macron})),
        ("a", frozenset()),
        ("s", frozenset()),
        ("t", frozenset()),
    )


def test_mark_pattern_moves_a_second_vowel_macron_to_the_first():
    assert DiacriticTransfer.mark_pattern("leāst") == DiacriticTransfer.mark_pattern(
        "lēast"
    )


def test_mark_pattern_ignores_case_hyphens_and_eth_thorn():
    pattern = DiacriticTransfer.mark_pattern
    assert pattern("Hlāford") == pattern("hlā-ford")
    assert pattern("ðā") == pattern("þā")
    assert pattern("a\u2014ælan") == pattern("aælan")


def test_mark_pattern_does_not_join_vowels_separated_by_a_hyphen():
    pattern = DiacriticTransfer.mark_pattern
    assert pattern("be-ōdrian") != pattern("bēodrian")
    assert pattern("beōdrian") == pattern("bēodrian")


def test_mark_pattern_leaves_a_breve_on_its_own_letter():
    breve = "\u0306"
    pattern = DiacriticTransfer.mark_pattern("ēliŏtrŏpus")
    assert pattern[3] == ("o", frozenset({breve}))
    assert pattern[2] == ("i", frozenset())


@pytest.mark.parametrize(
    ("source", "reference", "expected"),
    [
        # source already marks the second vowel: nothing is added (the bug)
        ("leāst", "lēast", "leāst"),
        ("lēast", "lēast", "lēast"),
        # unmarked source gets the macron on the FIRST vowel, from either style
        ("least", "lēast", "lēast"),
        ("least", "leāst", "lēast"),
        # source case wins
        ("LEAST", "lēast", "LĒAST"),
        ("Least", "leāst", "Lēast"),
        # ie and io are diphthongs too
        ("driefan", "driēfan", "drīefan"),
        ("driēfan", "drīefan", "driēfan"),
        ("hio", "hīo", "hīo"),
        # a hyphen in the REFERENCE keeps the vowels apart
        ("beodrian", "be-ōdrian", "beōdrian"),
        ("beodrian", "beōdrian", "bēodrian"),
        # a hyphen in the SOURCE does not matter
        ("e-a", "ēa", "ē-a"),
        # a different mark on the source is kept, nothing is added to the pair
        ("leăst", "lēast", "leăst"),
        # macrons on both reference vowels merge onto the first
        ("feond", "fēōnd", "fēond"),
        ("lēast", "lēāst", "lēast"),
        # a breve in the reference marks a hiatus: each mark stays on its letter
        ("eliotropus", "ēliŏtrŏpus", "ēliŏtrŏpus"),
        # not a diphthong: per-letter behavior
        ("hia", "hiā", "hiā"),
        ("hae", "hāe", "hāe"),
        # pairs do not overlap: the first pair wins
        ("beoa", "beōa", "bēoa"),
    ],
)
def test_transfer_treats_a_diphthong_as_one_unit(source, reference, expected):
    assert DiacriticTransfer.transfer(source, reference) == expected


def test_transfer_diphthong_in_decomposed_source_is_not_double_marked():
    import unicodedata

    source = unicodedata.normalize("NFD", "leāst")
    assert DiacriticTransfer.transfer(source, "lēast") == source


def test_transfer_adds_marks_to_a_decomposed_source_letter_as_composed():
    import unicodedata

    result = DiacriticTransfer.transfer(unicodedata.normalize("NFD", "least"), "lēast")
    assert result == unicodedata.normalize("NFC", "lēast")


def test_restorer_does_not_double_mark_a_bt_style_diphthong(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"least": "leāst"}, ambiguous={})
    restorer = DiacriticRestorer(macron_index_path=index_path)

    result = restorer.restore_text("least leāst lēast LEAST\n")

    assert result.marked_text == "lēast leāst lēast LĒAST\n"
    assert result.unaligned == []


def test_load_folded_word_list_skips_comments_blanks_and_folds(tmp_path: Path):
    words = tmp_path / "frontal.txt"
    words.write_text(
        "# a comment\n\n  Gildas  \ngǣst-\ngǣlsa -\ngēoguð\n-\n#-\n",
        encoding="utf-8",
    )

    assert _load_folded_word_list(words) == frozenset(
        {"gildas", "gǣst", "gǣlsa", "gēoguþ"}
    )


def test_load_folded_word_list_ignores_a_byte_order_mark(tmp_path: Path):
    words = tmp_path / "bom.txt"
    words.write_bytes(b"\xef\xbb\xbfGildas\ngigant\n")

    assert _load_folded_word_list(words) == frozenset({"gildas", "gigant"})


def test_load_folded_word_list_missing_file_is_empty_and_warns(tmp_path: Path, caplog):
    result = _load_folded_word_list(tmp_path / "nope.txt")

    assert result == frozenset()
    assert "nope.txt" in caplog.text


def test_load_folded_word_list_empty_file_is_empty(tmp_path: Path):
    words = tmp_path / "empty.txt"
    words.write_text("", encoding="utf-8")

    assert _load_folded_word_list(words) == frozenset()


def test_default_g_frontal_path_points_to_the_packaged_file():
    assert DEFAULT_G_FRONTAL_PATH.name == "frontal.txt"
    assert DEFAULT_G_FRONTAL_PATH.parent.name == "g"
    assert DEFAULT_G_FRONTAL_PATH.exists()
