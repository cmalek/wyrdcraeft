"""Textual shell for dictionary browse workflow."""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING, ClassVar, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

    from textual import events
    from textual.binding import BindingType

from sqlalchemy import text
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, ListItem, ListView, Static

from wyrdcraeft.services.dictionary.browse_progress import (
    DictionaryBrowseStartupStage,
    run_browse_startup_progress,
)
from wyrdcraeft.services.dictionary.browse_query import (
    BrowseSearchHit,
    DictionaryBrowseQueryService,
    EntryDetails,
    MorphologyGroup,
    MorphologyRow,
)
from wyrdcraeft.services.dictionary.etymology_display import (
    format_etymology_display,
    parse_etymology_text,
)
from wyrdcraeft.services.dictionary.form_decode import (
    MorphologyRowPayload,
    ParadigmSidebarSpec,
    build_paradigm_sidebar,
    filter_display_variants,
    format_bt_gender_label,
    morphology_row_matches_pos,
)
from wyrdcraeft.services.markup import normalize_old_english

if TYPE_CHECKING:
    from pathlib import Path


class _MorphClassLike(Protocol):
    """Structural morph-class payload used by browse detail formatters."""

    #: Display label for the assigned morphology class.
    display_label: str
    #: Provenance label describing how the class was assigned.
    assignment_source: str
    #: Whether the entry remains unclassified in the catalog.
    is_unclassified: bool


class _SenseLike(Protocol):
    """Structural dictionary sense payload used by browse detail formatters."""

    #: Source sense label such as ``I`` or ``II``.
    sense_label: str
    #: English gloss text for the sense.
    gloss_en: str


class _EntryDetailsLike(Protocol):
    """Structural detail payload accepted by shared browse text formatters."""

    #: Dictionary headword for the selected entry.
    headword: str
    #: Part-of-speech label stored on the dictionary entry.
    pos: str
    #: Display variant spellings linked to the entry.
    variants: list[str]
    #: Gender markers stored on the dictionary entry.
    genders: list[str]
    #: Person markers inferred from morphology rows.
    persons: list[str]
    #: Number markers inferred from morphology rows.
    numbers: list[str]
    #: First non-empty gloss summary for the entry.
    summary_sense: str
    #: Ordered dictionary senses for the entry.
    senses: list[_SenseLike]
    #: Etymology text stored on the dictionary entry.
    etymology: str
    #: Catalog morph-class summary for the entry, when present.
    morph_class: _MorphClassLike | None

#: Insertable/searchable Old English characters plus button display text.
_OE_BUTTONS: tuple[tuple[str, str], ...] = (
    ("æ", "æ"),
    ("þ", "þ"),
    ("ð", "ð"),
    ("ā", "ā"),
    ("ē", "ē"),
    ("ī", "ī"),
    ("ō", "ō"),
    ("ū", "ū"),
    ("ȳ", "ȳ"),
    ("ǣ", "ǣ"),
    ("ċ", "ċ"),
    ("ġ", "ġ"),
)

#: Canonical Old English characters inserted into the search field.
_OE_INSERT_CHARACTERS = tuple(
    insert_character for insert_character, _display in _OE_BUTTONS
)

#: Combining marks commonly produced by dead-key keyboard input for OE glyphs.
_OE_COMBINING_MARKS: tuple[str, ...] = (
    "\u0304",
    "\u0307",
)

#: Printable characters that should be accepted by app-level keyboard fallback.
_OE_KEYBOARD_CHARACTERS = frozenset(_OE_INSERT_CHARACTERS + _OE_COMBINING_MARKS)


def _key_name(character: str) -> str:
    """
    Build a Textual-style descriptive key name for one Unicode character.

    Args:
        character: Unicode character used for terminal key alias lookup.

    Returns:
        Lowercase underscore-separated Unicode name.

    """
    return unicodedata.name(character).lower().replace("-", "_").replace(" ", "_")


#: Non-printable terminal key aliases mapped to canonical insert text.
_OE_KEY_ALIASES = {
    **{_key_name(character): character for character in _OE_INSERT_CHARACTERS},
    "alt+apostrophe": "æ",
    "alt+shift+apostrophe": "Æ",
    "alt+d": "ð",
    "alt+shift+d": "Ð",
    "alt+t": "þ",
    "alt+shift+t": "Þ",
    "alt+a": "\u0304",
    "alt+w": "\u0307",
    "combining_macron": "\u0304",
    "combining_dot_above": "\u0307",
}


