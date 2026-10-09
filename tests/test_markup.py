from __future__ import annotations

import json
import unicodedata
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
from wyrdcraeft.services.standard_elements import StandardElements

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
    ambiguous_completed: list[str] | None = None,
) -> None:
    payload = {
        "unique": unique,
        "ambiguous": ambiguous,
        "ambiguous_completed": ambiguous_completed or [],
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
        unique={"ærþling": "ǣrst", "oælan": "ō-ǣlan", "hlaford": "hlāford"},
        ambiguous={},
    )
    restorer = DiacriticRestorer(macron_index_path=index_path)

    result = restorer.restore_text("ærþling oælan HLaford\n")

    assert result.marked_text == "ærþling ōǣlan HLāford\n"
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


def test_load_folded_word_list_missing_file_is_empty_and_warns(tmp_path: Path):
    from unittest.mock import patch

    missing = tmp_path / "nope.txt"
    # patch the module logger: caplog depends on logging config other tests change
    with patch("wyrdcraeft.services.markup.LOGGER") as logger:
        result = _load_folded_word_list(missing)

    assert result == frozenset()
    logger.warning.assert_called_once()
    assert missing in logger.warning.call_args.args


def test_load_folded_word_list_empty_file_is_empty(tmp_path: Path):
    words = tmp_path / "empty.txt"
    words.write_text("", encoding="utf-8")

    assert _load_folded_word_list(words) == frozenset()


def test_default_g_frontal_path_points_to_the_packaged_file():
    assert DEFAULT_G_FRONTAL_PATH.name == "frontal.txt"
    assert DEFAULT_G_FRONTAL_PATH.parent.name == "g"
    assert DEFAULT_G_FRONTAL_PATH.exists()


#: Every word in ``GPalatalizer.FRONTAL_G_EXCEPTIONS`` before it moved to a file.
OLD_FRONTAL_G_EXCEPTIONS = [
    "gǣl", "gǣf", "gǣfon", "gǣlscipe", "gǣng", "gǣnge", "gǣr", "gǣrlicgǣst",
    "gǣstas", "gǣsthus", "gǣstlic", "gǣstlīce", "gǣt", "gǣten", "gaf", "gafol",
    "gafolrǣden", "gafolgyld", "galan", "gangan", "gār", "gāt", "gēar", "gēara",
    "gēoguð", "geōguþ", "gēn", "gēna", "gēola", "gēol", "gēomor", "gēong",
    "gēongra", "gēs", "gēsne", "gēsnian", "gēsting", "gēstlīc", "gēsthus",
    "gēat", "gēatlic", "gēard", "gēatas", "gēatland",
]  # fmt: skip


def test_default_frontal_file_keeps_every_old_hardcoded_exception():
    from wyrdcraeft.services.markup import _fold

    in_file = _load_folded_word_list(DEFAULT_G_FRONTAL_PATH)

    missing = [w for w in OLD_FRONTAL_G_EXCEPTIONS if _fold(w) not in in_file]
    assert missing == []
    assert len(OLD_FRONTAL_G_EXCEPTIONS) == 44


def test_default_frontal_file_keeps_the_users_own_entries():
    in_file = _load_folded_word_list(DEFAULT_G_FRONTAL_PATH)

    assert {"gigant", "genesis", "gylden", "girwan", "gildas", "gǣst"} <= in_file


def test_g_palatalizer_reads_its_exceptions_from_the_given_file(tmp_path: Path):
    words = tmp_path / "frontal.txt"
    words.write_text("# comment\nGildas\ngǣst-\n", encoding="utf-8")
    palatalizer = GPalatalizer(frontal_path=words)

    assert palatalizer.palatalize("Gildas") == "Gildas"
    assert palatalizer.palatalize("gǣst") == "gǣst"
    # an entry exempts only that exact word, not longer words
    assert palatalizer.palatalize("gǣstas") == "ġǣstas"
    # a hyphenated token is exempted through its dash-free segment
    assert palatalizer.palatalize("gǣst-hūs") == "gǣst-hūs"
    # words not in this file lose the protection the old list gave
    assert palatalizer.palatalize("gēar") == "ġēar"


def test_g_palatalizer_with_an_empty_file_has_no_frontal_exceptions(tmp_path: Path):
    words = tmp_path / "empty.txt"
    words.write_text("", encoding="utf-8")

    assert GPalatalizer(frontal_path=words).palatalize("gēar") == "ġēar"


def test_g_palatalizer_default_file_applies_the_users_own_entries():
    palatalizer = GPalatalizer()

    assert palatalizer.palatalize("gigant") == "gigant"
    assert palatalizer.palatalize("Gildas") == "Gildas"
    assert palatalizer.palatalize("gylden") == "gylden"


