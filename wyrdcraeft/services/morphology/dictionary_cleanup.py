"""Normalize and deduplicate the morphology dictionary TSV source file."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from wyrdcraeft.services.morphology.text_utils import OENormalizer

if TYPE_CHECKING:
    from pathlib import Path

#: Sentinel values in column 2 that must not be lowercased.
_PRESERVE_CASE_COL2 = frozenset({"NULL"})


@dataclass(frozen=True)
class MorphologyDictionaryCleanupResult:
    """Summary of one morphology dictionary cleanup run."""

    #: Path to the timestamped backup copy created before mutation.
    backup_path: Path
    #: Number of non-empty source rows read.
    rows_read: int
    #: Number of rows whose column-2 lemma title was lowercased.
    lowercase_changes: int
    #: Number of rows whose column-2 BT diphthong spelling was corrected.
    diphthong_fixes: int
    #: Number of duplicate rows removed after normalization.
    duplicates_removed: int
    #: Number of rows written back to the dictionary file.
    rows_written: int


class MorphologyDictionaryCleaner:
    """
    Backup, normalize, and deduplicate one morphology dictionary TSV file.

    Note:
        Column-2 lemma titles are normalized with Bosworth-Toller diphthong
        long-mark correction and all-uppercase lowercasing in line with
        morphology loader behavior from ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, BT-style ``eā``,
        ``eō``, ``eī``, and ``iē`` sequences become ``ēa``, ``ēo``, ``ēi``,
        and ``īe`` before duplicate rows sharing the same non-id columns are
        collapsed. Part-of-speech scope: ``cross-PoS``.

    Args:
        dictionary_path: Path to ``dict_adj-vb-part-num-adv-noun.txt``.
        now: Optional timestamp override for deterministic backup naming.

    """

    def __init__(
        self,
        dictionary_path: Path,
        *,
        now: datetime | None = None,
    ) -> None:
        """
        Bind one morphology dictionary source file for cleanup.

        Args:
            dictionary_path: Path to ``dict_adj-vb-part-num-adv-noun.txt``.

        Keyword Args:
            now: Optional timestamp override for deterministic backup naming.

        """
        #: Path to the morphology dictionary TSV being cleaned.
        self._dictionary_path = dictionary_path.expanduser().resolve()
        #: Optional timestamp override for deterministic backup naming.
        self._now = now

    def run(self) -> MorphologyDictionaryCleanupResult:
        """
        Backup the dictionary file, normalize column 2, and remove duplicates.

        Returns:
            Cleanup counters and the backup path.

        Raises:
            FileNotFoundError: The dictionary source file does not exist.

        Side Effects:
            Writes a timestamped backup sibling and overwrites the source file.

        """
        if not self._dictionary_path.is_file():
            msg = f"Dictionary file not found: {self._dictionary_path}"
            raise FileNotFoundError(msg)

        backup_path = self._create_backup()
        raw_lines = self._dictionary_path.read_text(encoding="utf-8").splitlines()
        rows_read = 0
        lowercase_changes = 0
        diphthong_fixes = 0
        normalized_rows: list[list[str]] = []
        seen_keys: set[tuple[str, ...]] = set()
        duplicates_removed = 0

        for raw_line in raw_lines:
            if not raw_line:
                continue
            rows_read += 1
            columns = raw_line.split("\t")
            if len(columns) > 1 and columns[1] not in _PRESERVE_CASE_COL2:
                if self._should_lowercase_col2(columns[1]):
                    columns[1] = columns[1].lower()
                    lowercase_changes += 1
                normalized_title = OENormalizer.normalize_bt_display_spelling(
                    columns[1]
                )
                if normalized_title != columns[1]:
                    columns[1] = normalized_title
                    diphthong_fixes += 1

            dedupe_key = tuple(columns[1:])
            if dedupe_key in seen_keys:
                duplicates_removed += 1
                continue
            seen_keys.add(dedupe_key)
            normalized_rows.append(columns)

        output_text = "\n".join("\t".join(columns) for columns in normalized_rows)
        if output_text:
            output_text += "\n"
        self._dictionary_path.write_text(output_text, encoding="utf-8")

        return MorphologyDictionaryCleanupResult(
            backup_path=backup_path,
            rows_read=rows_read,
            lowercase_changes=lowercase_changes,
            diphthong_fixes=diphthong_fixes,
            duplicates_removed=duplicates_removed,
            rows_written=len(normalized_rows),
        )

    def _create_backup(self) -> Path:
        """
        Copy the dictionary file to a timestamped sibling backup.

        Returns:
            Path to the newly created backup file.

        Side Effects:
            Writes one ``*.bak`` copy beside the dictionary source file.

        """
        timestamp = (self._now or datetime.now(UTC)).strftime("%Y%m%d-%H%M%S")
        backup_path = self._dictionary_path.with_name(
            f"{self._dictionary_path.name}.{timestamp}.bak"
        )
        shutil.copy2(self._dictionary_path, backup_path)
        return backup_path

    @staticmethod
    def _should_lowercase_col2(value: str) -> bool:
        """
        Return whether one column-2 lemma title should be lowercased.

        Args:
            value: Raw column-2 value from the dictionary TSV.

        Returns:
            ``True`` when every alphabetic character is uppercase, punctuation
            is ignored, and the value is not a preserved sentinel such as
            ``NULL``.

        """
        if value in _PRESERVE_CASE_COL2:
            return False
        letters = [character for character in value if character.isalpha()]
        if not letters:
            return False
        return all(character.isupper() for character in letters)
