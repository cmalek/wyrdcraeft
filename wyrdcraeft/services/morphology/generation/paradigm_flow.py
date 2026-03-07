"""Paradigm traversal helpers for verb-generation orchestration."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
)

#: Callback used when dispatching one variant context.
VariantDispatcher = Callable[
    [ParadigmVariant, dict[str, str], str, str, str],
    None,
]
#: Callback used when dispatching one part context.
PartDispatcher = Callable[[ParadigmPart, dict[str, str], str, str, str], None]


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


def _nz(val: str | int | None) -> str:
    """
    Treat ``None`` and Perl-falsy ``0`` values as empty string.

    Args:
        val: Raw scalar value from a parsed paradigm slot.

    Returns:
        Empty string for ``None``/``0``; otherwise stringified ``val``.

    """
    if val is None or val in {"0", 0}:
        return ""
    return str(val)
