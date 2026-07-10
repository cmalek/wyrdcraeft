"""Validation sample contract for Bosworth-Toller OCR witness preparation."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

#: Supported validation page classifications for the fixed five-page sample.
VALIDATION_CLASSIFICATIONS = frozenset(
    {
        "standard_dense",
        "italics_abbreviations",
        "background_shadow",
    }
)
#: Historical graphemes tracked for exact-match token scoring.
HISTORICAL_CHARACTER_CHARSET = frozenset(
    {
        "þ",
        "ð",
        "æ",
        "ǣ",
        "ā",
        "ē",
        "ī",
        "ō",
        "ū",
        "ȳ",
        "ċ",
        "ġ",
        "Þ",
        "Ð",
        "Æ",
        "Ǣ",
        "Ā",
        "Ē",
        "Ī",
        "Ō",
        "Ū",
        "Ȳ",
        "Ċ",
        "Ġ",
    }
)
#: Minimum relative CER improvement required for Stage B recipe approval.
STAGE_B_MIN_RELATIVE_CER_IMPROVEMENT = 0.10
#: Human-readable Stage B approval rule emitted in benchmark summaries.
STAGE_B_RULE_DESCRIPTION = (
    "pass when relative diacritic-sensitive CER improvement is at least 10% "
    "versus the raw whole-page baseline and no catastrophic "
    "small-component guardrail failures are recorded"
)
#: Maximum consecutive blank lines preserved during text normalization.
_MAX_CONSECUTIVE_BLANK_LINES = 2
#: Token regex for historical-character exact-match scoring.
_HISTORICAL_TOKEN_PATTERN = re.compile(
    r"[A-Za-zÆæÐðÞþŌōĀāĒēĪīȲȳǢǣĊċĠġ'\-]+",
)


@dataclass(frozen=True)
class BTValidationPage:
    """
    One page record in the fixed BT OCR validation sample.

    Args:
        page_id: Stable page identifier derived from the source filename.
        source_filename: Source scan filename for the validation page.
        classification: Validation category for the page difficulty profile.
        comparison_witness_available: Whether a curated comparison witness exists.
        comparison_witness_path: Relative path to the comparison witness text file.

    """

    #: Stable page identifier derived from the source filename.
    page_id: str
    #: Source scan filename for the validation page.
    source_filename: str
    #: Validation category for the page difficulty profile.
    classification: str
    #: Whether a curated comparison witness exists.
    comparison_witness_available: bool
    #: Relative path to the comparison witness text file.
    comparison_witness_path: str | None = None


@dataclass(frozen=True)
class BTValidationManifest:
    """
    Fixed five-page validation sample contract for BT witness preparation.

    Args:
        pages: Validation page records in manifest order.

    """

    #: Validation page records in manifest order.
    pages: tuple[BTValidationPage, ...]


@dataclass(frozen=True)
class BTPageOCRComparison:
    """
    OCR comparison metrics for one validation page.

    Args:
        page_id: Stable page identifier from the validation manifest.
        classification: Validation category for the page difficulty profile.
        comparison_witness_available: Whether a curated comparison witness exists.
        baseline_cer: Diacritic-sensitive CER for the raw whole-page baseline.
        candidate_cer: Diacritic-sensitive CER for the candidate recipe output.
        historical_char_exact_match_rate: Exact-match rate for historical tokens.
        small_component_guardrail_failed: Whether catastrophic small-component
            loss was flagged during witness preparation.

    """

    #: Stable page identifier from the validation manifest.
    page_id: str
    #: Validation category for the page difficulty profile.
    classification: str
    #: Whether a curated comparison witness exists.
    comparison_witness_available: bool
    #: Diacritic-sensitive CER for the raw whole-page baseline.
    baseline_cer: float | None
    #: Diacritic-sensitive CER for the candidate recipe output.
    candidate_cer: float | None
    #: Exact-match rate for historical-character tokens.
    historical_char_exact_match_rate: float | None
    #: Whether catastrophic small-component loss was flagged.
    small_component_guardrail_failed: bool


@dataclass(frozen=True)
class BTRecipeStageBComparison:
    """
    Aggregated Stage B comparison for one candidate recipe.

    Args:
        recipe_id: Candidate witness-preparation recipe identifier.
        baseline_cer: Mean baseline diacritic-sensitive CER across witnessed pages.
        candidate_cer: Mean candidate diacritic-sensitive CER across witnessed
            pages.
        relative_cer_improvement: Relative CER reduction versus the baseline.
        historical_char_exact_match_rate: Mean historical-token exact-match rate
            across witnessed pages.
        passes_stage_b: Whether the candidate satisfies the Stage B pass rule.
        small_component_guardrail_failed: Whether any page failed the guardrail.
        pages: Per-page OCR comparison metrics in manifest order.
        pass_rule: Human-readable Stage B pass rule for benchmark summaries.

    """

    #: Candidate witness-preparation recipe identifier.
    recipe_id: str
    #: Mean baseline diacritic-sensitive CER across witnessed pages.
    baseline_cer: float
    #: Mean candidate diacritic-sensitive CER across witnessed pages.
    candidate_cer: float
    #: Relative CER reduction versus the baseline.
    relative_cer_improvement: float
    #: Mean historical-token exact-match rate across witnessed pages.
    historical_char_exact_match_rate: float
    #: Whether the candidate satisfies the Stage B pass rule.
    passes_stage_b: bool
    #: Whether any page failed the small-component guardrail.
    small_component_guardrail_failed: bool
    #: Per-page OCR comparison metrics in manifest order.
    pages: tuple[BTPageOCRComparison, ...]
    #: Human-readable Stage B pass rule for benchmark summaries.
    pass_rule: str = STAGE_B_RULE_DESCRIPTION


def _parse_validation_page(raw: dict[str, Any]) -> BTValidationPage:
    """
    Parse one validation page record from a manifest JSON object.

    Args:
        raw: One page object from the manifest ``pages`` list.

    Returns:
        Parsed validation page contract.

    Raises:
        ValueError: When classification or witness fields are invalid.

    """
    classification = str(raw["classification"])
    if classification not in VALIDATION_CLASSIFICATIONS:
        message = f"unsupported validation classification: {classification}"
        raise ValueError(message)

    witness_available = bool(raw["comparison_witness_available"])
    witness_path = raw.get("comparison_witness_path")
    if witness_available and not witness_path:
        message = (
            f"page {raw.get('page_id', '?')} marks comparison witness available "
            "but omits comparison_witness_path"
        )
        raise ValueError(message)
    if not witness_available and witness_path is not None:
        message = (
            f"page {raw.get('page_id', '?')} must set comparison_witness_path "
            "to null when comparison_witness_available is false"
        )
        raise ValueError(message)

    return BTValidationPage(
        page_id=str(raw["page_id"]),
        source_filename=str(raw["source_filename"]),
        classification=classification,
        comparison_witness_available=witness_available,
        comparison_witness_path=str(witness_path) if witness_path else None,
    )


def _tokenize_validation_text(text: str) -> list[str]:
    """
    Tokenize normalized validation text for historical-character scoring.

    Args:
        text: OCR or witness text.

    Returns:
        Tokens extracted in left-to-right order.

    """
    return _HISTORICAL_TOKEN_PATTERN.findall(normalize_validation_text(text))


def _historical_reference_tokens(
    reference: str,
    charset: frozenset[str],
) -> list[str]:
    """
    Select reference tokens that contain at least one historical grapheme.

    Args:
        reference: Curated comparison witness text.
        charset: Historical grapheme set used for token selection.

    Returns:
        Reference tokens containing one or more charset members.

    """
    return [
        token
        for token in _tokenize_validation_text(reference)
        if any(character in charset for character in token)
    ]


def _levenshtein_distance(
    expected: Sequence[str],
    observed: Sequence[str],
) -> int:
    """
    Compute Levenshtein distance between two character sequences.

    Args:
        expected: Expected character sequence.
        observed: Observed character sequence.

    Returns:
        Minimum edit distance between the two sequences.

    """
    if not expected:
        return len(observed)
    if not observed:
        return len(expected)

    previous = list(range(len(observed) + 1))
    for index_expected, expected_item in enumerate(expected, start=1):
        current = [index_expected]
        for index_observed, observed_item in enumerate(observed, start=1):
            substitution = previous[index_observed - 1] + (
                0 if expected_item == observed_item else 1
            )
            insertion = current[index_observed - 1] + 1
            deletion = previous[index_observed] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1]


def _mean_or_zero(values: list[float]) -> float:
    """
    Compute the arithmetic mean for one metric list.

    Args:
        values: Metric samples to average.

    Returns:
        Mean value, or ``0.0`` when the list is empty.

    """
    if not values:
        return 0.0
    return sum(values) / len(values)


def load_validation_manifest(path: Path) -> BTValidationManifest:
    """
    Load the fixed BT OCR validation sample manifest from JSON.

    Args:
        path: Path to ``validation_manifest.json``.

    Returns:
        Parsed validation manifest contract.

    Raises:
        FileNotFoundError: When the manifest file does not exist.
        TypeError: When the manifest payload has the wrong top-level shape.
        ValueError: When the manifest payload is malformed.

    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_pages = payload.get("pages")
    if not isinstance(raw_pages, list):
        message = "validation manifest must contain a pages list"
        raise TypeError(message)

    pages = tuple(_parse_validation_page(raw) for raw in raw_pages)
    return BTValidationManifest(pages=pages)


