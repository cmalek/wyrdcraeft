from __future__ import annotations

import io

import pytest

from wyrdcraeft.services.morphology.build_profile import MorphologyBuildProfiler
from wyrdcraeft.services.morphology.progress import MorphologyStage

pytestmark = pytest.mark.morphology


def test_build_profiler_emits_stage_and_sqlite_sections() -> None:
    profiler = MorphologyBuildProfiler(enabled=True)
    with profiler.time_setup("load data"):
        pass

    profiler.begin_stage(MorphologyStage.MANUAL, forms_written=0)
    profiler.end_stage(MorphologyStage.MANUAL, forms_written=3)
    profiler.record_sqlite_flush(0.5, 3)

    output = io.StringIO()
    profiler.emit_summary(forms_written=3, file=output)
    rendered = output.getvalue()

    assert "Morphology build profile" in rendered
    assert "manual" in rendered
    assert "sqlite_flush" in rendered
    assert "load data" in rendered
    assert "total" in rendered


def test_build_profiler_disabled_emits_nothing() -> None:
    profiler = MorphologyBuildProfiler(enabled=False)
    output = io.StringIO()
    profiler.emit_summary(forms_written=0, file=output)
    assert output.getvalue() == ""
