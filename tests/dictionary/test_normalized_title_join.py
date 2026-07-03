"""Unit tests for NormalizedTitleJoinIndex."""

from __future__ import annotations

from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)


def _index(
    *,
    entries: list[tuple[int, str, str]] | None = None,
    variants: list[tuple[int, str, str]] | None = None,
) -> NormalizedTitleJoinIndex:
    return NormalizedTitleJoinIndex.from_entry_variant_rows(
        entries or [],
        variants or [],
    )


def test_resolve_all_pos_direct_single_match() -> None:
    index = _index(entries=[(10, "abbad", "noun")])

    assert index.resolve_all("abbad", "noun") == [10]
    assert index.resolve_one("abbad", "noun") == 10


def test_resolve_all_pos_direct_multiple_matches() -> None:
    index = _index(
        entries=[
            (10, "work", "noun"),
            (20, "work", "verb"),
        ]
    )

    assert index.resolve_all("work", "noun") == [10]
    assert index.resolve_all("work", "verb") == [20]
    assert index.resolve_one("work", "noun") == 10
    assert index.resolve_one("work", "verb") == 20


def test_resolve_all_exactly_one_title_across_pos() -> None:
    index = _index(entries=[(42, "unique", "noun")])

    assert index.resolve_all("unique") == [42]
    assert index.resolve_one("unique") == 42


def test_resolve_all_variant_with_pos_filter() -> None:
    index = _index(
        entries=[(1, "abbad", "noun")],
        variants=[(1, "abbod", "noun")],
    )

    assert index.resolve_all("abbod", "noun") == [1]
    assert index.resolve_one("abbod", "noun") == 1


def test_resolve_all_variant_without_pos_filter() -> None:
    index = _index(
        entries=[(1, "abbad", "noun")],
        variants=[(1, "abbod", "noun")],
    )

    assert index.resolve_all("abbod") == [1]
    assert index.resolve_one("abbod") == 1


def test_resolve_one_variant_pos_filter_excludes_wrong_pos() -> None:
    index = _index(
        entries=[
            (1, "abbad", "noun"),
            (2, "other", "verb"),
        ],
        variants=[(1, "abbod", "noun")],
    )

    assert index.resolve_one("abbod", "verb") is None
    assert index.resolve_one("abbod", "noun") == 1


def test_resolve_one_tier_one_multi_match_returns_min_id() -> None:
    index = _index(
        entries=[
            (10, "dup", "noun"),
            (20, "dup", "noun"),
        ]
    )

    assert index.resolve_all("dup", "noun") == [10, 20]
    assert index.resolve_one("dup", "noun") == 10


def test_resolve_all_no_match() -> None:
    index = _index(entries=[(1, "abbad", "noun")])

    assert index.resolve_all("missing") == []
    assert index.resolve_one("missing") is None


def test_resolve_one_returns_none_for_ambiguous_variant_matches() -> None:
    index = _index(
        entries=[
            (1, "alpha", "noun"),
            (2, "beta", "noun"),
        ],
        variants=[
            (1, "alias", "noun"),
            (2, "alias", "noun"),
        ],
    )

    assert index.resolve_all("alias", "noun") == [1, 2]
    assert index.resolve_one("alias", "noun") is None


def test_resolve_normalizes_title_input() -> None:
    index = _index(entries=[(7, "abbad", "noun")])

    assert index.resolve_one("  AbbAD  ", "noun") == 7
