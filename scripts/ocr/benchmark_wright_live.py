from __future__ import annotations

import argparse
import json
import os
import re
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import httpx

from tests.ocr_metrics import compute_ocr_metrics

LLAMA_READINESS_POLL_SECONDS = 0.25
LLAMA_STARTUP_TIMEOUT_SECONDS = 120.0
LLAMA_SHUTDOWN_TIMEOUT_SECONDS = 10.0
DEFAULT_FIXTURE_STEMS = ("wright1", "wright2", "wright3", "wright4", "wright5")
DEFAULT_PROXY_CAP = 1500
DEFAULT_STAGE4_PROXY_CAPS = (1500, 2000, 2500, 3000, 4000)
DEFAULT_PROXY_OVERRIDE_LENGTH_TO_STOP = False
RETRY_LOG_MARKER = "transient upstream"
MAX_READY_STATUS_CODE_EXCLUSIVE = 500
TOKEN_COUNTER_PRIORITIES = (
    "llamacpp:tokens_predicted_total",
    "llamacpp:tokens_decoded_total",
    "llama_tokens_predicted_total",
    "llama_tokens_decoded_total",
)
PROXY_STATS_PATTERN = re.compile(
    r"chat completion stats: request_s=(?P<request_s>[0-9.]+) "
    r"prompt_tokens=(?P<prompt_tokens>\d+) "
    r"completion_tokens=(?P<completion_tokens>\d+) "
    r"total_tokens=(?P<total_tokens>\d+) "
    r"completion_tps=(?P<completion_tps>[0-9.]+)"
)
QUEUE_REMAINING_PATTERN = re.compile(r"Queue remaining:\s+(?P<remaining>\d+)")
PROMETHEUS_SAMPLE_PATTERN = re.compile(
    r"^(?P<metric>[a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{[^}]*\})?\s+(?P<value>-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)$"
)


@dataclass(frozen=True)
class LlamaProfile:
    """One llama-server profile candidate used for live OCR benchmarking."""

    name: str
    threads: int
    threads_batch: int
    threads_http: int
    batch: int
    ubatch: int
    parallel: int
    image_min_tokens: int
    image_max_tokens: int
    cont_batching: str = "on"
    seed: int = 0

    def to_env(self) -> dict[str, str]:
        """Render Makefile-compatible environment variables for this profile."""
        return {
            "LLAMA_THREADS": str(self.threads),
            "LLAMA_THREADS_BATCH": str(self.threads_batch),
            "LLAMA_THREADS_HTTP": str(self.threads_http),
            "LLAMA_BATCH": str(self.batch),
            "LLAMA_UBATCH": str(self.ubatch),
            "LLAMA_PARALLEL": str(self.parallel),
            "LLAMA_IMAGE_MIN_TOKENS": str(self.image_min_tokens),
            "LLAMA_IMAGE_MAX_TOKENS": str(self.image_max_tokens),
            "LLAMA_CONT_BATCHING": self.cont_batching,
            "LLAMA_SEED": str(self.seed),
        }


@dataclass(frozen=True)
class RunDiagnostics:
    """Aggregated proxy diagnostics parsed from one OCR command output."""

    proxy_request_count: int
    proxy_prompt_tokens: int
    proxy_completion_tokens: int
    proxy_total_tokens: int
    proxy_request_elapsed_seconds: float


def _parse_proxy_stats(log_output: str) -> RunDiagnostics:
    """Parse proxy per-request token diagnostics from combined command logs."""
    request_count = 0
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    request_elapsed_seconds = 0.0
    for match in PROXY_STATS_PATTERN.finditer(log_output):
        request_count += 1
        prompt_tokens += int(match.group("prompt_tokens"))
        completion_tokens += int(match.group("completion_tokens"))
        total_tokens += int(match.group("total_tokens"))
        request_elapsed_seconds += float(match.group("request_s"))
    return RunDiagnostics(
        proxy_request_count=request_count,
        proxy_prompt_tokens=prompt_tokens,
        proxy_completion_tokens=completion_tokens,
        proxy_total_tokens=total_tokens,
        proxy_request_elapsed_seconds=request_elapsed_seconds,
    )


