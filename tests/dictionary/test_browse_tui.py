"""Shell-level tests for the dictionary Textual browse scaffold."""

from __future__ import annotations

import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from textual import events
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, ListView, Static

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import LemmaMorphClass, MorphClass
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.services.dictionary.browse_query import DictionaryBrowseQueryService
from wyrdcraeft.services.dictionary.browse_tui import (
    DictionaryBrowseApp,
    DictionaryBrowseDataError,
    _MainResultItem,
    create_dictionary_browse_app,
    run_dictionary_browse,
)
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.markup import normalize_morphology_title, normalize_old_english
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader

if TYPE_CHECKING:
    from textual.widget import Widget

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))
_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


@pytest.fixture
def lexicon_source_db(tmp_path: Path) -> Path:
    """Dictionary-backed canonical DB fixture for browse TUI tests."""
    db_path = tmp_path / "browse-tui.sqlite3"
    upgrade_canonical_db(db_path)
    sink = BTSqliteSink(db_path, attach_mode=True)
    try:
        BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()
    return db_path


@pytest.fixture
def empty_browse_db(tmp_path: Path) -> Path:
    """Canonical schema with no dictionary rows for browse readiness tests."""
    db_path = tmp_path / "empty-browse.sqlite3"
    upgrade_canonical_db(db_path)
    return db_path


def _bt_entry_id(db_path: Path, *, norm_key: str) -> int:
    """Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions."""
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT id FROM bt_entries WHERE norm_key = ? ORDER BY id ASC LIMIT 1",
            (norm_key,),
        ).fetchone()
    assert row is not None
    return int(row[0])


def _pos_id(db_path: Path, *, code: str) -> int:
    """Resolve one canonical part-of-speech id for ad-hoc test inserts."""
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT id FROM parts_of_speech WHERE code = ?",
            (code,),
        ).fetchone()
    assert row is not None
    return int(row[0])


def _insert_inflection_code(
    connection: sqlite3.Connection,
    *,
    code: str,
    pos_id: int,
) -> int:
    """Insert one ad-hoc ``inflection_codes`` row and return its id."""
    connection.execute(
        """
        INSERT INTO inflection_codes (code, pos_id, display_json)
        VALUES (?, ?, '{}')
        """,
        (code, pos_id),
    )
    row = connection.execute(
        "SELECT id FROM inflection_codes WHERE code = ? AND pos_id = ?",
        (code, pos_id),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _seed_abbad_morphology_forms(db_path: Path) -> None:
    """Insert linked morphology rows for the ``abbad`` noun entry."""
    entry_id = _bt_entry_id(db_path, norm_key="abbad")
    noun_pos_id = _pos_id(db_path, code="noun")
    with sqlite3.connect(db_path) as connection:
        genitive_code_id = _insert_inflection_code(
            connection,
            code="genitive singular",
            pos_id=noun_pos_id,
        )
        nominative_code_id = _insert_inflection_code(
            connection,
            code="nominative plural",
            pos_id=noun_pos_id,
        )
        connection.execute(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment,
                bt_key, title_key, stem_key, form_key, formi_key,
                entry_id, wordclass_id, inflection_code_id
            ) VALUES (
                0, 'abbades', 'abbad', 'abbad', 'abbad', 'abbad', 'abbades',
                '0-abbad-0', '0', '0', '',
                'abbad', 'abbad', 'abbad', 'abbades', 'abbades',
                ?, ?, ?
            )
            """,
            (entry_id, noun_pos_id, genitive_code_id),
        )
        connection.execute(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment,
                bt_key, title_key, stem_key, form_key, formi_key,
                entry_id, wordclass_id, inflection_code_id
            ) VALUES (
                0, 'abades', 'abbad', 'abbad', 'abbad', 'abbad', 'abades',
                '0-abbad-0', '0', '0', '',
                'abbad', 'abbad', 'abbad', 'abades', 'abades',
                ?, ?, ?
            )
            """,
            (entry_id, noun_pos_id, nominative_code_id),
        )
        connection.commit()


