from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wyrdcraeft.services.ocr.bt_tile_ocr import (
    CANDIDATE_TILE_READING_ORDER,
    OCRRunner,
)
from wyrdcraeft.services.ocr.bt_tile_ocr import (
    discover_tile_images as discover_candidate_tile_images,
)
from wyrdcraeft.services.ocr.bt_tile_ocr import (
    run_page_witness_ocr as run_candidate_page_ocr,
)
from wyrdcraeft.services.ocr.bt_tile_ocr import (
    run_tile_ocr as run_page_ocr,
)
from wyrdcraeft.services.ocr.bt_witness_prep import (
    BTWitnessPrepInput,
    prepare_pages,
)
from wyrdcraeft.services.ocr.bt_witness_prep.manifest import TILES_MANIFEST_REL
from wyrdcraeft.services.ocr.bt_witness_prep.validation import (
    STAGE_B_RULE_DESCRIPTION,
    BTRecipeStageBComparison,
    BTValidationManifest,
    evaluate_stage_b_recipe,
    load_validation_manifest,
)

DEFAULT_MANIFEST = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "ocr"
    / "bt_witness_prep"
    / "validation_manifest.json"
)
DEFAULT_MANIFEST_DIR = DEFAULT_MANIFEST.parent
DEFAULT_RECIPE_ID = "bt-two-column-v1"

__all__ = [
    "CANDIDATE_TILE_READING_ORDER",
    "OCRRunner",
    "discover_candidate_tile_images",
    "run_candidate_page_ocr",
    "run_page_ocr",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse benchmark CLI arguments.

    Args:
        argv: Optional argument vector override for tests.

    Returns:
        Parsed namespace for one benchmark invocation.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark BT witness-prep candidate recipes against raw whole-page "
            "baselines for Stage B OCR validation."
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to validation_manifest.json.",
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=None,
        help="Directory containing comparison witness text files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path for the emitted JSON summary.",
    )
    parser.add_argument(
        "--recipe-id",
        default=DEFAULT_RECIPE_ID,
        help="Candidate witness-preparation recipe identifier.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional JP2 source directory for prepare_pages.",
    )
    parser.add_argument(
        "--prepare-output-dir",
        type=Path,
        default=None,
        help="Workspace for prepare_pages outputs when --source-dir is set.",
    )
    parser.add_argument(
        "--skip-ocr",
        action="store_true",
        help="Skip live olmocr and load pre-supplied hypothesis text files.",
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=None,
        help="Directory of raw whole-page baseline OCR text files keyed by page id.",
    )
    parser.add_argument(
        "--candidate-dir",
        type=Path,
        default=None,
        help="Directory of candidate recipe OCR text files keyed by page id.",
    )
    parser.add_argument(
        "--ocr-input-dir",
        type=Path,
        default=None,
        help=(
            "Deprecated for Stage B live pairing; baseline images are rendered "
            "from --source-dir via validation_manifest source_filename."
        ),
    )
    parser.add_argument(
        "--ocr-output-dir",
        type=Path,
        default=None,
        help="Workspace root for live OCR runs when --skip-ocr is not set.",
    )
    return parser.parse_args(argv)


def materialize_baseline_pages(
    manifest: BTValidationManifest,
    source_dir: Path,
    output_dir: Path,
) -> dict[str, Path]:
    """
    Render raw whole-page baseline PNGs from validation source JP2 files.

    Side Effects:
        Creates ``output_dir`` and writes one PNG per validation page.

    Args:
        manifest: Validation manifest whose ``source_filename`` values select
            baseline inputs.
        source_dir: Directory containing raw JP2 (or other scan) source pages.
        output_dir: Destination directory for ``<page_id>.png`` baseline images.

    Returns:
        Baseline image paths keyed by manifest ``page_id``.

    Raises:
        FileNotFoundError: When a manifest ``source_filename`` is missing under
            ``source_dir``.

    """
    resolved_source = source_dir.resolve()
    resolved_output = output_dir.resolve()
    resolved_output.mkdir(parents=True, exist_ok=True)

    baseline_paths: dict[str, Path] = {}
    for page in manifest.pages:
        source_path = resolved_source / page.source_filename
        if not source_path.is_file():
            message = (
                f"missing baseline source for {page.page_id}: "
                f"{source_path} (from source_filename={page.source_filename!r})"
            )
            raise FileNotFoundError(message)
        image_path = resolved_output / f"{page.page_id}.png"
        with Image.open(source_path) as image:
            image.convert("RGB").save(image_path, format="PNG")
        baseline_paths[page.page_id] = image_path
    return baseline_paths


