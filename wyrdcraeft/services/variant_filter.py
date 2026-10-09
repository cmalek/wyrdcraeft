"""Junk filter and similarity gate for Bosworth-Toller variant spellings."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Module logger.
LOGGER = logging.getLogger(__name__)
#: Packaged, hand-edited list of citation sigla and numerals to reject.
DEFAULT_VARIANT_STOPLIST_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1]
    / "etc"
    / "diacritic"
    / "bt_variant_stoplist.txt"
)
#: A key listed as a variant under this many headwords is a siglum, not a word.
FREQUENT_HEADWORD_COUNT: Final[int] = 3
#: A hyphenated token ending in one letter is a truncated fragment.
FRAGMENT_RE: Final[re.Pattern[str]] = re.compile(r"-\w$")
#: Edit distance always allowed between a variant and its headword.
MIN_GATE_DISTANCE: Final[int] = 2
#: The gate also allows one edit per this many letters of the headword key.
GATE_LENGTH_DIVISOR: Final[int] = 3
#: Fewest letters for a token to count as ALL-CAPS text.
MIN_ALL_CAPS_LETTERS: Final[int] = 2


class BTVariantFilter:
    """
    Decide which parser "variants" are real spellings of their headword.

    Args:
        stoplist: Tokens to reject, matched ignoring case.

    """

    def __init__(self, stoplist: Iterable[str]):
        """
        Store the stoplist.

        Args:
            stoplist: Tokens to reject, matched ignoring case.

        """
        #: Lowercase tokens that are never imported.
        self.stoplist = frozenset(token.strip().lower() for token in stoplist)

    @classmethod
    def load(cls, path: Path = DEFAULT_VARIANT_STOPLIST_PATH) -> BTVariantFilter:
        """
        Read a stoplist file.

        A ``#`` starts a comment anywhere on a line. A missing file logs a
        warning and gives an empty stoplist.

        Args:
            path: Stoplist file, one token per line.

        Returns:
            The loaded filter.

        """
        if not path.exists():
            LOGGER.warning("Variant stoplist missing: %s", path)
            return cls([])
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        entries = (line.split("#", maxsplit=1)[0] for line in lines)
        return cls(entry for entry in entries if entry.strip())

    def reject_reason(self, spelling: str, headword_count: int) -> str | None:
        """
        Say why a variant spelling is junk, if it is.

        Args:
            spelling: The variant exactly as Bosworth-Toller prints it.
            headword_count: How many different headwords list this key as a variant.

        Returns:
            ``all_caps``, ``fragment``, ``stoplist`` or ``frequent`` (checked in
            that order), or ``None`` when the spelling passes.

        """
        text = unicodedata.normalize("NFC", spelling)
        letters = sum(1 for char in text if char.isalpha())
        if letters >= MIN_ALL_CAPS_LETTERS and text.isupper():
            return "all_caps"
        if FRAGMENT_RE.search(text):
            return "fragment"
        if text.lower() in self.stoplist:
            return "stoplist"
        if headword_count >= FREQUENT_HEADWORD_COUNT:
            return "frequent"
        return None

    @staticmethod
    def within_gate(key: str, headword_key: str) -> bool:
        """
        Tell whether a variant is a spelling of its own headword.

        Args:
            key: Normalized key of the variant.
            headword_key: Normalized key of the headword it is listed under.

        Returns:
            ``True`` when the edit distance is at most
            ``max(2, len(headword_key) // 3)``.

        """
        limit = max(MIN_GATE_DISTANCE, len(headword_key) // GATE_LENGTH_DIVISOR)
        previous = list(range(len(headword_key) + 1))
        for i, char in enumerate(key, start=1):
            current = [i]
            for j, other in enumerate(headword_key, start=1):
                current.append(
                    min(
                        previous[j] + 1,
                        current[j - 1] + 1,
                        previous[j - 1] + (char != other),
                    )
                )
            previous = current
        return previous[-1] <= limit
