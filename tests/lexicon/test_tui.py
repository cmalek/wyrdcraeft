"""Shell-level tests for the lexicon Textual browse scaffold."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from textual import events
from textual.containers import Vertical
from textual.widgets import DataTable, Input, ListView, Static

from wyrdcraeft.models.lexicon_build import (
    BuildCancelled,
    BuildCounters,
    BuildFailed,
    BuildFinished,
    BuildLog,
    BuildSnapshot,
    BuildStageProgress,
    BuildStageStarted,
    LexiconBuildStage,
)
from wyrdcraeft.services.lexicon.build import rebuild_lexicon
from wyrdcraeft.services.lexicon.build_monitor import LexiconBuildMonitorApp
from wyrdcraeft.services.lexicon.build_runtime import LexiconBuildController
from wyrdcraeft.services.lexicon.query import LexiconQueryService
from wyrdcraeft.services.lexicon.tui import (
    LexiconBrowseApp,
    LexiconBrowseDataError,
    OldEnglishSearchInput,
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
            assert isinstance(app.query_one("#search-box"), OldEnglishSearchInput)
            assert isinstance(app.query_one("#search-input"), Input)
            body = app.query_one("#body")
            ids = _collect_widget_ids(body)
            assert "results-pane" in ids
            assert "details-pane" in ids
            assert "results-list" in ids
            assert "details-content" in ids
            assert "details-content-scroll" in ids
            assert "morphology-sidebar" in ids
            details_body = app.query_one("#details-body")
            assert isinstance(details_body, Vertical)
            search_box = app.query_one("#search-box", OldEnglishSearchInput)
            search_box_children = list(search_box.children)
            assert isinstance(search_box_children[0], Input)
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


def _table_text(table: DataTable) -> str:
    """
    Flatten a DataTable into plain text for assertions.

    Args:
        table: DataTable widget from the browse TUI.

    Returns:
        Space-joined cell text from all rendered rows.

    """
    return " ".join(
        str(cell)
        for row_key in table.rows
        for cell in table.get_row(row_key)
    )


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
async def test_browse_form_search_label_shows_root_in_parentheses(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abades")

            main_list = app.query_one("#results-list", ListView)
            first_item = main_list.children[0]
            assert isinstance(first_item, _MainResultItem)
            label_widget = first_item.children[0]
            assert isinstance(label_widget, Static)
            label = _static_text(label_widget)
            assert label == "abades (abbad, noun)"
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

            sidebar_text = _table_text(app.query_one("#morphology-table", DataTable))
            assert "orphan-form" in sidebar_text
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

            sidebar_text = _table_text(app.query_one("#morphology-table", DataTable))
            assert "abbades" in sidebar_text
            assert "abades" in sidebar_text or "abbades" in sidebar_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_oe_character_bar_inserts_into_search(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            first_button = app.query(".oe-char-button").first()
            await pilot.click(first_button)
            await pilot.pause()
            search = app.query_one("#search-input", Input)
            assert search.value == "æ"

            thorn_button = app.query(".oe-char-button")[2]
            await pilot.click(thorn_button)
            await pilot.pause()
            assert search.value == "æþ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_accepts_keyboard_unicode_characters(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus
            for character in ("æ", "Þ", "ð", "ā", "ċ"):
                app.post_message(events.Key(character, character))
                await pilot.pause()
            assert search.value == "æÞðāċ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_oe_character_buttons_skip_tab_focus(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus
            await pilot.press("tab")
            await pilot.pause()
            assert not search.has_focus
            assert app.focused is not None
            assert "oe-char-button" not in app.focused.classes
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_keeps_focus_after_submit(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    app = create_lexicon_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")
            search = app.query_one("#search-input", Input)
            assert search.has_focus
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


@pytest.mark.anyio
async def test_build_monitor_layout_has_stage_and_log_panes() -> None:
    app = LexiconBuildMonitorApp.fake()

    async with app.run_test():
        body = app.query_one("#build-body")
        ids = _collect_widget_ids(body)
        assert "build-stage-pane" in ids
        assert "build-log-pane" in ids


@pytest.mark.anyio
async def test_build_monitor_renders_progress_and_final_state() -> None:
    app = LexiconBuildMonitorApp.fake()

    async with app.run_test() as pilot:
        app.handle_event(
            BuildStageStarted(
                seq=1,
                at="2026-06-28T12:00:00Z",
                stage=LexiconBuildStage.LOAD_FORMS,
                total=10,
                detail="Loading forms",
            )
        )
        app.handle_event(
            BuildStageProgress(
                seq=2,
                at="2026-06-28T12:00:01Z",
                stage=LexiconBuildStage.LOAD_FORMS,
                completed=5,
                total=10,
                current_item="abbad",
            )
        )
        app.handle_event(
            BuildFinished(
                seq=3,
                at="2026-06-28T12:00:02Z",
                snapshot=BuildSnapshot(
                    status="complete",
                    active_stage=LexiconBuildStage.LOAD_FORMS,
                    counters=BuildCounters(forms_written=10),
                    status_message="Build complete.",
                ),
                built_at="2026-06-28T12:00:02Z",
                forms_source_count=10,
                bt_entries_source_count=1,
            )
        )
        await pilot.pause()

        assert "status: complete" in _static_text(app.query_one("#build-status", Static)).lower()
        assert "forms_written: 10" in _static_text(
            app.query_one("#build-counters", Static)
        )
        stages_text = _static_text(app.query_one("#build-stages", Static))
        assert "load forms 10/10" in stages_text.lower()
        assert "abbad" in stages_text.lower()


@pytest.mark.anyio
async def test_build_monitor_q_requests_cancel_while_running(tmp_path: Path) -> None:
    controller = LexiconBuildController(db_path=tmp_path / "lexicon.sqlite3", quiet=True)
    app = LexiconBuildMonitorApp(
        controller=controller,
        db_path=tmp_path / "lexicon.sqlite3",
    )

    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()

        assert controller.cancel_requested is True
        assert "cancellation requested" in _static_text(
            app.query_one("#build-status", Static)
        ).lower()


@pytest.mark.anyio
async def test_build_monitor_failure_shows_traceback_in_log() -> None:
    app = LexiconBuildMonitorApp.fake()

    async with app.run_test() as pilot:
        app.handle_event(
            BuildFailed(
                seq=1,
                at="2026-06-28T12:00:00Z",
                snapshot=BuildSnapshot(
                    status="failed",
                    active_stage=LexiconBuildStage.INSERT_FORMS,
                    counters=BuildCounters(forms_written=9),
                    status_message="boom",
                ),
                error_type="RuntimeError",
                message="boom",
                traceback_text="Traceback line 1\nTraceback line 2",
            )
        )
        await pilot.pause()

        log_text = _static_text(app.query_one("#build-log", Static))
        assert "runtimeerror: boom" in log_text.lower()
        assert "traceback line 1" in log_text.lower()
        assert "traceback line 2" in log_text.lower()


@pytest.mark.anyio
async def test_build_monitor_enter_exits_after_terminal_event() -> None:
    app = LexiconBuildMonitorApp.fake()

    async with app.run_test() as pilot:
        app.handle_event(
            BuildCancelled(
                seq=1,
                at="2026-06-28T12:00:00Z",
                snapshot=BuildSnapshot(
                    status="cancelled",
                    active_stage=LexiconBuildStage.BUILD_SEARCH_KEYS,
                    counters=BuildCounters(search_keys_written=4),
                    status_message="Build cancelled.",
                ),
                message="Build cancelled.",
            )
        )
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

    assert app.return_value == 130


@pytest.mark.anyio
async def test_build_monitor_log_history_is_capped() -> None:
    app = LexiconBuildMonitorApp.fake()

    async with app.run_test() as pilot:
        for index in range(205):
            app.handle_event(
                BuildLog(
                    seq=index,
                    at="2026-06-28T12:00:00Z",
                    stage=LexiconBuildStage.LOAD_ENTRIES,
                    level="info",
                    message=f"log {index}",
                )
            )
        await pilot.pause()

        log_text = _static_text(app.query_one("#build-log", Static))
        assert "log 0" not in log_text
        assert "log 204" in log_text


@pytest.mark.anyio
async def test_build_monitor_stage_progress_updates_after_many_logs() -> None:
    app = LexiconBuildMonitorApp.fake()

    async with app.run_test() as pilot:
        for index in range(205):
            app.handle_event(
                BuildLog(
                    seq=index,
                    at="2026-06-28T12:00:00Z",
                    stage=LexiconBuildStage.LOAD_FORMS,
                    level="info",
                    message=f"log {index}",
                ),
                render=False,
            )
        app.handle_event(
            BuildStageProgress(
                seq=999,
                at="2026-06-28T12:00:00Z",
                stage=LexiconBuildStage.INSERT_FORMS,
                completed=25000,
                total=13648040,
                detail="inserting rows",
            )
        )
        await pilot.pause()

        stages_text = _static_text(app.query_one("#build-stages", Static))
        assert "insert forms 25000/13648040" in stages_text