def test_g_palatalizer_default_file_keeps_the_old_protection():
    palatalizer = GPalatalizer()

    for word in ("gēar", "gēat", "gǣt", "gēn", "gǣl", "gēs"):
        assert palatalizer.palatalize(word) == word


def test_g_palatalizer_ending_exceptions_still_apply():
    palatalizer = GPalatalizer()

    assert palatalizer.palatalize("plǣg") == "plǣg"
    assert palatalizer.palatalize("sweg") == "sweg"


def test_g_palatalizer_no_longer_has_a_hardcoded_frontal_list():
    assert not hasattr(GPalatalizer, "FRONTAL_G_EXCEPTIONS")


@pytest.mark.parametrize(
    ("forms", "expected"),
    [
        (["ǣwisc-nys", "ǣwiscnys"], True),
        (["leāst", "lēast"], True),
        (["þēod-ne", "ðēodne"], True),
        (["cū-slyppe", "Cūslyppe"], True),
        (["ac", "āc"], False),
        (["wegas", "wēgas"], False),
        (["ǣwiscnys"], True),
        ([], False),
    ],
)
def test_same_marks(forms, expected):
    assert DiacriticTransfer.same_marks(forms) is expected


def test_macron_index_carries_completed_keys(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"ac": ["ac", "āc"]},
        ambiguous_completed=["ac"],
    )

    assert MacronApplicator(index_path).index.ambiguous_completed == frozenset({"ac"})


@pytest.mark.parametrize(
    ("options", "word", "expected"),
    [
        (["ǣwisc-nys", "ǣwiscnys"], "æwiscnys", "ǣwiscnys"),
        (["cū-slyppe", "cūslyppe"], "Cuslyppe", "Cūslyppe"),
        (["þēod-ne", "ðēodne"], "ðeodne", "ðēodne"),
        (["leāst", "lēast"], "least", "lēast"),
        (["cū-slyppe", "cūslyppe"], "cūslyppe", "cūslyppe"),
    ],
)
def test_apply_collapses_options_that_agree_on_marks(
    tmp_path: Path, options, word, expected
):
    index_path = tmp_path / "index.json"
    key = normalize_old_english(options[0])
    _write_index(index_path, unique={}, ambiguous={key: options})

    marked, ambiguity, is_unknown, unaligned = MacronApplicator(index_path).apply(
        word, line_number=1, word_number=1
    )

    assert marked == expected
    assert ambiguity is None
    assert is_unknown is False
    assert unaligned is None


def test_apply_collapse_keeps_decomposed_source_letters(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path, unique={}, ambiguous={"cuslyppe": ["cū-slyppe", "cūslyppe"]}
    )
    # The source already has a dot on the c, written as c + combining dot.
    source = unicodedata.normalize("NFD", "ċuslyppe")

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        source, line_number=1, word_number=1
    )

    assert ambiguity is None
    assert unicodedata.normalize("NFC", marked) == "ċūslyppe"


def test_apply_keeps_ambiguity_when_options_differ_in_marks(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous={"ac": ["ac", "āc"]})

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        "ac", line_number=1, word_number=1
    )

    assert marked == "ac"
    assert ambiguity is not None


def test_apply_never_collapses_a_completed_key(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"cuslyppe": ["cū-slyppe", "cūslyppe"]},
        ambiguous_completed=["cuslyppe"],
    )

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        "cuslyppe", line_number=1, word_number=1
    )

    assert marked == "cuslyppe"
    assert ambiguity is not None


def test_apply_single_option_ambiguous_key_marks_it(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous={"cild": ["cīld"]})

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        "cild", line_number=1, word_number=1
    )

    assert marked == "cīld"
    assert ambiguity is None


def test_restorer_marks_collapsed_token_and_reports_nothing(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"cuslyppe": ["cū-slyppe", "cūslyppe"], "ac": ["ac", "āc"]},
    )

    result = DiacriticRestorer(macron_index_path=index_path).restore_text(
        "Cuslyppe ac\n"
    )

    assert result.marked_text == "Cūslyppe ac\n"
    assert [a.word for a in result.ambiguities] == ["ac"]
    assert result.unknowns == []
    assert result.unaligned == []


