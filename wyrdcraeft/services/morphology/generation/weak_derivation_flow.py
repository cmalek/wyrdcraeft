"""Weak-derivation orchestration helpers for verb-generation flows."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Protocol

from wyrdcraeft.models.morphology import (
    Word,
    _WeakInfDerivationContext,
    _WeakPainsg1DerivationContext,
    _WeakPsinsg2DerivationContext,
)

from .weak_inflections import (
    emit_weak_derived_from_inf_sequence,
    emit_weak_derived_from_painsg1_context,
    emit_weak_derived_from_psinsg2_context,
)


#: Callback signature for attaching one participle row to adjective storage.
class WeakParticipleAdder(Protocol):
    """Protocol for adding one participle to adjective storage."""

    def __call__(
        self,
        word: Word,
        prefix: str,
        form_parts: str,
        *,
        is_past: bool,
    ) -> None:
        """
        Store one participle row in adjective sink.

        Args:
            word: Lexeme record that owns the derived participle.
            prefix: Prefix segment for the emitted participle.
            form_parts: Serialized form-parts payload for the participle.

        Keyword Args:
            is_past: Whether the participle is past (``True``) or present.

        """


#: Callback signature for one weak infinitive-derived row emission.
WeakInfFormEmitter = Callable[
    [
        dict[str, str],
        str,
        str,
        str,
        str,
        str,
        str | None,
        str,
        str,
        str | int | None,
    ],
    tuple[str, str],
]


class WeakFormContextEmitter(Protocol):
    """
    Protocol for emitting one weak row from a pre-bound stem context.

    The callback shape mirrors ``VerbFormGenerator._emit_form_for_context`` so
    low-level weak bridge helpers can delegate without rebuilding the payload.
    """

    def __call__(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        *,
        dental: str | None = "",
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        """
        Emit one weak row for a provided stem context.

        Args:
            formhash: Form metadata hash for the active branch.
            prefix: Prefix segment for the active part.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment for this derivation branch.
            post_vowel: Stem segment after the active vowel.
            boundary: Stem-boundary marker used in form-parts payloads.
            ending: Morphological ending.
            function: Morphological function code.

        Keyword Args:
            dental: Optional weak-dental segment.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
#: Callback signature for one weak ``PaInSg1`` raw row emission.
WeakPainsg1RawFormEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one weak ``PaInSg1`` routed-context row emission.
WeakPainsg1ContextFormEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str, str | int | None, str],
    tuple[str, str],
]
#: Callback signature for one context-aware weak infinitive-derived row emission.
WeakDerivedInfFormAction = Callable[
    [_WeakInfDerivationContext, str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one context-aware weak infinitive-derived participle action.
WeakDerivedInfParticipleAction = Callable[[_WeakInfDerivationContext, str], None]
#: Callback signature for one context-aware weak ``PaInSg1`` form action.
WeakPainsg1FormAction = Callable[
    [_WeakPainsg1DerivationContext, str, str, str, str | int | None, str],
    tuple[str, str] | None,
]
#: Callback signature for one context-aware weak ``PaInSg1`` manual form action.
WeakPainsg1ManualAction = Callable[
    [_WeakPainsg1DerivationContext, str, str, str, str | int | None],
    None,
]
#: Callback signature for one context-aware weak ``PaInSg1`` participle action.
WeakPainsg1ParticipleAction = Callable[[_WeakPainsg1DerivationContext, str], None]
#: Callback signature for one context-aware weak ``PsInSg2`` form action.
WeakPsinsg2FormAction = Callable[
    [_WeakPsinsg2DerivationContext, str, str, str | int | None, str],
    None,
]
#: Callback signature for one context-aware weak ``PsInSg2`` sound action.
WeakPsinsg2SoundAction = Callable[
    [_WeakPsinsg2DerivationContext, str, str, str | int | None, int, str],
    None,
]
#: Callback signature for one manual weak row emission.
WeakManualEmitter = Callable[
    [dict[str, str], str, str, str, str | int | None],
    None,
]
#: Callback signature for one weak ``PsInSg2`` row with simplified post-vowel.
WeakPsinsg2FormWithPostEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one weak ``PsInSg2`` derivation-context form emission.
WeakPsinsg2DerivationFormContextEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str | int | None, str],
    None,
]
#: Callback signature for one weak ``PsInSg2`` derivation-context sound emission.
WeakPsinsg2DerivationSoundContextEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str | int | None, int, str],
    None,
]


