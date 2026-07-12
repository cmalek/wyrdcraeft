"""CLI-facing orchestration for Bosworth-Toller OCR witness preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from wyrdcraeft.services.ocr.bt_witness_prep.models import (
    BTWitnessPrepInput,
    BTWitnessPrepRun,
)
from wyrdcraeft.services.ocr.bt_witness_prep.pipeline import prepare_pages

#: Default JP2 source directory for Bosworth-Toller scan pages.
DEFAULT_BT_SOURCE_DIR = Path("data/bosworth_toller/jp2")
#: Default witness-prep workspace for iterative development runs.
DEFAULT_BT_OUTPUT_DIR = Path("data/ocr/bosworth-toller/prep")
#: Default preprocessing recipe identifier for two-column dictionary pages.
DEFAULT_BT_RECIPE_ID = "bt-two-column-v1"
#: Default vertical overlap between upper and lower column halves.
DEFAULT_BT_OVERLAP_PX = 30
#: Callable that executes one witness-prep run.
_PrepRunner = Callable[[BTWitnessPrepInput], BTWitnessPrepRun]


@dataclass(frozen=True)
class BTWitnessOCRConfig:
    """
    Configuration contract for one Bosworth-Toller OCR command run.

    Args:
        source_dir: Directory containing Bosworth-Toller ``.jp2`` scan pages.
        output_dir: Workspace directory for prepared witness artifacts.
        recipe_id: Preprocessing recipe identifier applied to every page.
        overlap_px: Vertical overlap between upper and lower column halves.
        page_ids: Optional ``page_id`` slugs to keep after enumeration.
        limit: Optional maximum page count applied after ``page_ids`` filtering.
        force: Whether to overwrite an existing prep workspace.

    """

    #: Directory containing Bosworth-Toller ``.jp2`` scan pages.
    source_dir: Path
    #: Workspace directory for prepared witness artifacts.
    output_dir: Path
    #: Preprocessing recipe identifier applied to every page.
    recipe_id: str = DEFAULT_BT_RECIPE_ID
    #: Vertical overlap between upper and lower column halves.
    overlap_px: int = DEFAULT_BT_OVERLAP_PX
    #: Optional ``page_id`` slugs to keep after enumeration.
    page_ids: tuple[str, ...] | None = None
    #: Optional maximum page count applied after ``page_ids`` filtering.
    limit: int | None = None
    #: Whether to overwrite an existing prep workspace.
    force: bool = False


class BTWitnessOCROrchestrator:
    """
    Run Bosworth-Toller witness preparation with CLI safety guards.

    Args:
        prep_runner: Callable that executes one witness-prep run.

    """

    def __init__(
        self,
        *,
        prep_runner: _PrepRunner | None = None,
    ) -> None:
        """
        Initialize one orchestrator with an optional prep runner override.

        Keyword Args:
            prep_runner: Callable that executes one witness-prep run.

        """
        #: Callable that executes one witness-prep run.
        self._prep_runner = prep_runner or prepare_pages

    def run_prep(self, config: BTWitnessOCRConfig) -> BTWitnessPrepRun:
        """
        Prepare Bosworth-Toller witness pages for one configured run.

        Side Effects:
            Writes page and tile images plus JSONL manifests under
            ``config.output_dir`` when the workspace is writable.

        Args:
            config: Source, output, filtering, and overwrite settings.

        Raises:
            RuntimeError: When the output workspace already contains prep
                artifacts and ``force`` is false.

        Returns:
            Typed witness-prep run manifest.

        """
        self._assert_output_dir_writable(config.output_dir, config.force)
        prep_input = BTWitnessPrepInput(
            source_dir=config.source_dir,
            output_dir=config.output_dir,
            recipe_id=config.recipe_id,
            overlap_px=config.overlap_px,
            page_ids=config.page_ids,
            limit=config.limit,
        )
        return self._prep_runner(prep_input)

    def _assert_output_dir_writable(self, output_dir: Path, force: bool) -> None:
        """
        Refuse to overwrite an existing witness-prep workspace.

        Args:
            output_dir: Candidate output workspace root.
            force: Whether overwrite is explicitly requested.

        Raises:
            RuntimeError: When prep artifacts already exist and ``force`` is false.

        """
        if force:
            return

        resolved = output_dir.resolve()
        if (resolved / "manifests").is_dir() or (resolved / "tiles").is_dir():
            message = (
                "Witness-prep output directory already contains prep artifacts: "
                f"{resolved}. Use --force or choose a fresh --output-dir."
            )
            raise RuntimeError(message)
