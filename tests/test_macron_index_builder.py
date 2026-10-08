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
            "x@<B>ǣrst, ærþe-land, ærþling.</B> entry@ærþling,ærst,ærþe-land,ærþ\n"
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
    # variants whose headword is a different spelling are not mapped
    assert "barr" not in index.unique
    # each variant spelled out in the heading gets its own entry
    assert index.unique["ærst"] == "ǣrst"
    assert index.unique["ærþling"] == "ærþling"
    assert index.unique["ærþeland"] == "ærþe-land"
    assert "ærþ" not in index.unique
    assert "-ful" not in index.unique
    assert index.ambiguous_metadata == {}

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "meta" in payload
    assert payload["meta"]["unique_count"] == len(index.unique)
    assert payload["meta"]["ambiguous_count"] == len(index.ambiguous)
    assert payload["ambiguous_metadata"] == {}
