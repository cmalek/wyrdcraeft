"""Tests for optional Bosworth-Toller LLM parse repair."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from wyrdcraeft.models.dictionary import (
    BTLineKind,
    BTPos,
    BTSense,
    RawBTLine,
    legacy_bt_sense,
)
from wyrdcraeft.services.dictionary.line_parser import ParsedBTLine
from wyrdcraeft.services.dictionary.llm_fix_pass import (
    BTLLMFixPass,
    BTParseWarning,
    LLMFixResponseModel,
    _extract_json_object,
    write_parse_warnings,
)
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink


def _parsed_line(*, line_no: int = 42, senses: tuple[BTSense, ...] = ()) -> ParsedBTLine:
    raw = RawBTLine(
        line_no=line_no,
        kind=BTLineKind.MAIN,
        headword_raw="test",
        pos_fragment="n.",
        raw_text="<B>test</B> n. <I>broken gloss</I> :-- OE citation",
    )
    return ParsedBTLine(
        raw_line=raw,
        lookup_keys=("test",),
        slug_field="test",
        headword_macronized="test",
        variants=(),
        pos=BTPos.NOUN,
        genders=(),
        editorial_target=None,
        dele_refs=(),
        etymology_blocks=(),
        senses=senses,
        skip_reason=None,
    )


def test_extract_json_object_from_fenced_response() -> None:
    payload = _extract_json_object(
        '```json\n{"senses":[{"sense_label":"I","gloss_en":"A test"}]}\n```'
    )
    assert payload["senses"] == [{"sense_label": "I", "gloss_en": "A test"}]


def test_llm_fix_response_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        LLMFixResponseModel.model_validate(
            {
                "senses": [{"sense_label": "I", "gloss_en": "A test"}],
                "hallucinated": True,
            }
        )


def test_patch_parsed_line_replaces_senses_and_etymology() -> None:
    fix_pass = BTLLMFixPass(client=httpx.Client())
    parsed = _parsed_line()
    fix = LLMFixResponseModel(
        senses=[{"sense_label": "I", "gloss_en": "Repaired gloss"}],
        etymology="[Lat. testus]",
    )
    patched = fix_pass.patch_parsed_line(parsed, fix)
    assert patched.senses == (legacy_bt_sense("I", "Repaired gloss"),)
    assert patched.etymology_blocks == ("[Lat. testus]",)


def test_repair_warning_invalid_json_returns_none() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "not json at all"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fix_pass = BTLLMFixPass(client=client)
    warning = BTParseWarning(
        line_no=42,
        body="body",
        headword="test",
        pos_hint="noun",
        failure_reason="empty_senses_nonempty_body",
    )
    assert fix_pass.repair_warning(warning) is None


def test_apply_fixes_patches_only_warning_lines(temp_dir: Path) -> None:
    valid_fix = {
        "senses": [{"sense_label": "I", "gloss_en": "Repaired gloss"}],
        "etymology": "[Lat. testus]",
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": json.dumps(valid_fix)})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fix_pass = BTLLMFixPass(client=client)

    parsed_lines = [
        _parsed_line(line_no=1, senses=()),
        _parsed_line(line_no=42, senses=()),
    ]
    warnings_path = temp_dir / "parse_warnings.jsonl"
    write_parse_warnings(
        warnings_path,
        [
            BTParseWarning(
                line_no=42,
                body=parsed_lines[1].raw_line.raw_text if parsed_lines[1].raw_line else "",
                headword="test",
                pos_hint="noun",
                failure_reason="empty_senses_nonempty_body",
            )
        ],
    )

    stats = fix_pass.apply_fixes(warnings_path, parsed_lines)
    assert stats.attempted == 1
    assert stats.succeeded == 1
    assert stats.failed == 0
    assert parsed_lines[0].senses == ()
    assert parsed_lines[1].senses == (
        legacy_bt_sense("I", "Repaired gloss"),
    )


def test_apply_fixes_keeps_deterministic_line_on_validation_failure(
    temp_dir: Path,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "response": json.dumps(
                    {
                        "senses": [{"sense_label": "I", "gloss_en": "ok"}],
                        "extra_key": "bad",
                    }
                )
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fix_pass = BTLLMFixPass(client=client)
    parsed = _parsed_line(line_no=7, senses=())
    parsed_lines = [parsed]
    warnings_path = temp_dir / "parse_warnings.jsonl"
    write_parse_warnings(
        warnings_path,
        [
            BTParseWarning(
                line_no=7,
                body="body",
                headword="test",
                pos_hint="noun",
                failure_reason="empty_senses_nonempty_body",
            )
        ],
    )

    stats = fix_pass.apply_fixes(warnings_path, parsed_lines)
    assert stats.failed == 1
    assert parsed_lines[0].senses == ()


def test_pipeline_without_llm_fix_pass_unchanged(temp_dir: Path) -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "dictionary"
        / "sample_lines.txt"
    )
    index_db = temp_dir / "baseline.sqlite3"
    sink = BTSqliteSink(index_db)
    try:
        baseline_report = BTIndexPipeline().run(source, sink)
    finally:
        sink.close()

    index_db_2 = temp_dir / "with_warnings.sqlite3"
    sink_2 = BTSqliteSink(index_db_2)
    warnings_path = temp_dir / "parse_warnings.jsonl"
    try:
        warnings_report = BTIndexPipeline().run(
            source,
            sink_2,
            warnings_path=warnings_path,
        )
    finally:
        sink_2.close()

    assert warnings_report.merged == baseline_report.merged
    assert warnings_report.senses_written == baseline_report.senses_written
    assert warnings_path.is_file()


def test_pipeline_llm_fix_pass_only_runs_on_warnings(temp_dir: Path) -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "dictionary"
        / "sample_lines.txt"
    )
    warnings_path = temp_dir / "parse_warnings.jsonl"
    index_db = temp_dir / "llm.sqlite3"
    calls: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        calls.append(payload)
        return httpx.Response(
            200,
            json={
                "response": json.dumps(
                    {
                        "senses": [{"sense_label": "I", "gloss_en": "LLM gloss"}],
                    }
                )
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fix_pass = BTLLMFixPass(client=client)
    sink = BTSqliteSink(index_db)
    try:
        BTIndexPipeline().run(
            source,
            sink,
            warnings_path=warnings_path,
            llm_fix_pass=fix_pass,
        )
    finally:
        sink.close()

    warning_lines = warnings_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(calls) == len(warning_lines)


def test_parse_warning_detail_round_trip_and_llm_compatibility(temp_dir: Path) -> None:
    warnings_path = temp_dir / "parse_warnings.jsonl"
    original = BTParseWarning(
        line_no=9,
        body="<B>test</B>",
        headword="test",
        pos_hint="noun",
        failure_reason="target_missing",
        detail="dele_refs did not match any sense paths",
    )
    write_parse_warnings(warnings_path, [original])
    loaded = BTParseWarning.from_json(json.loads(warnings_path.read_text().strip()))
    assert loaded.detail == original.detail
    assert loaded.failure_reason == "target_missing"
    assert "detail" in original.to_json()
