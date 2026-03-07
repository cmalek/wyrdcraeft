from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.ocr.benchmark_wright_live import (
    DEFAULT_FIXTURE_STEMS,
    _build_base_profile,
    _evaluate_candidate,
    _load_thresholds,
    fixture_traits_for,
)

#: Default Q8_0 model artifact path used in matrix runs.
DEFAULT_MODEL_Q8_PATH = "./data/models/olmOCR-2-7B-1025-Q8_0.gguf"
#: Default Q6_K_M model artifact path used in matrix runs.
DEFAULT_MODEL_Q6_PATH = "./data/models/olmOCR-2-7B-1025-Q6_K_M.gguf"
#: Default Q5_K_M model artifact path used in matrix runs.
DEFAULT_MODEL_Q5_PATH = "./data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf"
#: Default multimodal projector artifact path used in matrix runs.
DEFAULT_MMPROJ_PATH = "./data/models/mmproj-olmOCR-2-7B-1025-vision.gguf"
#: Canonical family token required for model/mmproj compatibility checks.
MODEL_FAMILY_TOKEN = "2-7b-1025"  # noqa: S105
#: Default model-case ordering for matrix execution.
DEFAULT_MODEL_CASE_NAMES = ("Q8_0", "Q6_K_M", "Q5_K_M")
#: Easy-cohort improvement threshold used by acceptance checks.
EASY_IMPROVEMENT_TARGET = 0.20
#: Hard-cohort improvement threshold used by acceptance checks.
HARD_IMPROVEMENT_TARGET = 0.10


@dataclass(frozen=True)
class ModelCase:
    """
    Model and mmproj paths for one benchmark matrix case.

    Args:
        name: Human-readable model-case name.
        model_path: GGUF model path used by OCR pipeline and llama-server.
        mmproj_path: Multimodal projector path used by llama-server.

    """

    #: Human-readable model-case name.
    name: str
    #: GGUF model path used by OCR pipeline and llama-server.
    model_path: str
    #: Multimodal projector path used by llama-server.
    mmproj_path: str


def _parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments for focused OCR parameter matrix benchmarking.

    Returns:
        Parsed CLI namespace.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Run focused OCR matrix benchmarks over model quantization, LLAMA_CTX, "
            "KV-cache quantization, and optional preprocess modes with detailed "
            "quality/stability diagnostics."
        )
    )
    parser.add_argument(
        "--fixtures",
        nargs="+",
        default=list(DEFAULT_FIXTURE_STEMS),
        help=(
            "Fixture stems under tests/fixtures/ocr. "
            "Default includes existing and new multi-page Wright corpus fixtures."
        ),
    )
    parser.add_argument(
        "--ctx-values",
        nargs="+",
        type=int,
        default=[10240],
        help="LLAMA_CTX values to benchmark.",
    )
    parser.add_argument(
        "--cache-types",
        nargs="+",
        default=["q8_0"],
        help=(
            "LLAMA_CACHE_TYPE_K/LLAMA_CACHE_TYPE_V values to benchmark "
            "(default excludes q5_0)."
        ),
    )
    parser.add_argument(
        "--model-q8-path",
        default=DEFAULT_MODEL_Q8_PATH,
        help="GGUF model path for Q8_0 model case.",
    )
    parser.add_argument(
        "--model-q6-path",
        default=DEFAULT_MODEL_Q6_PATH,
        help="GGUF model path for Q6_K_M model case.",
    )
    parser.add_argument(
        "--model-q5-path",
        default=DEFAULT_MODEL_Q5_PATH,
        help="GGUF model path for Q5_K_M model case.",
    )
    parser.add_argument(
        "--mmproj-path",
        default=DEFAULT_MMPROJ_PATH,
        help="mmproj path used for all model cases.",
    )
    parser.add_argument(
        "--warmup-runs",
        type=int,
        default=0,
        help="Warmup runs excluded from metrics.",
    )
    parser.add_argument(
        "--measured-runs",
        type=int,
        default=3,
        help="Measured runs per fixture.",
    )
    parser.add_argument(
        "--proxy-max-tokens-cap",
        type=int,
        default=1500,
        help="Proxy max token cap passed through OCR CLI.",
    )
    parser.add_argument(
        "--proxy-override-length-to-stop",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable proxy finish_reason length->stop override.",
    )
    parser.add_argument(
        "--proxy-upstream-timeout-seconds",
        type=float,
        default=120.0,
        help="Managed proxy upstream timeout.",
    )
    parser.add_argument(
        "--proxy-upstream-max-retries",
        type=int,
        default=1,
        help="Managed proxy retry budget.",
    )
    parser.add_argument(
        "--proxy-upstream-retry-backoff-seconds",
        type=float,
        default=0.5,
        help="Managed proxy retry backoff.",
    )
    parser.add_argument(
        "--olmocr-max-page-retries",
        type=int,
        default=2,
        help="olmocr per-page retry budget.",
    )
    parser.add_argument(
        "--ocr-command-timeout-seconds",
        type=float,
        default=900.0,
        help="Per-page OCR command timeout seconds.",
    )
    parser.add_argument(
        "--fixture-timeout-seconds",
        type=float,
        default=0.0,
        help="Optional hard timeout budget per fixture across measured runs.",
    )
    parser.add_argument(
        "--vision-preprocess-modes",
        nargs="+",
        choices=("off", "apple-vision"),
        default=["off"],
        help="Preprocess modes to include in the matrix (off and/or apple-vision).",
    )
    parser.add_argument(
        "--vision-preprocess-timeout-seconds",
        type=float,
        default=120.0,
        help="Timeout for one preprocess invocation.",
    )
    parser.add_argument(
        "--upstream-base-url",
        default="http://127.0.0.1:18080/v1",
        help="Upstream llama.cpp OpenAI-compatible base URL used by managed proxy.",
    )
    parser.add_argument(
        "--snapshot-interval-seconds",
        type=float,
        default=5.0,
        help="Seconds between in-flight llama token-rate snapshots.",
    )
    parser.add_argument(
        "--print-live-snapshots",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print periodic in-flight llama token-rate snapshots while OCR runs.",
    )
    parser.add_argument(
        "--show-llama-server-logs",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Expose raw llama-server logs (includes eval tokens/sec).",
    )
    parser.add_argument(
        "--print-progress",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print per-page measured progress lines.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("data/ocr/wright_matrix_benchmark_report.json"),
        help="Path for JSON report output.",
    )
    return parser.parse_args()