class WeakPsinsg2SoundWithPostEmitter(Protocol):
    """
    Protocol for weak ``PsInSg2`` sound-change row emission with probability delta.
    """

    def __call__(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
        sound_change_prob_delta: int = 1,
    ) -> None:
        """
        Emit sound-changed weak rows for one ``PsInSg2`` branch.

        Args:
            formhash: Form metadata hash for the active branch.
            prefix: Prefix segment for the active part.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment for this derivation branch.
            post_vowel: Stem segment after the active vowel.
            boundary: Stem-boundary marker used in form-parts payloads.
            dental: Optional weak-dental segment.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Keyword Args:
            sound_change_prob_delta: Probability delta applied to sound-changed
                alternatives.

        """


def emit_weak_inf_form(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str | None,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_weak_principal_form: WeakInfFormEmitter,
) -> tuple[str, str]:
    """
    Emit one weak infinitive-derived row by delegating to principal-form output.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        formhash: Form metadata hash for the active branch.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment for this derivation branch.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Optional weak-dental segment for this emitted row.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_weak_principal_form: Callback for one weak principal-form row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental-based derivation;
        this helper only forwards the legacy argument slots unchanged.

    """
    return emit_weak_principal_form(
        formhash,
        prefix,
        pre_vowel,
        vowel,
        post_vowel,
        boundary,
        dental,
        ending,
        function,
        prob,
    )


def emit_weak_principal_form_context(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str | None,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_form_for_context: WeakFormContextEmitter,
) -> tuple[str, str]:
    """
    Emit one weak principal-form row for a pre-bound stem context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        formhash: Form metadata hash for the active branch.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment for this derivation branch.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Optional weak-dental segment for this emitted row.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_form_for_context: Callback that emits one weak row from the
            already-selected stem context.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental-row emission;
        this helper only forwards the legacy slots unchanged so callback order,
        probability flow, and form-part assembly remain parity-locked.

    """
    return emit_form_for_context(
        formhash,
        prefix,
        pre_vowel,
        vowel,
        post_vowel,
        boundary,
        ending,
        function,
        dental=dental,
        prob=prob,
    )


def emit_weak_painsg1_form_for_vowel(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    boundary: str,
    dental: str,
    current_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    post_vowel_simple: str,
    *,
    emit_form: WeakPainsg1RawFormEmitter,
) -> tuple[str, str]:
    """
    Emit one weak ``PaInSg1`` row for a selected vowel variant.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        formhash: Form metadata hash for the active branch.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Weak preterite dental segment for this derivation branch.
        current_vowel: Selected vowel for the emitted branch.
        ending: Morphological ending.
        function: Morphology function code.
        prob: Optional probability annotation.
        post_vowel_simple: Simplified post-vowel segment for this branch.

    Keyword Args:
        emit_form: Callback that emits one weak form row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PaInSg1`` variants;
        this helper preserves callback slot ordering and probability flow.

    """
    return emit_form(
        formhash,
        prefix,
        pre_vowel,
        current_vowel,
        post_vowel_simple,
        boundary,
        dental,
        ending,
        function,
        prob,
    )


def emit_weak_painsg1_form_for_vowel_from_context(  # noqa: PLR0913
    context: _WeakPainsg1DerivationContext,
    current_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    post_vowel_simple: str,
    *,
    emit_form_for_vowel: WeakPainsg1ContextFormEmitter,
) -> tuple[str, str]:
    """
    Route one weak ``PaInSg1`` form emission through derivation context payload.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared weak ``PaInSg1`` derivation context.
        current_vowel: Selected vowel for the emitted branch.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.
        post_vowel_simple: Simplified post-vowel segment for this branch.

    Keyword Args:
        emit_form_for_vowel: Callback that emits one weak ``PaInSg1`` row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak preterite routing;
        this helper only unpacks stored context and forwards it in order.

    """
    return emit_form_for_vowel(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.boundary,
        context.dental,
        current_vowel,
        ending,
        function,
        prob,
        post_vowel_simple,
    )


