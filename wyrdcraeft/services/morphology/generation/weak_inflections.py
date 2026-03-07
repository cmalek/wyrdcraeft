"""Weak-verb infinitive derivation helpers for morphology generation."""

from __future__ import annotations

import re
from collections.abc import Callable

from ..text_utils import OENormalizer
from .probability import probability_or_zero, probability_plus
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
#: Callback signature for one weak-form emission with simplified post-vowel.
WeakSimpleFormWithPostEmitter = Callable[[str, str, str | int | None, str], None]
#: Callback signature for one weak sound-emission with simplified post-vowel.
WeakSoundWithPostEmitter = Callable[
    [str, str, str | int | None, int, str],
    None,
]
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
#: Callback signature for one weak ``PaInSg1`` vowel-variant emission.
WeakPainsg1VariantEmitter = Callable[[str, int], str]
#: Callback signature for one ``PaInSg1`` form emission for a selected vowel.
WeakPainsg1VowelFormEmitter = Callable[
    [str, str, str, str | int | None, str],
    tuple[str, str] | None,
]
#: Stem-part tuple ``(pre_vowel, vowel, post_vowel, boundary)``.
WeakStemParts = tuple[str, str, str, str]
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


def emit_weak_derived_from_inf_sequence(  # noqa: PLR0913
    *,
    class2: str | None,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    original_ending: str,
    probability: str | int | None,
    emit_form: WeakFormEmitter,
    on_participle: WeakParticipleSink,
) -> None:
    """
    Emit weak-verb infinitive-derived branches for one principal-part context.

    Side Effects:
        Emits generated rows through callbacks and forwards participle rows.

    Args:
        class2: Weak-verb class2 marker from form metadata.
        prefix: Word prefix component.
        pre_vowel: Pre-vowel stem segment.
        vowel: Active vowel segment.
        post_vowel: Post-vowel stem segment.
        boundary: Boundary consonant segment.
        original_ending: Source infinitive ending from the paradigm.
        probability: Base probability scalar for derived forms.
        emit_form: Callback that emits one generated form.
        on_participle: Callback invoked for each derived participle form-parts.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    effective_probability = probability if probability is not None else ""
    probability_plus_one = probability_plus(
        effective_probability,
        delta=1,
        empty_default=1,
    )
    fp_base = f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}"

    emit_weak_derived_from_inf_by_class2(
        class2=class2,
        original_ending=original_ending,
        probability=effective_probability,
        probability_plus_one=probability_plus_one,
        perl_inf_vowel_end=has_perl_inf_vowel_ending(fp_base),
        regex_vowel_end=has_regex_vowel_ending(fp_base),
        emit_form=emit_form,
        on_participle=on_participle,
    )


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


def emit_weak_derived_from_psinsg2_context(
    *,
    probability: str | int | None,
    post_vowel: str,
    emit_form_with_post: WeakSimpleFormWithPostEmitter,
    emit_sound_with_post: WeakSoundWithPostEmitter,
) -> None:
    """
    Emit weak ``PsInSg2``-derived forms for one principal-part stem context.

    Side Effects:
        Invokes form and sound callbacks for all branch rows.

    Args:
        probability: Base probability scalar for the branch.
        post_vowel: Post-vowel segment from the principal-part stem.
        emit_form_with_post: Callback for one form row with simplified post-vowel.
        emit_sound_with_post: Callback for one sound-change row with post-vowel.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    effective_probability = probability if probability is not None else ""
    probability_plus_one = probability_plus(
        effective_probability,
        delta=1,
        empty_default=1,
    )
    # Perl: $post_vowel =~ s/(.)\1/$1/;
    post_vowel_simple = re.sub(r"(.)\1", r"\1", post_vowel)

    emit_weak_derived_from_psinsg2(
        probability=effective_probability,
        probability_plus_one=probability_plus_one,
        emit_form=lambda ending, function, prob_value: emit_form_with_post(
            ending,
            function,
            prob_value,
            post_vowel_simple,
        ),
        emit_sound=lambda ending, function, prob_value, consonant_change_prob: (
            emit_sound_with_post(
                ending,
                function,
                prob_value,
                consonant_change_prob,
                post_vowel_simple,
            )
        ),
    )


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


