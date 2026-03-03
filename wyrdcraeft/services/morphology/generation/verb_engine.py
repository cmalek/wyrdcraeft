"""
Verb generation orchestration wrappers.

This module introduces explicit orchestration boundaries while delegating to the
existing parity-preserving implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..generators.common import VerbFormGenerator

if TYPE_CHECKING:
    from ..contracts import FormOutput
    from ..session import GeneratorSession

class VerbFormOrchestrator:
    """Compatibility orchestrator for verb form generation."""

    def __init__(self, session: GeneratorSession, output_file: FormOutput) -> None:
        self._session = session
        self._output_file = output_file

    def generate(self) -> None:
        """Generate all verb forms using the legacy parity engine."""
        generator = VerbFormGenerator(self._session, self._output_file)
        generator.generate()
