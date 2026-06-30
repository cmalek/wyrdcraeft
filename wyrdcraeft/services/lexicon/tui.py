"""Textual shell for lexicon browse workflow."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, ListItem, ListView, Static

from wyrdcraeft.services.lexicon.build import check_lexicon_staleness
from wyrdcraeft.services.lexicon.form_decode import (
    MorphologyRowPayload,
    ParadigmSidebarSpec,
    build_paradigm_sidebar,
    filter_display_variants,
    format_bt_gender_label,
    format_noun_declension,
    format_verb_class,
    morphology_row_matches_pos,
)
from wyrdcraeft.services.lexicon.progress import (
    LexiconBrowseStartupStage,
    run_browse_startup_progress,
)
from wyrdcraeft.services.lexicon.query import (
    EntryDetails,
    LexiconQueryService,
    MorphologyGroup,
    MorphologyRow,
    OrphanDetails,
    OrphanHit,
    SearchHit,
)
from wyrdcraeft.services.markup import normalize_old_english

if TYPE_CHECKING:
    from pathlib import Path

#: Insertable Old English characters for the browse search bar.
_OE_INSERT_CHARACTERS: tuple[str, ...] = (
    "æ",
    "Æ",
    "þ",
    "Þ",
    "ð",
    "Ð",
    "ā",
    "Ā",
    "ē",
    "Ē",
    "ī",
    "Ī",
    "ō",
    "Ō",
    "ū",
    "Ū",
    "ȳ",
    "Ȳ",
    "ǣ",
    "Ǣ",
    "ċ",
    "Ċ",
    "ġ",
    "Ġ",
)


class LexiconBrowseDataError(RuntimeError):
    """Raised when lexicon browse data is unavailable for the TUI shell."""


class OldEnglishSearchInput(Vertical):
    """
    Search input with optional Old English character insert buttons.

    Keyboard entry is the primary path: when the search field is focused,
    printable æ/þ/ð/macron/dot characters from the terminal are accepted
    directly. The character bar below the field is a fallback for terminals
    that cannot deliver those keys as printable input.
    """

    class Submitted(Message):
        """Posted when the search input is submitted."""

        def __init__(self, value: str) -> None:
            """
            Initialize one submitted-search message.

            Args:
                value: Search string submitted by the user.

            """
            super().__init__()
            #: Search string submitted by the user.
            self.value = value

    def compose(self) -> ComposeResult:
        """
        Compose the character bar and search input.

        Returns:
            Textual widget tree for Old English search entry.

        """
        yield Input(
            placeholder="Search lexicon (press Enter)",
            id="search-input",
        )
        with Horizontal(id="oe-char-bar"):
            for character in _OE_INSERT_CHARACTERS:
                yield Button(character, classes="oe-char-button")

    def on_mount(self) -> None:
        """
        Focus the search input and keep character buttons mouse-only.

        Side Effects:
            Focuses ``#search-input`` and disables tab focus on OE buttons.

        """
        self.focus_search()
        for button in self.query(".oe-char-button"):
            button.can_focus = False

    def focus_search(self) -> None:
        """Return keyboard focus to the search input field."""
        self.query_one("#search-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Insert one Old English character at the search input cursor.

        Args:
            event: Textual button press event.

        Side Effects:
            Inserts the pressed character into the search input.

        """
        if not event.button.has_class("oe-char-button"):
            return
        search = self.query_one("#search-input", Input)
        character = getattr(event.button.label, "plain", str(event.button.label))
        search.insert_text_at_cursor(character)
        self.focus_search()
        event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Bubble search submission to browse app listeners.

        Args:
            event: Textual input submission event.

        """
        if event.input.id != "search-input":
            return
        self.post_message(self.Submitted(event.value))


class _MainResultItem(ListItem):
    """
    List row for one dictionary-backed search hit.

    Args:
        hit: Search hit rendered in the main results list.

    """

    def __init__(self, hit: SearchHit) -> None:
        """
        Build one main-result list row with headword and POS labels.

        Args:
            hit: Dictionary-backed search hit to display.

        """
        super().__init__(Static(_format_main_result_label(hit)))
        #: Search hit rendered in the main results list.
        self.hit = hit


class _OrphanResultItem(ListItem):
    """
    List row for one morphology-only orphan search hit.

    Args:
        hit: Orphan search hit rendered in the lower results section.

    """

    def __init__(self, hit: OrphanHit) -> None:
        """
        Build one orphan-result list row with lemma and morphology labels.

        Args:
            hit: Morphology-only search hit to display.

        """
        super().__init__(Static(_format_orphan_result_label(hit)))
        #: Orphan search hit rendered in the lower results section.
        self.hit = hit


def _format_main_result_label(hit: SearchHit) -> str:
    """
    Format a main results row with headword and POS for homograph disambiguation.

    Args:
        hit: Dictionary-backed search hit.

    Returns:
        Single-line label for a main results list row.

    """
    pos = hit.pos.strip() or "unknown"
    headword_norm = normalize_old_english(hit.headword) or ""
    matched_norm = normalize_old_english(hit.matched_text) or ""
    if hit.rank_tier > 1 and matched_norm and matched_norm != headword_norm:
        return f"{hit.matched_text} ({hit.headword}, {pos})"
    return f"{hit.headword} ({pos})"


def _format_orphan_result_label(hit: OrphanHit) -> str:
    """
    Format an orphan results row with lemma and morphology labels.

    Args:
        hit: Morphology-only search hit.

    Returns:
        Single-line label for an orphan results list row.

    """
    wordclass = hit.wordclass.strip()
    function = hit.function.strip()
    if wordclass and function:
        return f"{hit.lemma} [{wordclass}, {function}]"
    if wordclass:
        return f"{hit.lemma} [{wordclass}]"
    return hit.lemma


def _join_labels(labels: Iterable[str]) -> str:
    """
    Join non-empty labels for compact metadata display.

    Args:
        labels: Candidate label strings.

    Returns:
        Comma-separated labels, or an empty string when none are present.

    """
    values = [label.strip() for label in labels if label.strip()]
    return ", ".join(values)


def _filter_morphology_rows(
    rows: list[MorphologyRow],
    *,
    entry_pos: str,
) -> list[MorphologyRow]:
    """
    Keep morphology rows that match the dictionary entry part of speech.

    Args:
        rows: Morphology rows linked to one dictionary entry.

    Keyword Args:
        entry_pos: Dictionary entry POS label.

    Returns:
        Rows whose ``wordclass`` matches ``entry_pos``.

    """
    if not entry_pos.strip():
        return rows
    return [
        row
        for row in rows
        if morphology_row_matches_pos(wordclass=row.wordclass, entry_pos=entry_pos)
    ]


def _morphology_rows_from_groups(groups: list[MorphologyGroup]) -> list[MorphologyRow]:
    """
    Flatten grouped morphology rows while preserving group order.

    Args:
        groups: Morphology groups from the query service.

    Returns:
        Flat morphology row list.

    """
    rows: list[MorphologyRow] = []
    for group in groups:
        rows.extend(group.rows)
    return rows


def _filter_morphology_rows_for_entry(
    rows: list[MorphologyRow],
    *,
    headword: str,
    entry_pos: str,
) -> list[MorphologyRow]:
    """
    Keep morphology rows that match the dictionary entry headword and POS.

    Args:
        rows: Morphology rows linked to one dictionary entry.

    Keyword Args:
        headword: Dictionary headword for the selected entry.
        entry_pos: Dictionary entry POS label.

    Returns:
        Rows whose lemma/title matches the headword and POS filter.

    """
    pos_filtered = _filter_morphology_rows(rows, entry_pos=entry_pos)
    headword_norm = normalize_old_english(headword) or ""
    if not headword_norm:
        return pos_filtered
    filtered: list[MorphologyRow] = []
    for row in pos_filtered:
        for candidate in (row.lemma, row.title):
            candidate_norm = normalize_old_english(candidate) or ""
            if candidate_norm == headword_norm or candidate_norm.endswith(
                headword_norm
            ):
                filtered.append(row)
                break
    return filtered


def _dedupe_morphology_rows(rows: list[MorphologyRow]) -> list[MorphologyRow]:
    """
    Keep one morphology row per function and normalized surface form.

    Args:
        rows: Candidate morphology rows for sidebar rendering.

    Returns:
        Deduped rows preserving first-seen order.

    """
    seen: set[tuple[str, str]] = set()
    deduped: list[MorphologyRow] = []
    for row in rows:
        surface = row.form.strip() or row.formi.strip()
        norm_surface = normalize_old_english(surface) or surface.casefold()
        key = (row.function.strip(), norm_surface)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _morphology_payloads(rows: list[MorphologyRow]) -> list[MorphologyRowPayload]:
    """
    Convert morphology dataclass rows into paradigm-builder payloads.

    Args:
        rows: Morphology rows for sidebar rendering.

    Returns:
        Payload rows for ``build_paradigm_sidebar``.

    """
    return [
        MorphologyRowPayload(
            form=row.form,
            formi=row.formi,
            function=row.function,
            wordclass=row.wordclass,
            class1=row.class1,
            class2=row.class2,
            class3=row.class3,
        )
        for row in rows
    ]


def _populate_morphology_table(
    table: DataTable,
    sidebar: ParadigmSidebarSpec,
) -> None:
    """
    Render paradigm sidebar sections into one scrollable data table.

    Args:
        table: Target morphology sidebar table widget.
        sidebar: POS-aware paradigm sidebar specification.

    Side Effects:
        Clears and repopulates ``table`` columns and rows.

    """
    table.clear(columns=True)
    if not sidebar.sections:
        table.add_column("form")
        table.add_row("No morphology rows linked.")
        return

    first = True
    for section in sidebar.sections:
        if not first:
            table.add_row(*([""] * len(table.columns)))
        first = False
        if section.title:
            if not table.columns:
                table.add_column(section.title)
                for column in section.columns[1:]:
                    table.add_column(column)
            elif len(table.columns) != len(section.columns):
                table.clear(columns=True)
                for column in section.columns:
                    table.add_column(column)
            else:
                table.add_row(section.title, *([""] * (len(section.columns) - 1)))
        elif not table.columns:
            for column in section.columns:
                table.add_column(column)
        for row in section.rows:
            table.add_row(*row)


def _populate_morphology_table_for_rows(
    table: DataTable,
    rows: list[MorphologyRow],
    *,
    wordclass: str,
    entry_genders: tuple[str, ...] = (),
) -> None:
    """
    Build and render POS-aware paradigm grids for morphology rows.

    Args:
        table: Target morphology sidebar table widget.
        rows: Morphology rows to display.

    Keyword Args:
        wordclass: Dominant morphology wordclass label.
        entry_genders: Gender markers stored on the dictionary entry.

    Side Effects:
        Clears and repopulates ``table`` columns and rows.

    """
    sidebar = build_paradigm_sidebar(
        _morphology_payloads(rows),
        wordclass=wordclass,
        entry_genders=entry_genders,
    )
    _populate_morphology_table(table, sidebar)


def _format_pos_label(pos: str) -> str:
    """
    Format one dictionary POS label for the details pane.

    Args:
        pos: Part-of-speech label stored on the dictionary entry.

    Returns:
        Display POS label.

    """
    return pos.strip() or "unknown"


def _format_class_lines(details: EntryDetails) -> list[str]:
    """
    Build class and declension lines for the details pane.

    Args:
        details: Entry details payload from the query service.

    Returns:
        Metadata lines describing morphology classes and declension.

    """
    lines: list[str] = []
    pos = details.pos.strip().casefold()
    if pos == "verb":
        classes = _ordered_verb_classes(details.morphology_groups)
        if classes:
            lines.append(f"Classes: {', '.join(classes)}")
        return lines
    if pos == "noun":
        inflections = _ordered_distinct_classes(
            [
                row.class1
                for group in details.morphology_groups
                for row in group.rows
                if row.class1.strip().casefold() in {"strong", "weak"}
            ]
        )
        if inflections:
            lines.append(f"Classes: {', '.join(inflections)}")
        declension = format_noun_declension(details.declension_paradigm)
        if declension:
            lines.append(f"Declension: {declension}")
        return lines
    class_summary = _ordered_distinct_classes(details.class_summary)
    if class_summary:
        lines.append(f"Classes: {', '.join(class_summary)}")
    return lines


def _ordered_distinct_classes(values: list[str]) -> list[str]:
    """
    Return ordered distinct non-empty class labels.

    Args:
        values: Candidate class labels.

    Returns:
        Ordered distinct class labels.

    """
    result: list[str] = []
    for value in values:
        candidate = value.strip()
        if candidate and candidate not in result:
            result.append(candidate)
    return result


def _ordered_verb_classes(groups: list[MorphologyGroup]) -> list[str]:
    """
    Return ordered distinct verb class labels for one entry.

    Args:
        groups: Morphology groups linked to the entry.

    Returns:
        Ordered verb class labels.

    """
    labels: list[str] = []
    for group in groups:
        for row in group.rows:
            label = format_verb_class(row.class1, row.class2, row.class3)
            if label and label not in labels:
                labels.append(label)
    return labels


def _format_entry_details(details: EntryDetails) -> str:
    """
    Format dictionary entry details with summary sense before the full sense list.

    Args:
        details: Entry details payload from the query service.

    Returns:
        Multi-line details pane text.

    """
    lines = [
        details.headword,
        f"POS: {_format_pos_label(details.pos)}",
    ]
    variants = _join_labels(filter_display_variants(details.variants))
    if variants:
        lines.append(f"Variants: {variants}")
    lines.extend(_format_class_lines(details))
    genders = _join_labels(format_bt_gender_label(gender) for gender in details.genders)
    if genders:
        lines.append(f"Gender: {genders}")
    if details.pos.strip().casefold() == "verb":
        persons = _join_labels(details.persons)
        if persons:
            lines.append(f"Person: {persons}")
        numbers = _join_labels(details.numbers)
        if numbers:
            lines.append(f"Number: {numbers}")

    lines.append("")
    summary = details.summary_sense.strip()
    if summary:
        lines.append("Summary")
        lines.append(summary)

    if details.senses:
        lines.append("")
        lines.append("Senses")
        for sense in details.senses:
            gloss = sense.gloss_en.strip()
            if not gloss:
                continue
            label = sense.sense_label.strip()
            if label:
                lines.append(f"{label}. {gloss}")
            else:
                lines.append(gloss)

    etymology = details.etymology.strip()
    if etymology:
        lines.append("")
        lines.append("Etymology")
        lines.append(etymology)

    return "\n".join(lines)


def _format_orphan_details(details: OrphanDetails) -> str:
    """
    Format morphology-only orphan details for the details pane.

    Args:
        details: Orphan details payload from the query service.

    Returns:
        Multi-line details pane text.

    """
    lines = [
        details.lemma,
        "Morphology-only form (no dictionary entry)",
    ]
    class_summary = _join_labels(_ordered_distinct_classes(details.class_summary))
    if class_summary:
        lines.append(f"Classes: {class_summary}")
    genders = _join_labels(format_bt_gender_label(gender) for gender in details.genders)
    if genders:
        lines.append(f"Gender: {genders}")
    persons = _join_labels(details.persons)
    if persons:
        lines.append(f"Person: {persons}")
    numbers = _join_labels(details.numbers)
    if numbers:
        lines.append(f"Number: {numbers}")
    return "\n".join(lines)


class LexiconBrowseApp(App[None]):
    """
    Textual browse app for unified lexicon search and read-only details.

    Args:
        query_service: Query service used for all lexicon data loading.
        db_path: Path to the morphology-backed lexicon database.

    """

    #: Textual stylesheet for the browse layout.
    CSS = """
  Screen {
      layout: vertical;
      overflow: hidden;
  }

  #search-box {
      height: auto;
  }

  #results-title,
  #details-title,
  #orphans-header {
      height: auto;
  }

  #search-input {
      margin: 1 1 0 1;
  }

  #oe-char-bar {
      height: auto;
      margin: 0 1 1 1;
  }

  .oe-char-button {
      min-width: 3;
      height: 1;
      margin: 0 1 0 0;
      padding: 0 1;
  }

  #body {
      layout: horizontal;
      height: 1fr;
      min-height: 0;
      overflow: hidden;
  }

  #results-pane {
      width: 1fr;
      height: 1fr;
      min-height: 0;
      layout: vertical;
      overflow: hidden;
      margin: 0 1 1 1;
      border: solid $accent;
  }

  #results-list {
      height: 1fr;
      min-height: 0;
  }

  #orphans-list {
      height: auto;
      max-height: 8;
      min-height: 0;
  }

  #details-pane {
      width: 2fr;
      height: 1fr;
      min-height: 0;
      layout: vertical;
      overflow: hidden;
      margin: 0 1 1 0;
      border: solid $accent;
  }

  #details-body {
      layout: vertical;
      height: 1fr;
      min-height: 0;
      overflow: hidden;
  }

  #details-content-scroll {
      height: 1fr;
      min-height: 0;
      width: 100%;
  }

  #details-content {
      width: 100%;
      height: auto;
      padding: 0 1;
  }

  #morphology-sidebar {
      width: 100%;
      height: 1fr;
      min-height: 0;
      border-top: solid $accent;
  }

  #morphology-table {
      height: auto;
      min-height: 0;
  }

  #orphans-header {
      margin: 1 0 0 0;
      text-style: bold;
  }

  #orphans-header.hidden {
      display: none;
  }

  #orphans-list.hidden {
      display: none;
  }
  """

    #: Query service used by the shell and browse interactions.
    query_service: LexiconQueryService
    #: Database path displayed in shell placeholders.
    db_path: Path
    #: Last main-result hits shown in the results pane.
    _main_hits: list[SearchHit]
    #: Last orphan hits shown in the lower results section.
    _orphan_hits: list[OrphanHit]
    #: Main dictionary-entry results list widget.
    _main_results_list: ListView
    #: Section header above orphan morphology hits.
    _orphans_header: Static
    #: Orphan morphology results list widget.
    _orphans_list: ListView
    #: Primary details text widget.
    _details_content: Static
    #: Scrollable morphology sidebar table widget.
    _morphology_table: DataTable
    #: Initial details-pane message shown before the first search.
    _initial_details_message: str

    def __init__(
        self,
        *,
        query_service: LexiconQueryService,
        db_path: Path,
        initial_details_message: str | None = None,
    ) -> None:
        """
        Initialize the lexicon browse shell.

        Keyword Args:
            query_service: Query service used for lexicon reads.
            db_path: Path to morphology SQLite containing ``lexicon_*`` tables.
            initial_details_message: Optional idle details text before first search.

        """
        super().__init__()
        #: Query service used by the shell and browse interactions.
        self.query_service = query_service
        #: Database path displayed in shell placeholders.
        self.db_path = db_path
        #: Last main-result hits shown in the results pane.
        self._main_hits = []
        #: Last orphan hits shown in the lower results section.
        self._orphan_hits = []
        default_message = (
            f"Connected to {db_path}. Search and select a result to view details."
        )
        #: Initial details-pane message shown before the first search.
        self._initial_details_message = initial_details_message or default_message

    def compose(self) -> ComposeResult:
        """
        Compose the browse shell layout.

        Returns:
            Textual widget tree for search, results, and details panes.

        """
        yield OldEnglishSearchInput(id="search-box")
        with Horizontal(id="body"):
            with Vertical(id="results-pane"):
                yield Static("Results", id="results-title")
                yield ListView(id="results-list")
                yield Static("Orphans", id="orphans-header", classes="hidden")
                yield ListView(id="orphans-list", classes="hidden")
            with Vertical(id="details-pane"):
                yield Static("Details", id="details-title")
                with Vertical(id="details-body"):
                    with ScrollableContainer(id="details-content-scroll"):
                        yield Static(
                            self._initial_details_message,
                            id="details-content",
                        )
                    with ScrollableContainer(id="morphology-sidebar"):
                        yield DataTable(id="morphology-table", zebra_stripes=True)

    def on_mount(self) -> None:
        """
        Cache browse pane widgets for stable access during event handling.

        Side Effects:
            Stores references to results and details pane widgets.

        """
        self._main_results_list = self.query_one("#results-list", ListView)
        self._orphans_header = self.query_one("#orphans-header", Static)
        self._orphans_list = self.query_one("#orphans-list", ListView)
        self._details_content = self.query_one("#details-content", Static)
        self._morphology_table = self.query_one("#morphology-table", DataTable)
        self._morphology_table.cursor_type = "none"

    def on_old_english_search_input_submitted(
        self,
        event: OldEnglishSearchInput.Submitted,
    ) -> None:
        """
        Run unified search when the user submits the search box.

        Args:
            event: Old English search submission event.

        Side Effects:
            Rebuilds results lists and may auto-focus a single main hit.

        """
        self._run_search(event.value)
        self.query_one("#search-box", OldEnglishSearchInput).focus_search()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Show details for a selected main or orphan search result.

        Args:
            event: Textual list selection event.

        Side Effects:
            Updates the details and morphology sidebar panes.

        """
        if event.list_view.id == "results-list":
            item = event.item
            if isinstance(item, _MainResultItem):
                self._show_entry_details(item.hit.entry_id)
            return

        if event.list_view.id == "orphans-list":
            item = event.item
            if isinstance(item, _OrphanResultItem):
                self._show_orphan_details(item.hit.form_id)

    def _run_search(self, query: str) -> None:
        """
        Execute unified search and refresh browse panes from query results.

        Args:
            query: Raw user-entered search string.

        Side Effects:
            Rebuilds results lists and may auto-focus one main hit.

        """
        results = self.query_service.search(query)
        self._main_hits = list(results.main_entries)
        self._orphan_hits = list(results.orphans)
        self._populate_results_lists()

        if results.main_entry_count == 1:
            self._main_results_list.index = 0
            self._show_entry_details(self._main_hits[0].entry_id)
            return

        if not self._main_hits and not self._orphan_hits:
            self._show_idle_details("No results.")
            return

        if not self._main_hits:
            self._show_idle_details(
                "No dictionary entries matched. Select an orphan below."
            )
            return

        self._show_idle_details("Select a result to view details.")

    def _populate_results_lists(self) -> None:
        """
        Rebuild main and orphan result list views from the last search.

        Side Effects:
            Clears and repopulates results list widgets.

        """
        main_list = self._main_results_list
        orphans_header = self._orphans_header
        orphans_list = self._orphans_list

        main_list.clear()
        if self._main_hits:
            for hit in self._main_hits:
                main_list.append(_MainResultItem(hit))
        else:
            main_list.append(
                ListItem(Static("No dictionary entries matched.")),
            )

        orphans_list.clear()
        if self._orphan_hits:
            orphans_header.remove_class("hidden")
            orphans_list.remove_class("hidden")
            for orphan_hit in self._orphan_hits:
                orphans_list.append(_OrphanResultItem(orphan_hit))
        else:
            orphans_header.add_class("hidden")
            orphans_list.add_class("hidden")

    def _show_entry_details(self, entry_id: int) -> None:
        """
        Load and render dictionary entry details in the details pane.

        Args:
            entry_id: Dictionary entry identifier from search results.

        Side Effects:
            Updates details and morphology sidebar widgets.

        """
        details = self.query_service.get_details(entry_id)
        if details is None:
            self._show_idle_details(f"Entry {entry_id} is unavailable.")
            return
        self._details_content.update(_format_entry_details(details))
        morphology_rows = _dedupe_morphology_rows(
            _filter_morphology_rows_for_entry(
                _morphology_rows_from_groups(details.morphology_groups),
                headword=details.headword,
                entry_pos=details.pos,
            )
        )
        wordclass = morphology_rows[0].wordclass if morphology_rows else details.pos
        _populate_morphology_table_for_rows(
            self._morphology_table,
            morphology_rows,
            wordclass=wordclass,
            entry_genders=tuple(details.genders),
        )

    def _show_orphan_details(self, form_id: int) -> None:
        """
        Load and render morphology-only orphan details in the details pane.

        Args:
            form_id: Morphology form identifier from orphan search results.

        Side Effects:
          Updates details and morphology sidebar widgets.

        """
        details = self.query_service.get_orphan_details(form_id)
        if details is None:
            self._show_idle_details(f"Orphan form {form_id} is unavailable.")
            return
        self._details_content.update(_format_orphan_details(details))
        morphology_rows = _dedupe_morphology_rows(
            _morphology_rows_from_groups(details.morphology_groups)
        )
        if morphology_rows:
            wordclass = morphology_rows[0].wordclass
            morphology_rows = [
                row for row in morphology_rows if row.wordclass == wordclass
            ]
        _populate_morphology_table_for_rows(
            self._morphology_table,
            morphology_rows,
            wordclass=morphology_rows[0].wordclass if morphology_rows else "morphology",
            entry_genders=tuple(details.genders),
        )

    def _show_idle_details(self, message: str) -> None:
        """
        Show a neutral details placeholder and clear the morphology sidebar.

        Args:
            message: Idle-state message for the details pane.

        Side Effects:
          Updates details and morphology sidebar widgets.

        """
        self._details_content.update(message)
        self._morphology_table.clear(columns=True)