def _extract_prometheus_token_counters(metrics_text: str) -> dict[str, float]:
    """Extract token-like Prometheus counter samples from ``/metrics`` output."""
    counters: dict[str, float] = {}
    for raw_line in metrics_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = PROMETHEUS_SAMPLE_PATTERN.match(line)
        if not match:
            continue
        metric_name = match.group("metric")
        metric_name_lower = metric_name.lower()
        if "token" not in metric_name_lower:
            continue
        if "total" not in metric_name_lower:
            continue
        counters[metric_name] = float(match.group("value"))
    return counters


def _llama_host() -> str:
    """Return llama-server host from environment with a safe default."""
    return os.environ.get("LLAMA_HOST", "127.0.0.1")


def _llama_port() -> int:
    """Return llama-server port from environment with a safe default."""
    return int(os.environ.get("LLAMA_PORT", "8080"))


def _llama_base_url() -> str:
    """Build the base URL for the active llama-server process."""
    return f"http://{_llama_host()}:{_llama_port()}"


def _llama_healthcheck_url() -> str:
    """Build the llama-server healthcheck URL used by readiness probes."""
    return f"{_llama_base_url()}/v1/models"


def _llama_metrics_url() -> str:
    """Build the Prometheus metrics endpoint URL for llama-server."""
    return f"{_llama_base_url()}/metrics"


def _llama_slots_url() -> str:
    """Build the slots endpoint URL for llama-server."""
    return f"{_llama_base_url()}/slots"


def _try_extract_slot_token_sum(payload: Any) -> float:
    """Best-effort token counter fallback when only the ``/slots`` endpoint is open."""
    if isinstance(payload, dict):
        total = 0.0
        for key, value in payload.items():
            key_lower = key.lower()
            if isinstance(value, (int, float)) and "token" in key_lower:
                total += float(value)
                continue
            total += _try_extract_slot_token_sum(value)
        return total
    if isinstance(payload, list):
        return sum(_try_extract_slot_token_sum(item) for item in payload)
    return 0.0


def _sample_llama_token_counter() -> tuple[str, float] | None:
    """Read one token counter sample from llama-server metrics endpoints."""
    try:
        response = httpx.get(_llama_metrics_url(), timeout=1.0)
        if response.status_code < MAX_READY_STATUS_CODE_EXCLUSIVE:
            counters = _extract_prometheus_token_counters(response.text)
            for metric_name in TOKEN_COUNTER_PRIORITIES:
                if metric_name in counters:
                    return metric_name, counters[metric_name]
            if counters:
                selected_name = sorted(counters.keys())[0]
                return selected_name, counters[selected_name]
    except httpx.RequestError:
        pass

    try:
        response = httpx.get(_llama_slots_url(), timeout=1.0)
        if response.status_code < MAX_READY_STATUS_CODE_EXCLUSIVE:
            payload = response.json()
            token_sum = _try_extract_slot_token_sum(payload)
            if token_sum > 0:
                return "slots_token_sum", token_sum
    except (httpx.RequestError, ValueError):
        pass

    return None


def _is_llama_server_healthy() -> bool:
    try:
        response = httpx.get(_llama_healthcheck_url(), timeout=2.0)
    except httpx.RequestError:
        return False
    return response.status_code < MAX_READY_STATUS_CODE_EXCLUSIVE


def _start_llama_server(
    repo_root: Path, profile: LlamaProfile, *, show_llama_server_logs: bool
) -> subprocess.Popen[str]:
    env = dict(os.environ)
    env.update(profile.to_env())
    stdout_target = None if show_llama_server_logs else subprocess.DEVNULL
    stderr_target = None if show_llama_server_logs else subprocess.STDOUT
    process = subprocess.Popen(
        ["make", "llama-test"],
        cwd=repo_root,
        env=env,
        start_new_session=True,
        stdout=stdout_target,
        stderr=stderr_target,
        text=True,
    )

    deadline = time.monotonic() + LLAMA_STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            message = (
                "make llama-test exited before readiness check "
                f"(code {process.returncode})"
            )
            raise RuntimeError(message)
        if _is_llama_server_healthy():
            return process
        time.sleep(LLAMA_READINESS_POLL_SECONDS)

    _stop_llama_server(process)
    message = (
        "Timed out waiting for llama-server readiness at "
        f"{_llama_healthcheck_url()} after {LLAMA_STARTUP_TIMEOUT_SECONDS:.1f}s."
    )
    raise RuntimeError(message)


