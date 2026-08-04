# ruff: noqa: I001,PLR0913,ARG002,D417,RUF100,PLC0415
import re
from collections.abc import Sequence
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    _ParadigmVariantDispatchContext,
    _StrongPrincipalPartContext,
    _StrongInfDerivationContext,
    _VariantPartDispatchContext,
    _WeakPrincipalPartContext,
    _WeakInfDerivationContext,
    _WeakPainsg1DerivationContext,
    _WeakPsinsg2DerivationContext,
    VerbParadigm,
    Word,
)
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologyStage,
)
from wyrdcraeft.services.morphology.session import (
    GenerationRunState,
    WordPool,
)
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_rows import generate_and_print_form as _generate_and_print_form
from .form_rows import generate_and_print_manual as _generate_and_print_manual
from .form_rows import (
    generate_and_print_form_with_sound_changes
    as _generate_and_print_form_with_sound_changes_row,
)
from .form_rows import emit_form_for_context as _emit_form_for_context_row
from .form_rows import emit_imsg_for_context as _emit_imsg_for_context_row
from .form_rows import (
    emit_sound_changed_form_for_context as _emit_sound_changed_form_for_context_row,
)
from .form_rows import print_one_form as _print_one_form
from .participles import (
    add_participle_to_adjectives as _add_participle_to_adjectives_session,
)
from .probability import probability_or_zero, probability_plus
from .scalar_utils import nz as _nz_scalar
from .scalar_utils import perl_numify as _perl_numify
from .shared import FormOutput
from .sound_changes import derive_papt_sound_changed_forms


def nz(val: str | int | None) -> str:
    """
    Treat '0' or None as empty string for logic checks, matching Perl's falsy
    behavior for these strings.

    Args:
        val: The value to check.

    Returns:
        The value as a string.

    """
    return _nz_scalar(val)


def perl_numify(val: str) -> float:
    """
    Approximate Perl scalar-to-number coercion for ``==`` comparisons.

    Args:
        val: Value to coerce.

    Returns:
        Numeric value extracted from the start of ``val``, or ``0.0``.

    """
    return _perl_numify(val)


def print_one_form(
    run_state: GenerationRunState, form_data: dict[str, str], output_file: FormOutput
) -> None:
    r"""
    Print one form to the output file.  A form in this context is a single form
    of a word.

    Notes:
        Matches Perl implementation of print_one_form function:

        .. code-block:: perl

            print(OUTPUT "$main::output_counter\t$formi\t$form{BT}\t$form{title}\t$form{stem}\t$form{form}\t$form{formParts}\t$form{var}\t" . (defined $form{probability} ? $form{probability} : "") . "\t$form{function}\t$form{wright}\t$form{paradigm}\t$form{paraID}\t$form{wordclass}\t$form{class1}\t$form{class2}\t$form{class3}\t$form{comment}\n");

        - In Perl, ``$form{probability}`` prints as empty string if undefined.
        - In Perl, if ``$count`` is greater than 0, a second line is printed with the probability incremented by 1.

    Args:
        run_state: Active generation run state tracking the output counter.
        form_data: The form data.
        output_file: The output file.

    """  # noqa: E501
    _print_one_form(run_state, form_data, output_file)


