"""Textual shell for dictionary browse workflow."""

from __future__ import annotations

import threading
import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:

    from textual import events
    from textual.binding import BindingType
    from textual.widget import Widget

    from wyrdcraeft.services.dictionary.definition_cache import DefinitionLineCache

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, ListItem, ListView, Static
from textual.worker import get_current_worker

from wyrdcraeft.services.dictionary.browse_entry import (
    SECTION_CLASS,
    build_text_sections,
)
from wyrdcraeft.services.dictionary.browse_forms import (
    PRIMARY,
    SECONDARY,
    EntryColumn,
    FormsSection,
    FormsSelection,
)
from wyrdcraeft.services.dictionary.browse_keys import (
    APP_BINDINGS,
    SEARCH_BINDINGS,
    SEARCH_INPUT_ID,
    ResultsList,
    focus_action_allowed,
)
from wyrdcraeft.services.dictionary.browse_progress import (
    DictionaryBrowseStartupStage,
    run_browse_startup_progress,
)
from wyrdcraeft.services.dictionary.browse_query import (
    BrowseSearchHit,
    DictionaryBrowseDataError,
    DictionaryBrowseQueryService,
    EntryDetails,
    MorphologyGroup,
    MorphologyRow,
)
from wyrdcraeft.services.dictionary.browse_results import (
    definition_text,
    headword_content,
    pos_label,
    pos_tag_class,
)
from wyrdcraeft.services.dictionary.browse_theme import WYRDCRAEFT_THEME
from wyrdcraeft.services.dictionary.form_decode import morphology_row_matches_pos
from wyrdcraeft.services.dictionary.paradigm_sidebar import (
    MorphologyRowPayload,
    ParadigmSidebarSpec,
    build_paradigm_sidebar,
)
from wyrdcraeft.services.markup import normalize_old_english

#: Dictionary POS codes whose entries omit the morphology sidebar.
_POS_WITHOUT_MORPHOLOGY: frozenset[str] = frozenset(
    {"preposition", "conjunction", "interjection", "indeclinable"},
)

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


class OldEnglishSearchInput(Input):
    """Search input that accepts OE key aliases and paste-driven compose paths."""

    #: ``up``/``down`` move the results selection without leaving the input.
    BINDINGS: ClassVar[list[BindingType]] = SEARCH_BINDINGS

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
        event.prevent_default()


class _MainResultItem(ListItem):
    """
    Results row for one dictionary-backed search hit (ADR 0026, ADR 0028).

    Left to right: the headword, the dim definition line, the POS tag.

    Args:
        hit: Search hit rendered in the main results list.

    """

    def __init__(self, hit: BrowseSearchHit) -> None:
        """
        Build one results row from a search hit.

        Args:
            hit: Dictionary-backed search hit to display.

        """
        #: Dim definition-line cell, updated when a missing line is filled.
        self._definition = Static(definition_text(hit), classes="result-definition")
        tag = Static(pos_label(hit), classes=f"pos-tag {pos_tag_class(hit)}")
        super().__init__(
            Static(headword_content(hit), classes="result-headword"),
            self._definition,
            tag,
            classes="result-row",
        )
        #: Search hit rendered in the main results list.
        self.hit = hit

    def set_definition_line(self, line: str) -> None:
        """
        Show a definition line filled after the row was built.

        Args:
            line: Definition line for this row's entry; empty shows nothing.

        Side Effects:
            Replaces :attr:`hit` with a copy carrying ``line`` and redraws the
            definition cell.

        """
        self.hit = replace(self.hit, definition_line=line)
        self._definition.update(line)


#: Fallback results-row height before layout (one line plus padding).
_RESULT_ROW_HEIGHT = 3


# ponytail: False until Wright & Wright 1925 OCR is corrected; flip this constant.
#: Show the Wright § list and its section-text modal in dictionary browse.
SHOW_WRIGHT_SECTION_LISTINGS = False


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


def _forms_sidebar(details: EntryDetails) -> ParadigmSidebarSpec | None:
    """
    Build the paradigm sidebar for an entry's Forms section.

    Args:
        details: Entry details payload from the query service.

    Returns:
        The sidebar spec, or ``None`` when the entry's part of speech has no
        forms or no sidebar section has a row.

    """
    if details.pos in _POS_WITHOUT_MORPHOLOGY:
        return None
    morphology_rows = _dedupe_morphology_rows(
        _filter_morphology_rows_for_entry(
            _morphology_rows_from_groups(details.morphology_groups),
            headword=details.headword,
            entry_pos=details.pos,
        )
    )
    wordclass = morphology_rows[0].wordclass if morphology_rows else details.pos
    sidebar = build_paradigm_sidebar(
        _morphology_payloads(morphology_rows),
        wordclass=wordclass,
        entry_genders=tuple(details.genders),
    )
    has_rows = any(section.rows for section in sidebar.sections)
    return sidebar if has_rows else None


