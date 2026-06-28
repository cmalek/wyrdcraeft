"""Textual shell for lexicon browse workflow."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, ListItem, ListView, Static

from wyrdcraeft.services.lexicon.build import check_lexicon_staleness
from wyrdcraeft.services.lexicon.query import (
    EntryDetails,
    LexiconQueryService,
    MorphologyGroup,
    MorphologyRow,
    OrphanDetails,
    OrphanHit,
    SearchHit,
)

if TYPE_CHECKING:
    from pathlib import Path


class LexiconBrowseDataError(RuntimeError):
    """Raised when lexicon browse data is unavailable for the TUI shell."""


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
    pos = hit.pos.strip()
    if pos:
        return f"{hit.headword} ({pos})"
    return hit.headword


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


def _join_labels(labels: list[str]) -> str:
    """
    Join non-empty labels for compact metadata display.

    Args:
        labels: Candidate label strings.

    Returns:
        Comma-separated labels, or an empty string when none are present.

    """
    values = [label.strip() for label in labels if label.strip()]
    return ", ".join(values)


def _format_morphology_row(row: MorphologyRow) -> str:
    """
    Format one raw morphology row for sidebar display.

    Args:
        row: Morphology row from entry or orphan details.

    Returns:
        Single-line morphology row summary.

    """
    parts = [
        f"form={row.form}",
        f"stem={row.stem}",
        f"lemma={row.lemma}",
    ]
    if row.formi.strip() and row.formi != row.form:
        parts.append(f"formi={row.formi}")
    if row.probability.strip():
        parts.append(f"p={row.probability}")
    classes = _join_labels([row.class1, row.class2, row.class3])
    if classes:
        parts.append(f"class={classes}")
    return "  " + " ".join(parts)


def _format_morphology_groups(groups: list[MorphologyGroup]) -> str:
    """
    Format grouped morphology rows for the details sidebar.

    Args:
        groups: Morphology groups from the query service.

    Returns:
        Multi-line sidebar text, or a placeholder when no rows exist.

    """
    if not groups:
        return "No morphology rows linked."

    lines: list[str] = []
    for group in groups:
        header = _join_labels([group.wordclass, group.function])
        lines.append(header or "Morphology")
        lines.extend(_format_morphology_row(row) for row in group.rows)
        lines.append("")
    return "\n".join(lines).strip()


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
        f"POS: {details.pos}",
    ]
    variants = _join_labels(details.variants)
    if variants:
        lines.append(f"Variants: {variants}")
    class_summary = _join_labels(details.class_summary)
    if class_summary:
        lines.append(f"Classes: {class_summary}")
    genders = _join_labels(details.genders)
    if genders:
        lines.append(f"Gender: {genders}")
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
    class_summary = _join_labels(details.class_summary)
    if class_summary:
        lines.append(f"Classes: {class_summary}")
    genders = _join_labels(details.genders)
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
  }

  #search-input {
      margin: 0 1;
  }

  #body {
      layout: horizontal;
      height: 1fr;
  }

  #results-pane {
      width: 1fr;
      margin: 0 1 1 1;
      border: solid $accent;
  }

  #details-pane {
      width: 2fr;
      margin: 0 1 1 0;
      border: solid $accent;
  }

  #details-body {
      layout: horizontal;
      height: 1fr;
  }

  #details-content {
      width: 2fr;
      padding: 0 1;
  }

  #morphology-sidebar {
      width: 1fr;
      padding: 0 1;
      border-left: solid $accent;
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
    #: Grouped morphology sidebar widget.
    _morphology_sidebar: Static
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
        yield Input(
            placeholder="Search lexicon (press Enter)",
            id="search-input",
        )
        with Horizontal(id="body"):
            with Vertical(id="results-pane"):
                yield Static("Results", id="results-title")
                yield ListView(id="results-list")
                yield Static("Orphans", id="orphans-header", classes="hidden")
                yield ListView(id="orphans-list", classes="hidden")
            with Vertical(id="details-pane"):
                yield Static("Details", id="details-title")
                with Horizontal(id="details-body"):
                    yield Static(
                        self._initial_details_message,
                        id="details-content",
                    )
                    yield Static("Morphology", id="morphology-sidebar")

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
        self._morphology_sidebar = self.query_one("#morphology-sidebar", Static)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Run unified search when the user submits the search box.

        Args:
            event: Textual input submission event.

        Side Effects:
            Rebuilds results lists and may auto-focus a single main hit.

        """
        if event.input.id != "search-input":
            return
        self._run_search(event.value)

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
        self._morphology_sidebar.update(
            _format_morphology_groups(details.morphology_groups),
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
        self._morphology_sidebar.update(
            _format_morphology_groups(details.morphology_groups),
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
        self._morphology_sidebar.update("")


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


def run_lexicon_browse(db_path: Path) -> None:
    """
    Launch the lexicon browse Textual shell for one morphology database.

    Args:
        db_path: Path to the morphology SQLite database.

    Side Effects:
        Starts an interactive Textual terminal app.

    Raises:
        LexiconBrowseDataError: Browse tables are missing or empty.

    """
    app = create_lexicon_browse_app(db_path)
    try:
        app.run()
    finally:
        app.query_service.close()
