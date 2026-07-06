"""Normalize dictionary POS labels and resolve canonical POS identifiers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from wyrdcraeft.models.dictionary import BTPos

if TYPE_CHECKING:
    import sqlite3

#: Bosworth-Toller ``bt_entries.pos`` values and CLI aliases mapped to
#: ``morph_classes.pos`` vocabulary.
_BT_POS_TO_CATALOG: Final[dict[str, str]] = {
    BTPos.NOUN.value: "noun",
    BTPos.VERB.value: "verb",
    BTPos.ADJ.value: "adjective",
    BTPos.ADV.value: "adverb",
    BTPos.PRON.value: "pronoun",
    BTPos.NUMERAL.value: "numeral",
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "adjective": "adjective",
    "adverb": "adverb",
    "num": "numeral",
}

#: Stored BT POS values and accepted CLI aliases mapped to canonical
#: ``parts_of_speech.code`` values.
_BT_POS_TO_CODE: Final[dict[str, str]] = {
    BTPos.NOUN.value: "noun",
    BTPos.VERB.value: "verb",
    BTPos.ADJ.value: "adjective",
    BTPos.ADV.value: "adverb",
    BTPos.PRON.value: "pronoun",
    BTPos.NUMERAL.value: "numeral",
    BTPos.PREP.value: "preposition",
    BTPos.CONJ.value: "conjunction",
    BTPos.INTERJ.value: "interjection",
    BTPos.INDECL.value: "indeclinable",
    BTPos.UNKNOWN.value: "unknown",
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "adjective": "adjective",
    "adverb": "adverb",
    "num": "numeral",
}

#: Morphology generator ``wordclass`` values mapped to canonical
#: ``parts_of_speech.code`` values.
_WORDCLASS_TO_POS_CODE: Final[dict[str, str]] = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adjective",
    "adverb": "adverb",
    "pronoun": "pronoun",
    "numeral": "numeral",
    "preposition": "preposition",
    "conjunction": "conjunction",
    "interjection": "interjection",
    "indeclinable": "indeclinable",
    "participle": "participle",
}

#: Morphology generator ``wordclass`` values mapped to catalog POS.
#: ``None`` marks classes with no Wright morph-class assignment yet.
_WORDCLASS_TO_CATALOG: Final[dict[str, str | None]] = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adjective",
    "adverb": "adverb",
    "pronoun": "pronoun",
    "participle": "adjective",
    "preposition": None,
    "conjunction": None,
    "interjection": None,
    "indeclinable": None,
    "numeral": None,
}


def _normalize_pos_key(value: str) -> str:
    """
    Normalize one POS lookup token for deterministic mapping checks.

    Args:
        value: Raw POS string from dictionary, generator, or CLI input.

    Returns:
        Trimmed lowercase lookup token.

    """
    return value.strip().lower()


def _pos_id_from_code(connection: sqlite3.Connection, code: str) -> int:
    """
    Resolve one canonical POS code to its seeded ``parts_of_speech.id`` row.

    Note:
        The canonical code vocabulary follows the cross-part-of-speech categories
        documented in ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this bridges
        human-readable POS codes such as ``adjective`` or ``unknown`` to the
        integer lookup rows seeded for the normalized morphology schema.
        Part-of-speech scope: ``cross-PoS``.

    Args:
        connection: Open ``sqlite3.Connection`` bound to the canonical SQLite
            database. This module uses ``sqlite3`` directly so it matches
            ``pos_seed.py`` and the Alembic migration that unwraps SQLAlchemy to
            the underlying driver connection.
        code: Canonical ``parts_of_speech.code`` value to resolve.

    Returns:
        Seeded ``parts_of_speech.id`` value for ``code``.

    Raises:
        ValueError: The canonical code does not exist in ``parts_of_speech``.

    """
    row = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = ?",
        (_normalize_pos_key(code),),
    ).fetchone()
    if row is None:
        msg = f"no parts_of_speech row for code {code!r}"
        raise ValueError(msg)
    return int(row[0])


def catalog_pos_from_bt_pos(bt_pos: str) -> str:
    """
    Map a Bosworth-Toller POS label to ``morph_classes.pos`` vocabulary.

    Note:
        Wright's inflectional taxonomy in ``data/OldEnglishGrammar.pdf`` and
        Ondřej Tichý's generator tables in ``data/Ondej_Tich_40-54-1.pdf``
        cover nouns, verbs, adjectives, adverbs, and pronouns; catalog rows
        currently use those full POS names rather than BT abbreviations such
        as ``adj`` or ``pron``. Part-of-speech scope: ``cross-PoS``.

    Args:
        bt_pos: Stored ``bt_entries.pos`` value or CLI POS alias.

    Returns:
        Catalog POS string such as ``adjective`` or ``pronoun``.

    Raises:
        ValueError: When ``bt_pos`` has no catalog morph-class vocabulary.

    """
    key = _normalize_pos_key(bt_pos)
    try:
        return _BT_POS_TO_CATALOG[key]
    except KeyError as exc:
        msg = f"no catalog POS mapping for BTPos {bt_pos!r}"
        raise ValueError(msg) from exc


def catalog_pos_from_wordclass(wordclass: str) -> str | None:
    """
    Map a morphology generator ``wordclass`` to ``morph_classes.pos``.

    Note:
        Generator participles are verbal in origin (see
        ``data/Ondej_Tich_40-54-1.pdf``) but declined participial lemmas are
        assigned under catalog ``adjective`` rows with participial features,
        matching Wright's adjective-participle treatment in
        ``data/OldEnglishGrammar.pdf``. Closed-class and numeral wordclasses
        have no catalog rows yet. Part-of-speech scope: ``cross-PoS``.

    Args:
        wordclass: Morphology form ``wordclass`` field from generation output.

    Returns:
        Catalog POS string, or ``None`` when the wordclass is unmappable.

    """
    key = _normalize_pos_key(wordclass)
    if key not in _WORDCLASS_TO_CATALOG:
        return None
    return _WORDCLASS_TO_CATALOG[key]


def pos_id_from_bt_pos(connection: sqlite3.Connection, bt_pos: str) -> int:
    """
    Resolve one BT POS label or CLI alias to ``parts_of_speech.id``.

    Note:
        Bosworth-Toller stored POS values and CLI aliases collapse onto the
        canonical cross-part-of-speech categories documented in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``. In
        plain terms, abbreviations such as ``adj`` and ``prep`` resolve to the
        seeded ``adjective`` and ``preposition`` lookup rows. Part-of-speech
        scope: ``cross-PoS``.

    Args:
        connection: Open ``sqlite3.Connection`` bound to the canonical SQLite
            database. This matches the seed helpers and migration path already
            used for ``parts_of_speech``.
        bt_pos: Stored ``bt_entries.pos`` value or accepted CLI alias.

    Returns:
        Seeded ``parts_of_speech.id`` matching the normalized BT POS value.

    Raises:
        ValueError: ``bt_pos`` is unknown or its canonical row is missing.

    """
    key = _normalize_pos_key(bt_pos)
    try:
        code = _BT_POS_TO_CODE[key]
    except KeyError as exc:
        msg = f"no canonical POS mapping for BTPos {bt_pos!r}"
        raise ValueError(msg) from exc
    return _pos_id_from_code(connection, code)


def pos_id_from_wordclass(
    connection: sqlite3.Connection,
    wordclass: str,
) -> int | None:
    """
    Resolve one morphology generator wordclass to ``parts_of_speech.id``.

    Note:
        Generator wordclasses resolve directly against seeded
        ``parts_of_speech.code`` rows documented in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``. In
        plain terms, this is the lookup path for ``forms.wordclass_id`` and
        other normalized-schema FK writes. Unknown generator labels still return
        ``None``. Part-of-speech scope: ``cross-PoS``.

    Args:
        connection: Open ``sqlite3.Connection`` bound to the canonical SQLite
            database.
        wordclass: Morphology form ``wordclass`` emitted by the generator.

    Returns:
        Seeded ``parts_of_speech.id`` for the mapped wordclass, or ``None`` when
        the wordclass label is unknown.

    Raises:
        ValueError: The mapped canonical POS row is missing from the database.

    """
    key = _normalize_pos_key(wordclass)
    try:
        code = _WORDCLASS_TO_POS_CODE[key]
    except KeyError:
        return None
    return _pos_id_from_code(connection, code)


def pos_id_from_catalog_pos(connection: sqlite3.Connection, catalog_pos: str) -> int:
    """
    Resolve one canonical catalog POS string to ``parts_of_speech.id``.

    Note:
        Canonical catalog POS strings mirror the seeded reference vocabulary
        grounded in ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this is the direct
        lookup path when callers already have a canonical code such as
        ``adjective``. Part-of-speech scope: ``cross-PoS``.

    Args:
        connection: Open ``sqlite3.Connection`` bound to the canonical SQLite
            database.
        catalog_pos: Canonical ``parts_of_speech.code`` string.

    Returns:
        Seeded ``parts_of_speech.id`` matching ``catalog_pos``.

    Raises:
        ValueError: ``catalog_pos`` is not present in ``parts_of_speech``.

    """
    return _pos_id_from_code(connection, catalog_pos)