def emit_weak_painsg1_manual_context(  # noqa: PLR0913
    context: _WeakPainsg1DerivationContext,
    form: str,
    form_parts: str,
    function: str,
    prob: str | int | None,
    *,
    emit_manual: WeakManualEmitter,
) -> None:
    """
    Emit one manual row from a pre-bound weak ``PaInSg1`` context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared weak ``PaInSg1`` derivation context.
        form: Emitted surface form.
        form_parts: Structured form-parts payload.
        function: Morphological function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_manual: Callback that emits one manual morphology row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PaInSg1`` output as
        regular branch emission; this helper preserves ordering and slots.

    """
    emit_manual(
        context.formhash,
        form,
        form_parts,
        function,
        prob,
    )


def emit_weak_painsg1_participle_context(
    context: _WeakPainsg1DerivationContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: WeakParticipleAdder,
) -> None:
    """
    Attach a past participle emitted from a weak ``PaInSg1`` branch.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared weak ``PaInSg1`` derivation context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe participle derivation in weak
        paradigms; this helper forwards payloads without altering sequencing.

    """
    add_participle_to_adjectives(
        context.word,
        context.prefix,
        form_parts,
        is_past=True,
    )


def emit_weak_derived_inf_form(  # noqa: PLR0913
    context: _WeakInfDerivationContext,
    dental: str | None,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_weak_inf_form: WeakInfFormEmitter,
) -> tuple[str, str]:
    """
    Emit one weak infinitive-derived row from a shared derivation context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared weak infinitive-derivation context.
        dental: Optional weak-dental segment for the emitted row.
        ending: Ending segment for the emitted row.
        function: Morphology function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_weak_inf_form: Callback that emits one weak infinitive-derived row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental derivation;
        this helper only routes the same slots to the existing emitter.

    """
    return emit_weak_inf_form(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.post_vowel,
        context.boundary,
        dental,
        ending,
        function,
        prob,
    )


def emit_weak_psinsg2_form_with_post_context(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    boundary: str,
    ending: str,
    function: str,
    prob: str | int | None,
    post_vowel_simple: str,
    *,
    emit_form_with_post: WeakPsinsg2FormWithPostEmitter,
) -> None:
    """
    Emit one weak ``PsInSg2``-branch form row with simplified post-vowel.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        formhash: The mutable form metadata hash.
        prefix: Prefix segment.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment.
        boundary: Boundary consonant segment.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.
        post_vowel_simple: Simplified post-vowel segment.

    Keyword Args:
        emit_form_with_post: Callback that emits one weak row with a simplified
            post-vowel slot.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PsInSg2`` branching;
        this helper preserves argument ordering and probability flow.

    """
    emit_form_with_post(
        formhash,
        prefix,
        pre_vowel,
        vowel,
        post_vowel_simple,
        boundary,
        None,
        ending,
        function,
        prob,
    )


def emit_weak_psinsg2_sound_with_post_context(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    boundary: str,
    ending: str,
    function: str,
    prob: str | int | None,
    consonant_change_prob: int,
    post_vowel_simple: str,
    *,
    emit_sound_with_post: WeakPsinsg2SoundWithPostEmitter,
) -> None:
    """
    Emit one weak ``PsInSg2`` sound-change branch with simplified post-vowel.

    Side Effects:
        Writes generated and sound-changed rows to the output stream.

    Args:
        formhash: The mutable form metadata hash.
        prefix: Prefix segment.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment.
        boundary: Boundary consonant segment.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.
        consonant_change_prob: Probability delta used by sound changes.
        post_vowel_simple: Simplified post-vowel segment.

    Keyword Args:
        emit_sound_with_post: Callback that emits sound-changed weak rows.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe deterministic weak
        sound-change alternations; this helper keeps branch payloads intact.

    """
    emit_sound_with_post(
        formhash,
        prefix,
        pre_vowel,
        vowel,
        post_vowel_simple,
        boundary,
        None,
        ending,
        function,
        prob,
        sound_change_prob_delta=consonant_change_prob,
    )


