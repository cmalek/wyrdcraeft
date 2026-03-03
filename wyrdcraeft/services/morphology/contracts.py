"""Shared protocols for morphology refactor boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TextIO, TypeVar

if TYPE_CHECKING:
    from .session import GeneratorSession


class FormWriter(Protocol):
    """Minimal writer protocol used by morphology emitters."""

    def write(self, text: str) -> Any:
        """Write text to the underlying output stream."""


FormOutput = TextIO | FormWriter

TWord_contra = TypeVar("TWord_contra", contravariant=True)
TContext_contra = TypeVar("TContext_contra", contravariant=True)


class Rule(Protocol[TWord_contra, TContext_contra]):
    """Ordered classification rule for paradigm assignment."""

    def apply(self, word: TWord_contra, context: TContext_contra) -> list[str]:
        """Return matched paradigm labels for ``word`` in ``context``."""


RuleSet = list[Rule[TWord_contra, TContext_contra]]


class ParadigmAssigner(Protocol):
    """Session-level assigner contract."""

    def assign(self, session: GeneratorSession) -> None:
        """Assign paradigms in-place for session words."""


class FormEmitter(Protocol):
    """Form emission contract."""

    def emit(self, form_record: dict[str, str], output: FormOutput) -> None:
        """Emit one normalized form record to ``output``."""
