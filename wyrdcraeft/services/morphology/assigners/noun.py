from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import Word

    from ..session import GeneratorSession

R_STEM_PARADIGM_BY_STEM = {
    "fæder": "fæder",
    "brōþor": "brōþor",
    "mōdor": "mōdor",
    "dōhtor": "dōhtor",
    "sweostor": "sweostor",
}

# Ordered, parity-preserving Wright mapping rules.
NOUN_WRIGHT_RULES: tuple[tuple[str, tuple[str, ...], bool], ...] = (
    (r"335|339|387|354|386|337|340|341|352", ("stán",), False),
    ("356", ("cynn",), True),
    (r"343|349|348", ("word",), False),
    (r"344|350|357|393|358", ("hof",), False),
    ("336", ("dæg",), True),
    ("345", ("fæt",), True),
    (r"367|368|373|376|390|366|372|370|375|378", ("ár",), False),
    ("383", ("strengu",), True),
    ("397", ("feld",), True),
    ("398", ("hand", "duru"), True),
    ("396", ("sunu",), True),
    (r"359|360", ("bearu",), False),
    (r"362|363", ("bealu",), False),
    (r"380|381", ("beadu",), False),
    ("401", ("guma",), True),
    ("402", ("fréa",), True),
    ("404", ("tunge",), True),
    ("405", ("béo",), True),
    ("407", ("éage",), True),
    ("418", ("wígend",), True),
)


def _match_wright_rule(wright: str, pattern: str, exact: bool) -> bool:
    """
    Evaluate one ordered Wright mapping rule.

    Args:
        wright: Wright code string.
        pattern: Pattern to match.
        exact: Whether to match the pattern exactly.

    Returns:
        ``True`` if the pattern is matched, otherwise ``False``.

    """
    return pattern in wright if exact else bool(re.search(pattern, wright))


def _assign_by_wright(word: Word) -> None:
    """
    Apply ordered Wright noun rules and append first-match paradigms.

    Args:
        word: The word to assign.

    """
    for pattern, paradigms, exact in NOUN_WRIGHT_RULES:
        if not _match_wright_rule(word.wright, pattern, exact):
            continue
        for paradigm in paradigms:
            if paradigm not in word.noun_paradigm:
                word.noun_paradigm.append(paradigm)
        return


def _wright_has_token(wright: str, token: str) -> bool:
    """
    Check whether ``wright`` contains the exact semicolon-delimited token.

    Args:
        wright: Wright code string.
        token: Token to match.

    Returns:
        ``True`` if token is present as an exact token; else ``False``.

    """
    return bool(re.search(rf"(?:^|;){re.escape(token)}(?:;|$)", wright))


def _get_r_stem_paradigm(word: Word) -> str | None:
    """
    Resolve opt-in r-stem paradigm for a word.

    Classification uses:
    - exact Wright token ``415``, and/or
    - explicit lexeme stem allowlist.

    Args:
        word: The word to classify.

    Returns:
        Canonical r-stem paradigm label when matched, otherwise ``None``.

    """
    stem_match = word.stem in R_STEM_PARADIGM_BY_STEM
    wright_match = _wright_has_token(word.wright, "415")
    if not (stem_match or wright_match):
        return None
    return R_STEM_PARADIGM_BY_STEM.get(word.stem)


def _assign_from_simple_stem(word: Word, assigned: list[Word]) -> bool:
    """
    Assign paradigm from exact-stem matches in the assigned noun pool.

    Args:
        word: Noun candidate to assign.
        assigned: Nouns already assigned a paradigm in current pass order.

    Returns:
        ``True`` when a paradigm was copied and ``word`` appended to ``assigned``.

    """
    for other in assigned:
        if word.stem == other.stem:
            word.noun_paradigm = [other.noun_paradigm[0]]
            assigned.append(word)
            return True
    return False


def _normalized_stem_variants(stem: str, prefix_re: str) -> tuple[str, str, str, str]:
    """
    Build ordered normalized stem candidates for advanced noun matching.

    Args:
        stem: Candidate noun stem.
        prefix_re: Session prefix regex used by the legacy stripping rule.

    Returns:
        Ordered tuple matching legacy ``mod_match`` transformation flow.

    """
    mod_match1 = re.sub(f"^({prefix_re})-?(.*)", r"\2", stem)
    mod_match2 = mod_match1.replace("y", "i")
    mod_match3 = mod_match1.replace("i", "y")
    mod_match4 = mod_match2.replace("i", "ie")
    return mod_match1, mod_match2, mod_match3, mod_match4


def _assign_from_advanced_stem(
    word: Word,
    assigned: list[Word],
    prefix_re: str,
) -> bool:
    """
    Assign paradigm using normalized stem variants against assigned nouns.

    Args:
        word: Noun candidate to assign.
        assigned: Nouns already assigned a paradigm in current pass order.
        prefix_re: Session prefix regex used by normalization.

    Returns:
        ``True`` when a paradigm was copied and ``word`` appended to ``assigned``.

    """
    stem_candidates = _normalized_stem_variants(word.stem, prefix_re)
    for other in assigned:
        if other.stem in stem_candidates:
            word.noun_paradigm = [other.noun_paradigm[0]]
            assigned.append(word)
            return True
    return False


