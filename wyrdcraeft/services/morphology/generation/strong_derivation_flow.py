"""Strong-derivation orchestration helpers for verb-generation flows."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Protocol

from wyrdcraeft.models.morphology import Word, _StrongInfDerivationContext

from ..text_utils import OENormalizer
from .strong_inflections import emit_strong_derived_from_inf_sequence


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


#: Callback signature for one strong infinitive-derived form emission.
StrongVowelFormEmitter = Callable[
    [
        dict[str, str],
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        str | int | None,
    ],
    tuple[str, str],
]
#: Callback signature for one strong infinitive-derived sound emission.
StrongVowelSoundEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str, str | int | None],
    None,
]
#: Callback signature for one strong imperative-singular derivative emission.
StrongImSgEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str | int | None],
    None,
]
#: Callback signature for routing one strong infinitive-derived branch.
StrongInfDerivationRouter = Callable[
    [dict[str, str], Word, str, str, str, str, str, str, str | int | None],
    None,
]
#: Callback signature for one context-aware strong infinitive-derived form action.
StrongDerivedInfFormAction = Callable[
    [_StrongInfDerivationContext, str, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one context-aware strong infinitive-derived sound action.
StrongDerivedInfSoundAction = Callable[
    [_StrongInfDerivationContext, str, str, str, str | int | None],
    None,
]
#: Callback signature for one context-aware strong infinitive-derived participle action.
StrongDerivedInfParticipleAction = Callable[[_StrongInfDerivationContext, str], None]
#: Callback signature for one context-aware strong imperative-singular action.
StrongDerivedInfImsgAction = Callable[
    [_StrongInfDerivationContext, str | int | None],
    None,
]
class StrongFormContextEmitter(Protocol):
    """Protocol for one low-level form-context row emission."""

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
        dental: str | None = None,
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        """
        Emit one stem-context form row.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            function: Morphological function code.

        Keyword Args:
            dental: Optional weak-dental segment.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
#: Callback signature for one low-level sound-context row emission.
StrongSoundContextEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str, str, str | int | None],
    None,
]


def emit_strong_vowel_form_context(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    post_vowel: str,
    boundary: str,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_form_for_context: StrongFormContextEmitter,
) -> tuple[str, str]:
    """
    Emit one strong-form row for a pre-bound stem context.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        formhash: The mutable form metadata hash.
        prefix: Prefix segment.
        pre_vowel: Stem segment before the active vowel.
        post_vowel: Stem segment after the active vowel.
        boundary: Boundary consonant segment.
        active_vowel: Active ablaut/umlaut vowel.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_form_for_context: Callback that emits one row for the provided
            vowel/context payload.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong-vowel slot routing;
        this helper preserves the same argument ordering and probability flow.

    """
    return emit_form_for_context(
        formhash,
        prefix,
        pre_vowel,
        active_vowel,
        post_vowel,
        boundary,
        ending,
        function,
        prob=prob,
    )


def emit_strong_vowel_sound_context(  # noqa: PLR0913
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    post_vowel: str,
    boundary: str,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_sound_for_context: StrongSoundContextEmitter,
) -> None:
    """
    Emit strong sound-changed rows for one pre-bound stem context.

    Side Effects:
        Writes generated and sound-changed rows to the output stream.

    Args:
        formhash: The mutable form metadata hash.
        prefix: Prefix segment.
        pre_vowel: Stem segment before the active vowel.
        post_vowel: Stem segment after the active vowel.
        boundary: Boundary consonant segment.
        active_vowel: Active ablaut/umlaut vowel.
        ending: Morphological ending.
        function: Morphological function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_sound_for_context: Callback that emits sound-change rows for the
            provided vowel/context payload.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe predictable strong sound
        outcomes; this helper only forwards context slots unchanged.

    """
    emit_sound_for_context(
        formhash,
        prefix,
        pre_vowel,
        active_vowel,
        post_vowel,
        boundary,
        ending,
        function,
        prob,
    )


