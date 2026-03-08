"""Sound-change dispatch orchestration helpers for verb-generation flows."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

from wyrdcraeft.models.morphology import _SoundChangeDispatchContext

from .sound_changes import emit_sound_changed_from_source

#: Callback signature for one source-row emission using expanded context values.
SoundSourceContextEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one manual-row emission using expanded context values.
SoundManualContextEmitter = Callable[
    [dict[str, str], str, str, str, str | int | None],
    None,
]
#: Callback signature for one context-aware source-row emission operation.
SoundSourceDispatchAction = Callable[[_SoundChangeDispatchContext], tuple[str, str]]
#: Callback signature for one context-aware manual-row emission operation.
SoundManualDispatchAction = Callable[
    [_SoundChangeDispatchContext, str, str, str, str | int | None],
    None,
]


def generate_and_print_form_with_sound_changes(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str | None,
    ending: str,
    function: str,
    probability: str | int | None,
    sound_change_prob_delta: int,
    emit_source_form_with_context: SoundSourceDispatchAction,
    emit_manual_with_context: SoundManualDispatchAction,
) -> None:
    """
    Emit one source row and its sound-change derivatives with shared context.

    Side Effects:
        Writes rows to the morphology output stream through callbacks.

    Args:
        formhash: Shared form metadata for emitted rows.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        vowel: Active stem vowel for source-row emission.
        post_vowel: Segment after the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Optional weak preterite dental segment.
        ending: Morphological ending for source-row emission.
        function: Morphology function code for source-row emission.
        probability: Optional source-row probability annotation.
        sound_change_prob_delta: Probability increment for derived rows.
        emit_source_form_with_context: Callback that emits source form row.
        emit_manual_with_context: Callback that emits one derived manual row.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe regular phonological
        alternation in inflection; this helper preserves legacy dispatch order.

    """
    context = _SoundChangeDispatchContext(
        formhash=formhash,
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
        dental=dental,
        ending=ending,
        function=function,
        probability=probability,
    )
    emit_sound_changed_from_source(
        function=function,
        probability=probability,
        sound_change_prob_delta=sound_change_prob_delta,
        emit_source_form=partial(emit_source_form_with_context, context),
        emit_manual=partial(emit_manual_with_context, context),
    )


def emit_source_form_with_sound_dispatch_context(
    context: _SoundChangeDispatchContext,
    *,
    emit_source_form_with_sound_context_callback: SoundSourceContextEmitter,
) -> tuple[str, str]:
    """
    Emit one sound-change source row from shared dispatch context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared source-row dispatch context.

    Keyword Args:
        emit_source_form_with_sound_context_callback: Callback that emits source
            form.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe phonological alternation
        paths; this wrapper keeps source-row argument ordering unchanged.

    """
    return emit_source_form_with_sound_context(
        context,
        emit_source_form=emit_source_form_with_sound_context_callback,
    )


def emit_source_form_with_sound_context(
    context: _SoundChangeDispatchContext,
    *,
    emit_source_form: SoundSourceContextEmitter,
) -> tuple[str, str]:
    """
    Emit one source row used for downstream sound-change derivations.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared source-row dispatch context.

    Keyword Args:
        emit_source_form: Callback that emits the source row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe preserving source stems
        before phonological alternations; this helper forwards slots unchanged.

    """
    return emit_source_form(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.post_vowel,
        context.boundary,
        context.dental,
        context.ending,
        context.function,
        context.probability,
    )


def emit_manual_sound_changed_dispatch_context(  # noqa: PLR0913
    context: _SoundChangeDispatchContext,
    sound_changed_form: str,
    source_form_parts: str,
    source_function: str,
    source_probability: str | int | None,
    *,
    emit_manual_sound_changed_context_callback: SoundManualContextEmitter,
) -> None:
    """
    Emit one manual sound-change row using shared dispatch context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared source-row dispatch context.
        sound_changed_form: The emitted sound-changed form text.
        source_form_parts: The source form-parts payload.
        source_function: The morphology function code.
        source_probability: Optional probability annotation.

    Keyword Args:
        emit_manual_sound_changed_context_callback: Callback that emits manual
            row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe deterministic branch
        ordering for derived forms; this helper preserves that order.

    """
    emit_manual_sound_changed_context(
        context,
        sound_changed_form,
        source_form_parts,
        source_function,
        source_probability,
        emit_manual=emit_manual_sound_changed_context_callback,
    )


def emit_manual_sound_changed_context(  # noqa: PLR0913
    context: _SoundChangeDispatchContext,
    sound_changed_form: str,
    source_form_parts: str,
    source_function: str,
    source_probability: str | int | None,
    *,
    emit_manual: SoundManualContextEmitter,
) -> None:
    """
    Emit one manually assembled row for a sound-changed derivative.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared source-row dispatch context.
        sound_changed_form: The emitted sound-changed form text.
        source_form_parts: The source form-parts payload.
        source_function: The morphology function code.
        source_probability: Optional probability annotation.

    Keyword Args:
        emit_manual: Callback that emits the manual row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) treat these as downstream outcomes
        of one source stem; this helper forwards payloads unchanged.

    """
    emit_manual(
        context.formhash,
        sound_changed_form,
        source_form_parts,
        source_function,
        source_probability,
    )