def _stop_llama_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    deadline = time.monotonic() + LLAMA_SHUTDOWN_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return
        time.sleep(LLAMA_READINESS_POLL_SECONDS)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def _load_thresholds(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "tests/fixtures/ocr/wright_quality_thresholds.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _threshold_for(stem: str, threshold_payload: dict[str, Any]) -> dict[str, float]:
    merged = dict(threshold_payload["defaults"])
    merged.update(threshold_payload["fixtures"].get(stem, {}))
    return {
        "max_cer": float(merged["max_cer"]),
        "max_wer": float(merged["max_wer"]),
        "min_thorn_recall": float(merged["min_thorn_recall"]),
        "max_thorn_to_p_rate": float(merged["max_thorn_to_p_rate"]),
        "min_macron_recall": float(merged["min_macron_recall"]),
    }


def _run_ocr_once(  # noqa: PLR0913, PLR0915
    *,
    repo_root: Path,
    fixture_stem: str,
    output_dir: Path,
    proxy_cap: int,
    proxy_override_length_to_stop: bool,
    model_path: str,
    proxy_upstream_timeout_seconds: float,
    proxy_upstream_max_retries: int,
    proxy_upstream_retry_backoff_seconds: float,
    olmocr_max_page_retries: int,
    ocr_command_timeout_seconds: float,
    upstream_base_url: str,
    snapshot_interval_seconds: float,
    print_live_snapshots: bool,
) -> tuple[float, int, RunDiagnostics, dict[str, float | int] | None, str | None]:
    input_pdf = repo_root / f"tests/fixtures/ocr/{fixture_stem}.pdf"
    expected_path = repo_root / f"tests/fixtures/ocr/{fixture_stem}.md"
    command = [
        sys.executable,
        "-m",
        "wyrdcraeft.main",
        "ocr",
        "old-english",
        "--input-pdf",
        str(input_pdf),
        "--output-dir",
        str(output_dir),
        "--upstream-base-url",
        upstream_base_url,
        "--olmocr-model",
        model_path,
        "--proxy-max-tokens-cap",
        str(proxy_cap),
        (
            "--proxy-override-length-to-stop"
            if proxy_override_length_to_stop
            else "--no-proxy-override-length-to-stop"
        ),
        "--proxy-upstream-timeout-seconds",
        str(proxy_upstream_timeout_seconds),
        "--proxy-upstream-max-retries",
        str(proxy_upstream_max_retries),
        "--proxy-upstream-retry-backoff-seconds",
        str(proxy_upstream_retry_backoff_seconds),
        "--olmocr-max-page-retries",
        str(olmocr_max_page_retries),
    ]

    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log_buffer:
        start = time.monotonic()
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=log_buffer,
            stderr=subprocess.STDOUT,
            text=True,
        )
        read_offset = 0
        retry_events_seen = 0
        previous_counter_name: str | None = None
        previous_counter_value: float | None = None
        previous_counter_time: float | None = None
        queue_remaining_latest: int | None = None
        last_snapshot_time = 0.0
        timed_out = False

        while process.poll() is None:
            time.sleep(0.2)
            elapsed_seconds = time.monotonic() - start
            if (
                ocr_command_timeout_seconds > 0
                and elapsed_seconds >= ocr_command_timeout_seconds
            ):
                process.kill()
                timed_out = True
                break

            log_buffer.flush()
            log_buffer.seek(read_offset)
            new_log_chunk = log_buffer.read()
            read_offset = log_buffer.tell()
            retry_events_seen += new_log_chunk.lower().count(RETRY_LOG_MARKER)
            queue_matches = list(QUEUE_REMAINING_PATTERN.finditer(new_log_chunk))
            if queue_matches:
                queue_remaining_latest = int(queue_matches[-1].group("remaining"))

            if (
                print_live_snapshots
                and snapshot_interval_seconds > 0
                and elapsed_seconds - last_snapshot_time >= snapshot_interval_seconds
            ):
                last_snapshot_time = elapsed_seconds
                counter_sample = _sample_llama_token_counter()
                counter_tps = 0.0
                counter_name = "n/a"
                if counter_sample is not None:
                    counter_name, counter_value = counter_sample
                    if (
                        previous_counter_name == counter_name
                        and previous_counter_value is not None
                        and previous_counter_time is not None
                    ):
                        delta_value = counter_value - previous_counter_value
                        delta_time = elapsed_seconds - previous_counter_time
                        if delta_value >= 0 and delta_time > 0:
                            counter_tps = delta_value / delta_time
                    previous_counter_name = counter_name
                    previous_counter_value = counter_value
                    previous_counter_time = elapsed_seconds

                print(
                    "Live snapshot "
                    f"fixture={fixture_stem} elapsed={elapsed_seconds:.1f}s "
                    f"retry_events_seen={retry_events_seen} "
                    f"queue_remaining={queue_remaining_latest} "
                    f"llama_counter={counter_name} "
                    f"counter_tps={counter_tps:.2f}"
                )

        return_code = process.wait()
        elapsed_seconds = time.monotonic() - start
        log_buffer.seek(0)
        combined_output = log_buffer.read()
        retry_events = combined_output.lower().count(RETRY_LOG_MARKER)
        diagnostics = _parse_proxy_stats(combined_output)

        if timed_out:
            message = (
                f"OCR run timed out for {fixture_stem} after "
                f"{ocr_command_timeout_seconds:.1f}s.\n"
                f"Command: {' '.join(command)}\n"
                f"Output:\n{combined_output[-4000:]}"
            )
            return elapsed_seconds, retry_events, diagnostics, None, message

        if return_code != 0:
            message = (
                f"OCR run failed for {fixture_stem} with code {return_code}.\n"
                f"Command: {' '.join(command)}\n"
                f"Output:\n{combined_output[-4000:]}"
            )
            return elapsed_seconds, retry_events, diagnostics, None, message

        observed_path = output_dir / "02_raw.txt"
        observed_text = observed_path.read_text(encoding="utf-8")
        expected_text = expected_path.read_text(encoding="utf-8")
        metrics = compute_ocr_metrics(
            expected_text=expected_text,
            observed_text=observed_text,
        )
        return elapsed_seconds, retry_events, diagnostics, metrics, None


