"""
Test configuration and fixtures for the ai-coding project.

This file contains shared fixtures and configuration that can be used across
all test files in the project.
"""

import os
import signal
import subprocess
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from click.testing import CliRunner
from rich.console import Console

LLAMA_HEALTHCHECK_URL = "http://127.0.0.1:8080/v1/models"
LLAMA_READINESS_POLL_SECONDS = 0.25
LLAMA_STARTUP_TIMEOUT_SECONDS = 120.0
LLAMA_SHUTDOWN_TIMEOUT_SECONDS = 10.0
MAX_READY_STATUS_CODE_EXCLUSIVE = 500
DEFAULT_LLAMA_MODEL_PATH = Path("data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf")
DEFAULT_LLAMA_MMPROJ_PATH = Path("data/models/mmproj-olmOCR-2-7B-1025-vision.gguf")


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_console():
    """Create a mock console for testing."""
    return Mock(spec=Console)


@pytest.fixture
def mock_settings():
    """Create a mock settings object for testing."""
    mock = Mock()
    mock.model_dump.return_value = {
        "app_name": "wyrdcraeft",
        "app_version": "0.1.0",
        "default_output_format": "table",
        "enable_colors": True,
        "quiet_mode": False,
        "log_level": "INFO",
        "log_file": None,
        "llm_model_id": "qwen2.5:14b-instruct",
        "llm_provider": "ollama",
        "llm_temperature": 0.0,
        "llm_max_tokens": 4096,
        "llm_timeout_s": 120,
    }
    mock.llm_config = Mock()
    mock.llm_config.model_id = "qwen2.5:14b-instruct"
    mock.llm_config.provider = "ollama"
    mock.llm_config.temperature = 0.0
    mock.llm_config.max_tokens = 4096
    mock.llm_config.timeout_s = 120
    return mock


@pytest.fixture
def cli_context(mock_settings, mock_console):
    """Create a mock CLI context for testing."""
    return {
        "settings": mock_settings,
        "utils": Mock(),
        "console": mock_console,
        "output": "table",
    }


def pytest_addoption(parser):
    """Add custom command line options to pytest."""
    parser.addoption(
        "--run-llm",
        action="store_true",
        default=False,
        help="run tests that require LLM",
    )
    parser.addoption(
        "--run-ocr-integration",
        action="store_true",
        default=False,
        help="run live OCR integration tests that need local llama-server",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip expensive integration tests by default."""
    run_llm = bool(config.getoption("--run-llm"))
    run_ocr_integration = bool(config.getoption("--run-ocr-integration"))
    skip_llm = pytest.mark.skip(reason="need --run-llm option to run")
    skip_ocr_integration = pytest.mark.skip(
        reason="need --run-ocr-integration option to run"
    )
    for item in items:
        if "llm" in item.keywords and not run_llm:
            item.add_marker(skip_llm)
        if "ocr_integration" in item.keywords and not run_ocr_integration:
            item.add_marker(skip_ocr_integration)


def _is_llama_server_healthy() -> bool:
    """Return true when the local llama-server health endpoint is responsive."""
    try:
        response = httpx.get(LLAMA_HEALTHCHECK_URL, timeout=2.0)
    except httpx.RequestError:
        return False
    return response.status_code < MAX_READY_STATUS_CODE_EXCLUSIVE


def _stop_process_group(process: subprocess.Popen[str]) -> None:
    """Stop one process group with SIGTERM and SIGKILL fallback."""
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


def _resolve_llama_path(env_name: str, fallback: Path) -> Path:
    """
    Resolve one filesystem path from environment variable or fallback value.

    Args:
        env_name: Environment variable name to inspect.
        fallback: Default relative path when env variable is not set.

    Returns:
        Resolved absolute path.

    """
    configured = os.environ.get(env_name)
    if configured:
        return Path(configured).expanduser().resolve()
    return fallback.resolve()


@pytest.fixture(scope="session")
def ensure_llama_server() -> Generator[None]:
    """
    Ensure a local llama-server is running for live OCR integration tests.

    Side Effects:
        Starts and optionally stops a ``make llama-test`` subprocess when needed.

    Raises:
        pytest.skip: If required model artifacts are missing or startup fails.

    """
    if _is_llama_server_healthy():
        yield
        return

    model_path = _resolve_llama_path("LLAMA_MODEL", DEFAULT_LLAMA_MODEL_PATH)
    mmproj_path = _resolve_llama_path("LLAMA_MMPROJ", DEFAULT_LLAMA_MMPROJ_PATH)
    missing_paths = [
        str(path)
        for path in (model_path, mmproj_path)
        if not path.exists()
    ]
    if missing_paths:
        pytest.skip(
            "llama-server artifacts are missing for live OCR integration tests: "
            + ", ".join(missing_paths)
        )

    env = dict(os.environ)
    command = ["make", "llama-test"]
    process = subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.monotonic() + LLAMA_STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.skip(
                    "make llama-test exited before readiness check "
                    f"(code {process.returncode})."
                )
            if _is_llama_server_healthy():
                break
            time.sleep(LLAMA_READINESS_POLL_SECONDS)
        else:
            pytest.skip(
                "Timed out waiting for llama-server readiness at "
                f"{LLAMA_HEALTHCHECK_URL} after {LLAMA_STARTUP_TIMEOUT_SECONDS:.1f}s."
            )

        yield
    finally:
        _stop_process_group(process)
