"""Standard spellings for prefixes and compound elements (ADR 0019)."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Packaged, hand-edited list of standard element spellings.
DEFAULT_STANDARD_ELEMENTS_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "etc" / "diacritic" / "standard_elements.txt"
)

#: A form needs at least this many hyphen segments for an element to count.
MIN_SEGMENTS: Final[int] = 2


class StandardElements:
    """
    Rewrite the marks of listed prefixes and compound elements in index forms.

    An element counts only where the form writes a hyphen after it (a prefix
    entry such as ``for-``, first segment only) or around it (a compound entry
    such as ``bonde``). A form with no hyphen is never changed.

    Args:
        entries: Standard spellings; a trailing hyphen marks a prefix.

    """

    def __init__(self, entries: Iterable[str]):
        """
        Index the entries by their unmarked key.

        Args:
            entries: Standard spellings; a trailing hyphen marks a prefix.

        """
        #: Unmarked key -> standard spelling, for first-segment prefixes.
        self.prefixes: dict[str, str] = {}
        #: Unmarked key -> standard spelling, for any hyphen-bounded segment.
        self.compounds: dict[str, str] = {}
        for entry in entries:
            text = unicodedata.normalize("NFC", entry.strip())
            if text.endswith("-"):
                self.prefixes[self._key(text[:-1])] = text[:-1]
            elif text:
                self.compounds[self._key(text)] = text

    @staticmethod
    def _key(text: str) -> str:
        """
        Drop case, diacritics and eth/thorn.

        Args:
            text: One hyphen segment.

        Returns:
            Lowercase text without combining marks, with ``ð`` as ``þ``.

        """
        decomposed = unicodedata.normalize("NFD", text.lower())
        stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
        return stripped.replace("ð", "þ")

    @classmethod
    def load(cls, path: Path = DEFAULT_STANDARD_ELEMENTS_PATH) -> StandardElements:
        """
        Read a standard-element file.

        Args:
            path: File with one entry per line; blank lines and ``#`` lines skipped.

        Returns:
            The loaded elements.

        """
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        return cls(
            line for line in lines if line.strip() and not line.lstrip().startswith("#")
        )

    def standardize(self, form: str) -> str:
        """
        Replace the marks of listed elements in an index form.

        Args:
            form: An index display form.

        Returns:
            The form with listed elements spelled as their standard form.

        """
        segments = form.split("-")
        if len(segments) < MIN_SEGMENTS:
            return form
        out: list[str] = []
        for position, segment in enumerate(segments):
            key = self._key(segment)
            standard = self.compounds.get(key)
            if position == 0:
                standard = self.prefixes.get(key, standard)
            out.append(segment if standard is None else standard)
        return "-".join(out)
