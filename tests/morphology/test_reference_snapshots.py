from __future__ import annotations

import json

import pytest

from wyrdcraeft.services.morphology.reference_snapshots import (
    canonical_sort_rows,
    form_rows_for_stage,
    format_reference_snapshot_result,
    generate_reference_snapshots,
    parse_form_output,
    write_jsonl_gz,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from .conftest import MANUAL_FORMS, PREFIXES, SUBSET_DICTIONARY, VERBAL_PARADIGMS
from .snapshot_io import read_jsonl_gz


def test_parse_form_output_drops_blank_lines_and_pads() -> None:
    rows = parse_form_output("\nonly\ttwo\n")
    assert rows == [
        {
            "formi": "two",
            "BT": "",
            "title": "",
            "stem": "",
            "form": "",
            "formParts": "",
            "var": "",
            "probability": "",
            "function": "",
            "wright": "",
            "paradigm": "",
            "paraID": "",
            "wordclass": "",
            "class1": "",
            "class2": "",
            "class3": "",
            "comment": "",
        }
    ]


def test_canonical_sort_and_write_jsonl_gz(tmp_path) -> None:
    rows = canonical_sort_rows(
        [{"b": 2, "a": 1}, {"b": 1, "a": 2}],
        sort_fields=["a"],
    )
    assert [row["a"] for row in rows] == ["1", "2"]

    path = tmp_path / "nested" / "snap.jsonl.gz"
    write_jsonl_gz(path, rows, update=False)
    assert read_jsonl_gz(path) == rows
    with pytest.raises(FileExistsError, match="Snapshot already exists"):
        write_jsonl_gz(path, rows, update=False)
    write_jsonl_gz(path, [{"a": "9"}], update=True)
    assert read_jsonl_gz(path) == [{"a": "9"}]


def test_form_rows_for_stage_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="Unknown stage"):
        form_rows_for_stage(GeneratorSession(), stage_name="nope")


def test_generate_reference_snapshots_subset(tmp_path) -> None:
    # ponytail: subset file also stands in for the full dict so include_full
    # runs the smoke branch without the 35k-line morphology_full dictionary.
    result = generate_reference_snapshots(
        output_dir=tmp_path,
        update=False,
        include_full=True,
        subset_dictionary=SUBSET_DICTIONARY,
        full_dictionary=SUBSET_DICTIONARY,
        manual_forms=MANUAL_FORMS,
        verbal_paradigms=VERBAL_PARADIGMS,
        prefixes=PREFIXES,
    )
    assert json.loads(format_reference_snapshot_result(result)) == {
        "output_dir": str(tmp_path),
        "include_full": True,
    }
    names = {path.name for path in tmp_path.iterdir()}
    assert "full_flow_full_smoke.jsonl.gz" in names
    assert "preprocess_subset.jsonl.gz" in names
    smoke = read_jsonl_gz(tmp_path / "full_flow_full_smoke.jsonl.gz")
    assert set(smoke[0]) == {"line_count", "byte_count", "sha256"}
