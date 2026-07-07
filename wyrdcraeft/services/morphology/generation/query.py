"""SQLAlchemy-backed morphology query service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTPos
from wyrdcraeft.models.morphology import MorphClassQueryMetadata, QueryFormRow
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.query import BTQueryService
from wyrdcraeft.services.markup import normalize_morphology_title
from wyrdcraeft.services.morphology.catalog.query import (
    MorphClassView,
    format_morph_class_display_label,
)

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from sqlalchemy.engine import Connection, Engine, RowMapping

#: Morphology ``wordclass`` values mapped to Bosworth-Toller ``bt_entries.pos``.
#: Unmapped classes (for example ``participle``) are treated as ambiguous and do
#: not narrow the dictionary join.
_WORDCLASS_TO_BT_POS: dict[str, str] = {
    "noun": BTPos.NOUN.value,
    "verb": BTPos.VERB.value,
    "adjective": BTPos.ADJ.value,
    "adverb": BTPos.ADV.value,
    "numeral": BTPos.NUMERAL.value,
    "pronoun": BTPos.PRON.value,
    "preposition": BTPos.PREP.value,
    "conjunction": BTPos.CONJ.value,
    "interjection": BTPos.INTERJ.value,
    "indeclinable": BTPos.INDECL.value,
}


def _normalize_key(value: str) -> str:
    """
    Normalize a lookup token for deterministic morphology queries.

    Args:
        value: Raw lookup token.

    Returns:
        Canonicalized lookup key.

    """
    return OENormalizer.normalize_output(value).casefold()


#: Legacy string columns dropped from ``forms`` in Phase D that have no direct
#: FK replacement value. Query rows emit empty strings for these fields;
#: ``wordclass``/``function`` are read from FK joins instead.
_DROPPED_LEGACY_FIELDS_SQL = """
        '' AS wright,
        '' AS paradigm,
        '' AS paraID,
        '' AS class1,
        '' AS class2,
        '' AS class3,"""
#: Lemma lookup SQL without catalog joins.
_FORM_LOOKUP_LEMMA_SQL = (
    """
    SELECT
        f.counter,
        f.formi,
        f.BT,
        f.title,
        f.normalized_title,
        f.stem,
        f.form,
        f.formParts,
        f.var,
        f.probability,
        COALESCE(ic.code, '') AS function,"""
    + _DROPPED_LEGACY_FIELDS_SQL
    + """
        COALESCE(fpos.code, '') AS wordclass,
        f.comment,
        COALESCE(f.bt_key, '') || '|'
            || COALESCE(f.title_key, '') || '|'
            || COALESCE(f.stem_key, '') AS lemma_key,
        f.form_key
    FROM forms f
    LEFT JOIN parts_of_speech fpos ON fpos.id = f.wordclass_id
    LEFT JOIN inflection_codes ic ON ic.id = f.inflection_code_id
    WHERE
        f.bt_key = :lemma_key
        OR f.title_key = :lemma_key
        OR f.stem_key = :lemma_key
    ORDER BY f.counter ASC, f.id ASC
    LIMIT :limit
"""
)
#: Surface-form lookup SQL without catalog joins.
_FORM_LOOKUP_FORM_SQL = (
    """
    SELECT
        f.counter,
        f.formi,
        f.BT,
        f.title,
        f.normalized_title,
        f.stem,
        f.form,
        f.formParts,
        f.var,
        f.probability,
        COALESCE(ic.code, '') AS function,"""
    + _DROPPED_LEGACY_FIELDS_SQL
    + """
        COALESCE(fpos.code, '') AS wordclass,
        f.comment,
        COALESCE(f.bt_key, '') || '|'
            || COALESCE(f.title_key, '') || '|'
            || COALESCE(f.stem_key, '') AS lemma_key,
        f.form_key
    FROM forms f
    LEFT JOIN parts_of_speech fpos ON fpos.id = f.wordclass_id
    LEFT JOIN inflection_codes ic ON ic.id = f.inflection_code_id
    WHERE f.form_key = :form_key OR f.formi_key = :form_key
    ORDER BY f.counter ASC, f.id ASC
    LIMIT :limit
