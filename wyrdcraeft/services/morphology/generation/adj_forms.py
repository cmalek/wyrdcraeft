"""
Adjective form generation. Port of Perl generate_adjforms from create_dict31.pl.
"""

import re
from collections.abc import Iterable
from typing import Final, Literal

from wyrdcraeft.models.morphology import Word
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologyStage,
)
from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_rows import print_one_form
from .shared import FormOutput

#: Remove parity ``form_parts`` markers without regex overhead.
_FORM_PARTS_DELETE = str.maketrans("", "", "0-\n")
#: Compiled patterns reused while expanding comparative/superlative stems.
_RE_U_SUFFIX: Final = re.compile(r"u$")
#: Trailing ``h`` matcher for adjective stem syncope variants.
_RE_H_SUFFIX: Final = re.compile(r"h$")
#: First vowel-plus-optional-e/a/o matcher for i-umlaut expansion.
_RE_VOWEL_EAO: Final = re.compile(f"({OENormalizer.VOWEL}[eao]?)")
#: Single-shot vowel replacement pattern for degree stem alternants.
_RE_VOWEL_REPLACE: Final = re.compile(f"{OENormalizer.VOWEL}[eao]?")
#: Trailing vowel matcher for syncope and weak-form variants.
_RE_VOWEL_END: Final = re.compile(f"({OENormalizer.VOWEL})$")
#: ``hālig`` syncope matcher for adjective degree stems.
_RE_HALIG_SYNCOPE: Final = re.compile(
    f"({OENormalizer.VOWEL}.*){OENormalizer.VOWEL}(.*)$"
)
#: Shared weak-paradigm case/ending pairs for definite degree forms.
_WEAK_DEGREE_CASE_ENDINGS: Final[tuple[tuple[str, str], ...]] = (
    ("SgMaNo", "a"),
    ("SgMaAc", "an"),
    ("SgMaGe", "an"),
    ("SgMaDa", "an"),
    ("SgNeNo", "e"),
    ("SgNeAc", "e"),
    ("SgNeGe", "an"),
    ("SgNeDa", "an"),
    ("SgFeNo", "e"),
    ("SgFeAc", "an"),
    ("SgFeGe", "an"),
    ("SgFeDa", "an"),
    ("PlMaNo", "an"),
    ("PlMaAc", "an"),
    ("PlMaGe", "a"),
    ("PlMaGe", "ena"),
    ("PlMaDa", "um"),
    ("PlNeNo", "an"),
    ("PlNeAc", "an"),
    ("PlNeGe", "a"),
    ("PlNeGe", "ena"),
    ("PlNeDa", "um"),
    ("PlFeNo", "an"),
    ("PlFeAc", "an"),
    ("PlFeGe", "a"),
    ("PlFeGe", "ena"),
    ("PlFeDa", "um"),
)
#: Superlative strong probability overrides from Perl ``create_dict31.pl``.
_SP_STRONG_PROB_PLUS_1: Final[frozenset[int]] = frozenset(
    {2, 5, 10, 14, 16, 18, 20, 22, 25, 27, 32, 35}
)
#: Superlative strong probability overrides requiring ``prob + 2``.
_SP_STRONG_PROB_PLUS_2: Final[frozenset[int]] = frozenset({29, 33, 36, 38})
#: Superlative strong case/ending pairs emitted after weak superlative forms.
_SP_STRONG_CASE_ENDINGS: Final[tuple[tuple[str, str], ...]] = (
    ("SgMaNo", "0"),
    ("SgMaAc", "ne"),
    ("SgMaAc", "0"),
    ("SgMaGe", "es"),
    ("SgMaDa", "um"),
    ("SgMaDa", "0"),
    ("SgNeNo", "0"),
    ("SgNeAc", "0"),
    ("SgNeGe", "es"),
    ("SgNeDa", "um"),
    ("SgNeDa", "0"),
    ("SgFeNo", "0"),
    ("SgFeAc", "e"),
    ("SgFeGe", "re"),
    ("SgFeGe", "0"),
    ("SgFeDa", "re"),
    ("SgFeDa", "0"),
    ("PlMaNo", "e"),
    ("PlMaNo", "0"),
    ("PlMaAc", "e"),
    ("PlMaAc", "0"),
    ("PlMaGe", "ra"),
    ("PlMaGe", "0"),
    ("PlMaDa", "um"),
    ("PlNeNo", "e"),
    ("PlNeNo", "0"),
    ("PlNeAc", "e"),
    ("PlNeAc", "0"),
    ("PlNeGe", "ra"),
    ("PlNeGe", "0"),
    ("PlNeDa", "um"),
    ("PlFeNo", "a"),
    ("PlFeNo", "e"),
    ("PlFeNo", "0"),
    ("PlFeAc", "a"),
    ("PlFeAc", "e"),
    ("PlFeAc", "0"),
    ("PlFeGe", "ra"),
    ("PlFeGe", "0"),
    ("PlFeDa", "um"),
)

def _dedupe_preserve_first(values: Iterable[str]) -> list[str]:
    """
    Return unique values, preserving first-seen order.

    Note:
        Adjective variant handling follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this keeps adjective
        Part-of-Speech alternants without duplicate repeats.

    Args:
        values: Input sequence in original order.

    Returns:
        De-duplicated values preserving first appearance.

    """
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique

def _perl_hash_order(values: list[str]) -> list[str]:
    """
    Return deterministic title ordering without Perl runtime dependency.

    Note:
        ``data/OldEnglishGrammar.pdf`` documents adjective alternants that can
        collapse to the same surface stem (for example, syncope/analogy around
        ``halig`` in §223 and §431, plus u/wa variation in §439-§440). The
        Old English generator description in
        ``data/Ondej_Tich_40-54-1.pdf`` also states that adjective generation
        intentionally emits multiple phonological/morphological alternatives.
        Part of Speech scope: adjective. In plain terms, this keeps the first
        linguistically valid stem order, then removes repeats so we do not emit
        duplicate adjective alternatives when different historical rules land on
        the same written form.

    Args:
        values: Candidate title variants in source order.

    Returns:
        Stable title variants in parity-preserving order.

    """
    return _dedupe_preserve_first(values)

