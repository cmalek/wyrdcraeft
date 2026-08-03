from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import Word

    from ..session import WordPool

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


def _assign_from_advanced_stem(
    word: Word,
    assigned: _NounAssignedIndex,
    prefix_re: str,
) -> bool:
    """
    Assign paradigm using normalized stem variants against assigned nouns.

    Args:
        word: Noun candidate to assign.
        assigned: Index of nouns already assigned a paradigm in current pass order.
        prefix_re: Session prefix regex used by normalization.

    Returns:
        ``True`` when a paradigm was copied and ``word`` registered in ``assigned``.

    """
    return assigned.assign_from_advanced_stem(word, prefix_re)


class _NounAssignedIndex:
    """
    Track assigned noun paradigms with O(1) exact-stem and ordered advanced lookup.

    Note:
        Preserves Perl assignment order: the first assigned noun with a matching
        stem (exact or normalized variant) wins.

    """

    #: Nouns registered in assignment order.
    _assigned: list[Word]
    #: First assigned index for each noun stem.
    _stem_first_index: dict[str, int]
    #: Paradigm copied from the first assigned noun for each stem.
    _stem_paradigm: dict[str, str]

    def __init__(self) -> None:
        """Initialize empty assigned-noun tracking state."""
        #: Nouns registered in assignment order.
        self._assigned = []
        #: First assigned index for each noun stem.
        self._stem_first_index = {}
        #: Paradigm copied from the first assigned noun for each stem.
        self._stem_paradigm = {}

    def register(self, word: Word) -> None:
        """
        Register one assigned noun and its first-seen stem paradigm mapping.

        Args:
            word: Noun that now has at least one assigned paradigm.

        """
        self._assigned.append(word)
        if not word.noun_paradigm:
            return
        stem = word.stem
        if stem in self._stem_first_index:
            return
        index = len(self._assigned) - 1
        self._stem_first_index[stem] = index
        self._stem_paradigm[stem] = word.noun_paradigm[0]

    def assign_from_exact_stem(self, word: Word) -> bool:
        """
        Copy a paradigm from the first assigned noun with the same stem.

        Args:
            word: Noun candidate to assign.

        Returns:
            ``True`` when a paradigm was copied and ``word`` was registered.

        """
        paradigm = self._stem_paradigm.get(word.stem)
        if paradigm is None:
            return False
        word.noun_paradigm = [paradigm]
        self.register(word)
        return True

    def assign_from_advanced_stem(self, word: Word, prefix_re: str) -> bool:
        """
        Copy a paradigm from the first assigned noun matching a stem variant.

        Args:
            word: Noun candidate to assign.
            prefix_re: Session prefix regex used by normalization.

        Returns:
            ``True`` when a paradigm was copied and ``word`` was registered.

        """
        candidate_set = set(_normalized_stem_variants(word.stem, prefix_re))
        matching_stems = [
            stem for stem in self._stem_first_index if stem in candidate_set
        ]
        if not matching_stems:
            return False
        first_stem = min(matching_stems, key=self._stem_first_index.__getitem__)
        word.noun_paradigm = [self._stem_paradigm[first_stem]]
        self.register(word)
        return True


def _assign_from_simple_stem(word: Word, assigned: _NounAssignedIndex) -> bool:
    """
    Assign paradigm from exact-stem matches in the assigned noun pool.

    Args:
        word: Noun candidate to assign.
        assigned: Index of nouns already assigned a paradigm in current pass order.

    Returns:
        ``True`` when a paradigm was copied and ``word`` registered in ``assigned``.

    """
    return assigned.assign_from_exact_stem(word)


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


def _run_simple_stem_pass(nouns: list[Word], assigned: _NounAssignedIndex) -> None:
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
    assigned: _NounAssignedIndex,
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
    assigned: _NounAssignedIndex,
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
        buggy_word: Companion word from ``word_pool.words`` preserving Perl indexing.
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
        buggy_word: Companion word from ``word_pool.words`` preserving Perl indexing.
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
        buggy_word: Companion word from ``word_pool.words`` preserving Perl indexing.

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
    assigned: _NounAssignedIndex,
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
                assigned.register(word)
                continue
        _assign_by_wright(word)

        if word.noun_paradigm:
            assigned.register(word)


def _run_heuristic_pass(
    nouns: list[Word],
    words: list[Word],
    assigned: _NounAssignedIndex,
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
                assigned.register(word)


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



def set_noun_paradigm(word_pool: WordPool, *, enable_r_stem_nouns: bool) -> None:
    """
    Set the noun paradigm.

    Args:
        word_pool: The word pool.

    Keyword Args:
        enable_r_stem_nouns: Whether opt-in r-stem assignment is enabled.

    Note:
        This preserves the staged assignment flow described by Tichý (2017):
        exemplar assignment, morphophonological heuristics, then probability
        fallback, while keeping Wright-style declension exemplars used by the
        generator.

    """
    nouns = word_pool.nouns
    prefix_re = "|".join(word_pool.prefixes) if word_pool.prefixes else "0"
    vowel_re = OENormalizer.VOWEL
    lvowel_re = OENormalizer.LVOWEL

    assigned = _NounAssignedIndex()
    _run_initial_assignment_pass(
        nouns,
        assigned,
        enable_r_stem_nouns,
    )
    _run_stem_propagation_cycle(nouns, assigned, prefix_re)
    _run_heuristic_pass(
        nouns,
        word_pool.words,
        assigned,
        vowel_re,
        lvowel_re,
    )
    _run_stem_propagation_cycle(nouns, assigned, prefix_re)
    _run_final_fallback_pass(nouns, word_pool.words)
