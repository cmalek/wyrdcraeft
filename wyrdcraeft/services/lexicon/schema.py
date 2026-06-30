"""SQLite schema for the lexicon browse read-model tables."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

#: Lexicon dictionary-entry table storing one row per real Bosworth-Toller entry.
TABLE_LEXICON_ENTRIES: Final = "lexicon_entries"
#: Lexicon morphology projection table; rows may exist without a dictionary entry.
TABLE_LEXICON_FORMS: Final = "lexicon_forms"
#: Lexicon normalized search keys used for unified lookup and ranking.
TABLE_LEXICON_SEARCH_KEYS: Final = "lexicon_search_keys"
#: Lexicon build metadata key/value store.
TABLE_LEXICON_BUILD_META: Final = "lexicon_build_meta"

#: Ordered lexicon table names managed by rebuild workflows.
LEXICON_TABLE_NAMES: Final = (
    TABLE_LEXICON_ENTRIES,
    TABLE_LEXICON_FORMS,
    TABLE_LEXICON_SEARCH_KEYS,
    TABLE_LEXICON_BUILD_META,
)

#: Current lexicon read-model schema version written to ``lexicon_build_meta``.
SCHEMA_VERSION: Final = 1

#: Metadata key storing the active lexicon schema version.
META_KEY_SCHEMA_VERSION: Final = "schema_version"
#: Metadata key storing the ISO-8601 UTC timestamp of the last rebuild.
META_KEY_BUILT_AT: Final = "built_at"
#: Metadata key storing the source ``forms`` row count at rebuild time.
META_KEY_FORMS_SOURCE_COUNT: Final = "forms_source_count"
#: Metadata key storing the source ``bt_entries`` row count at rebuild time.
META_KEY_BT_ENTRIES_SOURCE_COUNT: Final = "bt_entries_source_count"

#: Search-key kind for dictionary headword matches.
KEY_KIND_LEMMA: Final = "lemma"
#: Search-key kind for dictionary variant spelling matches.
KEY_KIND_VARIANT: Final = "variant"
#: Search-key kind for morphology lemma/stem matches.
KEY_KIND_STEM: Final = "stem"
#: Search-key kind for inflected morphology form matches.
KEY_KIND_FORM: Final = "form"

#: Highest-priority rank tier for exact dictionary lemma or variant hits.
RANK_TIER_EXACT_ENTRY: Final = 1
#: Rank tier for morphology lemma or stem hits joined to a dictionary entry.
RANK_TIER_MORPH_LEMMA_STEM: Final = 2
#: Rank tier for morphology form hits joined to a dictionary entry.
RANK_TIER_MORPH_FORM: Final = 3
#: Rank tier for morphology-only hits with no dictionary entry join.
RANK_TIER_ORPHAN: Final = 4

#: DDL script creating all ``lexicon_*`` tables and lookup indexes.
LEXICON_SCHEMA_DDL: Final = """
CREATE TABLE IF NOT EXISTS lexicon_entries (
    entry_id INTEGER PRIMARY KEY,
    norm_key TEXT NOT NULL,
    pos TEXT NOT NULL,
    headword TEXT NOT NULL,
    summary_sense TEXT NOT NULL,
    etymology TEXT NOT NULL,
    variants_json TEXT NOT NULL,
    genders_json TEXT NOT NULL,
    senses_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lexicon_forms (
    form_id INTEGER PRIMARY KEY,
    entry_id INTEGER REFERENCES lexicon_entries(entry_id),
    bt TEXT NOT NULL,
    title TEXT NOT NULL,
    stem TEXT NOT NULL,
    form TEXT NOT NULL,
    formi TEXT NOT NULL,
    wordclass TEXT NOT NULL,
    function TEXT NOT NULL,
    probability TEXT NOT NULL,
    class1 TEXT NOT NULL,
    class2 TEXT NOT NULL,
    class3 TEXT NOT NULL,
    paradigm TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS lexicon_search_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_text TEXT NOT NULL,
    key_kind TEXT NOT NULL,
    rank_tier INTEGER NOT NULL,
    entry_id INTEGER REFERENCES lexicon_entries(entry_id),
    form_id INTEGER REFERENCES lexicon_forms(form_id),
    display_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lexicon_build_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lexicon_entries_norm_pos
    ON lexicon_entries(norm_key, pos);
CREATE INDEX IF NOT EXISTS idx_lexicon_forms_entry_id
    ON lexicon_forms(entry_id);
CREATE INDEX IF NOT EXISTS idx_lexicon_search_keys_key_text
    ON lexicon_search_keys(key_text);
CREATE INDEX IF NOT EXISTS idx_lexicon_search_keys_entry_id
    ON lexicon_search_keys(entry_id);
CREATE INDEX IF NOT EXISTS idx_lexicon_search_keys_form_id
    ON lexicon_search_keys(form_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lexicon_search_keys_dedupe
    ON lexicon_search_keys(
        TRIM(key_text),
        key_kind,
        rank_tier,
        COALESCE(entry_id, -1),
        COALESCE(form_id, -1),
        TRIM(display_text)
    );
"""


def migrate_lexicon_schema(connection: sqlite3.Connection) -> None:
    """
    Add missing columns to existing lexicon tables without committing.

    Args:
        connection: Open SQLite connection containing ``lexicon_*`` tables.

    Side Effects:
        Executes additive ``ALTER TABLE`` statements when legacy columns are absent.

    """
    columns = connection.execute("PRAGMA table_info(lexicon_forms)").fetchall()
    column_names = {str(row[1]) for row in columns}
    if not column_names:
        return
    if "paradigm" not in column_names:
        connection.execute(
            "ALTER TABLE lexicon_forms ADD COLUMN paradigm TEXT NOT NULL DEFAULT ''"
        )


def apply_lexicon_schema(connection: sqlite3.Connection) -> None:
    """
    Apply lexicon DDL and additive column migrations without committing.

    Args:
        connection: Open SQLite connection receiving the ``lexicon_*`` schema.

    Side Effects:
        Executes ``LEXICON_SCHEMA_DDL`` and adds missing ``lexicon_forms`` columns.

    """
    connection.executescript(LEXICON_SCHEMA_DDL)
    migrate_lexicon_schema(connection)


def create_lexicon_tables(connection: sqlite3.Connection) -> None:
    """
    Create lexicon read-model tables and indexes when missing.

    Args:
        connection: Open SQLite connection receiving the ``lexicon_*`` schema.

    Side Effects:
        Executes ``apply_lexicon_schema`` and commits the connection.

    """
    apply_lexicon_schema(connection)
    connection.commit()
