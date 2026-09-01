"""Tests for Bosworth-Toller parse warning JSONL I/O."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from wyrdcraeft.models.dictionary import BTParseWarning

if TYPE_CHECKING:
    from pathlib import Path
from wyrdcraeft.services.dictionary.parse_warnings import (
    append_parse_warnings,
    write_parse_warnings,
)


def test_parse_warning_jsonl_round_trip(tmp_path: Path) -> None:
    warnings_path = tmp_path / "parse_warnings.jsonl"
    original = BTParseWarning(
        line_no=9,
        body="<B>test</B>",
        headword="test",
        pos_hint="noun",
        failure_reason="target_missing",
        detail="dele_refs did not match any sense paths",
    )
    write_parse_warnings(warnings_path, [original])
    extra = BTParseWarning(
        line_no=10,
        body="<B>other</B>",
        headword="other",
        pos_hint="verb",
        failure_reason="empty_gloss",
    )
    append_parse_warnings(warnings_path, [extra])
    rows = [
        BTParseWarning.from_json(json.loads(line))
        for line in warnings_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert rows == [original, extra]
    assert "detail" in original.to_json()
    assert "detail" not in extra.to_json()
