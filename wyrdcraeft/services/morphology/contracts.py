"""Shared protocols for morphology refactor boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TextIO, TypeVar

if TYPE_CHECKING:
    from .session import GenerationRunState, WordPool


class FormWriter(Protocol):
    """Minimal writer protocol used by morphology emitters."""

    def write(self, text: str) -> Any:
        """Write text to the underlying output stream."""


class ParityFormOutput(Protocol):
    """Parity-aware output protocol accepting legacy form payloads."""

    def emit_form_data(
        self, run_state: GenerationRunState, form_data: dict[str, str]
    ) -> Any:
        """
        Emit one legacy form payload using parity row semantics.

        Note:
            Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this turns one
            lexeme-plus-inflection payload into surface-form rows for the word's
            Part of Speech.

        Args:
            run_state: Active generation run state tracking the output counter.
            form_data: Legacy mutable row payload.

        """


#: Supported output targets for morphology emission.
FormOutput = TextIO | FormWriter | ParityFormOutput

#: Contravariant word type accepted by classification rules.
TWord_contra = TypeVar("TWord_contra", contravariant=True)
#: Contravariant context type accepted by classification rules.
TContext_contra = TypeVar("TContext_contra", contravariant=True)


class Rule(Protocol[TWord_contra, TContext_contra]):
    """Ordered classification rule for paradigm assignment."""

    def apply(self, word: TWord_contra, context: TContext_contra) -> list[str]:
        """
        Return matched paradigm labels for ``word`` in ``context``.

        Note:
            Paradigm matching follows patterns described in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this picks the inflection class for a noun, verb,
            adjective, adverb, or numeral.

        Args:
            word: Candidate word model to classify.
            context: Additional assignment context.

        Returns:
            Matched paradigm labels in rule order.

        """


#: Ordered collection of paradigm assignment rules.
RuleSet = list[Rule[TWord_contra, TContext_contra]]


class ParadigmAssigner(Protocol):
    """Session-level assigner contract."""

    def assign(self, word_pool: WordPool) -> None:
        """
        Assign paradigms in-place for session words.

        Note:
            Paradigm assignment reflects the noun/verb/adjective class cues in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, it labels each Part of Speech with the right paradigm.

        Args:
            word_pool: Word pool with loaded words to assign paradigms for.

        """


class FormEmitter(Protocol):
    """Form emission contract."""

    def emit(self, form_record: dict[str, str], output: FormOutput) -> None:
        """
        Emit one normalized form record to ``output``.

        Note:
            Form realization follows Old English inflection conventions in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this writes one inflected form for the row's Part of
            Speech.

        Args:
            form_record: Normalized form payload ready for output.
            output: Target output sink.

        """
