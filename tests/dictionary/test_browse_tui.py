"""Shell-level tests for the dictionary Textual browse scaffold."""

from __future__ import annotations

import sqlite3
from dataclasses import replace as dataclass_replace
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from rich.style import Style
from sqlalchemy import select
from sqlalchemy.orm import Session
from textual import events
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.content import Content
from textual.selection import Selection
from textual.widgets import Button, DataTable, Footer, Input, ListView, Static
from textual.widgets._footer import FooterKey, FooterLabel, KeyGroup

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import LemmaMorphClass, MorphClass
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.services.dictionary import browse_tui as browse_tui_module
from wyrdcraeft.services.dictionary.browse_query import DictionaryBrowseQueryService
from wyrdcraeft.services.dictionary.browse_tui import (
    DictionaryBrowseApp,
    DictionaryBrowseDataError,
    _MainResultItem,
    create_dictionary_browse_app,
    run_dictionary_browse,
)
from wyrdcraeft.services.dictionary.definition_line import definition_line
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
            assert "entry-banner" in ids
            assert "entry-column" in ids
            assert "entry-message" in ids
            assert "orphans-header" not in ids
            assert "orphans-list" not in ids
            # ADR 0026: one scrolling column; the old second scroll is gone.
            assert "details-content-scroll" not in ids
            assert "morphology-sidebar" not in ids
            column = app.query_one("#entry-column")
            assert isinstance(column, VerticalScroll)
            assert column.parent is app.query_one("#details-pane")
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


def _result_row_text(item: _MainResultItem) -> str:
    """
    Render one results row to plain text, left to right.

    Args:
        item: Results list row from the browse TUI.

    Returns:
        Space-joined text of the row's non-empty cells.

    """
    parts = [_static_text(widget) for widget in item.query(Static)]
    return " ".join(part for part in parts if part)


def _entry_column_text(app: DictionaryBrowseApp) -> str:
    """
    Read every drawn Static in the entry column as one plain-text target.

    Args:
        app: Running lexicon browse app under test.

    Returns:
        Newline-joined text of the displayed, non-empty Statics in
        ``#entry-column``, in document order.

    """
    column = app.query_one("#entry-column")
    parts = [
        _static_text(widget)
        for widget in column.query(Static)
        if widget.display and not widget.has_class("hidden")
    ]
    return "\n".join(part for part in parts if part)