def test_apply_collapse_does_not_double_mark_a_diphthong(tmp_path: Path):
    index_path = tmp_path / "index.json"
    # "stē-ap" sorts before "stēap"; only the second treats ēa as one unit.
    _write_index(index_path, unique={}, ambiguous={"steap": ["stē-ap", "stēap"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path).apply("steāp", 1, 1)

    assert ambiguity is None
    assert transformed == "steāp"


def test_apply_keeps_ambiguity_when_key_is_in_unique_and_ambiguous(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"ac": "ac"}, ambiguous={"ac": ["ac", "āc"]})

    transformed, ambiguity, is_unknown, _ = MacronApplicator(index_path).apply(
        "ac", 1, 1
    )

    assert transformed == "ac"
    assert ambiguity is not None
    assert not is_unknown


def test_same_marks_standardizes_elements_first():
    elements = StandardElements(["hīrēd-", "for-"])

    assert not DiacriticTransfer.same_marks(["hīred-mann", "hīrēd-mann"])
    assert DiacriticTransfer.same_marks(["hīred-mann", "hīrēd-mann"], elements)
    assert DiacriticTransfer.same_marks(["for-beran", "fōr-beran"], elements)
    # No BT hyphen in one option, so the pair stays ambiguous.
    assert not DiacriticTransfer.same_marks(["ge-an", "gēan"], StandardElements(["ge-"]))


@pytest.mark.parametrize(
    ("ambiguous", "word", "expected"),
    [
        ({"hiredmann": ["hīred-mann", "hīrēd-mann"]}, "hiredmann", "hīrēdmann"),
        ({"foreberan": ["fore-beran", "fōre-beran"]}, "foreberan", "foreberan"),
    ],
)
def test_apply_collapses_options_that_differ_only_in_a_standard_element(
    tmp_path: Path, ambiguous: dict[str, list[str]], word: str, expected: str
):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous=ambiguous)

    transformed, ambiguity, _, _ = MacronApplicator(index_path).apply(word, 1, 1)

    assert ambiguity is None
    assert transformed == expected


def test_apply_keeps_ge_an_and_gean_apart(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous={"gean": ["ge-an", "gēan"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path).apply("gean", 1, 1)

    assert transformed == "gean"
    assert ambiguity is not None


@pytest.mark.parametrize(
    ("unique", "word", "expected"),
    [
        ({"abacan": "ā-bacan"}, "abacan", "abacan"),
        ({"oþfeolan": "oþ-feolan"}, "oþfeolan", "ōþfeolan"),
        # Source keeps its own marks (additive, ADR 0015).
        ({"abacan": "ā-bacan"}, "ābacan", "ābacan"),
    ],
)
def test_apply_standardizes_unique_forms_too(
    tmp_path: Path, unique: dict[str, str], word: str, expected: str
):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique=unique, ambiguous={})

    assert MacronApplicator(index_path).apply(word, 1, 1)[0] == expected


def test_apply_never_collapses_a_completed_key_even_through_elements(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"foreberan": ["fore-beran", "fōre-beran"]},
        ambiguous_completed=["foreberan"],
    )

    _, ambiguity, _, _ = MacronApplicator(index_path).apply("foreberan", 1, 1)

    assert ambiguity is not None


@pytest.mark.parametrize(
    ("forms", "expected"),
    [
        (["ac", "āc"], "āc"),
        (["lufigende", "lūfigende"], "lūfigende"),
        # macron vs breve on one letter conflict: no mark on that letter
        (["lŭfigende", "lūfigende", "lufigende"], "lufigende"),
        # dot-above does not conflict with a macron
        (["ġē", "ge", "gē"], "ġē"),
        # letters that cannot be lined up: no union
        (["ac", "acc"], None),
    ],
)
def test_union_form(forms: list[str], expected: str | None):
    assert DiacriticTransfer.union_form(forms) == expected


@pytest.mark.parametrize(
    ("forms", "expected"),
    [
        (["weg-fara", "wēg-fara"], True),
        (["an-weald", "ānweald"], True),
        (["ge-an", "gēan"], True),
        (["gold-hord", "gold-hōrd"], False),
        (["ac", "āc"], False),
        (["ac", "ac"], False),
    ],
)
def test_differs_only_before_hyphen(forms: list[str], expected: bool):
    assert DiacriticTransfer.differs_only_before_hyphen(forms) is expected


def _policy_index(tmp_path: Path, completed: list[str] | None = None) -> Path:
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={
            "ac": ["ac", "āc"],
            "wundorlic": ["wundorlic", "wundōrlic"],
            "goldhord": ["gold-hord", "gold-hōrd"],
            "wegfara": ["weg-fara", "wēg-fara"],
            "gean": ["ge-an", "gēan"],
        },
        ambiguous_completed=completed,
    )
    return index_path


@pytest.mark.parametrize(
    ("policy", "word", "written", "guessed"),
    [
        ("leave", "ac", "ac", None),
        ("leave", "goldhord", "goldhord", None),
        ("auto", "ac", "ac", None),  # short, no hyphen
        ("auto", "wundorlic", "wundōrlic", "auto"),  # 8+ letters
        ("auto", "goldhord", "goldhōrd", "auto"),  # hyphenated
        ("auto", "wegfara", "wegfara", None),  # differs only before the hyphen
        ("auto", "gean", "gean", None),  # ge-an / gēan stay apart (Review Focus)
        ("union", "ac", "āc", "union"),
        ("union", "wegfara", "wēgfara", "union"),
    ],
)
def test_apply_policy(
    tmp_path: Path, policy: str, word: str, written: str, guessed: str | None
):
    applicator = MacronApplicator(_policy_index(tmp_path), policy=policy)

    transformed, ambiguity, is_unknown, unaligned = applicator.apply(word, 1, 1)

    assert transformed == written
    assert ambiguity is not None  # guessed tokens stay in the report (decision 6)
    assert ambiguity.policy == guessed
    assert ambiguity.applied_form == (transformed if guessed else None)
    assert not is_unknown
    assert unaligned is None


