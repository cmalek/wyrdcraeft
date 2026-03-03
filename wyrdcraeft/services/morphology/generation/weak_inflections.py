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
#: Callback signature for one weak principal-form emission operation.
WeakPrincipalEmitter = Callable[
    [str, str, str, str, str, str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for attaching a derived participle form.
WeakParticipleSink = Callable[[str], None]
#: Callback signature for one derived-branch dispatch action.
WeakBranchAction = Callable[[], None]
#: Lower bound (exclusive) for using raw item-shape weak forms.
WEAK_ITEM_SHAPE_MIN_ID: int = 88
#: Upper bound (exclusive) for using raw item-shape weak forms.
WEAK_ITEM_SHAPE_MAX_ID: int = 93


def has_perl_inf_vowel_ending(fp_base: str) -> bool:
    """
    Check whether a form-parts base ends in a Perl-style vowel segment.

    Side Effects:
        None.

    Args:
        fp_base: Form-parts base string.

    Keyword Args:
        This function does not define keyword-only arguments.

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


def emit_weak_derived_from_inf_by_class2(  # noqa: PLR0913
    *,
    class2: str | None,
    original_ending: str,
    probability: str | int | None,
    probability_plus_one: int,
    perl_inf_vowel_end: bool,
    regex_vowel_end: bool,
    emit_form: WeakFormEmitter,
    on_participle: WeakParticipleSink,
) -> None:
    """
    Emit weak infinitive-derived branches according to ``class2`` routing.

    Side Effects:
        Emits generated rows via ``emit_form`` and forwards participles.

    Args:
        class2: Weak-verb class2 marker from form metadata.
        original_ending: Source infinitive ending from the paradigm.
        probability: Base probability scalar for principal forms.
        probability_plus_one: Incremented probability scalar.
        perl_inf_vowel_end: Perl-style vowel-ending predicate.
        regex_vowel_end: Regex-based vowel-ending predicate.
        emit_form: Callback that emits one generated form.
        on_participle: Callback invoked for each derived participle form-parts.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Raises:
        Does not raise directly.

    Returns:
        ``None``.

    """
    # create_dict31.pl applies this branch to weak verbs generally.
    if class2 in {"", "1", "2"}:
        iending_general = "i" if original_ending.lower().startswith("i") else ""
        fp = emit_weak_derived_from_inf_general(
            original_ending=original_ending,
            iending=iending_general,
            probability=probability,
            probability_plus_one=probability_plus_one,
            perl_inf_vowel_end=perl_inf_vowel_end,
            regex_vowel_end=regex_vowel_end,
            emit_form=emit_form,
        )
        on_participle(fp)

    # Perl: if ($word->{class2} == 2)
    elif class2 == "2":
        for iending in ["ig", "ige", ""]:
            fp = emit_weak_derived_from_inf_class2_variant(
                iending=iending,
                perl_inf_vowel_end=perl_inf_vowel_end,
                regex_vowel_end=regex_vowel_end,
                emit_form=emit_form,
            )
            on_participle(fp)


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


def is_weak_item_shape_window(para_id_num: str) -> bool:
    """
    Return whether weak generation should use raw item shape by paradigm ID.

    Side Effects:
        None.

    Args:
        para_id_num: Paradigm numeric ID string.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``True`` when ``88 < int(para_id_num) < 93``.

    """
    if not str(para_id_num).isdigit():
        return False
    para_id_int = int(para_id_num)
    return WEAK_ITEM_SHAPE_MIN_ID < para_id_int < WEAK_ITEM_SHAPE_MAX_ID


def emit_weak_principal_form(  # noqa: PLR0913
    *,
    para_id: str,
    prefix: str,
    default_parts: tuple[str, str, str, str],
    item_parts: tuple[str, str, str, str],
    dental: str | None,
    ending: str,
    variant_id: int,
    use_item_shape: bool,
    emit_form: WeakPrincipalEmitter,
) -> str:
    """
    Emit one weak principal form and return emitted ``formParts``.

    Side Effects:
        Writes one principal-form row through ``emit_form``.

    Args:
        para_id: Paradigm function identifier.
        prefix: Word prefix component.
        default_parts: ``(pre_vowel, vowel, post_vowel, boundary)`` tuple.
        item_parts: Raw item tuple ``(pre_vowel, vowel, post_vowel, boundary)``.
        dental: Dental segment.
        ending: Paradigm ending.
        variant_id: Variant index for principal probability rules.
        use_item_shape: Whether to emit from raw item parts.
        emit_form: Callback that emits one generated principal form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Emitted ``formParts`` string.

    """
    if use_item_shape:
        pre_vowel, vowel, post_vowel, boundary = item_parts
        _, form_parts = emit_form(
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            dental,
            ending,
            para_id,
            0,
        )
        return form_parts

    pre_vowel, vowel, post_vowel, boundary = default_parts
    principal_prob: str | int | None = (
        None if (para_id.lower() == "painsg1" and variant_id == 0) else 0
    )
    _, form_parts = emit_form(
        prefix,
        pre_vowel,
        vowel,
        post_vowel,
        boundary,
        dental,
        ending,
        para_id,
        principal_prob,
    )
    return form_parts


def dispatch_weak_derived_forms(
    *,
    para_id: str,
    use_item_shape: bool,
    on_inf: WeakBranchAction,
    on_psinsg2: WeakBranchAction,
    on_painsg1: WeakBranchAction,
) -> bool:
    """
    Dispatch weak derived-form generation for one principal paradigm function.

    Side Effects:
        Invokes one branch callback when a derived branch applies.

    Args:
        para_id: Principal function identifier from the paradigm row.
        use_item_shape: Whether generation is in raw item-shape mode.
        on_inf: Callback for infinitive-derived branch.
        on_psinsg2: Callback for ``PsInSg2``-derived branch.
        on_painsg1: Callback for ``PaInSg1``-derived branch.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Raises:
        Does not raise directly.

    Returns:
        ``True`` when a branch callback was invoked, otherwise ``False``.

    """
    if use_item_shape:
        return False

    para_id_lower = para_id.lower()
    if para_id_lower == "if":
        on_inf()
        return True
    if para_id_lower == "psinsg2":
        on_psinsg2()
        return True
    if para_id_lower == "painsg1":
        on_painsg1()
        return True
    return False