class DictionaryBrowseDataError(RuntimeError):
    """Raised when dictionary browse data is unavailable for the TUI shell."""


class OldEnglishSearchInput(Input):
    """Search input that accepts OE key aliases and paste-driven compose paths."""

    #: Pending combining mark from a macOS dead-key event.
    _pending_dead_key: str | None = None

    async def _on_key(self, event: events.Key) -> None:
        """
        Accept OE key aliases before Textual's default printable-key handling.

        Args:
            event: Textual key event delivered to the focused input.

        Side Effects:
            Inserts mapped OE text for non-printable alias keys.

        """
        alias = _OE_KEY_ALIASES.get(event.key) if event.character is None else None
        compose_target = event.character or alias
        if self._pending_dead_key is not None and compose_target:
            composed = unicodedata.normalize(
                "NFC",
                f"{compose_target}{self._pending_dead_key}",
            )
            self.insert_text_at_cursor(composed)
            self._pending_dead_key = None
            event.stop()
            event.prevent_default()
            return
        if event.character is None and alias is not None:
            if event.key in {"alt+a", "alt+w"}:
                self._pending_dead_key = alias
                event.stop()
                event.prevent_default()
                return
            self.insert_text_at_cursor(alias)
            event.stop()
            event.prevent_default()
            return
        await super()._on_key(event)

    def _on_paste(self, event: events.Paste) -> None:
        """
        Normalize pasted text so terminal compose/paste paths keep OE glyphs.

        Args:
            event: Textual paste event delivered to the focused input.

        Side Effects:
            Inserts the first pasted line at the cursor in NFC form.

        """
        if event.text:
            line = unicodedata.normalize("NFC", event.text.splitlines()[0])
            selection = self.selection
            if selection.is_empty:
                self.insert_text_at_cursor(line)
            else:
                self.replace(line, *selection)
        event.stop()


class _MainResultItem(ListItem):
    """
    List row for one dictionary-backed search hit.

    Args:
        hit: Search hit rendered in the main results list.

    """

    def __init__(self, hit: BrowseSearchHit) -> None:
        """
        Build one main-result list row with headword and POS labels.

        Args:
            hit: Dictionary-backed search hit to display.

        """
        super().__init__(Static(_format_main_result_label(hit)))
        #: Search hit rendered in the main results list.
        self.hit = hit


class _WrightSectionItem(ListItem):
    """
    Selectable list row for one Wright section citation.

    Args:
        section_no: Wright grammar section number linked to the selected class.

    """

    def __init__(self, section_no: int) -> None:
        """
        Build one Wright section selection row for the details pane.

        Args:
            section_no: Wright grammar section number linked to the selected class.

        """
        super().__init__(Static(f"Wright § {section_no}"))
        #: Wright grammar section number linked to the selected class.
        self.section_no = section_no