def _ensure_browse_ready(query_service: LexiconQueryService) -> None:
    """
    Validate that browse tables exist and contain searchable rows.

    Args:
        query_service: Query service bound to a morphology SQLite database.

    Raises:
        LexiconBrowseDataError: Browse tables are missing or have no lexicon rows.

    """
    try:
        counts = query_service._connection.execute(  # noqa: SLF001
            """
            SELECT
                (SELECT COUNT(*) FROM lexicon_entries) AS entry_count,
                (SELECT COUNT(*) FROM lexicon_search_keys) AS key_count
            """
        ).fetchone()
    except sqlite3.OperationalError as exc:
        msg = (
            "Lexicon browse tables are missing. "
            "Run `wyrdcraeft lexicon build` for this morphology database first."
        )
        raise LexiconBrowseDataError(msg) from exc

    if (
        counts is not None
        and int(counts["entry_count"]) > 0
        and int(counts["key_count"]) > 0
    ):
        return

    msg = (
        "Lexicon browse tables are empty. "
        "Run `wyrdcraeft lexicon build` for this morphology database first."
    )
    raise LexiconBrowseDataError(msg)


def _format_browse_connect_message(db_path: Path) -> str:
    """
    Build the initial browse details placeholder, including staleness hints.

    Args:
        db_path: Path to the morphology SQLite database.

    Returns:
        Idle-state message shown before the first search.

    """
    lines = [
        f"Connected to {db_path}.",
        "Search and select a result to view details.",
    ]
    staleness = check_lexicon_staleness(db_path)
    if staleness.is_stale:
        lines.append(f"Note: {staleness.reason} Run `wyrdcraeft lexicon build`.")
    elif staleness.meta is not None:
        lines.append(f"Lexicon built at {staleness.meta.built_at}.")
    return " ".join(lines)


