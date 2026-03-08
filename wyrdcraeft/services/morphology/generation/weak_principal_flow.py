"""Weak principal-part orchestration helpers for verb-generation flows."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Protocol

from wyrdcraeft.models.morphology import ParadigmPart, Word, _WeakPrincipalPartContext

from .weak_inflections import emit_weak_principal_part_sequence


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
#: Callback signature for weak infinitive-derived branch generation.
WeakInfBranchGenerator = Callable[
    [dict[str, str], Word, str, str, str, str, str, str, str | int | None],
    None,
]
#: Callback signature for weak ``PsInSg2``-derived branch generation.
WeakPsinsg2BranchGenerator = Callable[
    [dict[str, str], str, str, str, str, str, str | int | None],
    None,
]
#: Callback signature for weak ``PaInSg1``-derived branch generation.
WeakPainsg1BranchGenerator = Callable[
    [
        dict[str, str],
        Word,
        str,
        str,
        str,
        str,
        str,
        str,
        str | int | None,
        str,
        str,
    ],
    None,
]
#: Callback signature for one principal weak-form emission.
WeakPrincipalFormEmitter = Callable[
    [str, str, str, str, str, str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one context-aware weak derivation action.
WeakPrincipalContextAction = Callable[[_WeakPrincipalPartContext], None]
#: Callback signature for one context-aware weak participle action.
WeakPrincipalParticipleAction = Callable[[_WeakPrincipalPartContext, str], None]


def emit_weak_principal_pspt_participle(
    context: _WeakPrincipalPartContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: WeakParticipleAdder,
) -> None:
    """
    Attach a present participle emitted from a weak principal-part row.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared weak principal-part context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak participle derivation;
        this helper only routes the already-selected payload without changing
        emission order.

    """
    add_participle_to_adjectives(
        context.word,
        context.prefix,
        form_parts,
        is_past=False,
    )


def emit_weak_principal_papt_participle(
    context: _WeakPrincipalPartContext,
    form_parts: str,
    *,
    add_participle_to_adjectives: WeakParticipleAdder,
) -> None:
    """
    Attach a past participle emitted from a weak principal-part row.

    Side Effects:
        Adds one adjective-row candidate to session state.

    Args:
        context: Shared weak principal-part context.
        form_parts: Form-parts payload for the derived participle.

    Keyword Args:
        add_participle_to_adjectives: Callback that stores the participle row.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak participle derivation;
        this helper only routes the already-selected payload without changing
        emission order.

    """
    add_participle_to_adjectives(
        context.word,
        context.prefix,
        form_parts,
        is_past=True,
    )


def emit_weak_principal_inf_derivation(
    context: _WeakPrincipalPartContext,
    *,
    generate_weak_derived_from_inf: WeakInfBranchGenerator,
) -> None:
    """
    Emit weak infinitive-derived rows from a principal-part context.

    Side Effects:
        Writes generated rows and participle side effects to output/session.

    Args:
        context: Shared weak principal-part context.

    Keyword Args:
        generate_weak_derived_from_inf: Callback for infinitive-derived flow.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe dental weak-verb paradigms;
        this helper preserves legacy routing while delegating all emissions.

    """
    generate_weak_derived_from_inf(
        context.formhash,
        context.word,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.post_vowel,
        context.boundary,
        context.ending,
        context.probability,
    )


def emit_weak_principal_psinsg2_derivation(
    context: _WeakPrincipalPartContext,
    *,
    generate_weak_derived_from_psinsg2: WeakPsinsg2BranchGenerator,
) -> None:
    """
    Emit weak ``PsInSg2``-derived rows from a principal-part context.

    Side Effects:
        Writes generated rows to the morphology output stream.

    Args:
        context: Shared weak principal-part context.

    Keyword Args:
        generate_weak_derived_from_psinsg2: Callback for ``PsInSg2`` flow.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak inflection branch
        sequencing; this helper preserves that deterministic branch order.

    """
    generate_weak_derived_from_psinsg2(
        context.formhash,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.post_vowel,
        context.boundary,
        context.probability,
    )


def emit_weak_principal_painsg1_derivation(
    context: _WeakPrincipalPartContext,
    *,
    generate_weak_derived_from_painsg1: WeakPainsg1BranchGenerator,
) -> None:
    """
    Emit weak ``PaInSg1``-derived rows from a principal-part context.

    Side Effects:
        Writes generated rows and participle side effects to output/session.

    Args:
        context: Shared weak principal-part context.

    Keyword Args:
        generate_weak_derived_from_painsg1: Callback for ``PaInSg1`` flow.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental preterite
        derivation; this helper forwards the same contextual slots in the same
        order as the legacy flow.

    """
    generate_weak_derived_from_painsg1(
        context.formhash,
        context.word,
        context.prefix,
        context.pre_vowel,
        context.vowel,
        context.post_vowel,
        context.boundary,
        context.dental,
        context.probability,
        context.vowel_inf,
        context.vowel_pa,
    )


def generate_weak_verb_parts(  # noqa: PLR0913
    *,
    formhash: dict[str, str],
    word: Word,
    item: ParadigmPart,
    prefix: str,
    pre_vowel: str,
    root_vowel_actual: str,
    post_vowel: str,
    variant_id: int,
    para_id_num: str,
    vowel_inf: str,
    vowel_pa: str,
    emit_form: WeakPrincipalFormEmitter,
    on_pspt_participle: WeakPrincipalParticipleAction,
    on_papt_participle: WeakPrincipalParticipleAction,
    on_inf: WeakPrincipalContextAction,
    on_psinsg2: WeakPrincipalContextAction,
    on_painsg1: WeakPrincipalContextAction,
) -> None:
    """
    Route weak principal-part row generation through the shared inflection flow.

    Side Effects:
        Emits generated rows and participle side effects via callbacks.

    Args:
        formhash: Form metadata hash for the active branch.
        word: Lexeme record currently being generated.
        item: Active paradigm part.
        prefix: Prefix segment for the active part.
        pre_vowel: Stem segment before the active vowel.
        root_vowel_actual: Active vowel segment.
        post_vowel: Stem segment after the active vowel.
        variant_id: Variant identifier of the active part.
        para_id_num: Numeric paradigm identifier used in branch routing.
        vowel_inf: Exemplar infinitive vowel from the seed variant.
        vowel_pa: Exemplar preterite singular vowel from the seed variant.
        emit_form: Callback that emits one principal weak form.
        on_pspt_participle: Callback for ``PsPt`` participle side effects.
        on_papt_participle: Callback for ``PaPt`` participle side effects.
        on_inf: Callback for infinitive-derived weak branch generation.
        on_psinsg2: Callback for ``PsInSg2``-derived weak branch generation.
        on_painsg1: Callback for ``PaInSg1``-derived weak branch generation.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Note:
        Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
        (``data/Ondej_Tich_40-54-1.pdf``) describe weak-verb principal-part
        sequencing; this helper preserves legacy branch order by delegating to
        ``emit_weak_principal_part_sequence`` with the same callback order.

    """
    para_id = item.para_id
    ending = item.ending
    dental = item.dental
    boundary = item.boundary
    prob: str | int | None = 0
    context = _WeakPrincipalPartContext(
        formhash=formhash,
        word=word,
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=root_vowel_actual,
        post_vowel=post_vowel,
        boundary=boundary,
        ending=ending,
        dental=dental,
        probability=prob,
        vowel_inf=vowel_inf,
        vowel_pa=vowel_pa,
    )
    emit_weak_principal_part_sequence(
        para_id=para_id,
        para_id_num=para_id_num,
        variant_id=variant_id,
        prefix=prefix,
        default_parts=(pre_vowel, root_vowel_actual, post_vowel, boundary),
        item_parts=(item.pre_vowel, item.vowel, item.post_vowel, item.boundary),
        dental=dental,
        ending=ending,
        emit_form=emit_form,
        on_pspt_participle=partial(on_pspt_participle, context),
        on_papt_participle=partial(on_papt_participle, context),
        on_inf=partial(on_inf, context),
        on_psinsg2=partial(on_psinsg2, context),
        on_painsg1=partial(on_painsg1, context),
    )
