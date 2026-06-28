"""Shell-level tests for the lexicon Textual browse scaffold."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from textual.widgets import Input, ListView, Static

from wyrdcraeft.services.lexicon.build import rebuild_lexicon
from wyrdcraeft.services.lexicon.query import LexiconQueryService
from wyrdcraeft.services.lexicon.tui import (
    LexiconBrowseApp,
    LexiconBrowseDataError,
    _MainResultItem,
    _OrphanResultItem,
    create_lexicon_browse_app,
    run_lexicon_browse,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual.widget import Widget

def _collect_widget_ids(widget: Widget) -> set[str]:
    """
    Collect all widget ids reachable from one widget tree root.

    Args:
        widget: Root widget to traverse recursively.

    Returns:
        Set of non-empty widget ids.

    """
    ids: set[str] = set()
    if widget.id:
        ids.add(widget.id)
    for child in widget.children:
        ids.update(_collect_widget_ids(child))
    return ids


def test_shell_create_app_wires_query_service(lexicon_source_db: Path) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        assert isinstance(app, LexiconBrowseApp)
        assert isinstance(app.query_service, LexiconQueryService)
        assert app.db_path == lexicon_source_db
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_shell_layout_exposes_search_and_two_panes(lexicon_source_db: Path) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            assert isinstance(app.query_one("#search-input"), Input)
            body = app.query_one("#body")
            ids = _collect_widget_ids(body)
            assert "results-pane" in ids
            assert "details-pane" in ids
            assert "results-list" in ids
            assert "details-content" in ids
    finally:
        app.query_service.close()


def test_shell_rejects_missing_lexicon_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "no-lexicon.sqlite3"
    db_path.touch()

    with pytest.raises(LexiconBrowseDataError, match="tables are missing"):
        create_lexicon_browse_app(db_path)


def test_shell_rejects_empty_lexicon_tables(lexicon_db_path: Path) -> None:
    with pytest.raises(LexiconBrowseDataError, match="tables are empty"):
        create_lexicon_browse_app(lexicon_db_path)


def test_shell_run_entrypoint_uses_textual_app(
    lexicon_source_db: Path,
    monkeypatch,
) -> None:
    rebuild_lexicon(lexicon_source_db)
    run_called = False

    def _fake_run(_self: LexiconBrowseApp) -> None:
        nonlocal run_called
        run_called = True

    monkeypatch.setattr(LexiconBrowseApp, "run", _fake_run)
    run_lexicon_browse(lexicon_source_db)

    assert run_called


def _static_text(widget: Static) -> str:
    """
    Render a Static widget to plain text for assertions.

    Args:
        widget: Static widget from the browse TUI.

    Returns:
        Plain-text rendering of the widget content.

    """
    return str(widget.render())


async def _submit_search(app: LexiconBrowseApp, pilot, query: str) -> None:
    """
    Enter a query and submit the browse search box with Enter.

    Args:
        app: Running lexicon browse app under test.
        pilot: Textual test pilot bound to ``app``.
        query: Search string to submit.

    Side Effects:
        Posts an Enter keypress to trigger browse search handling.

    """
    search = app.query_one("#search-input", Input)
    search.value = query
    await pilot.press("enter")


@pytest.mark.anyio
async def test_browse_search_on_enter_populates_main_results_with_pos(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")

            main_list = app.query_one("#results-list", ListView)
            first_item = main_list.children[0]
            assert isinstance(first_item, _MainResultItem)
            assert first_item.hit.headword == "abbad"
            assert first_item.hit.pos == "noun"
            label_widget = first_item.children[0]
            assert isinstance(label_widget, Static)
            label = _static_text(label_widget)
            assert label == "abbad (noun)"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_does_not_search_until_enter(lexicon_source_db: Path) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            search = app.query_one("#search-input", Input)
            search.value = "ABBOD"
            details = app.query_one("#details-content", Static)
            assert "Connected to" in _static_text(details)

            main_list = app.query_one("#results-list", ListView)
            assert not main_list.children
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_single_main_result_auto_shows_details(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")

            details_text = _static_text(app.query_one("#details-content", Static))
            assert "abbad" in details_text
            assert "POS: noun" in details_text
            assert "Summary" in details_text
            assert "an abbot; abbot" in details_text
            assert "Senses" in details_text
            assert "bishops were sometimes subject to an abbot" in details_text

            main_list = app.query_one("#results-list", ListView)
            assert main_list.index == 0
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_orphans_shown_in_separate_section(lexicon_source_db: Path) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "orphan-form")

            main_list = app.query_one("#results-list", ListView)
            assert len(main_list.children) == 1
            assert not isinstance(main_list.children[0], _MainResultItem)

            orphans_header = app.query_one("#orphans-header", Static)
            assert "hidden" not in orphans_header.classes

            orphans_list = app.query_one("#orphans-list", ListView)
            assert "hidden" not in orphans_list.classes
            orphan_item = orphans_list.children[0]
            assert isinstance(orphan_item, _OrphanResultItem)
            assert orphan_item.hit.lemma == "orphan-lemma"

            details_text = _static_text(app.query_one("#details-content", Static))
            assert "No dictionary entries matched" in details_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_select_orphan_shows_details_and_morphology_sidebar(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "orphan-form")

            orphans_list = app.query_one("#orphans-list", ListView)
            orphans_list.index = 0
            orphans_list.action_select_cursor()
            await pilot.pause()

            details_text = _static_text(app.query_one("#details-content", Static))
            assert "orphan-lemma" in details_text
            assert "Morphology-only form" in details_text

            sidebar_text = _static_text(app.query_one("#morphology-sidebar", Static))
            assert "noun" in sidebar_text
            assert "form=orphan-form" in sidebar_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_morphology_sidebar_groups_by_wordclass_and_function(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abades")

            sidebar_text = _static_text(app.query_one("#morphology-sidebar", Static))
            assert "noun" in sidebar_text
            assert "No" in sidebar_text
            assert "form=abbades" in sidebar_text
            assert "formi=abades" in sidebar_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_shows_build_timestamp_after_fresh_build(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            details_text = _static_text(app.query_one("#details-content", Static))
            assert "Connected to" in details_text
            assert "Lexicon built at" in details_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_build_then_browse_integration_smoke(lexicon_source_db: Path) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")

            main_list = app.query_one("#results-list", ListView)
            assert isinstance(main_list.children[0], _MainResultItem)

            details_text = _static_text(app.query_one("#details-content", Static))
            assert "abbad" in details_text
            assert "POS: noun" in details_text
    finally:
        app.query_service.close()