def _run_simple_stem_pass(nouns: list[Word], assigned: list[Word]) -> None:
    """
    Run one exact-stem propagation pass for nouns lacking paradigms.

    Args:
        nouns: Nouns to process.
        assigned: Nouns already assigned paradigms.

    """
    for word in nouns:
        if not word.noun_paradigm:
            _assign_from_simple_stem(word, assigned)


def _run_advanced_stem_pass(
    nouns: list[Word],
    assigned: list[Word],
    prefix_re: str,
) -> None:
    """
    Run one normalized-stem propagation pass for nouns lacking paradigms.

    Args:
        nouns: Nouns to process.
        assigned: Nouns already assigned paradigms.
        prefix_re: Session prefix regex used by normalization.

    """
    for word in nouns:
        if not word.noun_paradigm:
            _assign_from_advanced_stem(word, assigned, prefix_re)


def _apply_noun_heuristics(  # noqa: PLR0912
    *,
    word: Word,
    buggy_word: Word,
    vowel_re: str,
    lvowel_re: str,
) -> bool:
    """
    Apply legacy noun heuristic rules for one word.

    Args:
        word: Noun candidate to assign.
        buggy_word: Companion word from ``session.words`` preserving Perl indexing.
        vowel_re: Vowel regex fragment.
        lvowel_re: Long-vowel regex fragment.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        ``True`` when at least one paradigm was appended.

    """
    v_match = re.search(
        f"^({vowel_re}?{vowel_re}?.*?)({vowel_re}{vowel_re}?)",
        word.stem,
    )
    vowel = v_match.group(2) if v_match else ""

    if word.stem.endswith("a"):
        if re.search(lvowel_re, vowel):
            word.noun_paradigm.append("fr\u00e9a")
        else:
            word.noun_paradigm.append("guma")
    if word.stem.endswith("e"):
        if word.n_fem == 1:
            word.noun_paradigm.append("tunge")
        if word.n_masc == 1:
            word.noun_paradigm.append("st\u00e1n")
        if word.n_neut == 1:
            word.noun_paradigm.append("hof")
    if word.stem.endswith("nd") and word.n_masc == 1:
        word.noun_paradigm.append("w\u00edgend")
    if re.search(r"(els|scipe)$", word.stem):
        word.noun_paradigm.append("st\u00e1n")
    if word.stem.endswith("incel"):
        word.noun_paradigm.append("hof")
    if re.search(r"(ness|niss|nyss|ung)$", word.stem):
        word.noun_paradigm.append("\u00e1r")

    if re.search(r"[\u00e6\u01fd]", vowel) and buggy_word.syllables < 2:  # noqa: PLR2004
        if word.n_masc == 1:
            word.noun_paradigm.append("d\u00e6g")
        if word.n_neut == 1:
            word.noun_paradigm.append("f\u00e6t")

    return bool(word.noun_paradigm)


def _apply_final_fallback(word: Word, buggy_word: Word) -> None:
    """
    Apply last-resort noun paradigm fallback rules for one word.

    Args:
        word: Noun candidate to assign.
        buggy_word: Companion word from ``session.words`` preserving Perl indexing.

    """
    if word.n_masc == 1 or word.n_uncert == 1:
        word.noun_paradigm.append("st\u00e1n")

    if word.n_neut == 1:
        if OENormalizer.stem_length(buggy_word.stem):
            word.noun_paradigm.append("word")
        else:
            word.noun_paradigm.append("hof")

    if word.n_fem == 1:
        word.noun_paradigm.append("\u00e1r")



def set_noun_paradigm(session: GeneratorSession) -> None:
    """
    Set the noun paradigm.

    Args:
        session: The generator session.

    """
    nouns = session.nouns
    prefix_re = session.prefix_regex
    vowel_re = OENormalizer.VOWEL
    lvowel_re = OENormalizer.LVOWEL

    assigned: list[Word] = []

    for word in nouns:
        word.noun_paradigm = []
        if session.enable_r_stem_nouns:
            r_stem_paradigm = _get_r_stem_paradigm(word)
            if r_stem_paradigm:
                word.noun_paradigm.append(r_stem_paradigm)
                assigned.append(word)
                continue
        _assign_by_wright(word)

        if word.noun_paradigm:
            assigned.append(word)

    _run_simple_stem_pass(nouns, assigned)
    _run_advanced_stem_pass(nouns, assigned, prefix_re)

    # Heuristics
    for i, word in enumerate(nouns):
        if not word.noun_paradigm:
            if _apply_noun_heuristics(
                word=word,
                buggy_word=session.words[i],
                vowel_re=vowel_re,
                lvowel_re=lvowel_re,
            ):
                assigned.append(word)

    _run_simple_stem_pass(nouns, assigned)
    _run_advanced_stem_pass(nouns, assigned, prefix_re)

    # Final fallback
    for i, word in enumerate(nouns):
        if not word.noun_paradigm:
            _apply_final_fallback(word, session.words[i])
