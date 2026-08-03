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
    from ..session import GenerationRunState, WordPool


class VerbFormOrchestrator:
    """
    Compatibility orchestrator for verb form generation.

    Args:
        word_pool: Categorized word pool for this run.
        run_state: Cross-stage scalar run state for this run.
        output_file: Output sink receiving generated rows.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Bind one word pool, run state, output sink, and optional progress coordinator.

        Args:
            word_pool: Categorized word pool for this run.
            run_state: Cross-stage scalar run state for this run.
            output_file: Output sink receiving generated rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Categorized word pool for this run.
        self._word_pool = word_pool
        #: Cross-stage scalar run state for this run.
        self._run_state = run_state
        #: Output sink receiving generated rows.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """Generate all verb forms using the legacy parity engine."""
        generator = VerbFormGenerator(
            self._word_pool,
            self._run_state,
            self._output_file,
            progress=self._progress,
        )
        generator.generate()
