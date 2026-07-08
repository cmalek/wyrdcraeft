"""Source-block grouping for Bosworth-Toller editorial merge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...models.dictionary import BTLineKind, BTPos
from ..markup import normalize_old_english
from .target_resolver import BTTargetResolver

if TYPE_CHECKING:
    from .line_parser import ParsedBTLine


@dataclass
class BTSourceBlock:
    """
    One dictionary source block in ``oe_bt.txt`` document order.

    A block begins at a primary MAIN line or at an editorial seed line when no
    compatible preceding block exists.  Follow-on MAIN lines with ``pos=unknown``
    and nearby ADD / SUBSTITUTE / DELE lines attach to the nearest preceding
    compatible block.  Homograph MAIN lines with the same ``(norm_key, pos)``
    remain separate blocks.

    Attributes:
        source_block_index: Zero-based index in the built block sequence.
        entry_order: One-based stable ordering assigned during consolidation.
        norm_key: Normalised Old English lookup key for the block seed.
        pos: Normalised part of speech for the block seed.
        lines: All parsed lines attached to this block in source order.

    """

    #: Zero-based index in the built block sequence.
    source_block_index: int
    #: One-based stable ordering assigned during consolidation.
    entry_order: int
    #: Normalised Old English lookup key for the block seed.
    norm_key: str
    #: Normalised part of speech for the block seed.
    pos: BTPos
    #: Parsed lines attached to this block in source order.
    lines: list[ParsedBTLine] = field(default_factory=list)

    @property
    def seed_line(self) -> ParsedBTLine:
        """
        Return the first parsed line that seeded this block.

        Returns:
            Seed parsed line for the block.

        """
        return self.lines[0]

    @property
    def max_line_no(self) -> int:
        """
        Return the highest source line number attached to this block.

        Returns:
            Maximum ``raw_line.line_no`` among attached lines, or ``0``.

        """
        line_nos = [
            line.raw_line.line_no
            for line in self.lines
            if line.raw_line is not None
        ]
        return max(line_nos, default=0)


class BTSourceBlockBuilder:
    """
    Group parsed Bosworth-Toller lines into source-order dictionary blocks.

    Responsibilities are limited to block formation and editorial-line
    attachment.  Sense consolidation and edit application belong to
    :class:`~wyrdcraeft.services.dictionary.editorial_merger.BTEditorialMerger`.

    Args:
        resolver: Optional target-resolver collaborator for editorial attachment.

    """

    def __init__(self, resolver: BTTargetResolver | None = None) -> None:
        """
        Initialise the builder with an optional target resolver.

        Args:
            resolver: Optional pre-built :class:`BTTargetResolver` instance.

        """
        #: Target-resolver collaborator.
        self.resolver: BTTargetResolver = resolver or BTTargetResolver()

    def build(self, parsed_lines: list[ParsedBTLine]) -> list[BTSourceBlock]:
        """
        Build ordered source blocks from parsed BT lines.

        Skipped lines are ignored.  MAIN lines start new blocks unless they are
        follow-on citation lines with ``pos=unknown`` for the same ``norm_key``.
        ADD / SUBSTITUTE / DELE / DELE_AND_ADD lines attach to the nearest
        preceding compatible block when possible; otherwise they seed a new
        block when they carry enough material to stand alone.

        Args:
            parsed_lines: Parsed lines in any order; sorted by source line number.

        Returns:
            Ordered source blocks preserving document order.

        """
        blocks: list[BTSourceBlock] = []
        ordered = sorted(
            (line for line in parsed_lines if line.skip_reason is None),
            key=lambda ln: ln.raw_line.line_no if ln.raw_line else 0,
        )

        for line in ordered:
            if line.raw_line is None:
                continue
            kind = line.raw_line.kind
            if kind == BTLineKind.CROSS_REF:
                continue

            norm_key = self._norm_key_for_line(line)
            if not norm_key:
                continue

            if kind == BTLineKind.MAIN:
                if (
                    line.pos == BTPos.UNKNOWN
                    and blocks
                    and blocks[-1].norm_key == norm_key
                ):
                    blocks[-1].lines.append(line)
                    continue
                blocks.append(self._new_block(blocks, norm_key, line.pos, line))
                continue

            target = self.resolver.resolve_block_for_line(line, blocks)
            if target is not None:
                target.lines.append(line)
                continue

            if self._can_seed_block(line):
                pos = line.pos if line.pos != BTPos.UNKNOWN else BTPos.UNKNOWN
                blocks.append(self._new_block(blocks, norm_key, pos, line))
                continue

            blocks.append(self._new_block(blocks, norm_key, line.pos, line))

        for entry_order, block in enumerate(blocks, start=1):
            block.entry_order = entry_order
        return blocks

    def _new_block(
        self,
        blocks: list[BTSourceBlock],
        norm_key: str,
        pos: BTPos,
        line: ParsedBTLine,
    ) -> BTSourceBlock:
        """
        Create one new source block seeded by *line*.

        Args:
            blocks: Blocks built so far.
            norm_key: Normalised lookup key for the new block.
            pos: Part of speech for the new block.
            line: Seed parsed line.

        Returns:
            Newly created source block with *line* attached.

        """
        return BTSourceBlock(
            source_block_index=len(blocks),
            entry_order=0,
            norm_key=norm_key,
            pos=pos,
            lines=[line],
        )

    @staticmethod
    def _norm_key_for_line(line: ParsedBTLine) -> str | None:
        """
        Return the normalised lookup key for one parsed line.

        Args:
            line: Parsed BT line.

        Returns:
            Normalised headword key, or ``None`` when unavailable.

        """
        if line.raw_line is None:
            return None
        return normalize_old_english(line.raw_line.headword_raw) or None

    @staticmethod
    def _can_seed_block(line: ParsedBTLine) -> bool:
        """
        Return ``True`` when an orphan editorial line may seed a block.

        Args:
            line: Parsed BT line without a resolved attachment target.

        Returns:
            ``True`` when the line can stand alone as a block seed.

        """
        if line.raw_line is None:
            return False
        kind = line.raw_line.kind
        if kind == BTLineKind.SUBSTITUTE and line.senses:
            return True
        return bool(kind == BTLineKind.ADD and line.senses)