def emit_weak_psinsg2_form_with_post_derivation_context(  # noqa: PLR0913
    context: _WeakPsinsg2DerivationContext,
    ending: str,
    function: str,
    prob: str | int | None,
    post_vowel_simple: str,
    *,
    emit_form_with_post_context: WeakPsinsg2DerivationFormContextEmitter,
) -> None:
    """
    Emit one weak ``PsInSg2`` form row from a pre-bound derivation context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared weak ``PsInSg2`` derivation context.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.
        post_vowel_simple: Simplified post-vowel segment.

    Keyword Args:
        emit_form_with_post_context: Callback that emits one weak ``PsInSg2``
            row for a provided context payload.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PsInSg2`` branch
        propagation; this helper unpacks context without changing row order.

    """
    emit_form_with_post_context(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.boundary,
        ending,
        function,
        prob,
        post_vowel_simple,
    )


def emit_weak_psinsg2_sound_with_post_derivation_context(  # noqa: PLR0913
    context: _WeakPsinsg2DerivationContext,
    ending: str,
    function: str,
    prob: str | int | None,
    consonant_change_prob: int,
    post_vowel_simple: str,
    *,
    emit_sound_with_post_context: WeakPsinsg2DerivationSoundContextEmitter,
) -> None:
    """
    Emit one weak ``PsInSg2`` sound-change row from a pre-bound context.

    Side Effects:
        Writes generated and sound-changed rows to the output stream.

    Args:
        context: Shared weak ``PsInSg2`` derivation context.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.
        consonant_change_prob: Probability delta used by sound changes.
        post_vowel_simple: Simplified post-vowel segment.

    Keyword Args:
        emit_sound_with_post_context: Callback that emits one weak sound-change
            row for a provided context payload.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak sound-change branch
        routing; this helper preserves callback order and probability plumbing.

    """
    emit_sound_with_post_context(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.boundary,
        ending,
        function,
        prob,
        consonant_change_prob,
        post_vowel_simple,
    )


def emit_weak_derived_inf_participle(
    context: _WeakInfDerivationContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: WeakParticipleAdder,
) -> None:
    """
    Attach a present participle emitted from infinitive-derived weak rows.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared weak infinitive-derivation context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak participle derivation;
        this helper forwards the emitted payload unchanged.

    """
    add_participle_to_adjectives(
        context.word,
        context.prefix,
        form_parts,
        is_past=False,
    )


