# ruff: noqa: ERA001
"""
Noun form generation. Port of Perl generate_nounforms from create_dict31.pl.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from wyrdcraeft.services.morphology.progress import MorphologyStage
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_rows import print_one_form

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import Word
    from wyrdcraeft.services.morphology.progress import (
        MorphologyGenerateProgressCoordinator,
    )
    from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool

    from .shared import FormOutput

#: The vowel regex, saved here for convenience.
VOWEL = OENormalizer.VOWEL
#: The consonant regex, saved here for convenience.
CONSONANT = OENormalizer.CONSONANT_REGEX.pattern

#: Paradigm labels that use the opt-in r-stem emission tables.
R_STEM_PARADIGMS = {"fæder", "brōþor", "mōdor", "dōhtor", "sweostor"}

#: Full-form overrides for the r-stem noun ``fæder``.
R_STEM_FAEDER_FORMS = {
    "SgMaNo": ["fæder"],
    "SgMaAc": ["fæder"],
    "SgMaGe": ["fæder", "fæderes"],
    "SgMaDa": ["fæder", "fædere"],
    "PlMaNo": ["fæderas"],
    "PlMaAc": ["fæderas"],
    "PlMaGe": ["fædera"],
    "PlMaDa": ["fæderum"],
}

#: Full-form overrides for the r-stem noun ``brōþor``.
R_STEM_BROTHOR_FORMS = {
    "SgMaNo": ["brōþor", "brōþur", "brōdor", "brōdur"],
    "SgMaAc": ["brōþor", "brōþur", "brōdor", "brōdur"],
    "SgMaGe": ["brōþor", "brōþur", "brōdor", "brōdur"],
    "SgMaDa": ["brōþer", "brēþer", "brōder", "brēder"],
    "PlMaNo": [
        "brōþor",
        "brōþru",
        "brōþur",
        "brōþro",
        "brōþer",
        "brōþra",
        "brōdor",
        "brōdru",
        "brōdur",
        "brōdro",
        "brōder",
        "brōdra",
    ],
    "PlMaAc": [
        "brōþor",
        "brōþru",
        "brōþur",
        "brōþro",
        "brōþer",
        "brōþra",
        "brōdor",
        "brōdru",
        "brōdur",
        "brōdro",
        "brōder",
        "brōdra",
    ],
    "PlMaGe": ["brōþra", "brōdra"],
    "PlMaDa": ["brōþrum", "brōdrum"],
}

#: Full-form overrides for the r-stem noun ``dōhtor``.
R_STEM_DOHTOR_FORMS = {
    "SgFeNo": ["dōhtor"],
    "SgFeAc": ["dōhtor"],
    "SgFeGe": ["dōhtor"],
    "SgFeDa": ["dēhter"],
    "PlFeNo": ["dōhtor", "dōhtru", "dōhtra"],
    "PlFeAc": ["dōhtor", "dōhtru", "dōhtra"],
    "PlFeGe": ["dōhtra"],
    "PlFeDa": ["dōhtrum"],
}

#: Full-form overrides for the r-stem noun ``mōdor``.
R_STEM_MODOR_FORMS = {
    "SgFeNo": ["mōdor"],
    "SgFeAc": ["mōdor"],
    "SgFeGe": ["mōdor"],
    "SgFeDa": ["mēder"],
    "PlFeNo": ["mōdor", "mōdru", "mōdra"],
    "PlFeAc": ["mōdor", "mōdru", "mōdra"],
    "PlFeGe": ["mōdra"],
    "PlFeDa": ["mōdrum"],
}

#: Full-form overrides for the r-stem noun ``sweostor``.
R_STEM_SWEOSTOR_FORMS = {
    "SgFeNo": ["sweostor"],
    "SgFeAc": ["sweostor"],
    "SgFeGe": ["sweostor"],
    "SgFeDa": ["sweostor"],
    "PlFeNo": ["sweostor"],
    "PlFeAc": ["sweostor"],
    "PlFeGe": ["sweostra"],
    "PlFeDa": ["sweostrum"],
}


def _is_ge_collective(word: Word) -> bool:
    """
    Check if a noun is a ge-prefixed collective form.

    Args:
        word: The word to check.

    Returns:
        ``True`` for ge-prefixed collectives, otherwise ``False``.

    """
    return (word.prefix or "0") == "ge" and word.title.startswith("ge-")


def _form_from_parts(form_parts: str) -> str:
    r"""
    "Remove [0\\-\\n] from ``form_parts`` to get form.

    Note:
        This is the same as Perl s/[0\\-\\n]//.

    Args:
        form_parts: The form parts to process.

    Returns:
        The processed form.

    """
    return re.sub(r"[0\-\n]", "", form_parts)


def _noun_print(
    run_state: GenerationRunState,
    output_file: FormOutput,
    formhash: dict[str, str],
    form_parts: str,
    func: str,
) -> None:
    """
    Helper to set ``form/formParts/function`` and call ``print_one_form``.

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        formhash: The form hash.
        form_parts: The form parts.
        func: The function.

    """
    fh = formhash.copy()
    fh["function"] = func
    fh["form"] = _form_from_parts(form_parts)
    fh["formParts"] = form_parts.replace("\n", "")
    fh.setdefault("var", "")
    fh.setdefault("probability", "")
    fh.setdefault("paraID", "")
    fh.setdefault("class2", "")
    fh.setdefault("class3", "")
    fh.setdefault("comment", "")
    print_one_form(run_state, fh, output_file)


def _build_stem_geminate(stem: str) -> list[str]:
    r"""
    Build stem array with geminate reduction: ``({CONSONANT})\\1$ -> \\1``.

    Note:
        This is the same as Perl ``($consonant_regex)\\1$ -> \\1``.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    stems = [stem]
    alt = re.sub(f"({CONSONANT})\\1$", r"\1", stem)
    if alt != stem:
        stems.append(alt)
    return stems


