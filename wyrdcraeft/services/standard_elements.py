"""Standard spellings for prefixes and compound elements (ADR 0019)."""

from __future__ import annotations

import logging
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Module logger.
LOGGER = logging.getLogger(__name__)

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
                self._add(self.prefixes, text[:-1], text)
            elif text:
                self._add(self.compounds, text, text)

    def _add(self, table: dict[str, str], spelling: str, entry: str) -> None:
        """
        Record one standard spelling, warning when it replaces a different one.

        Side Effects:
            Logs a warning on a conflicting duplicate; the later entry wins.

        Args:
            table: ``prefixes`` or ``compounds``.
            spelling: The standard spelling without a trailing hyphen.
            entry: The entry as written, for the warning.

        """
        key = self._key(spelling)
        if table.get(key, spelling) != spelling:
            LOGGER.warning(
                "Standard element %r conflicts with %r; using the later one",
                entry,
                table[key],
            )
        table[key] = spelling

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

        Side Effects:
            Logs a warning when the file is missing.

        Args:
            path: File with one entry per line; ``#`` starts a comment anywhere
                on a line.

        Returns:
            The loaded elements; empty when the file is missing.

        """
        if not path.exists():
            LOGGER.warning("Standard element list missing: %s", path)
            return cls([])
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        entries = (line.split("#", maxsplit=1)[0] for line in lines)
        return cls(entry for entry in entries if entry.strip())

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