class StrongVerbGenerator:
    """
    Generator for Old English strong-verb form derivation.

    Handles the strong-paradigm branch of verb generation: principal-part
    emission across ablaut vowel variants, past-participle projection, and
    the infinitive-derived branch cascade (non-umlaut and umlaut forms, plus
    the ``PaInSg1``/``PaInPl`` side branches). Consumed by
    ``VerbFormGenerator``, which constructs one instance per run and calls
    ``generate_verb_parts`` once per strong-paradigm word/variant/part.

    Args:
        word_pool: Categorized word pool receiving derived participle rows.
        run_state: Cross-stage scalar run state for this run.
        output_file: Output handle receiving generated form rows.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
    ) -> None:
        """
        Initialize the strong-verb generator context.

        Args:
            word_pool: Categorized word pool receiving derived participle rows.
            run_state: Cross-stage scalar run state for this run.
            output_file: Output handle receiving generated form rows.

        """
        #: Categorized word pool receiving derived participle rows.
        self.word_pool = word_pool
        #: Cross-stage scalar run state for this run.
        self.run_state = run_state
        #: Output handle receiving generated form rows.
        self.output_file = output_file

    # -- low-level row-emission primitives -----------------------------------

    def _emit_form_for_context(  # noqa: PLR0913
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
        Emit one generated form for a fixed stem context.

        Side Effects:
            Writes one row to the morphology output stream.

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
            dental: Dental segment for weak forms.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _emit_form_for_context_row(
            self.run_state,
            self.output_file,
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

    def _emit_sound_changed_form_for_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        prob: str | int | None,
        *,
        dental: str | None = "",
        sound_change_prob_delta: int = 1,
    ) -> None:
        """
        Emit one source row and its sound-change derivatives for a stem context.

        Side Effects:
            Writes generated and derived rows to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation for the source row.

        Keyword Args:
            dental: Dental segment for weak-form contexts.
            sound_change_prob_delta: Probability delta used on derived forms.

        """
        _emit_sound_changed_form_for_context_row(
            self.run_state,
            self.output_file,
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            ending,
            function,
            prob,
            dental=dental,
            sound_change_prob_delta=sound_change_prob_delta,
        )

    def _emit_imsg_for_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit the imperative-singular row for one fixed stem context.

        Side Effects:
            Writes one ``ImSg`` row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            prob: Optional probability annotation.

        """
        _emit_imsg_for_context_row(
            self.run_state,
            self.output_file,
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            prob,
        )

    def _add_participle_to_adjectives(
        self, word: Word, prefix: str, form_parts: str, is_past: bool
    ) -> None:
        """
        Add a participle to adjectives.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            word: The word.
            prefix: The prefix.
            form_parts: The form parts.
            is_past: Whether the form is past.

        """
        _add_participle_to_adjectives_session(
            self.word_pool,
            word=word,
            prefix=prefix,
            form_parts=form_parts,
            is_past=is_past,
        )

    # -- vowel/sound/inf-derivation context primitives -----------------------

    def _emit_vowel_form_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        post_vowel: str,
        boundary: str,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_form_for_context(
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

    def _emit_vowel_sound_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        post_vowel: str,
        boundary: str,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        """
        self._emit_sound_changed_form_for_context(
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

    # -- infinitive-derived branch cascade -----------------------------------

    def _emit_derived_inf_form_for_vowel(  # noqa: PLR0913
        self,
        context: _StrongInfDerivationContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_vowel_form_context(
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

    def _emit_derived_inf_form_for_vowel_context(  # noqa: PLR0913
        self,
        context: _StrongInfDerivationContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_derived_inf_form_for_vowel(
            context,
            active_vowel,
            ending,
            function,
            prob,
        )

    def _emit_derived_inf_sound_for_vowel(  # noqa: PLR0913
        self,
        context: _StrongInfDerivationContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        """
        self._emit_vowel_sound_context(
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

    def _emit_derived_inf_sound_for_vowel_context(  # noqa: PLR0913
        self,
        context: _StrongInfDerivationContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        """
        self._emit_derived_inf_sound_for_vowel(
            context,
            active_vowel,
            ending,
            function,
            prob,
        )

    def _emit_derived_inf_participle(
        self, context: _StrongInfDerivationContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from infinitive-derived strong rows.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared strong infinitive-derivation context.
            form_parts: Form-parts payload for the derived participle.

        """
        self._add_participle_to_adjectives(
            context.word,
            context.prefix,
            form_parts,
            is_past=False,
        )

    def _emit_derived_inf_participle_context(
        self, context: _StrongInfDerivationContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from infinitive-derived strong rows.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared strong-derivation emission context.
            form_parts: Form-parts payload for the derived participle.

        """
        self._emit_derived_inf_participle(context, form_parts)

    def _emit_derived_inf_imsg(
        self, context: _StrongInfDerivationContext, prob: str | int | None
    ) -> None:
        """
        Emit the strong imperative-singular derivative for infinitive branches.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared strong infinitive-derivation context.
            prob: Optional probability annotation.

        """
        self._emit_imsg_for_context(
            context.formhash,
            context.prefix,
            context.pre_vowel,
            context.base_vowel,
            context.post_vowel,
            context.boundary,
            prob,
        )

    def _emit_derived_inf_imsg_context(
        self, context: _StrongInfDerivationContext, prob: str | int | None
    ) -> None:
        """
        Emit the strong imperative-singular derivative for infinitive branches.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared strong-derivation emission context.
            prob: Optional probability annotation.

        """
        self._emit_derived_inf_imsg(context, prob)

    def _emit_derived_from_inf_sequence(
        self,
        *,
        context: _StrongInfDerivationContext,
        ending: str,
        vowel: str,
        probability: str | int | None,
        umlaut_vowels: Sequence[str],
    ) -> None:
        """
        Emit the full strong-verb infinitive-derived sequence.

        Side Effects:
            Emits non-umlaut, imperative, participle, and umlaut rows.

        Args:
            context: Shared strong infinitive-derivation context.
            ending: Original paradigm ending from the infinitive principal part.
            vowel: Base infinitive vowel.
            probability: Base probability scalar for the branch.
            umlaut_vowels: Ordered umlaut vowel variants for the base vowel.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        probability_plus_one = probability_plus(probability, delta=1, empty_default=1)
        form_parts = self._emit_derived_from_inf_non_umlaut(
            context=context,
            vowel=vowel,
            ending=ending,
            probability=probability,
            probability_plus_one=probability_plus_one,
        )
        self._emit_derived_inf_participle_context(context, form_parts)
        self._emit_derived_inf_imsg_context(context, probability)

        for mv_idx, mvowel in enumerate(umlaut_vowels):
            mv_prob = int(probability) + mv_idx if probability is not None else mv_idx
            self._emit_umlaut_for_vowel(
                context=context,
                vowel=mvowel,
                probability=mv_prob,
            )

    def _emit_derived_from_inf_non_umlaut(
        self,
        *,
        context: _StrongInfDerivationContext,
        vowel: str,
        ending: str,
        probability: str | int | None,
        probability_plus_one: int,
    ) -> str:
        """
        Emit non-umlaut strong-verb forms derived from the infinitive principal part.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared strong infinitive-derivation context.
            vowel: Base infinitive vowel used for every emitted row.
            ending: Original paradigm ending from the infinitive part.
            probability: Base probability scalar.
            probability_plus_one: Incremented probability scalar.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Returns:
            Final participle ``formParts`` string used for adjective derivation.

        """
        # Local shorthand for this class's own bound emitter; the emission table
        # below is flat and unconditional, so every row goes to the same method.
        emit = self._emit_derived_inf_form_for_vowel_context

        if "an" in ending:
            emit(context, vowel, "anne", "IdIf", probability)
            emit(context, vowel, "enne", "IdIf", probability)
            _, participle_form_parts = emit(context, vowel, "ende", "PsPt", probability)

            emit(context, vowel, "e", "PsInSg1", probability)
            emit(context, vowel, "u", "PsInSg1", probability_plus_one)
            emit(context, vowel, "o", "PsInSg1", probability_plus_one)
            emit(context, vowel, "æ", "PsInSg1", probability_plus_one)

            emit(context, vowel, "aþ", "PsInPl", probability)
            emit(context, vowel, "eþ", "PsInPl", probability_plus_one)
            emit(context, vowel, "es", "PsInPl", probability_plus_one)
            emit(context, vowel, "as", "PsInPl", probability_plus_one)

            emit(context, vowel, "e", "PsSuSg", probability)
            emit(context, vowel, "en", "PsSuPl", probability)
            emit(context, vowel, "aþ", "ImPl", probability)
            return participle_form_parts

        emit(context, vowel, "nne", "IdIf", probability)
        _, participle_form_parts = emit(context, vowel, "nde", "PsPt", probability)

        emit(context, vowel, "0", "PsInSg1", probability)
        emit(context, vowel, "þ", "PsInPl", probability)
        emit(context, vowel, "0", "PsSuSg", probability)
        emit(context, vowel, "n", "PsSuPl", probability)
        emit(context, vowel, "þ", "ImPl", probability)
        return participle_form_parts

    def _emit_umlaut_for_vowel(
        self,
        *,
        context: _StrongInfDerivationContext,
        vowel: str,
        probability: int,
    ) -> None:
        """
        Emit umlaut-derived ``PsInSg2`` and ``PsInSg3`` strong-verb forms.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            context: Shared strong infinitive-derivation context.
            vowel: Umlauted vowel variant for this branch.
            probability: Base umlaut probability for this vowel variant.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        emit = self._emit_derived_inf_form_for_vowel_context
        emit_sound = self._emit_derived_inf_sound_for_vowel_context
        emit(context, vowel, "stu", "PsInSg2", probability + 1)
        emit(context, vowel, "est", "PsInSg2", probability + 1)
        emit(context, vowel, "ist", "PsInSg2", probability + 1)
        emit(context, vowel, "s", "PsInSg2", probability + 1)
        emit_sound(context, vowel, "st", "PsInSg2", probability)

        emit(context, vowel, "eþ", "PsInSg3", probability + 1)
        emit(context, vowel, "iþ", "PsInSg3", probability + 1)
        emit_sound(context, vowel, "þ", "PsInSg3", probability)

    def _dispatch_derived_from_principal_part(
        self,
        *,
        context: _StrongPrincipalPartContext,
        para_id: str,
        form_parts: str,
        active_vowel: str,
        probability: str | int | None,
    ) -> bool:
        """
        Dispatch and emit strong derived branches for one principal-part emission.

        Side Effects:
            Emits derived branch rows and participle side effects per ``para_id``.

        Args:
            context: Shared strong principal-part context.
            para_id: Principal function identifier from the paradigm row.
            form_parts: Emitted principal-form ``formParts`` string.
            active_vowel: Active vowel for the current branch context.
            probability: Probability scalar for derived branch emissions.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Returns:
            ``True`` when any derived branch was emitted, else ``False``.

        """
        invoked = False
        para_id_lower = para_id.lower()

        if para_id_lower == "papt":
            self._emit_principal_participle_context(context, form_parts)
            invoked = True

        if para_id_lower == "if":
            self._emit_principal_inf_derivation_context(
                context, active_vowel, probability
            )
            return True
        if para_id_lower == "painsg1":
            self._emit_painsg1_derived(
                context=context,
                active_vowel=active_vowel,
                probability=probability,
            )
            return True
        if para_id_lower == "painpl":
            self._emit_painpl_derived(
                context=context,
                active_vowel=active_vowel,
                probability=probability,
            )
            return True
        return invoked

    def _emit_principal_part_sequence(
        self,
        *,
        context: _StrongPrincipalPartContext,
        para_id: str,
        ending: str,
        vowels: Sequence[str],
    ) -> None:
        """
        Emit one strong principal-part sequence and dispatch derived branches.

        Note:
            Wright's strong-verb chapter groups verbs by vowel alternation classes,
            and Tichý's generation description likewise replaces the root vowel by
            paradigm-specific ablaut/umlaut options. This helper keeps that
            vowel-first branching order unchanged for parity.

        Side Effects:
            Emits forms and derived branch rows for each active vowel.

        Args:
            context: Shared strong principal-part context.
            para_id: Principal function identifier from the paradigm row.
            ending: Morphological ending from the active principal part.
            vowels: Ordered vowel variants to emit for the principal part.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        for vcount, active_vowel in enumerate(vowels):
            prob: str | int | None = 1 if vcount == 1 else None
            _, form_parts = self._emit_principal_form_for_vowel_context(
                context, active_vowel, ending, para_id, prob
            )
            self._dispatch_derived_from_principal_part(
                context=context,
                para_id=para_id,
                form_parts=form_parts,
                active_vowel=active_vowel,
                probability=prob,
            )

    def _emit_painsg1_derived(
        self,
        *,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        probability: str | int | None,
    ) -> None:
        """
        Emit ``PaInSg1``-derived strong-verb side branch forms.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared strong principal-part context.
            active_vowel: Active vowel for the current branch context.
            probability: Base probability scalar for branch emissions.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        self._emit_principal_form_for_vowel_context(
            context, active_vowel, "0", "PaInSg3", probability
        )

    def _emit_painpl_derived(
        self,
        *,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        probability: str | int | None,
    ) -> None:
        """
        Emit ``PaInPl``-derived strong-verb side branch forms.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared strong principal-part context.
            active_vowel: Active vowel for the current branch context.
            probability: Base probability scalar for branch emissions.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        emit = self._emit_principal_form_for_vowel_context
        emit(context, active_vowel, "e", "PaInSg2", probability)
        emit(context, active_vowel, "e", "PaSuSg", probability)
        emit(context, active_vowel, "en", "PaSuPl", probability)

    # -- principal-part generation --------------------------------------------

    def _emit_principal_form_for_vowel_context(
        self,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
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

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_vowel_form_context(
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

    def _emit_principal_participle_context(
        self, context: _StrongPrincipalPartContext, form_parts: str
    ) -> None:
        """
        Attach a past participle emitted from a strong principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared strong principal-part context.
            form_parts: Form-parts payload for the derived participle.

        """
        self._add_participle_to_adjectives(
            context.word,
            context.prefix,
            form_parts,
            is_past=True,
        )

    def _emit_principal_inf_derivation_context(
        self,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit strong infinitive-derived rows from principal context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared strong principal-part context.
            active_vowel: Active stem vowel for this derivation branch.
            prob: Optional probability annotation.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe strong principal-part
            branching into infinitive-derived rows; this helper keeps that
            sequencing intact.

        """
        inf_context = _StrongInfDerivationContext(
            formhash=context.formhash,
            word=context.word,
            prefix=context.prefix,
            pre_vowel=context.pre_vowel,
            base_vowel=active_vowel,
            post_vowel=context.post_vowel,
            boundary=context.boundary,
        )
        self._emit_derived_from_inf_sequence(
            context=inf_context,
            ending=context.ending,
            vowel=active_vowel,
            probability=prob,
            umlaut_vowels=OENormalizer.iumlaut([active_vowel]),
        )

    def generate_verb_parts(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        item: ParadigmPart,
        prefix: str,
        pre_vowel: str,
        root_vowel_actual: str,  # noqa: ARG002
        post_vowel: str,
        variant_id: int,  # noqa: ARG002
    ) -> None:
        """
        Entry point: route one strong-paradigm part into principal-part generation.

        Matches Perl's ``generate_strong_verb_parts``. Called once per
        strong-paradigm word/variant/part by ``VerbFormGenerator._process_part``.

        Side Effects:
            Emits generated rows and participle side effects.

        Args:
            formhash: The form hash.
            word: The word to process.
            item: The part to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            root_vowel_actual: Unused; retained for call-site compatibility with
                the legacy signature (only ``item.vowel`` is used).
            post_vowel: The post-vowel.
            variant_id: Unused; retained for call-site compatibility with the
                legacy signature.

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
        self._emit_principal_part_sequence(
            context=context,
            para_id=para_id,
            ending=ending,
            vowels=[item.vowel],
        )


#: Stem-part tuple ``(pre_vowel, vowel, post_vowel, boundary)``.
WeakStemParts = tuple[str, str, str, str]


class WeakVerbGenerator:
    """
    Generator for Old English weak-verb form derivation.

    Handles the weak-paradigm branch of verb generation: principal-part
    emission (including the legacy raw item-shape window), past/present
    participle projection, and the three derived-branch cascades (infinitive,
    ``PsInSg2``, ``PaInSg1``). Consumed by ``VerbFormGenerator``, which
    constructs one instance per run and calls ``generate_verb_parts`` once
    per weak-paradigm word/variant/part.

    Args:
        word_pool: Categorized word pool receiving derived participle rows.
        run_state: Cross-stage scalar run state for this run.
        output_file: Output handle receiving generated form rows.

    """

    #: Lower bound (exclusive) for using raw item-shape weak forms.
    WEAK_ITEM_SHAPE_MIN_ID: Final[int] = 88
    #: Upper bound (exclusive) for using raw item-shape weak forms.
    WEAK_ITEM_SHAPE_MAX_ID: Final[int] = 93

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
    ) -> None:
        """
        Initialize the weak-verb generator context.

        Args:
            word_pool: Categorized word pool receiving derived participle rows.
            run_state: Cross-stage scalar run state for this run.
            output_file: Output handle receiving generated form rows.

        """
        #: Categorized word pool receiving derived participle rows.
        self.word_pool = word_pool
        #: Cross-stage scalar run state for this run.
        self.run_state = run_state
        #: Output handle receiving generated form rows.
        self.output_file = output_file

    # -- low-level row-emission primitives -----------------------------------

    def _emit_form_for_context(  # noqa: PLR0913
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
        Emit one generated form for a fixed stem context.

        Side Effects:
            Writes one row to the morphology output stream.

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
            dental: Dental segment for weak forms.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _emit_form_for_context_row(
            self.run_state,
            self.output_file,
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

    def _add_participle_to_adjectives(
        self, word: Word, prefix: str, form_parts: str, is_past: bool
    ) -> None:
        """
        Add a participle to adjectives.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            word: The word.
            prefix: The prefix.
            form_parts: The form parts.
            is_past: Whether the form is past.

        """
        _add_participle_to_adjectives_session(
            self.word_pool,
            word=word,
            prefix=prefix,
            form_parts=form_parts,
            is_past=is_past,
        )

    def _generate_and_print_form(  # noqa: PLR0913
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
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        """
        Generate and print a form.

        Note:
            Kept as a method (not a bare call into ``form_rows.py``) because
            ``form_rows.generate_and_print_form`` declares ``prob`` keyword-only
            while every weak-branch consumer here passes it positionally; this
            method performs that positional-to-keyword adaptation, so it is
            not a pure one-line forward.

            Matches Perl implementation of generate_and_print_form function:

            .. code-block:: perl

                if ($formhash->{class1} eq "s") {
                    $form_parts = "$prefix-$pre_vowel-$vowel-$post_vowel-$boundary-$ending";
                } else {
                    $form_parts = "$prefix-$pre_vowel-$vowel-$post_vowel-$boundary-" . (defined $dental ? $dental : "") . "-$ending";
                }

        Args:
            formhash: The form hash.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            dental: The dental.
            ending: The ending.
            function: The function.

        Keyword Args:
            prob: The probability.

        Returns:
            The form and form parts as a tuple.

        """  # noqa: E501
        return _generate_and_print_form(
            self.run_state,
            self.output_file,
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            dental,
            ending,
            function,
            prob=prob,
        )

    # -- weak-inflection helpers (former weak_inflections.py) ---------------

    def _has_perl_inf_vowel_ending(self, fp_base: str) -> bool:
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

    def _has_regex_vowel_ending(self, fp_base: str) -> bool:
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

    def _emit_weak_derived_from_inf_general(  # noqa: PLR0913
        self,
        *,
        context: _WeakInfDerivationContext,
        original_ending: str,
        iending: str,
        probability: str | int | None,
        probability_plus_one: int,
        perl_inf_vowel_end: bool,
        regex_vowel_end: bool,
    ) -> str:
        """
        Emit weak-verb forms derived from infinitives for the general class2 branch.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared weak infinitive-derivation context.
            original_ending: Source infinitive ending from the paradigm.
            iending: Derived ``i``-prefixed dental component.
            probability: Base probability scalar for principal forms.
            probability_plus_one: Incremented probability scalar.
            perl_inf_vowel_end: Perl-style vowel-ending predicate.
            regex_vowel_end: Regex-based vowel-ending predicate.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Raises:
            None.

        Returns:
            Final participle ``formParts`` string used for adjective derivation.

        """
        emit_row = self._emit_weak_derived_inf_form

        emit_row(context, None, original_ending, "if", probability)
        if perl_inf_vowel_end:
            emit_row(context, None, "n", "if", probability)

        emit_row(context, iending, "anne", "IdIf", probability)
        emit_row(context, iending, "enne", "IdIf", probability)
        if perl_inf_vowel_end:
            emit_row(context, iending, "nne", "IdIf", probability)

        emit_row(context, iending, "e", "PsInSg1", probability)
        emit_row(context, iending, "u", "PsInSg1", probability_plus_one)
        emit_row(context, iending, "o", "PsInSg1", probability_plus_one)
        emit_row(context, iending, "æ", "PsInSg1", probability_plus_one)
        if perl_inf_vowel_end:
            emit_row(context, None, "0", "PsInSg1", probability)

        emit_row(context, iending, "aþ", "PsInPl", probability)
        emit_row(context, iending, "eþ", "PsInPl", probability_plus_one)
        emit_row(context, iending, "es", "PsInPl", probability_plus_one)
        emit_row(context, iending, "as", "PsInPl", probability_plus_one)
        if perl_inf_vowel_end:
            emit_row(context, iending, "þ", "PsInPl", probability)

        emit_row(context, iending, "e", "PsSuSg", probability)
        if perl_inf_vowel_end:
            emit_row(context, None, "0", "PsSuSg", probability)

        emit_row(context, iending, "en", "PsSuPl", probability)
        if regex_vowel_end:
            emit_row(context, iending, "n", "PsSuPl", probability)

        emit_row(context, iending, "aþ", "ImPl", probability)
        if perl_inf_vowel_end:
            emit_row(context, None, "þ", "ImPl", probability)

        _, participle_form_parts = emit_row(
            context, iending, "ende", "PsPt", probability
        )
        if perl_inf_vowel_end:
            _, participle_form_parts = emit_row(
                context, iending, "nde", "PsPt", probability
            )
        return participle_form_parts

    def _emit_weak_derived_from_inf_class2_variant(
        self,
        *,
        context: _WeakInfDerivationContext,
        iending: str,
        perl_inf_vowel_end: bool,
        regex_vowel_end: bool,
    ) -> str:
        """
        Emit weak-verb forms for one variant of the class2-special infinitive branch.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared weak infinitive-derivation context.
            iending: Class2 variant dental component (``ig``, ``ige``, or ``""``).
            perl_inf_vowel_end: Perl-style vowel-ending predicate.
            regex_vowel_end: Regex-based vowel-ending predicate.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Raises:
            None.

        Returns:
            Final participle ``formParts`` string used for adjective derivation.

        """
        emit_row = self._emit_weak_derived_inf_form
        prob_c2 = 0

        if iending != "":
            emit_row(context, iending, "an", "if", prob_c2)
            if perl_inf_vowel_end:
                emit_row(context, None, "n", "if", prob_c2)
        elif perl_inf_vowel_end:
            emit_row(context, None, "n", "if", prob_c2)

        emit_row(context, iending, "anne", "IdIf", prob_c2)
        emit_row(context, iending, "enne", "IdIf", prob_c2)
        if perl_inf_vowel_end:
            emit_row(context, iending, "nne", "IdIf", prob_c2)

        emit_row(context, iending, "a", "ImSg", prob_c2)
        if perl_inf_vowel_end:
            emit_row(context, None, "0", "ImSg", prob_c2)

        emit_row(context, iending, "e", "PsInSg1", prob_c2)
        emit_row(context, iending, "u", "PsInSg1", prob_c2 + 1)
        emit_row(context, iending, "o", "PsInSg1", prob_c2 + 1)
        emit_row(context, iending, "æ", "PsInSg1", prob_c2 + 1)
        if perl_inf_vowel_end:
            emit_row(context, None, "0", "PsInSg1", prob_c2)

        emit_row(context, iending, "aþ", "PsInPl", prob_c2)
        emit_row(context, iending, "eþ", "PsInPl", prob_c2 + 1)
        emit_row(context, iending, "es", "PsInPl", prob_c2 + 1)
        emit_row(context, iending, "as", "PsInPl", prob_c2 + 1)
        if perl_inf_vowel_end:
            emit_row(context, iending, "þ", "PsInPl", prob_c2)

        emit_row(context, iending, "e", "PsSuSg", prob_c2)
        if perl_inf_vowel_end:
            emit_row(context, None, "0", "PsSuSg", prob_c2)

        emit_row(context, iending, "en", "PsSuPl", prob_c2)
        if regex_vowel_end:
            emit_row(context, iending, "n", "PsSuPl", prob_c2)

        emit_row(context, iending, "aþ", "ImPl", prob_c2)
        if perl_inf_vowel_end:
            emit_row(context, None, "þ", "ImPl", prob_c2)

        _, participle_form_parts = emit_row(context, iending, "ende", "PsPt", prob_c2)
        if perl_inf_vowel_end:
            _, participle_form_parts = emit_row(
                context, iending, "nde", "PsPt", prob_c2
            )
        return participle_form_parts

    def _emit_weak_derived_from_inf_by_class2(  # noqa: PLR0913
        self,
        *,
        context: _WeakInfDerivationContext,
        class2: str | None,
        original_ending: str,
        probability: str | int | None,
        probability_plus_one: int,
        perl_inf_vowel_end: bool,
        regex_vowel_end: bool,
    ) -> None:
        """
        Emit weak infinitive-derived branches according to ``class2`` routing.

        Side Effects:
            Emits generated rows and stores derived participles.

        Args:
            context: Shared weak infinitive-derivation context.
            class2: Weak-verb class2 marker from form metadata.
            original_ending: Source infinitive ending from the paradigm.
            probability: Base probability scalar for principal forms.
            probability_plus_one: Incremented probability scalar.
            perl_inf_vowel_end: Perl-style vowel-ending predicate.
            regex_vowel_end: Regex-based vowel-ending predicate.

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
            fp = self._emit_weak_derived_from_inf_general(
                context=context,
                original_ending=original_ending,
                iending=iending_general,
                probability=probability,
                probability_plus_one=probability_plus_one,
                perl_inf_vowel_end=perl_inf_vowel_end,
                regex_vowel_end=regex_vowel_end,
            )
            self._emit_weak_derived_inf_participle(context, fp)

        # Perl: if ($word->{class2} == 2)
        elif class2 == "2":
            for iending in ["ig", "ige", ""]:
                fp = self._emit_weak_derived_from_inf_class2_variant(
                    context=context,
                    iending=iending,
                    perl_inf_vowel_end=perl_inf_vowel_end,
                    regex_vowel_end=regex_vowel_end,
                )
                self._emit_weak_derived_inf_participle(context, fp)

    def _emit_weak_derived_from_inf_sequence(
        self,
        *,
        context: _WeakInfDerivationContext,
        class2: str | None,
        original_ending: str,
        probability: str | int | None,
    ) -> None:
        """
        Emit weak-verb infinitive-derived branches for one principal-part context.

        Side Effects:
            Emits generated rows and stores derived participles.

        Args:
            context: Shared weak infinitive-derivation context.
            class2: Weak-verb class2 marker from form metadata.
            original_ending: Source infinitive ending from the paradigm.
            probability: Base probability scalar for derived forms.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        effective_probability = probability if probability is not None else ""
        probability_plus_one = probability_plus(
            effective_probability,
            delta=1,
            empty_default=1,
        )
        fp_base = (
            f"{context.prefix}-{context.pre_vowel}-{context.vowel}"
            f"-{context.post_vowel}-{context.boundary}"
        )

        self._emit_weak_derived_from_inf_by_class2(
            context=context,
            class2=class2,
            original_ending=original_ending,
            probability=effective_probability,
            probability_plus_one=probability_plus_one,
            perl_inf_vowel_end=self._has_perl_inf_vowel_ending(fp_base),
            regex_vowel_end=self._has_regex_vowel_ending(fp_base),
        )

    def _emit_weak_derived_from_psinsg2(
        self,
        *,
        context: _WeakPsinsg2DerivationContext,
        probability: str | int | None,
        probability_plus_one: int,
        post_vowel_simple: str,
    ) -> None:
        """
        Emit weak-verb forms derived from the ``PsInSg2`` principal part.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            context: Shared weak ``PsInSg2`` derivation context.
            probability: Base probability scalar.
            probability_plus_one: Incremented probability scalar.
            post_vowel_simple: Simplified post-vowel segment for this branch.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Raises:
            None.

        Returns:
            ``None``.

        """
        emit_row = self._emit_weak_psinsg2_form_with_post_derivation_context
        emit_sound_row = self._emit_weak_psinsg2_sound_with_post_derivation_context
        pvs = post_vowel_simple

        emit_row(context, "est", "PsInSg2", probability_plus_one, pvs)
        emit_row(context, "es", "PsInSg2", probability_plus_one, pvs)
        emit_row(context, "ist", "PsInSg2", probability_plus_one, pvs)
        emit_row(context, "s", "PsInSg2", probability_plus_one, pvs)

        emit_sound_row(context, "st", "PsInSg2", probability, 1, pvs)

        emit_row(context, "eþ", "PsInSg3", probability_plus_one, pvs)
        emit_row(context, "ieþ", "PsInSg3", probability_plus_one, pvs)
        emit_row(context, "iþ", "PsInSg3", probability_plus_one, pvs)

        emit_sound_row(context, "þ", "PsInSg3", probability_plus_one, 0, pvs)

        emit_row(context, "e", "ImSg", probability, pvs)
        emit_row(context, "ie", "ImSg", probability, pvs)
        emit_row(context, "0", "ImSg", probability, pvs)

    def _emit_weak_derived_from_psinsg2_context(
        self,
        *,
        context: _WeakPsinsg2DerivationContext,
        probability: str | int | None,
        post_vowel: str,
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived forms for one principal-part stem context.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            context: Shared weak ``PsInSg2`` derivation context.
            probability: Base probability scalar for the branch.
            post_vowel: Post-vowel segment from the principal-part stem.

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

        self._emit_weak_derived_from_psinsg2(
            context=context,
            probability=effective_probability,
            probability_plus_one=probability_plus_one,
            post_vowel_simple=post_vowel_simple,
        )

    def _emit_weak_derived_from_painsg1_variant(
        self,
        *,
        context: _WeakPainsg1DerivationContext,
        vowel: str,
        post_vowel_simple: str,
        probability: int,
    ) -> str:
        """
        Emit one weak-verb ``PaInSg1``-derived vowel variant sequence.

        Side Effects:
            Writes generated and manual rows to the morphology output stream.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            vowel: Active vowel for this variant.
            post_vowel_simple: Simplified post-vowel segment.
            probability: Base probability for this variant.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Raises:
            None.

        Returns:
            ``formParts`` string used for participle adjective derivation.

        """
        emit_row = self._emit_weak_painsg1_form_for_vowel_from_context
        emit_manual = self._emit_weak_painsg1_manual_context
        pvs = post_vowel_simple

        emit_row(context, vowel, "e", "PaInSg1", probability, pvs)

        emit_row(context, vowel, "est", "PaInSg2", probability, pvs)
        emit_row(context, vowel, "es", "PaInSg2", probability + 1, pvs)

        emit_row(context, vowel, "e", "PaInSg3", probability, pvs)
        emit_row(context, vowel, "on", "PaInPl", probability, pvs)
        emit_row(context, vowel, "e", "PaSuSg", probability, pvs)
        emit_row(context, vowel, "en", "PaSuPl", probability, pvs)

        form_parts = (
            f"{context.prefix}-{context.pre_vowel}-{vowel}"
            f"-{post_vowel_simple}-{context.boundary}-{context.dental}"
        )
        form = form_parts.replace("0", "").replace("-", "")
        emit_manual(context, form, form_parts, "PaPt", probability)

        for sound_changed_form in derive_papt_sound_changed_forms(form):
            emit_manual(
                context, sound_changed_form, form_parts, "PaPt", probability + 1
            )

        return form_parts

    def _emit_weak_derived_from_painsg1_sequence(  # noqa: PLR0913
        self,
        *,
        context: _WeakPainsg1DerivationContext,
        vowel: str,
        vowel_inf: str,
        vowel_pa: str,
        post_vowel_simple: str,
        probability: str | int | None,
    ) -> None:
        """
        Emit all weak ``PaInSg1``-derived vowel variants for one principal context.

        Side Effects:
            Emits one variant sequence and one participle per emitted vowel.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            vowel: Principal ``PaInSg1`` vowel segment.
            vowel_inf: Infinitive vowel from variant 0.
            vowel_pa: Preterite singular vowel from variant 0.
            post_vowel_simple: Simplified post-vowel segment.
            probability: Base probability scalar for variant sequencing.

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
            form_parts = self._emit_weak_derived_from_painsg1_variant(
                context=context,
                vowel=current_vowel,
                post_vowel_simple=post_vowel_simple,
                probability=base_probability + vcount,
            )
            self._emit_weak_painsg1_participle_context(context, form_parts)

    def _emit_weak_derived_from_painsg1_context(  # noqa: PLR0913
        self,
        *,
        context: _WeakPainsg1DerivationContext,
        vowel: str,
        post_vowel: str,
        vowel_inf: str,
        vowel_pa: str,
        probability: str | int | None,
    ) -> None:
        """
        Emit weak ``PaInSg1`` derivatives for a fully bound stem context.

        Note:
            Wright treats weak preterites as dental-suffix formations, and Tichý's
            pipeline generates verbal participles with verbs before adjective
            inflection. This helper keeps that ``PaInSg1`` ordering intact.

        Side Effects:
            Emits generated rows and stores derived participles.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            vowel: Base ``PaInSg1`` vowel segment.
            post_vowel: Post-vowel stem segment before simplification.
            vowel_inf: Infinitive vowel from variant 0.
            vowel_pa: Preterite singular vowel from variant 0.
            probability: Base probability scalar for this branch.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        post_vowel_simple = re.sub(r"(.)\1", r"\1", post_vowel)

        self._emit_weak_derived_from_painsg1_sequence(
            context=context,
            vowel=vowel,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            post_vowel_simple=post_vowel_simple,
            probability=probability,
        )

    def _is_weak_item_shape_window(self, para_id_num: str) -> bool:
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
        return self.WEAK_ITEM_SHAPE_MIN_ID < para_id_int < self.WEAK_ITEM_SHAPE_MAX_ID

    def _should_use_weak_item_shape(
        self,
        para_id_num: str,
        *,
        paradigm_type: str,
    ) -> bool:
        """
        Return whether weak generation should emit from ``para_vb`` item parts.

        Note:
            Anomalous (``a``) and preterite-present (``pp``) paradigms store fully
            specified segments in ``para_vb.txt``; regular weak verbs in the legacy
            ``89``--``92`` id window do the same. Other weak verbs derive forms from
            principal-part branches. Part-of-speech scope: ``verb``.

        Args:
            para_id_num: Paradigm numeric ID string.

        Keyword Args:
            paradigm_type: ``VerbParadigm.type`` label from the active paradigm row.

        Returns:
            ``True`` when generation should use raw paradigm item shape.

        """
        if paradigm_type in {"a", "pp"}:
            return True
        return self._is_weak_item_shape_window(para_id_num)

    def _emit_weak_principal_form(  # noqa: PLR0913
        self,
        *,
        para_id: str,
        formhash: dict[str, str],
        prefix: str,
        default_parts: WeakStemParts,
        item_parts: WeakStemParts,
        dental: str | None,
        ending: str,
        variant_id: int,
        use_item_shape: bool,
    ) -> str:
        """
        Emit one weak principal form and return emitted ``formParts``.

        Side Effects:
            Writes one principal-form row to the morphology output stream.

        Args:
            para_id: Paradigm function identifier.
            formhash: Form metadata hash for the active branch.
            prefix: Word prefix component.
            default_parts: ``(pre_vowel, vowel, post_vowel, boundary)`` tuple.
            item_parts: Raw item tuple ``(pre_vowel, vowel, post_vowel, boundary)``.
            dental: Dental segment.
            ending: Paradigm ending.
            variant_id: Variant index for principal probability rules.
            use_item_shape: Whether to emit from raw item parts.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Raises:
            None.

        Returns:
            Emitted ``formParts`` string.

        """
        if use_item_shape:
            pre_vowel, vowel, post_vowel, boundary = item_parts
            _, form_parts = self._emit_weak_principal_form_context(
                formhash,
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
        _, form_parts = self._emit_weak_principal_form_context(
            formhash,
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

    def _emit_weak_principal_part_sequence(  # noqa: PLR0913
        self,
        *,
        context: _WeakPrincipalPartContext,
        para_id: str,
        para_id_num: str,
        paradigm_type: str,
        variant_id: int,
        prefix: str,
        default_parts: WeakStemParts,
        item_parts: WeakStemParts,
        dental: str | None,
        ending: str,
    ) -> None:
        """
        Emit one weak principal part and route all dependent derivation branches.

        Side Effects:
            Emits principal-form rows and triggers derived branch generation.

        Args:
            context: Shared weak principal-part context.
            para_id: Principal function identifier from the paradigm row.
            para_id_num: Numeric paradigm ID used for legacy shape branching.
            paradigm_type: ``VerbParadigm.type`` label for item-shape routing.
            variant_id: Variant index for principal probability rules.
            prefix: Word prefix component.
            default_parts: Stem parts from normalized root extraction.
            item_parts: Stem parts from raw paradigm item values.
            dental: Dental segment from the paradigm item.
            ending: Morphological ending from the paradigm item.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        use_item_shape = self._should_use_weak_item_shape(
            para_id_num,
            paradigm_type=paradigm_type,
        )
        form_parts = self._emit_weak_principal_form(
            para_id=para_id,
            formhash=context.formhash,
            prefix=prefix,
            default_parts=default_parts,
            item_parts=item_parts,
            dental=dental,
            ending=ending,
            variant_id=variant_id,
            use_item_shape=use_item_shape,
        )
        self._dispatch_weak_principal_part_derivations(
            context=context,
            para_id=para_id,
            use_item_shape=use_item_shape,
            form_parts=form_parts,
        )

    def _dispatch_weak_derived_forms(
        self,
        *,
        context: _WeakPrincipalPartContext,
        para_id: str,
        use_item_shape: bool,
    ) -> bool:
        """
        Dispatch weak derived-form generation for one principal paradigm function.

        Side Effects:
            Generates one derived branch when a derived branch applies.

        Args:
            context: Shared weak principal-part context.
            para_id: Principal function identifier from the paradigm row.
            use_item_shape: Whether generation is in raw item-shape mode.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Raises:
            Does not raise directly.

        Returns:
            ``True`` when a derived branch ran, otherwise ``False``.

        """
        if use_item_shape:
            return False

        para_id_lower = para_id.lower()
        if para_id_lower == "if":
            self._emit_weak_principal_inf_derivation(context)
            return True
        if para_id_lower == "psinsg2":
            self._emit_weak_principal_psinsg2_derivation(context)
            return True
        if para_id_lower == "painsg1":
            self._emit_weak_principal_painsg1_derivation(context)
            return True
        return False

    def _dispatch_weak_principal_part_derivations(
        self,
        *,
        context: _WeakPrincipalPartContext,
        para_id: str,
        use_item_shape: bool,
        form_parts: str,
    ) -> bool:
        """
        Dispatch weak branch derivations and participle side effects per principal part.

        Side Effects:
            Stores derived participles and generates derived branches.

        Args:
            context: Shared weak principal-part context.
            para_id: Principal function identifier from the paradigm row.
            use_item_shape: Whether generation is in raw item-shape mode.
            form_parts: Emitted principal-form ``formParts`` string.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Returns:
            ``True`` when a derived branch ran, otherwise ``False``.

        """
        para_id_lower = para_id.lower()
        if para_id_lower == "pspt":
            self._emit_weak_principal_pspt_participle(context, form_parts)
        if para_id_lower == "papt":
            self._emit_weak_principal_papt_participle(context, form_parts)

        return self._dispatch_weak_derived_forms(
            context=context,
            para_id=para_id,
            use_item_shape=use_item_shape,
        )

    # -- weak principal-part orchestration (former weak_principal_flow.py) --

    def _emit_weak_principal_pspt_participle(
        self,
        context: _WeakPrincipalPartContext,
        form_parts: str,
    ) -> None:
        """
        Attach a present participle emitted from a weak principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak participle derivation;
            this helper only routes the already-selected payload without changing
            emission order.

        """
        self._add_participle_to_adjectives(
            context.word,
            context.prefix,
            form_parts,
            is_past=False,
        )

    def _emit_weak_principal_papt_participle(
        self,
        context: _WeakPrincipalPartContext,
        form_parts: str,
    ) -> None:
        """
        Attach a past participle emitted from a weak principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak participle derivation;
            this helper only routes the already-selected payload without changing
            emission order.

        """
        self._add_participle_to_adjectives(
            context.word,
            context.prefix,
            form_parts,
            is_past=True,
        )

    def _emit_weak_principal_inf_derivation(
        self,
        context: _WeakPrincipalPartContext,
    ) -> None:
        """
        Emit weak infinitive-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental derivation from
            principal parts; this helper preserves that branch order.

        """
        self._generate_weak_derived_from_inf(
            formhash=context.formhash,
            word=context.word,
            prefix=context.prefix,
            pre_vowel=context.pre_vowel,
            vowel=context.vowel,
            post_vowel=context.post_vowel,
            boundary=context.boundary,
            original_ending=context.ending,
            probability=context.probability,
        )

    def _emit_weak_principal_psinsg2_derivation(
        self,
        context: _WeakPrincipalPartContext,
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived rows from a principal-part context.

        Side Effects:
            Writes generated and sound-changed rows to the morphology output stream.

        Args:
            context: Shared weak principal-part context.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak branch alternations for
            present singular forms; this helper preserves that routing.

        """
        self._generate_weak_derived_from_psinsg2(
            formhash=context.formhash,
            prefix=context.prefix,
            pre_vowel=context.pre_vowel,
            vowel=context.vowel,
            post_vowel=context.post_vowel,
            boundary=context.boundary,
            probability=context.probability,
        )

    def _emit_weak_principal_painsg1_derivation(
        self,
        context: _WeakPrincipalPartContext,
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental-preterite
            derivation; this helper keeps branch order intact.

        """
        self._generate_weak_derived_from_painsg1(
            formhash=context.formhash,
            word=context.word,
            prefix=context.prefix,
            pre_vowel=context.pre_vowel,
            vowel=context.vowel,
            post_vowel=context.post_vowel,
            boundary=context.boundary,
            dental=context.dental or "",
            probability=context.probability,
            vowel_inf=context.vowel_inf,
            vowel_pa=context.vowel_pa,
        )

    def _generate_weak_verb_parts(  # noqa: PLR0913
        self,
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
    ) -> None:
        """
        Route weak principal-part row generation through the shared inflection flow.

        Side Effects:
            Emits generated rows and participle side effects.

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

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak-verb principal-part
            sequencing; this helper preserves legacy branch order by delegating to
            ``_emit_weak_principal_part_sequence``.

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
        self._emit_weak_principal_part_sequence(
            context=context,
            para_id=para_id,
            para_id_num=para_id_num,
            paradigm_type=str(formhash.get("class1", "")),
            variant_id=variant_id,
            prefix=prefix,
            default_parts=(pre_vowel, root_vowel_actual, post_vowel, boundary),
            item_parts=(item.pre_vowel, item.vowel, item.post_vowel, item.boundary),
            dental=dental,
            ending=ending,
        )

    # -- weak-derivation orchestration (former weak_derivation_flow.py) -----

    def _emit_weak_principal_form_context(  # noqa: PLR0913
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

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental-row emission;
            this helper only maps the legacy positional slots onto the low-level
            row emitter so callback order, probability flow, and form-part
            assembly remain parity-locked.

        """
        return self._emit_form_for_context(
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

    def _emit_weak_painsg1_form_for_vowel_from_context(  # noqa: PLR0913
        self,
        context: _WeakPainsg1DerivationContext,
        current_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> tuple[str, str]:
        """
        Emit one weak ``PaInSg1`` row for a selected vowel variant.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            current_vowel: Selected vowel for the emitted branch.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment for this branch.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PaInSg1`` variants;
            this helper preserves the legacy emitter slot ordering, in which the
            simplified post-vowel takes the ``post_vowel`` slot.

        """
        return self._generate_and_print_form(
            context.formhash,
            context.prefix,
            context.pre_vowel,
            current_vowel,
            post_vowel_simple,
            context.boundary,
            context.dental,
            ending,
            function,
            prob,
        )

    def _emit_weak_painsg1_manual_context(  # noqa: PLR0913
        self,
        context: _WeakPainsg1DerivationContext,
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
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

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PaInSg1`` output as
            regular branch emission; this helper preserves ordering and slots.

        """
        _generate_and_print_manual(
            self.run_state,
            self.output_file,
            context.formhash,
            form,
            form_parts,
            function,
            prob,
        )

    def _emit_weak_painsg1_participle_context(
        self,
        context: _WeakPainsg1DerivationContext,
        form_parts: str,
    ) -> None:
        """
        Attach a past participle emitted from a weak ``PaInSg1`` branch.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            form_parts: Form-parts payload for the derived participle.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe participle derivation in weak
            paradigms; this helper forwards payloads without altering sequencing.

        """
        self._add_participle_to_adjectives(
            context.word,
            context.prefix,
            form_parts,
            is_past=True,
        )

    def _emit_weak_derived_inf_form(
        self,
        context: _WeakInfDerivationContext,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
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

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental derivation;
            this helper only routes the same slots to the principal-form emitter.

        """
        return self._emit_weak_principal_form_context(
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

    def _emit_weak_psinsg2_form_with_post_derivation_context(
        self,
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
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

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak ``PsInSg2`` branch
            propagation; this helper unpacks context without changing row order.
            The ``dental`` slot is unconditionally ``None`` for this branch, as in
            the legacy flow.

        """
        self._generate_and_print_form(
            context.formhash,
            context.prefix,
            context.pre_vowel,
            context.vowel,
            post_vowel_simple,
            context.boundary,
            None,
            ending,
            function,
            prob,
        )

    def _emit_weak_psinsg2_sound_with_post_derivation_context(  # noqa: PLR0913
        self,
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        prob: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
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

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak sound-change branch
            routing; this helper preserves slot order and probability plumbing.
            The ``dental`` slot is unconditionally ``None`` for this branch, as in
            the legacy flow.

        """
        _generate_and_print_form_with_sound_changes_row(
            self.run_state,
            self.output_file,
            context.formhash,
            context.prefix,
            context.pre_vowel,
            context.vowel,
            post_vowel_simple,
            context.boundary,
            None,
            ending,
            function,
            prob,
            sound_change_prob_delta=consonant_change_prob,
        )

    def _emit_weak_derived_inf_participle(
        self,
        context: _WeakInfDerivationContext,
        form_parts: str,
    ) -> None:
        """
        Attach a present participle emitted from infinitive-derived weak rows.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak infinitive-derivation context.
            form_parts: Form-parts payload for the derived participle.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak participle derivation;
            this helper forwards the emitted payload unchanged.

        """
        self._add_participle_to_adjectives(
            context.word,
            context.prefix,
            form_parts,
            is_past=False,
        )

    def _generate_weak_derived_from_inf(  # noqa: PLR0913
        self,
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
    ) -> None:
        """
        Emit weak infinitive-derived branches for one principal-part context.

        Side Effects:
            Writes generated rows and stores derived participles.

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

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental branch
            sequencing; this helper preserves the legacy branch order.

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
        self._emit_weak_derived_from_inf_sequence(
            context=context,
            class2=formhash.get("class2"),
            original_ending=original_ending,
            probability=probability,
        )

    def _generate_weak_derived_from_painsg1(  # noqa: PLR0913
        self,
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
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived branches for one principal-part context.

        Side Effects:
            Writes generated rows and stores derived participles.

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

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak preterite derivation;
            this helper keeps the legacy branch order unchanged.

        """
        context = _WeakPainsg1DerivationContext(
            formhash=formhash,
            word=word,
            prefix=prefix,
            pre_vowel=pre_vowel,
            boundary=boundary,
            dental=dental,
        )
        self._emit_weak_derived_from_painsg1_context(
            context=context,
            vowel=vowel,
            post_vowel=post_vowel,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            probability=probability,
        )

    def _generate_weak_derived_from_psinsg2(  # noqa: PLR0913
        self,
        *,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        probability: str | int | None,
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived branches for one principal-part context.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            formhash: Form metadata hash for the active branch.
            prefix: Prefix segment for the active part.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment for this derivation branch.
            post_vowel: Stem segment after the active vowel.
            boundary: Stem-boundary marker used in form-parts payloads.
            probability: Base probability annotation for the branch.

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
        self._emit_weak_derived_from_psinsg2_context(
            context=context,
            probability=probability,
            post_vowel=post_vowel,
        )

    # -- entry point ---------------------------------------------------------

    def generate_verb_parts(  # noqa: PLR0913
        self,
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
    ) -> None:
        """
        Entry point: route one weak-paradigm part into principal-part generation.

        Matches Perl's ``generate_weak_verb_parts``. Called once per
        weak-paradigm word/variant/part by ``VerbFormGenerator._process_part``.

        Side Effects:
            Emits generated rows and participle side effects.

        Args:
            formhash: The form hash.
            word: The word to process.
            item: The part to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            root_vowel_actual: The root vowel actual.
            post_vowel: The post-vowel.
            variant_id: The variant ID.
            para_id_num: The paradigm ID number.
            vowel_inf: The infinitive vowel from variant 0.
            vowel_pa: The preterite singular vowel from variant 0.

        """
        self._generate_weak_verb_parts(
            formhash=formhash,
            word=word,
            item=item,
            prefix=prefix,
            pre_vowel=pre_vowel,
            root_vowel_actual=root_vowel_actual,
            post_vowel=post_vowel,
            variant_id=variant_id,
            para_id_num=para_id_num,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
        )


class VerbFormGenerator:
    """
    Generator for Old English verb forms.

    Args:
        word_pool: Categorized word pool containing loaded lexemes.
        run_state: Cross-stage scalar run state for this run.
        output_file: The output file.

    """

    #: The changes for strong verbs of type 2.
    S2_CHANGES: Final[list[tuple[str, str]]] = [
        ("dst$", "tst"),
        ("þst$", "tst"),
        ("tst$", "st"),
        ("ngst$", "ncst"),
        ("ncst$", "nst"),
        ("gst$", "hst"),
        ("hst$", "xst"),
    ]
    #: The changes for strong verbs of type 3.
    S3_CHANGES: Final[list[tuple[str, str]]] = [
        (r"[td]þ$", "tt"),
        (r"tt$", "t"),
        (r"þþ$", "þ"),
        (r"þ$", "t"),
        (r"sþ$", "st"),
        (r"ngþ$", "ncþ"),
        (r"gþ$", "hþ"),
    ]

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Initialize the verb-form generator context.

        Args:
            word_pool: Categorized word pool containing loaded lexemes.
            run_state: Cross-stage scalar run state for this run.
            output_file: Output handle receiving generated form rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Categorized word pool containing loaded lexemes.
        self.word_pool = word_pool
        #: Cross-stage scalar run state for this run.
        self.run_state = run_state
        #: The output file.
        self.output_file = output_file
        #: Optional live progress coordinator.
        self.progress = progress
        #: Collaborator handling strong-paradigm verb form generation.
        self._strong_generator = StrongVerbGenerator(word_pool, run_state, output_file)
        #: Collaborator handling weak-paradigm verb form generation.
        self._weak_generator = WeakVerbGenerator(word_pool, run_state, output_file)

    def generate(self) -> None:
        """Main entry point to generate all verb forms."""
        for word in self.word_pool.words:
            if word.verb == 1 and (word.pspart + word.papart == 0):
                if self.progress is not None:
                    self.progress.advance(
                        MorphologyStage.VERBS,
                        lemma=word.title,
                        wright=word.wright,
                        forms_written=self.run_state.output_counter,
                    )
                self._process_word(word)

    def _process_word(self, word: Word) -> None:
        """
        Process a single word's paradigms.

        Args:
            word: The word to process.

        """
        for vp in word.vb_paradigm:
            self._process_paradigm(word, vp)

    def _build_verb_formhash_base(self, word: Word, vp: VerbParadigm) -> dict[str, str]:
        """
        Build the base metadata hash used for all emitted verb forms.

        Args:
            word: Lexeme record currently being generated.
            vp: Verb paradigm record currently being generated.

        Returns:
            Base form hash copied per variant and then extended per emitted row.

        """
        return {
            "title": word.title,
            "stem": word.stem,
            "BT": f"{word.nid:06d}",
            "wordclass": "verb",
            "class1": vp.type,
            "class2": vp.class_,
            "class3": vp.subclass,
            "paradigm": vp.title,
            "paraID": vp.ID,
            "wright": word.wright,
            "comment": "",
        }

    def _derive_paradigm_seed_vowels(self, vp: VerbParadigm) -> tuple[str, str, str]:
        """
        Derive boundary and exemplar vowels from the first paradigm variant.

        Args:
            vp: Verb paradigm record currently being generated.

        Returns:
            Three-item tuple ``(boundary_inf, vowel_inf, vowel_pa)`` used by
            branch orchestration to match legacy ordering/probability behavior.

        """
        variant0 = vp.variants[0]
        inf_part = variant0.parts.get("if")
        painsg1_part = variant0.parts.get("painsg1")
        boundary_inf = nz(inf_part.boundary if inf_part else "")
        vowel_inf = nz(inf_part.vowel if inf_part else "")
        vowel_pa = nz(painsg1_part.vowel if painsg1_part else "")
        return boundary_inf, vowel_inf, vowel_pa

    def _process_paradigm(self, word: Word, vp: VerbParadigm) -> None:
        """
        Process a single paradigm and expand each variant into full traversal context.

        Side Effects:
            Invokes ``_dispatch_variant_context`` once per variant in source order.

        Args:
            word: The word to process.
            vp: The paradigm to process.

        """
        formhash_base = self._build_verb_formhash_base(word, vp)
        boundary_inf, vowel_inf, vowel_pa = self._derive_paradigm_seed_vowels(vp)
        context = _ParadigmVariantDispatchContext(word=word, paradigm=vp)
        for variant in vp.variants:
            formhash_var = formhash_base.copy()
            formhash_var["var"] = str(variant.variant_id)
            self._dispatch_variant_context(
                context,
                variant,
                formhash_var,
                boundary_inf,
                vowel_inf,
                vowel_pa,
            )

    def _dispatch_variant_context(
        self,
        context: _ParadigmVariantDispatchContext,
        variant: ParadigmVariant,
        formhash_base: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Dispatch one paradigm variant using the shared traversal flow.

        Side Effects:
            Delegates one variant traversal through ``_process_variant``.

        Args:
            context: Shared paradigm-level dispatch context.
            variant: Active variant being dispatched.
            formhash_base: Variant-scoped form hash payload.
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        self._process_variant(
            context.word,
            context.paradigm,
            variant,
            formhash_base,
            boundary_inf,
            vowel_inf,
            vowel_pa,
        )

    def _process_variant(
        self,
        word: Word,
        vp: VerbParadigm,
        variant: ParadigmVariant,
        formhash_base: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Process a single variant and expand each part into full traversal context.

        Side Effects:
            Invokes ``_dispatch_part_context`` once per part in source order.

        Args:
            word: The word to process.
            vp: The paradigm to process.
            variant: The variant to process.
            formhash_base: The base form hash.
            boundary_inf: The boundary information.

        """
        context = _VariantPartDispatchContext(
            word=word,
            paradigm=vp,
            variant=variant,
        )
        for item in variant.parts.values():
            self._dispatch_part_context(
                context,
                item,
                formhash_base,
                boundary_inf,
                vowel_inf,
                vowel_pa,
            )

    def _dispatch_part_context(
        self,
        context: _VariantPartDispatchContext,
        item: ParadigmPart,
        formhash_var: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Dispatch one variant part using the shared traversal flow.

        Side Effects:
            Delegates one part traversal through ``_process_part``.

        Args:
            context: Shared variant-level dispatch context.
            item: Active part being dispatched.
            formhash_var: Variant-scoped form hash payload.
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        self._process_part(
            context.word,
            context.paradigm,
            context.variant,
            item,
            formhash_var,
            boundary_inf,
            vowel_inf,
            vowel_pa,
        )

    def _process_part(  # noqa: PLR0913
        self,
        word: Word,
        vp: VerbParadigm,
        variant: ParadigmVariant,
        item: ParadigmPart,
        formhash_var: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Process one part and route it into strong or weak generation flow.

        Side Effects:
            Invokes the strong or weak generator exactly once.

        Args:
            word: The word to process.
            vp: The paradigm to process.
            variant: The variant to process.
            item: The part to process.
            formhash_var: The form hash.
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        prefix, pre_vowel, actual_vowel, post_vowel = self._derive_part_stem_segments(
            word,
            item,
            boundary_inf,
        )

        if vp.type == "s":
            self._strong_generator.generate_verb_parts(
                formhash_var,
                word,
                item,
                prefix,
                pre_vowel,
                actual_vowel,
                post_vowel,
                variant.variant_id,
            )
            return

        self._weak_generator.generate_verb_parts(
            formhash_var,
            word,
            item,
            prefix,
            pre_vowel,
            actual_vowel,
            post_vowel,
            variant.variant_id,
            vp.ID,
            vowel_inf,
            vowel_pa,
        )

    def _derive_part_stem_segments(
        self,
        word: Word,
        item: ParadigmPart,
        boundary_inf: str,
    ) -> tuple[str, str, str, str]:
        """
        Bind stem segments used by strong and weak part generators.

        Side Effects:
            None.

        Args:
            word: Active lexeme record.
            item: Active paradigm part.
            boundary_inf: Infinitive boundary from variant ``0``.

        Returns:
            Four-item tuple ``(prefix, pre_vowel, vowel, post_vowel)``.

        """
        prefix = self._get_prefix(word, item)
        post_vowel = self._get_post_vowel(word, item, boundary_inf)
        pre_vowel, actual_vowel = self._get_pre_vowel(word)
        return prefix, pre_vowel, actual_vowel, post_vowel

    def _get_prefix(self, word: Word, item: ParadigmPart) -> str:
        """
        Determine the prefix for a part.

        Note:
            Matches Perl implementation of get_prefix function:

            .. code-block:: perl

                if ($prefix ne $item->{prefix}) {
                    $prefix = $prefix . "-" . $item->{prefix};
                }

        Args:
            word: The word.
            item: The item.

        Returns:
            The prefix.

        """
        prefix = word.prefix
        if prefix != item.prefix:
            prefix = f"{prefix}-{item.prefix}"
        return prefix

    def _get_post_vowel(self, word: Word, item: ParadigmPart, boundary_inf: str) -> str:
        """
        Extract post-vowel from word stem.

        Note:
            Matches Perl implementation of derive_post_vowel function:

            .. code-block:: perl

                if ($item->{postVowel} ne "") {
                    $post_vowel = $item->{postVowel};
                }

            The regex pattern is:

            .. code-block:: perl

                m/$vowel_regex$vowel_regex*?($consonant_regex.*?)$boundary_inf$vowel_regex+n$/

        Args:
            word: The word.
            item: The item.
            boundary_inf: The boundary information.

        Returns:
            The post-vowel.

        """
        if not nz(item.post_vowel):
            return ""

        if boundary_inf:
            pattern = (
                f"{OENormalizer.VOWEL_REGEX.pattern}{OENormalizer.VOWEL_REGEX.pattern}*?"
                f"({OENormalizer.CONSONANT_REGEX.pattern}.*?){re.escape(boundary_inf)}"
                f"{OENormalizer.VOWEL_REGEX.pattern}+n$"
            )
        else:
            pattern = (
                f"{OENormalizer.VOWEL_REGEX.pattern}{OENormalizer.VOWEL_REGEX.pattern}*?"
                f"({OENormalizer.CONSONANT_REGEX.pattern}.*?){OENormalizer.VOWEL_REGEX.pattern}+n$"
            )
        match = re.search(pattern, word.stem)
        return match.group(1) if match else ""

    def _get_pre_vowel(self, word: Word) -> tuple[str, str]:
        """
        Extract pre-vowel and actual vowel from word stem.

        Note:
            Matches Perl implementation of derive_pre_vowel function:

            .. code-block:: perl

                $stem =~ m/^($vowel_regex*?.*?)($vowel_regex$vowel_regex?)/;


        Args:
            word: The word.

        Returns:
            The pre-vowel and actual vowel.

        """
        pattern = (
            f"^({OENormalizer.VOWEL_REGEX.pattern}*?.*?)"
            f"({OENormalizer.VOWEL_REGEX.pattern}{{1,2}})"
        )
        match = re.search(pattern, word.stem)
        if match:
            return match.group(1), match.group(2)
        return "", ""

    def _add_participle_to_adjectives(
        self, word: Word, prefix: str, form_parts: str, is_past: bool
    ) -> None:
        r"""
        Add a participle to adjectives.

        Notes:
            Matches Perl implementation of ``add_participle_to_adjectives`` function:

            .. code-block:: perl
                $stem = $1 if $form_parts =~ m/$prefix(.*)$/;
                $stem =~ s/[0\-\n]//g;

        Args:
            word: The word.
            prefix: The prefix.
            form_parts: The form parts.
            is_past: Whether the form is past.

        Returns:
            The stem.

        """
        _add_participle_to_adjectives_session(
            self.word_pool,
            word=word,
            prefix=prefix,
            form_parts=form_parts,
            is_past=is_past,
        )
