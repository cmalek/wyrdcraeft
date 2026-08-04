# ruff: noqa: I001,PLR0913,ARG002,D417,RUF100,PLC0415
import re
from collections.abc import Callable, Sequence
from functools import partial
from typing import Final, Protocol

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
#: Callback signature for one weak manual-form emission operation, as used by
#: the ``PaInSg1``-variant branch (no ``formhash`` slot).
WeakInflectionManualEmitter = Callable[[str, str, str, str | int | None], None]
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
#: Callback signature for one manual weak row emission (with ``formhash``).
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
#: Callback signature for one context-aware principal weak-form emission.
WeakPrincipalFormContextEmitter = Callable[
    [dict[str, str], str, str, str, str, str, str | None, str, str, str | int | None],
    tuple[str, str],
]
#: Callback signature for one context-aware weak derivation action.
WeakPrincipalContextAction = Callable[[_WeakPrincipalPartContext], None]
#: Callback signature for one context-aware weak participle action.
WeakPrincipalParticipleAction = Callable[[_WeakPrincipalPartContext, str], None]
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
class WeakParticipleAdder(Protocol):
    """
    Protocol for adding one participle to adjective storage.

    Note:
        This protocol was defined identically in both former
        ``weak_principal_flow.py`` and ``weak_derivation_flow.py``; merging
        both modules into ``generation.common`` collapses that pre-existing
        duplicate definition into one (Python does not allow two classes of
        the same name in one module namespace), not a design simplification.

    """

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
            while every callback consumer here passes it positionally; this
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

    def _emit_weak_derived_from_inf_class2_variant(
        self,
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

    def _emit_weak_derived_from_inf_by_class2(  # noqa: PLR0913
        self,
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
            fp = self._emit_weak_derived_from_inf_general(
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
                fp = self._emit_weak_derived_from_inf_class2_variant(
                    iending=iending,
                    perl_inf_vowel_end=perl_inf_vowel_end,
                    regex_vowel_end=regex_vowel_end,
                    emit_form=emit_form,
                )
                on_participle(fp)

    def _emit_weak_derived_from_inf_sequence(  # noqa: PLR0913
        self,
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

        self._emit_weak_derived_from_inf_by_class2(
            class2=class2,
            original_ending=original_ending,
            probability=effective_probability,
            probability_plus_one=probability_plus_one,
            perl_inf_vowel_end=self._has_perl_inf_vowel_ending(fp_base),
            regex_vowel_end=self._has_regex_vowel_ending(fp_base),
            emit_form=emit_form,
            on_participle=on_participle,
        )

    def _emit_weak_derived_from_psinsg2(
        self,
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

    def _emit_weak_derived_from_psinsg2_context(
        self,
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

        self._emit_weak_derived_from_psinsg2(
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

    def _emit_weak_derived_from_painsg1_variant(  # noqa: PLR0913
        self,
        *,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel_simple: str,
        boundary: str,
        dental: str,
        probability: int,
        emit_form: WeakSimpleFormEmitter,
        emit_manual: WeakInflectionManualEmitter,
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

        form_parts = (
            f"{prefix}-{pre_vowel}-{vowel}-{post_vowel_simple}-{boundary}-{dental}"
        )
        form = form_parts.replace("0", "").replace("-", "")
        emit_manual(form, form_parts, "PaPt", probability)

        for sound_changed_form in derive_papt_sound_changed_forms(form):
            emit_manual(sound_changed_form, form_parts, "PaPt", probability + 1)

        return form_parts

    def _emit_weak_derived_from_painsg1_sequence(  # noqa: PLR0913
        self,
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

    def _emit_weak_derived_from_painsg1_context(  # noqa: PLR0913
        self,
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
        emit_manual: WeakInflectionManualEmitter,
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

            return self._emit_weak_derived_from_painsg1_variant(
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

        self._emit_weak_derived_from_painsg1_sequence(
            vowel=vowel,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            probability=probability,
            emit_variant=emit_variant,
            on_participle=on_participle,
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
        prefix: str,
        default_parts: WeakStemParts,
        item_parts: WeakStemParts,
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

    def _emit_weak_principal_part_sequence(  # noqa: PLR0913
        self,
        *,
        para_id: str,
        para_id_num: str,
        paradigm_type: str,
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
            paradigm_type: ``VerbParadigm.type`` label for item-shape routing.
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
        use_item_shape = self._should_use_weak_item_shape(
            para_id_num,
            paradigm_type=paradigm_type,
        )
        form_parts = self._emit_weak_principal_form(
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
        self._dispatch_weak_principal_part_derivations(
            para_id=para_id,
            use_item_shape=use_item_shape,
            form_parts=form_parts,
            on_pspt_participle=on_pspt_participle,
            on_papt_participle=on_papt_participle,
            on_inf=on_inf,
            on_psinsg2=on_psinsg2,
            on_painsg1=on_painsg1,
        )

    def _dispatch_weak_derived_forms(
        self,
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

    def _dispatch_weak_principal_part_derivations(  # noqa: PLR0913
        self,
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

        return self._dispatch_weak_derived_forms(
            para_id=para_id,
            use_item_shape=use_item_shape,
            on_inf=on_inf,
            on_psinsg2=on_psinsg2,
            on_painsg1=on_painsg1,
        )

    # -- weak principal-part orchestration (former weak_principal_flow.py) --

    def _emit_weak_principal_pspt_participle(
        self,
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

    def _emit_weak_principal_papt_participle(
        self,
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

    def _emit_weak_principal_inf_derivation(
        self,
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

    def _emit_weak_principal_psinsg2_derivation(
        self,
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

    def _emit_weak_principal_painsg1_derivation(
        self,
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

    def _emit_weak_principal_inf_derivation_with_emitters(
        self,
        context: _WeakPrincipalPartContext,
        *,
        emit_form_for_context: WeakFormContextEmitter,
        add_participle_to_adjectives: WeakParticipleAdder,
    ) -> None:
        """
        Emit weak infinitive-derived rows from principal context via low-level emitters.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        Keyword Args:
            emit_form_for_context: Low-level row emitter for direct form output.
            add_participle_to_adjectives: Callback that stores derived participles.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental derivation from
            principal parts; this helper preserves that branch order while moving
            emitter binding out of ``generation.common``.

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
            emit_form_for_context=emit_form_for_context,
            add_participle_to_adjectives=add_participle_to_adjectives,
        )

    def _emit_weak_principal_psinsg2_derivation_with_emitters(
        self,
        context: _WeakPrincipalPartContext,
        *,
        emit_form: WeakPsinsg2FormWithPostEmitter,
        emit_sound: WeakPsinsg2SoundWithPostEmitter,
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived rows from principal context via low-level
        emitters.

        Side Effects:
            Writes generated and sound-changed rows to the morphology output stream.

        Args:
            context: Shared weak principal-part context.

        Keyword Args:
            emit_form: Low-level direct form emitter.
            emit_sound: Low-level sound-change emitter.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak branch alternations for
            present singular forms; this helper preserves that routing while
            centralizing emitter binding in the principal-flow module.

        """
        self._generate_weak_derived_from_psinsg2(
            formhash=context.formhash,
            prefix=context.prefix,
            pre_vowel=context.pre_vowel,
            vowel=context.vowel,
            post_vowel=context.post_vowel,
            boundary=context.boundary,
            probability=context.probability,
            emit_form=emit_form,
            emit_sound=emit_sound,
        )

    def _emit_weak_principal_painsg1_derivation_with_emitters(
        self,
        context: _WeakPrincipalPartContext,
        *,
        emit_form: WeakPainsg1RawFormEmitter,
        emit_manual: WeakManualEmitter,
        add_participle_to_adjectives: WeakParticipleAdder,
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived rows from principal context via low-level
        emitters.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        Keyword Args:
            emit_form: Low-level direct form emitter.
            emit_manual: Low-level manual row emitter.
            add_participle_to_adjectives: Callback that stores derived participles.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental-preterite
            derivation; this helper keeps callback order intact while removing
            compatibility-layer adapter assembly from ``generation.common``.

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
            emit_form=emit_form,
            emit_manual=emit_manual,
            add_participle_to_adjectives=add_participle_to_adjectives,
        )

    def _emit_weak_principal_pspt_participle_context(
        self, context: _WeakPrincipalPartContext, form_parts: str,
        *,
        add_participle_to_adjectives: WeakParticipleAdder,
    ) -> None:
        """
        Emit one weak ``PsPt`` participle side effect from context-bound inputs.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        Keyword Args:
            add_participle_to_adjectives: Callback that stores the participle row.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak-participle projection;
            this wrapper keeps callback routing unchanged.

        """
        self._emit_weak_principal_pspt_participle(
            context,
            form_parts,
            add_participle_to_adjectives=add_participle_to_adjectives,
        )

    def _emit_weak_principal_papt_participle_context(
        self, context: _WeakPrincipalPartContext, form_parts: str,
        *,
        add_participle_to_adjectives: WeakParticipleAdder,
    ) -> None:
        """
        Emit one weak ``PaPt`` participle side effect from context-bound inputs.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        Keyword Args:
            add_participle_to_adjectives: Callback that stores the participle row.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak-participle projection;
            this wrapper keeps callback routing unchanged.

        """
        self._emit_weak_principal_papt_participle(
            context,
            form_parts,
            add_participle_to_adjectives=add_participle_to_adjectives,
        )

    def _emit_weak_principal_inf_derivation_context(
        self,
        context: _WeakPrincipalPartContext,
        *,
        generate_weak_derived_from_inf: WeakInfBranchGenerator,
    ) -> None:
        """
        Emit weak infinitive-derived rows from one context-bound principal part.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        Keyword Args:
            generate_weak_derived_from_inf: Callback for infinitive-derived flow.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak branch derivation;
            this wrapper preserves legacy callback sequencing.

        """
        self._emit_weak_principal_inf_derivation(
            context,
            generate_weak_derived_from_inf=generate_weak_derived_from_inf,
        )

    def _emit_weak_principal_psinsg2_derivation_context(
        self,
        context: _WeakPrincipalPartContext,
        *,
        generate_weak_derived_from_psinsg2: WeakPsinsg2BranchGenerator,
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived rows from one context-bound principal part.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared weak principal-part context.

        Keyword Args:
            generate_weak_derived_from_psinsg2: Callback for ``PsInSg2`` flow.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak branch sequencing; this
            wrapper preserves the same deterministic routing.

        """
        self._emit_weak_principal_psinsg2_derivation(
            context,
            generate_weak_derived_from_psinsg2=generate_weak_derived_from_psinsg2,
        )

    def _emit_weak_principal_painsg1_derivation_context(
        self,
        context: _WeakPrincipalPartContext,
        *,
        generate_weak_derived_from_painsg1: WeakPainsg1BranchGenerator,
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived rows from one context-bound principal part.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        Keyword Args:
            generate_weak_derived_from_painsg1: Callback for ``PaInSg1`` flow.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak dental-preterite branch
            derivation; this wrapper preserves legacy callback sequencing.

        """
        self._emit_weak_principal_painsg1_derivation(
            context,
            generate_weak_derived_from_painsg1=generate_weak_derived_from_painsg1,
        )

    def _generate_weak_verb_parts_with_context(  # noqa: PLR0913
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
        emit_form_for_context: WeakFormContextEmitter,
        add_participle_to_adjectives: WeakParticipleAdder,
        generate_weak_derived_from_inf: WeakInfBranchGenerator,
        generate_weak_derived_from_psinsg2: WeakPsinsg2BranchGenerator,
        generate_weak_derived_from_painsg1: WeakPainsg1BranchGenerator,
    ) -> None:
        """
        Generate weak principal-part rows with context-bound callback routing.

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
            emit_form_for_context: Callback that emits one principal weak form with
                a bound formhash.
            add_participle_to_adjectives: Callback that stores derived participles.
            generate_weak_derived_from_inf: Callback for infinitive-derived flow.
            generate_weak_derived_from_psinsg2: Callback for ``PsInSg2`` flow.
            generate_weak_derived_from_painsg1: Callback for ``PaInSg1`` flow.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichy
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak principal-part
            sequencing; this helper preserves callback order and probability flow.

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
            emit_form=partial(
                self._emit_weak_principal_form_context,
                formhash,
                emit_form_for_context=emit_form_for_context,
            ),
            on_pspt_participle=partial(
                self._emit_weak_principal_pspt_participle_context,
                add_participle_to_adjectives=add_participle_to_adjectives,
            ),
            on_papt_participle=partial(
                self._emit_weak_principal_papt_participle_context,
                add_participle_to_adjectives=add_participle_to_adjectives,
            ),
            on_inf=partial(
                self._emit_weak_principal_inf_derivation_context,
                generate_weak_derived_from_inf=generate_weak_derived_from_inf,
            ),
            on_psinsg2=partial(
                self._emit_weak_principal_psinsg2_derivation_context,
                generate_weak_derived_from_psinsg2=generate_weak_derived_from_psinsg2,
            ),
            on_painsg1=partial(
                self._emit_weak_principal_painsg1_derivation_context,
                generate_weak_derived_from_painsg1=generate_weak_derived_from_painsg1,
            ),
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
            ``_emit_weak_principal_part_sequence`` with the same callback order.

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
            para_id=para_id,
            para_id_num=para_id_num,
            paradigm_type=str(formhash.get("class1", "")),
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

    def _generate_weak_verb_parts_with_emitters(  # noqa: PLR0913
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
        emit_form_for_context: WeakFormContextEmitter,
        emit_painsg1_form: WeakPainsg1RawFormEmitter,
        emit_painsg1_manual: WeakManualEmitter,
        emit_psinsg2_form: WeakPsinsg2FormWithPostEmitter,
        emit_psinsg2_sound: WeakPsinsg2SoundWithPostEmitter,
        add_participle_to_adjectives: WeakParticipleAdder,
    ) -> None:
        """
        Generate weak principal parts by binding low-level emitters once.

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
            emit_form_for_context: Low-level row emitter for direct form output.
            emit_painsg1_form: Low-level direct form emitter for ``PaInSg1`` rows.
            emit_painsg1_manual: Low-level manual-row emitter for ``PaInSg1`` rows.
            emit_psinsg2_form: Low-level direct form emitter for ``PsInSg2`` rows.
            emit_psinsg2_sound: Low-level sound-change emitter for ``PsInSg2`` rows.
            add_participle_to_adjectives: Callback that stores derived participles.

        Keyword Args:
            Uses keyword-only parameters for all inputs.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe weak principal-part
            sequencing as a fixed order of row emission and branch derivation; this
            helper preserves that order while keeping callback assembly out of
            ``generation.common``.

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
            emit_form=partial(
                self._emit_weak_principal_form_context,
                formhash,
                emit_form_for_context=emit_form_for_context,
            ),
            on_pspt_participle=partial(
                self._emit_weak_principal_pspt_participle_context,
                add_participle_to_adjectives=add_participle_to_adjectives,
            ),
            on_papt_participle=partial(
                self._emit_weak_principal_papt_participle_context,
                add_participle_to_adjectives=add_participle_to_adjectives,
            ),
            on_inf=partial(
                self._emit_weak_principal_inf_derivation_with_emitters,
                emit_form_for_context=emit_form_for_context,
                add_participle_to_adjectives=add_participle_to_adjectives,
            ),
            on_psinsg2=partial(
                self._emit_weak_principal_psinsg2_derivation_with_emitters,
                emit_form=emit_psinsg2_form,
                emit_sound=emit_psinsg2_sound,
            ),
            on_painsg1=partial(
                self._emit_weak_principal_painsg1_derivation_with_emitters,
                emit_form=emit_painsg1_form,
                emit_manual=emit_painsg1_manual,
                add_participle_to_adjectives=add_participle_to_adjectives,
            ),
        )

    # -- weak-derivation orchestration (former weak_derivation_flow.py) -----

    def _emit_weak_inf_form(  # noqa: PLR0913
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

    def _emit_weak_painsg1_form_for_vowel(  # noqa: PLR0913
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

    def _emit_weak_painsg1_form_for_vowel_from_context(  # noqa: PLR0913
        self,
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

    def _emit_weak_painsg1_manual_context(  # noqa: PLR0913
        self,
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

    def _emit_weak_painsg1_participle_context(
        self, context: _WeakPainsg1DerivationContext, form_parts: str,
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

    def _emit_weak_derived_inf_form(  # noqa: PLR0913
        self,
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

    def _emit_weak_psinsg2_form_with_post_derivation_context(
        self,
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

    def _emit_weak_psinsg2_sound_with_post_derivation_context(
        self,
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

    def _emit_weak_derived_inf_participle(
        self,
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
            return self._emit_weak_inf_form(
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
                    self._emit_weak_principal_form_context,
                    emit_form_for_context=emit_form_for_context,
                ),
            )

        def _emit_form(
            dental: str | None,
            ending: str,
            function: str,
            prob: str | int | None,
        ) -> tuple[str, str]:
            return self._emit_weak_derived_inf_form(
                context,
                dental,
                ending,
                function,
                prob,
                emit_weak_inf_form=_emit_inf_form_from_context,
            )

        def _on_participle(form_parts: str) -> None:
            self._emit_weak_derived_inf_participle(
                context,
                form_parts,
                add_participle_to_adjectives=add_participle_to_adjectives,
            )

        self._emit_weak_derived_from_inf_sequence(
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
            return self._emit_weak_painsg1_form_for_vowel_from_context(
                context,
                current_vowel,
                ending,
                function,
                prob,
                post_vowel_simple,
                emit_form_for_vowel=partial(
                    self._emit_weak_painsg1_form_for_vowel,
                    emit_form=emit_form,
                ),
            )

        def _emit_manual(
            form: str,
            form_parts: str,
            function: str,
            prob: str | int | None,
        ) -> None:
            self._emit_weak_painsg1_manual_context(
                context,
                form,
                form_parts,
                function,
                prob,
                emit_manual=emit_manual,
            )

        def _on_participle(form_parts: str) -> None:
            self._emit_weak_painsg1_participle_context(
                context,
                form_parts,
                add_participle_to_adjectives=add_participle_to_adjectives,
            )

        self._emit_weak_derived_from_painsg1_context(
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
            self._emit_weak_psinsg2_form_with_post_derivation_context(
                context,
                ending,
                function,
                prob,
                post_vowel_simple,
                emit_form_with_post_context=partial(
                    self._emit_weak_psinsg2_form_with_post_context,
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
            self._emit_weak_psinsg2_sound_with_post_derivation_context(
                context,
                ending,
                function,
                prob,
                consonant_change_prob,
                post_vowel_simple,
                emit_sound_with_post_context=partial(
                    self._emit_weak_psinsg2_sound_with_post_context,
                    emit_sound_with_post=emit_sound,
                ),
            )

        self._emit_weak_derived_from_psinsg2_context(
            probability=probability,
            post_vowel=post_vowel,
            emit_form_with_post=_emit_form_with_post,
            emit_sound_with_post=_emit_sound_with_post,
        )

    # -- former VerbFormGenerator weak forwarding methods (renamed, "weak_" -
    # -- stripped per Task 8 brief) ------------------------------------------

    def _emit_principal_form_context(  # noqa: PLR0913
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
        return self._emit_weak_principal_form_context(
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

    def _emit_inf_form_context(  # noqa: PLR0913
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
        return self._emit_weak_inf_form(
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
            emit_weak_principal_form=self._emit_principal_form_context,
        )

    def _emit_painsg1_form_for_vowel_context(  # noqa: PLR0913
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
        return self._emit_weak_painsg1_form_for_vowel(
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

    def _emit_painsg1_form_for_vowel_derivation_context(
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
        return self._emit_weak_painsg1_form_for_vowel_from_context(
            context,
            current_vowel,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_for_vowel=self._emit_painsg1_form_for_vowel_context,
        )

    def _emit_painsg1_manual_context(
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
        self._emit_weak_painsg1_manual_context(
            context,
            form,
            form_parts,
            function,
            prob,
            emit_manual=partial(
                _generate_and_print_manual, self.run_state, self.output_file
            ),
        )

    def _emit_painsg1_participle_context(
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
        self._emit_weak_painsg1_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_psinsg2_form_with_post_context(  # noqa: PLR0913
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
        self._emit_weak_psinsg2_form_with_post_context(
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

    def _emit_psinsg2_sound_with_post_context(  # noqa: PLR0913
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
        self._emit_weak_psinsg2_sound_with_post_context(
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
            emit_sound_with_post=partial(
                _generate_and_print_form_with_sound_changes_row,
                self.run_state,
                self.output_file,
            ),
        )

    def _emit_psinsg2_form_with_post_derivation_context(
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
        self._emit_weak_psinsg2_form_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_with_post_context=self._emit_psinsg2_form_with_post_context,
        )

    def _emit_psinsg2_sound_with_post_derivation_context(
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
        self._emit_weak_psinsg2_sound_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            consonant_change_prob,
            post_vowel_simple,
            emit_sound_with_post_context=self._emit_psinsg2_sound_with_post_context,
        )

    def _emit_principal_pspt_participle_context(
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
        self._emit_weak_principal_pspt_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_principal_papt_participle_context(
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
        self._emit_weak_principal_papt_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_principal_inf_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak infinitive-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        """
        self._emit_weak_principal_inf_derivation_with_emitters(
            context,
            emit_form_for_context=self._emit_form_for_context,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_principal_psinsg2_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared weak principal-part context.

        """
        self._emit_weak_principal_psinsg2_derivation_with_emitters(
            context,
            emit_form=self._generate_and_print_form,
            emit_sound=partial(
                _generate_and_print_form_with_sound_changes_row,
                self.run_state,
                self.output_file,
            ),
        )

    def _emit_principal_painsg1_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        """
        self._emit_weak_principal_painsg1_derivation_with_emitters(
            context,
            emit_form=self._generate_and_print_form,
            emit_manual=partial(
                _generate_and_print_manual, self.run_state, self.output_file
            ),
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

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
        self._generate_weak_verb_parts_with_emitters(
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
            emit_painsg1_manual=partial(
                _generate_and_print_manual, self.run_state, self.output_file
            ),
            emit_psinsg2_form=self._generate_and_print_form,
            emit_psinsg2_sound=partial(
                _generate_and_print_form_with_sound_changes_row,
                self.run_state,
                self.output_file,
            ),
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_derived_from_inf(  # noqa: PLR0913
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
        self._generate_weak_derived_from_inf(
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

    def _emit_derived_inf_form_context(
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
        return self._emit_weak_derived_inf_form(
            context,
            dental,
            ending,
            function,
            prob,
            emit_weak_inf_form=self._emit_inf_form_context,
        )

    def _emit_derived_inf_participle_context(
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
        self._emit_weak_derived_inf_participle(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_derived_from_painsg1(  # noqa: PLR0913
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
        self._generate_weak_derived_from_painsg1(
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
            emit_manual=partial(
                _generate_and_print_manual, self.run_state, self.output_file
            ),
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _generate_derived_from_psinsg2(  # noqa: PLR0913
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
        self._generate_weak_derived_from_psinsg2(
            formhash=formhash,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            probability=prob,
            emit_form=self._generate_and_print_form,
            emit_sound=partial(
                _generate_and_print_form_with_sound_changes_row,
                self.run_state,
                self.output_file,
            ),
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
