"""Phase 04 editorial merger for Bosworth-Toller dictionary entries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from ...models.dictionary import (
    BTConsolidatedEntry,
    BTEditorialOp,
    BTLineKind,
    BTPos,
    BTSense,
)
from ..markup import normalize_morphology_title, normalize_old_english
from .target_resolver import BTTargetResolver

if TYPE_CHECKING:
    from .line_parser import ParsedBTLine

#: Strips all HTML tags.
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")

#: Collapses whitespace.
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")

#: ``for all but X`` pattern in Substitute lines.
_FOR_ALL_BUT_RE: Final[re.Pattern[str]] = re.compile(
    r"for all but\s+(.+?)(?:\s*$|:)",
    re.IGNORECASE,
)

#: ``Substitute the following for X in Dict`` full pattern.
_SUBSTITUTE_FOR_X_RE: Final[re.Pattern[str]] = re.compile(
    r"substitute the following for\s+(.+?)\s+in\s+Dict",
    re.IGNORECASE,
)

#: ``Substitute the following:`` whole-entry replacement.
_SUBSTITUTE_FOLLOWING_RE: Final[re.Pattern[str]] = re.compile(
    r"substitute the following[:\s]",
    re.IGNORECASE,
)

#: ``Substitute:`` followed by a sense label (e.g. ``Substitute: p. de …``).
_SUBSTITUTE_SENSE_RE: Final[re.Pattern[str]] = re.compile(
    r"substitute:\s*([IVXivxA-Z][^:]*?)(?:\s*$|:--)",
    re.IGNORECASE,
)

#: ``v.`` / ``vide`` cross-reference target extractor.
_CROSS_REF_TARGET_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:v\.|vide)\s+<B>(.*?)</B>|(?:v\.|vide)\s+([\w\-ā-ū]+)",
    re.IGNORECASE,
)

#: ``Dele last passage`` or ``Dele bracket`` pattern (scoped dele).
_DELE_SCOPE_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>\s*Dele\b([^<]*)</I>",
    re.IGNORECASE,
)


@dataclass
class BTEditRecord:
    """
    Audit record for one editorial operation applied during entry consolidation.

    Suitable for storage in a ``bt_edit_log`` SQLite table in later phases.

    Attributes:
        op: The editorial operation kind.
        source_line_no: One-based source line number that triggered this operation.
        target_norm_key: Normalised lookup key of the entry being modified.
        target_pos: Part of speech of the entry being modified.
        scope: Human-readable description of what was affected (``all_senses``,
            ``sense_label:I``, ``for_X_in_Dict``, etc.).
        applied: Whether the operation was actually applied or skipped.
        note: Additional diagnostic text.

    """

    #: Editorial operation kind.
    op: BTEditorialOp
    #: Source file line number.
    source_line_no: int
    #: Norm key of the modified entry.
    target_norm_key: str
    #: POS of the modified entry.
    target_pos: BTPos
    #: Scope description for audit.
    scope: str
    #: Whether the op was applied.
    applied: bool
    #: Diagnostic note.
    note: str = ""


def _plain(text: str) -> str:
    """
    Strip HTML tags and collapse whitespace from *text*.

    Args:
        text: Input HTML string.

    Returns:
        Plain-text string with normalised whitespace.

    """
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


class BTEditorialMerger:
    """
    Merge a stream of :class:`~wyrdcraeft.services.dictionary.line_parser.ParsedBTLine`
    records into :class:`~wyrdcraeft.models.dictionary.BTConsolidatedEntry` objects.

    One consolidated entry is produced per
    ``(normalize_old_english(headword_raw), pos)`` group.
    All Add / Substitute / Dele / Dele+Add editorial operations are applied
    in document order within each group.  No editorial line kinds are exposed to the
    consumer API; only the final merged senses and metadata appear in the output.

    Cross-reference lines (``CROSS_REF``) are appended to the ``see_also`` field of
    the target entry rather than producing standalone lookup records.

    Args:
        resolver: Optional target-resolver collaborator.  A default instance is
            created when not provided.

    """

    def __init__(self, resolver: BTTargetResolver | None = None) -> None:
        """
        Initialise the merger with an optional target resolver collaborator.

        Args:
            resolver: Optional pre-built :class:`BTTargetResolver` instance.

        """
        #: Target-resolver collaborator.
        self.resolver: BTTargetResolver = resolver or BTTargetResolver()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def merge(
        self, parsed_lines: list[ParsedBTLine]
    ) -> tuple[list[BTConsolidatedEntry], list[BTEditRecord]]:
        """
        Produce one consolidated entry per ``(norm_key, pos)`` group.

        Skipped parsed lines (those with a non-None ``skip_reason``) are silently
        ignored.  Lines whose headword normalises to an empty string are also
        discarded.

        Args:
            parsed_lines: All parsed BT lines to merge; typically sourced from a
                complete pass through ``oe_bt.txt`` or a corpus sample.

        Returns:
            A pair ``(entries, edit_records)`` where *entries* is the ordered list of
            consolidated results and *edit_records* is the audit log.

        """
        groups: dict[tuple[str, BTPos], list[ParsedBTLine]] = {}
        for line in parsed_lines:
            if line.skip_reason is not None:
                continue
            key = self.resolver.merge_key_for_line(line)
            if key is None:
                continue
            groups.setdefault(key, []).append(line)

        # Redistribute editorial-only ``pos=unknown`` groups into their
        # unambiguous MAIN group.  BT supplement lines (DELE, ADD, SUBSTITUTE,
        # DELE_AND_ADD) rarely repeat the POS, so they end up in a separate
        # ``(norm_key, UNKNOWN)`` bucket.  When exactly one non-UNKNOWN group
        # shares the same ``norm_key``, merge the editorial lines there instead.
        self._redistribute_editorial_unknowns(groups)

        entries: list[BTConsolidatedEntry] = []
        audit: list[BTEditRecord] = []

        for (norm_key, pos), group in groups.items():
            entry, records = self._merge_group(norm_key, pos, group, groups)
            if entry is not None:
                entries.append(entry)
            audit.extend(records)

        self._apply_cross_refs(entries, parsed_lines)
        return entries, audit

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    #: Line kinds treated as editorial-only for redistribution purposes.
    _EDITORIAL_KINDS: frozenset[BTLineKind] = frozenset({
        BTLineKind.DELE,
        BTLineKind.ADD,
        BTLineKind.SUBSTITUTE,
        BTLineKind.DELE_AND_ADD,
    })

    def _redistribute_editorial_unknowns(
        self,
        groups: dict[tuple[str, BTPos], list[ParsedBTLine]],
    ) -> None:
        """
        Move editorial-only ``(norm_key, UNKNOWN)`` groups into the one
        unambiguous MAIN group that shares the same *norm_key*.

        BT Supplement lines (``Add:``, ``Dele``, ``Substitute:``) rarely
        repeat the POS, causing them to be bucketed under ``BTPos.UNKNOWN``.
        When exactly one group with a different ``pos`` exists for the same
        *norm_key*, we can safely reassign those editorial lines there.

        Side Effects:
            Modifies *groups* in place; empty buckets that were absorbed are
            deleted from the mapping.

        Args:
            groups: The fully-populated merge-key → lines mapping.

        """
        editorial_unknown_keys = [
            (nk, pos)
            for (nk, pos), lines in groups.items()
            if pos == BTPos.UNKNOWN
            and all(
                ln.raw_line is not None
                and ln.raw_line.kind in self._EDITORIAL_KINDS
                for ln in lines
            )
        ]
        for key in editorial_unknown_keys:
            norm_key, _ = key
            # Collect peer groups with the same norm_key but a known POS.
            peers = [
                (nk, p)
                for (nk, p) in groups
                if nk == norm_key and p != BTPos.UNKNOWN
            ]
            if len(peers) != 1:
                # Zero or multiple peer groups → can't resolve unambiguously.
                continue
            target_key = peers[0]
            groups[target_key].extend(groups.pop(key))

    def _merge_group(  # noqa: PLR0912
        self,
        norm_key: str,
        pos: BTPos,
        group: list[ParsedBTLine],
        all_groups: dict[tuple[str, BTPos], list[ParsedBTLine]],
    ) -> tuple[BTConsolidatedEntry | None, list[BTEditRecord]]:
        """
        Build one consolidated entry from all lines in *group*.

        Lines are sorted by source line number before processing.  The apply order
        within the group is: MAIN first, then SUBSTITUTE, DELE, DELE_AND_ADD, ADD —
        but each category is applied strictly in ascending ``source_line_no`` order.

        Args:
            norm_key: Normalised lookup key for this group.
            pos: Normalised part of speech for this group.
            group: All parsed lines sharing this ``(norm_key, pos)`` key.
            all_groups: Full group mapping used for cross-entry substitute resolution.

        Returns:
            A pair ``(entry, audit_records)`` where *entry* may be ``None`` when the
            group contains no usable MAIN line.

        """
        sorted_lines = sorted(
            group, key=lambda ln: ln.raw_line.line_no if ln.raw_line else 0
        )

        def _of_kind(kind: BTLineKind) -> list[ParsedBTLine]:
            return [
                ln for ln in sorted_lines
                if ln.raw_line and ln.raw_line.kind == kind
            ]

        mains = _of_kind(BTLineKind.MAIN)
        substitutes = _of_kind(BTLineKind.SUBSTITUTE)
        deles = _of_kind(BTLineKind.DELE)
        dele_and_adds = _of_kind(BTLineKind.DELE_AND_ADD)
        adds = _of_kind(BTLineKind.ADD)

        # When no MAIN line is present but SUBSTITUTE lines exist, treat the first
        # SUBSTITUTE as the seed.  This covers the common BT Supplement pattern
        # where an entry appears only as ``Substitute the following:`` with new
        # content, effectively replacing the corresponding old BT main entry.
        if not mains and substitutes:
            seed = substitutes.pop(0)
        elif not mains:
            # Pure DELE-only or ADD-only groups with no MAIN are orphans; skip.
            return None, []
        else:
            seed = mains[0]
        if seed.raw_line is None:
            return None, []

        entry = BTConsolidatedEntry(
            norm_key=norm_key,
            headword_raw=seed.raw_line.headword_raw,
            headword_macronized=seed.headword_macronized,
            normalized_title=normalize_morphology_title(seed.headword_macronized),
            pos=pos,
            genders=list(seed.genders),
            variants=list(seed.variants),
            senses=list(seed.senses),
            etymology=" ".join(seed.etymology_blocks),
            see_also=[],
            source_line_nos=[seed.raw_line.line_no],
        )

        # Merge additional MAIN lines (homograph helpers, variant forms, etc.)
        for ln in mains[1:]:
            if ln.raw_line is None:
                continue
            entry.source_line_nos.append(ln.raw_line.line_no)
            entry.senses.extend(
                s for s in ln.senses if s not in entry.senses
            )
            for v in ln.variants:
                if v not in entry.variants:
                    entry.variants.append(v)
            if not entry.etymology and ln.etymology_blocks:
                entry.etymology = " ".join(ln.etymology_blocks)

        audit: list[BTEditRecord] = []

        for ln in substitutes:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_substitute(entry, ln, all_groups))

        for ln in deles:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_dele(entry, ln))

        for ln in dele_and_adds:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_dele_and_add(entry, ln))

        for ln in adds:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_add(entry, ln))

        return entry, audit

    # ------------------------------------------------------------------
    # Substitute logic
    # ------------------------------------------------------------------

    def _apply_substitute(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        all_groups: dict[tuple[str, BTPos], list[ParsedBTLine]],
    ) -> list[BTEditRecord]:
        """
        Apply one SUBSTITUTE line to an entry or to a cross-entry target.

        Args:
            entry: The entry currently being built for this merge group.
            line: The parsed SUBSTITUTE line.
            all_groups: Full group map for cross-entry resolution.

        Returns:
            Audit records describing what was changed.

        """
        if line.raw_line is None:
            return []
        body = line.raw_line.raw_text
        plain_body = _plain(body)
        records: list[BTEditRecord] = []

        # Check for cross-entry substitute: ``Substitute the following for X in Dict``
        for_x_match = _SUBSTITUTE_FOR_X_RE.search(plain_body)
        if for_x_match:
            target_text = for_x_match.group(1).strip()
            target_norm = normalize_old_english(target_text) or ""
            # Try to find the target entry in any POS group.
            found_target = False
            for k, p in all_groups:
                if k == target_norm:
                    # We can't modify the target entry mid-merge, so record for
                    # deferred application.  At this stage, record the intent.
                    records.append(
                        BTEditRecord(
                            op=BTEditorialOp.SUBSTITUTE,
                            source_line_no=line.raw_line.line_no,
                            target_norm_key=target_norm,
                            target_pos=p,
                            scope=f"for_X_in_Dict:{target_text}",
                            applied=False,
                            note=(
                                "cross-entry substitute deferred;"
                                " target in different group"
                            ),
                        )
                    )
                    found_target = True
            if not found_target:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.SUBSTITUTE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=target_norm,
                        target_pos=entry.pos,
                        scope=f"for_X_in_Dict:{target_text}",
                        applied=False,
                        note="cross-entry target not found in parsed groups",
                    )
                )
            return records

        # ``Substitute the following:`` — replace entire sense list.
        if _SUBSTITUTE_FOLLOWING_RE.search(plain_body):
            if line.senses:
                entry.senses = list(line.senses)
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.SUBSTITUTE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=entry.norm_key,
                        target_pos=entry.pos,
                        scope="all_senses",
                        applied=True,
                    )
                )
            else:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.SUBSTITUTE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=entry.norm_key,
                        target_pos=entry.pos,
                        scope="all_senses",
                        applied=False,
                        note="substitute line has no parsed senses",
                    )
                )
            return records

        # ``Substitute for all but X`` — replace all except pinned labels.
        for_all_but = _FOR_ALL_BUT_RE.search(plain_body)
        if for_all_but:
            pinned_raw = for_all_but.group(1).strip()
            pinned_labels = {
                lbl.strip().rstrip(".")
                for lbl in re.split(r"[,;]", pinned_raw)
                if lbl.strip()
            }
            kept = [s for s in entry.senses if s.sense_label in pinned_labels]
            new_senses = kept + list(line.senses)
            entry.senses = new_senses
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.SUBSTITUTE,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=f"for_all_but:{pinned_raw}",
                    applied=True,
                )
            )
            return records

        # Fallback: treat as whole-entry substitute if senses are available.
        if line.senses:
            entry.senses = list(line.senses)
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.SUBSTITUTE,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope="all_senses_fallback",
                    applied=True,
                )
            )
        return records

    # ------------------------------------------------------------------
    # Dele logic
    # ------------------------------------------------------------------

    def _apply_dele(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
    ) -> list[BTEditRecord]:
        """
        Apply one DELE line to an entry.

        Args:
            entry: The entry to modify.
            line: The parsed DELE line.

        Returns:
            Audit records describing what was removed.

        """
        if line.raw_line is None:
            return []
        body = line.raw_line.raw_text
        records: list[BTEditRecord] = []

        # Bare ``<I>Dele</I>`` with nothing else — suppress standalone sense
        # (mark entry as deprecated / dele-only if no MAIN content remains).
        dele_scope_match = _DELE_SCOPE_RE.search(body)
        if dele_scope_match:
            scope_text = dele_scope_match.group(1).strip()
            if not scope_text:
                # Bare dele: mark all current senses as removed only if the entry
                # has no additional content from other lines.
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.DELE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=entry.norm_key,
                        target_pos=entry.pos,
                        scope="bare_dele",
                        applied=True,
                        note="bare Dele; entry marked deprecated",
                    )
                )
                entry.senses = []
                return records

        # ``Dele A: B: C`` — remove cited labels from sense list.
        if line.dele_refs:
            removed: list[str] = []
            for ref in line.dele_refs:
                ref_norm = ref.strip()
                before = len(entry.senses)
                entry.senses = [
                    s for s in entry.senses
                    if not self._sense_matches_ref(s, ref_norm)
                ]
                if len(entry.senses) < before:
                    removed.append(ref_norm)
            scope = "sense_labels:" + ",".join(removed) if removed else "no_match"
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.DELE,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=scope,
                    applied=bool(removed),
                    note="" if removed else "dele_refs did not match any sense labels",
                )
            )
            return records

        # No recognisable scope — record as no-op.
        records.append(
            BTEditRecord(
                op=BTEditorialOp.DELE,
                source_line_no=line.raw_line.line_no,
                target_norm_key=entry.norm_key,
                target_pos=entry.pos,
                scope="unknown",
                applied=False,
                note="dele line had no recognisable scope",
            )
        )
        return records

    # ------------------------------------------------------------------
    # Dele+Add logic
    # ------------------------------------------------------------------

    def _apply_dele_and_add(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
    ) -> list[BTEditRecord]:
        """
        Apply one DELE_AND_ADD line — first remove, then append.

        Args:
            entry: The entry to modify.
            line: The parsed DELE_AND_ADD line.

        Returns:
            Audit records for both the delete and add passes.

        """
        if line.raw_line is None:
            return []
        records: list[BTEditRecord] = []

        # Delete pass — using dele_refs from the parser.
        if line.dele_refs:
            removed: list[str] = []
            for ref in line.dele_refs:
                ref_norm = ref.strip()
                before = len(entry.senses)
                entry.senses = [
                    s for s in entry.senses
                    if not self._sense_matches_ref(s, ref_norm)
                ]
                if len(entry.senses) < before:
                    removed.append(ref_norm)
            scope = "dele_pass:" + (",".join(removed) if removed else "no_match")
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.DELE_AND_ADD,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=scope,
                    applied=True,
                    note="dele pass of dele_and_add",
                )
            )

        # Add pass — append new senses from this line.
        if line.senses:
            existing_labels = {s.sense_label for s in entry.senses}
            appended = 0
            for sense in line.senses:
                if sense.sense_label not in existing_labels or not sense.sense_label:
                    entry.senses.append(sense)
                    existing_labels.add(sense.sense_label)
                    appended += 1
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.DELE_AND_ADD,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=f"add_pass:{appended}_senses",
                    applied=appended > 0,
                    note="add pass of dele_and_add",
                )
            )

        entry.source_line_nos.append(line.raw_line.line_no)
        return records

    # ------------------------------------------------------------------
    # Add logic
    # ------------------------------------------------------------------

    def _apply_add(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
    ) -> list[BTEditRecord]:
        """
        Apply one ADD line to an entry by appending new senses.

        Args:
            entry: The entry to augment.
            line: The parsed ADD line.

        Returns:
            Audit record describing how many senses were appended.

        """
        if line.raw_line is None:
            return []
        records: list[BTEditRecord] = []

        existing_labels = {s.sense_label for s in entry.senses}
        appended = 0
        for sense in line.senses:
            # Append unlabelled senses and any new labelled senses.
            if sense.sense_label not in existing_labels or not sense.sense_label:
                entry.senses.append(sense)
                existing_labels.add(sense.sense_label)
                appended += 1

        entry.source_line_nos.append(line.raw_line.line_no)
        records.append(
            BTEditRecord(
                op=BTEditorialOp.ADD,
                source_line_no=line.raw_line.line_no,
                target_norm_key=entry.norm_key,
                target_pos=entry.pos,
                scope=f"append:{appended}_senses",
                applied=appended > 0,
                note="" if appended else "add line had no parseable senses",
            )
        )
        return records

    # ------------------------------------------------------------------
    # Cross-ref handling
    # ------------------------------------------------------------------

    def _apply_cross_refs(
        self,
        entries: list[BTConsolidatedEntry],
        parsed_lines: list[ParsedBTLine],
    ) -> None:
        """
        Append ``CROSS_REF`` targets to the ``see_also`` field of resolved entries.

        Side Effects:
            Modifies the ``see_also`` lists of entries in-place.

        Args:
            entries: All consolidated entries produced so far.
            parsed_lines: All parsed lines including CROSS_REF lines.

        """
        entry_map = {(e.norm_key, e.pos): e for e in entries}

        for line in parsed_lines:
            if line.skip_reason is not None:
                continue
            if line.raw_line is None:
                continue
            if line.raw_line.kind != BTLineKind.CROSS_REF:
                continue

            # Determine which entry this cross-ref belongs to.
            key = self.resolver.merge_key_for_line(line)
            if key is None:
                continue

            target_entry = entry_map.get(key)
            if target_entry is None:
                continue

            # Extract cross-ref targets from the raw text.
            for _target_norm, target_display in self._extract_cross_ref_targets(
                line.raw_line.raw_text
            ):
                if target_display and target_display not in target_entry.see_also:
                    target_entry.see_also.append(target_display)

    def _extract_cross_ref_targets(
        self, body: str
    ) -> list[tuple[str, str]]:
        """
        Extract cross-reference target names from a BT line body.

        Args:
            body: Raw HTML body content from a CROSS_REF line.

        Returns:
            List of ``(norm_key, display_text)`` pairs for each target found.

        """
        results: list[tuple[str, str]] = []
        for match in _CROSS_REF_TARGET_RE.finditer(body):
            display = (match.group(1) or match.group(2) or "").strip()
            if not display:
                continue
            norm = normalize_old_english(display)
            if norm:
                results.append((norm, display))
        return results

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _sense_matches_ref(sense: BTSense, ref: str) -> bool:
        """
        Return ``True`` when *sense* matches the deletion reference text *ref*.

        Matches on the sense label (case-insensitive, period-normalised) or on
        whether the plain English gloss contains the reference as a substring.

        Args:
            sense: Sense record to test.
            ref: Raw deletion reference string from ``dele_refs``.

        Returns:
            ``True`` when the sense should be removed.

        """
        label = sense.sense_label.strip().rstrip(".")
        ref_clean = ref.strip().rstrip(".")
        if label.lower() == ref_clean.lower():
            return True
        # Partial reference match for source citations like "Ælfc. T. 5, 25".
        # These are citation strings embedded in the body, not sense labels.
        # We check if it looks like a source citation rather than a label.
        if re.match(r"^[IVXivxa-zA-Z]{1,5}\.?$", ref_clean):
            # Looks like a sense label — only match by label equality.
            return False
        # Source citation: check if it appears in the gloss as a substring.
        # This only fires for long references unlikely to be labels.
        return False