def _build_stem_syncope(stem: str) -> list[str]:
    r"""
    Build stem with ``e$`` and ``h$`` removed, then syllab>1 syncope
    (``VC$ -> V``).

    Note:
        This is the same as Perl:

        .. cod e-block:: perl

            s/e$//; s/h$//; $syllable_count > 1 -> s/($vowel)($CONSONANT)$/\2``.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    s = re.sub(r"e$", "", stem)
    s = re.sub(r"h$", "", s, flags=re.IGNORECASE)
    stems = [s]
    if OENormalizer.syllable_count(s) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", s)
        if alt != s:
            stems.append(alt)
    return stems


def _build_stem_pl_no_ac(stem: str) -> list[str]:
    r"""
    Stem for plural nominative (PlNo)/ plural accusative (PlAc): drop e$, h$;
    geminate; syllab syncope.

    Note:
        This is the same as Perl:

        .. code-block:: perl

            s/e$//; s/h$//; $syllable_count > 1 -> s/($vowel)($CONSONANT)$/\2``.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    s = re.sub(r"e$", "", stem)
    s = re.sub(r"h$", "", s, flags=re.IGNORECASE)
    stems = [s]
    # Geminate reduction
    alt = re.sub(f"({CONSONANT})\\1$", r"\1", s)
    if alt != s:
        stems.append(alt)
    # Syllab syncope (if syllab>1)
    if OENormalizer.syllable_count(s) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", s)
        if alt != s:
            stems.append(alt)
    # o(C)$ -> e$1
    alt = re.sub(f"o({CONSONANT})$", r"e\1", s)
    if alt != s:
        stems.append(alt)
    return stems


def _build_stem_pl_ge_da(stem: str) -> list[str]:
    r"""
    Stem for plural genitive (PlGe)/ plural dative (PlDa): drop ``e$``, ``h$``;
    syllab syncope; stem[2] if ``o(C)$``.

    Note:
        This is the same as Perl:

        .. code-block:: perl

            s/e$//; s/h$//; $syllable_count > 1 -> s/($vowel)($CONSONANT)$/\2``.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    s = re.sub(r"e$", "", stem)
    s = re.sub(r"h$", "", s, flags=re.IGNORECASE)
    stems = [s]
    if OENormalizer.syllable_count(s) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", s)
        if alt != s:
            stems.append(alt)
    match = re.search(f"o{CONSONANT}$", s)
    if match:
        stem2 = re.sub(f"o({CONSONANT})$", r"e\1", s)
        stems.append(stem2)
    return stems


def _build_stem_word_syncope(stem: str) -> list[str]:
    r"""
    Stem for word paradigm singular genitive (SgGe)/ singular dative (SgDa)/
    plural genitive (PlGe)/ plural dative (PlDa): syllab>1 syncope only.

    This is for the ``word`` Wright paradigm.

    Note:
        This is the same as Perl:

        .. code-block:: perl

            $syllable_count > 1 -> s/($vowel)($CONSONANT)$/\2``.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    stems = [stem]
    if OENormalizer.syllable_count(stem) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", stem)
        if alt != stem:
            stems.append(alt)
    return stems


