from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from wyrdcraeft.services.ocr.bt_witness_prep.validation import (
    HISTORICAL_CHARACTER_CHARSET,
    STAGE_B_RULE_DESCRIPTION,
    BTRecipeStageBComparison,
    BTValidationManifest,
    diacritic_sensitive_cer,
    evaluate_stage_b_recipe,
    historical_char_exact_match_rate,
    load_comparison_witness,
    load_validation_manifest,
    recipe_passes_stage_b,
    relative_cer_improvement,
)

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "bt_witness_prep"
)
MANIFEST_PATH = FIXTURE_DIR / "validation_manifest.json"

REQUIRED_CLASSIFICATIONS = {
    "standard_dense": 3,
    "italics_abbreviations": 1,
    "background_shadow": 1,
}


@pytest.fixture
def manifest() -> BTValidationManifest:
    return load_validation_manifest(MANIFEST_PATH)


def test_validation_manifest_declares_exactly_five_pages(
    manifest: BTValidationManifest,
) -> None:
    assert len(manifest.pages) == 5


def test_validation_manifest_covers_required_page_classifications(
    manifest: BTValidationManifest,
) -> None:
    counts = Counter(page.classification for page in manifest.pages)

    assert counts == REQUIRED_CLASSIFICATIONS


def test_validation_manifest_comparison_witness_files_exist_when_available(
    manifest: BTValidationManifest,
) -> None:
    for page in manifest.pages:
        if not page.comparison_witness_available:
            assert page.comparison_witness_path is None
            continue

        assert page.comparison_witness_path is not None
        witness_path = FIXTURE_DIR / page.comparison_witness_path
        assert witness_path.is_file(), (
            f"missing comparison witness for {page.page_id}: {witness_path}"
        )
        assert witness_path.read_text(encoding="utf-8").strip()


def test_validation_manifest_page_ids_are_unique(
    manifest: BTValidationManifest,
) -> None:
    page_ids = [page.page_id for page in manifest.pages]

    assert len(page_ids) == len(set(page_ids))


def test_validation_manifest_source_files_exist_and_match_page_ids(
    manifest: BTValidationManifest,
) -> None:
    from wyrdcraeft.services.ocr.bt_witness_prep.models import BTSourcePage

    for page in manifest.pages:
        source_path = FIXTURE_DIR / page.source_filename
        assert source_path.is_file(), (
            f"missing source for {page.page_id}: {source_path}"
        )
        assert BTSourcePage.page_id_for(source_path) == page.page_id


def test_diacritic_sensitive_cer_is_zero_for_identical_text() -> None:
    reference = "Ðīn abal and cræft thy strength and power"

    assert diacritic_sensitive_cer(reference, reference) == 0.0


def test_diacritic_sensitive_cer_penalizes_diacritic_substitutions() -> None:
    reference = "Ðīn abal and cræft"
    hypothesis = "Din abal and craeft"

    assert diacritic_sensitive_cer(hypothesis, reference) > 0.15


def test_historical_char_exact_match_rate_counts_matching_tokens() -> None:
    reference = "ðū -bæcest, he -bæceþ; p. -bōc"
    hypothesis = "ðū -bæcest, he -baeth; p. -boc"

    rate = historical_char_exact_match_rate(
        hypothesis,
        reference,
        charset=HISTORICAL_CHARACTER_CHARSET,
    )

    assert 0.0 < rate < 1.0


def test_historical_char_exact_match_rate_is_one_for_identical_text() -> None:
    reference = "Se hlāf þurh fȳres hǣtan abacen"

    assert (
        historical_char_exact_match_rate(
            reference,
            reference,
            charset=HISTORICAL_CHARACTER_CHARSET,
        )
        == 1.0
    )


def test_relative_cer_improvement_measures_reduction_from_baseline() -> None:
    assert relative_cer_improvement(0.50, 0.40) == pytest.approx(0.20)
    assert relative_cer_improvement(0.50, 0.55) == pytest.approx(-0.10)


