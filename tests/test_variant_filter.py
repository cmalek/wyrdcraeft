from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from wyrdcraeft.services.variant_filter import (
    DEFAULT_VARIANT_STOPLIST_PATH,
    BTVariantFilter,
)

if TYPE_CHECKING:
    from pathlib import Path

FILTER = BTVariantFilter(["v", "cf", "ps", "rdr", "ii"])


@pytest.mark.parametrize(
    ("spelling", "headword_count", "expected"),
    [
        ("II", 1, "all_caps"),
        ("UNCERTAIN", 1, "all_caps"),
        ("APPLE-SHREDS", 1, "all_caps"),
        ("on-g", 1, "fragment"),
        ("ge-ǣ", 1, "fragment"),
        (unicodedata.normalize("NFD", "ge-ǣ"), 1, "fragment"),
        ("Cf", 1, "stoplist"),
        ("Ps", 1, "stoplist"),
        ("v", 1, "stoplist"),
        ("zzz", 3, "frequent"),
        ("zzz", 2, None),
        ("tiolung", 1, None),
        ("aa", 1, None),  # a real short word (variant of ā)
        ("Æ", 1, None),  # one capital letter is not all-caps text
        ("ā-ǣlan", 1, None),  # a one-letter prefix is not a fragment
        ("Lindesīge", 1, None),
    ],
)
def test_reject_reason(spelling: str, headword_count: int, expected: str | None):
    assert FILTER.reject_reason(spelling, headword_count) == expected


@pytest.mark.parametrize(
    ("key", "headword_key", "expected"),
    [
        ("aa", "a", True),
        ("tiolung", "tilung", True),
        ("senu", "seonu", True),
        ("lindessige", "lindesse", True),
        ("with", "landbygen", False),
        ("classes", "stregdan", False),
        ("bacest", "bacan", False),  # a real inflected form: reported, not imported
        ("seotu", "seoþþan", False),
        # Dialect and scribal spellings: the same word with other vowel digraphs.
        ("wirþe", "weorþ", True),
        ("byric", "beorc", True),
        ("gylpe", "gilpan", True),
        ("trywþ", "treowþe", True),
        ("tihian", "teohhian", True),
        ("ys", "eom", True),  # Anglian "is" under the verb "to be"
        ("mean", "stregdan", False),
    ],
)
def test_within_gate(key: str, headword_key: str, expected: bool):
    assert BTVariantFilter.within_gate(key, headword_key) is expected


def test_load_ignores_comments_blanks_and_bom(tmp_path: Path):
    path = tmp_path / "stoplist.txt"
    path.write_text("﻿# sigla\n\nCf  # see also\nvii\n", encoding="utf-8")

    loaded = BTVariantFilter.load(path)

    assert loaded.reject_reason("cf", 1) == "stoplist"
    assert loaded.reject_reason("VII", 1) == "all_caps"
    assert loaded.reject_reason("vii", 1) == "stoplist"


def test_missing_stoplist_logs_a_warning(tmp_path: Path):
    missing = tmp_path / "missing.txt"
    # Patch the module logger: caplog depends on logging config other tests change.
    with patch("wyrdcraeft.services.variant_filter.LOGGER") as logger:
        loaded = BTVariantFilter.load(missing)

    logger.warning.assert_called_once()
    assert missing in logger.warning.call_args.args
    assert loaded.reject_reason("v", 1) is None


def test_packaged_stoplist_has_the_sigla_and_numerals():
    loaded = BTVariantFilter.load(DEFAULT_VARIANT_STOPLIST_PATH)

    for token in [
        "v",
        "Cf",
        "ii",
        "Ps",
        "Rdr",
        "Wrt",
        "Voc",
        "Gl",
        "xiv",
        "axa",
        "acl",
        "afn",
    ]:
        assert loaded.reject_reason(token, 1) in {"stoplist", "all_caps"}, token
    assert loaded.reject_reason("aa", 1) is None
    assert loaded.reject_reason("tiolung", 1) is None
