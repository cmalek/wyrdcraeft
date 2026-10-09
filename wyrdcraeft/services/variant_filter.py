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
#: Spellings Old English dialects and scribes interchange, folded before comparing.
DIALECT_DIGRAPH_RE: Final[re.Pattern[str]] = re.compile(r"ea|eo|ie|io|ia|ei|ey|iu|eu")
#: Single-letter correspondences folded before comparing (``y`` as ``i``, ...).
DIALECT_LETTERS: Final[dict[str, str]] = {
    "æ": "e",
    "y": "i",
    "k": "c",
    "v": "f",
    "w": "u",
}
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

        The test runs on the keys as written, then again after the dialect
        correspondences are folded together (``wirþe`` against ``weorþ``).

        Args:
            key: Normalized key of the variant.
            headword_key: Normalized key of the headword it is listed under.

        Returns:
            ``True`` when the edit distance, plain or dialect-folded, is at most
            ``max(2, len(headword_key) // 3)``.

        """
        folded_key = BTVariantFilter._fold_dialects(key)
        folded_headword = BTVariantFilter._fold_dialects(headword_key)
        return any(
            BTVariantFilter._edit_distance(a, b)
            <= max(MIN_GATE_DISTANCE, len(b) // GATE_LENGTH_DIVISOR)
            for a, b in ((key, headword_key), (folded_key, folded_headword))
        )

    @staticmethod
    def _fold_dialects(key: str) -> str:
        """
        Collapse spellings that dialects and scribes interchange.

        Args:
            key: Normalized key.

        Returns:
            The key with diphthong digraphs reduced to ``e``, ``y`` read as
            ``i`` and so on, and doubled letters collapsed.

        """
        folded = DIALECT_DIGRAPH_RE.sub("e", key)
        folded = "".join(DIALECT_LETTERS.get(char, char) for char in folded)
        return re.sub(r"(.)\1+", r"\1", folded)

    @staticmethod
    def _edit_distance(left: str, right: str) -> int:
        """
        Count the single-letter edits between two strings.

        Args:
            left: One string.
            right: The other string.

        Returns:
            The Levenshtein distance.

        """
        previous = list(range(len(right) + 1))
        for i, char in enumerate(left, start=1):
            current = [i]
            for j, other in enumerate(right, start=1):
                current.append(
                    min(
                        previous[j] + 1,
                        current[j - 1] + 1,
                        previous[j - 1] + (char != other),
                    )
                )
            previous = current
        return previous[-1]