def _quality_passes(
    fixture_stem: str,
    metrics: dict[str, float | int],
    threshold_payload: dict[str, Any],
) -> bool:
    thresholds = _threshold_for(fixture_stem, threshold_payload)
    thorn_recall = float(metrics["thorn_preserved"]) / max(
        int(metrics["thorn_expected"]),
        1,
    )
    return bool(
        float(metrics["cer"]) <= thresholds["max_cer"]
        and float(metrics["wer"]) <= thresholds["max_wer"]
        and thorn_recall >= thresholds["min_thorn_recall"]
        and float(metrics["thorn_to_p_rate"]) <= thresholds["max_thorn_to_p_rate"]
        and float(metrics["macron_recall"]) >= thresholds["min_macron_recall"]
    )


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = int(0.95 * (len(ordered) - 1))
    return ordered[index]


def _evaluate_candidate(  # noqa: PLR0913, PLR0915
    *,
    repo_root: Path,
    profile: LlamaProfile,
    proxy_cap: int,
    fixture_stems: tuple[str, ...],
    warmup_runs: int,
    measured_runs: int,
    threshold_payload: dict[str, Any],
    proxy_override_length_to_stop: bool,
    model_path: str,
    proxy_upstream_timeout_seconds: float,
    proxy_upstream_max_retries: int,
    proxy_upstream_retry_backoff_seconds: float,
    olmocr_max_page_retries: int,
    ocr_command_timeout_seconds: float,
    upstream_base_url: str,
    snapshot_interval_seconds: float,
    print_live_snapshots: bool,
    show_llama_server_logs: bool,
    print_progress: bool,
) -> dict[str, Any]:
    process = _start_llama_server(
        repo_root,
        profile,
        show_llama_server_logs=show_llama_server_logs,
    )
    latencies: list[float] = []
    retry_events_total = 0
    proxy_request_count_total = 0
    proxy_prompt_tokens_total = 0
    proxy_completion_tokens_total = 0
    proxy_total_tokens_total = 0
    proxy_request_elapsed_seconds_total = 0.0
    pages_measured = 0
    failed_pages = 0
    quality_ok = True
    cer_values: list[float] = []
    wer_values: list[float] = []
    thorn_to_p_values: list[float] = []
    macron_recall_values: list[float] = []

    try:
        with tempfile.TemporaryDirectory(prefix=f"ocr-bench-{profile.name}-") as tmp:
            temp_root = Path(tmp)
            total_runs = warmup_runs + measured_runs
            for run_index in range(total_runs):
                is_warmup = run_index < warmup_runs
                for stem in fixture_stems:
                    output_dir = temp_root / f"run_{run_index}_{stem}"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    (
                        elapsed_seconds,
                        retry_events,
                        diagnostics,
                        metrics,
                        run_error,
                    ) = _run_ocr_once(
                        repo_root=repo_root,
                        fixture_stem=stem,
                        output_dir=output_dir,
                        proxy_cap=proxy_cap,
                        proxy_override_length_to_stop=proxy_override_length_to_stop,
                        model_path=model_path,
                        proxy_upstream_timeout_seconds=proxy_upstream_timeout_seconds,
                        proxy_upstream_max_retries=proxy_upstream_max_retries,
                        proxy_upstream_retry_backoff_seconds=(
                            proxy_upstream_retry_backoff_seconds
                        ),
                        olmocr_max_page_retries=olmocr_max_page_retries,
                        ocr_command_timeout_seconds=ocr_command_timeout_seconds,
                        upstream_base_url=upstream_base_url,
                        snapshot_interval_seconds=snapshot_interval_seconds,
                        print_live_snapshots=print_live_snapshots,
                    )
                    if is_warmup:
                        continue
                    pages_measured += 1
                    latencies.append(elapsed_seconds)
                    retry_events_total += retry_events
                    proxy_request_count_total += diagnostics.proxy_request_count
                    proxy_prompt_tokens_total += diagnostics.proxy_prompt_tokens
                    proxy_completion_tokens_total += diagnostics.proxy_completion_tokens
                    proxy_total_tokens_total += diagnostics.proxy_total_tokens
                    proxy_request_elapsed_seconds_total += (
                        diagnostics.proxy_request_elapsed_seconds
                    )
                    if print_progress:
                        completion_tps = (
                            diagnostics.proxy_completion_tokens
                            / diagnostics.proxy_request_elapsed_seconds
                            if diagnostics.proxy_request_elapsed_seconds > 0
                            else 0.0
                        )
                        print(
                            "Progress "
                            f"profile={profile.name} cap={proxy_cap} "
                            f"run={run_index - warmup_runs + 1}/{measured_runs} "
                            f"fixture={stem} elapsed={elapsed_seconds:.2f}s "
                            f"retries={retry_events} "
                            f"proxy_requests={diagnostics.proxy_request_count} "
                            f"completion_tokens={diagnostics.proxy_completion_tokens} "
                            f"completion_tps={completion_tps:.2f}"
                        )
                    if metrics is None:
                        failed_pages += 1
                        quality_ok = False
                        if run_error:
                            error_excerpt = "\n".join(run_error.splitlines()[:10])
                            print(
                                f"Candidate {profile.name} cap={proxy_cap} "
                                f"failed for {stem}:\n{error_excerpt}"
                            )
                        continue
                    cer_values.append(float(metrics["cer"]))
                    wer_values.append(float(metrics["wer"]))
                    thorn_to_p_values.append(float(metrics["thorn_to_p_rate"]))
                    macron_recall_values.append(float(metrics["macron_recall"]))
                    if not _quality_passes(stem, metrics, threshold_payload):
                        quality_ok = False
    finally:
        _stop_llama_server(process)

    mean_sec_per_page = _mean(latencies)
    retries_per_page = retry_events_total / max(pages_measured, 1)
    stddev_sec_per_page = (
        statistics.pstdev(latencies) if len(latencies) > 1 else 0.0
    )
    proxy_completion_tokens_per_second = (
        proxy_completion_tokens_total / proxy_request_elapsed_seconds_total
        if proxy_request_elapsed_seconds_total > 0
        else 0.0
    )
    return {
        "profile": asdict(profile),
        "proxy_max_tokens_cap": proxy_cap,
        "quality_pass": quality_ok,
        "mean_sec_per_page": mean_sec_per_page,
        "p95_sec_per_page": _p95(latencies),
        "stddev_sec_per_page": stddev_sec_per_page,
        "pages_per_minute": 60.0 / mean_sec_per_page if mean_sec_per_page > 0 else 0.0,
        "retries_per_page": retries_per_page,
        "mean_cer": _mean(cer_values),
        "mean_wer": _mean(wer_values),
        "mean_thorn_to_p_rate": _mean(thorn_to_p_values),
        "mean_macron_recall": _mean(macron_recall_values),
        "proxy_request_count": proxy_request_count_total,
        "proxy_prompt_tokens_total": proxy_prompt_tokens_total,
        "proxy_completion_tokens_total": proxy_completion_tokens_total,
        "proxy_total_tokens_total": proxy_total_tokens_total,
        "proxy_completion_tokens_per_second": proxy_completion_tokens_per_second,
        "pages_measured": pages_measured,
        "failed_pages": failed_pages,
    }