def _form_from_parts(form_parts: str) -> str:
    r"""
    Remove [0\\-\\n] from form_parts to get form.

    Note:
        This is the same as Perl s/[0\-\n]//.

    Args:
        form_parts: The form parts to process.

    Returns:
        The processed form.

    """
    return form_parts.translate(_FORM_PARTS_DELETE)


def _finalize_degree_titles(
    title_array: list[str],
    *,
    use_perl_hash_order: bool,
) -> list[str]:
    """
    De-duplicate and order comparative/superlative title variants.

    Args:
        title_array: Candidate title variants in source order.

    Keyword Args:
        use_perl_hash_order: Whether to preserve Perl ``keys %hash`` ordering.

    Returns:
        Final title variants for degree-form emission.

    """
    if use_perl_hash_order:
        return _perl_hash_order(title_array)

    seen: set[str] = set()
    unique: list[str] = []
    for title in title_array:
        if title not in seen:
            seen.add(title)
            unique.append(title)
    unique.sort()
    return unique


def _expand_regular_degree_stems(  # noqa: PLR0913
    *,
    prefix: str,
    stem: str,
    paradigm: str,
    papart: int,
    pspart: int,
    update_halig_title_alt: bool,
) -> list[str]:
    """
    Expand regular adjective stems used for comparative/superlative generation.

    Note:
        Adjective degree stem alternations follow ``data/OldEnglishGrammar.pdf``
        and ``data/Ondej_Tich_40-54-1.pdf``. Part of Speech scope: adjective.

    Keyword Args:
        prefix: Lemma prefix segment.
        stem: Adjective stem being expanded.
        paradigm: Selected adjective paradigm label.
        papart: Past-participle flag on the source word.
        pspart: Present-participle flag on the source word.
        update_halig_title_alt: Whether ``hālig`` syncope updates the active
            stem before trailing-``h`` dropping, matching comparative parity.

    Returns:
        Ordered title variants before final de-duplication/sorting.

    """
    title_array: list[str] = []
    match = _RE_VOWEL_EAO.search(stem)
    if match is None:
        return title_array

    vowels = OENormalizer.iumlaut([match.group(1)])
    for vowel in vowels:
        title_alt = _RE_VOWEL_REPLACE.sub(vowel, stem, count=1)
        title_array.append(f"{prefix}-{title_alt}")
        if _RE_U_SUFFIX.search(title_alt):
            title_alt = _RE_U_SUFFIX.sub("w", title_alt)
            title_array.append(f"{prefix}-{title_alt}")
        if _RE_VOWEL_END.search(title_alt):
            title_alt = _RE_VOWEL_END.sub("", title_alt)
            title_array.append(f"{prefix}-{title_alt}")
        if "hālig" in paradigm and (papart + pspart) == 0:
            new_alt = _RE_HALIG_SYNCOPE.sub(r"\1\2", title_alt)
            if new_alt != title_alt:
                title_array.append(f"{prefix}-{new_alt}")
                if update_halig_title_alt:
                    title_alt = new_alt
        if _RE_H_SUFFIX.search(title_alt):
            title_alt = _RE_H_SUFFIX.sub("", title_alt)
            title_array.append(f"{prefix}-{title_alt}")
    return title_array


def _build_adjective_formhash(
    word: Word,
    *,
    class1: str,
    paradigm: str,
) -> dict[str, str]:
    """
    Build the shared form payload used across adjective degree generators.

    Args:
        word: Adjective entry being generated.

    Keyword Args:
        class1: Strong/weak class label for the emitted block.
        paradigm: Paradigm label stored on emitted rows.

    Returns:
        Mutable form payload reused by degree-form emitters.

    """
    formhash = {
        "title": word.title,
        "stem": word.stem,
        "BT": f"{word.nid:06d}",
        "wordclass": "adjective",
        "class1": class1,
        "paradigm": paradigm,
        "wright": word.wright,
        "var": "",
        "paraID": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }
    if word.papart == 1:
        formhash["wordclass"] = "participle"
        formhash["class2"] = "past"
    if word.pspart == 1:
        formhash["wordclass"] = "participle"
        formhash["class2"] = "present"
    if word.pronoun == 1:
        formhash["wordclass"] = "pronoun"
    return formhash


def _emit_weak_degree_forms(  # noqa: PLR0913
    run_state: GenerationRunState,
    output_file: FormOutput,
    formhash: dict[str, str],
    title_array: list[str],
    *,
    degree_prefix: str,
    affix: str,
    prob_mode: Literal["variant", "abs_delta"],
) -> None:
    """
    Emit one weak definite degree paradigm for each title variant.

    Note:
        Comparative and superlative weak blocks share the same case/endings in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        Part of Speech scope: adjective.

    Args:
        run_state: Mutable per-run generation state.
        output_file: Output sink receiving emitted rows.
        formhash: Shared mutable form payload for the current word.
        title_array: Ordered title variants for this degree block.

    Keyword Args:
        degree_prefix: Function prefix such as ``Co`` or ``Sp``.
        affix: Comparative/superlative infix such as ``r`` or ``ost``.
        prob_mode: ``variant`` uses the title index; ``abs_delta`` uses
            ``abs(index - 2)`` for comparative/superlative weak parity.

    Side Effects:
        Writes generated rows to the morphology output stream.

    """
    for variant_index, base in enumerate(title_array):
        prob = (
            variant_index
            if prob_mode == "variant"
            else abs(variant_index - 2)
        )
        run_state.perl_probability = prob
        for form_index, (case, ending) in enumerate(_WEAK_DEGREE_CASE_ENDINGS):
            formhash["function"] = f"{degree_prefix}{case}"
            formhash["probability"] = (
                str(prob + 1) if form_index >= 15 else ""  # noqa: PLR2004
            )
            form_parts = f"{base}-{affix}-{ending}"
            formhash["form"] = _form_from_parts(form_parts)
            formhash["formParts"] = form_parts
            print_one_form(run_state, formhash, output_file)


