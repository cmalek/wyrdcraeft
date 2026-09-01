"""Phase 04 editorial merger for Bosworth-Toller dictionary entries."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

from ...models.dictionary import (
    BTConsolidatedEntry,
    BTEditorialOp,
    BTLineKind,
    BTParseWarning,
    BTPos,
    BTSense,
)
from ..dictionary.attestation_stripper import _substantive_html_content
from ..markup import normalize_morphology_title, normalize_old_english
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
            ``sense_path:1``, ``for_X_in_Dict``, etc.).
        applied: Whether the operation was actually applied or skipped.
        note: Additional diagnostic text.
        entry_order: Stable source-block ordering for homograph disambiguation.
        source_block_index: Zero-based source block index for audit joins.

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
    #: Stable source-block ordering for homograph disambiguation.
    entry_order: int = 0
    #: Zero-based source block index for audit joins.
    source_block_index: int = 0


def _plain(text: str) -> str:
    """
    Strip HTML tags and collapse whitespace from *text*.

    Args:
        text: Input HTML string.

    Returns:
        Plain-text string with normalised whitespace.

    """
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


def _target_note(reason: str, detail: str) -> str:
    """
    Format one standardized edit-log note with human context.

    Args:
        reason: Machine-readable note code such as ``target_missing``.
        detail: Human-readable diagnostic context.

    Returns:
        Combined note string for ``bt_edit_log``.

    """
    detail = detail.strip()
    if detail:
        return f"{reason}: {detail}"
    return reason


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

    def _merge_block(  # noqa: PLR0912
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
            A pair ``(entry, audit_records)`` where *entry* may be ``None`` when the
            block contains no usable seed line.

        """
        sorted_lines = sorted(
            block.lines,
            key=lambda ln: ln.raw_line.line_no if ln.raw_line else 0,
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

        substitute_seed = False
        if not mains and substitutes:
            seed = substitutes.pop(0)
            substitute_seed = True
        elif not mains and adds and adds[0].senses:
            seed = adds.pop(0)
            substitute_seed = False
        elif not mains:
            return None, []
        else:
            seed = mains[0]
            substitute_seed = False
        if seed.raw_line is None:
            return None, []

        pos = block.pos if block.pos != BTPos.UNKNOWN else seed.pos
        entry = BTConsolidatedEntry(
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

        for ln in mains[1:]:
            if ln.raw_line is None:
                continue
            entry.source_line_nos.append(ln.raw_line.line_no)
            self._extend_senses(entry, ln.senses)
            for variant in ln.variants:
                if variant not in entry.variants:
                    entry.variants.append(variant)
            if not entry.etymology and ln.etymology_blocks:
                entry.etymology = " ".join(ln.etymology_blocks)

        audit: list[BTEditRecord] = []

        if substitute_seed:
            audit.extend(self._apply_substitute(entry, seed, all_blocks, block))

        for ln in substitutes:
            if ln.raw_line is None:
                continue
            audit.extend(
                self._apply_substitute(entry, ln, all_blocks, block)
            )

        for ln in deles:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_dele(entry, ln, block))

        for ln in dele_and_adds:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_dele_and_add(entry, ln, block))

        for ln in adds:
            if ln.raw_line is None:
                continue
            audit.extend(self._apply_add(entry, ln, block))

        entry.genders = list(
            promote_entry_gender_from_senses(
                tuple(entry.genders),
                tuple(entry.senses),
            )
        )
        return entry, audit

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

    def _append_senses(
        self,
        entry: BTConsolidatedEntry,
        new_senses: tuple[BTSense, ...],
    ) -> int:
        """
        Append supplemental senses using label-aware deduplication.

        Unlabelled senses always append.  Labelled senses append only when their
        ``sense_label`` is not already present on the entry.

        Args:
            entry: Entry being augmented.
            new_senses: Candidate senses from one ADD or DELE_AND_ADD line.

        Returns:
            Number of senses appended.

        """
        existing_labels = {
            sense.source_label_raw.rstrip(".") for sense in entry.senses
        }
        appended = 0
        for sense in new_senses:
            raw_label = sense.source_label_raw.rstrip(".")
            if raw_label not in existing_labels or not raw_label:
                entry.senses.append(sense)
                existing_labels.add(raw_label)
                appended += 1
        return appended

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

    def _audit_context(self, block: BTSourceBlock) -> tuple[int, int]:
        """
        Return audit metadata shared by edit records for one block.

        Args:
            block: Source block whose edits are being recorded.

        Returns:
            ``(entry_order, source_block_index)`` pair for :class:`BTEditRecord`.

        """
        return block.entry_order, block.source_block_index

    def _apply_substitute(  # noqa: PLR0912
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        all_blocks: list[BTSourceBlock],
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Apply one SUBSTITUTE line to an entry or to a cross-entry target.

        Args:
            entry: The entry currently being built for this source block.
            line: The parsed SUBSTITUTE line.
            all_blocks: Full block list for cross-entry resolution.
            block: Current source block for audit metadata.

        Returns:
            Audit records describing what was changed.

        """
        if line.raw_line is None:
            return []
        body = line.raw_line.raw_text
        plain_body = _plain(body)
        records: list[BTEditRecord] = []
        audit_entry_order, audit_block_index = self._audit_context(block)

        for_x_match = _SUBSTITUTE_FOR_X_RE.search(plain_body)
        if for_x_match:
            target_text = for_x_match.group(1).strip()
            target_norm = normalize_old_english(target_text) or ""
            target_blocks = [
                candidate
                for candidate in all_blocks
                if candidate.norm_key == target_norm
            ]
            if len(target_blocks) == 1:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.SUBSTITUTE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=target_norm,
                        target_pos=target_blocks[0].pos,
                        scope=f"for_X_in_Dict:{target_text}",
                        applied=False,
                        note=(
                            "cross-entry substitute deferred;"
                            " target in different block"
                        ),
                        entry_order=target_blocks[0].entry_order,
                        source_block_index=target_blocks[0].source_block_index,
                    )
                )
            elif not target_blocks:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.SUBSTITUTE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=target_norm,
                        target_pos=entry.pos,
                        scope=f"for_X_in_Dict:{target_text}",
                        applied=False,
                        note=_target_note(
                            "target_missing",
                            f"cross-entry target {target_text!r} not found",
                        ),
                        entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                    )
                )
            else:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.SUBSTITUTE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=target_norm,
                        target_pos=entry.pos,
                        scope=f"for_X_in_Dict:{target_text}",
                        applied=False,
                        note=_target_note(
                            "target_ambiguous",
                            f"multiple blocks match {target_text!r}",
                        ),
                        entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                    )
                )
            return records

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
                        entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
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
                        entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                    )
                )
            return records

        for_all_but = _FOR_ALL_BUT_RE.search(plain_body)
        if for_all_but:
            pinned_raw = for_all_but.group(1).strip()
            pinned_paths = set()
            for label in re.split(r"[,;]", pinned_raw):
                cleaned = label.strip().rstrip(".")
                if not cleaned:
                    continue
                path = self.resolver.resolve_sense_path(cleaned, entry.senses)
                if path is not None:
                    pinned_paths.add(path)
            kept = [
                sense for sense in entry.senses
                if sense.sense_path in pinned_paths
            ]
            entry.senses = kept + list(line.senses)
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.SUBSTITUTE,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=f"for_all_but:{pinned_raw}",
                    applied=True,
                    entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                )
            )
            return records

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
                    entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                )
            )
        return records

    def _apply_dele(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Apply one DELE line to an entry.

        Args:
            entry: The entry to modify.
            line: The parsed DELE line.
            block: Current source block for audit metadata.

        Returns:
            Audit records describing what was removed.

        """
        if line.raw_line is None:
            return []
        body = line.raw_line.raw_text
        records: list[BTEditRecord] = []
        audit_entry_order, audit_block_index = self._audit_context(block)

        dele_scope_match = _DELE_SCOPE_RE.search(body)
        if dele_scope_match and not line.dele_refs:
            scope_text = dele_scope_match.group(1).strip()
            if not scope_text:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.DELE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=entry.norm_key,
                        target_pos=entry.pos,
                        scope="bare_dele",
                        applied=True,
                        note="bare Dele; entry marked deprecated",
                        entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                    )
                )
                entry.senses = []
                return records

        if line.dele_refs:
            paths, note = self.resolver.resolve_sense_paths_for_refs(
                list(line.dele_refs),
                entry.senses,
            )
            if not paths:
                records.append(
                    BTEditRecord(
                        op=BTEditorialOp.DELE,
                        source_line_no=line.raw_line.line_no,
                        target_norm_key=entry.norm_key,
                        target_pos=entry.pos,
                        scope="sense_paths:none",
                        applied=False,
                        note=_target_note(
                            note or "target_missing",
                            "dele_refs did not match any sense paths",
                        ),
                        entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                    )
                )
                return records
            removed = [
                path for path in paths
                if any(sense.sense_path == path for sense in entry.senses)
            ]
            entry.senses = [
                sense for sense in entry.senses
                if sense.sense_path not in set(paths)
            ]
            scope = "sense_paths:" + ",".join(removed) if removed else "no_match"
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.DELE,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=scope,
                    applied=bool(removed),
                    note=(
                        ""
                        if removed
                        else _target_note(
                            note or "target_missing",
                            "dele_refs did not match",
                        )
                    ),
                    entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                )
            )
            return records

        records.append(
            BTEditRecord(
                op=BTEditorialOp.DELE,
                source_line_no=line.raw_line.line_no,
                target_norm_key=entry.norm_key,
                target_pos=entry.pos,
                scope="unknown",
                applied=False,
                note="dele line had no recognisable scope",
                entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
            )
        )
        return records

    def _apply_dele_and_add(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Apply one DELE_AND_ADD line — first remove, then append.

        Args:
            entry: The entry to modify.
            line: The parsed DELE_AND_ADD line.
            block: Current source block for audit metadata.

        Returns:
            Audit records for both the delete and add passes.

        """
        if line.raw_line is None:
            return []
        records: list[BTEditRecord] = []
        audit_entry_order, audit_block_index = self._audit_context(block)

        if line.dele_refs:
            paths, note = self.resolver.resolve_sense_paths_for_refs(
                list(line.dele_refs),
                entry.senses,
            )
            removed = [
                path for path in paths
                if any(sense.sense_path == path for sense in entry.senses)
            ]
            if paths:
                entry.senses = [
                    sense for sense in entry.senses
                    if sense.sense_path not in set(paths)
                ]
            scope = "dele_pass:" + (",".join(removed) if removed else "no_match")
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.DELE_AND_ADD,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=scope,
                    applied=bool(removed),
                    note=note or "dele pass of dele_and_add",
                    entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                )
            )

        if line.senses:
            appended = self._append_senses(entry, line.senses)
            records.append(
                BTEditRecord(
                    op=BTEditorialOp.DELE_AND_ADD,
                    source_line_no=line.raw_line.line_no,
                    target_norm_key=entry.norm_key,
                    target_pos=entry.pos,
                    scope=f"add_pass:{appended}_senses",
                    applied=appended > 0,
                    note="add pass of dele_and_add",
                    entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
                )
            )

        entry.source_line_nos.append(line.raw_line.line_no)
        return records

    def _apply_add(
        self,
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
        audit_entry_order, audit_block_index = self._audit_context(block)

        appended = self._append_senses(entry, line.senses)

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
                entry_order=audit_entry_order,
                        source_block_index=audit_block_index,
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
