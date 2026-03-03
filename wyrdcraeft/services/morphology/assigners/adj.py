from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..session import GeneratorSession


def _wright_rule_425(stem: str) -> str:
    """Resolve the Wright 425 adjective paradigm using vowel-sensitive matching."""
    return "glæd" if re.search(r"[\u00E6\u00C6]|ea", stem) else "til"


# Ordered, parity-preserving Wright token rules for adjective paradigms.
ADJ_WRIGHT_RULES: tuple[tuple[str, str | Callable[[str], str]], ...] = (
    ("425", _wright_rule_425),
    ("426", "blind"),
    ("428", "héah"),
    ("430", "manig"),
    ("431", "hálig"),
    ("434", "wilde"),
    ("436", "gearu"),
    ("437", "blind"),
)


def _assign_by_wright(word_stem: str, wright: str) -> str | None:
    """Apply ordered Wright-token rules and return the first matching paradigm."""
    for token, resolver in ADJ_WRIGHT_RULES:
        if token not in wright:
            continue
        if callable(resolver):
            return resolver(word_stem)
        return resolver
    return None


def set_adj_paradigm(session: GeneratorSession) -> None:  # noqa: PLR0912
    """Set the adjective paradigm."""
    # Perl ``set_adj_paradigm`` iterates over the full word list and returns it.
    # Keep a dedicated mutable pool (separate list, same objects) for
    # ``generate_adjforms`` so verb-generated participles can be appended there.
    adjectives = session.words
    session.adjectives = list(adjectives)

    for word in adjectives:
        word.adj_paradigm = []
        if "feald" in word.stem:
            word.numeral = 0

        matched = _assign_by_wright(word.stem, word.wright)
        if matched is not None:
            word.adj_paradigm.append(matched)

        if "\u00fe" + "weorh" in word.stem:  # þweorh
            word.adj_paradigm = ["\u00fe" + "weorh"]

    # Stem comparison
    for word in adjectives:
        if not word.adj_paradigm:
            for other in adjectives:
                if other.adj_paradigm and word.stem == other.stem:
                    word.adj_paradigm = [other.adj_paradigm[0]]
                    break

    # Heuristics
    for word in adjectives:
        if not word.adj_paradigm:
            if re.search(r"(sum|lic|l\u00EDc|isc)$", word.stem):
                word.adj_paradigm.append("til")
            elif re.search(r"(cund|feald|f\u00E6st|l\u00E9as|full|iht)$", word.stem):
                word.adj_paradigm.append("blind")
            elif re.search(r"(ihte|b\u01FDre|ede|wende)$", word.stem):
                word.adj_paradigm.append("wilde")
            elif word.syllables < 2:  # noqa: PLR2004
                if not OENormalizer.stem_length(word.stem):
                    if re.search(r"[\u00E6\u00C6]|ea", word.stem):
                        word.adj_paradigm.append("gl\u00e6d")
                    else:
                        word.adj_paradigm.append("til")
                elif re.search(f"{OENormalizer.VOWEL}h$", word.stem):
                    word.adj_paradigm.append("h\u00e9ah")
                elif re.search(f"{OENormalizer.CONSONANT}h$", word.stem):
                    word.adj_paradigm.append("\u00fe" + "weorh")
                else:
                    word.adj_paradigm.append("blind")
            elif word.stem.endswith(("u", "o")):
                word.adj_paradigm.append("gearu")
            elif word.stem.endswith("e"):
                word.adj_paradigm.append("wilde")
            elif OENormalizer.stem_length(word.stem):
                word.adj_paradigm.append("h\u00e1lig")
            else:
                word.adj_paradigm.append("manig")