def test_apply_policy_never_touches_a_completed_key(tmp_path: Path):
    applicator = MacronApplicator(
        _policy_index(tmp_path, completed=["ac"]), policy="union"
    )

    transformed, ambiguity, _, _ = applicator.apply("ac", 1, 1)

    assert transformed == "ac"
    assert ambiguity is not None
    assert ambiguity.policy is None


def test_apply_union_keeps_decomposed_source_letters(tmp_path: Path):
    applicator = MacronApplicator(_policy_index(tmp_path), policy="union")
    source = unicodedata.normalize("NFD", "wundorlic")

    transformed, _, _, _ = applicator.apply(source, 1, 1)

    assert unicodedata.normalize("NFD", transformed).replace("̄", "") == source


def test_apply_union_with_unalignable_options_leaves_token_reported(tmp_path: Path):
    index_path = tmp_path / "index.json"
    # Hand-edited bad data: same key, different letter counts.
    _write_index(index_path, unique={}, ambiguous={"acc": ["ac", "ācc"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path, policy="union").apply(
        "acc", 1, 1
    )

    assert transformed == "acc"
    assert ambiguity is not None
    assert ambiguity.policy is None


def test_apply_policy_applies_to_a_key_that_is_also_unique(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"ac": "ac"}, ambiguous={"ac": ["ac", "āc"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path, policy="union").apply(
        "ac", 1, 1
    )

    assert transformed == "āc"
    assert ambiguity is not None
    assert ambiguity.policy == "union"


def test_restorer_reports_guessed_tokens_with_policy(tmp_path: Path):
    restorer = DiacriticRestorer(
        macron_applicator=MacronApplicator(_policy_index(tmp_path), policy="union")
    )

    result = restorer.restore_text("ac goldhord\n")

    assert result.marked_text == "āc goldhōrd\n"
    assert [(a.word, a.applied_form, a.policy) for a in result.ambiguities] == [
        ("ac", "āc", "union"),
        ("goldhord", "goldhōrd", "union"),
    ]


def test_restorer_applied_form_is_the_text_actually_written(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"geceosan": ["ge-ceosan", "ge-cēosan"]},
    )
    restorer = DiacriticRestorer(
        macron_applicator=MacronApplicator(index_path, policy="union")
    )

    result = restorer.restore_text("geceosan\n")

    assert len(result.ambiguities) == 1
    assert result.ambiguities[0].policy == "union"
    # The palatalizers run after the macron step; the report must show their result.
    assert result.ambiguities[0].applied_form == result.marked_text.strip()


def test_apply_guess_that_cannot_be_aligned_is_also_reported_as_unaligned(
    tmp_path: Path,
):
    index_path = tmp_path / "index.json"
    # Hand-edited bad data: the options do not spell the key.
    _write_index(index_path, unique={}, ambiguous={"ab": ["ac", "āc"]})
    applicator = MacronApplicator(index_path, policy="union")

    transformed, ambiguity, is_unknown, unaligned = applicator.apply("ab", 1, 1)

    assert transformed == "ab"
    assert ambiguity is not None
    assert ambiguity.policy is None
    assert not is_unknown
    assert unaligned == "āc"

    result = DiacriticRestorer(macron_applicator=applicator).restore_text("ab\n")
    assert [(u.word, u.index_form) for u in result.unaligned] == [("ab", "āc")]
    assert len(result.ambiguities) == 1


@pytest.mark.parametrize(
    ("existing", "candidate", "expected"),
    [
        ("weg", "weg", "same"),
        ("wēg", "wēg", "same"),
        ("ǣ-ge", "ǣge", "same"),  # hyphens do not count
        ("wēg", "weg", "fewer"),
        ("weg", "wēg", "more"),
        ("wĕg", "wēg", "conflict"),  # breve against macron
        ("weg", "wēge", "conflict"),  # different letters
        ("leāst", "lēast", "same"),  # diphthong style does not count
    ],
)
def test_mark_relation(existing: str, candidate: str, expected: str):
    assert DiacriticTransfer.mark_relation(existing, candidate) == expected


def test_mark_relation_standardizes_elements_first():
    elements = StandardElements(["for-"])

    assert DiacriticTransfer.mark_relation("fōr-beran", "for-beran", elements) == "same"
    assert DiacriticTransfer.mark_relation("fōr-beran", "for-beran") == "fewer"