async def _select_abbad_hit(app: DictionaryBrowseApp, pilot) -> None:
    """Select the first ``abbad`` noun hit from the results list."""
    main_list = app.query_one("#results-list", ListView)
    for index, child in enumerate(main_list.children):
        if isinstance(child, _MainResultItem) and child.hit.headword == "abbad":
            main_list.index = index
            main_list.action_select_cursor()
            await pilot.pause()
            return
    pytest.fail("abbad search hit not found in results list")


def _insert_entry(
    db_path: Path,
    *,
    headword: str,
    pos: str,
    summary_sense: str,
) -> None:
    """Insert one minimal browseable dictionary entry for TUI auto-select tests."""
    norm_key = normalize_old_english(headword)
    assert norm_key is not None
    normalized_title = normalize_morphology_title(headword)
    pos_id = _pos_id(db_path, code=pos)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO bt_entries (
                norm_key,
                headword,
                normalized_title,
                pos_id,
                genders_json,
                etymology,
                see_also_json,
                source_line_nos_json,
                entry_order
            ) VALUES (?, ?, ?, ?, '[]', '', '[]', '[]', 1)
            """,
            (norm_key, headword, normalized_title, pos_id),
        )
        entry_id = connection.execute(
            "SELECT id FROM bt_entries WHERE norm_key = ? AND pos_id = ?",
            (norm_key, pos_id),
        ).fetchone()
        assert entry_id is not None
        connection.execute(
            """
            INSERT INTO bt_senses (
                entry_id,
                sense_label,
                gloss_en,
                order_index,
                sense_path,
                parent_path,
                source_label_raw,
                source_fragment_raw,
                prefix_fragment_raw,
                modifiers_json,
                grammatical_context_json,
                usage_note
            ) VALUES (?, '', ?, 0, '1', NULL, '', ?, '', '[]', '[]', '')
            """,
            (int(entry_id[0]), summary_sense, summary_sense),
        )
        connection.commit()


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


def _seed_catalog_assignment(
    db_path: Path,
    *,
    normalized_title: str,
    catalog_pos: str,
    class_key: str,
    assignment_source: str = "paradigm",
) -> None:
    """Seed one catalog assignment row into a temporary lexicon test database."""
    engine = create_engine(db_path)
    try:
        MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
        with Session(engine) as session:
            morph_class = session.scalar(
                select(MorphClass).where(MorphClass.class_key == class_key),
            )
            assert morph_class is not None
            pos_id = session.scalar(
                select(PartOfSpeech.id).where(PartOfSpeech.code == catalog_pos),
            )
            assert pos_id is not None
            session.add(
                LemmaMorphClass(
                    normalized_title=normalized_title,
                    pos_id=pos_id,
                    morph_class_id=morph_class.id,
                    assignment_source=assignment_source,
                    confidence=100,
                )
            )
            session.commit()
    finally:
        engine.dispose()


def test_shell_create_app_wires_query_service(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        assert isinstance(app, DictionaryBrowseApp)
        assert isinstance(app.query_service, DictionaryBrowseQueryService)
        assert app.db_path == lexicon_source_db
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_shell_layout_exposes_search_and_two_panes(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            search = app.query_one("#search-input", Input)
            assert isinstance(search, Input)
            oe_char_bar = app.query_one("#oe-char-bar", Horizontal)
            assert isinstance(oe_char_bar, Horizontal)
            body = app.query_one("#body")
            ids = _collect_widget_ids(body)
            assert "results-pane" in ids
            assert "details-pane" in ids
            assert "results-list" in ids
            assert "details-content" in ids
            assert "details-content-scroll" in ids
            assert "morphology-sidebar" in ids
            assert "orphans-header" not in ids
            assert "orphans-list" not in ids
            details_body = app.query_one("#details-body")
            assert isinstance(details_body, Vertical)
            char_buttons = list(oe_char_bar.children)
            assert char_buttons
            assert all(isinstance(button, Button) for button in char_buttons)
    finally:
        app.query_service.close()


def test_shell_rejects_missing_lexicon_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "no-lexicon.sqlite3"
    db_path.touch()

    with pytest.raises(DictionaryBrowseDataError, match="tables are missing"):
        create_dictionary_browse_app(db_path)


def test_shell_rejects_empty_lexicon_tables(empty_browse_db: Path) -> None:
    with pytest.raises(DictionaryBrowseDataError, match="tables are empty"):
        create_dictionary_browse_app(empty_browse_db)


def test_shell_run_entrypoint_uses_textual_app(
    lexicon_source_db: Path,
    monkeypatch,
) -> None:
    run_called = False

    def _fake_run(_self: DictionaryBrowseApp) -> None:
        nonlocal run_called
        run_called = True

    monkeypatch.setattr(DictionaryBrowseApp, "run", _fake_run)
    run_dictionary_browse(lexicon_source_db)

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


def _details_text(app: DictionaryBrowseApp) -> str:
    """
    Read both details widgets as one plain-text assertion target.

    Args:
        app: Running lexicon browse app under test.

    Returns:
        Combined plain text from the details header and body widgets.

    """
    header = _static_text(app.query_one("#details-content", Static))
    body = _static_text(app.query_one("#details-body-content", Static))
    return "\n".join(part for part in (header, body) if part)


async def _submit_search(app: DictionaryBrowseApp, pilot, query: str) -> None:
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
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abbad")

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
async def test_browse_variant_search_label_shows_headword_in_parentheses(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")

            main_list = app.query_one("#results-list", ListView)
            first_item = main_list.children[0]
            assert isinstance(first_item, _MainResultItem)
            label_widget = first_item.children[0]
            assert isinstance(label_widget, Static)
            label = _static_text(label_widget)
            assert label == "abbod (abbad, noun)"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_does_not_search_until_enter(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
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
    _insert_entry(
        lexicon_source_db,
        headword="browseonly",
        pos="noun",
        summary_sense="unique browse-only gloss",
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "browseonly")

            details_text = _details_text(app)
            assert "browseonly" in details_text
            assert "POS: noun" in details_text
            assert "unique browse-only gloss" in details_text

            main_list = app.query_one("#results-list", ListView)
            assert main_list.index == 0
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_wright_section_selection_opens_ingested_text_modal(
    lexicon_source_db: Path,
) -> None:
    _seed_catalog_assignment(
        lexicon_source_db,
        normalized_title="abbad",
        catalog_pos="noun",
        class_key="noun.masculine.a_stem",
    )
    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute(
            "UPDATE wright_sections SET section_text = ? WHERE section_no = ?",
            ("Representative ingested Wright paragraph for abbad.", 334),
        )
        connection.commit()

    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")
            await _select_abbad_hit(app, pilot)

            sections_title = app.query_one("#wright-sections-title", Static)
            assert "hidden" not in sections_title.classes
            sections_list = app.query_one("#wright-sections-list", ListView)
            assert "hidden" not in sections_list.classes
            sections_list.index = 0
            sections_list.action_select_cursor()
            await pilot.pause()

            modal_screen = app.screen_stack[-1]
            modal_text = _static_text(modal_screen.query_one("#wright-modal-text", Static))
            assert "Representative ingested Wright paragraph" in modal_text

            await pilot.press("escape")
            await pilot.pause()
            assert not list(app.query("#wright-modal"))
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_wright_section_selection_shows_not_ingested_message(
    lexicon_source_db: Path,
) -> None:
    _seed_catalog_assignment(
        lexicon_source_db,
        normalized_title="abbad",
        catalog_pos="noun",
        class_key="noun.masculine.a_stem",
    )

    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")
            await _select_abbad_hit(app, pilot)

            sections_list = app.query_one("#wright-sections-list", ListView)
            sections_list.index = 0
            sections_list.action_select_cursor()
            await pilot.pause()

            modal_screen = app.screen_stack[-1]
            modal_text = _static_text(modal_screen.query_one("#wright-modal-text", Static))
            assert (
                "Wright § 334 text not ingested — run dictionary ingest-wright-text"
                in modal_text
            )
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_no_match_shows_empty_state(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "orphan-form")

            main_list = app.query_one("#results-list", ListView)
            assert len(main_list.children) == 1
            assert not isinstance(main_list.children[0], _MainResultItem)

            details_text = _details_text(app)
            assert details_text == "No results."
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_morphology_sidebar_groups_by_wordclass_and_function(
    lexicon_source_db: Path,
) -> None:
    _seed_abbad_morphology_forms(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")
            await _select_abbad_hit(app, pilot)

            sidebar_text = _table_text(app.query_one("#morphology-table", DataTable))
            assert "abbades" in sidebar_text
            assert "abades" in sidebar_text or "abbades" in sidebar_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_oe_character_bar_inserts_into_search(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            first_button = app.query(".oe-char-button").first()
            await pilot.click(first_button)
            await pilot.pause()
            search = app.query_one("#search-input", Input)
            assert search.value == "æ"

            thorn_button = app.query(".oe-char-button")[1]
            await pilot.click(thorn_button)
            await pilot.pause()
            assert search.value == "æþ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_accepts_keyboard_unicode_characters(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus
            await pilot.press(
                "æ",
                "Æ",
                "ð",
                "Ð",
                "þ",
                "Þ",
                "ā",
                "ē",
                "ī",
                "ō",
                "ū",
                "ȳ",
                "ǣ",
                "ċ",
                "ġ",
            )
            assert search.value == "æÆðÐþÞāēīōūȳǣċġ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_oe_character_buttons_use_light_text_on_dark_background(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            screenshot = app.export_screenshot()
            for character in ("æ", "þ"):
                assert character in screenshot
            button_labels = [
                getattr(button.label, "plain", str(button.label))
                for button in app.query(".oe-char-button")
                if isinstance(button, Button)
            ]
            assert "ȳ" in button_labels
            assert "ǣ" in button_labels
            assert button_labels.count("æ") == 1
            assert "Æ" not in button_labels
            assert "Þ" not in button_labels
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_accepts_app_level_unicode_key_fallback(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus
            app.post_message(events.Key("æ", "æ"))
            await pilot.pause()
            app.post_message(events.Key("ċ", "ċ"))
            await pilot.pause()
            assert search.value == "æċ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_accepts_input_level_oe_key_aliases(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus
            search.post_message(events.Key("latin_small_letter_ae", None))
            await pilot.pause()
            search.post_message(events.Key("combining_macron", None))
            await pilot.pause()
            search.post_message(events.Key("latin_small_letter_c_with_dot_above", None))
            await pilot.pause()
            assert search.value == "ǣċ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_accepts_macos_abc_extended_alt_keys(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus

            for key in (
                "alt+apostrophe",
                "alt+shift+apostrophe",
                "alt+d",
                "alt+shift+d",
                "alt+t",
                "alt+shift+t",
            ):
                search.post_message(events.Key(key, None))
                await pilot.pause()

            search.post_message(events.Key("alt+a", None))
            await pilot.pause()
            await pilot.press("a")
            search.post_message(events.Key("alt+a", None))
            await pilot.pause()
            await pilot.press("A")
            search.post_message(events.Key("alt+a", None))
            await pilot.pause()
            search.post_message(events.Key("alt+apostrophe", None))
            await pilot.pause()
            search.post_message(events.Key("alt+a", None))
            await pilot.pause()
            search.post_message(events.Key("alt+shift+apostrophe", None))
            await pilot.pause()

            search.post_message(events.Key("alt+w", None))
            await pilot.pause()
            await pilot.press("c")
            search.post_message(events.Key("alt+w", None))
            await pilot.pause()
            await pilot.press("G")

            assert search.value == "æÆðÐþÞāĀǣǢċĠ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_search_normalizes_combining_old_english_marks(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            assert search.has_focus
            await pilot.press("a")
            app.post_message(events.Key("combining_macron", "\u0304"))
            await pilot.pause()
            await pilot.press("c")
            app.post_message(events.Key("combining_dot_above", "\u0307"))
            await pilot.pause()
            assert search.value == "āċ"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_oe_character_buttons_skip_tab_focus(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
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
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")
            search = app.query_one("#search-input", Input)
            assert search.has_focus
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_shows_connect_message_before_search(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            details_text = _static_text(app.query_one("#details-content", Static))
            assert "Connected to" in details_text
            assert "Search and select a result to view details." in details_text
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_build_then_browse_integration_smoke(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")
            await _select_abbad_hit(app, pilot)

            main_list = app.query_one("#results-list", ListView)
            assert isinstance(main_list.children[0], _MainResultItem)

            details_text = _details_text(app)
            assert "abbad" in details_text
            assert "POS: noun" in details_text
    finally:
        app.query_service.close()