def _sha256_file(path: Path) -> str:
    """
    Compute SHA256 digest for one file.

    Args:
        path: File to hash.

    Returns:
        Hex digest string.

    """
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_model_case(*, repo_root: Path, case: ModelCase) -> dict[str, Any]:
    """
    Verify model/mmproj compatibility and collect artifact metadata.

    Args:
        repo_root: Repository root path.
        case: Model case to verify.

    Returns:
        Verification payload used in matrix rows.

    """
    model_path = (repo_root / case.model_path).resolve()
    mmproj_path = (repo_root / case.mmproj_path).resolve()
    model_exists = model_path.exists()
    mmproj_exists = mmproj_path.exists()
    model_name = model_path.name.lower()
    mmproj_name = mmproj_path.name.lower()
    family_match = (
        MODEL_FAMILY_TOKEN in model_name and MODEL_FAMILY_TOKEN in mmproj_name
    )
    verification = {
        "case_name": case.name,
        "model_requested_path": case.model_path,
        "mmproj_requested_path": case.mmproj_path,
        "model_resolved_path": str(model_path),
        "mmproj_resolved_path": str(mmproj_path),
        "model_exists": model_exists,
        "mmproj_exists": mmproj_exists,
        "model_size_bytes": model_path.stat().st_size if model_exists else 0,
        "mmproj_size_bytes": mmproj_path.stat().st_size if mmproj_exists else 0,
        "model_sha256": _sha256_file(model_path) if model_exists else None,
        "mmproj_sha256": _sha256_file(mmproj_path) if mmproj_exists else None,
        "family_match": family_match,
    }
    verification["valid"] = bool(model_exists and mmproj_exists and family_match)
    return verification


@contextmanager
def _temporary_env(updates: dict[str, str]):
    """
    Temporarily set process environment variables.

    Side Effects:
        Mutates ``os.environ`` for the duration of the context.

    Args:
        updates: Environment values to set while running one benchmark case.

    Yields:
        None.

    """
    sentinel = object()
    previous_values: dict[str, object] = {
        key: os.environ.get(key, sentinel) for key in updates
    }
    for key, value in updates.items():
        os.environ[key] = value
    try:
        yield
    finally:
        for key, previous in previous_values.items():
            if previous is sentinel:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(previous)


