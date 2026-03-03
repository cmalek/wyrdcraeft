"""Weak-verb infinitive derivation helpers for morphology generation."""

from __future__ import annotations

import re
from collections.abc import Callable

from ..text_utils import OENormalizer
from .sound_changes import derive_papt_sound_changed_forms

#: Callback signature for one weak-form emission operation.
WeakFormEmitter = Callable[
    [str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one weak-form emission without a dental component.
WeakSimpleFormEmitter = Callable[[str, str, str | int | None], None]
#: Callback signature for one weak-form sound-change emission operation.
WeakSoundEmitter = Callable[[str, str, str | int | None, int], None]
#: Callback signature for one weak manual-form emission operation.
WeakManualEmitter = Callable[[str, str, str, str | int | None], None]


def has_perl_inf_vowel_ending(fp_base: str) -> bool:
    """
    Check whether a form-parts base ends in a Perl-style vowel segment.

    Side Effects:
        None.

    Args:
        fp_base: Form-parts base string.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``True`` when ``fp_base`` matches the Perl vowel-ending pattern.

    """
    return bool(re.search(r"[æaeyouÆAEIYOUǣāēīȳōūǢĀĒĪȲŌŪ][0-]*?$", fp_base))


def has_regex_vowel_ending(fp_base: str) -> bool:
    """
    Check whether a form-parts base ends with the normalized vowel regex.

    Side Effects:
        None.

    Args:
        fp_base: Form-parts base string.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``True`` when ``fp_base`` ends in a vowel by ``OENormalizer`` rules.

    """
    return bool(
        re.search(f"{OENormalizer.VOWEL_REGEX.pattern}$", fp_base, re.IGNORECASE)
    )


def emit_weak_derived_from_inf_general(  # noqa: PLR0913
    *,
    original_ending: str,
    iending: str,
    probability: str | int | None,
    probability_plus_one: int,
    perl_inf_vowel_end: bool,
    regex_vowel_end: bool,
    emit_form: WeakFormEmitter,
) -> str:
    """
    Emit weak-verb forms derived from infinitives for the general class2 branch.

    Side Effects:
        Writes generated rows through ``emit_form``.

    Args:
        original_ending: Source infinitive ending from the paradigm.
        iending: Derived ``i``-prefixed dental component.
        probability: Base probability scalar for principal forms.
        probability_plus_one: Incremented probability scalar.
        perl_inf_vowel_end: Perl-style vowel-ending predicate.
        regex_vowel_end: Regex-based vowel-ending predicate.
        emit_form: Callback that emits one generated form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Final participle ``formParts`` string used for adjective derivation.

    """
    emit_form(None, original_ending, "if", probability)
    if perl_inf_vowel_end:
        emit_form(None, "n", "if", probability)

    emit_form(iending, "anne", "IdIf", probability)
    emit_form(iending, "enne", "IdIf", probability)
    if perl_inf_vowel_end:
        emit_form(iending, "nne", "IdIf", probability)

    emit_form(iending, "e", "PsInSg1", probability)
    emit_form(iending, "u", "PsInSg1", probability_plus_one)
    emit_form(iending, "o", "PsInSg1", probability_plus_one)
    emit_form(iending, "æ", "PsInSg1", probability_plus_one)
    if perl_inf_vowel_end:
        emit_form(None, "0", "PsInSg1", probability)

    emit_form(iending, "aþ", "PsInPl", probability)
    emit_form(iending, "eþ", "PsInPl", probability_plus_one)
    emit_form(iending, "es", "PsInPl", probability_plus_one)
    emit_form(iending, "as", "PsInPl", probability_plus_one)
    if perl_inf_vowel_end:
        emit_form(iending, "þ", "PsInPl", probability)

    emit_form(iending, "e", "PsSuSg", probability)
    if perl_inf_vowel_end:
        emit_form(None, "0", "PsSuSg", probability)

    emit_form(iending, "en", "PsSuPl", probability)
    if regex_vowel_end:
        emit_form(iending, "n", "PsSuPl", probability)

    emit_form(iending, "aþ", "ImPl", probability)
    if perl_inf_vowel_end:
        emit_form(None, "þ", "ImPl", probability)

    _, participle_form_parts = emit_form(iending, "ende", "PsPt", probability)
    if perl_inf_vowel_end:
        _, participle_form_parts = emit_form(iending, "nde", "PsPt", probability)
    return participle_form_parts


def emit_weak_derived_from_inf_class2_variant(
    *,
    iending: str,
    perl_inf_vowel_end: bool,
    regex_vowel_end: bool,
    emit_form: WeakFormEmitter,
) -> str:
    """
    Emit weak-verb forms for one variant of the class2-special infinitive branch.

    Side Effects:
        Writes generated rows through ``emit_form``.

    Args:
        iending: Class2 variant dental component (``ig``, ``ige``, or ``""``).
        perl_inf_vowel_end: Perl-style vowel-ending predicate.
        regex_vowel_end: Regex-based vowel-ending predicate.
        emit_form: Callback that emits one generated form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Final participle ``formParts`` string used for adjective derivation.

    """
    prob_c2 = 0

    if iending != "":
        emit_form(iending, "an", "if", prob_c2)
        if perl_inf_vowel_end:
            emit_form(None, "n", "if", prob_c2)
    elif perl_inf_vowel_end:
        emit_form(None, "n", "if", prob_c2)

    emit_form(iending, "anne", "IdIf", prob_c2)
    emit_form(iending, "enne", "IdIf", prob_c2)
    if perl_inf_vowel_end:
        emit_form(iending, "nne", "IdIf", prob_c2)

    emit_form(iending, "a", "ImSg", prob_c2)
    if perl_inf_vowel_end:
        emit_form(None, "0", "ImSg", prob_c2)

    emit_form(iending, "e", "PsInSg1", prob_c2)
    emit_form(iending, "u", "PsInSg1", prob_c2 + 1)
    emit_form(iending, "o", "PsInSg1", prob_c2 + 1)
    emit_form(iending, "æ", "PsInSg1", prob_c2 + 1)
    if perl_inf_vowel_end:
        emit_form(None, "0", "PsInSg1", prob_c2)

    emit_form(iending, "aþ", "PsInPl", prob_c2)
    emit_form(iending, "eþ", "PsInPl", prob_c2 + 1)
    emit_form(iending, "es", "PsInPl", prob_c2 + 1)
    emit_form(iending, "as", "PsInPl", prob_c2 + 1)
    if perl_inf_vowel_end:
        emit_form(iending, "þ", "PsInPl", prob_c2)

    emit_form(iending, "e", "PsSuSg", prob_c2)
    if perl_inf_vowel_end:
        emit_form(None, "0", "PsSuSg", prob_c2)

    emit_form(iending, "en", "PsSuPl", prob_c2)
    if regex_vowel_end:
        emit_form(iending, "n", "PsSuPl", prob_c2)

    emit_form(iending, "aþ", "ImPl", prob_c2)
    if perl_inf_vowel_end:
        emit_form(None, "þ", "ImPl", prob_c2)

    _, participle_form_parts = emit_form(iending, "ende", "PsPt", prob_c2)
    if perl_inf_vowel_end:
        _, participle_form_parts = emit_form(iending, "nde", "PsPt", prob_c2)
    return participle_form_parts


def emit_weak_derived_from_psinsg2(
    *,
    probability: str | int | None,
    probability_plus_one: int,
    emit_form: WeakSimpleFormEmitter,
    emit_sound: WeakSoundEmitter,
) -> None:
    """
    Emit weak-verb forms derived from the ``PsInSg2`` principal part.

    Side Effects:
        Writes generated rows through ``emit_form`` and ``emit_sound``.

    Args:
        probability: Base probability scalar.
        probability_plus_one: Incremented probability scalar.
        emit_form: Callback that emits one generated form.
        emit_sound: Callback that emits one sound-change branch.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``None``.

    """
    emit_form("est", "PsInSg2", probability_plus_one)
    emit_form("es", "PsInSg2", probability_plus_one)
    emit_form("ist", "PsInSg2", probability_plus_one)
    emit_form("s", "PsInSg2", probability_plus_one)

    emit_sound("st", "PsInSg2", probability, 1)

    emit_form("eþ", "PsInSg3", probability_plus_one)
    emit_form("ieþ", "PsInSg3", probability_plus_one)
    emit_form("iþ", "PsInSg3", probability_plus_one)

    emit_sound("þ", "PsInSg3", probability_plus_one, 0)

    emit_form("e", "ImSg", probability)
    emit_form("ie", "ImSg", probability)
    emit_form("0", "ImSg", probability)


def emit_weak_derived_from_painsg1_variant(  # noqa: PLR0913
    *,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel_simple: str,
    boundary: str,
    dental: str,
    probability: int,
    emit_form: WeakSimpleFormEmitter,
    emit_manual: WeakManualEmitter,
) -> str:
    """
    Emit one weak-verb ``PaInSg1``-derived vowel variant sequence.

    Side Effects:
        Writes generated rows through ``emit_form`` and ``emit_manual``.

    Args:
        prefix: Word prefix component.
        pre_vowel: Pre-vowel stem segment.
        vowel: Active vowel for this variant.
        post_vowel_simple: Simplified post-vowel segment.
        boundary: Boundary consonant segment.
        dental: Dental segment.
        probability: Base probability for this variant.
        emit_form: Callback that emits one generated inflection form.
        emit_manual: Callback that emits one manual-form row.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``formParts`` string used for participle adjective derivation.

    """
    emit_form("e", "PaInSg1", probability)

    emit_form("est", "PaInSg2", probability)
    emit_form("es", "PaInSg2", probability + 1)

    emit_form("e", "PaInSg3", probability)
    emit_form("on", "PaInPl", probability)
    emit_form("e", "PaSuSg", probability)
    emit_form("en", "PaSuPl", probability)

    form_parts = f"{prefix}-{pre_vowel}-{vowel}-{post_vowel_simple}-{boundary}-{dental}"
    form = form_parts.replace("0", "").replace("-", "")
    emit_manual(form, form_parts, "PaPt", probability)

    for sound_changed_form in derive_papt_sound_changed_forms(form):
        emit_manual(sound_changed_form, form_parts, "PaPt", probability + 1)

    return form_parts
