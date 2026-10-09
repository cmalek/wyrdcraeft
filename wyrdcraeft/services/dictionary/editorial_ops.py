"""Editorial operation collaborators for Bosworth-Toller consolidation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from ...models.dictionary import BTEditorialOp, BTEditRecord, BTPos, BTSense
from ..markup import normalize_old_english

if TYPE_CHECKING:
    from ...models.dictionary import BTConsolidatedEntry
    from .line_parser import ParsedBTLine
    from .source_blocks import BTSourceBlock
    from .target_resolver import BTTargetResolver

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
#: ``Dele last passage`` or ``Dele bracket`` pattern (scoped dele).
_DELE_SCOPE_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>\s*Dele\b([^<]*)</I>",
    re.IGNORECASE,
)


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


def _make_edit_record(  # noqa: PLR0913
    *,
    op: BTEditorialOp,
    line: ParsedBTLine,
    entry: BTConsolidatedEntry,
    block: BTSourceBlock,
    scope: str,
    applied: bool,
    note: str = "",
    target_norm_key: str | None = None,
    target_pos: BTPos | None = None,
    entry_order: int | None = None,
    source_block_index: int | None = None,
) -> BTEditRecord:
    """
    Build one :class:`BTEditRecord` from a line and source block.

    Keyword Args:
        op: Editorial operation kind.
        line: Parsed editorial line; ``raw_line`` must be set.
        entry: Entry used for default target key and POS.
        block: Source block used for default audit indices.
        scope: Audit scope string.
        applied: Whether the operation took effect.
        note: Diagnostic note.
        target_norm_key: Override for the target key.
        target_pos: Override for the target POS.
        entry_order: Override for ``entry_order``.
        source_block_index: Override for ``source_block_index``.

    Returns:
        Populated audit record.

    Raises:
        ValueError: If *line* has no ``raw_line``.

    """
    raw = line.raw_line
    if raw is None:
        msg = "editorial line is missing raw_line"
        raise ValueError(msg)
    return BTEditRecord(
        op=op,
        source_line_no=raw.line_no,
        target_norm_key=entry.norm_key if target_norm_key is None else target_norm_key,
        target_pos=entry.pos if target_pos is None else target_pos,
        scope=scope,
        applied=applied,
        note=note,
        entry_order=block.entry_order if entry_order is None else entry_order,
        source_block_index=(
            block.source_block_index
            if source_block_index is None
            else source_block_index
        ),
    )


def append_senses(
    entry: BTConsolidatedEntry,
    new_senses: tuple[BTSense, ...],
) -> int:
    """
    Append supplemental senses using label-aware deduplication.

    Unlabelled senses always append. Labelled senses append only when their
    ``source_label_raw`` is not already present on the entry.

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


