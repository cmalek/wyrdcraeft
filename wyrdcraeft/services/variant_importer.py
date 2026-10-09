"""Import Bosworth-Toller variant spellings into the macron index (ADR 0017)."""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from ..models.variant_import import (
    CollisionRow,
    ConflictingNewKey,
    VariantImportReport,
    VariantRow,
)
from .dictionary.line_parser import BTLineParser
from .markup import DiacriticTransfer, normalize_old_english
from .morphology.text_utils import OENormalizer
from .standard_elements import StandardElements
from .variant_filter import BTVariantFilter

if TYPE_CHECKING:
    from pathlib import Path

    from ..models.diacritics import MacronIndexPayload


class BTVariantImporter:
    """
    Decide which Bosworth-Toller variants become their own macron index entries.

    The importer never changes an existing key (ADR 0017 decision 3): it adds
    keys that are absent from ``unique`` and ``ambiguous`` and reports the rest.

    Args:
        parser: Line parser used for raw variants.
        variant_filter: Junk filter and similarity gate.
        standard_elements: Standard element list applied before comparing marks.

    """

    def __init__(
        self,
        parser: BTLineParser | None = None,
        variant_filter: BTVariantFilter | None = None,
        standard_elements: StandardElements | None = None,
    ):
        """
        Initialize the importer's collaborators.

        Args:
            parser: Line parser used for raw variants.
            variant_filter: Junk filter and similarity gate; packaged stoplist
                when omitted.
            standard_elements: Standard element list; packaged list when omitted.

        """
        #: Parser for raw (un-normalized) headwords and variants.
        self.parser = parser or BTLineParser()
        #: Junk filter and similarity gate.
        self.variant_filter = variant_filter or BTVariantFilter.load()
        #: Standard elements applied before comparing marks.
        self.standard_elements = standard_elements or StandardElements.load()

    def build_report(
        self, source_path: Path, payload: MacronIndexPayload
    ) -> VariantImportReport:
        """
        Work out what importing the variants of a source file would do.

        Args:
            source_path: Bosworth-Toller ``oe_bt.txt``.
            payload: The macron index; not modified.

        Returns:
            The additions, the collisions and conflicts left for review, the
            below-gate variants, and counts.

        """
        rows = self._read_rows(source_path)
        counts: Counter[str] = Counter(candidates=len(rows))
        report = VariantImportReport()
        kept = self._screen(rows, payload, report, counts)
        new_by_key = self._classify_existing(kept, payload, report, counts)
        self._classify_new(new_by_key, report, counts)
        report.counts = dict(counts)
        return report

    def apply(self, report: VariantImportReport, payload: MacronIndexPayload) -> int:
        """
        Add the report's new keys to the index payload.

        Side Effects:
            Adds entries to ``payload.unique``; existing keys are never replaced.

        Args:
            report: Report from :meth:`build_report` for the same payload.
            payload: The macron index to extend.

        Returns:
            How many keys were added.

        """
        added = 0
        for key, form in report.additions.items():
            if key not in payload.unique and key not in payload.ambiguous:
                payload.unique[key] = form
                added += 1
        return added

    def _read_rows(self, source_path: Path) -> list[VariantRow]:
        """
        Read every variant of every parseable line.

        Args:
            source_path: Bosworth-Toller ``oe_bt.txt``.

        Returns:
            One row per variant, in source order.

        """
        rows: list[VariantRow] = []
        with source_path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                parsed = self.parser.raw_variants(line.rstrip("\r\n"))
                if parsed is None:
                    continue
                headword, variants = parsed
                for spelling in variants:
                    key = normalize_old_english(spelling)
                    if key:
                        rows.append(
                            VariantRow(
                                spelling=self._index_style(spelling),
                                key=key,
                                headword=headword,
                                line_no=line_no,
                            )
                        )
        return rows

    @staticmethod
    def _index_style(spelling: str) -> str:
        """
        Put a diphthong's macron on its first vowel, as the index writes it.

        Args:
            spelling: Variant as BT prints it (``dreōganne``).

        Returns:
            The NFC spelling in index style (``drēoganne``).

        """
        return unicodedata.normalize(
            "NFC", OENormalizer.normalize_bt_display_spelling(spelling)
        )

    def _screen(
        self,
        rows: list[VariantRow],
        payload: MacronIndexPayload,
        report: VariantImportReport,
        counts: Counter[str],
    ) -> list[VariantRow]:
        """
        Drop junk, set aside variants below the similarity gate, de-duplicate.

        Side Effects:
            Appends to ``report.below_gate`` and updates ``counts``.

        Args:
            rows: All variants.
            payload: The macron index (to skip below-gate variants of known keys).
            report: Report receiving the below-gate rows.
            counts: Outcome counters.

        Returns:
            The variants that passed, unique by key and lowercase spelling.

        """
        headwords: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            headwords[row.key].add(row.headword.lower())
        kept: list[VariantRow] = []
        seen: set[tuple[str, str]] = set()
        for row in rows:
            reason = self.variant_filter.reject_reason(
                row.spelling, len(headwords[row.key])
            )
            if reason is not None:
                counts[f"rejected_{reason}"] += 1
                continue
            headword_key = normalize_old_english(row.headword) or ""
            if not self.variant_filter.within_gate(row.key, headword_key):
                if row.key not in payload.unique and row.key not in payload.ambiguous:
                    report.below_gate.append(row)
                continue
            identity = (row.key, row.spelling.lower())
            if identity not in seen:
                seen.add(identity)
                kept.append(row)
        return kept

    def _classify_existing(
        self,
        kept: list[VariantRow],
        payload: MacronIndexPayload,
        report: VariantImportReport,
        counts: Counter[str],
    ) -> dict[str, list[VariantRow]]:
        """
        Compare variants of known keys with the index; collect the new keys.

        Side Effects:
            Appends to ``report.collisions`` and updates ``counts``.

        Args:
            kept: Screened variants.
            payload: The macron index.
            report: Report receiving collisions.
            counts: Outcome counters.

        Returns:
            Variants of keys that are in neither ``unique`` nor ``ambiguous``,
            grouped by key.

        """
        new_by_key: dict[str, list[VariantRow]] = defaultdict(list)
        for row in kept:
            if row.key in payload.ambiguous_completed:
                counts["skipped_completed"] += 1
            elif row.key in payload.ambiguous:
                self._compare(row, payload.ambiguous[row.key], report, counts)
            elif row.key in payload.unique:
                self._compare(row, [payload.unique[row.key]], report, counts)
            else:
                new_by_key[row.key].append(row)
        return new_by_key

    def _compare(
        self,
        row: VariantRow,
        existing: list[str],
        report: VariantImportReport,
        counts: Counter[str],
    ) -> None:
        """
        Skip a variant that adds nothing, or list it for review.

        Side Effects:
            Updates ``counts`` or appends to ``report.collisions``.

        Args:
            row: The colliding variant.
            existing: Forms already in the index for its key.
            report: Report receiving collisions.
            counts: Outcome counters.

        """
        variant = row.spelling.lower()
        relations = [
            DiacriticTransfer.mark_relation(form, variant, self.standard_elements)
            for form in existing
        ]
        if "same" in relations:
            outcome = "same_marks" if len(existing) == 1 else "matches_option"
            counts[f"skipped_{outcome}"] += 1
        elif len(existing) == 1 and relations[0] == "fewer":
            counts["skipped_fewer_marks"] += 1
        else:
            if len(existing) > 1:
                reason = "new_pattern"
            elif relations[0] == "more":
                reason = "more_marks"
            else:
                reason = "conflicting_marks"
            report.collisions.append(
                CollisionRow(variant=row, existing=list(existing), reason=reason)
            )

    def _classify_new(
        self,
        new_by_key: dict[str, list[VariantRow]],
        report: VariantImportReport,
        counts: Counter[str],
    ) -> None:
        """
        Add each new key whose variants agree on marks; list the rest.

        Side Effects:
            Fills ``report.additions`` and ``report.conflicting_new``; updates
            ``counts["added"]``.

        Args:
            new_by_key: Variants of absent keys, grouped by key.
            report: Report receiving additions and conflicts.
            counts: Outcome counters.

        """
        for key, rows in new_by_key.items():
            patterns = {
                DiacriticTransfer.mark_pattern(
                    self.standard_elements.standardize(row.spelling.lower())
                )
                for row in rows
            }
            if len(patterns) == 1:
                report.additions[key] = rows[0].spelling.lower()
                counts["added"] += 1
            else:
                report.conflicting_new.append(ConflictingNewKey(key=key, variants=rows))
