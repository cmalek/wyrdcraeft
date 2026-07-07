"""Tests for normalized POS and inflection-code seed fixtures."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from wyrdcraeft.services.morphology.catalog.pos import catalog_pos_from_wordclass
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)

from .snapshot_io import read_jsonl_gz

pytestmark = pytest.mark.morphology

#: Repository root used to locate packaged seed fixtures and test snapshots.
REPO_ROOT = Path(__file__).resolve().parents[2]
#: Packaged POS seed fixture path.
PARTS_OF_SPEECH_FIXTURE = (
    REPO_ROOT / "wyrdcraeft/etc/morphology/parts_of_speech_seed.json"
)
#: Packaged inflection-code seed fixture path.
INFLECTION_CODES_FIXTURE = (
    REPO_ROOT / "wyrdcraeft/etc/morphology/inflection_codes_seed.json"
)
#: Snapshot directory containing current morphology output samples.
SNAPSHOT_DATA_DIR = REPO_ROOT / "tests/morphology/data"
#: Direct module path used to avoid lexicon package import-cycle side effects.
FORM_DECODE_PATH = REPO_ROOT / "wyrdcraeft/services/dictionary/form_decode.py"

_FORM_DECODE_SPEC = importlib.util.spec_from_file_location(
    "_test_form_decode_module",
    FORM_DECODE_PATH,
)
assert _FORM_DECODE_SPEC is not None
assert _FORM_DECODE_SPEC.loader is not None
_FORM_DECODE_MODULE = importlib.util.module_from_spec(_FORM_DECODE_SPEC)
sys.modules[_FORM_DECODE_SPEC.name] = _FORM_DECODE_MODULE
_FORM_DECODE_SPEC.loader.exec_module(_FORM_DECODE_MODULE)
WORDCLASS_TO_BT_POS = _FORM_DECODE_MODULE.WORDCLASS_TO_BT_POS


def test_pos_seed_is_idempotent() -> None:
    with sqlite3.connect(":memory:") as connection:
        expected_pos_rows = _load_fixture_rows(PARTS_OF_SPEECH_FIXTURE)
        expected_inflection_rows = _load_fixture_rows(INFLECTION_CODES_FIXTURE)

        first_pos_map = ensure_parts_of_speech(connection)
        first_inflection_map = ensure_inflection_codes(connection, first_pos_map)
        first_counts = (
            _row_count(connection, "parts_of_speech"),
            _row_count(connection, "inflection_codes"),
        )

        second_pos_map = ensure_parts_of_speech(connection)
        second_inflection_map = ensure_inflection_codes(connection, second_pos_map)
        second_counts = (
            _row_count(connection, "parts_of_speech"),
            _row_count(connection, "inflection_codes"),
        )

    assert first_counts == (
        len(expected_pos_rows),
        len(expected_inflection_rows),
    )
    assert second_counts == first_counts
    assert second_pos_map == first_pos_map
    assert second_inflection_map == first_inflection_map


def test_wordclass_keys_resolve_to_seeded_pos_rows() -> None:
    with sqlite3.connect(":memory:") as connection:
        pos_map = ensure_parts_of_speech(connection)

    for wordclass in WORDCLASS_TO_BT_POS:
        resolved_code = catalog_pos_from_wordclass(wordclass) or wordclass
        assert resolved_code in pos_map


def test_sample_inflection_codes_resolve_to_expected_pos_rows() -> None:
    with sqlite3.connect(":memory:") as connection:
        pos_map = ensure_parts_of_speech(connection)
        ensure_inflection_codes(connection, pos_map)
        code_to_pos = dict(
            connection.execute(
                """
                SELECT code, pos_id
                FROM inflection_codes
                WHERE code IN (?, ?, ?, ?, ?, ?)
                """,
                ("If", "Po", "SgFeNo", "PsInSg1", "sgmaac", ""),
            ).fetchall(),
        )

    assert code_to_pos == {
        "If": pos_map["verb"],
        "Po": pos_map["adverb"],
        "SgFeNo": pos_map["noun"],
        "PsInSg1": pos_map["verb"],
        "sgmaac": pos_map["numeral"],
        "": pos_map["unknown"],
    }


def test_inflection_seed_covers_observed_snapshot_function_codes() -> None:
    seeded_codes = {
        str(row["code"])
        for row in _load_fixture_rows(INFLECTION_CODES_FIXTURE)
    }
    observed_codes = set()
    for path in SNAPSHOT_DATA_DIR.glob("*.jsonl.gz"):
        for row in read_jsonl_gz(path):
            function_code = row.get("function")
            if function_code is not None:
                observed_codes.add(str(function_code))

    assert observed_codes <= seeded_codes
    assert {"If", "Inf", "Pp", "PsSug"} <= seeded_codes


def _load_fixture_rows(path: Path) -> list[dict[str, object]]:
    """Read one JSON fixture file used by the POS seed tests."""
    return json.loads(path.read_text(encoding="utf-8"))


def _row_count(connection: sqlite3.Connection, table_name: str) -> int:
    """Return the current row count for one reference table."""
    return int(
        connection.execute(
            f"SELECT COUNT(*) FROM {table_name}",  # noqa: S608
        ).fetchone()[0],
    )
