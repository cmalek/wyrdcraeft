"""Tests for Phase 02 Bosworth-Toller line parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from wyrdcraeft.models.dictionary import BTLineKind, BTPos
from wyrdcraeft.services.dictionary.line_parser import BTLineParser

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "dictionary" / "sample_lines.txt"
)
_MIN_FIXTURE_LINES = 45
_MAX_FIXTURE_LINES = 80


def _sample_lines() -> list[str]:
    return _FIXTURE_PATH.read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize(
    "line",
    _sample_lines(),
)
def test_sample_fixture_lines_are_parseable_or_skipped_with_reason(line: str) -> None:
    """
    Parse each fixture line and require deterministic success or explicit skip.
    """
    parser = BTLineParser()
    parsed = parser.parse(source_line_no=1, line=line)
    if parsed.raw_line is not None:
        assert parsed.skip_reason is None
        assert parsed.raw_line.headword_raw
        assert parsed.headword_macronized
        return
    assert parsed.skip_reason in {
        "not 3 @ fields",
        "no <B> headword",
        "headword not wordlike",
    }


def test_sample_fixture_contains_about_fifty_real_lines() -> None:
    """
    Fixture stays in the expected size range for phase-02 coverage.
    """
    lines = _sample_lines()
    assert _MIN_FIXTURE_LINES <= len(lines) <= _MAX_FIXTURE_LINES


@pytest.mark.parametrize(
    ("line", "expected_kind"),
    [
        (
            "aawarnian@<B>ā-awārnian.</B> <I>Add:</I> :-- Hȳ āswārnien "
            "<I>reuereantur,</I> Ps. Rdr. 82, 18.@a-awarnian",
            BTLineKind.ADD,
        ),
        (
            "abaedan@<B>ā-bǣdan.</B> <I>Substitute the following:</I> "
            "<B>I.</B> <I>to force, wring</I> :-- Ele ābǣdan and āwringan.@a-bædan",
            BTLineKind.SUBSTITUTE,
        ),
        (
            "abitweonum@<B>a-bitweōnum</B>. <I>Dele</I>.@a-bi-tweonum,a-bitweonum",
            BTLineKind.DELE,
        ),
        (
            "abutan@<B>ā-būtan</B>. <I>Dele first passage and add:</I> <B>I</B>. "
            "<I>prep. dat. acc.</I> marking (1) position :-- Stōdon him ābūtan "
            "swearte gāstas.@a-butan",
            BTLineKind.DELE_AND_ADD,
        ),
        (
            "ab@<B>āb.</B> v. ō-web.@ab",
            BTLineKind.CROSS_REF,
        ),
        (
            "aad@<B>aad</B> <I>a pile</I> :-- He mycelne aad gesomnode.@aad",
            BTLineKind.MAIN,
        ),
    ],
)
def test_line_kind_classification(line: str, expected_kind: BTLineKind) -> None:
    """
    Parser classifies editorial and cross-reference markers correctly.
    """
    parsed = BTLineParser().parse(source_line_no=1, line=line)
    assert parsed.raw_line is not None
    assert parsed.raw_line.kind == expected_kind


@pytest.mark.parametrize(
    ("line", "expected_reason"),
    [
        ("badly formatted line", "not 3 @ fields"),
        ("x@no bold here@y", "no <B> headword"),
        ("x@<B>-a,</B> demo@y", "headword not wordlike"),
    ],
)
def test_skip_reasons_are_explicit(line: str, expected_reason: str) -> None:
    """
    Skipped lines return explicit reasons needed by downstream reporting.
    """
    parsed = BTLineParser().parse(source_line_no=7, line=line)
    assert parsed.raw_line is None
    assert parsed.skip_reason == expected_reason


def test_extracts_substitute_editorial_target() -> None:
    """
    Substitute target extraction captures ``for X in Dict`` phrases.
    """
    line = (
        "abisgung@<B>ā-bisgung</B> e; <I>f. Substitute the following for</I> "
        "ā-bysgung <I>in Dict</I>. <B>I</B>. <I>occupation</I>.@a-bisgung"
    )
    parsed = BTLineParser().parse(source_line_no=110, line=line)
    assert parsed.editorial_target == "ā-bysgung"


def test_extracts_variants_and_pos_gender_from_headword_prefix() -> None:
    """
    Variant and noun-gender extraction uses pre-POS prefix conventions.
    """
    line = (
        "abbad@<B>abbad,</B> abbod, abbud, abbot, es; <I>m:</I> abboda, an; "
        "<I>m.</I> I. <I>an abbot;</I> sample.@abbad"
    )
    parsed = BTLineParser().parse(source_line_no=37, line=line)
    assert parsed.raw_line is not None
    assert parsed.pos == BTPos.NOUN
    assert [gender.value for gender in parsed.genders] == ["m"]
    assert parsed.variants[:3] == ("abbod", "abbud", "abbot")


@pytest.mark.parametrize(
    ("line", "expected_headword_macronized"),
    [
        (
            "abeodan@<B>ā-beōdan.</B> <I>Add:</I> sample text.@a-beodan",
            "ā-bēodan",
        ),
        (
            "aceosan@<B>ā-ceōsan</B>. <I>Add:</I> sample text.@a-ceosan",
            "ā-cēosan",
        ),
        (
            "abreotan@<B>ā-breōtan.</B> <I>Add:</I> sample text.@a-breotan",
            "ā-brēotan",
        ),
    ],
)
def test_headword_macronized_corrects_bt_second_vowel_long_mark(
    line: str,
    expected_headword_macronized: str,
) -> None:
    """
    Parser emits display headwords with Wright-style diphthong long marks.
    """
    parsed = BTLineParser().parse(source_line_no=1, line=line)
    assert parsed.raw_line is not None
    assert parsed.headword_macronized == expected_headword_macronized


def test_extracts_trailing_etymology_blocks() -> None:
    """
    Trailing bracket blocks are preserved for later etymology handling.
    """
    line = (
        "abarian@<B>ā-barian.</B> <I>Add:</I> <B>I.</B> <I>to lay bare</I> :-- body. "
        "[<I>O. H. Ger.</I> ar-bar;ōn <I>denudare, prodere.</I>]@a-barian"
    )
    parsed = BTLineParser().parse(source_line_no=35, line=line)
    assert parsed.etymology_blocks == (
        "[<I>O. H. Ger.</I> ar-bar;ōn <I>denudare, prodere.</I>]",
    )


def test_extracts_dele_references_until_stop_markers() -> None:
    """
    Deletion references are parsed from text after the ``Dele`` marker.
    """
    line = (
        "adon@<B>ā-dōn.</B> <I>Dele</I> Ælfc. T. 5, 25: Gen. 7, 23: 9, 11, "
        "<I>and add:</I> with words further marking removal.@a-don"
    )
    parsed = BTLineParser().parse(source_line_no=498, line=line)
    assert parsed.raw_line is not None
    assert parsed.raw_line.kind == BTLineKind.DELE_AND_ADD
    assert parsed.dele_refs == ("Ælfc. T. 5", "25: Gen. 7", "23: 9", "11")
