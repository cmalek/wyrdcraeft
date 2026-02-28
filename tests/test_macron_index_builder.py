from __future__ import annotations

import json
from typing import TYPE_CHECKING

from wyrdcraeft.services.markup import MacronApplicator

if TYPE_CHECKING:
    from pathlib import Path


def test_build_index_from_bt_extracts_and_dedupes(tmp_path: Path):
    source = tmp_path / "bt.txt"
    source.write_text(
        (
            "x@<B>fōo,</B> entry@foo\n"
            "x@<B>fōo,</B> duplicate@foo\n"
            "x@<B>foō;</B> entry@foo\n"
            "x@<B>bār.</B> entry@bar,barr\n"
            "x@<B>-ful,</B> affix@-ful\n"
            "invalid line"
        ),
        encoding="utf-8",
    )
    output = tmp_path / "index.json"

    index = MacronApplicator.build_index_from_bt(source, output)

    assert "foo" in index.ambiguous
    assert index.ambiguous["foo"] == ["foō", "fōo"]
    assert index.unique["bar"] == "bār"
    assert index.unique["barr"] == "bār"
    assert "-ful" not in index.unique

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "meta" in payload
    assert payload["meta"]["unique_count"] == len(index.unique)
    assert payload["meta"]["ambiguous_count"] == len(index.ambiguous)