def load_comparison_witness(
    manifest_dir: Path,
    page: BTValidationPage,
) -> str | None:
    """
    Load curated comparison witness text for one validation page.

    Args:
        manifest_dir: Directory containing the validation manifest and witnesses.
        page: Validation page record with witness availability metadata.

    Returns:
        Witness text when available, otherwise ``None``.

    Raises:
        FileNotFoundError: When witness availability is true but the file is
            missing.

    """
    if not page.comparison_witness_available:
        return None
    if page.comparison_witness_path is None:
        message = f"page {page.page_id} omits comparison_witness_path"
        raise ValueError(message)

    witness_path = manifest_dir / page.comparison_witness_path
    if not witness_path.is_file():
        message = f"missing comparison witness for {page.page_id}: {witness_path}"
        raise FileNotFoundError(message)
    return witness_path.read_text(encoding="utf-8")


def normalize_validation_text(text: str) -> str:
    """
    Normalize OCR comparison text while preserving diacritic distinctions.

    Args:
        text: Raw OCR or witness text.

    Returns:
        Whitespace-normalized text suitable for deterministic metric scoring.

    """
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]

    collapsed: list[str] = []
    consecutive_blank_lines = 0
    for line in lines:
        if line.strip():
            consecutive_blank_lines = 0
            collapsed.append(line)
            continue
        consecutive_blank_lines += 1
        if consecutive_blank_lines <= _MAX_CONSECUTIVE_BLANK_LINES:
            collapsed.append("")

    return "\n".join(collapsed).strip() + "\n"


