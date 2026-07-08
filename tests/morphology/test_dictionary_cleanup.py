"""Tests for morphology dictionary TSV cleanup."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from wyrdcraeft.services.morphology.dictionary_cleanup import (
    MorphologyDictionaryCleaner,
)


def test_dictionary_cleanup_module_avoids_dictionary_package_import() -> None:
    source = Path(__file__).resolve().parents[2] / (
        "wyrdcraeft/services/morphology/dictionary_cleanup.py"
    )
    module_source = source.read_text(encoding="utf-8")
    assert "services.dictionary" not in module_source


def test_dictionary_cleanup_import_chain_smoke() -> None:
    from wyrdcraeft.cli import cli
    from wyrdcraeft.main import main

    assert cli is not None
    assert main is not None


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
        "6\ta-beōdan\t646\t0\t0\t1\n"
        "9\tbeōn\t548\t0\t0\t0\t1\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t0\t0\t0\t0\t0\n"
        "7\teīg-land\tNULL\t1\t0\t0\n"
        "8\tNULL\t597\t1\t0\t0\n"
    )
    dictionary_path.write_text(original_text, encoding="utf-8")
    fixed_now = datetime(2026, 7, 8, 12, 30, 45, tzinfo=UTC)

    result = MorphologyDictionaryCleaner(
        dictionary_path,
        now=fixed_now,
    ).run()

    assert result.rows_read == 9
    assert result.lowercase_changes == 2
    assert result.diphthong_fixes == 3
    assert result.duplicates_removed == 1
    assert result.rows_written == 8
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
        "6\ta-bēodan\t646\t0\t0\t1",
        "9\tbēon\t548\t0\t0\t0\t1\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t0\t0\t0\t0\t0",
        "7\tēig-land\tNULL\t1\t0\t0",
        "8\tNULL\t597\t1\t0\t0",
    ]


def test_clean_dictionary_raises_when_source_missing(tmp_path) -> None:
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError, match="Dictionary file not found"):
        MorphologyDictionaryCleaner(missing).run()


@pytest.mark.parametrize(
    ("input_title", "expected_title"),
    [
        ("a-beātan", "a-bēatan"),
        ("a-beōdan", "a-bēodan"),
        ("eīg-land", "ēig-land"),
        ("ælf-sciēne", "ælf-scīene"),
        ("Abban dūn", "Abban dūn"),
        ("NULL", "NULL"),
    ],
)
def test_clean_dictionary_fixes_bt_diphthongs_in_col2(
    tmp_path,
    input_title: str,
    expected_title: str,
) -> None:
    dictionary_path = tmp_path / "dict_adj-vb-part-num-adv-noun.txt"
    dictionary_path.write_text(
        f"1\t{input_title}\tNULL\t1\t0\t0\n",
        encoding="utf-8",
    )

    result = MorphologyDictionaryCleaner(dictionary_path).run()

    assert result.rows_written == 1
    cleaned_title = dictionary_path.read_text(encoding="utf-8").splitlines()[0].split("\t")[1]
    assert cleaned_title == expected_title
