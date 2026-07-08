"""Tests for query-time dictionary browse search and details."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.services.dictionary.browse_query import DictionaryBrowseQueryService
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.markup import normalize_morphology_title, normalize_old_english

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


@pytest.fixture
def lexicon_source_db(tmp_path: Path) -> Path:
    """Dictionary-only canonical DB fixture for browse-query tests."""
    db_path = tmp_path / "browse-query.sqlite3"
    upgrade_canonical_db(db_path)
    sink = BTSqliteSink(db_path, attach_mode=True)
    try:
        BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()
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


def _next_entry_order(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(entry_order), 0) + 1 FROM bt_entries"
        ).fetchone()
    assert row is not None
    return int(row[0])


def _insert_bt_sense(
    connection: sqlite3.Connection,
    *,
    entry_id: int,
    sense_label: str,
    gloss_en: str,
    order_index: int,
    sense_path: str | None = None,
) -> None:
    """Insert one minimal rich ``bt_senses`` row for browse test fixtures."""
    path = sense_path if sense_path is not None else str(order_index + 1)
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
        ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, '', '[]', '[]', '')
        """,
        (
            entry_id,
            sense_label,
            gloss_en,
            order_index,
            path,
            sense_label,
            gloss_en,
        ),
    )


def _insert_entry(  # noqa: PLR0913
    db_path: Path,
    *,
    headword: str,
    pos: str,
    summary_sense: str,
    variants: tuple[str, ...] = (),
    genders: tuple[str, ...] = (),
) -> int:
    """
    Insert one minimal browseable dictionary entry into a temporary test database.

    Args:
        db_path: Target dictionary browse test database path.

    Keyword Args:
        headword: Display headword spelling.
        pos: Canonical ``parts_of_speech.code`` value.
        summary_sense: First gloss inserted into ``bt_senses``.
        variants: Optional display variants for ``bt_variants``.
        genders: Optional entry gender markers.

    Returns:
        Inserted ``bt_entries.id`` value.

    Side Effects:
        Inserts one ``bt_entries`` row plus optional senses and variants.

    """
    norm_key = normalize_old_english(headword)
    assert norm_key is not None
    normalized_title = normalize_morphology_title(headword)
    pos_id = _pos_id(db_path, code=pos)
    entry_order = _next_entry_order(db_path)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
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
            ) VALUES (?, ?, ?, ?, ?, '', '[]', '[]', ?)
            """,
            (
                norm_key,
                headword,
                normalized_title,
                pos_id,
                json.dumps(list(genders)),
                entry_order,
            ),
        )
        assert cursor.lastrowid is not None
        entry_id = int(cursor.lastrowid)
        _insert_bt_sense(
            connection,
            entry_id=entry_id,
            sense_label="",
            gloss_en=summary_sense,
            order_index=0,
        )
        for variant in variants:
            connection.execute(
                """
                INSERT INTO bt_variants (
                    entry_id,
                    spelling_raw,
                    spelling_macronized,
                    normalized_title
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    entry_id,
                    variant,
                    variant,
                    normalize_morphology_title(variant),
                ),
            )
        connection.commit()
    return entry_id


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


def test_search_returns_exact_headword_hit(lexicon_source_db: Path) -> None:
    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("abbad")
    finally:
        service.close()

    assert hits
    hit = hits[0]
    assert hit.headword == "abbad"
    assert hit.pos == "noun"
    assert hit.rank_tier == 1
    assert hit.matched_text == "abbad"
    assert hit.summary_sense == "an abbot; abbot"


def test_search_returns_exact_variant_hit_case_insensitive(
    lexicon_source_db: Path,
) -> None:
    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("ABBOD")
    finally:
        service.close()

    assert hits
    hit = hits[0]
    assert hit.headword == "abbad"
    assert hit.rank_tier == 2
    assert hit.matched_text == "abbod"


def test_search_matches_undiacritized_query_against_macron_headword(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="mōd",
        pos="noun",
        summary_sense="mind; spirit",
    )

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("mod")
    finally:
        service.close()

    assert hits
    assert hits[0].headword == "mōd"
    assert hits[0].rank_tier == 5


def test_search_keeps_best_tier_per_entry(lexicon_source_db: Path) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="mōd",
        pos="noun",
        summary_sense="mind; spirit",
        variants=("mōd",),
    )

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("mōd")
    finally:
        service.close()

    assert len(hits) == 1
    assert hits[0].headword == "mōd"
    assert hits[0].rank_tier == 1
    assert hits[0].matched_text == "mōd"


def test_search_returns_affix_hits_after_exact_matches(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="mōd",
        pos="noun",
        summary_sense="mind; spirit",
    )
    _insert_entry(
        lexicon_source_db,
        headword="acol-mōd",
        pos="adjective",
        summary_sense="fierce-minded",
    )

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("mōd")
    finally:
        service.close()

    assert [hit.headword for hit in hits[:2]] == ["mōd", "acol-mōd"]
    assert [hit.rank_tier for hit in hits[:2]] == [1, 7]