class WrightSectionTextScreen(ModalScreen[None]):
    """
    Modal overlay showing stored text for one Wright section citation.

    Args:
        section_no: Wright grammar section number shown in the overlay title.
        section_text: Stored section text or an actionable missing-ingest message.

    """

    #: Escape closes the overlay without leaving the browse app.
    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "close_overlay", "Close"),
    ]

    def __init__(self, *, section_no: int, section_text: str) -> None:
        """
        Initialize one Wright section modal overlay.

        Keyword Args:
            section_no: Wright grammar section number shown in the overlay title.
            section_text: Stored section text or an actionable missing-ingest message.

        """
        super().__init__()
        #: Wright grammar section number shown in the overlay title.
        self.section_no = section_no
        #: Stored section text or an actionable missing-ingest message.
        self.section_text = section_text

    def compose(self) -> ComposeResult:
        """
        Compose the Wright section modal overlay.

        Returns:
            Textual widget tree for the Wright section title, text, and close button.

        """
        with Vertical(id="wright-modal"):
            yield Static(f"Wright § {self.section_no}", id="wright-modal-title")
            with ScrollableContainer(id="wright-modal-scroll"):
                yield Static(self.section_text, id="wright-modal-text")
            yield Button("Close", id="wright-modal-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Close the overlay when the user activates the close button.

        Args:
            event: Textual button press event from the modal content.

        Side Effects:
            Pops the modal screen when the close button is pressed.

        """
        if event.button.id != "wright-modal-close":
            return
        self.app.pop_screen()
        event.stop()

    def action_close_overlay(self) -> None:
        """
        Dismiss the modal overlay from the Escape key binding.

        Side Effects:
            Pops the modal screen from the app stack.

        """
        self.app.pop_screen()


def _format_main_result_label(hit: BrowseSearchHit) -> str:
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
            if (
                candidate_norm == headword_norm
                or candidate_norm.endswith(headword_norm)
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
    Convert FK-backed morphology rows into paradigm-builder payloads.

    Args:
        rows: Morphology rows for sidebar rendering.

    Returns:
        Payload rows for ``build_paradigm_sidebar``.

    Note:
        Legacy ``forms.class1``-``class3`` columns were dropped in Phase D.
        Paradigm grids decode ``wordclass`` and ``function`` from FK joins and
        ``morph_classes`` strength metadata when available.

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
            inflection=row.inflection,
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


def _format_class_lines(details: _EntryDetailsLike) -> list[str]:
    """
    Build catalog morph-class lines for the details pane.

    Args:
        details: Entry details payload from the query service.

    Returns:
        Metadata lines describing catalog class and provenance.

    """
    morph_class = details.morph_class
    if morph_class is None or morph_class.is_unclassified:
        return ["Morph class: Unclassified"]
    lines = [f"Morph class: {morph_class.display_label}"]
    if morph_class.assignment_source.strip():
        lines.append(f"Provenance: {morph_class.assignment_source}")
    return lines


def _format_entry_header_text(details: _EntryDetailsLike) -> str:
    """
    Build the metadata header block for one entry's details pane.

    Args:
        details: Entry details payload from the query service.

    Returns:
        Multi-line header text with headword, POS, morph class, and metadata.

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
    return "\n".join(lines)


def _format_entry_body_text(details: _EntryDetailsLike) -> str:
    """
    Build the narrative body block for one entry's details pane.

    Args:
        details: Entry details payload from the query service.

    Returns:
        Summary, senses, and etymology text rendered below citation widgets.

    """
    lines: list[str] = []
    summary = details.summary_sense.strip()
    if summary:
        lines.append("Summary")
        lines.append(summary)
    if details.senses:
        if lines:
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
        if lines:
            lines.append("")
        formatted = format_etymology_display(parse_etymology_text(etymology))
        if formatted:
            lines.append(formatted)
        else:
            lines.append("Etymology")
            lines.append(etymology)
    return "\n".join(lines)


def _format_entry_details(details: _EntryDetailsLike) -> str:
    """
    Format dictionary entry details with summary sense before the full sense list.

    Args:
        details: Entry details payload from the query service.

    Returns:
        Multi-line details pane text.

    """
    header = _format_entry_header_text(details)
    body = _format_entry_body_text(details)
    if not body:
        return header
    return f"{header}\n\n{body}"


class DictionaryBrowseApp(App[None]):
    """
    Textual browse app for dictionary search and read-only details.

    Args:
        query_service: Query service used for all browse data loading.
        db_path: Path to the morphology-backed lexicon database.

    """

    #: Textual stylesheet for the browse layout.
    CSS = """
  Screen {
      layout: vertical;
      overflow: hidden;
  }

  #search-input {
      margin: 1 1 0 1;
  }

  #results-title,
  #details-title {
      height: auto;
  }

  #oe-char-bar {
      height: auto;
      margin: 0 1 1 1;
  }

  .oe-char-button {
      min-width: 4;
      height: auto;
      margin: 0 1 0 0;
      padding: 0 1;
      text-style: bold;
      color: #f6f7f9;
      background: #28313a;
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

  #wright-sections-title {
      height: auto;
      margin: 0 1;
      text-style: bold;
  }

  #wright-sections-list {
      height: auto;
      max-height: 10;
      margin: 0 1 1 1;
  }

  #details-body-content {
      width: 100%;
      height: auto;
      padding: 0 1 1 1;
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

  #wright-sections-title.hidden,
  #wright-sections-list.hidden {
      display: none;
  }

  WrightSectionTextScreen {
      align: center middle;
  }

  #wright-modal {
      width: 80%;
      height: 80%;
      border: solid $accent;
      background: $surface;
      padding: 1;
  }

  #wright-modal-title {
      height: auto;
      margin: 0 0 1 0;
      text-style: bold;
  }

  #wright-modal-scroll {
      height: 1fr;
      min-height: 0;
      width: 100%;
      border: solid $accent-darken-1;
      padding: 0 1;
      margin: 0 0 1 0;
  }

  #wright-modal-text {
      width: 100%;
      height: auto;
  }

  #wright-modal-close {
      width: 16;
  }
  """

    #: Query service used by the shell and browse interactions.
    query_service: DictionaryBrowseQueryService
    #: Database path displayed in shell placeholders.
    db_path: Path
    #: Last main-result hits shown in the results pane.
    _main_hits: list[BrowseSearchHit]
    #: Main dictionary-entry results list widget.
    _main_results_list: ListView
    #: Primary details header widget.
    _details_content: Static
    #: Title shown above the Wright section citation list.
    _wright_sections_title: Static
    #: Selectable Wright section citations for the current entry.
    _wright_sections_list: ListView
    #: Narrative details widget rendered below Wright section citations.
    _details_body_content: Static
    #: Scrollable morphology sidebar table widget.
    _morphology_table: DataTable
    #: Initial details-pane message shown before the first search.
    _initial_details_message: str

    def __init__(
        self,
        *,
        query_service: DictionaryBrowseQueryService,
        db_path: Path,
        initial_details_message: str | None = None,
    ) -> None:
        """
        Initialize the dictionary browse shell.

        Keyword Args:
            query_service: Query service used for browse reads.
            db_path: Path to canonical SQLite containing ``bt_*`` and ``forms``
                tables.
            initial_details_message: Optional idle details text before first search.

        """
        super().__init__()
        #: Query service used by the shell and browse interactions.
        self.query_service = query_service
        #: Database path displayed in shell placeholders.
        self.db_path = db_path
        #: Last main-result hits shown in the results pane.
        self._main_hits = []
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
        yield OldEnglishSearchInput(
            placeholder="Search dictionary (press Enter)",
            id="search-input",
        )
        with Horizontal(id="oe-char-bar"):
            for insert_character, display_text in _OE_BUTTONS:
                yield Button(
                    display_text,
                    name=insert_character,
                    classes="oe-char-button",
                    flat=True,
                )
        with Horizontal(id="body"):
            with Vertical(id="results-pane"):
                yield Static("Results", id="results-title")
                yield ListView(id="results-list")
            with Vertical(id="details-pane"):
                yield Static("Details", id="details-title")
                with Vertical(id="details-body"):
                    with ScrollableContainer(id="details-content-scroll"):
                        yield Static(
                            self._initial_details_message,
                            id="details-content",
                        )
                        yield Static(
                            "Wright Sections",
                            id="wright-sections-title",
                            classes="hidden",
                        )
                        yield ListView(id="wright-sections-list", classes="hidden")
                        yield Static("", id="details-body-content")
                    with ScrollableContainer(id="morphology-sidebar"):
                        yield DataTable(id="morphology-table", zebra_stripes=True)

    def on_mount(self) -> None:
        """
        Cache browse pane widgets for stable access during event handling.

        Side Effects:
            Stores references to results and details pane widgets, focuses the
            search input, and keeps OE buttons mouse-only.

        """
        self._main_results_list = self.query_one("#results-list", ListView)
        self._details_content = self.query_one("#details-content", Static)
        self._wright_sections_title = self.query_one("#wright-sections-title", Static)
        self._wright_sections_list = self.query_one("#wright-sections-list", ListView)
        self._details_body_content = self.query_one("#details-body-content", Static)
        self._morphology_table = self.query_one("#morphology-table", DataTable)
        self._morphology_table.cursor_type = "none"
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
        if event.button.has_class("oe-char-button"):
            search = self.query_one("#search-input", Input)
            character = event.button.name
            if character is None:
                character = getattr(
                    event.button.label,
                    "plain",
                    str(event.button.label),
                )
            search.insert_text_at_cursor(character)
            self.focus_search()
            event.stop()

    def on_key(self, event: events.Key) -> None:
        """
        Accept Old English keyboard characters at app level as a terminal fallback.

        Args:
            event: Textual key event that bubbled past the focused widget.

        Side Effects:
            Inserts supported OE characters into the search input when it has focus.

        """
        if event.character not in _OE_KEYBOARD_CHARACTERS:
            return
        search = self.query_one("#search-input", Input)
        if not search.has_focus:
            return
        search.insert_text_at_cursor(event.character)
        event.stop()
        event.prevent_default()

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Normalize search input text so dead-key combining marks become OE glyphs.

        Args:
            event: Textual input change event.

        Side Effects:
            Rewrites the search field value in NFC form when needed.

        """
        if event.input.id != "search-input":
            return
        normalized = unicodedata.normalize("NFC", event.value)
        if normalized == event.value:
            return
        cursor = event.input.cursor_position
        prefix = unicodedata.normalize("NFC", event.value[:cursor])
        event.input.value = normalized
        event.input.cursor_position = len(prefix)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Run browse search when the user submits the search box.

        Args:
            event: Textual input submission event.

        Side Effects:
            Rebuilds results list and may auto-focus a single hit.

        """
        if event.input.id != "search-input":
            return
        self._run_search(event.value)
        self.focus_search()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Show details for a selected search result or Wright section.

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

        if event.list_view.id == "wright-sections-list":
            item = event.item
            if isinstance(item, _WrightSectionItem):
                self._show_wright_section_text(item.section_no)

    def _run_search(self, query: str) -> None:
        """
        Execute search and refresh browse panes from query results.

        Args:
            query: Raw user-entered search string.

        Side Effects:
            Rebuilds results list and may auto-focus one hit.

        """
        self._main_hits = list(self.query_service.search(query))
        self._populate_results_list()

        if len(self._main_hits) == 1:
            self._main_results_list.index = 0
            self._show_entry_details(self._main_hits[0].entry_id)
            return

        if not self._main_hits:
            self._show_idle_details("No results.")
            return

        self._show_idle_details("Select a result to view details.")

    def _populate_results_list(self) -> None:
        """
        Rebuild the result list view from the last search.

        Side Effects:
            Clears and repopulates the results list widget.

        """
        self._main_results_list.clear()
        if self._main_hits:
            for hit in self._main_hits:
                self._main_results_list.append(_MainResultItem(hit))
            return
        self._main_results_list.append(ListItem(Static("No results.")))

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
        self._details_content.update(self._format_entry_header(details))
        self._details_body_content.update(self._format_entry_body(details))
        self._populate_wright_sections(details)
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

    def _show_idle_details(self, message: str) -> None:
        """
        Show a neutral details placeholder and clear the morphology sidebar.

        Args:
            message: Idle-state message for the details pane.

        Side Effects:
            Updates details and morphology sidebar widgets.

        """
        self._details_content.update(message)
        self._details_body_content.update("")
        self._clear_wright_sections()
        self._morphology_table.clear(columns=True)

    def _format_entry_header(self, details: EntryDetails) -> str:
        """
        Build the non-scroll-breaking header block for one entry's details pane.

        Args:
            details: Entry details payload from the query service.

        Returns:
            Multi-line header text with headword, POS, morph class, and metadata.

        """
        return _format_entry_header_text(cast("_EntryDetailsLike", details))

    def _format_entry_body(self, details: EntryDetails) -> str:
        """
        Build the narrative body block for one entry's details pane.

        Args:
            details: Entry details payload from the query service.

        Returns:
            Summary, senses, and etymology text rendered below citation widgets.

        """
        return _format_entry_body_text(cast("_EntryDetailsLike", details))

    def _populate_wright_sections(self, details: EntryDetails) -> None:
        """
        Show selectable Wright section citations for the current entry.

        Args:
            details: Entry details payload from the query service.

        Side Effects:
            Clears and repopulates the Wright section list in the details pane.

        """
        self._wright_sections_list.clear()
        section_numbers: tuple[int, ...] = ()
        if details.morph_class is not None and not details.morph_class.is_unclassified:
            section_numbers = details.morph_class.wright_sections
        if not section_numbers:
            self._wright_sections_title.add_class("hidden")
            self._wright_sections_list.add_class("hidden")
            return
        self._wright_sections_title.remove_class("hidden")
        self._wright_sections_list.remove_class("hidden")
        for section_no in section_numbers:
            self._wright_sections_list.append(_WrightSectionItem(section_no))

    def _clear_wright_sections(self) -> None:
        """
        Hide any previously rendered Wright section citations.

        Side Effects:
            Clears the Wright section list and hides its widgets.

        """
        self._wright_sections_list.clear()
        self._wright_sections_title.add_class("hidden")
        self._wright_sections_list.add_class("hidden")

    def _show_wright_section_text(self, section_no: int) -> None:
        """
        Open a modal overlay for one Wright section citation.

        Args:
            section_no: Wright grammar section number selected in the details pane.

        Side Effects:
            Pushes a modal screen showing stored section text or a
            missing-ingest message.

        """
        section_text = self.query_service.lookup_wright_section_text(section_no)
        if section_text is None or not section_text.strip():
            section_text = (
                f"Wright § {section_no} text not ingested — "
                "run dictionary ingest-wright-text"
            )
        self.push_screen(
            WrightSectionTextScreen(
                section_no=section_no,
                section_text=section_text.strip(),
            )
        )


def _ensure_browse_ready(query_service: DictionaryBrowseQueryService) -> None:
    """
    Validate that browse tables exist and contain searchable rows.

    Args:
        query_service: Query service bound to a morphology SQLite database.

    Raises:
        DictionaryBrowseDataError: Browse tables are missing or have no dictionary rows.

    """
    try:
        counts = query_service._connection.execute(  # noqa: SLF001
            text("SELECT COUNT(*) AS entry_count FROM bt_entries")
        ).mappings().first()
    except SQLAlchemyOperationalError as exc:
        msg = (
            "Dictionary browse tables are missing. "
            "Run `wyrdcraeft dictionary build` for this database first."
        )
        raise DictionaryBrowseDataError(msg) from exc

    if counts is not None and int(counts["entry_count"]) > 0:
        return

    msg = (
        "Dictionary browse tables are empty. "
        "Run `wyrdcraeft dictionary build` for this database first."
    )
    raise DictionaryBrowseDataError(msg)


def _format_browse_connect_message(db_path: Path) -> str:
    """
    Build the initial browse details placeholder.

    Args:
        db_path: Path to the morphology SQLite database.

    Returns:
        Idle-state message shown before the first search.

    """
    return (
        f"Connected to {db_path}. "
        "Search and select a result to view details."
    )


def create_dictionary_browse_app(db_path: Path) -> DictionaryBrowseApp:
    """
    Build a validated dictionary browse shell instance for tests and CLI wiring.

    Args:
        db_path: Path to the morphology SQLite database.

    Returns:
        Ready-to-run Textual app shell with injected query service.

    Raises:
        DictionaryBrowseDataError: Browse tables are missing or empty.

    """
    query_service = DictionaryBrowseQueryService(db_path)
    try:
        _ensure_browse_ready(query_service)
    except DictionaryBrowseDataError:
        query_service.close()
        raise
    return DictionaryBrowseApp(
        query_service=query_service,
        db_path=db_path,
        initial_details_message=_format_browse_connect_message(db_path),
    )


def run_dictionary_browse(db_path: Path, *, show_progress: bool = True) -> None:
    """
    Launch the dictionary browse Textual shell for one canonical database.

    Args:
        db_path: Path to the morphology SQLite database.

    Keyword Args:
        show_progress: Whether to show stderr startup progress before the TUI opens.

    Side Effects:
        Starts an interactive Textual terminal app.

    Raises:
        DictionaryBrowseDataError: Browse tables are missing or empty.

    """
    app: DictionaryBrowseApp | None = None

    def _startup(stage: DictionaryBrowseStartupStage) -> None:
        nonlocal app
        if stage == DictionaryBrowseStartupStage.VALIDATE:
            app = create_dictionary_browse_app(db_path)

    run_browse_startup_progress(_startup, enabled=show_progress)
    if app is None:
        app = create_dictionary_browse_app(db_path)
    try:
        app.run()
    finally:
        app.query_service.close()


__all__ = [
    "DictionaryBrowseApp",
    "DictionaryBrowseDataError",
    "_MainResultItem",
    "_format_entry_details",
    "create_dictionary_browse_app",
    "run_dictionary_browse",
]