"""
)
#: Lemma lookup SQL with catalog joins for FK-backed morph-class metadata.
_FORM_LOOKUP_LEMMA_CATALOG_SQL = (
    """
    SELECT
        f.counter,
        f.formi,
        f.BT,
        f.title,
        f.normalized_title,
        f.stem,
        f.form,
        f.formParts,
        f.var,
        f.probability,
        COALESCE(ic.code, '') AS function,"""
    + _DROPPED_LEGACY_FIELDS_SQL
    + """
        COALESCE(fpos.code, '') AS wordclass,
        f.comment,
        COALESCE(f.bt_key, '') || '|'
            || COALESCE(f.title_key, '') || '|'
            || COALESCE(f.stem_key, '') AS lemma_key,
        f.form_key,
        f.morph_class_id,
        mc.class_key AS morph_class_class_key,
        mcpos.code AS morph_class_pos,
        mc.canonical_name AS morph_class_canonical_name,
        mc.modern_class AS morph_class_modern_class,
        mc.wright_label AS morph_class_wright_label,
        mcws.wright_sections AS morph_class_wright_sections
    FROM forms f
    LEFT JOIN parts_of_speech fpos ON fpos.id = f.wordclass_id
    LEFT JOIN inflection_codes ic ON ic.id = f.inflection_code_id
    LEFT JOIN morph_classes mc ON mc.id = f.morph_class_id
    LEFT JOIN parts_of_speech mcpos ON mcpos.id = mc.pos_id
    LEFT JOIN (
        SELECT
            morph_class_id,
            GROUP_CONCAT(section_no ORDER BY sort_order, section_no) AS wright_sections
        FROM morph_class_wright_sections
        GROUP BY morph_class_id
    ) mcws ON mcws.morph_class_id = f.morph_class_id
    WHERE
        f.bt_key = :lemma_key
        OR f.title_key = :lemma_key
        OR f.stem_key = :lemma_key
    ORDER BY f.counter ASC, f.id ASC
    LIMIT :limit
"""
)
#: Surface-form lookup SQL with catalog joins for FK-backed morph-class metadata.
_FORM_LOOKUP_FORM_CATALOG_SQL = (
    """
    SELECT
        f.counter,
        f.formi,
        f.BT,
        f.title,
        f.normalized_title,
        f.stem,
        f.form,
        f.formParts,
        f.var,
        f.probability,
        COALESCE(ic.code, '') AS function,"""
    + _DROPPED_LEGACY_FIELDS_SQL
    + """
        COALESCE(fpos.code, '') AS wordclass,
        f.comment,
        COALESCE(f.bt_key, '') || '|'
            || COALESCE(f.title_key, '') || '|'
            || COALESCE(f.stem_key, '') AS lemma_key,
        f.form_key,
        f.morph_class_id,
        mc.class_key AS morph_class_class_key,
        mcpos.code AS morph_class_pos,
        mc.canonical_name AS morph_class_canonical_name,
        mc.modern_class AS morph_class_modern_class,
        mc.wright_label AS morph_class_wright_label,
        mcws.wright_sections AS morph_class_wright_sections
    FROM forms f
    LEFT JOIN parts_of_speech fpos ON fpos.id = f.wordclass_id
    LEFT JOIN inflection_codes ic ON ic.id = f.inflection_code_id
    LEFT JOIN morph_classes mc ON mc.id = f.morph_class_id
    LEFT JOIN parts_of_speech mcpos ON mcpos.id = mc.pos_id
    LEFT JOIN (
        SELECT
            morph_class_id,
            GROUP_CONCAT(section_no ORDER BY sort_order, section_no) AS wright_sections
        FROM morph_class_wright_sections
        GROUP BY morph_class_id
    ) mcws ON mcws.morph_class_id = f.morph_class_id
    WHERE f.form_key = :form_key OR f.formi_key = :form_key
    ORDER BY f.counter ASC, f.id ASC
    LIMIT :limit
