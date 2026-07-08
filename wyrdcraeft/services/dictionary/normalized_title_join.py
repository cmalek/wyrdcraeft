"""Shared morphology-to-dictionary join index keyed by normalized title."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from wyrdcraeft.services.markup import normalize_morphology_title

if TYPE_CHECKING:
    from collections.abc import Iterable


class NormalizedTitleJoinIndex:
    """
    In-memory resolver for macron-preserving ``normalized_title`` dictionary joins.

    Matching order for ``resolve_one`` and ``resolve_all``:
        1) Direct ``bt_entries`` hit on ``(normalized_title, pos)`` when POS is given.
        2) Direct ``bt_entries`` hit on ``normalized_title`` when exactly one entry
           exists across all POS values.
        3) ``bt_variants.normalized_title`` match, POS-filtered when POS is given.

    Args:
        entry_ids_by_title_pos: Entry ids keyed by ``(normalized_title, pos)``.
        entry_ids_by_title: Entry ids keyed by ``normalized_title`` only.
        variant_entry_ids_by_title_pos: Variant entry ids keyed by
            ``(normalized_title, pos)``.
        variant_entry_ids_by_title: Variant entry ids keyed by ``normalized_title``.

    """

    #: Entry ids keyed by ``(normalized_title, pos)``.
    _entry_ids_by_title_pos: dict[tuple[str, str], list[int]]
    #: Entry ids keyed by ``normalized_title`` only.
    _entry_ids_by_title: dict[str, list[int]]
    #: Variant entry ids keyed by ``(normalized_title, pos)``.
    _variant_entry_ids_by_title_pos: dict[tuple[str, str], list[int]]
    #: Variant entry ids keyed by ``normalized_title`` only.
    _variant_entry_ids_by_title: dict[str, list[int]]

    def __init__(
        self,
        *,
        entry_ids_by_title_pos: dict[tuple[str, str], list[int]],
        entry_ids_by_title: dict[str, list[int]],
        variant_entry_ids_by_title_pos: dict[tuple[str, str], list[int]],
        variant_entry_ids_by_title: dict[str, list[int]],
    ) -> None:
        """
        Initialize a preloaded normalized-title join index.

        Keyword Args:
            entry_ids_by_title_pos: Entry ids keyed by ``(normalized_title, pos)``.
            entry_ids_by_title: Entry ids keyed by ``normalized_title`` only.
            variant_entry_ids_by_title_pos: Variant entry ids keyed by
                ``(normalized_title, pos)``.
            variant_entry_ids_by_title: Variant entry ids keyed by
                ``normalized_title`` only.

        """
        #: Entry ids keyed by ``(normalized_title, pos)``.
        self._entry_ids_by_title_pos = entry_ids_by_title_pos
        #: Entry ids keyed by ``normalized_title`` only.
        self._entry_ids_by_title = entry_ids_by_title
        #: Variant entry ids keyed by ``(normalized_title, pos)``.
        self._variant_entry_ids_by_title_pos = variant_entry_ids_by_title_pos
        #: Variant entry ids keyed by ``normalized_title`` only.
        self._variant_entry_ids_by_title = variant_entry_ids_by_title

    @classmethod
    def from_entry_variant_rows(
        cls,
        entries: Iterable[tuple[int, str, str]],
        variants: Iterable[tuple[int, str, str]],
    ) -> NormalizedTitleJoinIndex:
        """
        Build a join index from dictionary entry and variant row tuples.

        Args:
            entries: ``(entry_id, normalized_title, pos)`` rows from ``bt_entries``.
            variants: ``(entry_id, normalized_title, pos)`` rows from ``bt_variants``
                where ``pos`` comes from the parent entry.

        Returns:
            Preloaded join index ready for ``resolve_one`` / ``resolve_all``.

        """
        entry_ids_by_title_pos: dict[tuple[str, str], list[int]] = defaultdict(list)
        entry_ids_by_title: dict[str, list[int]] = defaultdict(list)
        for entry_id, normalized_title, pos in entries:
            title_key = normalize_morphology_title(normalized_title)
            if not title_key:
                continue
            pos_key = pos.strip()
            if pos_key:
                entry_ids_by_title_pos[(title_key, pos_key)].append(entry_id)
            entry_ids_by_title[title_key].append(entry_id)

        for title_pos, entry_ids in entry_ids_by_title_pos.items():
            entry_ids_by_title_pos[title_pos] = sorted(set(entry_ids))
        for title, entry_ids in entry_ids_by_title.items():
            entry_ids_by_title[title] = sorted(set(entry_ids))

        variant_entry_ids_by_title_pos: dict[tuple[str, str], list[int]] = (
            defaultdict(list)
        )
        variant_entry_ids_by_title: dict[str, list[int]] = defaultdict(list)
        for entry_id, normalized_title, pos in variants:
            title_key = normalize_morphology_title(normalized_title)
            if not title_key:
                continue
            pos_key = pos.strip()
            variant_entry_ids_by_title[title_key].append(entry_id)
            if pos_key:
                variant_entry_ids_by_title_pos[(title_key, pos_key)].append(entry_id)

        for title_pos, entry_ids in variant_entry_ids_by_title_pos.items():
            variant_entry_ids_by_title_pos[title_pos] = cls._dedupe_sorted(entry_ids)
        for title, entry_ids in variant_entry_ids_by_title.items():
            variant_entry_ids_by_title[title] = cls._dedupe_sorted(entry_ids)

        return cls(
            entry_ids_by_title_pos=dict(entry_ids_by_title_pos),
            entry_ids_by_title=dict(entry_ids_by_title),
            variant_entry_ids_by_title_pos=dict(variant_entry_ids_by_title_pos),
            variant_entry_ids_by_title=dict(variant_entry_ids_by_title),
        )

    @staticmethod
    def _dedupe_sorted(entry_ids: list[int]) -> list[int]:
        """
        Return distinct entry ids in stable ascending order.

        Args:
            entry_ids: Candidate entry ids, possibly with duplicates.

        Returns:
            Distinct entry ids sorted ascending.

        """
        seen: set[int] = set()
        deduped: list[int] = []
        for entry_id in sorted(entry_ids):
            if entry_id in seen:
                continue
            seen.add(entry_id)
            deduped.append(entry_id)
        return deduped

    @staticmethod
    def _normalize_pos(pos: str | None) -> str | None:
        """
        Normalize an optional POS filter to a stored POS string.

        Args:
            pos: Optional part-of-speech filter.

        Returns:
            Stripped POS string, or ``None`` when no filter applies.

        """
        if pos is None:
            return None
        candidate = pos.strip()
        return candidate or None

    def resolve_all(self, title: str, pos: str | None = None) -> list[int]:
        """
        Resolve all matching dictionary entry ids for one morphology title.

        Args:
            title: Raw or normalized morphology lemma title.
            pos: Optional stored POS filter (for example ``noun``).

        Returns:
            Matching entry ids in stable ascending order, or an empty list.

        """
        title_key = normalize_morphology_title(title)
        if not title_key:
            return []

        pos_filter = self._normalize_pos(pos)
        if pos_filter is not None:
            direct_pos_matches = self._entry_ids_by_title_pos.get(
                (title_key, pos_filter),
                [],
            )
            if direct_pos_matches:
                return list(direct_pos_matches)

        direct_matches = self._entry_ids_by_title.get(title_key, [])
        if len(direct_matches) == 1:
            return list(direct_matches)

        if pos_filter is not None:
            return list(
                self._variant_entry_ids_by_title_pos.get((title_key, pos_filter), [])
            )
        return list(self._variant_entry_ids_by_title.get(title_key, []))

    def resolve_one(self, title: str, pos: str | None = None) -> int | None:
        """
        Resolve one dictionary entry id for one morphology title.

        Args:
            title: Raw or normalized morphology lemma title.
            pos: Optional stored POS filter (for example ``noun``).

        Returns:
            Matching entry id when the tier policy yields a single match,
            otherwise ``None``. Tier-1 direct ``(normalized_title, pos)``
            matches return ``None`` when more than one entry shares the title
            and POS (homograph ambiguity).

        """
        title_key = normalize_morphology_title(title)
        if not title_key:
            return None

        pos_filter = self._normalize_pos(pos)
        if pos_filter is not None:
            direct_pos_matches = self._entry_ids_by_title_pos.get(
                (title_key, pos_filter),
                [],
            )
            if len(direct_pos_matches) == 1:
                return direct_pos_matches[0]
            if len(direct_pos_matches) > 1:
                return None

        direct_matches = self._entry_ids_by_title.get(title_key, [])
        if len(direct_matches) == 1:
            return direct_matches[0]

        if pos_filter is not None:
            variant_matches = self._variant_entry_ids_by_title_pos.get(
                (title_key, pos_filter),
                [],
            )
        else:
            variant_matches = self._variant_entry_ids_by_title.get(title_key, [])
        if len(variant_matches) == 1:
            return variant_matches[0]
        return None
