"""Pure presentation rules for the dictionary browse entry column."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wyrdcraeft.services.dictionary.browse_query import filter_display_variants
from wyrdcraeft.services.dictionary.definition_line import definition_line
from wyrdcraeft.services.dictionary.form_decode import format_bt_gender_label

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from wyrdcraeft.services.dictionary.browse_query import EntryDetails
    from wyrdcraeft.services.morphology.catalog.query import LemmaMorphClassSummary

#: Parts of speech that get a Class row.
_CLASSED_POS = frozenset({"verb", "noun", "adjective"})
#: Class value shown (dimmed) when a classed POS has no assignment.
_UNCLASSIFIED = "unclassified"
#: Leading POS prefix stripped from class labels.
_VERB_PREFIX = "verb, "


def strip_pos_prefix(label: str) -> str:
    """
    Strip a leading ``verb, `` prefix from a class label.

    Args:
        label: Catalog class display label.

    Returns:
        Label without the verb prefix.

    """
    return label.removeprefix(_VERB_PREFIX)


def class_row_value(pos: str, morph_class: LemmaMorphClassSummary | None) -> str | None:
    """
    Decide the Class row value for an entry.

    Args:
        pos: Dictionary part of speech.
        morph_class: Catalog morph-class summary, if any.

    Returns:
        ``None`` for no Class row, ``"unclassified"`` when a verb, noun or
        adjective has no class, otherwise the stripped class label.

    """
    if pos.strip().casefold() not in _CLASSED_POS:
        return None
    if morph_class is None or morph_class.is_unclassified:
        return _UNCLASSIFIED
    return strip_pos_prefix(morph_class.display_label)


def show_summary(details: EntryDetails) -> bool:
    """
    Decide whether the summary line adds anything beyond sense 1.

    Args:
        details: Entry details payload.

    Returns:
        ``False`` when the summary is empty or equals sense 1 after
        definition-line formatting; ``True`` otherwise.

    """
    summary = definition_line(details.pos, [details.summary_sense])
    if not summary:
        return False
    if not details.senses:
        return True
    return summary != definition_line(details.pos, [details.senses[0].gloss_en])


def _join(labels: Iterable[str]) -> str:
    """
    Join non-empty labels with commas.

    Args:
        labels: Candidate labels.

    Returns:
        Comma-separated labels or an empty string.

    """
    return ", ".join(label.strip() for label in labels if label.strip())


def key_value_rows(details: EntryDetails) -> list[tuple[str, str]]:
    """
    Build the key/value block rows: Variants, Class, Gender, Source.

    Args:
        details: Entry details payload.

    Returns:
        Ordered ``(label, value)`` pairs, omitting rows with no value.

    """
    morph_class = details.morph_class
    source = ""
    if morph_class is not None and not morph_class.is_unclassified:
        source = morph_class.assignment_source.strip()
    candidates = [
        ("Variants", _join(filter_display_variants(details.variants))),
        ("Class", class_row_value(details.pos, morph_class) or ""),
        ("Gender", _join(format_bt_gender_label(g) for g in details.genders)),
        ("Source", source),
    ]
    return [(label, value) for label, value in candidates if value]


def drop_empty_columns(
    columns: Sequence[str], rows: Sequence[Sequence[str]]
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """
    Remove columns whose cells are all empty.

    Args:
        columns: Column headings.
        rows: Row cells aligned with ``columns``.

    Returns:
        Kept headings and rows, preserving order.

    """
    keep = [i for i in range(len(columns)) if any(row[i].strip() for row in rows)]
    return (
        tuple(columns[i] for i in keep),
        tuple(tuple(row[i] for i in keep) for row in rows),
    )