class DictionaryBrowseApp(App[None]):
    """
    Textual browse app for dictionary search and read-only details.

    Args:
        query_service: Query service used for all browse data loading.
        db_path: Path to the morphology-backed lexicon database.

    """

    #: Textual stylesheet for the browse layout; colours come from the theme.
    CSS_PATH = Path(__file__).with_name("browse.tcss")

    #: Query service used by the shell and browse interactions.
    query_service: DictionaryBrowseQueryService
    #: Database path displayed in shell placeholders.
    db_path: Path
    #: Last main-result hits shown in the results pane.
    _main_hits: list[BrowseSearchHit]
    #: Main dictionary-entry results list widget.
    _main_results_list: ListView
    #: Idle message shown in the entry column when no entry is open.
    _entry_message: Static
    #: Title shown above the Wright section citation list.
    _wright_sections_title: Static
    #: Selectable Wright section citations for the current entry.
    _wright_sections_list: ListView
    #: The entry pane's one scrolling column of sections (ADR 0026); it owns
    #: the forms switch keys (ADR 0027).
    _entry_column: EntryColumn
    #: Tab selection over the open entry's paradigm sections, if it has forms.
    _forms_selection: FormsSelection | None
    #: Pinned banner above the column: headword, POS tag, Copy button.
    _entry_banner: Horizontal
    #: Initial details-pane message shown before the first search.
    _initial_details_message: str
    #: Definition line copied by the Copy control for the current entry.
    _definition_line: str
    #: Banner headword widget.
    _entry_headword: Static
    #: Banner part-of-speech tag widget.
    _entry_pos_tag: Static
    #: Button that copies the current definition line.
    _copy_button: Button
    #: Definition-line cache used only by the row-fill worker thread.
    _row_definition_cache: DefinitionLineCache | None
    #: Read-only definition-line cache for the open entry (UI thread only).
    _entry_definition_cache: DefinitionLineCache | None
    #: Serializes row-fill workers so one thread uses the cache at a time.
    _row_definition_lock: threading.Lock

    #: Copy, focus and pane-switch keys (ADR 0028). ``ctrl+c`` is left to
    #: Textual, which shows its quit notice; quit is ``ctrl+q``.
    BINDINGS: ClassVar[list[BindingType]] = APP_BINDINGS

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
        self.register_theme(WYRDCRAEFT_THEME)
        #: Active Textual theme: the ``wyrdcraeft`` browse palette (ADR 0026).
        self.theme = WYRDCRAEFT_THEME.name
        #: Query service used by the shell and browse interactions.
        self.query_service = query_service
        #: Definition-line cache used only by the row-fill worker thread.
        self._row_definition_cache = None
        #: Read-only definition-line cache for the open entry (UI thread only).
        self._entry_definition_cache = None
        #: Serializes row-fill workers so one thread uses the cache at a time.
        self._row_definition_lock = threading.Lock()
        #: Database path displayed in shell placeholders.
        self.db_path = db_path
        #: Last main-result hits shown in the results pane.
        self._main_hits = []
        #: Definition line copied by the Copy control for the current entry.
        self._definition_line = ""
        #: Tab selection over the open entry's paradigm sections, if it has forms.
        self._forms_selection = None
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
            id=SEARCH_INPUT_ID,
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
            with Vertical(id="results-pane", classes="pane"):
                yield ResultsList(id="results-list")
            with Vertical(id="details-pane", classes="pane"):
                with Horizontal(id="entry-banner", classes="banner"):
                    yield Static("", id="entry-headword")
                    yield Static("", id="entry-pos-tag", classes="pos-tag")
                    yield Button("Copy", id="copy-definition", disabled=True)
                with EntryColumn(id="entry-column"):
                    yield Static(self._initial_details_message, id="entry-message")
                    yield Static(
                        "Wright Sections",
                        id="wright-sections-title",
                        classes="hidden",
                    )
                    yield ListView(id="wright-sections-list", classes="hidden")
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """
        Cache browse pane widgets for stable access during event handling.

        Side Effects:
            Stores references to results and details pane widgets, focuses the
            search input, and keeps OE buttons mouse-only.

        """
        self._main_results_list = self.query_one("#results-list", ListView)
        self._entry_banner = self.query_one("#entry-banner", Horizontal)
        self._entry_banner.display = False
        self._entry_headword = self.query_one("#entry-headword", Static)
        self._entry_pos_tag = self.query_one("#entry-pos-tag", Static)
        self._copy_button = self.query_one("#copy-definition", Button)
        self._entry_column = self.query_one("#entry-column", EntryColumn)
        self._entry_message = self.query_one("#entry-message", Static)
        self._wright_sections_title = self.query_one("#wright-sections-title", Static)
        self._wright_sections_list = self.query_one("#wright-sections-list", ListView)
        self.query_one("#results-pane").border_title = "Results"
        self.query_one("#details-pane").border_title = "Entry"
        self.watch(self.screen, "focused", self._mark_focused_pane)
        self.watch(self._main_results_list, "scroll_y", self._on_results_scrolled)
        self.focus_search()
        for button in self.query(".oe-char-button"):
            button.can_focus = False
        self._copy_button.can_focus = False

    def _mark_focused_pane(self, focused: Widget | None) -> None:
        """
        Give the pane holding keyboard focus the accent border and title.

        Args:
            focused: Widget that now has focus, or ``None``.

        Side Effects:
            Toggles the ``pane-focused`` class on each ``.pane`` container.

        """
        for pane in self.query(".pane"):
            holds_focus = focused is not None and (
                focused is pane or pane in focused.ancestors
            )
            pane.set_class(holds_focus, "pane-focused")

    def check_action(
        self,
        action: str,
        _parameters: tuple[object, ...],
    ) -> bool | None:
        """
        Allow copy and focus keys only where they act, so the footer shows them.

        Args:
            action: Action name.
            _parameters: Action parameters; none of these actions takes any.

        Returns:
            Whether the action is live in the current focus (ADR 0028).

        """
        focused = self.focused
        return focus_action_allowed(
            action,
            search_focused=focused is not None and focused.id == SEARCH_INPUT_ID,
            has_definition_line=bool(self._definition_line),
        )

    def action_copy_definition(self) -> None:
        """
        Copy the open entry's definition line to the clipboard.

        Side Effects:
            Writes the definition line to the app clipboard when there is one.

        """
        if self._definition_line:
            self.copy_to_clipboard(self._definition_line)

    def action_focus_search(self) -> None:
        """Move keyboard focus to the search input (the ``/`` key)."""
        self.focus_search()

    def action_focus_results(self) -> None:
        """Move keyboard focus to the results list (``escape`` in the search)."""
        self._main_results_list.focus()

    def action_move_results(self, step: int) -> None:
        """
        Move the results selection while focus stays in the search input.

        Args:
            step: ``1`` moves down, ``-1`` moves up.

        Side Effects:
            Changes the results list's highlighted row.

        """
        if step > 0:
            self._main_results_list.action_cursor_down()
        else:
            self._main_results_list.action_cursor_up()

    def focus_search(self) -> None:
        """Return keyboard focus to the search input field."""
        self.query_one(f"#{SEARCH_INPUT_ID}", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle Old English character buttons and the Copy button.

        Args:
            event: Textual button press event.

        Side Effects:
            Inserts the pressed character into the search input and refocuses
            it, or copies the current definition line for the Copy button.

        """
        if event.button.id == "copy-definition":
            self.action_copy_definition()
            event.stop()
            return
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

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Run browse search when the user submits the search box.

        Args:
            event: Textual input submission event.

        Side Effects:
            Rebuilds results list and may auto-focus a single hit.

        """
        if event.input.id != "search-input":
            return
        await self._run_search(event.value)
        self.focus_search()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Show details for a selected search result or Wright section.

        Args:
            event: Textual list selection event.

        Side Effects:
            Redraws the entry banner and column.

        """
        if event.list_view.id == "results-list":
            item = event.item
            if isinstance(item, _MainResultItem):
                await self._show_entry_details(item.hit.entry_id)
            return

        if event.list_view.id == "wright-sections-list":
            item = event.item
            if isinstance(item, _WrightSectionItem):
                self._show_wright_section_text(item.section_no)

    async def _run_search(self, query: str) -> None:
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
            await self._show_entry_details(self._main_hits[0].entry_id)
            return

        if not self._main_hits:
            await self._show_idle_details("No results.")
            return

        await self._show_idle_details("Select a result to view details.")

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
            self.call_after_refresh(self._fill_drawn_definition_lines)
            return
        self._main_results_list.append(ListItem(Static("No results.")))

    def _on_results_scrolled(self, _scroll_y: float) -> None:
        """
        Fill definition lines for rows that scrolling brought into view.

        Args:
            _scroll_y: New vertical scroll offset of the results list.

        Side Effects:
            May start a row-fill worker.

        """
        self._fill_drawn_definition_lines()

    def _drawn_rows_missing_lines(self) -> list[_MainResultItem]:
        """
        Find drawn results rows whose definition line is not computed yet.

        "Drawn" is the visible window plus one screen below it (ADR 0028).

        Returns:
            Rows in that window whose hit has ``definition_line`` ``None``.

        """
        results = self._main_results_list
        rows = [
            child for child in results.children if isinstance(child, _MainResultItem)
        ]
        row_height = rows[0].outer_size.height if rows else 0
        row_height = row_height or _RESULT_ROW_HEIGHT
        screen_rows = max(results.size.height // row_height, 1)
        first = int(results.scroll_y) // row_height
        window = rows[first : first + 2 * screen_rows]
        return [row for row in window if row.hit.definition_line is None]

    def _fill_drawn_definition_lines(self) -> None:
        """
        Start filling missing definition lines for the drawn results rows.

        Side Effects:
            Starts a thread worker when any drawn row lacks its line.

        """
        missing = self._drawn_rows_missing_lines()
        if not missing:
            return
        if self._row_definition_cache is None:
            self._row_definition_cache = self.query_service.open_definition_line_cache()
        self._fill_definition_lines(self._row_definition_cache, missing)

    @work(
        thread=True,
        exclusive=True,
        group="row-definition-lines",
        exit_on_error=False,
    )
    def _fill_definition_lines(
        self,
        cache: DefinitionLineCache,
        rows: list[_MainResultItem],
    ) -> None:
        """
        Compute missing row definition lines off the UI thread.

        A cache write can wait out SQLite's busy timeout while a build holds
        the database lock, so this never runs on the UI thread.

        Args:
            cache: Definition-line cache on the worker's own connection.
            rows: Drawn rows whose line is not computed yet.

        Side Effects:
            May write ``bt_entries.definition_line_cache``; updates each row on
            the UI thread as its line arrives.

        """
        worker = get_current_worker()
        with self._row_definition_lock:
            for row in rows:
                if worker.is_cancelled:
                    return
                line = cache.get(row.hit.entry_id)
                self.call_from_thread(self._apply_definition_line, row, line)

    def _apply_definition_line(self, row: _MainResultItem, line: str) -> None:
        """
        Show one filled definition line if its row is still in the results.

        Args:
            row: Results row the line was computed for.
            line: Definition line for the row's entry.

        Side Effects:
            Updates the row and the matching entry in the last search's hits.

        """
        if row.parent is not self._main_results_list:
            return
        row.set_definition_line(line)
        self._main_hits = [
            replace(hit, definition_line=line)
            if hit.entry_id == row.hit.entry_id
            else hit
            for hit in self._main_hits
        ]

    async def _show_entry_details(self, entry_id: int) -> None:
        """
        Load one dictionary entry and draw it as a sectioned column.

        Args:
            entry_id: Dictionary entry identifier from search results.

        Side Effects:
            Updates the banner, definition line and Copy button, and replaces
            the entry column's sections.

        """
        details = self.query_service.get_details(entry_id)
        if details is None:
            await self._show_idle_details(f"Entry {entry_id} is unavailable.")
            return
        self._show_banner(details)
        self._set_definition_line(self._entry_definition_line(entry_id))
        self._entry_message.display = False
        await self._replace_entry_sections(details)
        self._populate_wright_sections(details)
        self._entry_column.scroll_home(animate=False)

    def _entry_definition_line(self, entry_id: int) -> str:
        """
        Read the entry's definition line through the shared cache.

        The results preview reads the same :meth:`DefinitionLineCache.get`,
        so the copied line and the preview cannot disagree (ADR 0028).

        The UI-thread cache never writes, so opening an entry never waits on
        a database lock (for example while a build runs); the row-fill
        worker is the only writer.

        Args:
            entry_id: Dictionary entry identifier.

        Returns:
            The definition line; empty when the entry has none.

        Side Effects:
            Opens the read-only UI-thread cache on first use.

        """
        if self._entry_definition_cache is None:
            self._entry_definition_cache = (
                self.query_service.open_definition_line_cache(write=False)
            )
        return self._entry_definition_cache.get(entry_id)

    def _set_definition_line(self, line: str) -> None:
        """
        Make ``line`` the open entry's definition line for copying.

        Args:
            line: Definition line; empty disables copying.

        Side Effects:
            Enables or disables the Copy button and refreshes the footer keys.

        """
        self._definition_line = line
        self._copy_button.disabled = not line
        self.refresh_bindings()

    def _show_banner(self, details: EntryDetails) -> None:
        """
        Show the pinned banner for one entry.

        Args:
            details: Entry details payload from the query service.

        Side Effects:
            Sets the headword and POS tag text and class, and shows the banner.

        """
        self._entry_headword.update(details.headword)
        self._entry_pos_tag.update(pos_label(details))
        for name in list(self._entry_pos_tag.classes):
            if name.startswith("pos-") and name != "pos-tag":
                self._entry_pos_tag.remove_class(name)
        self._entry_pos_tag.add_class(pos_tag_class(details))
        self._entry_banner.display = True

    async def _replace_entry_sections(self, details: EntryDetails | None) -> None:
        """
        Remove the drawn sections and mount the ones that have content.

        The key/value block goes above the Wright widgets; Senses, Etymology
        and Forms go below them. Forms is mounted only when the paradigm
        sidebar has at least one row.

        Args:
            details: Entry to draw, or ``None`` to leave the column empty.

        Side Effects:
            Removes and mounts section widgets, resets the forms tab
            selection and draws the selected paradigm section.

        """
        await self._entry_column.query(f".{SECTION_CLASS}").remove()
        self._forms_selection = None
        if details is None:
            self._render_forms()
            return
        sections = build_text_sections(details)
        if sections and sections[0].id == "entry-keyvalues":
            await self._entry_column.mount(
                sections.pop(0), before=self._wright_sections_title
            )
        sidebar = _forms_sidebar(details)
        if sidebar is not None:
            sections.append(FormsSection())
            self._forms_selection = FormsSelection(sidebar.sections)
        if sections:
            await self._entry_column.mount_all(sections)
        self._render_forms()

    def _render_forms(self) -> None:
        """
        Draw the selected paradigm section at the column's current width.

        Side Effects:
            Updates the column's switch axis sizes and redraws ``#entry-forms``.

        """
        selection = self._forms_selection
        if selection is None:
            self._entry_column.set_axis_sizes(0, 0)
            return
        self._entry_column.set_axis_sizes(
            selection.axis_size(PRIMARY), selection.axis_size(SECONDARY)
        )
        forms = self._entry_column.query(FormsSection)
        if forms:
            width = self._entry_column.scrollable_content_region.width
            forms.first().show(selection, width)

    def on_entry_column_switch(self, event: EntryColumn.Switch) -> None:
        """
        Move the forms tab selection and redraw the table.

        Args:
            event: Switch request from the entry column's keys.

        Side Effects:
            Changes the selection and redraws ``#entry-forms`` when it moved.

        """
        event.stop()
        if self._forms_selection is not None and self._forms_selection.step(
            event.axis, event.step
        ):
            self._render_forms()

    def on_entry_column_resized(self, event: EntryColumn.Resized) -> None:
        """
        Re-fit the forms column to the new pane width.

        Args:
            event: Resize notice from the entry column.

        Side Effects:
            Redraws ``#entry-forms``.

        """
        event.stop()
        self._render_forms()

    async def _show_idle_details(self, message: str) -> None:
        """
        Show a neutral message in the entry column and hide the banner.

        Args:
            message: Idle-state message for the entry pane.

        Side Effects:
            Hides the banner, clears the definition line, disables Copy and
            removes every section.

        """
        self._entry_banner.display = False
        self._entry_headword.update("")
        self._set_definition_line("")
        self._entry_message.update(message)
        self._entry_message.display = True
        self._clear_wright_sections()
        await self._replace_entry_sections(None)

    def _populate_wright_sections(self, details: EntryDetails) -> None:
        """
        Show selectable Wright section citations for the current entry.

        Args:
            details: Entry details payload from the query service.

        Side Effects:
            Clears and repopulates the Wright section list in the details pane.
            ``SHOW_WRIGHT_SECTION_LISTINGS`` false hides the list instead.

        """
        if not SHOW_WRIGHT_SECTION_LISTINGS:
            self._clear_wright_sections()
            return
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
        query_service.ensure_ready()
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
    "create_dictionary_browse_app",
    "run_dictionary_browse",
]