def emit_weak_derived_from_painsg1_sequence(  # noqa: PLR0913
    *,
    vowel: str,
    vowel_inf: str,
    vowel_pa: str,
    probability: str | int | None,
    emit_variant: WeakPainsg1VariantEmitter,
    on_participle: WeakParticipleSink,
) -> None:
    """
    Emit all weak ``PaInSg1``-derived vowel variants for one principal context.

    Side Effects:
        Invokes variant and participle callbacks per emitted vowel/probability pair.

    Args:
        vowel: Principal ``PaInSg1`` vowel segment.
        vowel_inf: Infinitive vowel from variant 0.
        vowel_pa: Preterite singular vowel from variant 0.
        probability: Base probability scalar for variant sequencing.
        emit_variant: Callback that emits one vowel variant and returns form-parts.
        on_participle: Callback that consumes each emitted participle form-parts.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    base_probability = probability_or_zero(probability)
    vowel_list = [vowel]

    # Perl unshifts the paradigm preterite vowel when infinitive and
    # preterite vowels differ in the exemplar.
    if vowel_inf and vowel_pa and vowel_inf != vowel_pa:
        vowel_list.insert(0, vowel_pa)

    for vcount, current_vowel in enumerate(vowel_list):
        form_parts = emit_variant(current_vowel, base_probability + vcount)
        on_participle(form_parts)


def emit_weak_derived_from_painsg1_context(  # noqa: PLR0913
    *,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str,
    vowel_inf: str,
    vowel_pa: str,
    probability: str | int | None,
    emit_form_for_vowel: WeakPainsg1VowelFormEmitter,
    emit_manual: WeakManualEmitter,
    on_participle: WeakParticipleSink,
) -> None:
    """
    Emit weak ``PaInSg1`` derivatives for a fully bound stem context.

    Note:
        Wright treats weak preterites as dental-suffix formations, and Tichý's
        pipeline generates verbal participles with verbs before adjective
        inflection. This helper keeps that ``PaInSg1`` ordering intact.

    Side Effects:
        Emits rows through callback hooks and forwards participle form-parts.

    Args:
        prefix: Word prefix component.
        pre_vowel: Pre-vowel stem segment.
        vowel: Base ``PaInSg1`` vowel segment.
        post_vowel: Post-vowel stem segment before simplification.
        boundary: Boundary consonant segment.
        dental: Dental segment used in weak preterite forms.
        vowel_inf: Infinitive vowel from variant 0.
        vowel_pa: Preterite singular vowel from variant 0.
        probability: Base probability scalar for this branch.
        emit_form_for_vowel: Callback emitting one inflection for one vowel and
            simplified post-vowel segment.
        emit_manual: Callback emitting one manual-form row.
        on_participle: Callback consuming emitted participle form-parts.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    post_vowel_simple = re.sub(r"(.)\1", r"\1", post_vowel)

    def emit_variant(current_vowel: str, current_probability: int) -> str:
        def emit_form(
            ending: str,
            function: str,
            prob_value: str | int | None,
        ) -> None:
            emit_form_for_vowel(
                current_vowel,
                ending,
                function,
                prob_value,
                post_vowel_simple,
            )

        return emit_weak_derived_from_painsg1_variant(
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=current_vowel,
            post_vowel_simple=post_vowel_simple,
            boundary=boundary,
            dental=dental,
            probability=current_probability,
            emit_form=emit_form,
            emit_manual=emit_manual,
        )

    emit_weak_derived_from_painsg1_sequence(
        vowel=vowel,
        vowel_inf=vowel_inf,
        vowel_pa=vowel_pa,
        probability=probability,
        emit_variant=emit_variant,
        on_participle=on_participle,
    )


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