def _emit_superlative_strong_forms(
    run_state: GenerationRunState,
    output_file: FormOutput,
    formhash: dict[str, str],
    title_array: list[str],
    *,
    affix: str,
) -> None:
    """
    Emit superlative strong forms for each title variant.

    Note:
        Probability carry-over follows the Perl superlative-strong block in
        ``data/OldEnglishGrammar.pdf`` / ``data/Ondej_Tich_40-54-1.pdf``.
        Part of Speech scope: adjective.

    Args:
        run_state: Mutable per-run generation state.
        output_file: Output sink receiving emitted rows.
        formhash: Shared mutable form payload for the current word.
        title_array: Ordered title variants for this degree block.

    Keyword Args:
        affix: Superlative infix such as ``ost`` or ``0``.

    Side Effects:
        Writes generated rows to the morphology output stream.

    """
    for variant_index, base in enumerate(title_array):
        prob = abs(variant_index - 2)
        carried = ""
        for form_index, (case, ending) in enumerate(_SP_STRONG_CASE_ENDINGS):
            formhash["function"] = f"Sp{case}"
            if form_index < 2:  # noqa: PLR2004
                formhash["probability"] = ""
            elif form_index in _SP_STRONG_PROB_PLUS_1:
                carried = str(prob + 1)
                formhash["probability"] = carried
            elif form_index in _SP_STRONG_PROB_PLUS_2:
                carried = str(prob + 2)
                formhash["probability"] = carried
            else:
                formhash["probability"] = carried
            form_parts = f"{base}-{affix}-{ending}"
            formhash["form"] = _form_from_parts(form_parts)
            formhash["formParts"] = form_parts
            print_one_form(run_state, formhash, output_file)


def _adj_print(  # noqa: PLR0913
    run_state: GenerationRunState,
    output_file: FormOutput,
    formhash: dict[str, str],
    form_parts: str,
    func: str,
    prob: str,
) -> None:
    """
    Helper to set ``form``/``formParts``/``function``/``probability`` and call
    ``print_one_form``.

    Note:
        Matches Perl implementation of ``_adj_print`` function.

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        formhash: The form hash.
        form_parts: The form parts.
        func: The function.
        prob: The probability.

    """
    fh = formhash.copy()
    fh["function"] = func
    fh["probability"] = prob
    fh["form"] = _form_from_parts(form_parts)
    fh["formParts"] = form_parts.replace("\n", "")
    print_one_form(run_state, fh, output_file)


def _build_weak_title_array(word: Word, paradigm: str) -> list[str]:
    """
    Build title variants for weak adjective forms, matching Perl logic.

    Note:
        Weak adjective stem alternations follow ``data/OldEnglishGrammar.pdf``
        and ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this prepares
        adjective Part-of-Speech stem variants before adding endings.

    Args:
        word: Adjective entry being generated.
        paradigm: Selected adjective paradigm label.

    Returns:
        Ordered title variants used for weak-form emission.

    """
    vowel_regex = OENormalizer.VOWEL
    title_array: list[str] = []
    title_alt = word.stem

    # Original
    title_array.append(f"{word.prefix}-{title_alt}")

    # u -> w at end
    if re.search(r"u$", title_alt):
        title_alt = re.sub(r"u$", "w", title_alt)
        title_array.append(f"{word.prefix}-{title_alt}")

    # Drop final vowel
    if re.search(f"{vowel_regex}$", title_alt):
        title_alt = re.sub(f"({vowel_regex})$", "", title_alt)
        title_array.append(f"{word.prefix}-{title_alt}")

    # hālig syncope (only for hālig paradigm, not participles)
    is_halig = "hālig" in paradigm
    if is_halig and (word.papart + word.pspart) == 0:
        # Perl: $title_alt =~ s/($vowel_regex.*)$vowel_regex(.*?)$/$1$2/;
        new_alt = re.sub(
            f"({vowel_regex}.*){vowel_regex}(.*)$",
            r"\1\2",
            title_alt,
        )
        if new_alt != title_alt:
            title_alt = new_alt
            title_array.append(f"{word.prefix}-{title_alt}")

    # Drop trailing h
    if re.search(r"h$", title_alt):
        title_alt = re.sub(r"h$", "", title_alt)
        title_array.append(f"{word.prefix}-{title_alt}")

    return title_array


