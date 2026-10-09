"""Phase 04 editorial merger for Bosworth-Toller dictionary entries."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from ...models.dictionary import (
    BTConsolidatedEntry,
    BTEditorialOp,
    BTEditRecord,
    BTLineKind,
    BTParseWarning,
    BTPos,
    BTSense,
)
from ..dictionary.attestation_stripper import _substantive_html_content
from ..markup import normalize_morphology_title, normalize_old_english
from .editorial_ops import (
    BTDeleAndAddOp,
    BTDeleOp,
    BTSubstituteOp,
    append_senses,
)
from .sense_metadata import promote_entry_gender_from_senses
from .source_blocks import BTSourceBlock, BTSourceBlockBuilder
from .target_resolver import BTTargetResolver

if TYPE_CHECKING:
    from .line_parser import ParsedBTLine

#: Editorial line kinds that may emit debris warnings when glosses are missing.
_EDITORIAL_LINE_KINDS: Final[frozenset[BTLineKind]] = frozenset(
    {
        BTLineKind.ADD,
        BTLineKind.SUBSTITUTE,
        BTLineKind.DELE_AND_ADD,
    }
)

#: ``v.`` / ``vide`` cross-reference target extractor.
_CROSS_REF_TARGET_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:v\.|vide)\s+<B>(.*?)</B>|(?:v\.|vide)\s+([\w\-ā-ū]+)",
    re.IGNORECASE,
)


def _edit_note_reason(note: str) -> str | None:
    """
    Extract a standardized warning reason from one edit-log note.

    Args:
        note: Stored ``bt_edit_log.note`` value.

    Returns:
        ``target_missing``, ``target_ambiguous``, or ``None``.

    """
    if note == "target_ambiguous" or note.startswith("target_ambiguous:"):
        return "target_ambiguous"
    if note == "target_missing" or note.startswith("target_missing:"):
        return "target_missing"
    return None


def _edit_note_detail(note: str) -> str:
    """
    Return human context from one standardized edit-log note.

    Args:
        note: Stored ``bt_edit_log.note`` value.

    Returns:
        Detail text after the reason prefix, or the full note when unprefixed.

    """
    for prefix in ("target_ambiguous:", "target_missing:"):
        if note.startswith(prefix):
            return note[len(prefix) :].strip()
    return note


class BTEditorialMerger:
    """
    Merge parsed Bosworth-Toller lines into consolidated dictionary entries.

    One consolidated entry is produced per dictionary source block in document
    order.  Homograph MAIN lines with the same ``(norm_key, pos)`` remain
    separate entries.  Editorial operations target canonical ``sense_path``
    values rather than Roman labels.

    Args:
        resolver: Optional target-resolver collaborator.
        block_builder: Optional source-block builder collaborator.

    """

    def __init__(
        self,
        resolver: BTTargetResolver | None = None,
        block_builder: BTSourceBlockBuilder | None = None,
    ) -> None:
        """
        Initialise the merger with optional collaborators.

        Args:
            resolver: Optional pre-built :class:`BTTargetResolver` instance.
            block_builder: Optional pre-built :class:`BTSourceBlockBuilder`.

        """
        #: Target-resolver collaborator.
        self.resolver: BTTargetResolver = resolver or BTTargetResolver()
        #: Source-block builder collaborator.
        self.block_builder: BTSourceBlockBuilder = (
            block_builder or BTSourceBlockBuilder(self.resolver)
        )
        #: Substitute collaborator.
        self._substitute_op: BTSubstituteOp = BTSubstituteOp(self.resolver)
        #: Dele collaborator.
        self._dele_op: BTDeleOp = BTDeleOp(self.resolver)
        #: Dele-and-add collaborator.
        self._dele_and_add_op: BTDeleAndAddOp = BTDeleAndAddOp(self.resolver)

    def merge(
        self, parsed_lines: list[ParsedBTLine]
    ) -> tuple[list[BTConsolidatedEntry], list[BTEditRecord]]:
        """
        Produce one consolidated entry per dictionary source block.

        Skipped parsed lines are ignored.  Lines whose headword normalises to an
        empty string are also discarded.

        Args:
            parsed_lines: All parsed BT lines to merge.

        Returns:
            A pair ``(entries, edit_records)`` where *entries* is the ordered list of
            consolidated results and *edit_records* is the audit log.

        """
        blocks = self.block_builder.build(parsed_lines)
        entries: list[BTConsolidatedEntry] = []
        audit: list[BTEditRecord] = []

        for block in blocks:
            entry, records = self._merge_block(block, blocks)
            if entry is not None:
                entries.append(entry)
            audit.extend(records)

        self._apply_cross_refs(entries, parsed_lines)
        return entries, audit

    def collect_editorial_warnings(
        self,
        parsed_lines: list[ParsedBTLine],
        edit_records: list[BTEditRecord],
    ) -> list[BTParseWarning]:
        """
        Collect editorial-stage warnings for ``parse_warnings.jsonl``.

        Editorial debris warnings are emitted here rather than during segmentation.
        Unapplied edit records with ``target_missing`` or ``target_ambiguous`` notes
        are mirrored into parse warnings for audit visibility.

        Args:
            parsed_lines: Parsed lines from the indexing pass.
            edit_records: Audit records produced by :meth:`merge`.

        Returns:
            Editorial warning records to append after merge.

        """
        warnings: list[BTParseWarning] = []
        for parsed in parsed_lines:
            if parsed.skip_reason is not None or parsed.raw_line is None:
                continue
            if parsed.raw_line.kind not in _EDITORIAL_LINE_KINDS:
                continue
            body = parsed.raw_line.raw_text
            if parsed.senses or not _substantive_html_content(body):
                continue
            warnings.append(
                BTParseWarning(
                    line_no=parsed.raw_line.line_no,
                    body=body,
                    headword=parsed.headword_macronized or parsed.raw_line.headword_raw,
                    pos_hint=parsed.pos.value,
                    failure_reason="editorial_fragment_without_gloss",
                )
            )

        for record in edit_records:
            if record.applied:
                continue
            reason = _edit_note_reason(record.note)
            if reason is None:
                continue
            matched_line = next(
                (
                    line
                    for line in parsed_lines
                    if line.raw_line is not None
                    and line.raw_line.line_no == record.source_line_no
                ),
                None,
            )
            body = (
                matched_line.raw_line.raw_text
                if matched_line and matched_line.raw_line
                else ""
            )
            headword = (
                matched_line.headword_macronized
                if matched_line and matched_line.headword_macronized
                else record.target_norm_key
            )
            pos_hint = (
                matched_line.pos.value
                if matched_line is not None
                else record.target_pos.value
            )
            warnings.append(
                BTParseWarning(
                    line_no=record.source_line_no,
                    body=body,
                    headword=headword,
                    pos_hint=pos_hint,
                    failure_reason=reason,
                    detail=_edit_note_detail(record.note),
                )
            )
        return warnings

    def _merge_block(
        self,
        block: BTSourceBlock,
        all_blocks: list[BTSourceBlock],
    ) -> tuple[BTConsolidatedEntry | None, list[BTEditRecord]]:
        """
        Build one consolidated entry from all lines in *block*.

        Args:
            block: One dictionary source block.
            all_blocks: Full block list for cross-entry substitute resolution.

        Returns:
            A pair ``(entry, audit_records)`` where *entry* may be ``None`` when
            the block contains no usable seed line.

        """
        sorted_lines = sorted(
            block.lines,
            key=lambda ln: ln.raw_line.line_no if ln.raw_line else 0,
        )
        mains = self._of_kind(sorted_lines, BTLineKind.MAIN)
        substitutes = self._of_kind(sorted_lines, BTLineKind.SUBSTITUTE)
        deles = self._of_kind(sorted_lines, BTLineKind.DELE)
        dele_and_adds = self._of_kind(sorted_lines, BTLineKind.DELE_AND_ADD)
        adds = self._of_kind(sorted_lines, BTLineKind.ADD)
        seed, substitute_seed, substitutes, adds = self._pick_seed(
            mains, substitutes, adds
        )
        if seed is None or seed.raw_line is None:
            return None, []
        entry = self._new_entry(block, seed)
        self._absorb_main_follow_ons(entry, mains[1:])
        audit: list[BTEditRecord] = []
        if substitute_seed:
            audit.extend(
                self._substitute_op.apply(entry, seed, all_blocks, block)
            )
        for ln in substitutes:
            if ln.raw_line is not None:
                audit.extend(self._substitute_op.apply(entry, ln, all_blocks, block))
        for ln in deles:
            if ln.raw_line is not None:
                audit.extend(self._dele_op.apply(entry, ln, block))
        for ln in dele_and_adds:
            if ln.raw_line is not None:
                audit.extend(self._dele_and_add_op.apply(entry, ln, block))
        for ln in adds:
            if ln.raw_line is not None:
                audit.extend(self._apply_add(entry, ln, block))
        entry.genders = list(
            promote_entry_gender_from_senses(
                tuple(entry.genders),
                tuple(entry.senses),
            )
        )
        return entry, audit

    @staticmethod
    def _of_kind(
        sorted_lines: list[ParsedBTLine], kind: BTLineKind
    ) -> list[ParsedBTLine]:
        """
        Return lines whose raw kind is *kind*.

        Args:
            sorted_lines: Block lines in source order.
            kind: Line kind to keep.

        Returns:
            Matching parsed lines.

        """
        return [
            ln for ln in sorted_lines if ln.raw_line and ln.raw_line.kind == kind
        ]

    @staticmethod
    def _pick_seed(
        mains: list[ParsedBTLine],
        substitutes: list[ParsedBTLine],
        adds: list[ParsedBTLine],
    ) -> tuple[ParsedBTLine | None, bool, list[ParsedBTLine], list[ParsedBTLine]]:
        """
        Choose the seed line and remaining editorial lists.

        Pops the chosen substitute or add from the corresponding list when there
        is no MAIN line.

        Args:
            mains: MAIN lines in the block.
            substitutes: SUBSTITUTE lines; may be mutated.
            adds: ADD lines; may be mutated.

        Returns:
            ``(seed, substitute_seed, remaining_substitutes, remaining_adds)``.

        """
        if mains:
            return mains[0], False, substitutes, adds
        if substitutes:
            seed = substitutes.pop(0)
            return seed, True, substitutes, adds
        if adds and adds[0].senses:
            seed = adds.pop(0)
            return seed, False, substitutes, adds
        return None, False, substitutes, adds

    @staticmethod
    def _new_entry(
        block: BTSourceBlock, seed: ParsedBTLine
    ) -> BTConsolidatedEntry:
        """
        Construct the consolidated entry from the seed line and block.

        Args:
            block: Source block supplying identity and POS fallback.
            seed: Seed line; caller guarantees ``raw_line`` is set.

        Returns:
            New consolidated entry.

        """
        if seed.raw_line is None:
            msg = "seed line is missing raw_line"
            raise ValueError(msg)
        pos = block.pos if block.pos != BTPos.UNKNOWN else seed.pos
        return BTConsolidatedEntry(
            norm_key=block.norm_key,
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
            entry_order=block.entry_order,
        )

    def _absorb_main_follow_ons(
        self, entry: BTConsolidatedEntry, follow_ons: list[ParsedBTLine]
    ) -> None:
        """
        Merge later MAIN lines into *entry*.

        Args:
            entry: Seed entry being built.
            follow_ons: MAIN lines after the seed.

        """
        for ln in follow_ons:
            if ln.raw_line is None:
                continue
            entry.source_line_nos.append(ln.raw_line.line_no)
            self._extend_senses(entry, ln.senses)
            for variant in ln.variants:
                if variant not in entry.variants:
                    entry.variants.append(variant)
            if not entry.etymology and ln.etymology_blocks:
                entry.etymology = " ".join(ln.etymology_blocks)

    def _extend_senses(
        self,
        entry: BTConsolidatedEntry,
        new_senses: tuple[BTSense, ...],
    ) -> None:
        """
        Append follow-on MAIN senses, reassigning colliding ``sense_path`` values.

        Args:
            entry: Entry being built.
            new_senses: Candidate senses from a follow-on MAIN line.

        """
        existing_paths = {sense.sense_path for sense in entry.senses}
        next_top = self._next_top_level_path(existing_paths)
        for incoming in new_senses:
            sense = incoming
            if sense.sense_path in existing_paths:
                sense = replace(
                    sense,
                    sense_path=str(next_top),
                    parent_path=None,
                )
                next_top += 1
            entry.senses.append(sense)
            existing_paths.add(sense.sense_path)

    @staticmethod
    def _next_top_level_path(existing_paths: set[str]) -> int:
        """
        Return the next unused top-level ``sense_path`` integer.

        Args:
            existing_paths: Sense paths already present on one entry.

        Returns:
            One greater than the highest numeric top-level path already used.

        """
        top_levels = [
            int(path.split(".", maxsplit=1)[0])
            for path in existing_paths
            if path.split(".", maxsplit=1)[0].isdigit()
        ]
        return max(top_levels, default=0) + 1

    @staticmethod
    def _apply_add(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Apply one ADD line to an entry by appending new senses.

        Args:
            entry: The entry to augment.
            line: The parsed ADD line.
            block: Current source block for audit metadata.

        Returns:
            Audit record describing how many senses were appended.

        """
        if line.raw_line is None:
            return []
        records: list[BTEditRecord] = []
        appended = append_senses(entry, line.senses)
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
                entry_order=block.entry_order,
                source_block_index=block.source_block_index,
            )
        )
        return records

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
        entry_map = {
            (entry.norm_key, entry.pos, entry.entry_order): entry
            for entry in entries
        }
        fallback_map: dict[tuple[str, BTPos], BTConsolidatedEntry] = {}
        for entry in entries:
            entry_key = (entry.norm_key, entry.pos)
            if entry_key not in fallback_map:
                fallback_map[entry_key] = entry

        for line in parsed_lines:
            if line.skip_reason is not None:
                continue
            if line.raw_line is None:
                continue
            if line.raw_line.kind != BTLineKind.CROSS_REF:
                continue

            cross_ref_key = self.resolver.merge_key_for_line(line)
            if cross_ref_key is None:
                continue

            norm_key, pos = cross_ref_key
            target_entry = fallback_map.get((norm_key, pos))
            if target_entry is None:
                continue

            for _target_norm, target_display in self._extract_cross_ref_targets(
                line.raw_line.raw_text
            ):
                if target_display and target_display not in target_entry.see_also:
                    target_entry.see_also.append(target_display)

        _ = entry_map

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
