"""
Wrapped paradigm tables and their tab switches for the browse entry (ADR 0027).

The Forms section shows one paradigm section at a time in a single
``DataTable``. Form cells wrap inside a forms column whose width comes from
the pane width, so no form is ever cut off. ``EntryColumn`` carries the
switch keys: ``left``/``right`` move along the primary axis (Present/Past,
Strong/Weak, Singular/Plural) and ``[``/``]`` along the secondary axis
(adjective degree). They live on the column because a focused
``VerticalScroll`` consumes ``left`` and ``right`` before app bindings run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from rich.cells import cell_len
from rich.style import Style
from rich.text import Text
from textual.binding import Binding, BindingType
from textual.containers import Vertical, VerticalScroll
from textual.content import Content
from textual.message import Message
from textual.widgets import DataTable, Static

from wyrdcraeft.services.dictionary.browse_entry import SECTION_CLASS, SectionLabel
from wyrdcraeft.services.dictionary.browse_results import DIM_STYLE

if TYPE_CHECKING:
    from collections.abc import Sequence

    from textual import events
    from textual.app import ComposeResult
    from textual.widget import Widget

    from wyrdcraeft.services.dictionary.paradigm_sidebar import ParadigmTableSection

#: Axis switched with ``left``/``right``.
PRIMARY = "primary"
#: Axis switched with ``[``/``]``.
SECONDARY = "secondary"
#: Narrowest forms column, in cells, before feature columns merge and wrap.
MIN_FORMS_WIDTH = 8
#: Column headings that hold features (row labels, person, degree), not forms.
_FEATURE_HEADERS = frozenset({"", "Person", "Degree"})
#: First heading of the generic decoded table, whose first column is the form.
_GENERIC_FORM_HEADER = "form"
#: Cell values that mean "no form" (switchable grids use ``""``, nouns ``-``).
_NO_FORM_CELLS = frozenset({"", "-"})
#: Theme style of the selected tab label.
_ACTIVE_TAB_STYLE = "bold underline $primary"
#: Key hint drawn after a tab strip that can switch.
_KEY_HINTS = {PRIMARY: "← →", SECONDARY: "[ ]"}

#: Column headings of a table.
Columns = tuple[str, ...]
#: Rows of a table, each aligned to its headings.
Rows = tuple[tuple[str, ...], ...]


def axis_values(sections: Sequence[ParadigmTableSection], axis: str) -> tuple[str, ...]:
    """
    List the distinct non-empty values of one switch axis.

    The order keeps every group's own order: if Strong has Positive and
    Superlative and Weak has all three degrees, the result is Positive,
    Comparative, Superlative.

    Args:
        sections: Paradigm sections of one entry, in display order.
        axis: ``primary`` or ``secondary``.

    Returns:
        The axis values in display order.

    """
    other = SECONDARY if axis == PRIMARY else PRIMARY
    first_seen = list(dict.fromkeys(v for s in sections if (v := getattr(s, axis))))
    before: dict[str, set[str]] = {value: set() for value in first_seen}
    groups: dict[str, list[str]] = {}
    for section in sections:
        if value := getattr(section, axis):
            group = groups.setdefault(getattr(section, other), [])
            before[value].update(earlier for earlier in group if earlier != value)
            group.append(value)
    ordered: list[str] = []
    while first_seen:
        ready = next(
            (value for value in first_seen if before[value] <= set(ordered)),
            first_seen[0],
        )
        ordered.append(ready)
        first_seen.remove(ready)
    return tuple(ordered)


class FormsSelection:
    """
    The selected primary and secondary tab over one entry's paradigm sections.

    Each axis keeps an index into its values. The secondary values are the
    union over every primary value, so a primary that lacks one (Strong with
    no Comparative) keeps the index stable and shows an empty state rather
    than jumping to another degree.

    Args:
        sections: Paradigm sections of one entry, in display order.

    """

    def __init__(self, sections: Sequence[ParadigmTableSection]) -> None:
        """
        Start on the first value of each axis.

        Args:
            sections: Paradigm sections of one entry, in display order.

        """
        #: Paradigm sections of the entry, in display order.
        self.sections = tuple(sections)
        #: Values of each axis, in first-seen order.
        self.values = {
            axis: axis_values(sections, axis) for axis in (PRIMARY, SECONDARY)
        }
        #: Selected index on each axis.
        self.indexes = {PRIMARY: 0, SECONDARY: 0}

    def axis_size(self, axis: str) -> int:
        """
        Count the values on one axis.

        Args:
            axis: ``primary`` or ``secondary``.

        Returns:
            The number of tabs on that axis.

        """
        return len(self.values.get(axis, ()))

    def selected(self, axis: str) -> str:
        """
        Return the selected value on one axis.

        Args:
            axis: ``primary`` or ``secondary``.

        Returns:
            The selected value, or ``""`` when the axis has no values.

        """
        values = self.values.get(axis, ())
        return values[self.indexes[axis]] if values else ""

    def step(self, axis: str, delta: int) -> bool:
        """
        Move the selection along one axis, stopping at either end.

        Args:
            axis: ``primary`` or ``secondary``.
            delta: ``-1`` for the previous tab, ``1`` for the next.

        Side Effects:
            Updates the axis index.

        Returns:
            Whether the selection changed.

        """
        size = self.axis_size(axis)
        if size < 2:  # noqa: PLR2004
            return False
        index = min(max(self.indexes[axis] + delta, 0), size - 1)
        changed = index != self.indexes[axis]
        self.indexes[axis] = index
        return changed

    def visible_section(self) -> ParadigmTableSection | None:
        """
        Return the section matching both selections.

        A section with no axis matches when the entry has no axes.

        Returns:
            The section to show, or ``None`` when that combination is missing.

        """
        primary, secondary = self.selected(PRIMARY), self.selected(SECONDARY)
        for section in self.sections:
            if section.primary == primary and section.secondary == secondary:
                return section
        return None

    def label(self) -> str:
        """
        Name the selected combination, for example ``Strong · Comparative``.

        Returns:
            The selected axis values joined by ``·``.

        """
        values = (self.selected(PRIMARY), self.selected(SECONDARY))
        return " · ".join(value for value in values if value)


def form_column_indexes(columns: Sequence[str]) -> frozenset[int]:
    """
    Find the columns that hold forms rather than features.

    Args:
        columns: Section column headings.

    Returns:
        Indexes of the form columns.

    """
    if columns and columns[0] == _GENERIC_FORM_HEADER:
        return frozenset({0})
    return frozenset(
        index for index, header in enumerate(columns) if header not in _FEATURE_HEADERS
    )


def _column_cells(columns: Sequence[str], rows: Rows, index: int) -> list[str]:
    """
    Return one column's heading and cells.

    Args:
        columns: Column headings.
        rows: Table rows.
        index: Column index.

    Returns:
        The heading followed by every cell of that column.

    """
    return [columns[index], *(row[index] for row in rows if index < len(row))]


def _feature_width(cells: Sequence[str], *, wrap: bool) -> int:
    """
    Measure a feature column, whole cells or (``wrap``) longest word.

    Args:
        cells: Heading and cells of the column.

    Keyword Args:
        wrap: Whether labels may wrap at spaces.

    Returns:
        The column content width.

    """
    if wrap:
        return max(cell_len(word) for cell in cells for word in [*cell.split(), ""])
    return max(cell_len(cell) for cell in cells)


def merge_feature_columns(columns: Sequence[str], rows: Rows) -> tuple[Columns, Rows]:
    """
    Fold every feature column into one leading label column.

    A narrow pane cannot fit a verb's label and Person columns beside its
    forms, so ``Indicative Sing`` and ``1`` become ``Indicative Sing 1``.

    Args:
        columns: Column headings.
        rows: Table rows.

    Returns:
        The headings and rows with one label column, then the form columns.

    """
    forms = form_column_indexes(columns)
    features = [index for index in range(len(columns)) if index not in forms]
    if len(features) < 2:  # noqa: PLR2004
        return tuple(columns), tuple(rows)
    order = sorted(forms)
    merged_rows = tuple(
        (
            " ".join(row[index] for index in features if row[index].strip()),
            *(row[index] for index in order),
        )
        for row in rows
    )
    return ("", *(columns[index] for index in order)), merged_rows


def fit_columns(
    section: ParadigmTableSection,
    available: int,
    cell_padding: int,
) -> tuple[Columns, Rows, tuple[int, ...]]:
    """
    Lay a section out so the table fits ``available`` cells.

    Feature columns keep their natural width when they can. When the forms
    would get less than ``MIN_FORMS_WIDTH``, the feature columns merge into
    one label column and then wrap at spaces. The form columns share what is
    left, never more than their longest cell, so their cells wrap instead of
    overflowing. Only in a pane too narrow even for that do the form columns
    drop below ``MIN_FORMS_WIDTH`` (one cell at least) and fold long forms,
    so the table still never needs a horizontal scrollbar.

    Args:
        section: The paradigm section to draw.
        available: Width the table may use, in cells.
        cell_padding: Padding on each side of every cell.

    Returns:
        Headings, rows and the content width of each column.

    """
    padded = 2 * cell_padding
    columns, rows = tuple(section.columns), section.rows
    for step in ("natural", "merge", "wrap"):
        if step == "merge":
            columns, rows = merge_feature_columns(columns, rows)
        forms = form_column_indexes(columns)
        widths = [
            max(map(cell_len, _column_cells(columns, rows, index)))
            if index in forms
            else _feature_width(
                _column_cells(columns, rows, index), wrap=step == "wrap"
            )
            for index in range(len(columns))
        ]
        fixed = sum(w + padded for i, w in enumerate(widths) if i not in forms)
        room = (available - fixed) // max(len(forms), 1) - padded
        if room >= MIN_FORMS_WIDTH:
            break
    form_widths = _share_room(
        {index: widths[index] for index in forms},
        available - fixed - padded * len(forms),
    )
    fitted = tuple(form_widths.get(i, w) for i, w in enumerate(widths))
    return columns, rows, fitted


def _share_room(natural: dict[int, int], room: int) -> dict[int, int]:
    """
    Share ``room`` cells among form columns, giving narrow ones only their need.

    A column whose longest cell fits an equal share keeps that width; what it
    leaves goes to the wider columns, which wrap at an equal share.

    Args:
        natural: Longest-cell width of each form column, by column index.
        room: Content cells available to all form columns together.

    Returns:
        Content width of each form column (one cell at least).

    """
    widths: dict[int, int] = {}
    pending = dict(natural)
    while pending:
        share = max(1, room // len(pending))
        fitting = {i: w for i, w in pending.items() if w <= share}
        if not fitting:
            widths.update(dict.fromkeys(pending, share))
            break
        widths.update(fitting)
        room -= sum(fitting.values())
        pending = {i: w for i, w in pending.items() if i not in fitting}
    return widths


def forms_cell(cell: str, color: str) -> Text:
    """
    Style one forms cell: every form in ``color`` at regular weight.

    No form is bold. The sidebar orders a cell's forms alphabetically and
    the model carries no citation marker (``forms.probability`` is an
    undocumented generator score, empty for many rows), so no form can
    honestly be marked as the citation spelling (ADR 0027).

    Args:
        cell: Forms joined by ``", "``, or a no-form placeholder.
        color: Resolved Old English form colour (the theme's ``accent``).

    Returns:
        A wrappable Rich ``Text``.

    """
    if cell.strip() in _NO_FORM_CELLS:
        return Text(cell, end="")
    text = Text(end="")
    text.append(cell, style=Style(color=color))
    return text


def fill_forms_table(
    table: DataTable,
    section: ParadigmTableSection,
    *,
    width: int,
    color: str,
) -> None:
    """
    Redraw ``table`` with one section whose form cells wrap.

    Every column gets a fixed ``add_column(width=...)`` and every row is
    added with ``add_row(..., height=None)``, so Textual measures each row's
    height and wraps the cells instead of cropping them. A ``flat`` section
    draws without a header row.

    Args:
        table: The forms table.
        section: The section to draw.

    Keyword Args:
        width: Width the table may use, in cells.
        color: Resolved Old English form colour.

    Side Effects:
        Clears and refills ``table`` columns and rows.

    """
    table.clear(columns=True)
    table.show_header = not section.flat
    columns, rows, widths = fit_columns(section, width, table.cell_padding)
    forms = form_column_indexes(columns)
    for header, column_width in zip(columns, widths, strict=True):
        table.add_column(header, width=column_width)
    for row in rows:
        cells = [
            forms_cell(cell, color) if index in forms else cell
            for index, cell in enumerate(row)
        ]
        table.add_row(*cells, height=None)


def tab_strip(values: Sequence[str], selected: str, axis: str) -> Content:
    """
    Draw one axis's tabs with the selected one bold and underlined.

    Args:
        values: Tab labels.
        selected: The selected label.
        axis: ``primary`` or ``secondary``; picks the key hint.

    Returns:
        The tab strip; the key hint follows only when there is a choice.

    """
    parts: list[str | tuple[str, str]] = []
    for index, value in enumerate(values):
        if index:
            parts.append("  ")
        parts.append((value, _ACTIVE_TAB_STYLE if value == selected else DIM_STYLE))
    if len(values) > 1:
        parts.extend(("   ", (_KEY_HINTS[axis], DIM_STYLE)))
    return Content.assemble(*parts)


class FormsSection(Vertical):
    """
    The ``#entry-forms`` section: label, tab strips, table and empty state.

    ``show`` draws the section that a ``FormsSelection`` picks. The table is
    never a tab stop and has no cursor.
    """

    def __init__(self) -> None:
        """Create the section with its fixed id and section class."""
        super().__init__(id="entry-forms", classes=SECTION_CLASS)

    def compose(self) -> ComposeResult:
        """
        Compose the label, the two tab strips, the empty line and the table.

        Returns:
            The section's child widgets.

        """
        yield SectionLabel("Forms")
        yield Static("", id="forms-tabs-primary", classes="forms-tabs")
        yield Static("", id="forms-tabs-secondary", classes="forms-tabs")
        yield Static("", id="forms-empty")
        table: DataTable = DataTable(
            id="morphology-table",
            zebra_stripes=True,
            cursor_type="none",
        )
        table.can_focus = False
        yield table

    def show(self, selection: FormsSelection, width: int) -> None:
        """
        Draw the tabs and the selected section, or the empty state.

        Args:
            selection: The entry's tab selection.
            width: Width the table may use, in cells.

        Side Effects:
            Updates the tab strips, the empty line and the table.

        """
        for axis in (PRIMARY, SECONDARY):
            strip = self.query_one(f"#forms-tabs-{axis}", Static)
            values = selection.values[axis]
            strip.display = bool(values)
            strip.update(tab_strip(values, selection.selected(axis), axis))
        section = selection.visible_section()
        table = self.query_one("#morphology-table", DataTable)
        empty = self.query_one("#forms-empty", Static)
        table.display = section is not None
        empty.display = section is None
        if section is None:
            empty.update(Content.styled(f"No {selection.label()} forms.", DIM_STYLE))
            return
        color = self.app.theme_variables["accent"]
        fill_forms_table(table, section, width=width, color=color)


class EntryColumn(VerticalScroll):
    """
    The entry pane's scrolling column, which also owns the forms switch keys.

    ``check_action`` lets a switch key act only when its axis has more than
    one value; otherwise the binding is hidden and the key does nothing.

    Args:
        *children: Initial child widgets.
        **kwargs: ``VerticalScroll`` keyword arguments such as ``id``.

    """

    #: Switch keys. They live here because a focused ``VerticalScroll`` uses
    #: ``left``/``right`` for scrolling before app-level bindings run.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("left", "switch('primary', -1)", "Previous table", key_display="←"),
        Binding("right", "switch('primary', 1)", "Next table", key_display="→"),
        Binding(
            "left_square_bracket",
            "switch('secondary', -1)",
            "Previous degree",
            key_display="[",
        ),
        Binding(
            "right_square_bracket",
            "switch('secondary', 1)",
            "Next degree",
            key_display="]",
        ),
    ]

    class Switch(Message):
        """
        A switch key asked to move one axis.

        Args:
            axis: ``primary`` or ``secondary``.
            step: ``-1`` or ``1``.

        """

        def __init__(self, axis: str, step: int) -> None:
            """
            Record the axis and direction.

            Args:
                axis: ``primary`` or ``secondary``.
                step: ``-1`` or ``1``.

            """
            super().__init__()
            #: Axis to move.
            self.axis = axis
            #: Direction to move.
            self.step = step

    class Resized(Message):
        """The column changed size, so the forms column needs a new width."""

    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        """
        Create the column with no switchable axis.

        Args:
            *children: Initial child widgets.

        Keyword Args:
            **kwargs: ``VerticalScroll`` keyword arguments such as ``id``.

        """
        super().__init__(*children, **kwargs)
        #: Number of tabs on each axis for the open entry.
        self._axis_sizes = {PRIMARY: 0, SECONDARY: 0}

    def set_axis_sizes(self, primary: int, secondary: int) -> None:
        """
        Record how many tabs each axis has.

        Args:
            primary: Tabs on the primary axis.
            secondary: Tabs on the secondary axis.

        Side Effects:
            Refreshes the bindings so the footer shows only usable keys.

        """
        self._axis_sizes = {PRIMARY: primary, SECONDARY: secondary}
        self.refresh_bindings()

    def check_action(
        self,
        action: str,
        parameters: tuple[object, ...],
    ) -> bool | None:
        """
        Allow a switch only on an axis with more than one tab.

        Args:
            action: Action name.
            parameters: Action parameters; the axis comes first.

        Returns:
            Whether the action may run.

        """
        if action != "switch":
            return True
        axis = str(parameters[0]) if parameters else ""
        return self._axis_sizes.get(axis, 0) > 1

    def action_switch(self, axis: str, step: int) -> None:
        """
        Ask the app to move one axis.

        Args:
            axis: ``primary`` or ``secondary``.
            step: ``-1`` or ``1``.

        Side Effects:
            Posts ``EntryColumn.Switch``.

        """
        self.post_message(self.Switch(axis, step))

    def on_resize(self, _event: events.Resize) -> None:
        """
        Tell the app the column width may have changed.

        Args:
            _event: Textual resize event.

        Side Effects:
            Posts ``EntryColumn.Resized``.

        """
        self.post_message(self.Resized())


__all__ = [
    "MIN_FORMS_WIDTH",
    "PRIMARY",
    "SECONDARY",
    "EntryColumn",
    "FormsSection",
    "FormsSelection",
    "axis_values",
    "fill_forms_table",
    "fit_columns",
    "form_column_indexes",
    "forms_cell",
    "merge_feature_columns",
    "tab_strip",
]
