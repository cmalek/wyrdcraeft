"""Strong-verb ablaut generation engine."""

from __future__ import annotations

from collections.abc import Sequence

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    Word,
    _StrongInfDerivationContext,
    _StrongPrincipalPartContext,
)
from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_rows import emit_form_for_context as _emit_form_for_context_row
from .form_rows import emit_imsg_for_context as _emit_imsg_for_context_row
from .form_rows import (
    emit_sound_changed_form_for_context as _emit_sound_changed_form_for_context_row,
)
from .participles import (
    add_participle_to_adjectives as _add_participle_to_adjectives_session,
)
from .probability import probability_plus
from .shared import FormOutput


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
