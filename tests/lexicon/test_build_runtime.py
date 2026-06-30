"""Tests for the lexicon build runtime controller."""

from __future__ import annotations

from wyrdcraeft.models.lexicon_build import BuildFailed, BuildFinished
from wyrdcraeft.services.lexicon.build_runtime import LexiconBuildController


def test_controller_emits_finished_terminal_event(tmp_path) -> None:
    controller = LexiconBuildController(db_path=tmp_path / "demo.sqlite3", quiet=True)
    controller._emit_success_for_test_only()
    event = controller.get_event_nowait()
    assert isinstance(event, BuildFinished)


def test_controller_request_cancel_sets_flag_and_calls_interrupt() -> None:
    controller = LexiconBuildController(db_path=None, quiet=True)
    called: list[str] = []
    controller.set_interrupt_callback(lambda: called.append("interrupt"))
    controller.request_cancel()
    assert controller.cancel_requested is True
    assert called == ["interrupt"]


def test_controller_wraps_unhandled_exception_into_failed_event(tmp_path) -> None:
    controller = LexiconBuildController(db_path=tmp_path / "demo.sqlite3", quiet=True)
    controller._emit_failure_for_test_only(RuntimeError("boom"))
    event = controller.get_event_nowait()
    assert isinstance(event, BuildFailed)
    assert event.error_type == "RuntimeError"