def create_lexicon_browse_app(db_path: Path) -> LexiconBrowseApp:
    """
    Build a validated lexicon browse shell instance for tests and CLI wiring.

    Args:
        db_path: Path to the morphology SQLite database.

    Returns:
        Ready-to-run Textual app shell with injected query service.

    Raises:
        LexiconBrowseDataError: Browse tables are missing or empty.

    """
    query_service = LexiconQueryService(db_path)
    try:
        _ensure_browse_ready(query_service)
    except LexiconBrowseDataError:
        query_service.close()
        raise
    return LexiconBrowseApp(
        query_service=query_service,
        db_path=db_path,
        initial_details_message=_format_browse_connect_message(db_path),
    )


def run_lexicon_browse(db_path: Path, *, show_progress: bool = True) -> None:
    """
    Launch the lexicon browse Textual shell for one morphology database.

    Args:
        db_path: Path to the morphology SQLite database.

    Keyword Args:
        show_progress: Whether to show stderr startup progress before the TUI opens.

    Side Effects:
        Starts an interactive Textual terminal app.

    Raises:
        LexiconBrowseDataError: Browse tables are missing or empty.

    """
    app: LexiconBrowseApp | None = None

    def _startup(stage: LexiconBrowseStartupStage) -> None:
        nonlocal app
        if stage == LexiconBrowseStartupStage.VALIDATE:
            app = create_lexicon_browse_app(db_path)

    run_browse_startup_progress(_startup, enabled=show_progress)
    if app is None:
        app = create_lexicon_browse_app(db_path)
    try:
        app.run()
    finally:
        app.query_service.close()
