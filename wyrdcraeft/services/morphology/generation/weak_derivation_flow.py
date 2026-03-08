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
    emit_form: WeakDerivedInfFormAction,
    on_participle: WeakDerivedInfParticipleAction,
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
        emit_form: Callback that emits one infinitive-derived row.
        on_participle: Callback for each derived participle payload.

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
    emit_weak_derived_from_inf_sequence(
        class2=formhash.get("class2"),
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
        original_ending=original_ending,
        probability=probability,
        emit_form=partial(emit_form, context),
        on_participle=partial(on_participle, context),
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
    emit_form_for_vowel: WeakPainsg1FormAction,
    emit_manual: WeakPainsg1ManualAction,
    on_participle: WeakPainsg1ParticipleAction,
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
        emit_form_for_vowel: Callback for vowel-selected row emission.
        emit_manual: Callback for manual row emission.
        on_participle: Callback for each derived participle payload.

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
        emit_form_for_vowel=partial(emit_form_for_vowel, context),
        emit_manual=partial(emit_manual, context),
        on_participle=partial(on_participle, context),
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
    emit_form_with_post: WeakPsinsg2FormAction,
    emit_sound_with_post: WeakPsinsg2SoundAction,
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
        emit_form_with_post: Callback for direct form emission.
        emit_sound_with_post: Callback for sound-change emission.

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
    emit_weak_derived_from_psinsg2_context(
        probability=probability,
        post_vowel=post_vowel,
        emit_form_with_post=partial(emit_form_with_post, context),
        emit_sound_with_post=partial(emit_sound_with_post, context),
    )
