"""SQLAlchemy-backed morphology query service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTPos
from wyrdcraeft.models.morphology import QueryFormRow
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.query import BTQueryService
from wyrdcraeft.services.markup import normalize_morphology_title

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
        projected.append(QueryFormRow.model_validate(payload))
    return projected


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
            text(
                """
                SELECT
                    counter,
                    formi,
                    BT,
                    title,
                    normalized_title,
                    stem,
                    form,
                    formParts,
                    var,
                    probability,
                    function,
                    wright,
                    paradigm,
                    paraID,
                    wordclass,
                    class1,
                    class2,
                    class3,
                    comment,
                    COALESCE(bt_key, '') || '|'
                        || COALESCE(title_key, '') || '|'
                        || COALESCE(stem_key, '') AS lemma_key,
                    form_key
                FROM forms
                WHERE bt_key = :lemma_key
                    OR title_key = :lemma_key
                    OR stem_key = :lemma_key
                ORDER BY counter ASC, id ASC
                LIMIT :limit
                """
            ),
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
            text(
                """
                SELECT
                    counter,
                    formi,
                    BT,
                    title,
                    normalized_title,
                    stem,
                    form,
                    formParts,
                    var,
                    probability,
                    function,
                    wright,
                    paradigm,
                    paraID,
                    wordclass,
                    class1,
                    class2,
                    class3,
                    comment,
                    COALESCE(bt_key, '') || '|'
                        || COALESCE(title_key, '') || '|'
                        || COALESCE(stem_key, '') AS lemma_key,
                    form_key
                FROM forms
                WHERE form_key = :form_key OR formi_key = :form_key
                ORDER BY counter ASC, id ASC
                LIMIT :limit
                """
            ),
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