def load_hypothesis_dir(
    hypothesis_dir: Path,
    page_ids: tuple[str, ...],
) -> dict[str, str]:
    """
    Load pre-supplied OCR text files keyed by page id.

    Args:
        hypothesis_dir: Directory containing ``<page_id>.txt`` files.
        page_ids: Validation page ids to load.

    Returns:
        OCR text keyed by page id.

    Raises:
        FileNotFoundError: When a required page text file is missing.

    """
    hypotheses: dict[str, str] = {}
    for page_id in page_ids:
        text_path = hypothesis_dir / f"{page_id}.txt"
        if not text_path.is_file():
            message = f"missing hypothesis text for {page_id}: {text_path}"
            raise FileNotFoundError(message)
        hypotheses[page_id] = text_path.read_text(encoding="utf-8")
    return hypotheses


def collect_guardrail_flags(prep_output_dir: Path | None) -> dict[str, bool]:
    """
    Read small-component guardrail flags from a prepare_pages workspace.

    Args:
        prep_output_dir: Witness-prep output directory, if preparation ran.

    Returns:
        Guardrail failure flags keyed by page id.

    """
    if prep_output_dir is None:
        return {}

    tiles_manifest = prep_output_dir / TILES_MANIFEST_REL
    if not tiles_manifest.is_file():
        return {}

    guardrails: dict[str, bool] = {}
    for line in tiles_manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        page_id = str(row["page_id"])
        quality = row.get("quality") or {}
        failed = bool(quality.get("small_component_guardrail_failed"))
        guardrails[page_id] = guardrails.get(page_id, False) or failed
    return guardrails


