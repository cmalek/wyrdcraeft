"""
Section widgets for the dictionary browse entry column (ADR 0026).

The entry pane is one scrolling column: a key/value block, then ``Senses``,
``Etymology`` and ``Forms``. Each builder here returns ``None`` when its
section has no content, so the caller never mounts an empty section or its
label. Styling lives in ``browse.tcss``; inline spans use theme variables.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from textual.containers import Grid, Horizontal, Vertical
from textual.content import Content
from textual.widgets import DataTable, Rule, Static

from wyrdcraeft.services.dictionary.browse_results import DIM_STYLE
from wyrdcraeft.services.dictionary.entry_view import (
    drop_empty_columns,
    key_value_rows,
    show_summary,
)
from wyrdcraeft.services.dictionary.etymology_display import (
    EtymologyDisplay,
    parse_etymology_text,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from textual.widget import Widget

    from wyrdcraeft.services.dictionary.browse_query import EntryDetails, EntrySense

#: Class carried by every mountable entry section.
SECTION_CLASS = "entry-section"
#: Theme style for a main sense number: accent and bold.
MAIN_SENSE_STYLE = "bold $primary"
#: Class value drawn dim so a data gap stays visible.
_UNCLASSIFIED = "unclassified"
#: Sub-sense display label such as ``5a`` or ``10c``.
_SUB_SENSE_RE = re.compile(r"^\d+[a-z]")
#: Etymology table headings, in ``EtymologyTableRow`` field order.
_ETYMOLOGY_COLUMNS = ("LANGUAGE", "WORD", "MEANING", "SOURCE")
#: Heading whose cells hold the cognate form, drawn in the forms colour.
_WORD_COLUMN = "WORD"


class SectionLabel(Horizontal):
    """
    Dim caps section label followed by a hairline rule.

    Args:
        title: Section name; drawn upper-case.

    """

    def __init__(self, title: str) -> None:
        """
        Build the label row.

        Args:
            title: Section name; drawn upper-case.

        """
        super().__init__(
            Static(title.upper(), classes="section-label-text"),
            Rule(line_style="solid", classes="section-rule"),
            classes="section-label",
        )


def is_sub_sense(label: str) -> bool:
    """
    Decide whether a sense display label names a sub-sense.

    Args:
        label: Display label such as ``5`` or ``5a``.

    Returns:
        ``True`` for labels like ``5a`` and ``10c``.

    """
    return bool(_SUB_SENSE_RE.match(label.strip()))


def sense_number(label: str) -> Content:
    """
    Build the drawn number for one sense.

    Args:
        label: Display label such as ``5`` or ``5a``; may be empty.

    Returns:
        ``5.`` accent and bold for a main sense, ``5a.`` dim for a
        sub-sense, empty content for an unlabelled sense.

    """
    label = label.strip()
    if not label:
        return Content("")
    style = DIM_STYLE if is_sub_sense(label) else MAIN_SENSE_STYLE
    return Content.styled(f"{label}.", style)


def key_value_cells(details: EntryDetails) -> list[tuple[str, Content]]:
    """
    Build the key/value block cells from the entry presentation rules.

    Args:
        details: Entry details payload.

    Returns:
        ``(label, value)`` pairs; an ``unclassified`` Class value is dim.

    """
    cells: list[tuple[str, Content]] = []
    for label, value in key_value_rows(details):
        if label == "Class" and value == _UNCLASSIFIED:
            cells.append((label, Content.styled(value, DIM_STYLE)))
        else:
            cells.append((label, Content(value)))
    return cells


def etymology_table(
    display: EtymologyDisplay,
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """
    Build the etymology table, dropping columns that are empty in every row.

    Args:
        display: Parsed etymology payload.

    Returns:
        Kept headings and row cells.

    """
    rows = [
        (row.lang_source, row.word, row.meaning, row.source)
        for row in display.references
    ]
    return drop_empty_columns(_ETYMOLOGY_COLUMNS, rows)


def build_key_values(details: EntryDetails) -> Widget | None:
    """
    Build the key/value block (Variants, Class, Gender, Source).

    Args:
        details: Entry details payload.

    Returns:
        The ``#entry-keyvalues`` grid, or ``None`` when no row has a value.

    """
    cells = key_value_cells(details)
    if not cells:
        return None
    widgets: list[Widget] = []
    for label, value in cells:
        widgets.append(Static(label, classes="kv-label"))
        widgets.append(Static(value, classes="kv-value"))
    return Grid(*widgets, id="entry-keyvalues", classes=SECTION_CLASS)


def _sense_row(sense: EntrySense) -> Widget:
    """
    Build one sense row: number cell, then the wrapping gloss.

    Args:
        sense: Dictionary sense with a non-empty gloss.

    Returns:
        A ``.sense-row``; sub-senses also carry ``.sub-sense``.

    """
    classes = "sense-row sub-sense" if is_sub_sense(sense.sense_label) else "sense-row"
    return Horizontal(
        Static(sense_number(sense.sense_label), classes="sense-number"),
        Static(sense.gloss_en.strip(), classes="sense-gloss"),
        classes=classes,
    )


def build_senses(details: EntryDetails) -> Widget | None:
    """
    Build the Senses section, led by the summary when it adds anything.

    Args:
        details: Entry details payload.

    Returns:
        The ``#entry-senses`` section, or ``None`` with nothing to show.

    """
    lines: list[Widget] = []
    if show_summary(details):
        lines.append(Static(details.summary_sense.strip(), classes="senses-summary"))
    lines.extend(
        _sense_row(sense) for sense in details.senses if sense.gloss_en.strip()
    )
    if not lines:
        return None
    return Vertical(
        SectionLabel("Senses"),
        *lines,
        id="entry-senses",
        classes=SECTION_CLASS,
    )


def _etymology_grid(
    columns: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> Grid:
    """
    Build the etymology table grid: a dim heading row, then one row per cognate.

    Args:
        columns: Kept column headings.
        rows: Row cells aligned with ``columns``.

    Returns:
        ``.ety-table`` grid whose last column takes the remaining width.

    """
    cells: list[Widget] = [Static(name, classes="ety-head") for name in columns]
    for row in rows:
        for name, cell in zip(columns, row, strict=True):
            classes = "ety-cell ety-word" if name == _WORD_COLUMN else "ety-cell"
            cells.append(Static(cell, classes=classes))
    grid = Grid(*cells, classes="ety-table")
    grid.styles.grid_size_columns = len(columns)
    grid.styles.grid_columns = " ".join(["auto"] * (len(columns) - 1) + ["1fr"])
    return grid


def _etymology_lines(display: EtymologyDisplay, raw: str) -> list[Widget]:
    """
    Build the etymology body: table and notes, or the best plain fallback.

    Args:
        display: Parsed etymology payload.
        raw: Stored etymology text, used when nothing parses.

    Returns:
        Widgets drawn under the Etymology label.

    """
    lines: list[Widget] = []
    columns, rows = etymology_table(display)
    if columns:
        lines.append(_etymology_grid(columns, rows))
        lines.extend(
            Static(f"Note: {fragment}", classes="ety-note")
            for fragment in display.unparsed
        )
    elif display.unparsed and not display.attestations:
        lines.append(Static(display.unparsed[0], classes="ety-text"))
    if display.attestations:
        warning = "Misplaced attestations (not etymology)"
        lines.append(Static(Content.styled(warning, DIM_STYLE), classes="ety-warning"))
        for row in display.attestations:
            text = row.word.strip()
            if row.source:
                text = f"{text} [{row.source}]" if text else row.source
            if text:
                lines.append(Static(text, classes="ety-text"))
    if not lines:
        lines.append(Static(raw, classes="ety-text"))
    return lines


def build_etymology(details: EntryDetails) -> Widget | None:
    """
    Build the Etymology section.

    Args:
        details: Entry details payload.

    Returns:
        The ``#entry-etymology`` section, or ``None`` with no etymology.

    """
    raw = details.etymology.strip()
    if not raw:
        return None
    return Vertical(
        SectionLabel("Etymology"),
        *_etymology_lines(parse_etymology_text(raw), raw),
        id="entry-etymology",
        classes=SECTION_CLASS,
    )


def build_forms() -> Widget:
    """
    Build the Forms section around the single morphology table.

    The caller mounts it only when the paradigm sidebar has sections, then
    fills ``#morphology-table``.

    Returns:
        The ``#entry-forms`` section.

    """
    table: DataTable = DataTable(id="morphology-table", zebra_stripes=True)
    table.cursor_type = "none"
    return Vertical(
        SectionLabel("Forms"),
        table,
        id="entry-forms",
        classes=SECTION_CLASS,
    )


def build_text_sections(details: EntryDetails) -> list[Widget]:
    """
    Build the key/value block, Senses and Etymology, skipping empty ones.

    Args:
        details: Entry details payload.

    Returns:
        Sections in column order, without ``Forms``.

    """
    sections = (
        build_key_values(details),
        build_senses(details),
        build_etymology(details),
    )
    return [section for section in sections if section is not None]


__all__ = [
    "SECTION_CLASS",
    "SectionLabel",
    "build_etymology",
    "build_forms",
    "build_key_values",
    "build_senses",
    "build_text_sections",
    "etymology_table",
    "is_sub_sense",
    "key_value_cells",
    "sense_number",
]