def _print_matrix_table(results: list[dict[str, Any]]) -> None:
    """
    Print one compact matrix summary table to stdout.

    Args:
        results: Benchmark result rows.

    """
    headers = (
        "model",
        "ctx",
        "cache",
        "vision",
        "mean_s",
        "median_s",
        "p95_s",
        "pages_min",
        "CER",
        "WER",
        "ae_r",
        "eth_r",
        "thorn_r",
        "macron",
        "failed",
        "veto",
        "eligible",
    )
    print("\nMatrix summary")
    print("\t".join(headers))
    for row in results:
        fidelity = row.get("old_english_fidelity", {})
        print(
            "\t".join(
                [
                    row["model_case_name"],
                    str(row["ctx"]),
                    row["cache_type"],
                    row["vision_preprocess_mode"],
                    f"{float(row['mean_sec_per_page']):.3f}",
                    f"{float(row.get('median_sec_per_page', 0.0)):.3f}",
                    f"{float(row['p95_sec_per_page']):.3f}",
                    f"{float(row['pages_per_minute']):.3f}",
                    f"{float(row['mean_cer']):.4f}",
                    f"{float(row['mean_wer']):.4f}",
                    f"{float(fidelity.get('ae_recall', 0.0)):.4f}",
                    f"{float(fidelity.get('eth_recall', 0.0)):.4f}",
                    f"{float(fidelity.get('thorn_recall', 0.0)):.4f}",
                    f"{float(fidelity.get('macron_recall', 0.0)):.4f}",
                    str(row["failed_pages"]),
                    str(row.get("vetoed", False)).lower(),
                    str(row.get("eligible", False)).lower(),
                ]
            )
        )