"""
)


def _lemma_lookup_sql(*, include_catalog_join: bool) -> str:
    """
    Return lemma lookup SQL with optional catalog joins.

    Keyword Args:
        include_catalog_join: Whether to append catalog FK joins and metadata.

    Returns:
        Parameterized lookup SQL for ``lookup_by_lemma``.

    """
    if include_catalog_join:
        return _FORM_LOOKUP_LEMMA_CATALOG_SQL
    return _FORM_LOOKUP_LEMMA_SQL


def _form_lookup_sql(*, include_catalog_join: bool) -> str:
    """
    Return surface-form lookup SQL with optional catalog joins.

    Keyword Args:
        include_catalog_join: Whether to append catalog FK joins and metadata.

    Returns:
        Parameterized lookup SQL for ``lookup_by_form``.

    """
    if include_catalog_join:
        return _FORM_LOOKUP_FORM_CATALOG_SQL
    return _FORM_LOOKUP_FORM_SQL


def _parse_wright_sections(raw_value: object) -> tuple[int, ...]:
    """
    Parse a comma-separated Wright section list from SQL aggregation.

    Args:
        raw_value: ``GROUP_CONCAT`` payload from catalog joins.

    Returns:
        Sorted Wright section numbers, or an empty tuple when absent.

    """
    if raw_value is None:
        return ()
    text_value = str(raw_value).strip()
    if not text_value:
        return ()
    return tuple(
        sorted(
            {
                int(section_no)
                for section_no in text_value.split(",")
                if section_no.strip()
            }
        )
    )


def _build_morph_class_metadata(
    payload: dict[str, object],
) -> MorphClassQueryMetadata | None:
    """
    Build FK-backed morph-class metadata from joined catalog columns.

    Args:
        payload: Mutable lookup row payload with optional catalog join fields.

    Returns:
        Joined morph-class metadata, or ``None`` when no assignment is linked.

    """
    class_key = payload.pop("morph_class_class_key", None)
    if class_key is None:
        payload.pop("morph_class_pos", None)
        payload.pop("morph_class_canonical_name", None)
        payload.pop("morph_class_modern_class", None)
        payload.pop("morph_class_wright_label", None)
        payload.pop("morph_class_wright_sections", None)
        return None

    pos = str(payload.pop("morph_class_pos", ""))
    canonical_name = str(payload.pop("morph_class_canonical_name", ""))
    modern_class = str(payload.pop("morph_class_modern_class", ""))
    wright_label = str(payload.pop("morph_class_wright_label", ""))
    wright_sections = _parse_wright_sections(
        payload.pop("morph_class_wright_sections", None),
    )
    display_label = format_morph_class_display_label(
        MorphClassView(
            class_key=str(class_key),
            pos=pos,
            canonical_name=canonical_name,
            modern_class=modern_class,
            assignment_source="",
            wright_label=wright_label,
            wright_sections=wright_sections,
            sources=(),
        ),
    )
    return MorphClassQueryMetadata(
        class_key=str(class_key),
        pos=pos,
        canonical_name=canonical_name,
        modern_class=modern_class,
        wright_label=wright_label,
        display_label=display_label,
        wright_sections=wright_sections,
    )


def _project_query_rows(rows: Sequence[RowMapping]) -> list[QueryFormRow]:
    """
    Convert raw SQLAlchemy row mappings into typed morphology query rows.

    Args:
        rows: Raw row mappings returned from lookup queries.

    Returns:
        Validated query rows with counter values projected as strings.

    """
    projected: list[QueryFormRow] = []
    for row in rows:
        payload = dict(row)
        payload["counter"] = str(payload["counter"])
        morph_class_id = payload.pop("morph_class_id", None)
        morph_class = _build_morph_class_metadata(payload)
        projected.append(
            QueryFormRow.model_validate(
                {
                    **payload,
                    "morph_class_id": morph_class_id,
                    "morph_class": morph_class,
                },
            ),
        )
    return projected


def _db_has_table(connection: Connection, table_name: str) -> bool:
    """
    Return whether one SQLite table exists in the active database.

    Args:
        connection: Active SQLAlchemy connection.
        table_name: Table name to inspect.

    Returns:
        ``True`` when the named table is present.

    """
    row = connection.execute(
        text(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = :table_name
            LIMIT 1
            """
        ),
        {"table_name": table_name},
    ).first()
    return row is not None


def _forms_has_morph_class_id(connection: Connection) -> bool:
    """
    Return whether the ``forms`` table exposes ``morph_class_id``.

    Args:
        connection: Active SQLAlchemy connection.

    Returns:
        ``True`` when the FK column exists on ``forms``.

    """
    row = connection.execute(
        text(
            """
            SELECT 1
            FROM pragma_table_info('forms')
            WHERE name = 'morph_class_id'
            LIMIT 1
            """
        ),
    ).first()
    return row is not None


