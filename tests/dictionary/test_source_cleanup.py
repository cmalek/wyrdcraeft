"""Tests for Bosworth-Toller oe_bt.txt headword cleanup."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from wyrdcraeft.services.dictionary.source_cleanup import BTSourceHeadwordCleaner


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("BEŌN", True),
        ("ABAL,", True),
        ("Dōn", False),
        ("Abban dūn,", False),
        ("a-dōn;", False),
        ("133;265", False),
    ],
)
def test_should_lowercase_headword_only_all_upper_letters(value, expected) -> None:
    assert BTSourceHeadwordCleaner._should_lowercase_headword(value) is expected


def test_clean_headwords_lowercases_first_bold_and_backups(tmp_path) -> None:
    source_path = tmp_path / "oe_bt.txt"
    original_text = (
        "beon@<B>BEŌN</B> [biōn], to beōnne;@beon\n"
        "adon@<B>a-dōn;</B> <I>p.</I> -dyde;@a-don\n"
        "abban dun@<B>Abban dūn,</B> e; <I>f.</I>@abban dun\n"
    )
    source_path.write_text(original_text, encoding="utf-8")
    fixed_now = datetime(2026, 7, 8, 12, 30, 45, tzinfo=UTC)

    result = BTSourceHeadwordCleaner(
        source_path,
        now=fixed_now,
    ).run()

    assert result.lines_read == 3
    assert result.lowercase_changes == 1
    assert result.lines_written == 3
    assert result.backup_path == source_path.with_name("oe_bt.txt.20260708-123045.bak")
    assert result.backup_path.read_text(encoding="utf-8") == original_text

    cleaned_lines = source_path.read_text(encoding="utf-8").splitlines()
    assert cleaned_lines[0].startswith("beon@<B>beōn</B>")
    assert cleaned_lines[1] == (
        "adon@<B>a-dōn;</B> <I>p.</I> -dyde;@a-don"
    )
    assert cleaned_lines[2] == (
        "abban dun@<B>Abban dūn,</B> e; <I>f.</I>@abban dun"
    )


def test_clean_headwords_leaves_later_bold_tags_unchanged(tmp_path) -> None:
    source_path = tmp_path / "oe_bt.txt"
    original_text = (
        "abiddan@<B>ā-biddan</B>. <I>Add:</I> <B>I</B>. "
        "<I>to pray</I>@abiddan\n"
    )
    source_path.write_text(original_text, encoding="utf-8")

    result = BTSourceHeadwordCleaner(source_path).run()

    assert result.lowercase_changes == 0
    assert source_path.read_text(encoding="utf-8") == original_text


def test_clean_headwords_raises_when_source_missing(tmp_path) -> None:
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError, match="Dictionary source file not found"):
        BTSourceHeadwordCleaner(missing).run()
