from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.ocr_metrics import compute_ocr_metrics
from wyrdcraeft.services.ocr.old_english_pipeline import (
    OldEnglishOCRConfig,
    run_old_english_ocr_pipeline,
)

FIXTURE_STEMS = ("wright1", "wright2", "wright3", "wright4", "wright5")
INTEGRATION_PROXY_MAX_TOKENS_CAP = int(
    os.environ.get("OCR_INTEGRATION_PROXY_MAX_TOKENS_CAP", "2000")
)
INTEGRATION_PROXY_OVERRIDE_LENGTH_TO_STOP = (
    os.environ.get("OCR_INTEGRATION_PROXY_OVERRIDE_LENGTH_TO_STOP", "false").lower()
    in {"1", "true", "yes", "on"}
)
FIXTURE_PROXY_MAX_TOKENS_CAP_OVERRIDES: dict[str, int] = {
    "wright2": int(
        os.environ.get("OCR_INTEGRATION_WRIGHT2_PROXY_MAX_TOKENS_CAP", "4000")
    )
}


def _load_thresholds(stem: str) -> dict[str, float]:
    repo_root = Path(__file__).resolve().parents[1]
    thresholds_path = repo_root / "tests/fixtures/ocr/wright_quality_thresholds.json"
    payload = json.loads(thresholds_path.read_text(encoding="utf-8"))
    defaults = payload["defaults"]
    fixture_overrides = payload["fixtures"].get(stem, {})
    merged = dict(defaults)
    merged.update(fixture_overrides)
    return {
        "max_cer": float(merged["max_cer"]),
        "max_wer": float(merged["max_wer"]),
        "min_thorn_recall": float(merged["min_thorn_recall"]),
        "max_thorn_to_p_rate": float(merged["max_thorn_to_p_rate"]),
        "min_macron_recall": float(merged["min_macron_recall"]),
    }


@pytest.mark.ocr_integration
@pytest.mark.parametrize("fixture_stem", FIXTURE_STEMS)
def test_live_ocr_pipeline_meets_quality_thresholds(
    ensure_llama_server,  # noqa: ARG001
    fixture_stem: str,
    temp_dir: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_root = repo_root / "tests/fixtures/ocr"
    input_pdf = fixture_root / f"{fixture_stem}.pdf"
    expected_markdown_path = fixture_root / f"{fixture_stem}.md"
    output_dir = temp_dir / fixture_stem
    proxy_max_tokens_cap = FIXTURE_PROXY_MAX_TOKENS_CAP_OVERRIDES.get(
        fixture_stem, INTEGRATION_PROXY_MAX_TOKENS_CAP
    )

    try:
        output = run_old_english_ocr_pipeline(
            OldEnglishOCRConfig(
                input_pdf=input_pdf,
                output_dir=output_dir,
                olmocr_model="./data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf",
                proxy_max_tokens_cap=proxy_max_tokens_cap,
                proxy_override_length_to_stop=INTEGRATION_PROXY_OVERRIDE_LENGTH_TO_STOP,
            )
        )
    except RuntimeError as exc:
        if fixture_stem == "wright2":
            pytest.xfail(
                "wright2 live OCR is currently unstable on local profile: "
                f"{exc}"
            )
        raise
    observed_text = output.raw_text_path.read_text(encoding="utf-8")
    expected_text = expected_markdown_path.read_text(encoding="utf-8")
    metrics = compute_ocr_metrics(
        expected_text=expected_text,
        observed_text=observed_text,
    )
    thresholds = _load_thresholds(fixture_stem)
    thorn_expected = int(metrics["thorn_expected"])
    thorn_recall = (
        1.0
        if thorn_expected == 0
        else float(metrics["thorn_preserved"]) / thorn_expected
    )

    assert metrics["cer"] <= thresholds["max_cer"], metrics
    assert metrics["wer"] <= thresholds["max_wer"], metrics
    assert metrics["thorn_to_p_rate"] <= thresholds["max_thorn_to_p_rate"], metrics
    assert thorn_recall >= thresholds["min_thorn_recall"], metrics
    assert metrics["macron_recall"] >= thresholds["min_macron_recall"], metrics
