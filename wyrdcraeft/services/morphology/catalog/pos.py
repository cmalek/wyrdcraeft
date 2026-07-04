"""Normalize dictionary and generator POS labels to catalog vocabulary."""

from __future__ import annotations

from typing import Final

from wyrdcraeft.models.dictionary import BTPos

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
    key = bt_pos.strip().lower()
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
    key = wordclass.strip().lower()
    if key not in _WORDCLASS_TO_CATALOG:
        return None
    return _WORDCLASS_TO_CATALOG[key]
