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

#: Ordered suffix heuristics used in the morphophonological assignment stage.
NOUN_SUFFIX_HEURISTIC_RULES: tuple[tuple[str, str], ...] = (
    (r"(els|scipe)$", "st\u00e1n"),
    (r"incel$", "hof"),
    (r"(ness|niss|nyss|ung)$", "\u00e1r"),
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


def _run_stem_propagation_cycle(
    nouns: list[Word],
    assigned: list[Word],
    prefix_re: str,
) -> None:
    """
    Run one full stem-propagation cycle (simple then advanced).

    Args:
        nouns: Nouns to process.
        assigned: Nouns already assigned paradigms.
        prefix_re: Session prefix regex used by advanced matching.

    """
    _run_simple_stem_pass(nouns, assigned)
    _run_advanced_stem_pass(nouns, assigned, prefix_re)


def _extract_heuristic_vowel(stem: str, vowel_re: str) -> str:
    """
    Extract the legacy heuristic vowel capture from a noun stem.

    Args:
        stem: Noun stem to analyze.
        vowel_re: Vowel regex fragment.

    Returns:
        Captured vowel group used by heuristic rules, or ``""``.

    """
    v_match = re.search(
        f"^({vowel_re}?{vowel_re}?.*?)({vowel_re}{vowel_re}?)",
        stem,
    )
    return v_match.group(2) if v_match else ""


def _append_terminal_a_heuristic(word: Word, vowel: str, lvowel_re: str) -> None:
    """
    Append ``-a`` terminal heuristic paradigms.

    Args:
        word: Noun candidate to assign.
        vowel: Heuristic vowel capture for the stem.
        lvowel_re: Long-vowel regex fragment.

    """
    if not word.stem.endswith("a"):
        return
    if re.search(lvowel_re, vowel):
        word.noun_paradigm.append("fr\u00e9a")
    else:
        word.noun_paradigm.append("guma")


def _append_terminal_e_heuristic(word: Word) -> None:
    """
    Append ``-e`` terminal heuristic paradigms by grammatical gender flags.

    Args:
        word: Noun candidate to assign.

    """
    if not word.stem.endswith("e"):
        return
    if word.n_fem == 1:
        word.noun_paradigm.append("tunge")
    if word.n_masc == 1:
        word.noun_paradigm.append("st\u00e1n")
    if word.n_neut == 1:
        word.noun_paradigm.append("hof")


def _append_suffix_heuristics(word: Word) -> None:
    """
    Append heuristic paradigms for known terminal/suffix pattern classes.

    Args:
        word: Noun candidate to assign.

    Note:
        Wright lists ``-nd`` stems as a minor declension class
        (§§416-418). This helper keeps a dedicated ``-nd`` branch and then
        applies ordered compatibility suffix rules.

    """
    if word.stem.endswith("nd") and word.n_masc == 1:
        word.noun_paradigm.append("w\u00edgend")
    for pattern, paradigm in NOUN_SUFFIX_HEURISTIC_RULES:
        if re.search(pattern, word.stem):
            word.noun_paradigm.append(paradigm)


def _append_short_syllable_front_vowel_heuristic(
    word: Word,
    buggy_word: Word,
    vowel: str,
) -> None:
    """
    Append short-syllable front-vowel heuristic paradigms.

    Args:
        word: Noun candidate to assign.
        buggy_word: Companion word from ``session.words`` preserving Perl indexing.
        vowel: Heuristic vowel capture for the stem.

    """
    if not re.search(r"[\u00e6\u01fd]", vowel):
        return
    if buggy_word.syllables >= 2:  # noqa: PLR2004
        return
    if word.n_masc == 1:
        word.noun_paradigm.append("d\u00e6g")
    if word.n_neut == 1:
        word.noun_paradigm.append("f\u00e6t")


def _apply_noun_heuristics(
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
    vowel = _extract_heuristic_vowel(word.stem, vowel_re)
    _append_terminal_a_heuristic(word, vowel, lvowel_re)
    _append_terminal_e_heuristic(word)
    _append_suffix_heuristics(word)
    _append_short_syllable_front_vowel_heuristic(word, buggy_word, vowel)

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


def _run_initial_assignment_pass(
    nouns: list[Word],
    assigned: list[Word],
    enable_r_stem_nouns: bool,
) -> None:
    """
    Assign paradigms from r-stem and Wright rules for all nouns.

    Args:
        nouns: Nouns to process.
        assigned: Nouns already assigned paradigms.
        enable_r_stem_nouns: Whether opt-in r-stem assignment is enabled.

    Note:
        Tichý (2017) describes an initial assignment phase using exemplar
        paradigms derived from grammar before fallback stages.

    """
    for word in nouns:
        word.noun_paradigm = []
        if enable_r_stem_nouns:
            r_stem_paradigm = _get_r_stem_paradigm(word)
            if r_stem_paradigm:
                word.noun_paradigm.append(r_stem_paradigm)
                assigned.append(word)
                continue
        _assign_by_wright(word)

        if word.noun_paradigm:
            assigned.append(word)


def _run_heuristic_pass(
    nouns: list[Word],
    words: list[Word],
    assigned: list[Word],
    vowel_re: str,
    lvowel_re: str,
) -> None:
    """
    Assign paradigms using the legacy heuristic pass.

    Args:
        nouns: Nouns to process.
        words: Full session words list for legacy index coupling.
        assigned: Nouns already assigned paradigms.
        vowel_re: Vowel regex fragment.
        lvowel_re: Long-vowel regex fragment.

    Note:
        Tichý (2017, algorithm step 3) describes a morphophonological pass over
        previously unassigned items before probability fallback.

    """
    for i, word in enumerate(nouns):
        if not word.noun_paradigm:
            if _apply_noun_heuristics(
                word=word,
                buggy_word=words[i],
                vowel_re=vowel_re,
                lvowel_re=lvowel_re,
            ):
                assigned.append(word)


def _run_final_fallback_pass(nouns: list[Word], words: list[Word]) -> None:
    """
    Apply final fallback paradigms for nouns still lacking assignments.

    Args:
        nouns: Nouns to process.
        words: Full session words list for legacy index coupling.

    Note:
        Tichý (2017, algorithm step 4b) specifies noun fallback mapping:
        masculine/indefinite -> ``stán``, feminine -> ``ár``, neuter long stem
        -> ``word``, neuter short stem -> ``hof``.

    """
    for i, word in enumerate(nouns):
        if not word.noun_paradigm:
            _apply_final_fallback(word, words[i])



def set_noun_paradigm(session: GeneratorSession) -> None:
    """
    Set the noun paradigm.

    Args:
        session: The generator session.

    Note:
        This preserves the staged assignment flow described by Tichý (2017):
        exemplar assignment, morphophonological heuristics, then probability
        fallback, while keeping Wright-style declension exemplars used by the
        generator.

    """
    nouns = session.nouns
    prefix_re = session.prefix_regex
    vowel_re = OENormalizer.VOWEL
    lvowel_re = OENormalizer.LVOWEL

    assigned: list[Word] = []
    _run_initial_assignment_pass(
        nouns,
        assigned,
        session.enable_r_stem_nouns,
    )
    _run_stem_propagation_cycle(nouns, assigned, prefix_re)
    _run_heuristic_pass(
        nouns,
        session.words,
        assigned,
        vowel_re,
        lvowel_re,
    )
    _run_stem_propagation_cycle(nouns, assigned, prefix_re)
    _run_final_fallback_pass(nouns, session.words)