def resolve_dictionary_db_path(
    morphology_db_path: Path,
    dictionary_db_path: Path | None = None,
) -> Path | None:
    """
    Resolve the Bosworth-Toller dictionary SQLite path for morphology joins.

    Resolution order:

    1. Explicit ``dictionary_db_path`` when provided.
    2. Sibling ``dictionary.sqlite3`` in the morphology database directory.
    3. The morphology database itself when it contains ``bt_entries`` (attach mode).

    Args:
        morphology_db_path: Path to the morphology SQLite index.
        dictionary_db_path: Optional explicit dictionary database override.

    Returns:
        Resolved dictionary database path, or ``None`` when no join target exists.

    """
    if dictionary_db_path is not None:
        resolved = dictionary_db_path.expanduser().resolve()
        return resolved if resolved.is_file() else None

    sibling = morphology_db_path.parent / DICTIONARY_INDEX_FILENAME
    if sibling.is_file():
        return sibling.resolve()

    if _morphology_db_has_bt_entries(morphology_db_path):
        return morphology_db_path.resolve()

    return None


def _morphology_db_has_bt_entries(db_path: Path) -> bool:
    """
    Return whether a SQLite file contains Bosworth-Toller ``bt_entries`` rows.

    Args:
        db_path: SQLite database path to inspect.

    Returns:
        ``True`` when ``bt_entries`` exists in the schema.

    """
    engine = create_sqlalchemy_engine(db_path)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM sqlite_master
                    WHERE type = 'table' AND name = 'bt_entries'
                    LIMIT 1
                    """
                )
            ).first()
    finally:
        engine.dispose()
    return row is not None


def _infer_bt_pos_filter(form_rows: list[QueryFormRow]) -> str | None:
    """
    Infer an optional BT POS filter from morphology ``wordclass`` values.

    When every returned row maps to the same BT POS, that POS is returned.
    When mapping is mixed or any row uses an unmapped class, ``None`` is
    returned so all homographs for the normalized key are included.

    Args:
        form_rows: Morphology rows returned for the lookup.

    Returns:
        Stored ``bt_entries.pos`` value, or ``None`` when ambiguous.

    """
    mapped_pos: set[str] = set()
    for row in form_rows:
        bt_pos = _WORDCLASS_TO_BT_POS.get(row.wordclass.strip().lower())
        if bt_pos is None:
            return None
        mapped_pos.add(bt_pos)
    if len(mapped_pos) == 1:
        return next(iter(mapped_pos))
    return None


def _lookup_normalized_title(
    form_rows: list[QueryFormRow],
    lookup_token: str,
) -> str:
    """
    Resolve the macron-preserving title key used for dictionary joins.

    Args:
        form_rows: Morphology rows already returned for the lookup.
        lookup_token: Lemma or headword token used for the morphology lookup.

    Returns:
        ``normalized_title`` from the first emitted row, or a normalized fallback
        derived from ``lookup_token``.

    """
    for row in form_rows:
        title_key = row.normalized_title.strip()
        if title_key:
            return title_key
    return normalize_morphology_title(lookup_token)


def dictionary_join_entry_to_dict(entry: BTConsolidatedEntry) -> dict[str, object]:
    """
    Serialize one dictionary entry for morphology join JSON output.

    Args:
        entry: Consolidated Bosworth-Toller dictionary record.

    Returns:
        JSON-serializable mapping with headword, POS, genders, senses, and
        etymology fields.

    """
    return {
        "headword": entry.headword_macronized,
        "pos": entry.pos.value,
        "genders": [gender.value for gender in entry.genders],
        "senses": [
            {"sense_label": sense.sense_label, "gloss_en": sense.gloss_en}
            for sense in entry.senses
        ],
        "etymology": entry.etymology,
    }


class MorphologyQueryService:
    """
    Query interface over emitted morphology rows persisted in SQLite.

    Args:
        db_path: Path to SQLite database file produced by generation.

    """

    #: Path to the morphology SQLite index file.
    _db_path: Path
    #: SQLAlchemy engine bound to the morphology database.
    _engine: Engine
    #: Active SQLAlchemy connection for morphology lookups.
    _connection: Connection
    #: Whether catalog tables support FK-backed morph-class joins.
    _catalog_join_available: bool

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a SQLAlchemy query service for a generated morphology index.

        Note:
            Query semantics follow normalization expectations documented in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this opens one index used across all Parts of Speech.

        Args:
            db_path: Path to SQLite database file produced by generation.

        """
        #: Path to the morphology SQLite index file.
        self._db_path = db_path.expanduser().resolve()
        #: SQLAlchemy engine bound to the morphology database.
        self._engine = create_sqlalchemy_engine(self._db_path)
        #: Active SQLAlchemy connection for morphology lookups.
        self._connection = self._engine.connect()
        #: Whether catalog tables support FK-backed morph-class joins.
        self._catalog_join_available = (
            _db_has_table(self._connection, "morph_classes")
            and _forms_has_morph_class_id(self._connection)
        )

    def lookup_by_lemma(self, lemma: str, limit: int = 200) -> list[QueryFormRow]:
        """
        Look up emitted rows by normalized lemma/root token.

        Note:
            Lemma matching aligns with headword conventions in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this finds inflected rows for any Part of Speech
            sharing the same base lexeme.

        Args:
            lemma: Lemma/root token matching BT, title, or stem keys.
            limit: Maximum result count.

        Returns:
            Ordered query rows matching the lemma key.

        """
        lemma_key = _normalize_key(lemma)
        rows = self._connection.execute(
            text(_lemma_lookup_sql(include_catalog_join=self._catalog_join_available)),
            {"lemma_key": lemma_key, "limit": max(1, limit)},
        ).mappings().all()
        return _project_query_rows(rows)

    def lookup_by_form(self, form: str, limit: int = 200) -> list[QueryFormRow]:
        """
        Look up emitted rows by normalized surface form token.

        Note:
            Surface-form matching aligns with orthographic conventions in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this finds rows by written form across Parts of Speech.

        Args:
            form: Surface form token matching emitted ``form`` or ``formi`` keys.
            limit: Maximum result count.

        Returns:
            Ordered query rows matching the form key.

        """
        form_key = _normalize_key(form)
        rows = self._connection.execute(
            text(_form_lookup_sql(include_catalog_join=self._catalog_join_available)),
            {"form_key": form_key, "limit": max(1, limit)},
        ).mappings().all()
        return _project_query_rows(rows)

    def lookup_dictionary_entries(
        self,
        lookup_token: str,
        form_rows: list[QueryFormRow],
        *,
        dictionary_db_path: Path | None = None,
    ) -> list[dict[str, object]]:
        """
        Look up Bosworth-Toller entries to join with morphology query results.

        Note:
            Dictionary joins use macron-preserving ``normalized_title`` keys
            aligned with lexicon build semantics in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this attaches dictionary senses across Parts of Speech
            when the morphology wordclass mapping is unambiguous.

        Args:
            lookup_token: Lemma or headword token used for the morphology lookup.
            form_rows: Morphology rows already returned for the query.

        Keyword Args:
            dictionary_db_path: Optional explicit dictionary SQLite path override.

        Returns:
            Dictionary entry payloads for JSON join output; empty when no index
            is available or no entries match.

        """
        resolved_dictionary_db = resolve_dictionary_db_path(
            self._db_path,
            dictionary_db_path,
        )
        if resolved_dictionary_db is None:
            return []

        normalized_title = _lookup_normalized_title(form_rows, lookup_token)
        if not normalized_title:
            return []

        pos_filter = _infer_bt_pos_filter(form_rows)
        dictionary_service = BTQueryService(resolved_dictionary_db)
        try:
            entries = dictionary_service.lookup_by_normalized_title(
                normalized_title,
                pos=pos_filter,
            )
        finally:
            dictionary_service.close()

        return [dictionary_join_entry_to_dict(entry) for entry in entries]

    def close(self) -> None:
        """
        Close the SQLAlchemy connection and dispose the engine.

        Note:
            Closing is shared infrastructure for all Part-of-Speech queries
            generated from ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf`` aligned outputs.

        """
        self._connection.close()
        self._engine.dispose()