def _build_stem_hof_ge_da(stem: str) -> list[str]:
    """
    Stem for hof singular genitive (SgGe)/ singular dative (SgDa)/ plural
    genitive (PlGe)/ plural dative (PlDa): drop ``e$``, syllab>1 syncope.

    This is for the ``hof`` Wright paradigm.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    s = re.sub(r"e$", "", stem)
    stems = [s]
    if OENormalizer.syllable_count(s) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", s)
        if alt != s:
            stems.append(alt)
    return stems


def _build_stem_daeg_pl(stem: str) -> list[str]:
    r"""
    Stem for dæg plural: stem + ``æ->a``, ``ǣ->ā`` (i-mutation reversal).

    This is for the ``dæg`` Wright paradigm.

    Note:
        This is the same as Perl:

        .. code-block:: perl

            s/\x{00e6}/a/g; s/\x{01fd}/\x{00e1}/g``.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    stems = [stem]
    alt = stem.replace("æ", "a").replace("ǣ", "ā")  # æ->a, ǣ->ā
    if alt != stem:
        stems.append(alt)
    return stems


def _build_stem_ar_sg_no_ac(stem: str) -> list[str]:
    """
    Stem for ār singular nominative (SgNo)/ singular accusative (SgAc): stem +
    geminate.

    This is for the ``ār`` Wright paradigm.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    return _build_stem_geminate(stem)


def _build_stem_ar_sg_ge_da(stem: str) -> list[str]:
    """
    Stem for ār singular genitive (SgGe)/ singular dative (SgDa): drop ``u$``,
    syllab>1 syncope.

    This is for the ``ār`` Wright paradigm.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    s = re.sub(r"u$", "", stem)
    stems = [s]
    if OENormalizer.syllable_count(s) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", s)
        if alt != s:
            stems.append(alt)
    return stems


