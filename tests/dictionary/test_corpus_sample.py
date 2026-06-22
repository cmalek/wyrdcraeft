"""Smoke tests for the stratified Bosworth-Toller corpus sample fixture."""

from __future__ import annotations

import json
from pathlib import Path

from wyrdcraeft.models.dictionary import BTLineKind
from wyrdcraeft.services.dictionary import BTLineParser

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "dictionary"
_CORPUS_PATH = _FIXTURE_DIR / "corpus_sample.txt"
_MANIFEST_PATH = _FIXTURE_DIR / "corpus_sample_manifest.json"
_MIN_KEYS = 700
_MIN_LINES = 900
_MAX_LINES = 1150


def _load_manifest() -> dict[str, object]:
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def test_corpus_sample_manifest_and_line_count_bounds() -> None:
    """
    Ensure corpus fixture is present and within phase-02b size constraints.
    """
    manifest = _load_manifest()
    lines = _CORPUS_PATH.read_text(encoding="utf-8").splitlines()
    assert isinstance(manifest.get("key_count"), int)
    assert isinstance(manifest.get("line_count"), int)
    assert manifest["key_count"] >= _MIN_KEYS
    assert _MIN_LINES <= len(lines) <= _MAX_LINES
    assert manifest["line_count"] == len(lines)


def test_corpus_sample_lines_parse_without_raising() -> None:
    """
    Parse every corpus line and require deterministic parse or explicit skip.
    """
    parser = BTLineParser()
    lines = _CORPUS_PATH.read_text(encoding="utf-8").splitlines()
    kind_counts: dict[BTLineKind, int] = dict.fromkeys(BTLineKind, 0)
    parsed_main_count = 0

    for line_no, line in enumerate(lines, start=1):
        parsed = parser.parse(source_line_no=line_no, line=line)
        if parsed.raw_line is None:
            assert parsed.skip_reason in {
                "not 3 @ fields",
                "no <B> headword",
                "headword not wordlike",
            }
            continue
        assert parsed.skip_reason is None
        assert parsed.headword_macronized
        kind_counts[parsed.raw_line.kind] += 1
        if parsed.raw_line.kind == BTLineKind.MAIN:
            parsed_main_count += 1

    assert parsed_main_count > 0
    assert kind_counts[BTLineKind.MAIN] > 0
    assert kind_counts[BTLineKind.ADD] > 0
    assert kind_counts[BTLineKind.SUBSTITUTE] > 0
    assert (
        kind_counts[BTLineKind.DELE] > 0 or kind_counts[BTLineKind.DELE_AND_ADD] > 0
    )
    assert kind_counts[BTLineKind.CROSS_REF] > 0
