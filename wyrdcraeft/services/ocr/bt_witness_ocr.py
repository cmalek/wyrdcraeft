"""CLI-facing orchestration for Bosworth-Toller OCR witness preparation."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from wyrdcraeft.services.ocr.bt_tile_ocr import (
    WITNESSES_OUTPUT_DIR,
    WITNESSES_PAGES_DIR,
    WITNESSES_TILES_DIR,
    discover_tile_images,
    run_page_witness_ocr,
    tile_id_from_image_path,
)
from wyrdcraeft.services.ocr.bt_tile_ocr import (
    OCRRunner as _TileOCRRunner,
)
from wyrdcraeft.services.ocr.bt_witness_prep.manifest import PAGES_MANIFEST_REL
from wyrdcraeft.services.ocr.bt_witness_prep.models import (
    BTWitnessPrepInput,
    BTWitnessPrepRun,
)
from wyrdcraeft.services.ocr.bt_witness_prep.pipeline import (
    TILES_OUTPUT_DIR,
    prepare_pages,
)

if TYPE_CHECKING:
    from wyrdcraeft.services.ocr.old_english_pipeline import OldEnglishOCRConfig

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
        run_ocr: Whether to run tile OCR and emit ``witnesses/`` artifacts.
        skip_prep: When ``True`` with ``run_ocr``, require existing prep artifacts.
        skip_ocr: When ``True`` with ``run_ocr``, reuse cached per-tile OCR text.
        tile_ocr_base: Shared olmocr settings for per-tile OCR invocations.

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
    #: Whether to run tile OCR and emit ``witnesses/`` artifacts.
    run_ocr: bool = False
    #: When ``True`` with ``run_ocr``, require existing prep artifacts.
    skip_prep: bool = False
    #: When ``True`` with ``run_ocr``, reuse cached per-tile OCR text.
    skip_ocr: bool = False
    #: Shared olmocr settings for per-tile OCR invocations.
    tile_ocr_base: OldEnglishOCRConfig | None = None


@dataclass(frozen=True)
class BTWitnessOCRRun:
    """
    Result contract for one Bosworth-Toller OCR command run.

    Args:
        prep_run: Witness-prep run manifest when preparation executed.
        witnesses_dir: Root ``witnesses/`` directory when OCR executed.
        page_witness_paths: Joined page markdown witness paths.
        tile_witness_paths: Per-tile normalized OCR text paths.

    """

    #: Witness-prep run manifest when preparation executed.
    prep_run: BTWitnessPrepRun | None = None
    #: Root ``witnesses/`` directory when OCR executed.
    witnesses_dir: Path | None = None
    #: Joined page markdown witness paths.
    page_witness_paths: tuple[Path, ...] = ()
    #: Per-tile normalized OCR text paths.
    tile_witness_paths: tuple[Path, ...] = ()


class BTWitnessOCROrchestrator:
    """
    Run Bosworth-Toller witness preparation and optional tile OCR.

    Keyword Args:
        prep_runner: Callable that executes one witness-prep run.
        tile_ocr_runner: Injectable per-tile OCR runner for tests.

    """

    def __init__(
        self,
        *,
        prep_runner: _PrepRunner | None = None,
        tile_ocr_runner: _TileOCRRunner | None = None,
    ) -> None:
        """
        Initialize with optional runner overrides.

        Keyword Args:
            prep_runner: Witness-prep runner override.
            tile_ocr_runner: Per-tile OCR runner override.

        """
        #: Callable that executes one witness-prep run.
        self._prep_runner = prep_runner or prepare_pages
        #: Injectable per-tile OCR runner for tests.
        self._tile_ocr_runner = tile_ocr_runner

    def run(self, config: BTWitnessOCRConfig) -> BTWitnessOCRRun:
        """
        Execute one configured Bosworth-Toller OCR command run.

        Side Effects:
            Writes prep and/or witness artifacts under ``config.output_dir``.

        Args:
            config: Source, output, filtering, stage, and overwrite settings.

        Returns:
            Typed run manifest with optional witness artifact paths.

        """
        if config.run_ocr:
            prep_run: BTWitnessPrepRun | None
            if config.skip_prep:
                self._assert_prep_artifacts_exist(config.output_dir)
                prep_run = None
            else:
                prep_run = self.run_prep(config)
            return self.run_ocr_stage(config, prep_run)

        prep_run = self.run_prep(config)
        return BTWitnessOCRRun(prep_run=prep_run)

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

    def run_ocr_stage(
        self,
        config: BTWitnessOCRConfig,
        prep_run: BTWitnessPrepRun | None = None,
    ) -> BTWitnessOCRRun:
        """
        OCR prepared tiles and write joined page witnesses.

        Side Effects:
            Writes ``witnesses/tiles/<tile_id>/`` workspaces and
            ``witnesses/pages/<page_id>.md`` under ``config.output_dir``.

        Args:
            config: Output directory, filtering, and OCR stage settings.
            prep_run: Optional prep run whose page ids should drive OCR.

        Returns:
            Typed run manifest with witness artifact paths.

        """
        output_dir = config.output_dir.resolve()
        witnesses_dir = output_dir / WITNESSES_OUTPUT_DIR
        tiles_root = output_dir / WITNESSES_TILES_DIR
        pages_dir = output_dir / WITNESSES_PAGES_DIR
        page_ids = self._resolve_page_ids(output_dir, config, prep_run)

        page_witness_paths: list[Path] = []
        tile_witness_paths: list[Path] = []

        def _tile_output_dir(tile_path: Path, _index: int) -> Path:
            tile_id = tile_id_from_image_path(tile_path)
            return tiles_root / tile_id

        for page_id in page_ids:
            tile_paths = discover_tile_images(output_dir, page_id)
            page_text = run_page_witness_ocr(
                tile_paths,
                _tile_output_dir,
                skip_ocr=config.skip_ocr,
                ocr_runner=self._tile_ocr_runner,
                ocr_config=config.tile_ocr_base,
            )
            for tile_path in tile_paths:
                tile_dir = _tile_output_dir(tile_path, 0)
                tile_witness_paths.append(tile_dir / "03_normalized.txt")
            page_path = pages_dir / f"{page_id}.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(page_text, encoding="utf-8")
            page_witness_paths.append(page_path)

        return BTWitnessOCRRun(
            prep_run=prep_run,
            witnesses_dir=witnesses_dir,
            page_witness_paths=tuple(page_witness_paths),
            tile_witness_paths=tuple(tile_witness_paths),
        )

    def _resolve_page_ids(
        self,
        output_dir: Path,
        config: BTWitnessOCRConfig,
        prep_run: BTWitnessPrepRun | None,
    ) -> tuple[str, ...]:
        """
        Resolve page ids for one OCR stage run.

        Args:
            output_dir: Witness-prep workspace root.
            config: Optional page filter settings.
            prep_run: Optional prep run whose page ids should drive OCR.

        Returns:
            Page ids in stable sorted order.

        """
        if prep_run is not None:
            page_ids = tuple(
                sorted(page.page_id for page in prep_run.preprocessed_pages),
            )
        else:
            page_ids = _load_page_ids_from_manifest(output_dir)

        if config.page_ids is None:
            return page_ids

        requested = set(config.page_ids)
        filtered = tuple(page_id for page_id in page_ids if page_id in requested)
        missing = requested.difference(filtered)
        if missing:
            missing_text = ", ".join(sorted(missing))
            message = (
                "Requested page_id values not found in prep manifests: "
                f"{missing_text}"
            )
            raise ValueError(message)
        return filtered

    def _assert_prep_artifacts_exist(self, output_dir: Path) -> None:
        """
        Require an existing witness-prep workspace before OCR-only runs.

        Args:
            output_dir: Candidate witness-prep workspace root.

        Raises:
            RuntimeError: When ``manifests/`` or ``tiles/`` is missing.

        """
        resolved = output_dir.resolve()
        manifests_dir = resolved / "manifests"
        tiles_dir = resolved / TILES_OUTPUT_DIR
        if manifests_dir.is_dir() and tiles_dir.is_dir():
            return
        message = (
            "Witness-prep artifacts are required for --skip-prep --ocr. "
            f"Expected manifests/ and tiles/ under {resolved}."
        )
        raise RuntimeError(message)

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
        if (resolved / "manifests").is_dir() or (resolved / TILES_OUTPUT_DIR).is_dir():
            message = (
                "Witness-prep output directory already contains prep artifacts: "
                f"{resolved}. Use --force or choose a fresh --output-dir."
            )
            raise RuntimeError(message)


def _load_page_ids_from_manifest(output_dir: Path) -> tuple[str, ...]:
    """
    Load page ids from ``manifests/pages.jsonl``.

    Args:
        output_dir: Witness-prep workspace root.

    Returns:
        Page ids in stable sorted order.

    Raises:
        FileNotFoundError: When the page manifest is missing.
        RuntimeError: When the page manifest contains no rows.

    """
    pages_manifest = output_dir / PAGES_MANIFEST_REL
    if not pages_manifest.is_file():
        message = f"missing page manifest for OCR stage: {pages_manifest}"
        raise FileNotFoundError(message)

    page_ids: list[str] = []
    for line in pages_manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        page_ids.append(str(row["page_id"]))

    if not page_ids:
        message = f"page manifest contains no pages: {pages_manifest}"
        raise RuntimeError(message)

    return tuple(sorted(page_ids))