def diacritic_sensitive_cer(hypothesis: str, reference: str) -> float:
    """
    Compute character error rate on diacritic-preserving normalized text.

    Args:
        hypothesis: Candidate OCR text.
        reference: Curated comparison witness text.

    Returns:
        Character error rate on ``0.0``-``1.0`` where lower is better.

    """
    normalized_hypothesis = normalize_validation_text(hypothesis)
    normalized_reference = normalize_validation_text(reference)
    distance = _levenshtein_distance(
        list(normalized_hypothesis),
        list(normalized_reference),
    )
    denominator = max(len(normalized_reference), 1)
    return distance / denominator


def historical_char_exact_match_rate(
    hypothesis: str,
    reference: str,
    charset: frozenset[str] | None = None,
) -> float:
    """
    Compute exact-match rate for reference tokens containing historical graphemes.

    Args:
        hypothesis: Candidate OCR text.
        reference: Curated comparison witness text.

    Keyword Args:
        charset: Historical grapheme set used to select reference tokens.

    Returns:
        Fraction of historical reference tokens that appear exactly in the
        hypothesis on ``0.0``-``1.0``.

    """
    resolved_charset = charset or HISTORICAL_CHARACTER_CHARSET
    reference_tokens = _historical_reference_tokens(reference, resolved_charset)
    if not reference_tokens:
        return 1.0

    hypothesis_tokens = Counter(_tokenize_validation_text(hypothesis))
    matches = sum(
        min(count, hypothesis_tokens.get(token, 0))
        for token, count in Counter(reference_tokens).items()
    )
    return matches / len(reference_tokens)


def relative_cer_improvement(baseline_cer: float, candidate_cer: float) -> float:
    """
    Compute relative CER reduction from baseline to candidate.

    Args:
        baseline_cer: Baseline diacritic-sensitive CER.
        candidate_cer: Candidate diacritic-sensitive CER.

    Returns:
        Relative improvement where positive values mean the candidate improved
        over the baseline.

    """
    if baseline_cer <= 0.0:
        if candidate_cer <= 0.0:
            return 1.0
        return -candidate_cer
    return (baseline_cer - candidate_cer) / baseline_cer