def build_stage_b_summary(  # noqa: PLR0913
    *,
    manifest_path: Path,
    manifest_dir: Path,
    recipe_id: str,
    baseline_hypotheses: dict[str, str],
    candidate_hypotheses: dict[str, str],
    guardrail_flags: dict[str, bool] | None = None,
    ocr_mode: str,
    baseline_arm: dict[str, Any] | None = None,
    candidate_arm: dict[str, Any] | None = None,
    page_arm_metadata: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Build one Stage B benchmark summary payload.

    Args:
        manifest_path: Validation manifest path used for the run.
        manifest_dir: Directory containing comparison witness text files.
        recipe_id: Candidate recipe identifier under test.
        baseline_hypotheses: Raw whole-page OCR text keyed by page id.
        candidate_hypotheses: Candidate recipe OCR text keyed by page id.

    Keyword Args:
        guardrail_flags: Optional small-component guardrail flags keyed by page id.
        ocr_mode: OCR execution mode recorded in the summary.
        baseline_arm: Optional provenance metadata for the baseline OCR arm.
        candidate_arm: Optional provenance metadata for the candidate OCR arm.
        page_arm_metadata: Optional per-page image provenance rows.

    Returns:
        JSON-serializable benchmark summary with pass rule and ranking fields.

    """
    manifest = load_validation_manifest(manifest_path)
    comparison = evaluate_stage_b_recipe(
        recipe_id=recipe_id,
        manifest=manifest,
        manifest_dir=manifest_dir,
        baseline_hypotheses=baseline_hypotheses,
        candidate_hypotheses=candidate_hypotheses,
        small_component_guardrail_by_page=guardrail_flags,
    )
    summary: dict[str, Any] = {
        "manifest": str(manifest_path),
        "manifest_dir": str(manifest_dir),
        "recipe_id": recipe_id,
        "ocr_mode": ocr_mode,
        "pass_rule": STAGE_B_RULE_DESCRIPTION,
        "ranking": rank_stage_b_results((comparison,)),
        "comparison": asdict(comparison),
    }
    if baseline_arm is not None:
        summary["baseline_arm"] = baseline_arm
    if candidate_arm is not None:
        summary["candidate_arm"] = candidate_arm
    if page_arm_metadata is not None:
        summary["page_arm_metadata"] = page_arm_metadata
    return summary


def rank_stage_b_results(
    results: tuple[BTRecipeStageBComparison, ...],
) -> list[dict[str, Any]]:
    """
    Rank candidate recipes by Stage B pass status and CER improvement.

    Args:
        results: Candidate recipe comparisons to rank.

    Returns:
        Ranked summary rows with pass status and headline metrics.

    """
    ordered = sorted(
        results,
        key=lambda result: (
            result.passes_stage_b,
            result.relative_cer_improvement,
            -result.candidate_cer,
        ),
        reverse=True,
    )
    return [
        {
            "rank": index + 1,
            "recipe_id": result.recipe_id,
            "passes_stage_b": result.passes_stage_b,
            "baseline_cer": result.baseline_cer,
            "candidate_cer": result.candidate_cer,
            "relative_cer_improvement": result.relative_cer_improvement,
            "historical_char_exact_match_rate": result.historical_char_exact_match_rate,
            "small_component_guardrail_failed": result.small_component_guardrail_failed,
        }
        for index, result in enumerate(ordered)
    ]


def run_benchmark(
    args: argparse.Namespace,
    *,
    ocr_runner: OCRRunner | None = None,
) -> dict[str, Any]:
    """
    Execute one Stage B benchmark run from parsed CLI arguments.

    Args:
        args: Parsed benchmark CLI namespace.

    Keyword Args:
        ocr_runner: Injectable OCR runner for tests; live mode only.

    Returns:
        JSON-serializable benchmark summary.

    Raises:
        ValueError: When required text directories are missing for offline mode.
        RuntimeError: When live OCR is requested but inputs are not configured.

    """
    manifest_path = args.manifest.resolve()
    manifest_dir = (args.manifest_dir or manifest_path.parent).resolve()
    manifest = load_validation_manifest(manifest_path)
    page_ids = tuple(page.page_id for page in manifest.pages)

    prep_output_dir = (
        args.prepare_output_dir.resolve()
        if args.prepare_output_dir
        else None
    )
    if args.source_dir is not None:
        if prep_output_dir is None:
            message = "--prepare-output-dir is required when --source-dir is set"
            raise ValueError(message)
        prepare_pages(
            BTWitnessPrepInput(
                source_dir=args.source_dir.resolve(),
                output_dir=prep_output_dir,
                recipe_id=args.recipe_id,
            ),
        )

    baseline_arm: dict[str, Any] | None = None
    candidate_arm: dict[str, Any] | None = None
    page_arm_metadata: list[dict[str, Any]] | None = None

    if args.skip_ocr:
        if args.baseline_dir is None or args.candidate_dir is None:
            message = "--baseline-dir and --candidate-dir are required with --skip-ocr"
            raise ValueError(message)
        baseline_hypotheses = load_hypothesis_dir(
            args.baseline_dir.resolve(),
            page_ids,
        )
        candidate_hypotheses = load_hypothesis_dir(
            args.candidate_dir.resolve(),
            page_ids,
        )
        ocr_mode = "offline_pre_supplied_text"
    else:
        if args.ocr_output_dir is None:
            message = (
                "Live OCR requires --ocr-output-dir, or use --skip-ocr with "
                "pre-supplied text directories."
            )
            raise RuntimeError(message)
        if args.source_dir is None:
            message = (
                "Live OCR requires --source-dir so baseline pages can be "
                "rendered from validation_manifest source_filename values."
            )
            raise RuntimeError(message)
        if prep_output_dir is None:
            message = (
                "Live OCR requires --prepare-output-dir with prepared candidate "
                "tiles from prepare_pages()."
            )
            raise RuntimeError(message)

        ocr_output_dir = args.ocr_output_dir.resolve()
        baseline_image_dir = ocr_output_dir / "baseline_pages"
        baseline_images = materialize_baseline_pages(
            manifest,
            args.source_dir.resolve(),
            baseline_image_dir,
        )
        baseline_hypotheses = {}
        candidate_hypotheses = {}
        page_arm_metadata = []
        for page in manifest.pages:
            page_id = page.page_id
            baseline_image = baseline_images[page_id]
            baseline_hypotheses[page_id] = run_page_ocr(
                baseline_image,
                ocr_output_dir / "baseline" / page_id,
                ocr_runner=ocr_runner,
            )
            tile_paths = discover_candidate_tile_images(prep_output_dir, page_id)
            def _candidate_tile_output_dir(
                _tile_path: Path,
                index: int,
                *,
                resolved_page_id: str = page_id,
            ) -> Path:
                return (
                    ocr_output_dir
                    / "candidate"
                    / resolved_page_id
                    / f"tile-{index:02d}"
                )

            candidate_hypotheses[page_id] = run_candidate_page_ocr(
                tile_paths,
                _candidate_tile_output_dir,
                ocr_runner=ocr_runner,
            )
            page_arm_metadata.append(
                {
                    "page_id": page_id,
                    "baseline_image_path": str(baseline_image),
                    "candidate_image_paths": [str(path) for path in tile_paths],
                    "candidate_tile_count": len(tile_paths),
                },
            )
        baseline_arm = {
            "kind": "raw_whole_page",
            "image_dir": str(baseline_image_dir),
        }
        candidate_arm = {
            "kind": "prepared_tiles_concatenated",
            "workspace_dir": str(prep_output_dir),
        }
        ocr_mode = "live_olmocr"

    return build_stage_b_summary(
        manifest_path=manifest_path,
        manifest_dir=manifest_dir,
        recipe_id=args.recipe_id,
        baseline_hypotheses=baseline_hypotheses,
        candidate_hypotheses=candidate_hypotheses,
        guardrail_flags=collect_guardrail_flags(prep_output_dir),
        ocr_mode=ocr_mode,
        baseline_arm=baseline_arm,
        candidate_arm=candidate_arm,
        page_arm_metadata=page_arm_metadata,
    )


def main(argv: list[str] | None = None) -> int:
    """
    Run the Stage B benchmark CLI and write one JSON summary.

    Args:
        argv: Optional argument vector override for tests.

    Returns:
        Process exit code where ``0`` means success.

    """
    args = parse_args(argv)
    summary = run_benchmark(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["ranking"], indent=2))
    print(f"pass_rule: {summary['pass_rule']}")
    print(f"wrote summary to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
