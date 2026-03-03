"""Weak-verb infinitive derivation helpers for morphology generation."""

from __future__ import annotations

import re
from collections.abc import Callable

from ..text_utils import OENormalizer

#: Callback signature for one weak-form emission operation.
WeakFormEmitter = Callable[
    [str | None, str, str, str | int | None],
    tuple[str, str],
]


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