def _trait_aggregates_for_row(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Build trait-sliced aggregates for one row using fixture-level results.

    Args:
        row: Matrix result row.

    Returns:
        Trait aggregate mapping.

    """
    fixture_results = row.get("fixture_results", {})
    trait_groups: dict[str, list[dict[str, Any]]] = {}
    for fixture_stats in fixture_results.values():
        for trait in fixture_stats.get("traits", []):
            trait_groups.setdefault(trait, []).append(fixture_stats)
    aggregates: dict[str, dict[str, Any]] = {}
    for trait, items in sorted(trait_groups.items()):
        means = [
            float(item["mean_sec_per_page"])
            for item in items
            if item["pages_measured"]
        ]
        p95_values = [
            float(item["p95_sec_per_page"]) for item in items if item["pages_measured"]
        ]
        pages_measured = sum(int(item["pages_measured"]) for item in items)
        failed_pages = sum(int(item["failed_pages"]) for item in items)
        aggregates[trait] = {
            "fixtures": len(items),
            "pages_measured": pages_measured,
            "failed_pages": failed_pages,
            "mean_sec_per_page": statistics.fmean(means) if means else 0.0,
            "p95_sec_per_page": max(p95_values) if p95_values else 0.0,
            "quality_pass": all(
                bool(item.get("quality_pass", False)) for item in items
            ),
        }
    return aggregates


def _build_model_cases(args: argparse.Namespace) -> list[ModelCase]:
    """
    Build ordered model cases from CLI arguments.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Ordered model cases.

    """
    return [
        ModelCase(
            name=DEFAULT_MODEL_CASE_NAMES[0],
            model_path=args.model_q8_path,
            mmproj_path=args.mmproj_path,
        ),
        ModelCase(
            name=DEFAULT_MODEL_CASE_NAMES[1],
            model_path=args.model_q6_path,
            mmproj_path=args.mmproj_path,
        ),
        ModelCase(
            name=DEFAULT_MODEL_CASE_NAMES[2],
            model_path=args.model_q5_path,
            mmproj_path=args.mmproj_path,
        ),
    ]


def _select_baseline(
    *,
    rows: list[dict[str, Any]],
    primary_ctx_value: int,
) -> dict[str, Any] | None:
    """
    Select baseline row used for quality-veto comparisons.

    Args:
        rows: Matrix result rows.
        primary_ctx_value: First context value requested by caller.

    Returns:
        Baseline row or ``None`` when no valid row exists.

    """
    preferred = [
        row
        for row in rows
        if row["model_case_name"] == "Q8_0"
        and row["cache_type"] == "q8_0"
        and row["vision_preprocess_mode"] == "off"
        and int(row["ctx"]) == primary_ctx_value
        and bool(row["model_verification"]["valid"])
    ]
    if preferred:
        return preferred[0]
    fallback = [row for row in rows if bool(row["model_verification"]["valid"])]
    if fallback:
        return fallback[0]
    return None


def _quality_veto_reasons(
    *, row: dict[str, Any], baseline: dict[str, Any] | None
) -> list[str]:
    """
    Determine quality-veto reasons for one matrix row.

    Args:
        row: Matrix row under evaluation.
        baseline: Baseline row used as comparator.

    Returns:
        Sorted veto reason list.

    """
    if not row["model_verification"]["valid"]:
        return ["model_verification_failed"]
    if baseline is None:
        return ["baseline_unavailable"]

    reasons: list[str] = []
    for metric_name in ("mean_cer", "mean_wer"):
        baseline_value = float(baseline.get(metric_name, 0.0))
        candidate_value = float(row.get(metric_name, 0.0))
        if baseline_value <= 0:
            if candidate_value > baseline_value:
                reasons.append(f"{metric_name}_exceeds_zero_baseline")
            continue
        if candidate_value > baseline_value * 1.05:
            regression_ratio = (candidate_value / baseline_value) - 1.0
            reasons.append(
                f"{metric_name}_regressed>{regression_ratio:.2%}"
            )

    fidelity_metrics = ("ae_recall", "eth_recall", "thorn_recall", "macron_recall")
    baseline_fidelity = baseline.get("old_english_fidelity", {})
    candidate_fidelity = row.get("old_english_fidelity", {})
    for metric_name in fidelity_metrics:
        baseline_value = float(baseline_fidelity.get(metric_name, 1.0))
        candidate_value = float(candidate_fidelity.get(metric_name, 1.0))
        if candidate_value < baseline_value - 0.02:
            reasons.append(
                f"{metric_name}_dropped>{(baseline_value - candidate_value):.4f}"
            )

    return sorted(reasons)


def _cohort_summary(*, row: dict[str, Any], fixtures: list[str]) -> dict[str, float]:
    """
    Build one cohort summary from fixture-level row data.

    Args:
        row: Matrix row with fixture-level metrics.
        fixtures: Fixture stems that belong to the cohort.

    Returns:
        Cohort summary payload.

    """
    fixture_results = row.get("fixture_results", {})
    latencies = [
        float(fixture_results[stem]["median_sec_per_page"])
        for stem in fixtures
        if stem in fixture_results and int(fixture_results[stem]["pages_measured"]) > 0
    ]
    p95_values = [
        float(fixture_results[stem]["p95_sec_per_page"])
        for stem in fixtures
        if stem in fixture_results and int(fixture_results[stem]["pages_measured"]) > 0
    ]
    return {
        "median_sec_per_page": statistics.fmean(latencies) if latencies else 0.0,
        "p95_sec_per_page": max(p95_values) if p95_values else 0.0,
    }


def main() -> int:  # noqa: PLR0915
    """
    Run the OCR model/ctx/cache matrix benchmark and write a report.

    Side Effects:
        Starts/stops local llama-server processes and writes a JSON report file.

    Returns:
        Zero on success.

    """
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    threshold_payload = _load_thresholds(repo_root)
    fixture_stems = tuple(args.fixtures)
    model_cases = _build_model_cases(args)

    run_controls = {
        "proxy_upstream_timeout_seconds": args.proxy_upstream_timeout_seconds,
        "proxy_upstream_max_retries": args.proxy_upstream_max_retries,
        "proxy_upstream_retry_backoff_seconds": (
            args.proxy_upstream_retry_backoff_seconds
        ),
        "olmocr_max_page_retries": args.olmocr_max_page_retries,
        "ocr_command_timeout_seconds": args.ocr_command_timeout_seconds,
        "fixture_timeout_seconds": args.fixture_timeout_seconds,
        "upstream_base_url": args.upstream_base_url,
        "snapshot_interval_seconds": args.snapshot_interval_seconds,
        "print_live_snapshots": args.print_live_snapshots,
        "show_llama_server_logs": args.show_llama_server_logs,
        "print_progress": args.print_progress,
        "vision_preprocess_timeout_seconds": args.vision_preprocess_timeout_seconds,
    }
    parsed_upstream = urlparse(args.upstream_base_url)
    upstream_host = parsed_upstream.hostname or "127.0.0.1"
    upstream_port = parsed_upstream.port or 8080

    model_verifications: dict[str, dict[str, Any]] = {
        case.name: _verify_model_case(repo_root=repo_root, case=case)
        for case in model_cases
    }

    matrix_results: list[dict[str, Any]] = []
    for vision_preprocess_mode in args.vision_preprocess_modes:
        for case in model_cases:
            verification = model_verifications[case.name]
            for ctx_value in args.ctx_values:
                for cache_type in args.cache_types:
                    row_base = {
                        "model_case_name": case.name,
                        "model_path": case.model_path,
                        "mmproj_path": case.mmproj_path,
                        "model_verification": verification,
                        "ctx": ctx_value,
                        "cache_type": cache_type,
                        "vision_preprocess_mode": vision_preprocess_mode,
                        "fixtures": list(fixture_stems),
                        "fixture_traits": {
                            stem: fixture_traits_for(stem) for stem in fixture_stems
                        },
                    }
                    if not verification["valid"]:
                        row = {
                            **row_base,
                            "profile": {},
                            "proxy_max_tokens_cap": args.proxy_max_tokens_cap,
                            "quality_pass": False,
                            "mean_sec_per_page": 0.0,
                            "median_sec_per_page": 0.0,
                            "p95_sec_per_page": 0.0,
                            "stddev_sec_per_page": 0.0,
                            "pages_per_minute": 0.0,
                            "retries_per_page": 0.0,
                            "mean_cer": 0.0,
                            "mean_wer": 0.0,
                            "mean_thorn_to_p_rate": 0.0,
                            "mean_macron_recall": 0.0,
                            "proxy_request_count": 0,
                            "proxy_prompt_tokens_total": 0,
                            "proxy_completion_tokens_total": 0,
                            "proxy_total_tokens_total": 0,
                            "proxy_completion_tokens_per_second": 0.0,
                            "pages_measured": 0,
                            "failed_pages": 0,
                            "failure_reasons": {
                                "model_verification_failed": len(fixture_stems)
                            },
                            "fixture_results": {},
                            "old_english_fidelity": {
                                "ae_recall": 1.0,
                                "ae_precision": 1.0,
                                "eth_recall": 1.0,
                                "eth_precision": 1.0,
                                "thorn_recall": 1.0,
                                "thorn_precision": 1.0,
                                "macron_recall": 1.0,
                            },
                            "trait_aggregates": {},
                        }
                        matrix_results.append(row)
                        continue

                    env_updates = {
                        "LLAMA_CTX": str(ctx_value),
                        "LLAMA_CACHE_TYPE_K": cache_type,
                        "LLAMA_CACHE_TYPE_V": cache_type,
                        "LLAMA_HOST": upstream_host,
                        "LLAMA_PORT": str(upstream_port),
                        "LLAMA_MODEL": case.model_path,
                        "LLAMA_MMPROJ": case.mmproj_path,
                    }
                    print(
                        "Running matrix case "
                        f"model={case.name} vision={vision_preprocess_mode} "
                        f"ctx={ctx_value} cache={cache_type} "
                        f"fixtures={','.join(fixture_stems)}"
                    )
                    with _temporary_env(env_updates):
                        base_profile = _build_base_profile()
                        result = _evaluate_candidate(
                            repo_root=repo_root,
                            profile=base_profile,
                            proxy_cap=args.proxy_max_tokens_cap,
                            fixture_stems=fixture_stems,
                            warmup_runs=args.warmup_runs,
                            measured_runs=args.measured_runs,
                            threshold_payload=threshold_payload,
                            proxy_override_length_to_stop=(
                                args.proxy_override_length_to_stop
                            ),
                            model_path=case.model_path,
                            vision_preprocess_mode=vision_preprocess_mode,
                            **run_controls,
                        )

                    row = {**row_base, **result}
                    row["trait_aggregates"] = _trait_aggregates_for_row(row)
                    matrix_results.append(row)

    primary_ctx_value = args.ctx_values[0]
    baseline = _select_baseline(
        rows=matrix_results,
        primary_ctx_value=primary_ctx_value,
    )
    for row in matrix_results:
        veto_reasons = _quality_veto_reasons(row=row, baseline=baseline)
        row["veto_reasons"] = veto_reasons
        row["vetoed"] = bool(veto_reasons)
        row["eligible"] = bool(
            row["model_verification"]["valid"]
            and not row["vetoed"]
            and row["quality_pass"]
            and int(row["failed_pages"]) == 0
        )

    eligible_rows = [row for row in matrix_results if row["eligible"]]
    if eligible_rows:
        best = min(
            eligible_rows,
            key=lambda item: (
                float(item.get("median_sec_per_page", item["mean_sec_per_page"])),
                float(item["p95_sec_per_page"]),
            ),
        )
    else:
        valid_rows = [
            row for row in matrix_results if row["model_verification"]["valid"]
        ]
        if valid_rows:
            best = min(
                valid_rows,
                key=lambda item: (
                    int(item["failed_pages"]),
                    float(item["mean_sec_per_page"]),
                ),
            )
        else:
            best = matrix_results[0]

    fixture_traits = {stem: fixture_traits_for(stem) for stem in fixture_stems}
    hard_fixtures = sorted(
        {
            stem
            for stem in fixture_stems
            if stem == "wright2"
            or "skew" in fixture_traits.get(stem, [])
            or "table" in fixture_traits.get(stem, [])
        }
    )
    easy_fixtures = sorted(
        stem for stem in fixture_stems if stem not in set(hard_fixtures)
    )

    baseline_easy = _cohort_summary(row=baseline or {}, fixtures=easy_fixtures)
    best_easy = _cohort_summary(row=best, fixtures=easy_fixtures)
    baseline_hard = _cohort_summary(row=baseline or {}, fixtures=hard_fixtures)
    best_hard = _cohort_summary(row=best, fixtures=hard_fixtures)
    easy_improvement = 0.0
    if baseline_easy["median_sec_per_page"] > 0:
        easy_improvement = (
            baseline_easy["median_sec_per_page"] - best_easy["median_sec_per_page"]
        ) / baseline_easy["median_sec_per_page"]
    hard_improvement = 0.0
    if baseline_hard["p95_sec_per_page"] > 0:
        hard_improvement = (
            baseline_hard["p95_sec_per_page"] - best_hard["p95_sec_per_page"]
        ) / baseline_hard["p95_sec_per_page"]
    acceptance = {
        "easy_median_improvement_target_met": (
            easy_improvement >= EASY_IMPROVEMENT_TARGET
        ),
        "hard_p95_improvement_target_met": (
            hard_improvement >= HARD_IMPROVEMENT_TARGET
        ),
        "best_has_no_quality_veto": not best["vetoed"],
        "best_has_no_unbounded_failures": int(best["failed_pages"]) == 0,
        "easy_median_improvement": easy_improvement,
        "hard_p95_improvement": hard_improvement,
    }

    _print_matrix_table(matrix_results)
    print(
        "\nBest case: "
        f"model={best['model_case_name']} "
        f"vision={best['vision_preprocess_mode']} "
        f"ctx={best['ctx']} cache={best['cache_type']} "
        f"mean={best['mean_sec_per_page']:.3f}s "
        f"median={best.get('median_sec_per_page', 0.0):.3f}s "
        f"p95={best['p95_sec_per_page']:.3f}s "
        f"pages/min={best['pages_per_minute']:.3f} "
        f"retries/page={best['retries_per_page']:.3f} "
        f"comp_tps={best['proxy_completion_tokens_per_second']:.3f} "
        f"CER={best['mean_cer']:.4f} WER={best['mean_wer']:.4f} "
        f"quality_pass={best['quality_pass']} vetoed={best['vetoed']}"
    )

    report = {
        "fixtures": list(fixture_stems),
        "fixture_traits": fixture_traits,
        "hard_fixtures": hard_fixtures,
        "easy_fixtures": easy_fixtures,
        "ctx_values": args.ctx_values,
        "cache_types": args.cache_types,
        "model_cases": [case.__dict__ for case in model_cases],
        "model_verification": model_verifications,
        "controls": run_controls,
        "proxy_max_tokens_cap": args.proxy_max_tokens_cap,
        "proxy_override_length_to_stop": args.proxy_override_length_to_stop,
        "vision_preprocess_modes": args.vision_preprocess_modes,
        "results": matrix_results,
        "baseline_reference": baseline,
        "best": best,
        "acceptance": acceptance,
        "cohorts": {
            "baseline_easy": baseline_easy,
            "best_easy": best_easy,
            "baseline_hard": baseline_hard,
            "best_hard": best_hard,
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote matrix report to {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
