"""Paradigm traversal helpers for verb-generation orchestration."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from functools import partial

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
    _ParadigmVariantDispatchContext,
    _VariantPartDispatchContext,
)
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .scalar_utils import nz as _nz

#: Callback used when dispatching one variant context.
VariantDispatcher = Callable[
    [ParadigmVariant, dict[str, str], str, str, str],
    None,
]
#: Callback used when dispatching one part context.
PartDispatcher = Callable[[ParadigmPart, dict[str, str], str, str, str], None]
#: Callback used when processing one fully-expanded variant traversal.
VariantProcessor = Callable[
    [Word, VerbParadigm, ParadigmVariant, dict[str, str], str, str, str],
    None,
]
#: Callback used when processing one fully-expanded part traversal.
PartProcessor = Callable[
    [
        Word,
        VerbParadigm,
        ParadigmVariant,
        ParadigmPart,
        dict[str, str],
        str,
        str,
        str,
    ],
    None,
]
#: Callback used to derive shared stem segments for one paradigm part.
PartStemSegmentDeriver = Callable[
    [Word, ParadigmPart, str],
    tuple[str, str, str, str],
]
#: Callback used for strong-verb part generation.
StrongPartGenerator = Callable[
    [dict[str, str], Word, ParadigmPart, str, str, str, str, int],
    None,
]
#: Callback used for weak-verb part generation.
WeakPartGenerator = Callable[
    [dict[str, str], Word, ParadigmPart, str, str, str, str, int, str, str, str],
    None,
]


def build_verb_formhash_base(word: Word, vp: VerbParadigm) -> dict[str, str]:
    """
    Build the base metadata hash used for all emitted verb forms.

    Args:
        word: Lexeme record currently being generated.
        vp: Verb paradigm record currently being generated.

    Returns:
        Base form hash copied per variant and then extended per emitted row.

    """
    return {
        "title": word.title,
        "stem": word.stem,
        "BT": f"{word.nid:06d}",
        "wordclass": "verb",
        "class1": vp.type,
        "class2": vp.class_,
        "class3": vp.subclass,
        "paradigm": vp.title,
        "paraID": vp.ID,
        "wright": word.wright,
        "comment": "",
    }


def derive_paradigm_seed_vowels(vp: VerbParadigm) -> tuple[str, str, str]:
    """
    Derive boundary and exemplar vowels from the first paradigm variant.

    Args:
        vp: Verb paradigm record currently being generated.

    Returns:
        Three-item tuple ``(boundary_inf, vowel_inf, vowel_pa)`` used by branch
        orchestration to match legacy ordering/probability behavior.

    """
    variant0 = vp.variants[0]
    inf_part = variant0.parts.get("if")
    painsg1_part = variant0.parts.get("painsg1")
    boundary_inf = _nz(inf_part.boundary if inf_part else "")
    vowel_inf = _nz(inf_part.vowel if inf_part else "")
    vowel_pa = _nz(painsg1_part.vowel if painsg1_part else "")
    return boundary_inf, vowel_inf, vowel_pa


def derive_part_prefix(word: Word, item: ParadigmPart) -> str:
    """
    Derive the effective prefix for one emitted paradigm part.

    Args:
        word: Active lexeme record being generated.
        item: Active paradigm part.

    Returns:
        Prefix segment used by downstream form assembly.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both model prefixed compounds as
        compositional segments; this preserves legacy prefix join behavior.

    """
    prefix = word.prefix
    if prefix != item.prefix:
        prefix = f"{prefix}-{item.prefix}"
    return prefix


def derive_part_post_vowel(
    word: Word, item: ParadigmPart, boundary_inf: str
) -> str:
    """
    Derive the post-vowel stem segment for one paradigm part.

    Args:
        word: Active lexeme record being generated.
        item: Active paradigm part.
        boundary_inf: Infinitive boundary captured from variant ``0``.

    Returns:
        Post-vowel segment used by downstream form assembly.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) describe vowel/consonant boundary
        segmentation in strong/weak paradigms; this keeps the legacy regex
        extraction unchanged.

    """
    if not _nz(item.post_vowel):
        return ""

    if boundary_inf:
        pattern = (
            f"{OENormalizer.VOWEL_REGEX.pattern}{OENormalizer.VOWEL_REGEX.pattern}*?"
            f"({OENormalizer.CONSONANT_REGEX.pattern}.*?){re.escape(boundary_inf)}"
            f"{OENormalizer.VOWEL_REGEX.pattern}+n$"
        )
    else:
        pattern = (
            f"{OENormalizer.VOWEL_REGEX.pattern}{OENormalizer.VOWEL_REGEX.pattern}*?"
            f"({OENormalizer.CONSONANT_REGEX.pattern}.*?){OENormalizer.VOWEL_REGEX.pattern}+n$"
        )
    match = re.search(pattern, word.stem)
    return match.group(1) if match else ""


def derive_part_pre_vowel(word: Word) -> tuple[str, str]:
    """
    Derive stem segments before and at the active root vowel.

    Args:
        word: Active lexeme record being generated.

    Returns:
        Two-item tuple ``(pre_vowel, vowel)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both rely on stable stem-vowel
        identification; this preserves the legacy extraction regex.

    """
    pattern = (
        f"^({OENormalizer.VOWEL_REGEX.pattern}*?.*?)"
        f"({OENormalizer.VOWEL_REGEX.pattern}{{1,2}})"
    )
    match = re.search(pattern, word.stem)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def derive_part_stem_segments(
    word: Word,
    item: ParadigmPart,
    boundary_inf: str,
) -> tuple[str, str, str, str]:
    """
    Derive stem segments consumed by strong and weak part generators.

    Args:
        word: Active lexeme record being generated.
        item: Active paradigm part.
        boundary_inf: Infinitive boundary captured from variant ``0``.

    Returns:
        Four-item tuple ``(prefix, pre_vowel, vowel, post_vowel)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) describe segment-level stem parsing;
        this orchestration wrapper preserves the same deterministic slot order.

    """
    prefix = derive_part_prefix(word, item)
    post_vowel = derive_part_post_vowel(word, item, boundary_inf)
    pre_vowel, actual_vowel = derive_part_pre_vowel(word)
    return prefix, pre_vowel, actual_vowel, post_vowel


def process_paradigm(
    *,
    word: Word,
    vp: VerbParadigm,
    on_variant: VariantProcessor,
) -> None:
    """
    Process one paradigm and expand each variant into full traversal context.

    Side Effects:
        Invokes ``on_variant`` once per variant in source order.

    Args:
        word: Lexeme record currently being generated.
        vp: Verb paradigm record currently being generated.
        on_variant: Callback receiving the expanded variant traversal payload.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both describe paradigm generation as
        ordered traversal over variants and parts; this helper keeps that same
        human-readable walk while moving the orchestration shell out of
        ``common.py``.

    """
    formhash_base = build_verb_formhash_base(word, vp)
    boundary_inf, vowel_inf, vowel_pa = derive_paradigm_seed_vowels(vp)
    context = _ParadigmVariantDispatchContext(word=word, paradigm=vp)
    dispatch_paradigm_variants(
        variants=vp.variants,
        formhash_base=formhash_base,
        boundary_inf=boundary_inf,
        vowel_inf=vowel_inf,
        vowel_pa=vowel_pa,
        on_variant=partial(
            dispatch_paradigm_variant_context,
            context=context,
            on_variant=on_variant,
        ),
    )


def dispatch_paradigm_variant_context(  # noqa: PLR0913
    variant: ParadigmVariant,
    formhash_base: dict[str, str],
    boundary_inf: str,
    vowel_inf: str,
    vowel_pa: str,
    *,
    context: _ParadigmVariantDispatchContext,
    on_variant: VariantProcessor,
) -> None:
    """
    Expand one variant callback into the full paradigm traversal payload.

    Side Effects:
        Invokes ``on_variant`` with word/paradigm context preserved.

    Args:
        variant: Active variant being dispatched.
        formhash_base: Variant-scoped form hash payload.
        boundary_inf: Infinitive boundary from variant ``0``.
        vowel_inf: Infinitive vowel from variant ``0``.
        vowel_pa: Preterite singular vowel from variant ``0``.

    Keyword Args:
        context: Shared paradigm-level dispatch context.
        on_variant: Callback receiving the expanded traversal payload.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both present paradigm traversal as a
        stable sequence over the same lexical entry and paradigm; this helper
        keeps that context intact while handing each variant off to the next
        stage.

    """
    on_variant(
        context.word,
        context.paradigm,
        variant,
        formhash_base,
        boundary_inf,
        vowel_inf,
        vowel_pa,
    )


def process_variant(  # noqa: PLR0913
    *,
    word: Word,
    vp: VerbParadigm,
    variant: ParadigmVariant,
    formhash_var: dict[str, str],
    boundary_inf: str,
    vowel_inf: str,
    vowel_pa: str,
    on_part: PartProcessor,
) -> None:
    """
    Process one variant and expand each part into full traversal context.

    Side Effects:
        Invokes ``on_part`` once per part in source order.

    Args:
        word: Lexeme record currently being generated.
        vp: Verb paradigm record currently being generated.
        variant: Active paradigm variant.
        formhash_var: Variant-scoped form hash payload.
        boundary_inf: Infinitive boundary from variant ``0``.
        vowel_inf: Infinitive vowel from variant ``0``.
        vowel_pa: Preterite singular vowel from variant ``0``.
        on_part: Callback receiving the expanded part traversal payload.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both describe each variant as an
        ordered set of principal or derived parts; this helper preserves that
        exact traversal order while moving the dispatch shell into
        ``paradigm_flow.py``.

    """
    context = _VariantPartDispatchContext(
        word=word,
        paradigm=vp,
        variant=variant,
    )
    dispatch_variant_parts(
        variant=variant,
        formhash_var=formhash_var,
        boundary_inf=boundary_inf,
        vowel_inf=vowel_inf,
        vowel_pa=vowel_pa,
        on_part=partial(
            dispatch_variant_part_context,
            context=context,
            on_part=on_part,
        ),
    )


def dispatch_variant_part_context(  # noqa: PLR0913
    item: ParadigmPart,
    formhash_var: dict[str, str],
    boundary_inf: str,
    vowel_inf: str,
    vowel_pa: str,
    *,
    context: _VariantPartDispatchContext,
    on_part: PartProcessor,
) -> None:
    """
    Expand one part callback into the full variant traversal payload.

    Side Effects:
        Invokes ``on_part`` with word/paradigm/variant context preserved.

    Args:
        item: Active part being dispatched.
        formhash_var: Variant-scoped form hash payload.
        boundary_inf: Infinitive boundary from variant ``0``.
        vowel_inf: Infinitive vowel from variant ``0``.
        vowel_pa: Preterite singular vowel from variant ``0``.

    Keyword Args:
        context: Shared variant-level dispatch context.
        on_part: Callback receiving the expanded traversal payload.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both keep each part attached to its
        owning variant; this helper simply carries that stable context forward
        without changing emission order or morphology decisions.

    """
    on_part(
        context.word,
        context.paradigm,
        context.variant,
        item,
        formhash_var,
        boundary_inf,
        vowel_inf,
        vowel_pa,
    )


def process_part(  # noqa: PLR0913
    *,
    word: Word,
    vp: VerbParadigm,
    variant: ParadigmVariant,
    item: ParadigmPart,
    formhash_var: dict[str, str],
    boundary_inf: str,
    vowel_inf: str,
    vowel_pa: str,
    derive_part_stem_segments: PartStemSegmentDeriver,
    generate_strong_verb_parts: StrongPartGenerator,
    generate_weak_verb_parts: WeakPartGenerator,
) -> None:
    """
    Process one part and route it into strong or weak generation flow.

    Side Effects:
        Invokes the supplied strong or weak generator exactly once.

    Args:
        word: Lexeme record currently being generated.
        vp: Verb paradigm record currently being generated.
        variant: Active paradigm variant.
        item: Active paradigm part.
        formhash_var: Variant-scoped form hash payload.
        boundary_inf: Infinitive boundary from variant ``0``.
        vowel_inf: Infinitive vowel from variant ``0``.
        vowel_pa: Preterite singular vowel from variant ``0``.
        derive_part_stem_segments: Callback deriving shared stem slots.
        generate_strong_verb_parts: Callback handling strong-verb branches.
        generate_weak_verb_parts: Callback handling weak-verb branches.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) both organize inflectional behavior
        around stem segments plus strong-vs-weak branch families; in plain
        terms, this helper computes the shared stem pieces once and then sends
        the part down the same legacy branch it would have taken before.

    """
    prefix, pre_vowel, actual_vowel, post_vowel = derive_part_stem_segments(
        word,
        item,
        boundary_inf,
    )

    if vp.type == "s":
        generate_strong_verb_parts(
            formhash_var,
            word,
            item,
            prefix,
            pre_vowel,
            actual_vowel,
            post_vowel,
            variant.variant_id,
        )
        return

    generate_weak_verb_parts(
        formhash_var,
        word,
        item,
        prefix,
        pre_vowel,
        actual_vowel,
        post_vowel,
        variant.variant_id,
        vp.ID,
        vowel_inf,
        vowel_pa,
    )


def dispatch_paradigm_variants(  # noqa: PLR0913
    *,
    variants: Sequence[ParadigmVariant],
    formhash_base: dict[str, str],
    boundary_inf: str,
    vowel_inf: str,
    vowel_pa: str,
    on_variant: VariantDispatcher,
) -> None:
    """
    Dispatch each variant in paradigm order with a per-variant hash copy.

    Side Effects:
        Invokes ``on_variant`` once per variant.

    Args:
        variants: Ordered variants to process.
        formhash_base: Base form hash to copy for each variant.
        boundary_inf: Exemplar infinitive boundary.
        vowel_inf: Exemplar infinitive vowel.
        vowel_pa: Exemplar preterite singular vowel.
        on_variant: Callback receiving one variant context.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    for variant in variants:
        formhash_var = formhash_base.copy()
        formhash_var["var"] = str(variant.variant_id)
        on_variant(
            variant,
            formhash_var,
            boundary_inf,
            vowel_inf,
            vowel_pa,
        )


def dispatch_variant_parts(  # noqa: PLR0913
    *,
    variant: ParadigmVariant,
    formhash_var: dict[str, str],
    boundary_inf: str,
    vowel_inf: str,
    vowel_pa: str,
    on_part: PartDispatcher,
) -> None:
    """
    Dispatch each part of one variant in source order.

    Side Effects:
        Invokes ``on_part`` once per part entry.

    Args:
        variant: Active paradigm variant.
        formhash_var: Variant-scoped form hash.
        boundary_inf: Exemplar infinitive boundary.
        vowel_inf: Exemplar infinitive vowel.
        vowel_pa: Exemplar preterite singular vowel.
        on_part: Callback receiving one part context.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    for item in variant.parts.values():
        on_part(item, formhash_var, boundary_inf, vowel_inf, vowel_pa)