def recipe_passes_stage_b(
    baseline_cer: float,
    candidate_cer: float,
    small_component_guardrail_failed: bool,
) -> bool:
    """
    Decide whether one candidate recipe passes Stage B validation.

    Args:
        baseline_cer: Mean baseline diacritic-sensitive CER.
        candidate_cer: Mean candidate diacritic-sensitive CER.
        small_component_guardrail_failed: Whether catastrophic small-component
            loss was flagged for the candidate recipe.

    Returns:
        ``True`` when the candidate meets the documented Stage B pass rule.

    """
    if small_component_guardrail_failed:
        return False
    return (
        relative_cer_improvement(baseline_cer, candidate_cer)
        >= STAGE_B_MIN_RELATIVE_CER_IMPROVEMENT
    )


def evaluate_stage_b_recipe(  # noqa: PLR0913
    *,
    recipe_id: str,
    manifest: BTValidationManifest,
    manifest_dir: Path,
    baseline_hypotheses: dict[str, str],
    candidate_hypotheses: dict[str, str],
    small_component_guardrail_by_page: dict[str, bool] | None = None,
) -> BTRecipeStageBComparison:
    """
    Compare one candidate recipe against raw whole-page baselines for Stage B.

    Args:
        recipe_id: Candidate witness-preparation recipe identifier.
        manifest: Fixed five-page validation manifest contract.
        manifest_dir: Directory containing comparison witness text files.
        baseline_hypotheses: Raw whole-page OCR text keyed by page id.
        candidate_hypotheses: Candidate recipe OCR text keyed by page id.

    Keyword Args:
        small_component_guardrail_by_page: Optional guardrail flags keyed by
            page id.

    Returns:
        Aggregated Stage B comparison with per-page metrics and pass decision.

    """
    guardrails = small_component_guardrail_by_page or {}
    page_comparisons: list[BTPageOCRComparison] = []
    baseline_cers: list[float] = []
    candidate_cers: list[float] = []
    historical_rates: list[float] = []
    any_guardrail_failed = False

    for page in manifest.pages:
        guardrail_failed = guardrails.get(page.page_id, False)
        any_guardrail_failed = any_guardrail_failed or guardrail_failed

        if not page.comparison_witness_available:
            page_comparisons.append(
                BTPageOCRComparison(
                    page_id=page.page_id,
                    classification=page.classification,
                    comparison_witness_available=False,
                    baseline_cer=None,
                    candidate_cer=None,
                    historical_char_exact_match_rate=None,
                    small_component_guardrail_failed=guardrail_failed,
                ),
            )
            continue

        reference = load_comparison_witness(manifest_dir, page)
        if reference is None:
            message = f"comparison witness missing for witnessed page {page.page_id}"
            raise ValueError(message)
        baseline_text = baseline_hypotheses[page.page_id]
        candidate_text = candidate_hypotheses[page.page_id]
        baseline_cer = diacritic_sensitive_cer(baseline_text, reference)
        candidate_cer = diacritic_sensitive_cer(candidate_text, reference)
        historical_rate = historical_char_exact_match_rate(
            candidate_text,
            reference,
        )
        baseline_cers.append(baseline_cer)
        candidate_cers.append(candidate_cer)
        historical_rates.append(historical_rate)
        page_comparisons.append(
            BTPageOCRComparison(
                page_id=page.page_id,
                classification=page.classification,
                comparison_witness_available=True,
                baseline_cer=baseline_cer,
                candidate_cer=candidate_cer,
                historical_char_exact_match_rate=historical_rate,
                small_component_guardrail_failed=guardrail_failed,
            ),
        )

    mean_baseline = _mean_or_zero(baseline_cers)
    mean_candidate = _mean_or_zero(candidate_cers)
    mean_historical = _mean_or_zero(historical_rates)
    return BTRecipeStageBComparison(
        recipe_id=recipe_id,
        baseline_cer=mean_baseline,
        candidate_cer=mean_candidate,
        relative_cer_improvement=relative_cer_improvement(
            mean_baseline,
            mean_candidate,
        ),
        historical_char_exact_match_rate=mean_historical,
        passes_stage_b=recipe_passes_stage_b(
            mean_baseline,
            mean_candidate,
            any_guardrail_failed,
        ),
        small_component_guardrail_failed=any_guardrail_failed,
        pages=tuple(page_comparisons),
    )
