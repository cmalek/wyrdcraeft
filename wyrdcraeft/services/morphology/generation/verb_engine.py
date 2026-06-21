"""
Verb generation orchestration wrappers.

This module introduces explicit orchestration boundaries while delegating to the
existing parity-preserving implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .common import VerbFormGenerator

if TYPE_CHECKING:
    from ..contracts import FormOutput
    from ..progress import MorphologyGenerateProgressCoordinator
    from ..session import GeneratorSession


class VerbFormOrchestrator:
    """
    Compatibility orchestrator for verb form generation.

    Args:
        session: Active generation session.
        output_file: Output sink receiving generated rows.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        session: GeneratorSession,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Bind one session, output sink, and optional progress coordinator.

        Args:
            session: Active generation session.
            output_file: Output sink receiving generated rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Active generation session.
        self._session = session
        #: Output sink receiving generated rows.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """Generate all verb forms using the legacy parity engine."""
        generator = VerbFormGenerator(
            self._session,
            self._output_file,
            progress=self._progress,
        )
        generator.generate()