def generate_weak_derived_from_inf(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    word: Word,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    original_ending: str,
    probability: str | int | None,
    emit_form_for_context: WeakFormContextEmitter,
    add_participle_to_adjectives: WeakParticipleAdder,
) -> None:
    """
    Emit weak infinitive-derived branches for one principal-part context.

    Side Effects:
        Writes generated rows and participle side effects via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment for this derivation branch.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        original_ending: Source infinitive ending from the principal part.
        probability: Base probability annotation for the branch.
        emit_form_for_context: Callback that emits one weak row from the
            selected stem context.
        add_participle_to_adjectives: Callback that stores derived
            participles.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental branch
        sequencing; this helper preserves callback order from the legacy flow.

    """
    context = _WeakInfDerivationContext(
        formhash=formhash,
        word=word,
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
    )

    def _emit_inf_form_from_context(  # noqa: PLR0913
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        return emit_weak_inf_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            dental,
            ending,
            function,
            prob,
            emit_weak_principal_form=partial(
                emit_weak_principal_form_context,
                emit_form_for_context=emit_form_for_context,
            ),
        )

    def _emit_form(
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        return emit_weak_derived_inf_form(
            context,
            dental,
            ending,
            function,
            prob,
            emit_weak_inf_form=_emit_inf_form_from_context,
        )

    def _on_participle(form_parts: str) -> None:
        emit_weak_derived_inf_participle(
            context,
            form_parts,
            add_participle_to_adjectives=add_participle_to_adjectives,
        )

    emit_weak_derived_from_inf_sequence(
        class2=formhash.get("class2"),
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
        original_ending=original_ending,
        probability=probability,
        emit_form=_emit_form,
        on_participle=_on_participle,
    )


def generate_weak_derived_from_painsg1(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    word: Word,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str,
    probability: str | int | None,
    vowel_inf: str,
    vowel_pa: str,
    emit_form: WeakPainsg1RawFormEmitter,
    emit_manual: WeakManualEmitter,
    add_participle_to_adjectives: WeakParticipleAdder,
) -> None:
    """
    Emit weak ``PaInSg1``-derived branches for one principal-part context.

    Side Effects:
        Writes generated rows and participle side effects via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment for this derivation branch.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Weak preterite dental segment for this derivation branch.
        probability: Base probability annotation for the branch.
        vowel_inf: Infinitive vowel from variant 0.
        vowel_pa: Preterite singular vowel from variant 0.
        emit_form: Callback for direct row emission.
        emit_manual: Callback for manual row emission.
        add_participle_to_adjectives: Callback for storing derived
            participles.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak preterite derivation;
        this helper keeps the legacy callback order unchanged.

    """
    context = _WeakPainsg1DerivationContext(
        formhash=formhash,
        word=word,
        prefix=prefix,
        pre_vowel=pre_vowel,
        boundary=boundary,
        dental=dental,
    )

    def _emit_form_for_vowel(
        current_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> tuple[str, str] | None:
        return emit_weak_painsg1_form_for_vowel_from_context(
            context,
            current_vowel,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_for_vowel=partial(
                emit_weak_painsg1_form_for_vowel,
                emit_form=emit_form,
            ),
        )

    def _emit_manual(
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        emit_weak_painsg1_manual_context(
            context,
            form,
            form_parts,
            function,
            prob,
            emit_manual=emit_manual,
        )

    def _on_participle(form_parts: str) -> None:
        emit_weak_painsg1_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=add_participle_to_adjectives,
        )

    emit_weak_derived_from_painsg1_context(
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
        dental=dental,
        vowel_inf=vowel_inf,
        vowel_pa=vowel_pa,
        probability=probability,
        emit_form_for_vowel=_emit_form_for_vowel,
        emit_manual=_emit_manual,
        on_participle=_on_participle,
    )


def generate_weak_derived_from_psinsg2(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    probability: str | int | None,
    emit_form: WeakPsinsg2FormWithPostEmitter,
    emit_sound: WeakPsinsg2SoundWithPostEmitter,
) -> None:
    """
    Emit weak ``PsInSg2``-derived branches for one principal-part context.

    Side Effects:
        Writes generated and sound-changed rows via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment for this derivation branch.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        probability: Base probability annotation for the branch.
        emit_form: Callback for direct form emission.
        emit_sound: Callback for sound-change emission.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PsInSg2`` branch
        routing; this helper keeps deterministic emit ordering intact.

    """
    context = _WeakPsinsg2DerivationContext(
        formhash=formhash,
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        boundary=boundary,
    )

    def _emit_form_with_post(
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> None:
        emit_weak_psinsg2_form_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_with_post_context=partial(
                emit_weak_psinsg2_form_with_post_context,
                emit_form_with_post=emit_form,
            ),
        )

    def _emit_sound_with_post(
        ending: str,
        function: str,
        prob: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
    ) -> None:
        emit_weak_psinsg2_sound_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            consonant_change_prob,
            post_vowel_simple,
            emit_sound_with_post_context=partial(
                emit_weak_psinsg2_sound_with_post_context,
                emit_sound_with_post=emit_sound,
            ),
        )

    emit_weak_derived_from_psinsg2_context(
        probability=probability,
        post_vowel=post_vowel,
        emit_form_with_post=_emit_form_with_post,
        emit_sound_with_post=_emit_sound_with_post,
    )