def _entry_message_text(app: DictionaryBrowseApp) -> str:
    """
    Read the entry column's idle message.

    Args:
        app: Running lexicon browse app under test.

    Returns:
        Plain text of ``#entry-message``.

    """
    return _static_text(app.query_one("#entry-message", Static))


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
            headword = first_item.query_one(".result-headword", Static)
            assert _static_text(headword) == "abbad"
            tag = first_item.query_one(".pos-tag", Static)
            assert _static_text(tag) == "noun"
            assert tag.has_class("pos-noun")
            assert "(noun)" not in _result_row_text(first_item)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_results_row_shows_arrow_headword_when_variant_matched(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "ABBOD")

            main_list = app.query_one("#results-list", ListView)
            first_item = main_list.children[0]
            assert isinstance(first_item, _MainResultItem)
            headword = first_item.query_one(".result-headword", Static)
            label = _static_text(headword)
            assert label == "abbod → abbad"
            assert _result_row_text(first_item).startswith("abbod")
            assert "(abbad, noun)" not in _result_row_text(first_item)
            arrow_start = label.index("→")
            content = headword.render()
            assert isinstance(content, Content)
            assert any(
                span.start <= arrow_start and span.end == len(label)
                for span in content.spans
            ), "the '→ headword' part is drawn dim"
            assert not any(span.start == 0 for span in content.spans)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_theme_wyrdcraeft_is_active(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            assert app.theme == "wyrdcraeft"
            theme = app.current_theme
            assert theme.background == "#101319"
            assert theme.surface == "#151922"
            assert theme.primary == "#e6b36a"
            assert theme.foreground == "#dbe0ea"
            assert app.CSS_PATH is not None
            assert Path(str(app.CSS_PATH)).name == "browse.tcss"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_results_row_dims_headword_hyphen(lexicon_source_db: Path) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="for-sceamian",
        pos="verb",
        summary_sense="to be greatly ashamed",
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "for-sceamian")

            main_list = app.query_one("#results-list", ListView)
            item = next(
                child
                for child in main_list.children
                if isinstance(child, _MainResultItem)
                and child.hit.headword == "for-sceamian"
            )
            headword = item.query_one(".result-headword", Static)
            assert _static_text(headword) == "for-sceamian"
            content = headword.render()
            assert isinstance(content, Content)
            hyphen = 3
            assert any(
                span.start <= hyphen < span.end for span in content.spans
            ), "hyphen inside the headword is drawn dim"
            assert not any(span.start <= 0 < span.end for span in content.spans)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_results_row_is_three_cells_tall(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await _submit_search(app, pilot, "abbad")
            await pilot.pause()

            main_list = app.query_one("#results-list", ListView)
            first_item = main_list.children[0]
            assert isinstance(first_item, _MainResultItem)
            assert first_item.outer_size.height == 3
            headword = first_item.query_one(".result-headword", Static)
            assert headword.region.y == first_item.region.y + 1

            main_list.focus()
            main_list.index = 0
            await pilot.pause()
            assert first_item.has_class("-highlight")
            assert first_item.outer_size.height == 3
            assert headword.region.y == first_item.region.y + 1
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_results_row_shows_definition_line(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 40)) as pilot:
            await _submit_search(app, pilot, "abbad")
            await app.workers.wait_for_complete()
            await pilot.pause()

            main_list = app.query_one("#results-list", ListView)
            first_item = main_list.children[0]
            assert isinstance(first_item, _MainResultItem)
            details = app.query_service.get_details(first_item.hit.entry_id)
            assert details is not None
            ordered = sorted(details.senses, key=lambda sense: sense.order_index)
            expected = definition_line(
                details.pos, [sense.gloss_en for sense in ordered]
            )
            assert expected
            gloss = first_item.query_one(".result-definition", Static)
            assert _static_text(gloss) == expected
            assert first_item.hit.definition_line == expected
            row_text = _result_row_text(first_item)
            assert row_text.index("abbad") < row_text.index(expected)
            assert row_text.index(expected) < row_text.rindex("noun")
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_focused_pane_has_accent_title_class(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            results_pane = app.query_one("#results-pane")
            details_pane = app.query_one("#details-pane")
            assert results_pane.border_title
            assert details_pane.border_title
            assert not results_pane.has_class("pane-focused")
            assert not details_pane.has_class("pane-focused")

            await _submit_search(app, pilot, "abbad")
            app.query_one("#results-list", ListView).focus()
            await pilot.pause()
            assert results_pane.has_class("pane-focused")
            assert not details_pane.has_class("pane-focused")

            app.focus_search()
            await pilot.pause()
            assert not results_pane.has_class("pane-focused")
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_does_not_search_until_enter(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test():
            search = app.query_one("#search-input", Input)
            search.value = "ABBOD"
            assert "Connected to" in _entry_message_text(app)

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

            headword = _static_text(app.query_one("#entry-headword", Static))
            assert headword == "browseonly"
            tag = app.query_one("#entry-pos-tag", Static)
            assert _static_text(tag) == "noun"
            assert tag.has_class("pos-noun")
            senses = app.query_one("#entry-senses")
            assert "unique browse-only gloss" in [
                _static_text(widget) for widget in senses.query(Static)
            ]
            assert not app.query_one("#entry-message", Static).display

            main_list = app.query_one("#results-list", ListView)
            assert main_list.index == 0
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_hides_wright_section_list_by_default(
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

            sections_title = app.query_one("#wright-sections-title", Static)
            sections_list = app.query_one("#wright-sections-list", ListView)
            assert "hidden" in sections_title.classes
            assert "hidden" in sections_list.classes
            assert len(list(sections_list.children)) == 0
            rows = _key_value_rows(app)
            assert _static_text(rows["Class"]) not in {"", "unclassified"}
            assert _static_text(rows["Source"]) == "paradigm"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_browse_wright_section_selection_opens_ingested_text_modal(
    lexicon_source_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(browse_tui_module, "SHOW_WRIGHT_SECTION_LISTINGS", True)
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(browse_tui_module, "SHOW_WRIGHT_SECTION_LISTINGS", True)
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

            assert _entry_column_text(app) == "No results."
            assert not app.query(".entry-section")
            assert not app.query_one("#entry-banner").display
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
async def test_browse_prep_entry_has_no_forms_table(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="tō",
        pos="preposition",
        summary_sense="to, toward",
    )
    entry_id = _bt_entry_id(lexicon_source_db, norm_key="to")
    prep_pos_id = _pos_id(lexicon_source_db, code="preposition")
    with sqlite3.connect(lexicon_source_db) as connection:
        dative_code_id = _insert_inflection_code(
            connection,
            code="dative singular",
            pos_id=prep_pos_id,
        )
        connection.execute(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment,
                bt_key, title_key, stem_key, form_key, formi_key,
                entry_id, wordclass_id, inflection_code_id
            ) VALUES (
                0, 'to', 'to', 'tō', 'to', 'to', 'tō',
                '0-to-0', '0', '0', '',
                'to', 'to', 'to', 'to', 'to',
                ?, ?, ?
            )
            """,
            (entry_id, prep_pos_id, dative_code_id),
        )
        connection.commit()

    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "to")

            # ADR 0026: no Forms section, so no table, even with linked forms.
            assert not app.query("#morphology-table")
            assert not app.query("#entry-forms")
            assert "No morphology rows linked." not in _entry_column_text(app)

            tag = app.query_one("#entry-pos-tag", Static)
            assert _static_text(tag) == "preposition"
            assert tag.has_class("pos-preposition")
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
async def test_browse_search_paste_inserts_once_in_nfc(
    lexicon_source_db: Path,
) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            search = app.query_one("#search-input", Input)
            search.post_message(events.Paste("a\u0304word"))
            await pilot.pause()
            assert search.value == "āword"
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
            details_text = _entry_message_text(app)
            assert "Connected to" in details_text
            assert "Search and select a result to view details." in details_text
            copy_button = app.query_one("#copy-definition", Button)
            assert copy_button.disabled is True
            assert not app.query_one("#entry-banner").display
            assert _static_text(app.query_one("#entry-headword", Static)) == ""
            ancestor_ids = {node.id for node in copy_button.ancestors}
            assert "entry-banner" in ancestor_ids
            assert "entry-column" not in ancestor_ids
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

            assert _static_text(app.query_one("#entry-headword", Static)) == "abbad"
            assert _static_text(app.query_one("#entry-pos-tag", Static)) == "noun"
            assert app.query_one("#entry-banner").display
    finally:
        app.query_service.close()


def _insert_two_senses_out_of_path_order(db_path: Path, *, headword: str) -> None:
    """Insert one entry whose ``order_index`` disagrees with ``sense_path``."""
    _insert_entry(db_path, headword=headword, pos="noun", summary_sense="placeholder")
    norm_key = normalize_old_english(headword)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT id FROM bt_entries WHERE norm_key = ?",
            (norm_key,),
        ).fetchone()
        assert row is not None
        entry_id = int(row[0])
        connection.execute("DELETE FROM bt_senses WHERE entry_id = ?", (entry_id,))
        for order_index, sense_path, gloss in ((0, "2", "second"), (1, "1", "first")):
            connection.execute(
                """
                INSERT INTO bt_senses (
                    entry_id, sense_label, gloss_en, order_index, sense_path,
                    parent_path, source_label_raw, source_fragment_raw,
                    prefix_fragment_raw, modifiers_json,
                    grammatical_context_json, usage_note
                ) VALUES (?, '', ?, ?, ?, NULL, '', ?, '', '[]', '[]', '')
                """,
                (entry_id, gloss, order_index, sense_path, gloss),
            )
        connection.commit()


@pytest.mark.anyio
async def test_copy_definition_button_copies_selected_entry(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="copyme",
        pos="noun",
        summary_sense="time; time; date",
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.pause()
            assert app.query_one("#copy-definition", Button).disabled is False
            await pilot.click("#copy-definition")
            await pilot.pause()
            assert app.clipboard == "time, date"
            assert app.focused is not None
            assert app.focused.id == "search-input"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_copy_definition_button_label_is_fully_visible(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="copyme",
        pos="noun",
        summary_sense="time; time; date",
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.pause()
            button = app.query_one("#copy-definition", Button)
            visible = app.screen.find_widget(button).visible_region
            assert visible.height == button.region.height
            assert button.region.height >= 1
            assert "Copy" in str(button.render())
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_no_results_search_resets_title_and_disables_copy(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="copyme",
        pos="noun",
        summary_sense="time; time; date",
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.pause()
            copy_button = app.query_one("#copy-definition", Button)
            assert copy_button.disabled is False
            assert _static_text(app.query_one("#entry-headword", Static)) == "copyme"
            assert app.query_one("#entry-banner").display
            await _submit_search(app, pilot, "orphan-form")
            await pilot.pause()
            assert _static_text(app.query_one("#entry-headword", Static)) == ""
            assert not app.query_one("#entry-banner").display
            assert not app.query(".entry-section")
            assert _entry_message_text(app) == "No results."
            assert copy_button.disabled is True
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_ctrl_c_in_search_selection_does_not_copy_the_definition(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="copyme",
        pos="noun",
        summary_sense="time; time; date",
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.pause()
            search = app.query_one("#search-input", Input)
            search.selection = Selection(0, len(search.value))
            await pilot.press("ctrl+c")
            await pilot.pause()
            assert app.clipboard == search.value
    finally:
        app.query_service.close()


def test_browse_tui_source_does_not_import_sqlalchemy() -> None:
    source = Path(browse_tui_module.__file__).read_text(encoding="utf-8")
    assert "from sqlalchemy" not in source
    assert "import sqlalchemy" not in source
    assert "query_service._connection" not in source
    assert "._connection" not in source


def test_create_app_closes_service_when_unready(
    empty_browse_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[object] = []
    real_close = DictionaryBrowseQueryService.close

    def tracking_close(self: DictionaryBrowseQueryService) -> None:
        closed.append(self)
        real_close(self)

    monkeypatch.setattr(DictionaryBrowseQueryService, "close", tracking_close)
    with pytest.raises(DictionaryBrowseDataError):
        create_dictionary_browse_app(empty_browse_db)
    assert closed


# --- Task 5b: sectioned entry column (ADR 0026) ---------------------------------

#: Real Bosworth-Toller etymology of the preposition ``for``.
_FOR_ETYMOLOGY = (
    "[<I>Piers P. Chauc.</I> for: <I>Laym. for,</I> uor: <I>Orm.</I> forr: "
    "<I>Plat,</I> för, vör: <I>O. Frs.</I> fori, fore, for: <I>Dut.</I> voor: "
    "<I>Ger.</I> für: <I>M. H. Ger.</I> vür, vüre: <I>O. H. Ger.</I> fora, furi: "
    "<I>Goth.</I> faur, faura: <I>Dan.</I> for: <I>Swed.</I> för: "
    "<I>Icel.</I> fyrir: <I>Lat.</I> pro.]"
)
#: Real etymology whose stray leading ``R.`` parses as a note fragment.
_AC_ETYMOLOGY = (
    "[R. <I>Glouc. Orm.</I> ac: <I>Laym.</I> ac, æc, ah: <I>Scot.</I> ac: "
    "<I>O. Sax.</I> ak: <I>O. H. Ger.</I> oh; <I>Goth,</I> ak.]"
)


def _insert_rich_entry(
    db_path: Path,
    *,
    headword: str,
    pos: str,
    senses: tuple[tuple[str, str, str], ...],
    etymology: str = "",
) -> None:
    """Insert one entry with labelled senses ``(sense_path, raw_label, gloss)``."""
    norm_key = normalize_old_english(headword)
    assert norm_key is not None
    pos_id = _pos_id(db_path, code=pos)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO bt_entries (
                norm_key, headword, normalized_title, pos_id, genders_json,
                etymology, see_also_json, source_line_nos_json, entry_order
            ) VALUES (?, ?, ?, ?, '[]', ?, '[]', '[]', 1)
            """,
            (
                norm_key,
                headword,
                normalize_morphology_title(headword),
                pos_id,
                etymology,
            ),
        )
        row = connection.execute(
            "SELECT id FROM bt_entries WHERE norm_key = ? AND pos_id = ?",
            (norm_key, pos_id),
        ).fetchone()
        assert row is not None
        for order_index, (sense_path, raw_label, gloss) in enumerate(senses):
            connection.execute(
                """
                INSERT INTO bt_senses (
                    entry_id, sense_label, gloss_en, order_index, sense_path,
                    parent_path, source_label_raw, source_fragment_raw,
                    prefix_fragment_raw, modifiers_json,
                    grammatical_context_json, usage_note
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, '', '[]', '[]', '')
                """,
                (
                    int(row[0]),
                    raw_label,
                    gloss,
                    order_index,
                    sense_path,
                    raw_label,
                    gloss,
                ),
            )
        connection.commit()


def _seed_forms(
    db_path: Path,
    *,
    headword: str,
    pos: str,
    forms: tuple[tuple[str, str], ...],
) -> None:
    """Link ``(function, form)`` morphology rows to one entry."""
    norm_key = normalize_old_english(headword)
    assert norm_key is not None
    entry_id = _bt_entry_id(db_path, norm_key=norm_key)
    pos_id = _pos_id(db_path, code=pos)
    with sqlite3.connect(db_path) as connection:
        for function, form in forms:
            existing = connection.execute(
                "SELECT id FROM inflection_codes WHERE code = ?",
                (function,),
            ).fetchone()
            code_id = (
                int(existing[0])
                if existing is not None
                else _insert_inflection_code(connection, code=function, pos_id=pos_id)
            )
            connection.execute(
                """
                INSERT INTO forms (
                    counter, formi, BT, title, normalized_title, stem, form,
                    formParts, var, probability, comment,
                    bt_key, title_key, stem_key, form_key, formi_key,
                    entry_id, wordclass_id, inflection_code_id
                ) VALUES (
                    0, ?, ?, ?, ?, ?, ?, '0', '0', '0', '',
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    form,
                    headword,
                    headword,
                    norm_key,
                    norm_key,
                    form,
                    norm_key,
                    norm_key,
                    norm_key,
                    form,
                    form,
                    entry_id,
                    pos_id,
                    code_id,
                ),
            )
        connection.commit()


async def _open_entry(app: DictionaryBrowseApp, pilot, headword: str) -> None:
    """Search for ``headword`` and open its results row."""
    await _submit_search(app, pilot, headword)
    await pilot.pause()
    main_list = app.query_one("#results-list", ListView)
    for index, child in enumerate(main_list.children):
        if isinstance(child, _MainResultItem) and child.hit.headword == headword:
            main_list.index = index
            main_list.action_select_cursor()
            await pilot.pause()
            await pilot.pause()
            return
    pytest.fail(f"{headword} search hit not found in results list")


def _column_section_ids(app: DictionaryBrowseApp) -> list[str]:
    """Return the ids of the ``#entry-*`` sections in the column, in order."""
    column = app.query_one("#entry-column")
    return [
        node.id
        for node in column.walk_children()
        if node.id is not None
        and node.id.startswith("entry-")
        and node.id != "entry-message"
    ]


def _section_label_texts(app: DictionaryBrowseApp) -> list[str]:
    """Return the text of every section label drawn in the entry column."""
    column = app.query_one("#entry-column")
    labels = column.query(".section-label-text").results(Static)
    return [_static_text(label) for label in labels]


def _key_value_rows(app: DictionaryBrowseApp) -> dict[str, Static]:
    """Map each key/value label to its value widget."""
    labels = list(app.query("#entry-keyvalues .kv-label").results(Static))
    values = list(app.query("#entry-keyvalues .kv-value").results(Static))
    assert len(labels) == len(values)
    return {
        _static_text(label): value
        for label, value in zip(labels, values, strict=True)
    }


def _spans_cover(content: Content, start: int, end: int, *needles: str) -> bool:
    """Whether one span over ``[start, end)`` has every ``needles`` style part."""
    return any(
        span.start <= start
        and span.end >= end
        and all(needle in str(span.style) for needle in needles)
        for span in content.spans
    )


@pytest.mark.anyio
async def test_entry_column_sections_in_order(lexicon_source_db: Path) -> None:
    _insert_rich_entry(
        lexicon_source_db,
        headword="testsceamian",
        pos="verb",
        senses=(("1", "1", "to be greatly ashamed"), ("2", "2", "to make ashamed")),
        etymology="[<I>Orm.</I> forrshamedd <I>much ashamed.</I>]",
    )
    _seed_forms(
        lexicon_source_db,
        headword="testsceamian",
        pos="verb",
        forms=(("if", "testsceamian"), ("psinsg1", "testsceame")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testsceamian")
            assert _column_section_ids(app) == [
                "entry-keyvalues",
                "entry-senses",
                "entry-etymology",
                "entry-forms",
            ]
            assert _section_label_texts(app) == ["SENSES", "ETYMOLOGY", "FORMS"]
            table = app.query_one("#entry-forms #morphology-table", DataTable)
            assert "testsceame" in _table_text(table)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_entry_banner_is_pinned_outside_the_scrolling_column(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(lexicon_source_db, headword="bannerword", pos="noun", summary_sense="x")
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "bannerword")
            banner = app.query_one("#entry-banner")
            column = app.query_one("#entry-column")
            assert column not in banner.ancestors
            assert banner not in column.ancestors
            assert banner.region.bottom <= column.region.y
            assert _static_text(app.query_one("#entry-headword", Static)) == "bannerword"
            tag = app.query_one("#entry-pos-tag", Static)
            assert _static_text(tag) == "noun"
            assert tag.has_class("pos-tag")
            assert tag.has_class("pos-noun")
            copy_button = app.query_one("#copy-definition", Button)
            assert banner in copy_button.ancestors
            assert copy_button.can_focus is False
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_entry_without_etymology_has_no_etymology_section(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(lexicon_source_db, headword="noetym", pos="noun", summary_sense="x")
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "noetym")
            assert not app.query("#entry-etymology")
            assert "ETYMOLOGY" not in _section_label_texts(app)
            assert "entry-senses" in _column_section_ids(app)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_unknown_pos_entry_has_no_class_row_and_no_forms_section(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(lexicon_source_db, headword="wāwā", pos="unknown", summary_sense="woe!")
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "wāwā")
            assert "entry-senses" in _column_section_ids(app)
            assert "Class" not in _key_value_rows(app)
            assert not app.query("#entry-forms")
            assert not app.query("#morphology-table")
            assert "FORMS" not in _section_label_texts(app)
            assert _static_text(app.query_one("#entry-pos-tag", Static)) == "unknown"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_preposition_has_no_forms_section_or_label(
    lexicon_source_db: Path,
) -> None:
    _insert_rich_entry(
        lexicon_source_db,
        headword="for",
        pos="preposition",
        senses=(("1", "1", "for, on account of"),),
        etymology=_FOR_ETYMOLOGY,
    )
    _seed_forms(
        lexicon_source_db,
        headword="for",
        pos="preposition",
        forms=(("dative singular", "for"),),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "for")
            assert not app.query("#entry-forms")
            assert not app.query("#morphology-table")
            assert "FORMS" not in _section_label_texts(app)
            assert "Class" not in _key_value_rows(app)
            assert _column_section_ids(app)[-1] == "entry-etymology"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_unclassified_class_row_is_dim(lexicon_source_db: Path) -> None:
    _insert_entry(lexicon_source_db, headword="unclassed", pos="noun", summary_sense="x")
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "unclassed")
            value = _key_value_rows(app)["Class"]
            assert _static_text(value) == "unclassified"
            content = value.render()
            assert isinstance(content, Content)
            assert _spans_cover(content, 0, len("unclassified"), "$text-muted")
    finally:
        app.query_service.close()


def _sense_rows(app: DictionaryBrowseApp) -> dict[str, Widget]:
    """Map each drawn sense number (``5.``, ``5a.``) to its sense row."""
    rows: dict[str, Widget] = {}
    for row in app.query("#entry-senses .sense-row"):
        number = row.query_one(".sense-number", Static)
        rows[_static_text(number)] = row
    return rows


#: ``healdan``-like senses with sub-senses ``5a`` and ``10c``.
_HEALDAN_SENSES = (
    ("4", "IV", "to behave, conduct"),
    ("5", "V", "to guard, defend, keep, preserve"),
    ("5.1", "V a", "to hold, bear; conduct"),
    ("10", "X", "to keep; keep in store"),
    ("10.3", "X c", "to continue to occupy, not to leave"),
)


@pytest.mark.anyio
async def test_sub_senses_are_indented_with_dim_number(lexicon_source_db: Path) -> None:
    _insert_rich_entry(
        lexicon_source_db, headword="testhealdan", pos="verb", senses=_HEALDAN_SENSES
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 60)) as pilot:
            await _open_entry(app, pilot, "testhealdan")
            rows = _sense_rows(app)
            assert list(rows) == ["4.", "5.", "5a.", "10.", "10c."]
            for main, sub in (("5.", "5a."), ("10.", "10c.")):
                main_number = rows[main].query_one(".sense-number", Static)
                sub_number = rows[sub].query_one(".sense-number", Static)
                assert sub_number.region.x > main_number.region.x
                content = sub_number.render()
                assert isinstance(content, Content)
                assert _spans_cover(content, 0, len(sub), "$text-muted")
                assert not _spans_cover(content, 0, len(sub), "bold")
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_main_sense_number_is_accent_bold(lexicon_source_db: Path) -> None:
    _insert_rich_entry(
        lexicon_source_db, headword="testhealdan", pos="verb", senses=_HEALDAN_SENSES
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 60)) as pilot:
            await _open_entry(app, pilot, "testhealdan")
            rows = _sense_rows(app)
            for main in ("4.", "5.", "10."):
                number = rows[main].query_one(".sense-number", Static)
                content = number.render()
                assert isinstance(content, Content)
                assert _spans_cover(content, 0, len(main), "bold", "$primary")
            gloss = rows["5a."].query_one(".sense-gloss", Static)
            assert _static_text(gloss) == "to hold, bear; conduct"
    finally:
        app.query_service.close()


def _patch_details(
    app: DictionaryBrowseApp,
    monkeypatch: pytest.MonkeyPatch,
    **changes: object,
) -> None:
    """Make ``get_details`` return its payload with ``changes`` applied."""
    real_get_details = app.query_service.get_details

    def _get_details(entry_id: int) -> object:
        details = real_get_details(entry_id)
        if details is None:
            return None
        return dataclass_replace(details, **changes)  # type: ignore[arg-type]

    monkeypatch.setattr(app.query_service, "get_details", _get_details)


def _senses_children_texts(app: DictionaryBrowseApp) -> list[str]:
    """Plain text of each line in the Senses section after its label."""
    section = app.query_one("#entry-senses")
    texts: list[str] = []
    for child in section.children:
        if child.has_class("section-label"):
            continue
        if child.has_class("sense-row"):
            cells = [_static_text(cell) for cell in child.query(Static)]
            texts.append(" ".join(cell for cell in cells if cell))
        elif isinstance(child, Static):
            texts.append(_static_text(child))
    return texts


@pytest.mark.anyio
async def test_summary_is_first_senses_line_when_it_differs_from_sense_one(
    lexicon_source_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _insert_rich_entry(
        lexicon_source_db,
        headword="testsumma",
        pos="noun",
        senses=(("1", "1", "a shield"), ("2", "2", "a protector")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    _patch_details(app, monkeypatch, summary_sense="a defence of any kind")
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testsumma")
            texts = _senses_children_texts(app)
            assert texts == ["a defence of any kind", "1. a shield", "2. a protector"]
            assert app.query_one("#entry-senses .senses-summary", Static)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_summary_dropped_when_equal_to_sense_one(lexicon_source_db: Path) -> None:
    _insert_rich_entry(
        lexicon_source_db,
        headword="testsumma",
        pos="noun",
        senses=(("1", "1", "a shield"), ("2", "2", "a protector")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testsumma")
            assert _senses_children_texts(app) == ["1. a shield", "2. a protector"]
            assert not app.query("#entry-senses .senses-summary")
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_summary_shown_when_entry_has_no_senses(
    lexicon_source_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _insert_entry(lexicon_source_db, headword="testlone", pos="noun", summary_sense="x")
    app = create_dictionary_browse_app(lexicon_source_db)
    _patch_details(app, monkeypatch, senses=[], summary_sense="a lone summary")
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testlone")
            assert _senses_children_texts(app) == ["a lone summary"]
            assert not app.query("#entry-senses .sense-row")
    finally:
        app.query_service.close()


def _etymology_grid(app: DictionaryBrowseApp) -> tuple[list[str], list[list[str]]]:
    """Read the etymology table as ``(headers, rows)`` of plain text."""
    table = app.query_one("#entry-etymology .ety-table")
    columns = table.styles.grid_size_columns
    cells = [_static_text(cell) for cell in table.query(Static)]
    headers = cells[:columns]
    body = cells[columns:]
    return headers, [body[i : i + columns] for i in range(0, len(body), columns)]


@pytest.mark.anyio
async def test_etymology_table_drops_empty_columns(lexicon_source_db: Path) -> None:
    _insert_rich_entry(
        lexicon_source_db,
        headword="for",
        pos="preposition",
        senses=(("1", "1", "for, on account of"),),
        etymology=_FOR_ETYMOLOGY,
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "for")
            headers, rows = _etymology_grid(app)
            assert headers == ["LANGUAGE", "WORD"]
            assert rows[0] == ["Piers P. Chauc.", "for"]
            assert rows[1] == ["Laym.", "for, uor"]
            assert rows[-1] == ["Lat.", "pro"]
            assert len(rows) == 14
            assert not app.query("#entry-etymology .ety-note")
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_etymology_note_line_under_table(lexicon_source_db: Path) -> None:
    _insert_rich_entry(
        lexicon_source_db,
        headword="testac",
        pos="conjunction",
        senses=(("1", "1", "but"),),
        etymology=_AC_ETYMOLOGY,
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 60)) as pilot:
            await _open_entry(app, pilot, "testac")
            table = app.query_one("#entry-etymology .ety-table")
            note = app.query_one("#entry-etymology .ety-note", Static)
            assert _static_text(note) == "Note: R"
            assert note.region.y >= table.region.bottom
            headers, rows = _etymology_grid(app)
            assert headers == ["LANGUAGE", "WORD"]
            assert rows[0] == ["Glouc. Orm.", "ac"]
    finally:
        app.query_service.close()


# --- Task 6: wrapping forms and switching (ADR 0027) -------------------------

#: Present indicative 1sg variants long enough to wrap at 60 columns.
_LONG_PRESENT_FORMS = (
    "testhealde",
    "testhealdu",
    "testhealdo",
    "testhealdæ",
    "testhaldee",
    "testhaldeo",
    "testheladu",
    "testhieldo",
    "testhealdige",
    "testhealdie",
)
#: Adjective forms per (strength morph class, function), all distinct.
_FULL_ADJECTIVE_FORMS = (
    ("adj.strong.a_o_stem", "PoSgMaNo", "strpos"),
    ("adj.strong.a_o_stem", "CoSgMaNo", "strcomp"),
    ("adj.strong.a_o_stem", "SpSgMaNo", "strsup"),
    ("adj.weak", "PoSgMaNo", "wkpos"),
    ("adj.weak", "CoSgMaNo", "wkcomp"),
    ("adj.weak", "SpSgMaNo", "wksup"),
)
#: Every forms-table key that can act on a switch.
_SWITCH_KEYS = ("right", "left", "right_square_bracket", "left_square_bracket")


def _seed_classed_forms(
    db_path: Path,
    *,
    headword: str,
    pos: str,
    forms: tuple[tuple[str, str, str], ...],
) -> None:
    """Link ``(morph class key, function, form)`` rows; loads the catalog."""
    engine = create_engine(db_path)
    try:
        MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
    finally:
        engine.dispose()
    _seed_forms(
        db_path,
        headword=headword,
        pos=pos,
        forms=tuple((function, form) for _key, function, form in forms),
    )
    with sqlite3.connect(db_path) as connection:
        for class_key, _function, form in forms:
            connection.execute(
                """
                UPDATE forms SET morph_class_id = (
                    SELECT id FROM morph_classes WHERE class_key = ?
                ) WHERE form = ?
                """,
                (class_key, form),
            )
        connection.commit()


def _seed_verb(db_path: Path, headword: str, forms: tuple[tuple[str, str], ...]) -> None:
    """Insert one verb entry with one sense and the given linked forms."""
    _insert_entry(db_path, headword=headword, pos="verb", summary_sense="to hold")
    _seed_forms(db_path, headword=headword, pos="verb", forms=forms)


def _seed_adjective(
    db_path: Path,
    forms: tuple[tuple[str, str, str], ...] = _FULL_ADJECTIVE_FORMS,
) -> None:
    """Insert the ``testgod`` adjective with strong and weak linked forms."""
    _insert_entry(db_path, headword="testgod", pos="adjective", summary_sense="good")
    _seed_classed_forms(db_path, headword="testgod", pos="adjective", forms=forms)


def _forms_table(app: DictionaryBrowseApp) -> DataTable:
    """Return the single forms table."""
    return app.query_one("#entry-forms #morphology-table", DataTable)


def _rendered_lines(table: DataTable) -> list[str]:
    """Return the table's painted lines as plain text."""
    return [table.render_line(y).text for y in range(table.size.height)]


def _assert_table_fits_and_paints(table: DataTable, forms: tuple[str, ...]) -> None:
    """
    Assert the real no-clipping invariants of the forms table.

    The overflow guard in ``browse.tcss`` keeps scrollbars off, so the
    scrollbar flags prove nothing; check widths and painted text instead.
    """
    assert table.virtual_size.width <= table.size.width
    columns_right = table.region.x + sum(
        column.get_render_width(table) for column in table.ordered_columns
    )
    assert columns_right <= table.region.right
    painted = "\n".join(_rendered_lines(table))
    assert "…" not in painted
    for form in forms:
        assert form in painted


def _active_tabs(app: DictionaryBrowseApp) -> list[str]:
    """Return the bold (selected) labels of every displayed tab strip."""
    labels: list[str] = []
    for strip in app.query("#entry-forms .forms-tabs").results(Static):
        if not strip.display:
            continue
        content = strip.render()
        assert isinstance(content, Content)
        labels.extend(
            content.plain[span.start : span.end]
            for span in content.spans
            if "bold" in str(span.style)
        )
    return labels


def _shown_forms(app: DictionaryBrowseApp) -> str:
    """Return the visible forms table text, or ``""`` while it is hidden."""
    table = _forms_table(app)
    return _table_text(table) if table.display else ""


async def _focus_entry_column(app: DictionaryBrowseApp, pilot) -> None:
    """Give the entry column keyboard focus."""
    app.query_one("#entry-column").focus()
    await pilot.pause()


async def _press(pilot, *keys: str) -> None:
    """Press keys and let the forms table repaint."""
    await pilot.press(*keys)
    await pilot.pause()
    await pilot.pause()


@pytest.mark.anyio
async def test_long_verb_forms_wrap_without_ellipsis(lexicon_source_db: Path) -> None:
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        (
            ("if", "testhealdan"),
            *(("psinsg1", form) for form in _LONG_PRESENT_FORMS),
        ),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(60, 40)) as pilot:
            await _open_entry(app, pilot, "testhealdan")
            table = _forms_table(app)
            forms = (*_LONG_PRESENT_FORMS, "testhealdan")
            _assert_table_fits_and_paints(table, forms)
            assert "…" not in _table_text(table)
            for form in forms:
                assert form in _table_text(table)
            assert any(row.height > 1 for row in table.rows.values())
            column = app.query_one("#entry-column")
            assert column.virtual_size.width <= column.scrollable_content_region.width
            assert table.region.right <= column.scrollable_content_region.right
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_forms_column_width_follows_pane_resize(lexicon_source_db: Path) -> None:
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        tuple(("psinsg1", form) for form in _LONG_PRESENT_FORMS),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 40)) as pilot:
            await _open_entry(app, pilot, "testhealdan")
            wide = _forms_table(app).ordered_columns[-1].width
            await pilot.resize_terminal(60, 40)
            await pilot.pause()
            await pilot.pause()
            table = _forms_table(app)
            assert table.ordered_columns[-1].width < wide
            _assert_table_fits_and_paints(table, _LONG_PRESENT_FORMS)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_forms_are_regular_weight_in_the_form_colour(
    lexicon_source_db: Path,
) -> None:
    # No citation marker in the model yet (ADR 0027), so no form is bold.
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        tuple(("psinsg1", form) for form in _LONG_PRESENT_FORMS),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testhealdan")
            cell = _forms_table(app).get_row_at(0)[-1]
            assert cell.plain == ", ".join(sorted(_LONG_PRESENT_FORMS))
            assert not cell.style
            accent = app.theme_variables["accent"].casefold()
            assert [(span.start, span.end) for span in cell.spans] == [
                (0, len(cell.plain))
            ]
            for span in cell.spans:
                assert isinstance(span.style, Style)
                assert not span.style.bold
                color = span.style.color
                assert color is not None
                assert color.triplet is not None
                assert color.triplet.hex.casefold() == accent
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_present_past_switch_with_arrow_keys(lexicon_source_db: Path) -> None:
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        (("psinsg1", "testhealde"), ("painsg1", "testheold")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testhealdan")
            await _focus_entry_column(app, pilot)
            assert _active_tabs(app) == ["Present"]
            assert "testhealde" in _shown_forms(app)
            assert "testheold" not in _shown_forms(app)
            await _press(pilot, "right")
            assert _active_tabs(app) == ["Past"]
            assert "testheold" in _shown_forms(app)
            assert "testhealde" not in _shown_forms(app)
            await _press(pilot, "left")
            assert _active_tabs(app) == ["Present"]
            assert "testhealde" in _shown_forms(app)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_present_and_past_with_different_column_counts(
    lexicon_source_db: Path,
) -> None:
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        (("psinsg1", "testhealde"), ("PaPt", "testhealden")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testhealdan")
            await _focus_entry_column(app, pilot)
            table = _forms_table(app)
            labels = [str(column.label) for column in table.ordered_columns]
            assert labels == ["", "Person", "Forms"]
            await _press(pilot, "right")
            table = _forms_table(app)
            labels = [str(column.label) for column in table.ordered_columns]
            assert labels == ["", "Forms"]
            assert table.row_count == 1
            row = [str(cell) for cell in table.get_row_at(0)]
            assert row == ["Participles", "testhealden"]
            await _press(pilot, "left")
            table = _forms_table(app)
            assert len(table.ordered_columns) == 3
            assert "testhealden" not in _table_text(table)
            assert "testhealde" in _table_text(table)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_adjective_degree_switch_with_brackets(lexicon_source_db: Path) -> None:
    _seed_adjective(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testgod")
            await _focus_entry_column(app, pilot)
            assert _active_tabs(app) == ["Strong", "Positive"]
            assert _shown_forms(app).split() == ["Nom", "strpos"]
            await _press(pilot, "right_square_bracket")
            assert _active_tabs(app) == ["Strong", "Comparative"]
            assert _shown_forms(app).split() == ["Nom", "strcomp"]
            await _press(pilot, "left_square_bracket")
            assert _active_tabs(app) == ["Strong", "Positive"]
            assert _shown_forms(app).split() == ["Nom", "strpos"]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_adjective_two_axis_selection(lexicon_source_db: Path) -> None:
    _seed_adjective(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testgod")
            await _focus_entry_column(app, pilot)
            await _press(pilot, "right", "right_square_bracket")
            assert _active_tabs(app) == ["Weak", "Comparative"]
            assert _shown_forms(app).split() == ["Nom", "wkcomp"]
            steps = (
                ("right_square_bracket", ("Weak", "Superlative"), "wksup"),
                ("left", ("Strong", "Superlative"), "strsup"),
                ("left_square_bracket", ("Strong", "Comparative"), "strcomp"),
                ("left_square_bracket", ("Strong", "Positive"), "strpos"),
                ("right", ("Weak", "Positive"), "wkpos"),
            )
            for key, tabs, form in steps:
                await _press(pilot, key)
                assert tuple(_active_tabs(app)) == tabs
                assert _shown_forms(app).split() == ["Nom", form]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_adjective_primary_missing_a_secondary_shows_empty_state(
    lexicon_source_db: Path,
) -> None:
    _seed_adjective(
        lexicon_source_db,
        tuple(row for row in _FULL_ADJECTIVE_FORMS if row[2] != "strcomp"),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testgod")
            await _focus_entry_column(app, pilot)
            empty = app.query_one("#entry-forms #forms-empty", Static)
            assert not empty.display
            await _press(pilot, "right_square_bracket")
            assert _active_tabs(app) == ["Strong", "Comparative"]
            assert not _forms_table(app).display
            assert empty.display
            assert _static_text(empty) == "No Strong · Comparative forms."
            await _press(pilot, "right")
            assert _active_tabs(app) == ["Weak", "Comparative"]
            assert not empty.display
            assert _shown_forms(app).split() == ["Nom", "wkcomp"]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_switch_keys_inert_in_search_input_and_results_list(
    lexicon_source_db: Path,
) -> None:
    _seed_adjective(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testgod")
            before = _shown_forms(app)
            assert "strpos" in before
            app.query_one("#results-list", ListView).focus()
            await pilot.pause()
            for key in _SWITCH_KEYS:
                await _press(pilot, key)
                assert _shown_forms(app) == before
                assert _active_tabs(app) == ["Strong", "Positive"]
            app.focus_search()
            await pilot.pause()
            for key in _SWITCH_KEYS:
                await _press(pilot, key)
                assert _shown_forms(app) == before
                assert _active_tabs(app) == ["Strong", "Positive"]
            assert app.query_one("#search-input", Input).has_focus
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_switch_keys_act_only_when_axis_has_two_values(
    lexicon_source_db: Path,
) -> None:
    _seed_verb(lexicon_source_db, "testhealdan", (("psinsg1", "testhealde"),))
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testhealdan")
            await _focus_entry_column(app, pilot)
            column = app.query_one("#entry-column")
            assert column.check_action("switch", ("primary", 1)) is False
            assert column.check_action("switch", ("secondary", 1)) is False
            await _press(pilot, "right", "right_square_bracket")
            assert _active_tabs(app) == ["Present"]
            assert "testhealde" in _shown_forms(app)
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_reselecting_an_entry_resets_the_selection(lexicon_source_db: Path) -> None:
    _seed_adjective(lexicon_source_db)
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        (("psinsg1", "testhealde"), ("painsg1", "testheold")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testgod")
            await _focus_entry_column(app, pilot)
            await _press(pilot, "right", "right_square_bracket")
            assert _active_tabs(app) == ["Weak", "Comparative"]
            app.focus_search()
            await _open_entry(app, pilot, "testhealdan")
            assert _active_tabs(app) == ["Present"]
            app.focus_search()
            await _open_entry(app, pilot, "testgod")
            assert _active_tabs(app) == ["Strong", "Positive"]
            assert _shown_forms(app).split() == ["Nom", "strpos"]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_forms_table_is_not_a_tab_stop(lexicon_source_db: Path) -> None:
    _seed_verb(
        lexicon_source_db,
        "testhealdan",
        (("psinsg1", "testhealde"), ("painsg1", "testheold")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testhealdan")
            table = _forms_table(app)
            assert table.can_focus is False
            seen = []
            for _ in range(8):
                await pilot.press("tab")
                await pilot.pause()
                seen.append(app.focused)
            assert table not in seen
            assert app.query_one("#entry-column") in seen
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_flat_section_shows_one_wrapped_list_and_no_headers(
    lexicon_source_db: Path,
) -> None:
    forms = tuple(f"testhwa{index:02d}" for index in range(15))
    _insert_entry(lexicon_source_db, headword="testhwa", pos="pronoun", summary_sense="who")
    _seed_forms(
        lexicon_source_db,
        headword="testhwa",
        pos="pronoun",
        forms=tuple(("nope", form) for form in forms),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(60, 40)) as pilot:
            await _open_entry(app, pilot, "testhwa")
            table = _forms_table(app)
            assert table.show_header is False
            assert len(table.ordered_columns) == 1
            assert table.row_count == 1
            assert _table_text(table) == ", ".join(forms)
            assert next(iter(table.rows.values())).height > 1
            painted = "\n".join(_rendered_lines(table))
            assert "Forms" not in painted
            _assert_table_fits_and_paints(table, forms)
            assert _active_tabs(app) == []
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_pronoun_singular_plural_switch(lexicon_source_db: Path) -> None:
    _insert_entry(lexicon_source_db, headword="testhe", pos="pronoun", summary_sense="he")
    _seed_forms(
        lexicon_source_db,
        headword="testhe",
        pos="pronoun",
        forms=(("SgMaNo", "hesg"), ("SgFeNo", "heosg"), ("PlMaNo", "hiepl")),
    )
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _open_entry(app, pilot, "testhe")
            await _focus_entry_column(app, pilot)
            table = _forms_table(app)
            assert _active_tabs(app) == ["Singular"]
            labels = [str(column.label) for column in table.ordered_columns]
            assert labels == ["", "Masc.", "Fem."]
            assert _shown_forms(app).split() == ["Nom", "hesg", "heosg"]
            await _press(pilot, "right")
            table = _forms_table(app)
            assert _active_tabs(app) == ["Plural"]
            labels = [str(column.label) for column in table.ordered_columns]
            assert labels == ["", "Plural"]
            assert _shown_forms(app).split() == ["Nom", "hiepl"]
            await _press(pilot, "left")
            assert _active_tabs(app) == ["Singular"]
            assert _shown_forms(app).split() == ["Nom", "hesg", "heosg"]
    finally:
        app.query_service.close()


# --- Copy key, focus model and results preview (ADR 0028) -------------------


def _insert_copyme(db_path: Path) -> None:
    """Insert ``copyme``, whose definition line is ``time, date``."""
    _insert_entry(db_path, headword="copyme", pos="noun", summary_sense="time; time; date")


def _insert_twins(db_path: Path) -> None:
    """Insert two ``twin`` entries with different glosses, so a search has 2 hits."""
    _insert_entry(db_path, headword="twin", pos="noun", summary_sense="a pair")
    _insert_entry(db_path, headword="twin", pos="verb", summary_sense="to join")


def _search_input(app: DictionaryBrowseApp) -> Input:
    """Return the search input."""
    return app.query_one("#search-input", Input)


def _focused_id(app: DictionaryBrowseApp) -> str | None:
    """Return the id of the focused widget, if any."""
    return None if app.focused is None else app.focused.id


async def _footer_items(app: DictionaryBrowseApp, pilot) -> list[str]:
    """
    Read the rendered footer as ``"<keys> <description>"`` items, sorted.

    A binding group renders as a ``KeyGroup`` of keys followed by a sibling
    ``FooterLabel``; it reads as the joined keys and that label.
    """
    await pilot.pause()
    await pilot.pause()
    footer = app.query_one(Footer)
    items: list[str] = []
    group_keys = ""
    for child in footer.children:
        if isinstance(child, FooterKey):
            items.append(f"{child.key_display} {child.description}")
        elif isinstance(child, KeyGroup):
            group_keys = "".join(key.key_display for key in child.query(FooterKey))
        elif isinstance(child, FooterLabel):
            items.append(f"{group_keys} {child.render()}")
    return sorted(items)


def _row_preview(row: _MainResultItem) -> str:
    """Return the dim definition-line text of one results row."""
    return _static_text(row.query_one(".result-definition", Static))


def _result_rows(app: DictionaryBrowseApp) -> list[_MainResultItem]:
    """Return the results rows in order."""
    main_list = app.query_one("#results-list", ListView)
    return [child for child in main_list.children if isinstance(child, _MainResultItem)]


@pytest.mark.anyio
async def test_c_copies_definition_line_from_results_list(
    lexicon_source_db: Path,
) -> None:
    _insert_copyme(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.press("escape")
            assert _focused_id(app) == "results-list"
            await pilot.press("c")
            await pilot.pause()
            assert app.clipboard == "time, date"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_c_in_search_input_types_the_letter_and_copies_nothing(
    lexicon_source_db: Path,
) -> None:
    _insert_copyme(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            search = _search_input(app)
            search.value = ""
            assert app.check_action("copy_definition", ()) is False
            await pilot.press("c")
            await pilot.pause()
            assert search.value == "c"
            assert search.has_focus
            assert app.clipboard == ""
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_slash_in_search_input_types_a_slash(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.pause()
            assert _search_input(app).value == "/"
            assert _focused_id(app) == "search-input"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_ctrl_c_shows_textual_default_notice(lexicon_source_db: Path) -> None:
    own_bindings = [
        binding for binding in DictionaryBrowseApp.BINDINGS if isinstance(binding, Binding)
    ]
    assert not any(binding.action == "help_quit" for binding in own_bindings)
    assert not any("ctrl+c" in binding.key for binding in own_bindings)
    _insert_copyme(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.press("escape")
            await pilot.press("ctrl+c")
            await pilot.pause()
            assert app.clipboard == ""
            assert any(
                "quit" in notification.message.casefold()
                for notification in app._notifications
            )
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_copy_button_copies_the_same_line(lexicon_source_db: Path) -> None:
    _insert_copyme(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.press("escape", "c")
            await pilot.pause()
            from_key = app.clipboard
            assert from_key == "time, date"
            app.copy_to_clipboard("")
            button = app.query_one("#copy-definition", Button)
            assert button.can_focus is False
            await pilot.click("#copy-definition")
            await pilot.pause()
            assert app.clipboard == from_key
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_copy_disabled_without_definition_line(lexicon_source_db: Path) -> None:
    _insert_entry(lexicon_source_db, headword="emptygloss", pos="noun", summary_sense="")
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "emptygloss")
            await pilot.pause()
            headword = _static_text(app.query_one("#entry-headword", Static))
            assert headword == "emptygloss"
            assert app.query_one("#copy-definition", Button).disabled is True
            await pilot.press("escape")
            assert _focused_id(app) == "results-list"
            assert app.check_action("copy_definition", ()) is False
            assert "c Copy" not in await _footer_items(app, pilot)
            await pilot.press("c")
            await pilot.pause()
            assert app.clipboard == ""
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_ctrl_c_and_super_c_do_not_copy(lexicon_source_db: Path) -> None:
    _insert_copyme(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "copyme")
            await pilot.press("escape")
            for focus_id in ("results-list", "entry-column"):
                app.query_one(f"#{focus_id}").focus()
                await pilot.pause()
                await pilot.press("ctrl+c", "super+c")
                await pilot.pause()
                assert app.clipboard == ""
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_escape_in_search_moves_focus_to_results(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abbad")
            assert _focused_id(app) == "search-input"
            await pilot.press("escape")
            await pilot.pause()
            assert _focused_id(app) == "results-list"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_escape_elsewhere_does_nothing(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abbad")
            await pilot.press("escape")
            await pilot.press("escape")
            await pilot.pause()
            assert _focused_id(app) == "results-list"
            await pilot.press("tab")
            assert _focused_id(app) == "entry-column"
            await pilot.press("escape")
            await pilot.pause()
            assert _focused_id(app) == "entry-column"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_slash_returns_to_search(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abbad")
            for focus_id in ("results-list", "entry-column"):
                app.query_one(f"#{focus_id}").focus()
                await pilot.pause()
                await pilot.press("slash")
                await pilot.pause()
                assert _focused_id(app) == "search-input"
                assert _search_input(app).value == "abbad"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_tab_order_search_results_entry(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abbad")
            seen = [_focused_id(app)]
            for _ in range(3):
                await pilot.press("tab")
                await pilot.pause()
                seen.append(_focused_id(app))
            assert seen == [
                "search-input",
                "results-list",
                "entry-column",
                "search-input",
            ]
            backwards = []
            for _ in range(3):
                await pilot.press("shift+tab")
                await pilot.pause()
                backwards.append(_focused_id(app))
            assert backwards == ["entry-column", "results-list", "search-input"]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_down_in_search_moves_selection_without_leaving_input(
    lexicon_source_db: Path,
) -> None:
    _insert_twins(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "twin")
            await pilot.pause()
            assert len(_result_rows(app)) == 2
            main_list = app.query_one("#results-list", ListView)
            main_list.index = 0
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            assert main_list.index == 1
            assert _focused_id(app) == "search-input"
            assert _search_input(app).value == "twin"
            await pilot.press("up")
            await pilot.pause()
            assert main_list.index == 0
            assert _focused_id(app) == "search-input"
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_results_preview_equals_copied_line(lexicon_source_db: Path) -> None:
    _insert_twins(lexicon_source_db)
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 40)) as pilot:
            await _submit_search(app, pilot, "twin")
            await app.workers.wait_for_complete()
            await pilot.pause()
            rows = _result_rows(app)
            assert len(rows) == 2
            app.query_one("#results-list", ListView).index = 0
            await pilot.press("escape")
            copied = []
            for position, row in enumerate(rows):
                if position:
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("c")
                await pilot.pause()
                assert _row_preview(row)
                assert _row_preview(row) == app.clipboard
                copied.append(app.clipboard)
            assert sorted(copied) == ["a pair", "join"]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_copy_uses_definition_line_cache_order(lexicon_source_db: Path) -> None:
    _insert_two_senses_out_of_path_order(lexicon_source_db, headword="ordered")
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test(size=(140, 40)) as pilot:
            await _submit_search(app, pilot, "ordered")
            await app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.press("escape", "c")
            await pilot.pause()
            assert app.clipboard == "first; second"
            (row,) = _result_rows(app)
            assert _row_preview(row) == app.clipboard
            cache = app.query_service.open_definition_line_cache()
            assert cache.get(row.hit.entry_id) == app.clipboard
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_filled_line_does_not_restore_a_stale_hit(lexicon_source_db: Path) -> None:
    app = create_dictionary_browse_app(lexicon_source_db)
    try:
        async with app.run_test() as pilot:
            await _submit_search(app, pilot, "abbad")
            await app.workers.wait_for_complete()
            await pilot.pause()
            row = _result_rows(app)[0]
            current = dataclass_replace(row.hit, headword="fresh", definition_line=None)
            app._main_hits = [current]
            app._apply_definition_line(row, "filled")
            assert app._main_hits == [dataclass_replace(current, definition_line="filled")]
    finally:
        app.query_service.close()


@pytest.mark.anyio
async def test_footer_lists_only_live_keys(lexicon_source_db: Path) -> None:
    _seed_adjective(lexicon_source_db)
    _seed_verb(lexicon_source_db, "testhealdan", (("psinsg1", "testhealde"),))
    app = create_dictionary_browse_app(lexicon_source_db)
    in_search = ["tab Switch pane", "↑↓ Move"]
    try:
        async with app.run_test(size=(140, 40)) as pilot:
            assert await _footer_items(app, pilot) == in_search
            await _open_entry(app, pilot, "testgod")
            assert _focused_id(app) == "search-input"
            assert await _footer_items(app, pilot) == in_search
            await pilot.press("escape")
            assert await _footer_items(app, pilot) == sorted(
                ["↑↓ Move", "⏎ Open", "/ Search", "tab Switch pane", "c Copy"]
            )
            await pilot.press("tab")
            assert _focused_id(app) == "entry-column"
            assert await _footer_items(app, pilot) == sorted(
                ["←→ Table", "[] Degree", "/ Search", "tab Switch pane", "c Copy"]
            )
            active = app.screen.active_bindings
            assert active["c"].binding.action == "copy_definition"
            assert "escape" not in active
            await pilot.press("slash")
            await _open_entry(app, pilot, "testhealdan")
            await pilot.press("escape", "tab")
            assert _focused_id(app) == "entry-column"
            assert await _footer_items(app, pilot) == sorted(
                ["/ Search", "tab Switch pane", "c Copy"]
            )
    finally:
        app.query_service.close()