class BTSubstituteOp:
    """
    Apply one SUBSTITUTE line to the current entry or a cross-entry target.

    Args:
        resolver: Target-resolver used for ``for all but`` sense paths.

    """

    def __init__(self, resolver: BTTargetResolver) -> None:
        """
        Bind the resolver used for sense-path lookup.

        Args:
            resolver: Target-resolver collaborator.

        """
        #: Sense-path resolver.
        self.resolver: BTTargetResolver = resolver

    def apply(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        all_blocks: list[BTSourceBlock],
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Dispatch one SUBSTITUTE line.

        Args:
            entry: Entry for the current source block.
            line: Parsed SUBSTITUTE line.
            all_blocks: All blocks, for ``for X in Dict`` lookup.
            block: Current source block for audit metadata.

        Returns:
            Audit records. Cross-entry hits stay ``applied=False``.

        """
        if line.raw_line is None:
            return []
        plain_body = _plain(line.raw_line.raw_text)
        if _SUBSTITUTE_FOR_X_RE.search(plain_body):
            return self._for_x_in_dict(entry, line, all_blocks, block, plain_body)
        if _SUBSTITUTE_FOLLOWING_RE.search(plain_body):
            return self._replace_following(entry, line, block)
        if _FOR_ALL_BUT_RE.search(plain_body):
            return self._for_all_but(entry, line, block, plain_body)
        return self._fallback(entry, line, block)

    @staticmethod
    def _for_x_in_dict(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        all_blocks: list[BTSourceBlock],
        block: BTSourceBlock,
        plain_body: str,
    ) -> list[BTEditRecord]:
        """
        Record a cross-entry ``for X in Dict`` substitute without rewriting.

        Args:
            entry: Current block entry (audit defaults).
            line: Parsed SUBSTITUTE line.
            all_blocks: Blocks searched for the named target.
            block: Current source block for audit defaults.
            plain_body: Tag-stripped line text.

        Returns:
            One unapplied audit record.

        """
        match = _SUBSTITUTE_FOR_X_RE.search(plain_body)
        if match is None:
            return []
        target_text = match.group(1).strip()
        target_norm = normalize_old_english(target_text) or ""
        target_blocks = [
            candidate for candidate in all_blocks if candidate.norm_key == target_norm
        ]
        scope = f"for_X_in_Dict:{target_text}"
        if len(target_blocks) == 1:
            target = target_blocks[0]
            return [
                _make_edit_record(
                    op=BTEditorialOp.SUBSTITUTE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope=scope,
                    applied=False,
                    note="cross-entry substitute deferred; target in different block",
                    target_norm_key=target_norm,
                    target_pos=target.pos,
                    entry_order=target.entry_order,
                    source_block_index=target.source_block_index,
                )
            ]
        if not target_blocks:
            return [
                _make_edit_record(
                    op=BTEditorialOp.SUBSTITUTE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope=scope,
                    applied=False,
                    note=_target_note(
                        "target_missing",
                        f"cross-entry target {target_text!r} not found",
                    ),
                    target_norm_key=target_norm,
                )
            ]
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope=scope,
                applied=False,
                note=_target_note(
                    "target_ambiguous",
                    f"multiple blocks match {target_text!r}",
                ),
                target_norm_key=target_norm,
            )
        ]

    @staticmethod
    def _replace_following(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Replace all senses when the line is ``substitute the following``.

        Args:
            entry: Entry whose senses are replaced.
            line: Parsed SUBSTITUTE line.
            block: Current source block for audit metadata.

        Returns:
            Audit records for the replacement attempt.

        """
        if line.senses:
            entry.senses = list(line.senses)
            return [
                _make_edit_record(
                    op=BTEditorialOp.SUBSTITUTE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope="all_senses",
                    applied=True,
                )
            ]
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope="all_senses",
                applied=False,
                note="substitute line has no parsed senses",
            )
        ]

    def _for_all_but(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
        plain_body: str,
    ) -> list[BTEditRecord]:
        """
        Keep pinned senses and append the substitute's new senses.

        Args:
            entry: Entry being rewritten.
            line: Parsed SUBSTITUTE line.
            block: Current source block for audit metadata.
            plain_body: Tag-stripped line text.

        Returns:
            One applied audit record.

        """
        match = _FOR_ALL_BUT_RE.search(plain_body)
        if match is None:
            return []
        pinned_raw = match.group(1).strip()
        pinned_paths: set[str] = set()
        for label in re.split(r"[,;]", pinned_raw):
            cleaned = label.strip().rstrip(".")
            if not cleaned:
                continue
            path = self.resolver.resolve_sense_path(cleaned, entry.senses)
            if path is not None:
                pinned_paths.add(path)
        kept = [sense for sense in entry.senses if sense.sense_path in pinned_paths]
        entry.senses = kept + list(line.senses)
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope=f"for_all_but:{pinned_raw}",
                applied=True,
            )
        ]

    @staticmethod
    def _fallback(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Replace all senses when no structured substitute pattern matched.

        Args:
            entry: Entry whose senses are replaced.
            line: Parsed SUBSTITUTE line.
            block: Current source block for audit metadata.

        Returns:
            Audit records, or an empty list when the line has no senses.

        """
        if not line.senses:
            return []
        entry.senses = list(line.senses)
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope="all_senses_fallback",
                applied=True,
            )
        ]


class BTDeleOp:
    """
    Apply one DELE line to the current entry.

    Args:
        resolver: Target-resolver used for ``dele_refs`` sense paths.

    """

    def __init__(self, resolver: BTTargetResolver) -> None:
        """
        Bind the resolver used for sense-path lookup.

        Args:
            resolver: Target-resolver collaborator.

        """
        #: Sense-path resolver.
        self.resolver: BTTargetResolver = resolver

    def apply(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Dispatch one DELE line.

        Args:
            entry: Entry to modify.
            line: Parsed DELE line.
            block: Current source block for audit metadata.

        Returns:
            Audit records describing what was removed.

        """
        if line.raw_line is None:
            return []
        body = line.raw_line.raw_text
        match = _DELE_SCOPE_RE.search(body)
        if match and not line.dele_refs:
            scoped = self._bare_or_scoped(
                entry, line, block, match.group(1).strip()
            )
            if scoped:
                return scoped
        if line.dele_refs:
            return self._by_refs(entry, line, block)
        return [
            _make_edit_record(
                op=BTEditorialOp.DELE,
                line=line,
                entry=entry,
                block=block,
                scope="unknown",
                applied=False,
                note="dele line had no recognisable scope",
            )
        ]

    @staticmethod
    def _bare_or_scoped(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
        scope_text: str,
    ) -> list[BTEditRecord]:
        """
        Clear all senses for a bare Dele; otherwise return no records.

        Args:
            entry: Entry to clear when the Dele is bare.
            line: Parsed DELE line.
            block: Current source block for audit metadata.
            scope_text: Text captured after ``Dele`` inside the italic tag.

        Returns:
            Bare-dele audit records, or an empty list so apply can fall through.

        """
        if scope_text:
            return []
        entry.senses = []
        return [
            _make_edit_record(
                op=BTEditorialOp.DELE,
                line=line,
                entry=entry,
                block=block,
                scope="bare_dele",
                applied=True,
                note="bare Dele; entry marked deprecated",
            )
        ]

    def _by_refs(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Remove senses whose paths match ``dele_refs``.

        Args:
            entry: Entry to modify.
            line: Parsed DELE line with ``dele_refs``.
            block: Current source block for audit metadata.

        Returns:
            Audit records describing matched or missing paths.

        """
        paths, note = self.resolver.resolve_sense_paths_for_refs(
            list(line.dele_refs),
            entry.senses,
        )
        if not paths:
            return [
                _make_edit_record(
                    op=BTEditorialOp.DELE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope="sense_paths:none",
                    applied=False,
                    note=_target_note(
                        note or "target_missing",
                        "dele_refs did not match any sense paths",
                    ),
                )
            ]
        removed = [
            path
            for path in paths
            if any(sense.sense_path == path for sense in entry.senses)
        ]
        entry.senses = [
            sense for sense in entry.senses if sense.sense_path not in set(paths)
        ]
        scope = "sense_paths:" + ",".join(removed) if removed else "no_match"
        return [
            _make_edit_record(
                op=BTEditorialOp.DELE,
                line=line,
                entry=entry,
                block=block,
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
            )
        ]


class BTDeleAndAddOp:
    """
    Apply one DELE_AND_ADD line: remove matching senses, then append.

    Args:
        resolver: Target-resolver used for the dele pass.

    """

    def __init__(self, resolver: BTTargetResolver) -> None:
        """
        Bind the resolver used for sense-path lookup.

        Args:
            resolver: Target-resolver collaborator.

        """
        #: Sense-path resolver.
        self.resolver: BTTargetResolver = resolver

    def apply(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Run the dele pass then the add pass for one line.

        Args:
            entry: Entry to modify.
            line: Parsed DELE_AND_ADD line.
            block: Current source block for audit metadata.

        Returns:
            Audit records for both passes.

        """
        if line.raw_line is None:
            return []
        records: list[BTEditRecord] = []
        if line.dele_refs:
            paths, note = self.resolver.resolve_sense_paths_for_refs(
                list(line.dele_refs),
                entry.senses,
            )
            removed = [
                path
                for path in paths
                if any(sense.sense_path == path for sense in entry.senses)
            ]
            if paths:
                entry.senses = [
                    sense
                    for sense in entry.senses
                    if sense.sense_path not in set(paths)
                ]
            records.append(
                _make_edit_record(
                    op=BTEditorialOp.DELE_AND_ADD,
                    line=line,
                    entry=entry,
                    block=block,
                    scope="dele_pass:" + (",".join(removed) if removed else "no_match"),
                    applied=bool(removed),
                    note=note or "dele pass of dele_and_add",
                )
            )
        if line.senses:
            appended = append_senses(entry, line.senses)
            records.append(
                _make_edit_record(
                    op=BTEditorialOp.DELE_AND_ADD,
                    line=line,
                    entry=entry,
                    block=block,
                    scope=f"add_pass:{appended}_senses",
                    applied=appended > 0,
                    note="add pass of dele_and_add",
                )
            )
        entry.source_line_nos.append(line.raw_line.line_no)
        return records