def _select_fastest(candidate_results: list[dict[str, Any]]) -> dict[str, Any]:
    passing = [item for item in candidate_results if item["quality_pass"]]
    pool = passing or candidate_results
    return min(
        pool,
        key=lambda item: (
            int(item["failed_pages"]),
            float(item["mean_sec_per_page"]),
        ),
    )


def _print_summary(title: str, result: dict[str, Any]) -> None:
    summary = (
        f"{title}: profile={result['profile']['name']} "
        f"cap={result['proxy_max_tokens_cap']} "
        f"quality_pass={result['quality_pass']} "
        f"failed_pages={result['failed_pages']} "
        f"mean={result['mean_sec_per_page']:.3f}s "
        f"p95={result['p95_sec_per_page']:.3f}s "
        f"pages/min={result['pages_per_minute']:.2f} "
        f"retries/page={result['retries_per_page']:.2f} "
        f"proxy_comp_tps={result['proxy_completion_tokens_per_second']:.2f} "
        f"CER={result['mean_cer']:.4f} "
        f"WER={result['mean_wer']:.4f} "
        f"thorn_to_p={result['mean_thorn_to_p_rate']:.4f} "
        f"macron_recall={result['mean_macron_recall']:.4f}"
    )
    print(summary)


def _build_base_profile() -> LlamaProfile:
    default_threads = int(os.environ.get("LLAMA_THREADS", str(os.cpu_count() or 8)))
    return LlamaProfile(
        name="baseline",
        threads=default_threads,
        threads_batch=default_threads,
        threads_http=int(os.environ.get("LLAMA_THREADS_HTTP", "2")),
        batch=int(os.environ.get("LLAMA_BATCH", "1024")),
        ubatch=int(os.environ.get("LLAMA_UBATCH", "512")),
        parallel=int(os.environ.get("LLAMA_PARALLEL", "1")),
        image_min_tokens=int(os.environ.get("LLAMA_IMAGE_MIN_TOKENS", "512")),
        image_max_tokens=int(os.environ.get("LLAMA_IMAGE_MAX_TOKENS", "2048")),
    )


