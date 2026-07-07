"""Shared morphology wordclass to dictionary POS mapping helpers."""

from __future__ import annotations

from typing import Final

#: Morphology ``wordclass`` values mapped to dictionary ``bt_entries.pos`` labels.
WORDCLASS_TO_BT_POS: Final[dict[str, str]] = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adj",
    "adverb": "adv",
    "numeral": "numeral",
    "pronoun": "pron",
    "preposition": "prep",
    "conjunction": "conj",
    "interjection": "interj",
    "indeclinable": "indecl",
}


def infer_bt_pos_from_wordclasses(wordclasses: set[str]) -> str | None:
    """
    Map distinct morphology wordclasses to one dictionary POS when unambiguous.

    Args:
        wordclasses: Distinct morphology ``wordclass`` labels for one lemma.

    Returns:
        Dictionary POS label, or ``None`` when inference is ambiguous.

    """
    mapped = {
        WORDCLASS_TO_BT_POS[wc.strip().casefold()]
        for wc in wordclasses
        if wc.strip().casefold() in WORDCLASS_TO_BT_POS
    }
    mapped.discard("")
    if len(mapped) == 1:
        return next(iter(mapped))
    return None