def emit_weak_principal_part_sequence(  # noqa: PLR0913
    *,
    para_id: str,
    para_id_num: str,
    variant_id: int,
    prefix: str,
    default_parts: WeakStemParts,
    item_parts: WeakStemParts,
    dental: str | None,
    ending: str,
    emit_form: WeakPrincipalEmitter,
    on_pspt_participle: WeakParticipleSink,
    on_papt_participle: WeakParticipleSink,
    on_inf: WeakBranchAction,
    on_psinsg2: WeakBranchAction,
    on_painsg1: WeakBranchAction,
) -> None:
    """
    Emit one weak principal part and route all dependent derivation branches.

    Side Effects:
        Emits principal-form rows and triggers derived branch callbacks.

    Args:
        para_id: Principal function identifier from the paradigm row.
        para_id_num: Numeric paradigm ID used for legacy shape branching.
        variant_id: Variant index for principal probability rules.
        prefix: Word prefix component.
        default_parts: Stem parts from normalized root extraction.
        item_parts: Stem parts from raw paradigm item values.
        dental: Dental segment from the paradigm item.
        ending: Morphological ending from the paradigm item.
        emit_form: Callback that emits one principal-form row.
        on_pspt_participle: Callback for present participle projection.
        on_papt_participle: Callback for past participle projection.
        on_inf: Callback for infinitive-derived weak branch generation.
        on_psinsg2: Callback for ``PsInSg2``-derived branch generation.
        on_painsg1: Callback for ``PaInSg1``-derived branch generation.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    use_item_shape = is_weak_item_shape_window(para_id_num)
    form_parts = emit_weak_principal_form(
        para_id=para_id,
        prefix=prefix,
        default_parts=default_parts,
        item_parts=item_parts,
        dental=dental,
        ending=ending,
        variant_id=variant_id,
        use_item_shape=use_item_shape,
        emit_form=emit_form,
    )
    dispatch_weak_principal_part_derivations(
        para_id=para_id,
        use_item_shape=use_item_shape,
        form_parts=form_parts,
        on_pspt_participle=on_pspt_participle,
        on_papt_participle=on_papt_participle,
        on_inf=on_inf,
        on_psinsg2=on_psinsg2,
        on_painsg1=on_painsg1,
    )


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


def dispatch_weak_principal_part_derivations(  # noqa: PLR0913
    *,
    para_id: str,
    use_item_shape: bool,
    form_parts: str,
    on_pspt_participle: WeakParticipleSink,
    on_papt_participle: WeakParticipleSink,
    on_inf: WeakBranchAction,
    on_psinsg2: WeakBranchAction,
    on_painsg1: WeakBranchAction,
) -> bool:
    """
    Dispatch weak branch derivations and participle side effects per principal part.

    Side Effects:
        Invokes participle sinks and derived-branch callbacks.

    Args:
        para_id: Principal function identifier from the paradigm row.
        use_item_shape: Whether generation is in raw item-shape mode.
        form_parts: Emitted principal-form ``formParts`` string.
        on_pspt_participle: Sink callback for ``PsPt`` participles.
        on_papt_participle: Sink callback for ``PaPt`` participles.
        on_inf: Callback for infinitive-derived branch.
        on_psinsg2: Callback for ``PsInSg2``-derived branch.
        on_painsg1: Callback for ``PaInSg1``-derived branch.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        ``True`` when a derived branch callback was invoked, otherwise ``False``.

    """
    para_id_lower = para_id.lower()
    if para_id_lower == "pspt":
        on_pspt_participle(form_parts)
    if para_id_lower == "papt":
        on_papt_participle(form_parts)

    return dispatch_weak_derived_forms(
        para_id=para_id,
        use_item_shape=use_item_shape,
        on_inf=on_inf,
        on_psinsg2=on_psinsg2,
        on_painsg1=on_painsg1,
    )
