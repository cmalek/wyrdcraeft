from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.models.diacritics import MacronIndexPayload
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.variant_filter import BTVariantFilter
from wyrdcraeft.services.variant_importer import BTVariantImporter

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.models.variant_import import VariantImportReport


def _line(headword: str, *variants: str) -> str:
    return f"{headword}@<B>{headword},</B> {', '.join(variants)}; <I>m.</I> a word.@{headword}"


def _importer() -> BTVariantImporter:
    return BTVariantImporter(variant_filter=BTVariantFilter(["v", "cf", "ps", "rdr"]))


def _report(
    tmp_path: Path,
    lines: list[str],
    *,
    unique: dict[str, str] | None = None,
    ambiguous: dict[str, list[str]] | None = None,
    completed: set[str] | None = None,
) -> VariantImportReport:
    source = tmp_path / "oe_bt.txt"
    source.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    payload = MacronIndexPayload(
        unique=unique or {},
        ambiguous=ambiguous or {},
        ambiguous_completed=completed or set(),
    )
    return _importer().build_report(source, payload)


def test_adds_spelling_variants_of_the_headword(tmp_path: Path):
    report = _report(tmp_path, [_line("tilung", "teolung", "tiolung")])

    assert report.additions == {"teolung": "teolung", "tiolung": "tiolung"}
    assert report.counts["added"] == 2
    assert report.collisions == []
    assert report.below_gate == []


def test_stores_what_bt_prints_lowercased_never_the_headword_marks(tmp_path: Path):
    report = _report(tmp_path, [_line("bār", "Barr")])

    # No macron is copied from the headword; capitalization is dropped.
    assert report.additions == {"barr": "barr"}


def test_every_added_form_normalizes_to_its_key(tmp_path: Path):
    report = _report(
        tmp_path,
        [_line("hīred-mann", "heord-mann", "Hīrēd-mann"), _line("tilung", "Tiolung")],
    )

    assert report.additions
    for key, form in report.additions.items():
        assert normalize_old_english(form) == key
        assert form == form.lower()


def test_rejects_junk_and_counts_it(tmp_path: Path):
    lines = [
        "bar@<B>bār,</B> v. Cf. Ps. Rdr; <I>m.</I> a boar.@bar",
        "stregdan@<B>stregdan,</B> classes, UNCERTAIN, on-g; <I>v.</I> to strew.@stregdan",
        _line("aaa", "zzz"),
        _line("bbb", "zzz"),
        _line("ccc", "zzz"),
    ]

    report = _report(tmp_path, lines)

    assert report.additions == {}
    assert report.counts["rejected_stoplist"] == 4
    assert report.counts["rejected_all_caps"] == 1
    assert report.counts["rejected_fragment"] == 1
    assert report.counts["rejected_frequent"] == 3


def test_variants_that_are_not_spellings_of_their_headword_go_to_review(
    tmp_path: Path,
):
    stregdan = "stregdan@<B>stregdan,</B> classes; <I>v.</I> to strew.@stregdan"

    report = _report(tmp_path, [_line("tilung", "tiolung"), stregdan])

    assert "classes" not in report.additions
    assert [(r.spelling, r.headword, r.line_no) for r in report.below_gate] == [
        ("classes", "stregdan", 2)
    ]


def test_below_gate_skips_keys_already_in_the_index(tmp_path: Path):
    stregdan = "stregdan@<B>stregdan,</B> classes; <I>v.</I> to strew.@stregdan"

    report = _report(tmp_path, [stregdan], unique={"classes": "classes"})

    assert report.below_gate == []


@pytest.mark.parametrize(
    ("unique", "variant", "counter", "collision_reason"),
    [
        ({"weg": "wēg"}, "wēg", "skipped_same_marks", None),
        ({"weg": "wēg"}, "weg", "skipped_fewer_marks", None),
        ({"weg": "weg"}, "wēg", None, "more_marks"),
        ({"weg": "wĕg"}, "wēg", None, "conflicting_marks"),
    ],
)
def test_collisions_with_a_unique_entry(
    tmp_path: Path,
    unique: dict[str, str],
    variant: str,
    counter: str | None,
    collision_reason: str | None,
):
    report = _report(tmp_path, [_line("wege", variant)], unique=unique)

    assert report.additions == {}
    if counter is not None:
        assert report.counts[counter] == 1
        assert report.collisions == []
    else:
        assert [c.reason for c in report.collisions] == [collision_reason]
        assert report.collisions[0].existing == list(unique.values())
        assert report.collisions[0].variant.spelling == variant


