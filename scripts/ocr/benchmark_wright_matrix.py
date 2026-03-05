from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.ocr.benchmark_wright_live import (
    LlamaProfile,
    _build_base_profile,
    _evaluate_candidate,
    _load_thresholds,
)


def _parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments for focused OCR parameter matrix benchmarking.

    Returns:
        Parsed CLI namespace.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Run focused OCR matrix benchmarks over LLAMA_CTX and KV-cache "
            "quantization settings with live retry/token diagnostics."
        )
    )
    parser.add_argument(
        "--fixtures",
        nargs="+",
        default=["wright1", "wright3", "wright4"],
        help=(
            "Fixture stems under tests/fixtures/ocr "
            "(default: wright1 wright3 wright4)."
        ),
    )
    parser.add_argument(
        "--ctx-values",
        nargs="+",
        type=int,
        default=[10240, 8192],
        help="LLAMA_CTX values to benchmark.",
    )
    parser.add_argument(
        "--cache-types",
        nargs="+",
        default=["q8_0", "q5_0"],
        help="LLAMA_CACHE_TYPE_K/LLAMA_CACHE_TYPE_V quantization values to benchmark.",
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
        default=1,
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
        default=45.0,
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
        help="Timeout per OCR command invocation.",
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
        "--model-path",
        default="./data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf",
        help="Model path passed to the OCR pipeline.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("data/ocr/wright_matrix_benchmark_report.json"),
        help="Path for JSON report output.",
    )
    return parser.parse_args()


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
        "ctx",
        "cache",
        "fixtures",
        "mean_s",
        "p95_s",
        "std_s",
        "pages_min",
        "retries_page",
        "CER",
        "WER",
        "thorn_p",
        "macron",
        "comp_tps",
        "quality",
        "failed",
    )
    print("\nMatrix summary")
    print("\t".join(headers))
    for row in results:
        print(
            "\t".join(
                [
                    str(row["ctx"]),
                    row["cache_type"],
                    ",".join(row["fixtures"]),
                    f"{row['mean_sec_per_page']:.3f}",
                    f"{row['p95_sec_per_page']:.3f}",
                    f"{row['stddev_sec_per_page']:.3f}",
                    f"{row['pages_per_minute']:.3f}",
                    f"{row['retries_per_page']:.3f}",
                    f"{row['mean_cer']:.4f}",
                    f"{row['mean_wer']:.4f}",
                    f"{row['mean_thorn_to_p_rate']:.4f}",
                    f"{row['mean_macron_recall']:.4f}",
                    f"{row['proxy_completion_tokens_per_second']:.3f}",
                    str(row["quality_pass"]).lower(),
                    str(row["failed_pages"]),
                ]
            )
        )


def main() -> int:
    """
    Run the LLAMA_CTX x cache-type matrix benchmark and write a report.

    Side Effects:
        Starts/stops local llama-server processes and writes a JSON report file.

    Returns:
        Zero on success.

    """
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    threshold_payload = _load_thresholds(repo_root)
    fixture_stems = tuple(args.fixtures)

    run_controls = {
        "proxy_upstream_timeout_seconds": args.proxy_upstream_timeout_seconds,
        "proxy_upstream_max_retries": args.proxy_upstream_max_retries,
        "proxy_upstream_retry_backoff_seconds": (
            args.proxy_upstream_retry_backoff_seconds
        ),
        "olmocr_max_page_retries": args.olmocr_max_page_retries,
        "ocr_command_timeout_seconds": args.ocr_command_timeout_seconds,
        "upstream_base_url": args.upstream_base_url,
        "snapshot_interval_seconds": args.snapshot_interval_seconds,
        "print_live_snapshots": args.print_live_snapshots,
        "show_llama_server_logs": args.show_llama_server_logs,
        "print_progress": args.print_progress,
    }
    parsed_upstream = urlparse(args.upstream_base_url)
    upstream_host = parsed_upstream.hostname or "127.0.0.1"
    upstream_port = parsed_upstream.port or 8080

    matrix_results: list[dict[str, Any]] = []
    for ctx_value in args.ctx_values:
        for cache_type in args.cache_types:
            env_updates = {
                "LLAMA_CTX": str(ctx_value),
                "LLAMA_CACHE_TYPE_K": cache_type,
                "LLAMA_CACHE_TYPE_V": cache_type,
                "LLAMA_HOST": upstream_host,
                "LLAMA_PORT": str(upstream_port),
            }
            print(
                "Running matrix case "
                f"ctx={ctx_value} cache={cache_type} fixtures={','.join(fixture_stems)}"
            )
            with _temporary_env(env_updates):
                base_profile: LlamaProfile = _build_base_profile()
                result = _evaluate_candidate(
                    repo_root=repo_root,
                    profile=base_profile,
                    proxy_cap=args.proxy_max_tokens_cap,
                    fixture_stems=fixture_stems,
                    warmup_runs=args.warmup_runs,
                    measured_runs=args.measured_runs,
                    threshold_payload=threshold_payload,
                    proxy_override_length_to_stop=args.proxy_override_length_to_stop,
                    model_path=args.model_path,
                    **run_controls,
                )

            row = {
                "ctx": ctx_value,
                "cache_type": cache_type,
                "fixtures": list(fixture_stems),
                **result,
            }
            matrix_results.append(row)

    matrix_results_sorted = sorted(
        matrix_results,
        key=lambda item: (
            int(item["failed_pages"]),
            0 if bool(item["quality_pass"]) else 1,
            float(item["mean_sec_per_page"]),
        ),
    )
    best = matrix_results_sorted[0]

    _print_matrix_table(matrix_results)
    print(
        "\nBest case: "
        f"ctx={best['ctx']} cache={best['cache_type']} "
        f"mean={best['mean_sec_per_page']:.3f}s "
        f"p95={best['p95_sec_per_page']:.3f}s "
        f"pages/min={best['pages_per_minute']:.3f} "
        f"retries/page={best['retries_per_page']:.3f} "
        f"comp_tps={best['proxy_completion_tokens_per_second']:.3f} "
        f"CER={best['mean_cer']:.4f} WER={best['mean_wer']:.4f} "
        f"thorn_to_p={best['mean_thorn_to_p_rate']:.4f} "
        f"macron={best['mean_macron_recall']:.4f} "
        f"quality_pass={best['quality_pass']}"
    )

    report = {
        "fixtures": list(fixture_stems),
        "ctx_values": args.ctx_values,
        "cache_types": args.cache_types,
        "model_path": args.model_path,
        "controls": run_controls,
        "proxy_max_tokens_cap": args.proxy_max_tokens_cap,
        "proxy_override_length_to_stop": args.proxy_override_length_to_stop,
        "results": matrix_results,
        "best": best,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote matrix report to {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
