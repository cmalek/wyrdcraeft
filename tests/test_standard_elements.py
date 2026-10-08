from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.standard_elements import (
    DEFAULT_STANDARD_ELEMENTS_PATH,
    StandardElements,
)

if TYPE_CHECKING:
    from pathlib import Path

ELEMENTS = StandardElements(
    ["a-", "for-", "fore-", "ge-", "bonde", "hīrēd-", "bēacen-", "ōþ-"]
)


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        ("ā-bacan", "a-bacan"),
        ("fōr-beran", "for-beran"),
        ("fōre-beran", "fore-beran"),
        ("gē-bindan", "ge-bindan"),
        ("ge-bēd-man", "ge-bēd-man"),
        ("gē-bēd-man", "ge-bēd-man"),
        ("hūs-bōnde", "hūs-bonde"),
        ("bōnde-land", "bonde-land"),
        ("hīred-mann", "hīrēd-mann"),
        ("beacen-fȳr", "bēacen-fȳr"),
        ("oð-feolan", "ōþ-feolan"),
        # No BT hyphen after the element: never standardized.
        ("gēan", "gēan"),
        ("fōr", "fōr"),
        ("fōrþ", "fōrþ"),
        ("bōnde", "bōnde"),
        ("gēon", "gēon"),
        # Different element, same start.
        ("foran-weard", "foran-weard"),
        ("gebed-tīd", "gebed-tīd"),
        # A prefix entry only matches the first segment.
        ("hūs-fōr-beran", "hūs-fōr-beran"),
    ],
)
def test_standardize(form: str, expected: str):
    assert ELEMENTS.standardize(form) == expected


def test_load_ignores_comments_blanks_bom_and_duplicates(tmp_path: Path):
    path = tmp_path / "elements.txt"
    path.write_text("﻿# editorial\n\nfor-\nfor-\nbonde\n", encoding="utf-8")

    elements = StandardElements.load(path)

    assert elements.standardize("fōr-beran") == "for-beran"
    assert elements.standardize("hūs-bōnde") == "hūs-bonde"


def test_packaged_file_lists_the_adr_elements():
    elements = StandardElements.load(DEFAULT_STANDARD_ELEMENTS_PATH)

    assert elements.standardize("ā-bacan") == "a-bacan"
    assert elements.standardize("fōre-beran") == "fore-beran"
    assert elements.standardize("hīred-mann") == "hīrēd-mann"
    assert elements.standardize("ōþ-feolan") == "ōþ-feolan"
    assert elements.standardize("gebed-tīd") == "gebed-tīd"