@pytest.mark.parametrize(
    ("variant", "completed", "counter", "collision_reason"),
    [
        ("wēg", set(), "skipped_matches_option", None),
        ("wĕg", set(), None, "new_pattern"),
        ("wēg", {"weg"}, "skipped_completed", None),
        ("wĕg", {"weg"}, "skipped_completed", None),
    ],
)
def test_collisions_with_an_ambiguous_key(
    tmp_path: Path,
    variant: str,
    completed: set[str],
    counter: str | None,
    collision_reason: str | None,
):
    report = _report(
        tmp_path,
        [_line("wege", variant)],
        ambiguous={"weg": ["weg", "wēg"]},
        completed=completed,
    )

    assert report.additions == {}
    if counter is not None:
        assert report.counts[counter] == 1
        assert report.collisions == []
    else:
        assert [c.reason for c in report.collisions] == [collision_reason]
        assert report.collisions[0].existing == ["weg", "wēg"]


def test_two_variants_with_different_marks_for_one_new_key_add_neither(
    tmp_path: Path,
):
    report = _report(tmp_path, [_line("wege", "weg"), _line("wēge", "wēg")])

    assert report.additions == {}
    assert [c.key for c in report.conflicting_new] == ["weg"]
    assert sorted(v.spelling for v in report.conflicting_new[0].variants) == [
        "weg",
        "wēg",
    ]


def test_two_variants_with_the_same_marks_add_once(tmp_path: Path):
    report = _report(tmp_path, [_line("wege", "weg"), _line("wegen", "Weg")])

    assert report.additions == {"weg": "weg"}
    assert report.conflicting_new == []


def test_hyphen_and_case_differences_do_not_conflict(tmp_path: Path):
    report = _report(tmp_path, [_line("ǣwege", "ǣ-weg"), _line("ǣwegen", "Ǣweg")])

    # Same marks once hyphens and case are ignored: one entry, first spelling kept.
    assert report.conflicting_new == []
    assert report.additions == {"æweg": "ǣ-weg"}


def test_blank_unparseable_crlf_and_nfd_lines_do_not_crash(tmp_path: Path):
    source = tmp_path / "oe_bt.txt"
    nfd = unicodedata.normalize("NFD", _line("tilung", "tīolung"))
    lines = ["", "no at signs", "a@b", "x@<B>12</B> text@x", nfd]
    source.write_text(
        "".join(f"{line}\r\n" for line in lines), encoding="utf-8", newline=""
    )

    report = _importer().build_report(source, MacronIndexPayload())

    assert report.additions == {"tiolung": "tīolung"}


def test_apply_adds_only_new_keys_and_is_idempotent(tmp_path: Path):
    lines = [_line("tilung", "teolung", "tiolung")]
    source = tmp_path / "oe_bt.txt"
    source.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    payload = MacronIndexPayload(unique={"tilung": "tilung"})
    importer = _importer()

    first = importer.build_report(source, payload)
    added = importer.apply(first, payload)
    second = importer.build_report(source, payload)

    assert added == 2
    assert payload.unique == {
        "tilung": "tilung",
        "teolung": "teolung",
        "tiolung": "tiolung",
    }
    assert second.additions == {}
    assert second.counts["skipped_same_marks"] == 2
    assert importer.apply(second, payload) == 0


def test_apply_never_replaces_a_key_that_now_exists(tmp_path: Path):
    source = tmp_path / "oe_bt.txt"
    source.write_text(_line("tilung", "tiolung") + "\n", encoding="utf-8")
    importer = _importer()
    report = importer.build_report(source, MacronIndexPayload())
    # The index gained the key (by hand) after the report was built.
    payload = MacronIndexPayload(unique={"tiolung": "tīolung"})

    assert importer.apply(report, payload) == 0
    assert payload.unique == {"tiolung": "tīolung"}


@pytest.mark.parametrize(
    ("printed", "stored"),
    [
        ("dreōganne", "drēoganne"),  # BT marks the second vowel; the index the first
        ("biēn", "bīen"),
        ("be-geāton", "be-gēaton"),
        ("ge-ān", "ge-ān"),  # a hyphen between the vowels is not a diphthong
        ("drēoganne", "drēoganne"),
    ],
)
def test_diphthong_marks_are_stored_on_the_first_vowel(
    tmp_path: Path, printed: str, stored: str
):
    # The headword is one letter off, so the variant passes the similarity gate.
    report = _report(tmp_path, [_line(normalize_old_english(printed) + "x", printed)])

    assert list(report.additions.values()) == [stored]