def main() -> int:  # noqa: PLR0915
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark live OCR throughput/latency and quality on Wright fixtures "
            "using staged llama.cpp tuning sweeps."
        )
    )
    parser.add_argument(
        "--fixtures",
        nargs="+",
        default=list(DEFAULT_FIXTURE_STEMS),
        help="Fixture stems under tests/fixtures/ocr (default: wright1..wright5).",
    )
    parser.add_argument(
        "--warmup-runs",
        type=int,
        default=1,
        help="Warmup runs excluded from metrics (default: 1).",
    )
    parser.add_argument(
        "--measured-runs",
        type=int,
        default=3,
        help="Measured runs per fixture (default: 3).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("data/ocr/wright_live_benchmark_report.json"),
        help="Path for JSON report output.",
    )
    parser.add_argument(
        "--model-path",
        default="./data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf",
        help="Model path passed to the OCR pipeline.",
    )
    parser.add_argument(
        "--proxy-caps",
        nargs="+",
        type=int,
        default=list(DEFAULT_STAGE4_PROXY_CAPS),
        help=(
            "Stage-4 proxy max-token cap candidates "
            "(default: 1500 2000 2500 3000 4000)."
        ),
    )
    parser.add_argument(
        "--proxy-override-length-to-stop",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_PROXY_OVERRIDE_LENGTH_TO_STOP,
        help=(
            "Pass --proxy-override-length-to-stop through the OCR CLI "
            "(default: disabled for quality-safe benchmarking)."
        ),
    )
    parser.add_argument(
        "--proxy-upstream-timeout-seconds",
        type=float,
        default=120.0,
        help="Managed proxy upstream timeout forwarded to OCR CLI.",
    )
    parser.add_argument(
        "--proxy-upstream-max-retries",
        type=int,
        default=2,
        help="Managed proxy retry budget forwarded to OCR CLI.",
    )
    parser.add_argument(
        "--proxy-upstream-retry-backoff-seconds",
        type=float,
        default=0.5,
        help="Managed proxy retry backoff forwarded to OCR CLI.",
    )
    parser.add_argument(
        "--olmocr-max-page-retries",
        type=int,
        default=5,
        help="olmocr per-page retry budget forwarded to OCR CLI.",
    )
    parser.add_argument(
        "--ocr-command-timeout-seconds",
        type=float,
        default=0.0,
        help="Optional timeout for each OCR command invocation (0 disables timeout).",
    )
    parser.add_argument(
        "--upstream-base-url",
        default="http://127.0.0.1:8080/v1",
        help="Upstream llama.cpp OpenAI-compatible base URL used by managed proxy.",
    )
    parser.add_argument(
        "--print-progress",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Emit one progress line per measured page run.",
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
        help="Expose raw llama-server logs (includes per-request eval tokens/sec).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Run a reduced sweep (fewer candidates per stage) "
            "for faster calibration."
        ),
    )
    parser.add_argument(
        "--ultra-quick",
        action="store_true",
        help=(
            "Run the smallest sweep (one candidate per stage and first cap only)."
        ),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    fixture_stems = tuple(args.fixtures)
    threshold_payload = _load_thresholds(repo_root)
    base_profile = _build_base_profile()
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

    print("Running baseline candidate...")
    baseline_result = _evaluate_candidate(
        repo_root=repo_root,
        profile=base_profile,
        proxy_cap=DEFAULT_PROXY_CAP,
        fixture_stems=fixture_stems,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        threshold_payload=threshold_payload,
        proxy_override_length_to_stop=args.proxy_override_length_to_stop,
        model_path=args.model_path,
        **run_controls,
    )
    _print_summary("Baseline", baseline_result)

    if args.ultra_quick:
        stage1_profiles = [
            replace(
                base_profile,
                name="stage1_img_512_2048",
                image_min_tokens=512,
                image_max_tokens=2048,
            ),
        ]
    elif args.quick:
        stage1_profiles = [
            replace(
                base_profile,
                name="stage1_img_512_2048",
                image_min_tokens=512,
                image_max_tokens=2048,
            ),
            replace(
                base_profile,
                name="stage1_img_384_1536",
                image_min_tokens=384,
                image_max_tokens=1536,
            ),
        ]
    else:
        stage1_profiles = [
            replace(
                base_profile,
                name="stage1_img_512_2048",
                image_min_tokens=512,
                image_max_tokens=2048,
            ),
            replace(
                base_profile,
                name="stage1_img_384_1536",
                image_min_tokens=384,
                image_max_tokens=1536,
            ),
            replace(
                base_profile,
                name="stage1_img_256_1024",
                image_min_tokens=256,
                image_max_tokens=1024,
            ),
        ]
    stage1_results = [
        _evaluate_candidate(
            repo_root=repo_root,
            profile=profile,
            proxy_cap=DEFAULT_PROXY_CAP,
            fixture_stems=fixture_stems,
            warmup_runs=args.warmup_runs,
            measured_runs=args.measured_runs,
            threshold_payload=threshold_payload,
            proxy_override_length_to_stop=args.proxy_override_length_to_stop,
            model_path=args.model_path,
            **run_controls,
        )
        for profile in stage1_profiles
    ]
    stage1_best = _select_fastest(stage1_results)
    _print_summary("Stage 1 best", stage1_best)

    stage2_base = LlamaProfile(**stage1_best["profile"])
    if args.ultra_quick:
        stage2_profiles = [
            replace(stage2_base, name="stage2_batch_1024_512", batch=1024, ubatch=512),
        ]
    elif args.quick:
        stage2_profiles = [
            replace(stage2_base, name="stage2_batch_1024_512", batch=1024, ubatch=512),
            replace(stage2_base, name="stage2_batch_1280_640", batch=1280, ubatch=640),
        ]
    else:
        stage2_profiles = [
            replace(stage2_base, name="stage2_batch_1024_512", batch=1024, ubatch=512),
            replace(stage2_base, name="stage2_batch_1280_640", batch=1280, ubatch=640),
            replace(stage2_base, name="stage2_batch_1536_768", batch=1536, ubatch=768),
        ]
    stage2_results = [
        _evaluate_candidate(
            repo_root=repo_root,
            profile=profile,
            proxy_cap=DEFAULT_PROXY_CAP,
            fixture_stems=fixture_stems,
            warmup_runs=args.warmup_runs,
            measured_runs=args.measured_runs,
            threshold_payload=threshold_payload,
            proxy_override_length_to_stop=args.proxy_override_length_to_stop,
            model_path=args.model_path,
            **run_controls,
        )
        for profile in stage2_profiles
    ]
    stage2_best = _select_fastest(stage2_results)
    _print_summary("Stage 2 best", stage2_best)

    stage3_base = LlamaProfile(**stage2_best["profile"])
    if args.ultra_quick:
        stage3_profiles = [
            replace(
                stage3_base,
                name="stage3_threads_6_http_1",
                threads=6,
                threads_batch=6,
                threads_http=1,
            ),
        ]
    elif args.quick:
        stage3_profiles = [
            replace(
                stage3_base,
                name="stage3_threads_6_http_1",
                threads=6,
                threads_batch=6,
                threads_http=1,
            ),
            replace(
                stage3_base,
                name="stage3_threads_8_http_1",
                threads=8,
                threads_batch=8,
                threads_http=1,
            ),
        ]
    else:
        stage3_profiles = [
            replace(
                stage3_base,
                name="stage3_threads_6_http_1",
                threads=6,
                threads_batch=6,
                threads_http=1,
            ),
            replace(
                stage3_base,
                name="stage3_threads_8_http_1",
                threads=8,
                threads_batch=8,
                threads_http=1,
            ),
            replace(
                stage3_base,
                name="stage3_threads_10_http_2",
                threads=10,
                threads_batch=10,
                threads_http=2,
            ),
        ]
    stage3_results = [
        _evaluate_candidate(
            repo_root=repo_root,
            profile=profile,
            proxy_cap=DEFAULT_PROXY_CAP,
            fixture_stems=fixture_stems,
            warmup_runs=args.warmup_runs,
            measured_runs=args.measured_runs,
            threshold_payload=threshold_payload,
            proxy_override_length_to_stop=args.proxy_override_length_to_stop,
            model_path=args.model_path,
            **run_controls,
        )
        for profile in stage3_profiles
    ]
    stage3_best = _select_fastest(stage3_results)
    _print_summary("Stage 3 best", stage3_best)

    stage4_profile = LlamaProfile(**stage3_best["profile"])
    if args.ultra_quick:
        stage4_caps = (int(args.proxy_caps[0]),)
    else:
        stage4_caps = tuple(args.proxy_caps)
    stage4_results = [
        _evaluate_candidate(
            repo_root=repo_root,
            profile=stage4_profile,
            proxy_cap=proxy_cap,
            fixture_stems=fixture_stems,
            warmup_runs=args.warmup_runs,
            measured_runs=args.measured_runs,
            threshold_payload=threshold_payload,
            proxy_override_length_to_stop=args.proxy_override_length_to_stop,
            model_path=args.model_path,
            **run_controls,
        )
        for proxy_cap in stage4_caps
    ]
    final_best = _select_fastest(stage4_results)
    _print_summary("Final best", final_best)

    report = {
        "baseline": baseline_result,
        "stage1": {"results": stage1_results, "best": stage1_best},
        "stage2": {"results": stage2_results, "best": stage2_best},
        "stage3": {"results": stage3_results, "best": stage3_best},
        "stage4": {"results": stage4_results, "best": final_best},
        "recommended_env": {
            **LlamaProfile(**final_best["profile"]).to_env(),
            "WYRDCRAEFT_OCR_PROXY_MAX_TOKENS_CAP": str(
                final_best["proxy_max_tokens_cap"]
            ),
            "WYRDCRAEFT_OCR_PROXY_OVERRIDE_LENGTH_TO_STOP": str(
                args.proxy_override_length_to_stop
            ).lower(),
        },
        "before_after_summary": {
            "before_mean_sec_per_page": baseline_result["mean_sec_per_page"],
            "after_mean_sec_per_page": final_best["mean_sec_per_page"],
            "before_p95_sec_per_page": baseline_result["p95_sec_per_page"],
            "after_p95_sec_per_page": final_best["p95_sec_per_page"],
            "before_pages_per_minute": baseline_result["pages_per_minute"],
            "after_pages_per_minute": final_best["pages_per_minute"],
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote benchmark report to {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