def test_recipe_passes_stage_b_requires_ten_percent_gain_without_guardrail() -> None:
    assert recipe_passes_stage_b(
        baseline_cer=0.50,
        candidate_cer=0.40,
        small_component_guardrail_failed=False,
    )
    assert not recipe_passes_stage_b(
        baseline_cer=0.50,
        candidate_cer=0.46,
        small_component_guardrail_failed=False,
    )
    assert not recipe_passes_stage_b(
        baseline_cer=0.50,
        candidate_cer=0.40,
        small_component_guardrail_failed=True,
    )


def test_load_comparison_witness_reads_fixture_transcriptions(
    manifest: BTValidationManifest,
) -> None:
    page = next(
        page for page in manifest.pages if page.page_id == "bt-0002"
    )

    witness = load_comparison_witness(FIXTURE_DIR, page)

    assert witness is not None
    assert "abal" in witness
    assert "Ðīn" in witness


def test_evaluate_stage_b_recipe_pairs_baseline_and_candidate_texts(
    manifest: BTValidationManifest,
) -> None:
    reference_by_page = {
        page.page_id: load_comparison_witness(FIXTURE_DIR, page)
        for page in manifest.pages
        if page.comparison_witness_available
    }
    baseline_hypotheses = {
        page_id: text.replace("Ð", "D").replace("ī", "i").replace("æ", "ae")
        for page_id, text in reference_by_page.items()
        if text is not None
    }
    candidate_hypotheses = dict(reference_by_page)

    result = evaluate_stage_b_recipe(
        recipe_id="bt-two-column-v1",
        manifest=manifest,
        manifest_dir=FIXTURE_DIR,
        baseline_hypotheses=baseline_hypotheses,
        candidate_hypotheses={
            page_id: text
            for page_id, text in candidate_hypotheses.items()
            if text is not None
        },
        small_component_guardrail_by_page={
            page.page_id: False for page in manifest.pages
        },
    )

    assert isinstance(result, BTRecipeStageBComparison)
    assert result.recipe_id == "bt-two-column-v1"
    assert result.baseline_cer > result.candidate_cer
    assert result.relative_cer_improvement >= 0.10
    assert result.historical_char_exact_match_rate == 1.0
    assert result.passes_stage_b
    assert result.pass_rule == STAGE_B_RULE_DESCRIPTION
    assert len(result.pages) == 5
    assert result.pages[0].baseline_cer is not None
    assert result.pages[0].candidate_cer is not None


def test_evaluate_stage_b_recipe_accepts_stitched_candidate_page_text(
    manifest: BTValidationManifest,
) -> None:
    page = next(page for page in manifest.pages if page.page_id == "bt-0002")
    reference = load_comparison_witness(FIXTURE_DIR, page)
    assert reference is not None

    # ponytail: page-level CER only; tile concat is benchmark-script concern
    baseline_text = reference.replace("Ð", "D").replace("ī", "i")
    tile_a, tile_b = reference[: len(reference) // 2], reference[len(reference) // 2 :]
    stitched_candidate = f"{tile_a.strip()}\n\n{tile_b.strip()}\n"

    result = evaluate_stage_b_recipe(
        recipe_id="bt-two-column-v1",
        manifest=BTValidationManifest(pages=(page,)),
        manifest_dir=FIXTURE_DIR,
        baseline_hypotheses={page.page_id: baseline_text},
        candidate_hypotheses={page.page_id: stitched_candidate},
        small_component_guardrail_by_page={page.page_id: False},
    )

    assert result.pages[0].baseline_cer is not None
    assert result.pages[0].candidate_cer is not None
    assert result.pages[0].candidate_cer < result.pages[0].baseline_cer


def test_evaluate_stage_b_recipe_keeps_none_metrics_without_comparison_witness(
    manifest: BTValidationManifest,
) -> None:
    page = next(
        page for page in manifest.pages if not page.comparison_witness_available
    )

    result = evaluate_stage_b_recipe(
        recipe_id="bt-two-column-v1",
        manifest=BTValidationManifest(pages=(page,)),
        manifest_dir=FIXTURE_DIR,
        baseline_hypotheses={},
        candidate_hypotheses={},
        small_component_guardrail_by_page={page.page_id: True},
    )

    assert result.pages[0].baseline_cer is None
    assert result.pages[0].candidate_cer is None
    assert result.pages[0].historical_char_exact_match_rate is None
    assert result.pages[0].small_component_guardrail_failed is True
    assert result.small_component_guardrail_failed is True
