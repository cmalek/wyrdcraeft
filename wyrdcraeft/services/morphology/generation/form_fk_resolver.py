"""Resolve morphology form rows to normalized-schema foreign keys."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)
from wyrdcraeft.services.dictionary.query import _bt_pos_from_code
from wyrdcraeft.services.markup import normalize_morphology_title
from wyrdcraeft.services.morphology.catalog.pos import (
    _WORDCLASS_TO_POS_CODE,
    catalog_pos_from_wordclass,
    pos_id_from_wordclass,
)
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)

from .query import _WORDCLASS_TO_BT_POS

if TYPE_CHECKING:
    import sqlite3

#: Verbal participle morphology function codes that inherit verb lemma classes.
_VERB_PARTICIPLE_FUNCTIONS: Final[frozenset[str]] = frozenset({"PsPt", "PaPt"})


def _load_morph_class_ids(connection: sqlite3.Connection) -> dict[tuple[str, int], int]:
    """
    Load lemma morph-class assignments keyed by normalized title and POS id.

    Args:
        connection: Open canonical SQLite connection.

    Returns:
        Mapping from ``(normalized_title, pos_id)`` to ``morph_class_id``.

    """
    rows = connection.execute(
        """
        SELECT normalized_title, pos_id, morph_class_id
        FROM lemma_morph_classes
        """,
    ).fetchall()
    return {
        (str(normalized_title), int(pos_id)): int(morph_class_id)
        for normalized_title, pos_id, morph_class_id in rows
    }


def _load_join_index(connection: sqlite3.Connection) -> NormalizedTitleJoinIndex:
    """
    Build a dictionary join index from canonical ``bt_entries`` and variants.

    Args:
        connection: Open canonical SQLite connection.

    Returns:
        Preloaded join index using Bosworth-Toller POS labels.

    """
    entry_rows = connection.execute(
        """
        SELECT bt_entries.id, bt_entries.normalized_title, parts_of_speech.code
        FROM bt_entries
        JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
        """,
    ).fetchall()
    variant_rows = connection.execute(
        """
        SELECT bt_variants.entry_id, bt_variants.normalized_title, parts_of_speech.code
        FROM bt_variants
        JOIN bt_entries ON bt_entries.id = bt_variants.entry_id
        JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
        WHERE trim(coalesce(bt_variants.normalized_title, '')) != ''
        """,
    ).fetchall()

    def _bt_pos_label(code: str) -> str:
        return _bt_pos_from_code(code).value

    return NormalizedTitleJoinIndex.from_entry_variant_rows(
        [
            (int(entry_id), str(normalized_title), _bt_pos_label(str(pos_code)))
            for entry_id, normalized_title, pos_code in entry_rows
        ],
        [
            (int(entry_id), str(normalized_title), _bt_pos_label(str(pos_code)))
            for entry_id, normalized_title, pos_code in variant_rows
        ],
    )


class FormFkResolver:
    """
    Resolve generated morphology form metadata to normalized-schema FK ids.

    Note:
        Lookup follows Wright's inflection taxonomy in
        ``data/OldEnglishGrammar.pdf`` and generator output conventions in
        ``data/Ondej_Tich_40-54-1.pdf``. Verbal participles keep the parent
        verb's lemma morph-class assignment, while other inflected forms use
        catalog POS vocabulary from ``catalog_pos_from_wordclass``. Dictionary
        ``entry_id`` resolution reuses ``NormalizedTitleJoinIndex.resolve_one``
        and returns ``None`` when the join policy is ambiguous. Part-of-speech
        scope: ``cross-PoS``.

    Args:
        connection: Optional canonical SQLite connection used to preload lookup
            maps when explicit maps are omitted.
        join_index: Optional preloaded normalized-title dictionary join index.
        inflection_code_ids: Optional ``inflection_codes.code`` to id map.
        morph_class_ids: Optional ``(normalized_title, pos_id)`` to
            ``morph_class_id`` map.
        pos_ids_by_code: Optional canonical ``parts_of_speech.code`` to id map.

    """

    #: Optional canonical SQLite connection for on-demand POS resolution.
    _connection: sqlite3.Connection | None
    #: Dictionary join index for ``entry_id`` resolution.
    _join_index: NormalizedTitleJoinIndex
    #: Seeded ``inflection_codes.code`` to id map.
    _inflection_code_ids: dict[str, int]
    #: Lemma assignment map keyed by ``(normalized_title, pos_id)``.
    _morph_class_ids: dict[tuple[str, int], int]
    #: Seeded canonical POS code to id map.
    _pos_ids_by_code: dict[str, int]

    def __init__(
        self,
        *,
        connection: sqlite3.Connection | None = None,
        join_index: NormalizedTitleJoinIndex | None = None,
        inflection_code_ids: dict[str, int] | None = None,
        morph_class_ids: dict[tuple[str, int], int] | None = None,
        pos_ids_by_code: dict[str, int] | None = None,
    ) -> None:
        """
        Initialize resolver lookup maps from a connection or preloaded data.

        Keyword Args:
            connection: Optional canonical SQLite connection used to preload
                lookup maps when explicit maps are omitted.
            join_index: Optional preloaded normalized-title dictionary join
                index.
            inflection_code_ids: Optional ``inflection_codes.code`` to id map.
            morph_class_ids: Optional ``(normalized_title, pos_id)`` to
                ``morph_class_id`` map.
            pos_ids_by_code: Optional canonical ``parts_of_speech.code`` to id
                map.

        Raises:
            ValueError: Preloaded maps are required when ``connection`` is
                omitted.

        """
        if connection is not None:
            if pos_ids_by_code is None:
                pos_ids_by_code = ensure_parts_of_speech(connection)
            if inflection_code_ids is None:
                inflection_code_ids = ensure_inflection_codes(
                    connection,
                    pos_ids_by_code,
                )
            if morph_class_ids is None:
                morph_class_ids = _load_morph_class_ids(connection)
            if join_index is None:
                join_index = _load_join_index(connection)
        elif (
            join_index is None
            or inflection_code_ids is None
            or morph_class_ids is None
            or pos_ids_by_code is None
        ):
            msg = "preloaded maps required when connection is omitted"
            raise ValueError(msg)

        #: Optional canonical SQLite connection for on-demand POS resolution.
        self._connection = connection
        #: Dictionary join index for ``entry_id`` resolution.
        self._join_index = join_index
        #: Seeded ``inflection_codes.code`` to id map.
        self._inflection_code_ids = inflection_code_ids
        #: Lemma assignment map keyed by ``(normalized_title, pos_id)``.
        self._morph_class_ids = morph_class_ids
        #: Seeded canonical POS code to id map.
        self._pos_ids_by_code = pos_ids_by_code

    def resolve_wordclass_id(self, wordclass: str) -> int | None:
        """
        Resolve one generator ``wordclass`` label to ``parts_of_speech.id``.

        Args:
            wordclass: Morphology form ``wordclass`` emitted by the generator.

        Returns:
            Seeded POS id for the mapped wordclass, or ``None`` when unknown.

        """
        if self._connection is not None:
            return pos_id_from_wordclass(self._connection, wordclass)
        code = _WORDCLASS_TO_POS_CODE.get(wordclass.strip().lower())
        if code is None:
            return None
        return self._pos_ids_by_code.get(code)

    def resolve_inflection_code_id(
        self,
        function: str,
        wordclass: str,
    ) -> int | None:
        """
        Resolve one morphology ``function`` code to ``inflection_codes.id``.

        Note:
            Empty or whitespace-only function strings resolve to the dedicated
            seeded ``unknown`` row, matching current morphology output in
            ``data/Ondej_Tich_40-54-1.pdf``. Part-of-speech scope:
            ``cross-PoS``.

        Args:
            function: Morphology form ``function`` code from generation output.
            wordclass: Generator ``wordclass`` label carried alongside the
                function for sink callers.

        Returns:
            Matching inflection-code id, or ``None`` when the code is absent
            from the seeded lookup table.

        """
        _ = wordclass
        code = function.strip()
        return self._inflection_code_ids.get(code)

    def resolve_morph_class_id(
        self,
        normalized_title: str,
        wordclass: str,
        function: str,
    ) -> int | None:
        """
        Resolve one lemma's assigned morph class for a generated form row.

        Note:
            Verbal participles with ``wordclass=verb`` and ``function`` in
            ``PsPt`` or ``PaPt`` inherit the parent verb lemma assignment, as
            documented in ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. Other forms use
            ``catalog_pos_from_wordclass`` before looking up
            ``lemma_morph_classes``. Part-of-speech scope: ``cross-PoS``.

        Args:
            normalized_title: Macron-preserving normalized lemma title.
            wordclass: Morphology form ``wordclass`` label.
            function: Morphology form ``function`` code.

        Returns:
            Assigned ``morph_class_id`` when exactly one lemma assignment
            exists, otherwise ``None``.

        """
        title_key = normalize_morphology_title(normalized_title)
        if not title_key:
            return None

        wordclass_key = wordclass.strip().lower()
        function_key = function.strip()
        catalog_pos: str | None
        if wordclass_key == "verb" and function_key in _VERB_PARTICIPLE_FUNCTIONS:
            catalog_pos = "verb"
        else:
            catalog_pos = catalog_pos_from_wordclass(wordclass)
        if catalog_pos is None:
            return None

        pos_id = self._pos_ids_by_code.get(catalog_pos)
        if pos_id is None:
            return None
        return self._morph_class_ids.get((title_key, pos_id))

    def resolve_entry_id(
        self,
        normalized_title: str,
        wordclass: str,
    ) -> int | None:
        """
        Resolve one dictionary ``bt_entries.id`` for a morphology form row.

        Args:
            normalized_title: Macron-preserving normalized lemma title.
            wordclass: Morphology form ``wordclass`` label used to narrow BT
                POS during the join.

        Returns:
            Matching entry id when ``NormalizedTitleJoinIndex.resolve_one``
            yields a single hit, otherwise ``None``.

        """
        bt_pos = _WORDCLASS_TO_BT_POS.get(wordclass.strip().lower())
        return self._join_index.resolve_one(normalized_title, bt_pos or None)