def emit_strong_inf_derivation_for_context(  # noqa: PLR0913
    formhash: dict[str, str],
    word: Word,
    prefix: str,
    pre_vowel: str,
    post_vowel: str,
    boundary: str,
    ending: str,
    active_vowel: str,
    prob: str | int | None,
    *,
    generate_strong_derived_from_inf: StrongInfDerivationRouter,
) -> None:
    """
    Route one strong principal-part branch into infinitive-derived generation.

    Side Effects:
        Writes generated rows and participle side effects via callback.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        ending: Source ending from the principal-part branch.
        active_vowel: Selected active vowel from principal-part sequencing.
        prob: Optional probability annotation.

    Keyword Args:
        generate_strong_derived_from_inf: Callback that emits infinitive-derived
            strong rows.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong ablaut branch routing;
        this helper preserves legacy slot ordering and probability forwarding.

    """
    generate_strong_derived_from_inf(
        formhash,
        word,
        prefix,
        pre_vowel,
        active_vowel,
        post_vowel,
        boundary,
        ending,
        prob,
    )


def emit_strong_derived_inf_form_for_vowel(  # noqa: PLR0913
    context: _StrongInfDerivationContext,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_strong_vowel_form: StrongVowelFormEmitter,
) -> tuple[str, str]:
    """
    Emit one strong infinitive-derived row for a selected active vowel.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared strong infinitive-derivation context.
        active_vowel: Active vowel used for the emitted row.
        ending: Ending segment for the emitted row.
        function: Morphology function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_strong_vowel_form: Callback that emits one strong derived row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong-verb stem alternation;
        this helper forwards the selected vowel branch without changing order.

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


def emit_strong_derived_inf_form_for_vowel_context(  # noqa: PLR0913
    context: _StrongInfDerivationContext,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_strong_vowel_form_context: StrongVowelFormEmitter,
) -> tuple[str, str]:
    """
    Emit one strong infinitive-derived row for a selected active vowel.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared strong-derivation emission context.
        active_vowel: Active vowel used for the emitted row.
        ending: Ending segment for the emitted row.
        function: Morphology function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_strong_vowel_form_context: Callback that emits one strong
            infinitive-derived form row.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong derivation branch
        propagation; this helper preserves callback sequencing.

    """
    return emit_strong_derived_inf_form_for_vowel(
        context,
        active_vowel,
        ending,
        function,
        prob,
        emit_strong_vowel_form=emit_strong_vowel_form_context,
    )


def emit_strong_derived_inf_sound_for_vowel(  # noqa: PLR0913
    context: _StrongInfDerivationContext,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_strong_vowel_sound: StrongVowelSoundEmitter,
) -> None:
    """
    Emit sound-change rows for one strong infinitive-derived vowel branch.

    Side Effects:
        Writes one or more rows to the morphology output stream.

    Args:
        context: Shared strong infinitive-derivation context.
        active_vowel: Active vowel used for source-row assembly.
        ending: Ending segment for the source row.
        function: Morphology function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_strong_vowel_sound: Callback that emits sound-change derived rows.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong-verb alternation plus
        phonological outcomes; this helper only routes existing branch payloads.

    """
    emit_strong_vowel_sound(
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


def emit_strong_derived_inf_sound_for_vowel_context(  # noqa: PLR0913
    context: _StrongInfDerivationContext,
    active_vowel: str,
    ending: str,
    function: str,
    prob: str | int | None,
    *,
    emit_strong_vowel_sound_context: StrongVowelSoundEmitter,
) -> None:
    """
    Emit sound-change rows for one strong infinitive-derived vowel branch.

    Side Effects:
        Writes one or more rows to the morphology output stream.

    Args:
        context: Shared strong-derivation emission context.
        active_vowel: Active vowel used for source-row assembly.
        ending: Ending segment for the source row.
        function: Morphology function code.
        prob: Optional probability annotation.

    Keyword Args:
        emit_strong_vowel_sound_context: Callback that emits strong
            sound-change rows for one selected vowel branch.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong branch phonological
        outcomes; this helper only routes existing callback payloads.

    """
    emit_strong_derived_inf_sound_for_vowel(
        context,
        active_vowel,
        ending,
        function,
        prob,
        emit_strong_vowel_sound=emit_strong_vowel_sound_context,
    )


def emit_strong_derived_inf_participle(
    context: _StrongInfDerivationContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: StrongParticipleAdder,
) -> None:
    """
    Attach a present participle emitted from infinitive-derived strong rows.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared strong infinitive-derivation context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe participle projection from
        strong stems; this helper forwards the payload unchanged.

    """
    add_participle_to_adjectives(
        context.word,
        context.prefix,
        form_parts,
        is_past=False,
    )


def emit_strong_derived_inf_participle_context(
    context: _StrongInfDerivationContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: StrongParticipleAdder,
) -> None:
    """
    Attach a present participle emitted from infinitive-derived strong rows.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared strong-derivation emission context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe participle projection from
        strong stems; this helper preserves payload forwarding semantics.

    """
    emit_strong_derived_inf_participle(
        context,
        form_parts,
        add_participle_to_adjectives=add_participle_to_adjectives,
    )


def emit_strong_derived_inf_imsg(
    context: _StrongInfDerivationContext,
    prob: str | int | None,
    *,
    emit_imsg_for_context: StrongImSgEmitter,
) -> None:
    """
    Emit the strong imperative-singular derivative for infinitive branches.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared strong infinitive-derivation context.
        prob: Optional probability annotation.

    Keyword Args:
        emit_imsg_for_context: Callback that emits the imperative-singular row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) treat imperative forms within regular
        strong paradigms; this helper preserves the legacy branch call site.

    """
    emit_imsg_for_context(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.base_vowel,
        context.post_vowel,
        context.boundary,
        prob,
    )


def emit_strong_derived_inf_imsg_context(
    context: _StrongInfDerivationContext,
    prob: str | int | None,
    *,
    emit_imsg_for_context: StrongImSgEmitter,
) -> None:
    """
    Emit the strong imperative-singular derivative for infinitive branches.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        context: Shared strong-derivation emission context.
        prob: Optional probability annotation.

    Keyword Args:
        emit_imsg_for_context: Callback that emits the imperative-singular row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) treat imperative rows as part of the
        regular strong paradigm; this helper keeps callback ordering unchanged.

    """
    emit_strong_derived_inf_imsg(
        context,
        prob,
        emit_imsg_for_context=emit_imsg_for_context,
    )


def generate_strong_derived_from_inf(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    word: Word,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    ending: str,
    probability: str | int | None,
    emit_form_for_vowel: StrongDerivedInfFormAction,
    emit_sound_for_vowel: StrongDerivedInfSoundAction,
    on_participle: StrongDerivedInfParticipleAction,
    emit_imsg: StrongDerivedInfImsgAction,
) -> None:
    """
    Emit strong infinitive-derived branches for one principal-part context.

    Side Effects:
        Writes generated rows and participle side effects via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        vowel: Base infinitive vowel for this derivation branch.
        post_vowel: Stem segment after the active vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        ending: Source infinitive ending from the principal part.
        probability: Base probability annotation for the branch.
        emit_form_for_vowel: Callback that emits one derived row.
        emit_sound_for_vowel: Callback that emits one sound-change branch.
        on_participle: Callback for each derived participle payload.
        emit_imsg: Callback that emits imperative-singular derivative row.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe strong-verb branch ordering;
        this helper keeps the exact callback sequencing from the legacy flow.

    """
    context = _StrongInfDerivationContext(
        formhash=formhash,
        word=word,
        prefix=prefix,
        pre_vowel=pre_vowel,
        base_vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
    )
    emit_strong_derived_from_inf_sequence(
        ending=ending,
        vowel=vowel,
        probability=probability,
        umlaut_vowels=OENormalizer.iumlaut([vowel]),
        emit_form_for_vowel=partial(emit_form_for_vowel, context),
        emit_sound_for_vowel=partial(emit_sound_for_vowel, context),
        on_participle=partial(on_participle, context),
        emit_imsg=partial(emit_imsg, context),
    )
