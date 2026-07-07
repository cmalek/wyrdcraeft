"""Tests for lexicon build event models."""

from __future__ import annotations

from wyrdcraeft.models.lexicon_build import (
    BuildCounters,
    BuildFailed,
    BuildLog,
    BuildSnapshot,
    LexiconBuildStage,
)


def test_stage_order_remains_stable() -> None:
    assert list(LexiconBuildStage) == [
        LexiconBuildStage.VERIFY_SOURCES,
        LexiconBuildStage.INFER_POS,
        LexiconBuildStage.BUILD_DICTIONARY_KEYS,
        LexiconBuildStage.BUILD_MORPHOLOGY_KEYS,
        LexiconBuildStage.INSERT_SEARCH_KEYS,
        LexiconBuildStage.WRITE_META,
    ]


def test_terminal_events_carry_final_snapshot() -> None:
    snapshot = BuildSnapshot(
        status="failed",
        active_stage=LexiconBuildStage.BUILD_MORPHOLOGY_KEYS,
        counters=BuildCounters(search_keys_written=0),
    )
    event = BuildFailed(
        seq=10,
        at="2026-06-28T12:00:00Z",
        snapshot=snapshot,
        error_type="RuntimeError",
        message="boom",
        traceback_text="Traceback...",
    )
    assert event.snapshot.status == "failed"
    assert event.error_type == "RuntimeError"


def test_log_event_keeps_structured_current_work() -> None:
    event = BuildLog(
        seq=3,
        at="2026-06-28T12:00:00Z",
        stage=LexiconBuildStage.BUILD_MORPHOLOGY_KEYS,
        level="info",
        message="heartbeat",
        current_item="abbad",
        processed=5000,
        total=420000,
    )
    assert event.current_item == "abbad"
    assert event.processed == 5000