def test_search_orders_exact_headword_before_variant_before_normalized_title(
    lexicon_source_db: Path,
) -> None:
    _insert_entry(
        lexicon_source_db,
        headword="acolmōd",
        pos="noun",
        summary_sense="exact display",
    )
    _insert_entry(
        lexicon_source_db,
        headword="otherword",
        pos="noun",
        summary_sense="variant display",
        variants=("acolmōd",),
    )
    _insert_entry(
        lexicon_source_db,
        headword="acol-mōd",
        pos="adjective",
        summary_sense="normalized title",
    )

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("acolmōd")
    finally:
        service.close()

    assert [hit.headword for hit in hits[:3]] == ["acolmōd", "otherword", "acol-mōd"]
    assert [hit.rank_tier for hit in hits[:3]] == [1, 2, 3]


def test_search_summary_uses_first_ordered_sense(lexicon_source_db: Path) -> None:
    entry_id = _insert_entry(
        lexicon_source_db,
        headword="twisens",
        pos="noun",
        summary_sense="later gloss",
    )
    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute("DELETE FROM bt_senses WHERE entry_id = ?", (entry_id,))
        _insert_bt_sense(
            connection,
            entry_id=entry_id,
            sense_label="II",
            gloss_en="later gloss",
            order_index=1,
            sense_path="2",
        )
        _insert_bt_sense(
            connection,
            entry_id=entry_id,
            sense_label="I",
            gloss_en="first gloss",
            order_index=0,
            sense_path="1",
        )
        connection.commit()

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        hits = service.search("twisens")
    finally:
        service.close()

    assert hits
    assert hits[0].summary_sense == "first gloss"


def test_get_details_returns_entry_payload_with_grouped_morphology(
    lexicon_source_db: Path,
) -> None:
    entry_id = _bt_entry_id(lexicon_source_db, norm_key="abbad")
    noun_pos_id = _pos_id(lexicon_source_db, code="noun")
    with sqlite3.connect(lexicon_source_db) as connection:
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
                0, 'abbadu', 'abbad', 'abbad', 'abbad', 'abbad', 'abbadu',
                '0-abbad-0', '0', '0', '',
                'abbad', 'abbad', 'abbad', 'abbadu', 'abbadu',
                ?, ?, ?
            )
            """,
            (entry_id, noun_pos_id, nominative_code_id),
        )
        connection.commit()

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        details = service.get_details(entry_id)
    finally:
        service.close()

    assert details is not None
    assert details.entry_id == entry_id
    assert details.headword == "abbad"
    assert details.pos == "noun"
    assert details.variants == ["abbod", "abbot", "abbud"]
    assert details.summary_sense == "an abbot; abbot"
    assert [sense.gloss_en for sense in details.senses] == [
        "an abbot; abbot",
        "bishops were sometimes subject to an abbot, as they were to the abbots of Iona",
    ]
    assert [sense.sense_label for sense in details.senses] == ["1", "2"]
    assert details.class_summary == []
    assert details.genders == ["m"]
    assert details.persons == []
    assert details.numbers == ["singular", "plural"]
    groups_by_function = {
        group.function: group for group in details.morphology_groups
    }
    assert len(groups_by_function) == 2
    assert groups_by_function["genitive singular"].wordclass == "noun"
    assert groups_by_function["nominative plural"].function == "nominative plural"


def test_get_details_sorts_senses_by_hierarchical_path_not_order_index(
    lexicon_source_db: Path,
) -> None:
    entry_id = _insert_entry(
        lexicon_source_db,
        headword="dóm",
        pos="noun",
        summary_sense="doom, judgment",
    )
    with sqlite3.connect(lexicon_source_db) as connection:
        for order_index, sense_label, gloss_en, sense_path in (
            (1, "II", "a ruling", "2"),
            (2, "III", "might, power", "3"),
            (3, "IV", "will, free will", "4"),
            (4, "V", "sense, meaning", "5"),
            (5, "VI", "judgement", "6"),
            (6, "VII", "direction", "7"),
            (7, "VIII", "will, discretion", "8"),
            (8, "IV a", "an authority, a court", "4.1"),
            (9, "IX", "reputation", "9"),
        ):
            _insert_bt_sense(
                connection,
                entry_id=entry_id,
                sense_label=sense_label,
                gloss_en=gloss_en,
                order_index=order_index,
                sense_path=sense_path,
            )
        connection.commit()

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        details = service.get_details(entry_id)
    finally:
        service.close()

    assert details is not None
    sense_labels = [sense.sense_label for sense in details.senses]
    four_index = sense_labels.index("4")
    assert sense_labels[four_index + 1] == "4a"
    assert sense_labels[four_index + 2] == "5"
    assert sense_labels.index("8") > sense_labels.index("4a")
