"""Strong principal-part orchestration helpers for verb-generation flows."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Protocol

from wyrdcraeft.models.morphology import ParadigmPart, Word, _StrongPrincipalPartContext

from . import strong_derivation_flow as _strong_derivation_flow
from .strong_inflections import emit_strong_principal_part_sequence

if TYPE_CHECKING:
    from .strong_derivation_flow import (
        StrongFormContextEmitter,
        StrongImSgEmitter,
        StrongSoundContextEmitter,
    )


#: Callback signature for attaching one participle row to adjective storage.
class StrongParticipleAdder(Protocol):
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


#: Callback signature for one strong principal-form emission operation.
StrongVowelFormEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one strong infinitive-derived branch emission.
StrongInfDerivationEmitter = Callable[
    [dict[str, str], Word, str, str, str, str, str, str, str | int | None],
    None,
]
#: Callback signature for one context-aware strong principal-form action.
StrongPrincipalFormAction = Callable[
    [_StrongPrincipalPartContext, str, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one context-aware strong participle action.
StrongPrincipalParticipleAction = Callable[[_StrongPrincipalPartContext, str], None]
#: Callback signature for one context-aware strong infinitive-branch action.
StrongPrincipalInfDerivationAction = Callable[
    [_StrongPrincipalPartContext, str, str | int | None],
    None,
]


def emit_strong_principal_form_for_vowel(  # noqa: PLR0913
    context: _StrongPrincipalPartContext,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_strong_vowel_form: StrongVowelFormEmitter,
) -> tuple[str, str]:
    """
    Emit one strong principal-part row for a selected active vowel.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared strong principal-part context.
        active_vowel: Active stem vowel for this emitted row.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_strong_vowel_form: Callback that emits one strong principal row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong-verb ablaut
        alternation; this helper only forwards one selected vowel branch.

    """
    return emit_strong_vowel_form(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.post_vowel,
        context.boundary,
        active_vowel,
        ending,
        function,
        prob,
    )


def emit_strong_principal_participle(
    context: _StrongPrincipalPartContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: StrongParticipleAdder,
) -> None:
    """
    Attach a past participle emitted from a strong principal-part row.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared strong principal-part context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong participle derivation;
        this helper routes the payload unchanged.

    """
    add_participle_to_adjectives(
        context.word,
        context.prefix,
        form_parts,
        is_past=True,
    )


def emit_strong_principal_inf_derivation(
    context: _StrongPrincipalPartContext,
    active_vowel: str,
    prob: str | int | None,
    *,
    emit_strong_inf_derivation_for_context: StrongInfDerivationEmitter,
) -> None:
    """
    Emit strong infinitive-derived rows from a principal-part context.

    Side Effects:
        Writes generated rows and participle side effects to output/session.

    Args:
        context: Shared strong principal-part context.
        active_vowel: Active stem vowel for this derivation branch.
        prob: Optional probability annotation.

    Keyword Args:
        emit_strong_inf_derivation_for_context: Callback for infinitive-derived
            strong branch emission.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong principal-part
        branching; this helper preserves legacy argument ordering.

    """
    emit_strong_inf_derivation_for_context(
        context.formhash,
        context.word,
        context.prefix,
        context.pre_vowel,
        context.post_vowel,
        context.boundary,
        context.ending,
        active_vowel,
        prob,
    )


def emit_strong_principal_inf_derivation_with_emitters(  # noqa: PLR0913
    context: _StrongPrincipalPartContext,
    active_vowel: str,
    prob: str | int | None,
    *,
    emit_form_for_context: StrongFormContextEmitter,
    emit_sound_for_context: StrongSoundContextEmitter,
    emit_imsg_for_context: StrongImSgEmitter,
    add_participle_to_adjectives: StrongParticipleAdder,
) -> None:
    """
    Emit strong infinitive-derived rows from principal context via low-level emitters.

    Side Effects:
        Writes generated rows and participle side effects to output/session.

    Args:
        context: Shared strong principal-part context.
        active_vowel: Active stem vowel for this derivation branch.
        prob: Optional probability annotation.

    Keyword Args:
        emit_form_for_context: Low-level row emitter for direct form output.
        emit_sound_for_context: Low-level sound-change emitter.
        emit_imsg_for_context: Low-level imperative-singular emitter.
        add_participle_to_adjectives: Callback that stores derived participles.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong principal-part
        branching into infinitive-derived rows; this helper keeps that
        sequencing intact while moving callback-stack assembly out of
        ``generation.common``.

    """
    _strong_derivation_flow.generate_strong_derived_from_inf(
        formhash=context.formhash,
        word=context.word,
        prefix=context.prefix,
        pre_vowel=context.pre_vowel,
        vowel=active_vowel,
        post_vowel=context.post_vowel,
        boundary=context.boundary,
        ending=context.ending,
        probability=prob,
        emit_form_for_vowel=partial(
            _strong_derivation_flow.emit_strong_derived_inf_form_for_vowel_context,
            emit_strong_vowel_form_context=partial(
                _strong_derivation_flow.emit_strong_vowel_form_context,
                emit_form_for_context=emit_form_for_context,
            ),
        ),
        emit_sound_for_vowel=partial(
            _strong_derivation_flow.emit_strong_derived_inf_sound_for_vowel_context,
            emit_strong_vowel_sound_context=partial(
                _strong_derivation_flow.emit_strong_vowel_sound_context,
                emit_sound_for_context=emit_sound_for_context,
            ),
        ),
        on_participle=partial(
            _strong_derivation_flow.emit_strong_derived_inf_participle_context,
            add_participle_to_adjectives=add_participle_to_adjectives,
        ),
        emit_imsg=partial(
            _strong_derivation_flow.emit_strong_derived_inf_imsg_context,
            emit_imsg_for_context=emit_imsg_for_context,
        ),
    )


def generate_strong_verb_parts(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    word: Word,
    item: ParadigmPart,
    prefix: str,
    pre_vowel: str,
    post_vowel: str,
    emit_form_for_vowel: StrongPrincipalFormAction,
    on_papt_participle: StrongPrincipalParticipleAction,
    on_inf: StrongPrincipalInfDerivationAction,
) -> None:
    """
    Route strong principal-part generation through shared inflection sequencing.

    Side Effects:
        Emits generated rows and participle side effects via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        item: Active paradigm part.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        post_vowel: Stem segment after the active vowel.
        emit_form_for_vowel: Callback that emits one principal strong form.
        on_papt_participle: Callback for ``PaPt`` participle side effects.
        on_inf: Callback for infinitive-derived strong branch generation.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong-verb principal-part
        sequencing; this helper preserves the callback order used by the legacy
        generator.

    """
    para_id = item.para_id
    ending = item.ending
    boundary = item.boundary
    context = _StrongPrincipalPartContext(
        formhash=formhash,
        word=word,
        prefix=prefix,
        pre_vowel=pre_vowel,
        post_vowel=post_vowel,
        boundary=boundary,
        ending=ending,
    )
    emit_strong_principal_part_sequence(
        para_id=para_id,
        ending=ending,
        vowels=[item.vowel],
        emit_form_for_vowel=partial(emit_form_for_vowel, context),
        on_papt_form_parts=partial(on_papt_participle, context),
        on_inf=partial(on_inf, context),
    )


def generate_strong_verb_parts_with_emitters(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    word: Word,
    item: ParadigmPart,
    prefix: str,
    pre_vowel: str,
    post_vowel: str,
    emit_form_for_context: StrongFormContextEmitter,
    emit_sound_for_context: StrongSoundContextEmitter,
    emit_imsg_for_context: StrongImSgEmitter,
    add_participle_to_adjectives: StrongParticipleAdder,
) -> None:
    """
    Generate strong principal parts by binding low-level row emitters once.

    Side Effects:
        Emits generated rows and participle side effects via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        item: Active paradigm part.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        post_vowel: Stem segment after the active vowel.
        emit_form_for_context: Low-level row emitter for direct form output.
        emit_sound_for_context: Low-level sound-change emitter.
        emit_imsg_for_context: Low-level imperative-singular emitter.
        add_participle_to_adjectives: Callback that stores derived participles.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong principal-part
        sequencing as a fixed derivational order; this helper keeps the same
        order while centralizing emitter binding in the principal-flow module.

    """
    generate_strong_verb_parts(
        formhash=formhash,
        word=word,
        item=item,
        prefix=prefix,
        pre_vowel=pre_vowel,
        post_vowel=post_vowel,
        emit_form_for_vowel=partial(
            emit_strong_principal_form_for_vowel,
            emit_strong_vowel_form=partial(
                _strong_derivation_flow.emit_strong_vowel_form_context,
                emit_form_for_context=emit_form_for_context,
            ),
        ),
        on_papt_participle=partial(
            emit_strong_principal_participle,
            add_participle_to_adjectives=add_participle_to_adjectives,
        ),
        on_inf=partial(
            emit_strong_principal_inf_derivation_with_emitters,
            emit_form_for_context=emit_form_for_context,
            emit_sound_for_context=emit_sound_for_context,
            emit_imsg_for_context=emit_imsg_for_context,
            add_participle_to_adjectives=add_participle_to_adjectives,
        ),
    )
