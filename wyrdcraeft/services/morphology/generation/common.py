# ruff: noqa: I001,PLR0913,ARG002,D417,RUF100,PLC0415
import re
from collections.abc import Callable, Sequence
from functools import partial
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
from .probability import probability_plus
from .scalar_utils import nz as _nz_scalar
from .scalar_utils import perl_numify as _perl_numify
from .shared import FormOutput
from . import weak_derivation_flow as _weak_derivation_flow
from . import weak_principal_flow as _weak_principal_flow


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

    def _emit_inf_derivation_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        active_vowel: str,
        prob: str | int | None,
    ) -> None:
        """
        Route one strong principal-part branch into infinitive-derived generation.

        Side Effects:
            Writes generated rows and participle side effects via callback.

        Note:
            Currently unreachable from the live traversal (the production path
            reaches ``_generate_derived_from_inf`` directly through
            ``_emit_principal_inf_derivation_context``); kept for parity with
            the pre-migration call surface. Flagged for Task 9 review.

        Args:
            formhash: The mutable form metadata hash.
            word: Active lexeme record.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            active_vowel: Active ablaut/umlaut vowel.
            prob: Optional probability annotation.

        """
        self._generate_derived_from_inf(
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

    def _generate_derived_from_inf(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        prob: str | int | None,
    ) -> None:
        """
        Generate strong verb forms derived from the infinitive principal part.

        Side Effects:
            Writes generated rows and participle side effects via callbacks.

        Note:
            Wright (``Old English Grammar``, §§474-475) describes strong verbs
            as deriving preterite and participle stems by vowel alternation
            (ablaut) across a fixed stem set. This routine emits those
            infinitive-derived rows in that legacy order. Tichý (2017, p. 43)
            keeps the same traditional strong/weak split for transparent
            morphological analysis.

        Args:
            formhash: The form hash.
            word: The word to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            ending: The ending.
            prob: The probability.

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
        self._emit_derived_from_inf_sequence(
            ending=ending,
            vowel=vowel,
            probability=prob,
            umlaut_vowels=OENormalizer.iumlaut([vowel]),
            emit_form_for_vowel=partial(
                self._emit_derived_inf_form_for_vowel_context, context
            ),
            emit_sound_for_vowel=partial(
                self._emit_derived_inf_sound_for_vowel_context, context
            ),
            on_participle=partial(self._emit_derived_inf_participle_context, context),
            emit_imsg=partial(self._emit_derived_inf_imsg_context, context),
        )

    def _emit_derived_from_inf_sequence(  # noqa: PLR0913
        self,
        *,
        ending: str,
        vowel: str,
        probability: str | int | None,
        umlaut_vowels: Sequence[str],
        emit_form_for_vowel: Callable[
            [str, str, str, str | int | None], tuple[str, str]
        ],
        emit_sound_for_vowel: Callable[[str, str, str, str | int | None], None],
        on_participle: Callable[[str], None],
        emit_imsg: Callable[[str | int | None], None],
    ) -> None:
        """
        Emit the full strong-verb infinitive-derived sequence.

        Side Effects:
            Invokes emission callbacks for non-umlaut, imperative, and umlaut forms.

        Args:
            ending: Original paradigm ending from the infinitive principal part.
            vowel: Base infinitive vowel.
            probability: Base probability scalar for the branch.
            umlaut_vowels: Ordered umlaut vowel variants for the base vowel.
            emit_form_for_vowel: Callback that emits a form for one active vowel.
            emit_sound_for_vowel: Callback that emits sound-change rows for one vowel.
            on_participle: Callback that consumes the emitted participle form-parts.
            emit_imsg: Callback that emits the ``ImSg`` derived row.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        probability_plus_one = probability_plus(probability, delta=1, empty_default=1)
        form_parts = self._emit_derived_from_inf_non_umlaut(
            ending=ending,
            probability=probability,
            probability_plus_one=probability_plus_one,
            emit_form=lambda ending_value, function, prob_value: emit_form_for_vowel(
                vowel,
                ending_value,
                function,
                prob_value,
            ),
        )
        on_participle(form_parts)
        emit_imsg(probability)

        for mv_idx, mvowel in enumerate(umlaut_vowels):
            mv_prob = int(probability) + mv_idx if probability is not None else mv_idx

            def emit_umlaut(
                ending_value: str,
                function: str,
                prob_value: str | int | None,
                *,
                _mvowel: str = mvowel,
            ) -> tuple[str, str]:
                return emit_form_for_vowel(
                    _mvowel,
                    ending_value,
                    function,
                    prob_value,
                )

            def emit_umlaut_sound(
                ending_value: str,
                function: str,
                prob_value: str | int | None,
                *,
                _mvowel: str = mvowel,
            ) -> None:
                emit_sound_for_vowel(
                    _mvowel,
                    ending_value,
                    function,
                    prob_value,
                )

            self._emit_umlaut_for_vowel(
                probability=mv_prob,
                emit_form=emit_umlaut,
                emit_sound=emit_umlaut_sound,
            )

    def _emit_derived_from_inf_non_umlaut(
        self,
        *,
        ending: str,
        probability: str | int | None,
        probability_plus_one: int,
        emit_form: Callable[[str, str, str | int | None], tuple[str, str]],
    ) -> str:
        """
        Emit non-umlaut strong-verb forms derived from the infinitive principal part.

        Side Effects:
            Writes generated rows through ``emit_form``.

        Args:
            ending: Original paradigm ending from the infinitive part.
            probability: Base probability scalar.
            probability_plus_one: Incremented probability scalar.
            emit_form: Callback that emits one generated form.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Returns:
            Final participle ``formParts`` string used for adjective derivation.

        """
        if "an" in ending:
            emit_form("anne", "IdIf", probability)
            emit_form("enne", "IdIf", probability)
            _, participle_form_parts = emit_form("ende", "PsPt", probability)

            emit_form("e", "PsInSg1", probability)
            emit_form("u", "PsInSg1", probability_plus_one)
            emit_form("o", "PsInSg1", probability_plus_one)
            emit_form("æ", "PsInSg1", probability_plus_one)

            emit_form("aþ", "PsInPl", probability)
            emit_form("eþ", "PsInPl", probability_plus_one)
            emit_form("es", "PsInPl", probability_plus_one)
            emit_form("as", "PsInPl", probability_plus_one)

            emit_form("e", "PsSuSg", probability)
            emit_form("en", "PsSuPl", probability)
            emit_form("aþ", "ImPl", probability)
            return participle_form_parts

        emit_form("nne", "IdIf", probability)
        _, participle_form_parts = emit_form("nde", "PsPt", probability)

        emit_form("0", "PsInSg1", probability)
        emit_form("þ", "PsInPl", probability)
        emit_form("0", "PsSuSg", probability)
        emit_form("n", "PsSuPl", probability)
        emit_form("þ", "ImPl", probability)
        return participle_form_parts

    def _emit_umlaut_for_vowel(
        self,
        *,
        probability: int,
        emit_form: Callable[[str, str, str | int | None], tuple[str, str]],
        emit_sound: Callable[[str, str, str | int | None], None],
    ) -> None:
        """
        Emit umlaut-derived ``PsInSg2`` and ``PsInSg3`` strong-verb forms.

        Side Effects:
            Writes generated rows through ``emit_form`` and ``emit_sound``.

        Args:
            probability: Base umlaut probability for this vowel variant.
            emit_form: Callback that emits one generated form.
            emit_sound: Callback that emits one sound-change branch.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        emit_form("stu", "PsInSg2", probability + 1)
        emit_form("est", "PsInSg2", probability + 1)
        emit_form("ist", "PsInSg2", probability + 1)
        emit_form("s", "PsInSg2", probability + 1)
        emit_sound("st", "PsInSg2", probability)

        emit_form("eþ", "PsInSg3", probability + 1)
        emit_form("iþ", "PsInSg3", probability + 1)
        emit_sound("þ", "PsInSg3", probability)

    def _dispatch_verb_part_branches(
        self,
        *,
        para_id: str,
        on_papt: Callable[[], None],
        on_inf: Callable[[], None],
        on_painsg1: Callable[[], None],
        on_painpl: Callable[[], None],
    ) -> bool:
        """
        Dispatch strong-verb principal-part branch actions for one ``para_id``.

        Side Effects:
            Invokes at least one branch callback when a branch matches.

        Args:
            para_id: Principal function identifier from paradigm row.
            on_papt: Callback for past-participle branch side effects.
            on_inf: Callback for infinitive-derived branch.
            on_painsg1: Callback for ``PaInSg1``-derived branch.
            on_painpl: Callback for ``PaInPl``-derived branch.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Returns:
            ``True`` when any branch callback was invoked, else ``False``.

        """
        invoked = False
        para_id_lower = para_id.lower()

        if para_id_lower == "papt":
            on_papt()
            invoked = True

        if para_id_lower == "if":
            on_inf()
            return True
        if para_id_lower == "painsg1":
            on_painsg1()
            return True
        if para_id_lower == "painpl":
            on_painpl()
            return True
        return invoked

    def _dispatch_derived_from_principal_part(  # noqa: PLR0913
        self,
        *,
        para_id: str,
        form_parts: str,
        active_vowel: str,
        probability: str | int | None,
        on_papt_form_parts: Callable[[str], None],
        on_inf: Callable[[str, str | int | None], None],
        emit_form_for_vowel: Callable[
            [str, str, str, str | int | None], tuple[str, str]
        ],
    ) -> bool:
        """
        Dispatch and emit strong derived branches for one principal-part emission.

        Side Effects:
            Invokes branch emitters and participle sinks according to ``para_id``.

        Args:
            para_id: Principal function identifier from the paradigm row.
            form_parts: Emitted principal-form ``formParts`` string.
            active_vowel: Active vowel for the current branch context.
            probability: Probability scalar for derived branch emissions.
            on_papt_form_parts: Sink for ``PaPt`` participle projection.
            on_inf: Callback that emits infinitive-derived branches.
            emit_form_for_vowel: Callback for one strong form on ``active_vowel``.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Returns:
            ``True`` when any branch callback was invoked, else ``False``.

        """

        def on_papt() -> None:
            on_papt_form_parts(form_parts)

        def on_inf_branch() -> None:
            on_inf(active_vowel, probability)

        def on_painsg1_branch() -> None:
            def emit_form(
                ending_value: str,
                function: str,
                prob_value: str | int | None,
            ) -> tuple[str, str]:
                return emit_form_for_vowel(
                    active_vowel,
                    ending_value,
                    function,
                    prob_value,
                )

            self._emit_painsg1_derived(
                probability=probability,
                emit_form=emit_form,
            )

        def on_painpl_branch() -> None:
            def emit_form(
                ending_value: str,
                function: str,
                prob_value: str | int | None,
            ) -> tuple[str, str]:
                return emit_form_for_vowel(
                    active_vowel,
                    ending_value,
                    function,
                    prob_value,
                )

            self._emit_painpl_derived(
                probability=probability,
                emit_form=emit_form,
            )

        return self._dispatch_verb_part_branches(
            para_id=para_id,
            on_papt=on_papt,
            on_inf=on_inf_branch,
            on_painsg1=on_painsg1_branch,
            on_painpl=on_painpl_branch,
        )

    def _emit_principal_part_sequence(  # noqa: PLR0913
        self,
        *,
        para_id: str,
        ending: str,
        vowels: Sequence[str],
        emit_form_for_vowel: Callable[
            [str, str, str, str | int | None], tuple[str, str]
        ],
        on_papt_form_parts: Callable[[str], None],
        on_inf: Callable[[str, str | int | None], None],
    ) -> None:
        """
        Emit one strong principal-part sequence and dispatch derived branches.

        Note:
            Wright's strong-verb chapter groups verbs by vowel alternation classes,
            and Tichý's generation description likewise replaces the root vowel by
            paradigm-specific ablaut/umlaut options. This helper keeps that
            vowel-first branching order unchanged for parity.

        Side Effects:
            Emits forms and invokes derived-branch callbacks for each active vowel.

        Args:
            para_id: Principal function identifier from the paradigm row.
            ending: Morphological ending from the active principal part.
            vowels: Ordered vowel variants to emit for the principal part.
            emit_form_for_vowel: Callback emitting one form for one active vowel.
            on_papt_form_parts: Callback receiving ``PaPt`` participle form-parts.
            on_inf: Callback emitting infinitive-derived branches.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        for vcount, active_vowel in enumerate(vowels):
            prob: str | int | None = 1 if vcount == 1 else None
            _, form_parts = emit_form_for_vowel(active_vowel, ending, para_id, prob)
            self._dispatch_derived_from_principal_part(
                para_id=para_id,
                form_parts=form_parts,
                active_vowel=active_vowel,
                probability=prob,
                on_papt_form_parts=on_papt_form_parts,
                on_inf=on_inf,
                emit_form_for_vowel=emit_form_for_vowel,
            )

    def _emit_painsg1_derived(
        self,
        *,
        probability: str | int | None,
        emit_form: Callable[[str, str, str | int | None], tuple[str, str]],
    ) -> None:
        """
        Emit ``PaInSg1``-derived strong-verb side branch forms.

        Side Effects:
            Writes generated rows through ``emit_form``.

        Args:
            probability: Base probability scalar for branch emissions.
            emit_form: Callback that emits one generated form.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        emit_form("0", "PaInSg3", probability)

    def _emit_painpl_derived(
        self,
        *,
        probability: str | int | None,
        emit_form: Callable[[str, str, str | int | None], tuple[str, str]],
    ) -> None:
        """
        Emit ``PaInPl``-derived strong-verb side branch forms.

        Side Effects:
            Writes generated rows through ``emit_form``.

        Args:
            probability: Base probability scalar for branch emissions.
            emit_form: Callback that emits one generated form.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        """
        emit_form("e", "PaInSg2", probability)
        emit_form("e", "PaSuSg", probability)
        emit_form("en", "PaSuPl", probability)

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

    def _emit_principal_inf_derivation(
        self,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit strong infinitive-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Note:
            Currently unreachable: no caller passes this method as the ``on_inf``
            branch action (the live path uses
            ``_emit_principal_inf_derivation_context`` instead). Kept for parity
            with the pre-migration call surface. Flagged for Task 9 review.

        Args:
            context: Shared strong principal-part context.
            active_vowel: Active stem vowel for this derivation branch.
            prob: Optional probability annotation.

        """
        self._emit_inf_derivation_context(
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
            ending=context.ending,
            vowel=active_vowel,
            probability=prob,
            umlaut_vowels=OENormalizer.iumlaut([active_vowel]),
            emit_form_for_vowel=partial(
                self._emit_derived_inf_form_for_vowel_context, inf_context
            ),
            emit_sound_for_vowel=partial(
                self._emit_derived_inf_sound_for_vowel_context, inf_context
            ),
            on_participle=partial(
                self._emit_derived_inf_participle_context, inf_context
            ),
            emit_imsg=partial(self._emit_derived_inf_imsg_context, inf_context),
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
            para_id=para_id,
            ending=ending,
            vowels=[item.vowel],
            emit_form_for_vowel=partial(
                self._emit_principal_form_for_vowel_context, context
            ),
            on_papt_form_parts=partial(
                self._emit_principal_participle_context, context
            ),
            on_inf=partial(self._emit_principal_inf_derivation_context, context),
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

        self._generate_weak_verb_parts(
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
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            dental: Dental segment for weak forms.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_principal_form_context(
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
            emit_form_for_context=self._emit_form_for_context,
        )

    def _emit_weak_inf_form_context(  # noqa: PLR0913
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
        Emit one weak infinitive-derived row for a pre-bound stem context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            dental: Dental segment for weak forms.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_inf_form(
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
            emit_weak_principal_form=self._emit_weak_principal_form_context,
        )

    def _emit_weak_painsg1_form_for_vowel_context(  # noqa: PLR0913
        self,
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
    ) -> tuple[str, str]:
        """
        Emit one ``PaInSg1`` weak form row for a selected vowel variant.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            boundary: Boundary consonant segment.
            dental: Weak dental suffix segment.
            current_vowel: Active vowel for this variant.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_painsg1_form_for_vowel(
            formhash,
            prefix,
            pre_vowel,
            boundary,
            dental,
            current_vowel,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form=self._generate_and_print_form,
        )

    def _emit_weak_painsg1_form_for_vowel_derivation_context(
        self,
        context: _WeakPainsg1DerivationContext,
        current_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> tuple[str, str]:
        """
        Emit one ``PaInSg1`` form row from a pre-bound weak derivation context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            current_vowel: Active vowel for this variant.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_painsg1_form_for_vowel_from_context(
            context,
            current_vowel,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_for_vowel=self._emit_weak_painsg1_form_for_vowel_context,
        )

    def _emit_weak_painsg1_manual_context(
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

        """
        _weak_derivation_flow.emit_weak_painsg1_manual_context(
            context,
            form,
            form_parts,
            function,
            prob,
            emit_manual=self._generate_and_print_manual,
        )

    def _emit_weak_painsg1_participle_context(
        self, context: _WeakPainsg1DerivationContext, form_parts: str
    ) -> None:
        """
        Attach a past participle emitted from a weak ``PaInSg1`` branch.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_derivation_flow.emit_weak_painsg1_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_psinsg2_form_with_post_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        boundary: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
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

        """
        _weak_derivation_flow.emit_weak_psinsg2_form_with_post_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            boundary,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_with_post=self._generate_and_print_form,
        )

    def _emit_weak_psinsg2_sound_with_post_context(  # noqa: PLR0913
        self,
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

        """
        _weak_derivation_flow.emit_weak_psinsg2_sound_with_post_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            boundary,
            ending,
            function,
            prob,
            consonant_change_prob,
            post_vowel_simple,
            emit_sound_with_post=self._generate_and_print_form_with_sound_changes,
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

        """
        _weak_derivation_flow.emit_weak_psinsg2_form_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_with_post_context=self._emit_weak_psinsg2_form_with_post_context,
        )

    def _emit_weak_psinsg2_sound_with_post_derivation_context(
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

        """
        _weak_derivation_flow.emit_weak_psinsg2_sound_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            consonant_change_prob,
            post_vowel_simple,
            emit_sound_with_post_context=self._emit_weak_psinsg2_sound_with_post_context,
        )

    def _generate_and_print_form_with_sound_changes(  # noqa: PLR0912, PLR0913
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
        Matches Perl's generate_and_print_form_with_sound_changes.

        Notes:
            Matches Perl implementation of ``generate_and_print_form_with_sound_changes``
            function:

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
            prob: The probability.
            sound_change_prob_delta: Probability increment for derived rows.

        """  # noqa: E501
        _generate_and_print_form_with_sound_changes_row(
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
            prob,
            sound_change_prob_delta=sound_change_prob_delta,
        )

    def _generate_and_print_manual(
        self,
        formhash: dict[str, str],
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        """
        Matches Perl's generate_and_print_manual.

        Args:
            formhash: The form hash.
            form: The generated form text.
            form_parts: The generated form-parts payload.
            function: The morphology function code.
            prob: The probability annotation.

        """
        _generate_and_print_manual(
            self.run_state,
            self.output_file,
            formhash,
            form,
            form_parts,
            function,
            prob,
        )

    def _emit_weak_principal_pspt_participle_context(
        self, context: _WeakPrincipalPartContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from a weak principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_principal_flow.emit_weak_principal_pspt_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_principal_papt_participle_context(
        self, context: _WeakPrincipalPartContext, form_parts: str
    ) -> None:
        """
        Attach a past participle emitted from a weak principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_principal_flow.emit_weak_principal_papt_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_principal_inf_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak infinitive-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        """
        _weak_principal_flow.emit_weak_principal_inf_derivation_with_emitters(
            context,
            emit_form_for_context=self._emit_form_for_context,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_principal_psinsg2_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared weak principal-part context.

        """
        _weak_principal_flow.emit_weak_principal_psinsg2_derivation_with_emitters(
            context,
            emit_form=self._generate_and_print_form,
            emit_sound=self._generate_and_print_form_with_sound_changes,
        )

    def _emit_weak_principal_painsg1_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        """
        _weak_principal_flow.emit_weak_principal_painsg1_derivation_with_emitters(
            context,
            emit_form=self._generate_and_print_form,
            emit_manual=self._generate_and_print_manual,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_weak_verb_parts(  # noqa: PLR0913
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
        Matches Perl's generate_weak_verb_parts.

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
        _weak_principal_flow.generate_weak_verb_parts_with_emitters(
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
            emit_form_for_context=self._emit_form_for_context,
            emit_painsg1_form=self._generate_and_print_form,
            emit_painsg1_manual=self._generate_and_print_manual,
            emit_psinsg2_form=self._generate_and_print_form,
            emit_psinsg2_sound=self._generate_and_print_form_with_sound_changes,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_weak_derived_from_inf(  # noqa: PLR0912, PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        original_ending: str,
        prob: str | int | None,
    ) -> None:
        """
        Generate weak verbs derived from inf.

        Notes:
            Matches Perl implementation of ``generate_weak_derived_from_inf``
            function.

        Note:
            Wright (``Old English Grammar``, §§474 and 520) describes weak
            verbs as forming preterites and participles with dental suffixes.
            This helper keeps that weak-class dental sequencing in the same
            deterministic order used by the legacy generator and by Tichý's
            class-based analyzer design (2017, p. 43).

        Args:
            formhash: The form hash.
            word: The word to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            original_ending: The original ending.
            prob: The probability.

        """
        _weak_derivation_flow.generate_weak_derived_from_inf(
            formhash=formhash,
            word=word,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            original_ending=original_ending,
            probability=prob,
            emit_form_for_context=self._emit_form_for_context,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_derived_inf_form_context(
        self,
        context: _WeakInfDerivationContext,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        """
        Emit one weak infinitive-derived row for a selected dental/ending pair.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak-derivation emission context.
            dental: Optional weak-dental segment for the emitted row.
            ending: Ending segment for the emitted row.
            function: Morphology function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_derived_inf_form(
            context,
            dental,
            ending,
            function,
            prob,
            emit_weak_inf_form=self._emit_weak_inf_form_context,
        )

    def _emit_weak_derived_inf_participle_context(
        self, context: _WeakInfDerivationContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from infinitive-derived weak rows.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak-derivation emission context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_derivation_flow.emit_weak_derived_inf_participle(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_weak_derived_from_painsg1(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str,
        prob: str | int | None,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Generate weak verbs derived from painsg1.

        Args:
            formhash: The form hash.
            word: The word to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            dental: The dental.
            prob: The probability.
            vowel_inf: The infinitive vowel from variant 0.
            vowel_pa: The preterite singular vowel from variant 0.

        """
        _weak_derivation_flow.generate_weak_derived_from_painsg1(
            formhash=formhash,
            word=word,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            dental=dental,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            probability=prob,
            emit_form=self._generate_and_print_form,
            emit_manual=self._generate_and_print_manual,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_weak_derived_from_psinsg2(  # noqa: PLR0913
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
        Matches Perl's generate_weak_derived_from_psinsg2.

        Args:
            formhash: The form hash.
            prefix: The prefix segment.
            pre_vowel: The pre-vowel segment.
            vowel: The active vowel segment.
            post_vowel: The post-vowel segment.
            boundary: The boundary segment.
            prob: The probability annotation.

        """
        _weak_derivation_flow.generate_weak_derived_from_psinsg2(
            formhash=formhash,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            probability=prob,
            emit_form=self._generate_and_print_form,
            emit_sound=self._generate_and_print_form_with_sound_changes,
        )


def generate_vbforms(
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Wrapper for VerbFormGenerator.

    Args:
        word_pool: Categorized word pool containing loaded lexemes.
        run_state: Cross-stage scalar run state for this run.
        output_file: The output file.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    from .verb_engine import VerbFormOrchestrator

    orchestrator = VerbFormOrchestrator(
        word_pool, run_state, output_file, progress=progress
    )
    orchestrator.generate()
