"""Lowercase all-uppercase Bosworth-Toller headwords in oe_bt.txt."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from wyrdcraeft.services.markup import BOLD_HEADWORD_RE

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class BTSourceHeadwordCleanupResult:
    """Summary of one Bosworth-Toller source headword cleanup run."""

    #: Path to the timestamped backup copy created before mutation.
    backup_path: Path
    #: Number of source lines read.
    lines_read: int
    #: Number of lines whose first bold headword was lowercased.
    lowercase_changes: int
    #: Number of lines written back to the source file.
    lines_written: int


class BTSourceHeadwordCleaner:
    """
    Backup and lowercase all-uppercase first headwords in one oe_bt.txt file.

    Note:
        Only the first ``<B>…</B>`` capture on each line is considered, matching
        Bosworth-Toller parser headword extraction. Mixed-case captures such as
        ``Dōn`` or ``Abban dūn`` are left unchanged. Part-of-speech scope:
        ``cross-PoS``.

    Args:
        source_path: Path to ``oe_bt.txt``.
        now: Optional timestamp override for deterministic backup naming.

    """

    def __init__(
        self,
        source_path: Path,
        *,
        now: datetime | None = None,
    ) -> None:
        """
        Bind one Bosworth-Toller source file for headword cleanup.

        Args:
            source_path: Path to ``oe_bt.txt``.

        Keyword Args:
            now: Optional timestamp override for deterministic backup naming.

        """
        #: Path to the Bosworth-Toller source file being cleaned.
        self._source_path = source_path.expanduser().resolve()
        #: Optional timestamp override for deterministic backup naming.
        self._now = now

    def run(self) -> BTSourceHeadwordCleanupResult:
        """
        Backup the source file and lowercase eligible first headwords.

        Returns:
            Cleanup counters and the backup path.

        Raises:
            FileNotFoundError: The source file does not exist.

        Side Effects:
            Writes a timestamped backup sibling and overwrites the source file.

        """
        if not self._source_path.is_file():
            msg = f"Dictionary source file not found: {self._source_path}"
            raise FileNotFoundError(msg)

        backup_path = self._create_backup()
        raw_lines = self._source_path.read_text(encoding="utf-8").splitlines()
        lowercase_changes = 0
        output_lines: list[str] = []

        for raw_line in raw_lines:
            new_line, changed = self._lowercase_first_headword(raw_line)
            if changed:
                lowercase_changes += 1
            output_lines.append(new_line)

        output_text = "\n".join(output_lines)
        if output_text:
            output_text += "\n"
        self._source_path.write_text(output_text, encoding="utf-8")

        return BTSourceHeadwordCleanupResult(
            backup_path=backup_path,
            lines_read=len(raw_lines),
            lowercase_changes=lowercase_changes,
            lines_written=len(output_lines),
        )

    def _create_backup(self) -> Path:
        """
        Copy the source file to a timestamped sibling backup.

        Returns:
            Path to the newly created backup file.

        Side Effects:
            Writes one ``*.bak`` copy beside the source file.

        """
        timestamp = (self._now or datetime.now(UTC)).strftime("%Y%m%d-%H%M%S")
        backup_path = self._source_path.with_name(
            f"{self._source_path.name}.{timestamp}.bak"
        )
        shutil.copy2(self._source_path, backup_path)
        return backup_path

    @staticmethod
    def _lowercase_first_headword(raw_line: str) -> tuple[str, bool]:
        """
        Lowercase the first bold headword capture when fully uppercase.

        Args:
            raw_line: One raw ``oe_bt.txt`` line.

        Returns:
            Updated line text and whether the first bold capture changed.

        """
        match = BOLD_HEADWORD_RE.search(raw_line)
        if match is None:
            return raw_line, False
        capture = match.group(1)
        if not BTSourceHeadwordCleaner._should_lowercase_headword(capture):
            return raw_line, False
        lowered = capture.lower()
        if lowered == capture:
            return raw_line, False
        new_line = raw_line[: match.start(1)] + lowered + raw_line[match.end(1) :]
        return new_line, True

    @staticmethod
    def _should_lowercase_headword(value: str) -> bool:
        """
        Return whether one bold headword capture should be lowercased.

        Args:
            value: Raw text from the first ``<B>…</B>`` match.

        Returns:
            ``True`` when every alphabetic character is uppercase and punctuation
            is ignored.

        """
        letters = [character for character in value if character.isalpha()]
        if not letters:
            return False
        return all(character.isupper() for character in letters)