def _build_stem_ar_pl(stem: str) -> list[str]:
    """
    Stem for ār plural: drop ``u$``, syllab syncope, geminate.

    This is for the ``ār`` Wright paradigm.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    s = re.sub(r"u$", "", stem)
    stems = [s]
    if OENormalizer.syllable_count(s) > 1:
        alt = re.sub(f"({VOWEL})({CONSONANT})$", r"\2", s)
        if alt != s:
            stems.append(alt)
    alt = re.sub(f"({CONSONANT})\\1$", r"\1", s)
    if alt != s:
        stems.append(alt)
    return stems


class NounFormGenerator:
    """
    Generates noun surface forms across every noun paradigm (a-stem,
    ja-stem, root nouns, ō-stem, u-stem, consonant-stem, wa-stem, weak
    n-stem, nd-stem, and opt-in r-stem) for one morphology generation run.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: The output file handle.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    #: Ordered ``(regex pattern, method name)`` pairs tried in sequence
    #: against the current paradigm label; first match wins. Order mirrors
    #: the original ``elif re.search(...)`` chain exactly (ADR 0009 Decision
    #: item 3). Confirmed mutually exclusive against real paradigm labels, so
    #: table order does not change matching outcomes, but the original order
    #: is preserved regardless. ``stan_cynn`` is intentionally NOT in this
    #: table: it must be checked (on the per-iteration ``paradigm``) ahead of
    #: the ``word`` block's loop-invariant ``noun_paradigm[0]`` check in
    #: ``_generate_word``, which is not provably mutually exclusive with it.
    _PARADIGM_DISPATCH: ClassVar[list[tuple[str, str]]] = [
        (r"hof", "_gen_hof"),
        (r"dæg", "_gen_daeg"),
        (r"fæt", "_gen_faet"),
        (r"ár", "_gen_ar"),
        (r"strengu", "_gen_strengu"),
        (r"hand|feld", "_gen_hand_feld"),
        (r"sunu|duru", "_gen_sunu_duru"),
        (r"bearu", "_gen_bearu"),
        (r"bealu", "_gen_bealu"),
        (r"guma", "_gen_guma"),
        (r"fréa", "_gen_frea"),
        (r"tunge", "_gen_tunge"),
        (r"éage", "_gen_eage"),
        (r"wígend", "_gen_wigend"),
    ]

    #: Method names in ``_PARADIGM_DISPATCH`` that need the current paradigm
    #: label passed as a positional argument in addition to ``word``/
    #: ``formhash_base``.
    _DISPATCH_NEEDS_PARADIGM_ARG: ClassVar[frozenset[str]] = frozenset(
        {"_gen_hand_feld", "_gen_sunu_duru"}
    )

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Bind a noun form generator to one word pool, run state, and output
        sink.

        Args:
            word_pool: Word pool supplying the lemmas to generate forms for.
            run_state: Mutable per-run generation state.
            output_file: The output file handle.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Word pool supplying the lemmas to generate forms for.
        self._word_pool = word_pool
        #: Mutable per-run generation state.
        self._run_state = run_state
        #: The output file handle.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """
        Generate noun forms.

        Side Effects:
            Writes generated rows to the morphology output stream.

        """
        for word in self._word_pool.words:
            if not word.noun_paradigm:
                continue
            self._generate_word(word)

    def _generate_word(self, word: Word) -> None:
        """
        Generate noun forms for a single word.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            word: The word to generate forms for.

        """
        if self._progress is not None:
            self._progress.advance(
                MorphologyStage.NOUNS,
                lemma=word.title,
                wright=word.wright,
                forms_written=self._run_state.output_counter,
            )
        bt_id = f"{word.nid:06d}"
        formhash_base = {
            "title": word.title,
            "stem": word.stem,
            "BT": bt_id,
            "wordclass": "noun",
            "class1": "strong",
            "wright": word.wright,
            "var": "",
            "probability": "",
            "paraID": "",
            "class2": "",
            "class3": "",
            "comment": "",
        }
        for _i2, paradigm in enumerate(word.noun_paradigm):
            if paradigm is None:
                continue
            formhash_base["paradigm"] = paradigm
            if self._run_state.enable_r_stem_nouns and paradigm in R_STEM_PARADIGMS:
                self._dispatch_r_stem(word, formhash_base, paradigm)
            elif re.search(r"stān|cynn", paradigm):
                # Checked here (per-iteration ``paradigm``) ahead of the
                # ``word`` block below, which tests the loop-invariant
                # ``noun_paradigm[0]`` instead. The two are not provably
                # mutually exclusive across a multi-entry ``noun_paradigm``
                # list, so the original elif-chain priority (stan_cynn before
                # word) must be preserved exactly; see ADR 0009 Decision item
                # 3.
                self._gen_stan_cynn(
                    word,
                    formhash_base,
                    paradigm,
                    is_cynn=bool(re.search(r"cynn", paradigm)),
                )
            elif word.noun_paradigm[0] and re.search(r"word", word.noun_paradigm[0]):
                # Perl: for i2 in 0..scalar(@noun_paradigm) - word block checks
                # [0], runs len+1 times
                for _i2 in range(len(word.noun_paradigm) + 1):
                    paradigm_val = (
                        word.noun_paradigm[_i2] if _i2 < len(word.noun_paradigm) else ""
                    )
                    formhash_base = {**formhash_base, "paradigm": paradigm_val}
                    self._gen_word(word, formhash_base)
            else:
                self._dispatch_paradigm(word, formhash_base, paradigm)

    def _dispatch_r_stem(
        self, word: Word, formhash_base: dict[str, str], paradigm: str
    ) -> None:
        """
        Call the r-stem generator matching ``paradigm``.

        Args:
            word: The word to generate forms for.
            formhash_base: The base form hash.
            paradigm: The current paradigm label; must be a member of
                ``R_STEM_PARADIGMS``.

        """
        if paradigm == "fæder":
            self._gen_r_stem_faeder(word, formhash_base)
        elif paradigm == "brōþor":
            self._gen_r_stem_brothor(word, formhash_base)
        elif paradigm == "mōdor":
            self._gen_r_stem_modor(word, formhash_base)
        elif paradigm == "dōhtor":
            self._gen_r_stem_dohtor(word, formhash_base)
        elif paradigm == "sweostor":
            self._gen_r_stem_sweostor(word, formhash_base)

    def _dispatch_paradigm(
        self, word: Word, formhash_base: dict[str, str], paradigm: str
    ) -> None:
        """
        Call the first ``_PARADIGM_DISPATCH`` method whose pattern matches.

        Note:
            First-match-wins over the ordered table, mirroring the original
            ``elif re.search(...)`` chain exactly (ADR 0009 Decision item 3).

        Args:
            word: The word to generate forms for.
            formhash_base: The base form hash.
            paradigm: The current paradigm label.

        """
        for pattern, method_name in self._PARADIGM_DISPATCH:
            if re.search(pattern, paradigm):
                method = getattr(self, method_name)
                if method_name in self._DISPATCH_NEEDS_PARADIGM_ARG:
                    method(word, formhash_base, paradigm)
                else:
                    method(word, formhash_base)
                return

    def _gen_word(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``word`` paradigm (neuter a-stems). Uses ``noun_paradigm[0]`` for match.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"

        def fp(stem: str, ending: str) -> str:
            return f"{prefix}-{stem}-{ending}"

        # SgNo, SgAc: plain stem
        for s in [word.stem]:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgNeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgNeAc",
                )

        # SgGe, SgDa: stem + syllab syncope
        for s in _build_stem_word_syncope(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "es"),
                    "SgNeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgNeDa",
                )

        # PlNo, PlAc: plain stem (no reset between)
        for s in [word.stem]:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "PlNeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "PlNeAc",
                )

        # PlGe, PlDa: stem + syllab syncope
        for s in _build_stem_word_syncope(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlNeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "um"),
                    "PlNeDa",
                )

    def _gen_hof(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``hof`` paradigm (neuter ja-stems).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"
        stem_base = re.sub(r"e$", "", word.stem)

        def fp(stem: str, ending: str) -> str:
            return f"{prefix}-{stem}-{ending}"

        # SgNo, SgAc: stem + geminate
        for s in _build_stem_geminate(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgNeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgNeAc",
                )

        # SgGe, SgDa: stem e$ removed + syllab syncope
        for s in _build_stem_hof_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "es"),
                    "SgNeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgNeDa",
                )

        # PlNo: stem e$ removed, endings -u and -o
        for s in [stem_base]:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "u"),
                    "PlNeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "o"),
                    "PlNeNo",
                )

        # PlAc: stem e$ removed, endings -u and -o
        for s in [stem_base]:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "u"),
                    "PlNeAc",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "o"),
                    "PlNeAc",
                )

        # PlGe, PlDa: stem e$ removed + syllab syncope
        for s in _build_stem_hof_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlNeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "um"),
                    "PlNeDa",
                )

    def _gen_daeg(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``dæg`` paradigm (masculine root nouns, i-mutation).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"

        def fp(stem: str, ending: str) -> str:
            return f"{prefix}-{stem}-{ending}"

        # SgNo, SgAc, SgGe, SgDa: plain stem
        for s in [word.stem]:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgMaNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgMaAc",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "es"),
                    "SgMaGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgMaDa",
                )

        # PlNo, PlAc, PlGe, PlDa: stem + æ->a, ǣ->ā
        for s in _build_stem_daeg_pl(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "as"),
                    "PlMaNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "as"),
                    "PlMaAc",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlMaGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "um"),
                    "PlMaDa",
                )

    def _gen_faet(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``faet`` paradigm (neuter root nouns).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"

        def fp(stem: str, ending: str) -> str:
            return f"{prefix}-{stem}-{ending}"

        # SgNo, SgAc, SgGe, SgDa: plain stem
        for s in [word.stem]:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgNeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgNeAc",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "es"),
                    "SgNeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgNeDa",
                )

        # PlNo: stem + æ->a, ǣ->ā, endings -u and -o
        for s in _build_stem_daeg_pl(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "u"),
                    "PlNeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "o"),
                    "PlNeNo",
                )

        # PlAc: same
        for s in _build_stem_daeg_pl(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "u"),
                    "PlNeAc",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "o"),
                    "PlNeAc",
                )

        # PlGe, PlDa
        for s in _build_stem_daeg_pl(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlNeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "um"),
                    "PlNeDa",
                )

    def _gen_ar(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``ār`` paradigm (feminine ō-stems).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"

        def fp(stem: str, ending: str) -> str:
            return f"{prefix}-{stem}-{ending}"

        # SgNo, SgAc: stem + geminate
        for s in _build_stem_ar_sg_no_ac(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    "SgFeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgFeAc",
                )

        # SgGe, SgDa: stem u$ removed + syllab syncope
        for s in _build_stem_ar_sg_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgFeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "SgFeDa",
                )

        # PlNo & PlAc: Perl reuses @stem - PlNo does not zero, PlAc overwrites
        # [0] then pushes
        stems_pl = _build_stem_ar_pl(word.stem)
        for s in stems_pl:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlFeNo",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "PlFeNo",
                )
        stems_ac = stems_pl + [x for x in stems_pl[1:] if x]
        for s in stems_ac:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlFeAc",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    "PlFeAc",
                )

        # PlGe: stem u$ removed + syllab syncope, endings -a and -na and -ena
        for s in _build_stem_ar_sg_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    "PlFeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "na"),
                    "PlFeGe",
                )
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "ena"),
                    "PlFeGe",
                )

        # PlDa: stem u$ removed + syllab syncope
        for s in _build_stem_ar_sg_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "um"),
                    "PlFeDa",
                )

    def _gen_strengu(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``strengu`` paradigm (feminine u-stems).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"
        s = re.sub(r"u$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        for end, func in [("u", "SgFeNo"), ("o", "SgFeNo")]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), func
            )
        for end, func in [("e", "SgFeAc"), ("u", "SgFeAc"), ("o", "SgFeAc")]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), func
            )
        for end, func in [("e", "SgFeGe"), ("u", "SgFeGe"), ("o", "SgFeGe")]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), func
            )
        for end, func in [("e", "SgFeDa"), ("u", "SgFeDa"), ("o", "SgFeDa")]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), func
            )
        for end in ["e", "u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "PlFeNo"
            )
        for end in ["e", "u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "PlFeAc"
            )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), "PlFeGe"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("um"), "PlFeDa"
        )

    def _gen_hand_feld(
        self, word: Word, formhash_base: dict[str, str], paradigm: str
    ) -> None:
        """
        ``hand``/``feld`` paradigm (feminine/masculine consonant stems).

        Args:
            word: The word to process.
            formhash_base: The base form hash.
            paradigm: The paradigm.

        """
        prefix = word.prefix or "0"
        is_feld = bool(re.search(r"feld", paradigm))
        sfx = "Ma" if is_feld else "Fe"

        def fp(ending: str) -> str:
            return f"{prefix}-{word.stem}-{ending}"

        for func in [f"Sg{sfx}No", f"Sg{sfx}Ac"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp("0"), func
            )
        for func in [f"Sg{sfx}Ge", f"Sg{sfx}Da"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp("a"), func
            )
        for func in [f"Pl{sfx}No", f"Pl{sfx}Ac"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp("a"), func
            )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), f"Pl{sfx}Ge"
        )
        # Perl: feld PlDa uses PlMaGe (likely typo for PlMaDa)
        _noun_print(
            self._run_state,
            self._output_file,
            formhash_base,
            fp("um"),
            f"Pl{sfx}Ge" if is_feld else f"Pl{sfx}Da",
        )

    def _gen_sunu_duru(
        self, word: Word, formhash_base: dict[str, str], paradigm: str
    ) -> None:
        """
        Sunu/duru paradigm (masculine/feminine u-stems).

        Note:
            U-stem noun alternations follow ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits noun
            Part-of-Speech endings for ``sunu``/``duru``-like stems.

        Args:
            word: The word to process.
            formhash_base: The base form hash.
            paradigm: The noun paradigm.

        """
        prefix = word.prefix or "0"
        s = re.sub(r"u$", "", word.stem)
        if not s:
            return
        is_duru = bool(re.search(r"duru", paradigm))
        sfx = "Ma" if is_duru else "Fe"

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        for end in ["u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), f"Sg{sfx}No"
            )
        for end in ["u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), f"Sg{sfx}Ac"
            )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), f"Sg{sfx}Ge"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), f"Sg{sfx}Da"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), f"Pl{sfx}No"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), f"Pl{sfx}Ac"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("a"), f"Pl{sfx}Ge"
        )
        _noun_print(
            self._run_state,
            self._output_file,
            formhash_base,
            fp("um"),
            f"Pl{sfx}Ge" if is_duru else f"Pl{sfx}Da",
        )

    def _gen_bearu(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        Bearu paradigm (masculine wa-stems).

        Note:
            Wa-stem noun behavior follows ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits noun
            Part-of-Speech forms for ``bearu``-like stems.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"
        s = re.sub(r"[uw]$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        for end in ["u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "SgMaNo"
            )
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "SgMaAc"
            )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("wes"), "SgMaGe"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("we"), "SgMaDa"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("was"), "PlMaNo"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("was"), "PlMaAc"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("wa"), "PlMaGe"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("wum"), "PlMaDa"
        )

    def _gen_bealu(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        Bealu paradigm (neuter wa-stems).

        Note:
            Neuter wa-stem noun behavior follows ``data/OldEnglishGrammar.pdf``
            and ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits
            noun Part-of-Speech forms for ``bealu``-like stems.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        prefix = word.prefix or "0"
        s = re.sub(r"[uw]$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        for end in ["u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "SgNeNo"
            )
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "SgNeAc"
            )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("wes"), "SgNeGe"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("we"), "SgNeDa"
        )
        for end in ["u", "o"]:
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "PlNeNo"
            )
            _noun_print(
                self._run_state, self._output_file, formhash_base, fp(end), "PlNeAc"
            )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("wa"), "PlNeGe"
        )
        _noun_print(
            self._run_state, self._output_file, formhash_base, fp("wum"), "PlNeDa"
        )

    def _gen_guma(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``guma`` paradigm (masculine n-stems, weak).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        fh = formhash_base.copy()
        fh["class1"] = "weak"
        prefix = word.prefix or "0"
        s = re.sub(r"a$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        _noun_print(self._run_state, self._output_file, fh, fp("a"), "SgMaNo")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "SgMaAc")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "SgMaGe")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "SgMaDa")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "PlMaNo")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "PlMaAc")
        _noun_print(self._run_state, self._output_file, fh, fp("ena"), "PlMaGe")
        _noun_print(self._run_state, self._output_file, fh, fp("um"), "PlMaDa")

    def _gen_frea(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        Frēa paradigm (masculine n-stems, weak).

        Note:
            Weak n-stem noun behavior follows ``data/OldEnglishGrammar.pdf``
            and ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits
            noun Part-of-Speech forms for ``frēa``-like stems.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        fh = formhash_base.copy()
        fh["class1"] = "weak"
        prefix = word.prefix or "0"
        s = re.sub(r"a$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        _noun_print(self._run_state, self._output_file, fh, fp("a"), "SgMaNo")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "SgMaAc")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "SgMaGe")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "SgMaDa")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "PlMaNo")
        _noun_print(self._run_state, self._output_file, fh, fp("an"), "PlMaAc")
        _noun_print(self._run_state, self._output_file, fh, fp("ana"), "PlMaGe")
        for end in ["um", "am", "aum"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlMaDa")

    def _gen_tunge(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``tunge`` paradigm (feminine ōn-stems, weak).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        fh = formhash_base.copy()
        fh["class1"] = "weak"
        prefix = word.prefix or "0"
        s = re.sub(r"e$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        _noun_print(self._run_state, self._output_file, fh, fp("e"), "SgFeNo")
        for end in ["an", "ean"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "SgFeAc")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "SgFeGe")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "SgFeDa")
        for end in ["an", "ean"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlFeNo")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlFeAc")
        _noun_print(self._run_state, self._output_file, fh, fp("ena"), "PlFeGe")
        for end in ["um", "eum"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlFeDa")

    def _gen_eage(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``ēage`` paradigm (neuter n-stems, weak).

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        fh = formhash_base.copy()
        fh["class1"] = "weak"
        prefix = word.prefix or "0"
        s = re.sub(r"e$", "", word.stem)
        if not s:
            return

        def fp(ending: str) -> str:
            return f"{prefix}-{s}-{ending}"

        _noun_print(self._run_state, self._output_file, fh, fp("e"), "SgNeNo")
        for end in ["an", "ean"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "SgNeAc")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "SgNeGe")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "SgNeDa")
        for end in ["an", "ean"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlNeNo")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlNeAc")
        _noun_print(self._run_state, self._output_file, fh, fp("ena"), "PlNeGe")
        for end in ["um", "eum"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlNeDa")

    def _gen_wigend(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``wīgend`` paradigm (masculine nd-stems).

        Note:
            This is part of the ``weak`` block in Perl.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        fh = formhash_base.copy()
        fh["class1"] = "weak"
        prefix = word.prefix or "0"

        def fp(ending: str) -> str:
            return f"{prefix}-{word.stem}-{ending}"

        _noun_print(self._run_state, self._output_file, fh, fp("0"), "SgMaNo")
        _noun_print(self._run_state, self._output_file, fh, fp("0"), "SgMaAc")
        _noun_print(self._run_state, self._output_file, fh, fp("es"), "SgMaGe")
        _noun_print(self._run_state, self._output_file, fh, fp("e"), "SgMaDa")
        for end in ["0", "e", "as"]:
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlMaNo")
            _noun_print(self._run_state, self._output_file, fh, fp(end), "PlMaAc")
        _noun_print(self._run_state, self._output_file, fh, fp("ra"), "PlMaGe")
        _noun_print(self._run_state, self._output_file, fh, fp("um"), "PlMaDa")

    def _emit_r_stem_forms(
        self,
        word: Word,
        formhash_base: dict[str, str],
        forms_by_function: dict[str, list[str]],
    ) -> None:
        """
        Emit r-stem forms from a function-to-surfaces mapping.

        Args:
            word: The word to process.
            formhash_base: The base form hash.
            forms_by_function: Mapping of function to surface forms.

        """
        prefix = word.prefix or "0"
        for function, surfaces in forms_by_function.items():
            for surface in surfaces:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    f"{prefix}-{surface}",
                    function,
                )

    def _gen_r_stem_faeder(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``fæder`` opt-in r-stem forms.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        self._emit_r_stem_forms(word, formhash_base, R_STEM_FAEDER_FORMS)

    def _gen_r_stem_brothor(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``brōþor`` opt-in r-stem forms.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        forms = R_STEM_BROTHOR_FORMS
        if _is_ge_collective(word):
            forms = {
                "PlMaNo": forms["PlMaNo"],
                "PlMaAc": forms["PlMaAc"],
                "PlMaGe": forms["PlMaGe"],
                "PlMaDa": forms["PlMaDa"],
            }
        self._emit_r_stem_forms(word, formhash_base, forms)

    def _gen_r_stem_modor(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``mōdor`` opt-in r-stem forms.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        self._emit_r_stem_forms(word, formhash_base, R_STEM_MODOR_FORMS)

    def _gen_r_stem_dohtor(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``dōhtor`` opt-in r-stem forms.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        self._emit_r_stem_forms(word, formhash_base, R_STEM_DOHTOR_FORMS)

    def _gen_r_stem_sweostor(self, word: Word, formhash_base: dict[str, str]) -> None:
        """
        ``sweostor`` opt-in r-stem forms.

        Args:
            word: The word to process.
            formhash_base: The base form hash.

        """
        forms = R_STEM_SWEOSTOR_FORMS
        if _is_ge_collective(word):
            forms = {
                "PlFeNo": forms["PlFeNo"],
                "PlFeAc": forms["PlFeAc"],
                "PlFeGe": forms["PlFeGe"],
                "PlFeDa": forms["PlFeDa"],
            }
        self._emit_r_stem_forms(word, formhash_base, forms)

    def _gen_stan_cynn(  # noqa: PLR0912
        self,
        word: Word,
        formhash_base: dict[str, str],
        paradigm: str,  # noqa: ARG002
        is_cynn: bool,
    ) -> None:
        """
        ``stán``/``cynn`` paradigm (masculine/neuter a-stems).

        Args:
            word: The word to process.
            formhash_base: The base form hash.
            paradigm: The paradigm.
            is_cynn: Whether the word is a cynn.

        """
        prefix = word.prefix or "0"
        func_suffix = "Ne" if is_cynn else "Ma"

        def fp(stem: str, ending: str) -> str:
            return f"{prefix}-{stem}-{ending}"

        # SgNo
        for s in _build_stem_geminate(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    f"Sg{func_suffix}No",
                )

        # SgAc
        for s in _build_stem_geminate(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "0"),
                    f"Sg{func_suffix}Ac",
                )

        # SgGe
        for s in _build_stem_syncope(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "es"),
                    f"Sg{func_suffix}Ge",
                )

        # SgDa
        for s in _build_stem_syncope(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "e"),
                    f"Sg{func_suffix}Da",
                )

        # PlNo & PlAc: Perl reuses @stem - PlNo does not zero, PlAc overwrites
        # [0] then pushes
        stems_pl = _build_stem_pl_no_ac(word.stem)
        for s in stems_pl:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "as"),
                    f"Pl{func_suffix}No",
                )
        # PlAc: Perl overwrites $stem[0], pushes geminate/syncope/o alts ->
        # [s0,s1,s2,s3,s1,s2,s3]
        stems_ac = stems_pl + [s for s in stems_pl[1:] if s]
        for s in stems_ac:
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "as"),
                    f"Pl{func_suffix}Ac",
                )

        # PlGe
        for s in _build_stem_pl_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "a"),
                    f"Pl{func_suffix}Ge",
                )

        # PlDa
        for s in _build_stem_pl_ge_da(word.stem):
            if s:
                _noun_print(
                    self._run_state,
                    self._output_file,
                    formhash_base,
                    fp(s, "um"),
                    f"Pl{func_suffix}Da",
                )