def _gen_strong_glaed_til(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``glæd``/``til`` paradigm.

    Note:
        Matches Perl ``glæd``/``til`` block.

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    title_alt = f"{word.prefix}-{word.stem}"
    if re.search(r"[\u00e6\u00c6]|ea", paradigm):
        stem_alt = re.sub(r"[\u00e6]|ea", "a", word.stem, flags=re.IGNORECASE)
        stem_alt = re.sub(r"[\u00c6]", "a", stem_alt)
        title_alt = f"{word.prefix}-{stem_alt}"

    base = f"{word.prefix}-{word.stem}"
    # Sg Ma
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoSgMaNo", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-ne", "PoSgMaAc", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoSgMaAc", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-es", "PoSgMaGe", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-um", "PoSgMaDa", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-0", "PoSgMaDa", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-e", "PoSgMaIs", "0")
    # Sg Ne
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoSgNeNo", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoSgNeAc", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-es", "PoSgNeGe", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-um", "PoSgNeDa", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-0", "PoSgNeDa", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-e", "PoSgNeIs", "0")
    # Sg Fe
    _adj_print(run_state, output_file, formhash, f"{title_alt}-u", "PoSgFeNo", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-o", "PoSgFeNo", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-0", "PoSgFeAc", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-re", "PoSgFeGe", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoSgFeGe", "1")
    _adj_print(run_state, output_file, formhash, f"{base}-re", "PoSgFeDa", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoSgFeDa", "1")
    # Pl Ma
    _adj_print(run_state, output_file, formhash, f"{title_alt}-e", "PoPlMaNo", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-0", "PoPlMaNo", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-e", "PoPlMaAc", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-0", "PoPlMaAc", "1")
    _adj_print(run_state, output_file, formhash, f"{base}-ra", "PoPlMaGe", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoPlMaGe", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-um", "PoPlMaDa", "0")
    # Pl Ne
    _adj_print(run_state, output_file, formhash, f"{title_alt}-u", "PoPlNeNo", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-o", "PoPlNeNo", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-u", "PoPlNeAc", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-o", "PoPlNeAc", "1")
    _adj_print(run_state, output_file, formhash, f"{base}-ra", "PoPlNeGe", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoPlNeGe", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-um", "PoPlNeDa", "0")
    # Pl Fe
    _adj_print(run_state, output_file, formhash, f"{title_alt}-a", "PoPlFeNo", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-o", "PoPlFeNo", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-a", "PoPlFeAc", "0")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-o", "PoPlFeAc", "1")
    _adj_print(run_state, output_file, formhash, f"{base}-ra", "PoPlFeGe", "0")
    _adj_print(run_state, output_file, formhash, f"{base}-0", "PoPlFeGe", "1")
    _adj_print(run_state, output_file, formhash, f"{title_alt}-um", "PoPlFeDa", "0")


def _gen_strong_blind(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``blind`` paradigm.

    Note:
        Matches Perl ``blind`` block.

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    base = f"{word.prefix}-{word.stem}"
    forms = [
        ("PoSgMaNo", "0", "0"),
        ("PoSgMaAc", "ne", "0"),
        ("PoSgMaAc", "0", "1"),
        ("PoSgMaGe", "es", "0"),
        ("PoSgMaDa", "um", "0"),
        ("PoSgMaDa", "0", "1"),
        ("PoSgMaIs", "e", "0"),
        ("PoSgNeNo", "0", "0"),
        ("PoSgNeAc", "0", "0"),
        ("PoSgNeGe", "es", "0"),
        ("PoSgNeDa", "um", "0"),
        ("PoSgNeDa", "0", "1"),
        ("PoSgNeIs", "e", "0"),
        ("PoSgFeNo", "0", "0"),
        ("PoSgFeAc", "e", "0"),
        ("PoSgFeGe", "re", "0"),
        ("PoSgFeGe", "0", "1"),
        ("PoSgFeDa", "re", "0"),
        ("PoSgFeDa", "0", "1"),
        ("PoPlMaNo", "e", "0"),
        ("PoPlMaNo", "0", "1"),
        ("PoPlMaAc", "e", "0"),
        ("PoPlMaAc", "0", "1"),
        ("PoPlMaGe", "ra", "0"),
        ("PoPlMaGe", "0", "1"),
        ("PoPlMaDa", "um", "0"),
        ("PoPlNeNo", "0", "0"),
        ("PoPlNeAc", "0", "0"),
        ("PoPlNeGe", "ra", "0"),
        ("PoPlNeGe", "0", "1"),
        ("PoPlNeDa", "um", "0"),
        ("PoPlFeNo", "a", "0"),
        ("PoPlFeNo", "e", "1"),
        ("PoPlFeAc", "a", "0"),
        ("PoPlFeAc", "e", "1"),
        ("PoPlFeGe", "ra", "0"),
        ("PoPlFeGe", "0", "1"),
        ("PoPlFeDa", "um", "0"),
    ]
    for func, ending, prob in forms:
        _adj_print(run_state, output_file, formhash, f"{base}-{ending}", func, prob)


def _gen_strong_heah_thweorh(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``hēah``/``þweorh`` paradigm (h-stem).

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    title_alt = f"{word.prefix}-{word.stem}"
    if "weorh" in paradigm:  # þweorh
        stem_alt = re.sub(r"e([ao])", "\u0113\\1", word.stem)  # e+ao -> ēa/ēo
        stem_alt = re.sub(r"([^\u0113])o", lambda m: f"{m.group(1)}ō", stem_alt)
        title_alt = f"{word.prefix}-{stem_alt}"
    title_alt = re.sub(r"h$", "", title_alt)
    forms = [
        ("PoSgMaNo", f"{title_alt}h-0", "0"),
        ("PoSgMaAc", f"{title_alt}-ne", "0"),
        ("PoSgMaAc", f"{title_alt}n-ne", "1"),
        ("PoSgMaGe", f"{title_alt}-s", "0"),
        ("PoSgMaGe", f"{title_alt}-es", "0"),
        ("PoSgMaDa", f"{title_alt}-m", "0"),
        ("PoSgMaDa", f"{title_alt}-um", "1"),
        ("PoSgMaIs", f"{title_alt}-0", "0"),
        ("PoSgNeNo", f"{title_alt}h-0", "0"),
        ("PoSgNeAc", f"{title_alt}h-0", "0"),
        ("PoSgNeGe", f"{title_alt}-s", "0"),
        ("PoSgNeGe", f"{title_alt}-es", "0"),
        ("PoSgNeDa", f"{title_alt}-m", "0"),
        ("PoSgNeDa", f"{title_alt}-um", "1"),
        ("PoSgNeIs", f"{title_alt}-0", "0"),
        ("PoSgFeNo", f"{title_alt}-0", "0"),
        ("PoSgFeAc", f"{title_alt}-0", "0"),
        ("PoSgFeGe", f"{title_alt}-re", "0"),
        ("PoSgFeGe", f"{title_alt}r-re", "1"),
        ("PoSgFeDa", f"{title_alt}-re", "0"),
        ("PoSgFeDa", f"{title_alt}r-re", "1"),
        ("PoPlMaNo", f"{title_alt}-0", "0"),
        ("PoPlMaAc", f"{title_alt}-0", "0"),
        ("PoPlMaGe", f"{title_alt}-ra", "0"),
        ("PoPlMaGe", f"{title_alt}r-ra", "1"),
        ("PoPlMaDa", f"{title_alt}-m", "0"),
        ("PoPlMaDa", f"{title_alt}-um", "1"),
        ("PoPlNeNo", f"{title_alt}-0", "0"),
        ("PoPlNeAc", f"{title_alt}-0", "0"),
        ("PoPlNeGe", f"{title_alt}-ra", "0"),
        ("PoPlNeGe", f"{title_alt}r-ra", "1"),
        ("PoPlNeDa", f"{title_alt}-m", "0"),
        ("PoPlNeDa", f"{title_alt}-um", "1"),
        ("PoPlFeNo", f"{title_alt}-0", "0"),
        ("PoPlFeAc", f"{title_alt}-0", "0"),
        ("PoPlFeGe", f"{title_alt}-ra", "0"),
        ("PoPlFeGe", f"{title_alt}r-ra", "1"),
        ("PoPlFeDa", f"{title_alt}-m", "0"),
        ("PoPlFeDa", f"{title_alt}-um", "1"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(run_state, output_file, formhash, form_parts, func, prob)


def _gen_strong_manig(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``māniġ`` paradigm.

    Note:
        Matches Perl māniġ block: no base-0 variants for PoSgMaAc, PoSgMaDa,
        PoSgNeDa, PoSgFeGe, PoSgFeDa, PoPlMaNo, PoPlMaAc, PoPlMaGe, PoPlNeGe,
        PoPlFeGe.

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    base = f"{word.prefix}-{word.stem}"
    forms = [
        ("PoSgMaNo", "0", "0"),
        ("PoSgMaAc", "ne", "0"),
        ("PoSgMaGe", "es", "0"),
        ("PoSgMaDa", "um", "0"),
        ("PoSgMaIs", "e", "0"),
        ("PoSgNeNo", "0", "0"),
        ("PoSgNeAc", "0", "0"),
        ("PoSgNeGe", "es", "0"),
        ("PoSgNeDa", "um", "0"),
        ("PoSgNeIs", "e", "0"),
        ("PoSgFeNo", "0", "0"),
        ("PoSgFeAc", "e", "0"),
        ("PoSgFeGe", "re", "0"),
        ("PoSgFeDa", "re", "0"),
        ("PoPlMaNo", "e", "0"),
        ("PoPlMaAc", "e", "0"),
        ("PoPlMaGe", "ra", "0"),
        ("PoPlMaDa", "um", "0"),
        ("PoPlNeNo", "0", "0"),
        ("PoPlNeAc", "0", "0"),
        ("PoPlNeGe", "ra", "0"),
        ("PoPlNeDa", "um", "0"),
        ("PoPlFeNo", "a", "0"),
        ("PoPlFeNo", "e", "1"),
        ("PoPlFeAc", "a", "0"),
        ("PoPlFeAc", "e", "1"),
        ("PoPlFeGe", "ra", "0"),
        ("PoPlFeDa", "um", "0"),
    ]
    for func, ending, prob in forms:
        _adj_print(run_state, output_file, formhash, f"{base}-{ending}", func, prob)


def _gen_strong_halig(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``hāliġ`` paradigm (ja-stem with syncope).

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    vowel_regex = OENormalizer.VOWEL
    title_alt = word.stem
    if word.papart != 1:
        title_alt = re.sub(f"({vowel_regex}.*){vowel_regex}(.*)$", r"\1\2", title_alt)
    title_alt = f"{word.prefix}-{title_alt}"
    base = f"{word.prefix}-{word.stem}"
    forms = [
        ("PoSgMaNo", f"{base}-0", "0"),
        ("PoSgMaAc", f"{base}-ne", "0"),
        ("PoSgMaGe", f"{title_alt}-es", "0"),
        ("PoSgMaGe", f"{base}-es", "1"),
        ("PoSgMaDa", f"{title_alt}-um", "0"),
        ("PoSgMaDa", f"{base}-um", "1"),
        ("PoSgMaIs", f"{title_alt}-e", "0"),
        ("PoSgMaIs", f"{base}-e", "1"),
        ("PoSgNeNo", f"{base}-0", "0"),
        ("PoSgNeAc", f"{base}-0", "0"),
        ("PoSgNeGe", f"{title_alt}-es", "0"),
        ("PoSgNeGe", f"{base}-es", "1"),
        ("PoSgNeDa", f"{title_alt}-um", "0"),
        ("PoSgNeDa", f"{base}-um", "1"),
        ("PoSgNeIs", f"{title_alt}-e", "0"),
        ("PoSgNeIs", f"{base}-e", "1"),
        ("PoSgFeNo", f"{base}-u", "0"),
        ("PoSgFeNo", f"{base}-o", "1"),
        ("PoSgFeAc", f"{title_alt}-e", "0"),
        ("PoSgFeAc", f"{base}-e", "1"),
        ("PoSgFeGe", f"{base}-re", "0"),
        ("PoSgFeDa", f"{base}-re", "0"),
        ("PoPlMaNo", f"{title_alt}-e", "0"),
        ("PoPlMaNo", f"{base}-e", "1"),
        ("PoPlMaAc", f"{title_alt}-e", "0"),
        ("PoPlMaAc", f"{base}-e", "1"),
        ("PoPlMaGe", f"{base}-ra", "0"),
        ("PoPlMaDa", f"{title_alt}-um", "0"),
        ("PoPlMaDa", f"{base}-um", "1"),
        ("PoPlNeNo", f"{base}-u", "0"),
        ("PoPlNeNo", f"{base}-o", "1"),
        ("PoPlNeAc", f"{base}-u", "0"),
        ("PoPlNeAc", f"{base}-o", "1"),
        ("PoPlNeGe", f"{base}-ra", "0"),
        ("PoPlNeDa", f"{title_alt}-um", "0"),
        ("PoPlNeDa", f"{base}-um", "1"),
        ("PoPlFeNo", f"{base}-a", "0"),
        ("PoPlFeNo", f"{base}-e", "1"),
        ("PoPlFeAc", f"{base}-a", "0"),
        ("PoPlFeAc", f"{base}-e", "1"),
        ("PoPlFeGe", f"{base}-ra", "0"),
        ("PoPlFeDa", f"{title_alt}-um", "0"),
        ("PoPlFeDa", f"{base}-um", "1"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(run_state, output_file, formhash, form_parts, func, prob)


def _gen_strong_wilde(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``wilde`` paradigm (i-stem, stem drops final e).

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    title_alt = re.sub(r"e$", "", word.stem)
    title_alt = f"{word.prefix}-{title_alt}"
    forms = [
        ("PoSgMaNo", f"{title_alt}-e", "0"),
        ("PoSgMaAc", f"{title_alt}-ne", "0"),
        ("PoSgMaGe", f"{title_alt}-es", "0"),
        ("PoSgMaDa", f"{title_alt}-um", "0"),
        ("PoSgMaIs", f"{title_alt}-e", "0"),
        ("PoSgNeNo", f"{title_alt}-e", "0"),
        ("PoSgNeAc", f"{title_alt}-e", "0"),
        ("PoSgNeGe", f"{title_alt}-es", "0"),
        ("PoSgNeDa", f"{title_alt}-um", "0"),
        ("PoSgNeIs", f"{title_alt}-e", "0"),
        ("PoSgFeNo", f"{title_alt}-u", "0"),
        ("PoSgFeNo", f"{title_alt}-o", "1"),
        ("PoSgFeAc", f"{title_alt}-e", "0"),
        ("PoSgFeGe", f"{title_alt}-re", "0"),
        ("PoSgFeDa", f"{title_alt}-re", "0"),
        ("PoPlMaNo", f"{title_alt}-e", "0"),
        ("PoPlMaAc", f"{title_alt}-e", "0"),
        ("PoPlMaGe", f"{title_alt}-ra", "0"),
        ("PoPlMaDa", f"{title_alt}-um", "0"),
        ("PoPlNeNo", f"{title_alt}-u", "0"),
        ("PoPlNeNo", f"{title_alt}-o", "1"),
        ("PoPlNeAc", f"{title_alt}-u", "0"),
        ("PoPlNeAc", f"{title_alt}-o", "1"),
        ("PoPlNeGe", f"{title_alt}-ra", "0"),
        ("PoPlNeDa", f"{title_alt}-um", "0"),
        ("PoPlFeNo", f"{title_alt}-a", "0"),
        ("PoPlFeNo", f"{title_alt}-e", "0"),
        ("PoPlFeAc", f"{title_alt}-a", "0"),
        ("PoPlFeAc", f"{title_alt}-e", "0"),
        ("PoPlFeGe", f"{title_alt}-ra", "0"),
        ("PoPlFeDa", f"{title_alt}-um", "0"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(run_state, output_file, formhash, form_parts, func, prob)


def _gen_strong_gearu(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``gearu`` paradigm (u-stem).

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    title_alt = re.sub(r".$", "", word.stem)
    title_alt = f"{word.prefix}-{title_alt}"
    forms = [
        ("PoSgMaNo", f"{title_alt}-u", "0"),
        ("PoSgMaNo", f"{title_alt}-o", "1"),
        ("PoSgMaAc", f"{title_alt}-one", "0"),
        ("PoSgMaGe", f"{title_alt}-wes", "0"),
        ("PoSgMaGe", f"{title_alt}-uwes", "1"),
        ("PoSgMaGe", f"{title_alt}-owes", "2"),
        ("PoSgMaDa", f"{title_alt}-wum", "0"),
        ("PoSgMaIs", f"{title_alt}-we", "0"),
        ("PoSgNeNo", f"{title_alt}-u", "0"),
        ("PoSgNeNo", f"{title_alt}-o", "1"),
        ("PoSgNeAc", f"{title_alt}-u", "0"),
        ("PoSgNeAc", f"{title_alt}-o", "1"),
        ("PoSgNeGe", f"{title_alt}-wes", "0"),
        ("PoSgNeDa", f"{title_alt}-wum", "0"),
        ("PoSgNeIs", f"{title_alt}-we", "0"),
        ("PoSgFeNo", f"{title_alt}-u", "0"),
        ("PoSgFeNo", f"{title_alt}-o", "1"),
        ("PoSgFeAc", f"{title_alt}-we", "0"),
        ("PoSgFeGe", f"{title_alt}-ore", "0"),
        ("PoSgFeDa", f"{title_alt}-ore", "0"),
        ("PoPlMaNo", f"{title_alt}-e", "0"),
        ("PoPlMaAc", f"{title_alt}-e", "0"),
        ("PoPlMaGe", f"{title_alt}-ora", "0"),
        ("PoPlMaDa", f"{title_alt}-wum", "0"),
        ("PoPlNeNo", f"{title_alt}-u", "0"),
        ("PoPlNeNo", f"{title_alt}-o", "1"),
        ("PoPlNeAc", f"{title_alt}-u", "0"),
        ("PoPlNeAc", f"{title_alt}-o", "1"),
        ("PoPlNeGe", f"{title_alt}-ora", "0"),
        ("PoPlNeDa", f"{title_alt}-wum", "0"),
        ("PoPlFeNo", f"{title_alt}-wa", "0"),
        ("PoPlFeNo", f"{title_alt}-we", "0"),
        ("PoPlFeAc", f"{title_alt}-wa", "0"),
        ("PoPlFeAc", f"{title_alt}-we", "0"),
        ("PoPlFeGe", f"{title_alt}-ora", "0"),
        ("PoPlFeDa", f"{title_alt}-wum", "0"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(run_state, output_file, formhash, form_parts, func, prob)


def _gen_weak(
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    paradigm: str,
) -> None:
    """
    Weak (definite) adjective forms for all adjectives.

    Args:
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.
        paradigm: The paradigm.

    Side Effects:
        Writes generated rows to the morphology output stream.

    """
    bt_id = f"{word.nid:06d}"
    title_array = _build_weak_title_array(word, paradigm)
    base_fh = {
        "title": word.title,
        "stem": word.stem,
        "BT": bt_id,
        "wordclass": "adjective",
        "class1": "weak",
        "paradigm": "blinda",
        "wright": word.wright,
        "var": "",
        "paraID": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }
    if word.papart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "past"
    if word.pspart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "present"
    if word.pronoun == 1:
        base_fh["wordclass"] = "pronoun"
    for y, base in enumerate(title_array):
        prob = str(y)
        run_state.perl_probability = int(prob)
        forms = [
            ("PoSgMaNo", f"{base}-a"),
            ("PoSgMaAc", f"{base}-an"),
            ("PoSgMaGe", f"{base}-an"),
            ("PoSgMaDa", f"{base}-an"),
            ("PoSgNeNo", f"{base}-e"),
            ("PoSgNeAc", f"{base}-e"),
            ("PoSgNeGe", f"{base}-an"),
            ("PoSgNeDa", f"{base}-an"),
            ("PoSgFeNo", f"{base}-e"),
            ("PoSgFeAc", f"{base}-an"),
            ("PoSgFeGe", f"{base}-an"),
            ("PoSgFeDa", f"{base}-an"),
            ("PoPlMaNo", f"{base}-an"),
            ("PoPlMaAc", f"{base}-an"),
            ("PoPlMaGe", f"{base}-ra"),
            ("PoPlMaGe", f"{base}-ena"),
            ("PoPlMaDa", f"{base}-um"),
            ("PoPlNeNo", f"{base}-an"),
            ("PoPlNeAc", f"{base}-an"),
            ("PoPlNeGe", f"{base}-ra"),
            ("PoPlNeGe", f"{base}-ena"),
            ("PoPlNeDa", f"{base}-um"),
            ("PoPlFeNo", f"{base}-an"),
            ("PoPlFeAc", f"{base}-an"),
            ("PoPlFeGe", f"{base}-ra"),
            ("PoPlFeGe", f"{base}-ena"),
            ("PoPlFeDa", f"{base}-um"),
        ]
        for i, (func, form_parts) in enumerate(forms):
            fh = base_fh.copy()
            fh["function"] = func
            # Perl: no probability before first -ena (index 15); prob+1 from
            # first -ena onwards
            fh["probability"] = str(int(prob) + 1) if i >= 15 else ""  # noqa: PLR2004
            fh["form"] = _form_from_parts(form_parts)
            fh["formParts"] = form_parts.replace("\n", "")
            print_one_form(run_state, fh, output_file)


def _build_comparative_title_array(
    word: Word,
    paradigm: str,
    use_perl_hash_order: bool,
    *,
    regular_stems: list[str] | None = None,
) -> tuple[list[str], str]:
    """
    Build ``title_array`` for comparative, which is used to generate the
    comparative forms.

    Returns:
        A tuple containing the title_array and the comparative suffix.

    Args:
        word: The word.
        paradigm: The paradigm.
        use_perl_hash_order: Whether to use Perl ``keys %hash`` ordering
            semantics (full-flow parity mode).

    Keyword Args:
        regular_stems: Pre-expanded regular stems when already computed for
            the same word.

    """
    stem = word.stem
    if stem == "g\u00f3d":
        title_array = [
            f"{word.prefix}-beter",
            f"{word.prefix}-betr",
            f"{word.prefix}-bettr",
            f"{word.prefix}-s\u00e9lr",
            f"{word.prefix}-selr",
        ]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )
    if stem == "yfel":
        title_array = [f"{word.prefix}-wiers"]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )
    if stem == "micel":
        title_array = [f"{word.prefix}-m\u00e1r"]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )
    if stem == "lytel":
        title_array = [f"{word.prefix}-l\u01fdss"]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )

    if regular_stems is None:
        regular_stems = _expand_regular_degree_stems(
            prefix=word.prefix,
            stem=stem,
            paradigm=paradigm,
            papart=word.papart,
            pspart=word.pspart,
            update_halig_title_alt=True,
        )
    return (
        _finalize_degree_titles(regular_stems, use_perl_hash_order=use_perl_hash_order),
        "r",
    )


def _shared_regular_degree_stems(
    word: Word,
    paradigm: str,
) -> tuple[list[str] | None, list[str] | None]:
    """
    Build regular comparative/superlative stems once when parity allows sharing.

    Args:
        word: Adjective entry being generated.
        paradigm: Selected adjective paradigm label.

    Returns:
        Tuple of ``(comparative_stems, superlative_stems)``. Each side is
        ``None`` when irregular degree stems make sharing impossible.

    """
    stem = word.stem
    if stem in {"g\u00f3d", "yfel", "micel", "lytel"}:
        return (None, None)

    need_halig_split = "hālig" in paradigm and (word.papart + word.pspart) == 0
    if need_halig_split:
        return (
            _expand_regular_degree_stems(
                prefix=word.prefix,
                stem=stem,
                paradigm=paradigm,
                papart=word.papart,
                pspart=word.pspart,
                update_halig_title_alt=True,
            ),
            _expand_regular_degree_stems(
                prefix=word.prefix,
                stem=stem,
                paradigm=paradigm,
                papart=word.papart,
                pspart=word.pspart,
                update_halig_title_alt=False,
            ),
        )

    shared = _expand_regular_degree_stems(
        prefix=word.prefix,
        stem=stem,
        paradigm=paradigm,
        papart=word.papart,
        pspart=word.pspart,
        update_halig_title_alt=False,
    )
    return (shared, shared)


def _gen_comparative(  # noqa: PLR0913
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    *,
    use_perl_hash_order: bool | None = None,
    regular_stems: list[str] | None = None,
) -> None:
    """
    Comparative (Co) weak forms for all adjectives.

    Note:
        This is for the ``weak`` block in Perl.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.

    Keyword Args:
        use_perl_hash_order: Optional parity ordering override.
        regular_stems: Pre-expanded regular stems when already computed for
            the same word.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    resolved_use_perl_hash_order = (
        len(word_pool.adjectives) > len(word_pool.words)
        if use_perl_hash_order is None
        else use_perl_hash_order
    )
    title_array, affix = _build_comparative_title_array(
        word,
        paradigm,
        resolved_use_perl_hash_order,
        regular_stems=regular_stems,
    )
    base_fh = _build_adjective_formhash(word, class1="weak", paradigm="blinda")
    _emit_weak_degree_forms(
        run_state,
        output_file,
        base_fh,
        title_array,
        degree_prefix="Co",
        affix=affix,
        prob_mode="abs_delta",
    )


def _build_superlative_title_array(
    word: Word,
    paradigm: str,
    use_perl_hash_order: bool,
    *,
    regular_stems: list[str] | None = None,
) -> tuple[list[str], str]:
    """
    Build ``title_array`` for superlative weak.

    Args:
        word: The word.
        paradigm: The paradigm.
        use_perl_hash_order: Whether to use Perl ``keys %hash`` ordering
            semantics (full-flow parity mode).

    Keyword Args:
        regular_stems: Pre-expanded regular stems when already computed for
            the same word.

    Returns:
        A tuple containing the title array and the ``s`` suffix.

    """
    stem = word.stem
    if stem == "g\u00f3d":
        title_array = [
            f"{word.prefix}-betst",
            f"{word.prefix}-betest",
            f"{word.prefix}-best",
            f"{word.prefix}-s\u00e9lest",
        ]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )
    if stem == "yfel":
        title_array = [f"{word.prefix}-wierrest", f"{word.prefix}-wyrst"]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )
    if stem == "micel":
        title_array = [f"{word.prefix}-m\u01fdst"]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )
    if stem == "lytel":
        title_array = [f"{word.prefix}-l\u01fdst"]
        return (
            _finalize_degree_titles(
                title_array,
                use_perl_hash_order=use_perl_hash_order,
            ),
            "0",
        )

    if regular_stems is None:
        regular_stems = _expand_regular_degree_stems(
            prefix=word.prefix,
            stem=stem,
            paradigm=paradigm,
            papart=word.papart,
            pspart=word.pspart,
            update_halig_title_alt=False,
        )
    return (
        _finalize_degree_titles(regular_stems, use_perl_hash_order=use_perl_hash_order),
        "ost",
    )


def _gen_superlative(  # noqa: PLR0913
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    word: Word,
    *,
    use_perl_hash_order: bool | None = None,
    regular_stems: list[str] | None = None,
) -> None:
    """
    Generate superlative adjective forms: weak (Sp) forms then strong (Sp)
    forms.

    Note:
        Matches Perl ``superlative`` block.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: The output file handle.
        word: The word.

    Keyword Args:
        use_perl_hash_order: Optional parity ordering override.
        regular_stems: Pre-expanded regular stems when already computed for
            the same word.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    resolved_use_perl_hash_order = (
        len(word_pool.adjectives) > len(word_pool.words)
        if use_perl_hash_order is None
        else use_perl_hash_order
    )
    title_array, affix = _build_superlative_title_array(
        word,
        paradigm,
        resolved_use_perl_hash_order,
        regular_stems=regular_stems,
    )
    weak_fh = _build_adjective_formhash(word, class1="weak", paradigm="blinda")
    _emit_weak_degree_forms(
        run_state,
        output_file,
        weak_fh,
        title_array,
        degree_prefix="Sp",
        affix=affix,
        prob_mode="abs_delta",
    )
    strong_fh = _build_adjective_formhash(
        word,
        class1="strong",
        paradigm=paradigm,
    )
    _emit_superlative_strong_forms(
        run_state,
        output_file,
        strong_fh,
        title_array,
        affix=affix,
    )


def generate_adjforms(  # noqa: PLR0912
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Generate adjective forms.

    Note:
        Port of Perl ``generate_adjforms``.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: The output file handle.

    Keyword Args:
        progress: Optional live progress coordinator.

    Side Effects:
        Writes generated rows to the morphology output stream. Sets
        ``run_state.enable_num_probability_carry`` so a later
        ``generate_numforms`` stage carries the shared probability forward.

    """
    # Perl main flow calls generate_adjforms on a mutable adjective pool that
    # starts as all words and then gets additional generated participles.
    words = [
        w
        for w in word_pool.adjectives
        if (w.adjective == 1 or (w.pspart + w.papart) > 0) and w.numeral != 1
    ]
    use_perl_hash_order = len(word_pool.adjectives) > len(word_pool.words)
    for word in words:
        if progress is not None:
            progress.advance(
                MorphologyStage.ADJECTIVES,
                lemma=word.title,
                wright=word.wright,
                forms_written=run_state.output_counter,
            )
        paradigm = (
            word.adj_paradigm[0]
            if word.adj_paradigm
            else ("wilde" if (word.pspart or word.papart) else "")
        )
        bt_id = f"{word.nid:06d}"
        formhash = {
            "title": word.title,
            "stem": word.stem,
            "BT": bt_id,
            "wordclass": "adjective",
            "class1": "strong",
            "paradigm": paradigm,
            "wright": word.wright,
            "var": "",
            "paraID": "",
            "class2": "",
            "class3": "",
            "comment": "",
        }
        if word.pronoun == 1:
            formhash["wordclass"] = "pronoun"
        # Manig: papart + short stem -> override paradigm
        if "manig" in paradigm or (
            word.papart == 1 and not OENormalizer.stem_length(word.stem)
        ):
            if word.papart == 1:
                word.adj_paradigm = ["manig"]
                formhash["wordclass"] = "participle"
                formhash["class2"] = "past"
                formhash["paradigm"] = "manig"
            _gen_strong_manig(run_state, output_file, word, formhash)
        elif (
            "hālig" in paradigm
            or (word.papart == 1 and OENormalizer.stem_length(word.stem))
        ):
            if word.papart == 1:
                word.adj_paradigm = ["hālig"]
                formhash["wordclass"] = "participle"
                formhash["class2"] = "past"
                formhash["paradigm"] = "halig"
            _gen_strong_halig(run_state, output_file, word, formhash)
        elif "wilde" in paradigm or word.pspart == 1:
            if word.pspart == 1:
                word.adj_paradigm = ["wilde"]
                formhash["wordclass"] = "participle"
                formhash["class2"] = "present"
                formhash["paradigm"] = "wilde"
            _gen_strong_wilde(run_state, output_file, word, formhash)
        elif re.search(r"gl\u00e6d|glæd|til", paradigm, re.IGNORECASE):
            _gen_strong_glaed_til(run_state, output_file, word, formhash)
        elif "blind" in paradigm:
            _gen_strong_blind(run_state, output_file, word, formhash)
        elif re.search(r"hēah|weorh", paradigm):
            _gen_strong_heah_thweorh(run_state, output_file, word, formhash)
        elif "gearu" in paradigm:
            _gen_strong_gearu(run_state, output_file, word, formhash)
        # else: no strong paradigm match, but still generate weak forms
        _gen_weak(run_state, output_file, word, paradigm)

        # Comparative and Superlative (only for adjectives, not numerals or pronouns)
        if word.numeral == 0 and word.pronoun == 0:
            comp_stems, sup_stems = _shared_regular_degree_stems(word, paradigm)
            _gen_comparative(
                word_pool,
                run_state,
                output_file,
                word,
                use_perl_hash_order=use_perl_hash_order,
                regular_stems=comp_stems,
            )
            _gen_superlative(
                word_pool,
                run_state,
                output_file,
                word,
                use_perl_hash_order=use_perl_hash_order,
                regular_stems=sup_stems,
            )

    # Full-flow create_dict31 behavior carries a shared $probability into
    # generate_numforms after adjective generation has run.
    run_state.enable_num_probability_carry = True
