"""Tests for morphology dictionary TSV cleanup."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from wyrdcraeft.services.morphology.dictionary_cleanup import (
    MorphologyDictionaryCleaner,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ACSAN", True),
        ("A-BACAN", True),
        ("Ā", True),
        ("Abban dūn", False),
        ("abban dūn", False),
        ("ā", False),
        ("NULL", False),
        ("133;265", False),
    ],
)
def test_should_lowercase_col2_only_all_upper_letters(value, expected) -> None:
    assert MorphologyDictionaryCleaner._should_lowercase_col2(value) is expected


def test_clean_dictionary_lowercases_col2_dedupes_and_backups(tmp_path) -> None:
    dictionary_path = tmp_path / "dict_adj-vb-part-num-adv-noun.txt"
    original_text = (
        "1\tAbban dūn\tNULL\t1\t0\t0\n"
        "2\tabban dūn\tNULL\t1\t0\t0\n"
        "3\tā\t133\t0\t0\t1\n"
        "4\tĀ\t133\t0\t0\t1\n"
        "5\tACSAN\t597\t1\t0\t0\n"
        "6\tNULL\t597\t1\t0\t0\n"
    )
    dictionary_path.write_text(original_text, encoding="utf-8")
    fixed_now = datetime(2026, 7, 8, 12, 30, 45, tzinfo=UTC)

    result = MorphologyDictionaryCleaner(
        dictionary_path,
        now=fixed_now,
    ).run()

    assert result.rows_read == 6
    assert result.lowercase_changes == 2
    assert result.duplicates_removed == 1
    assert result.rows_written == 5
    assert result.backup_path == dictionary_path.with_name(
        "dict_adj-vb-part-num-adv-noun.txt.20260708-123045.bak"
    )
    assert result.backup_path.read_text(encoding="utf-8") == original_text

    cleaned_lines = dictionary_path.read_text(encoding="utf-8").splitlines()
    assert cleaned_lines == [
        "1\tAbban dūn\tNULL\t1\t0\t0",
        "2\tabban dūn\tNULL\t1\t0\t0",
        "3\tā\t133\t0\t0\t1",
        "5\tacsan\t597\t1\t0\t0",
        "6\tNULL\t597\t1\t0\t0",
    ]


def test_clean_dictionary_raises_when_source_missing(tmp_path) -> None:
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError, match="Dictionary file not found"):
        MorphologyDictionaryCleaner(missing).run()
