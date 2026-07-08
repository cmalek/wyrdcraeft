"""Unit and integration tests for BTQueryService."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTPos, BTSense
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.query import BTQueryService, entry_to_dict
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.markup import normalize_old_english

_CORPUS_SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "corpus_sample.txt"
)
_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _seed_forms_table(db_path: Path, row_count: int) -> int:
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment, bt_key, title_key,
                stem_key, form_key, formi_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    "",
                    "0",
                    "0",
                    "",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                )
                for index in range(row_count)
            ],
        )
        conn.commit()
    return row_count


def _index_fixture(source: Path, temp_dir: Path) -> Path:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    if not index_db.exists():
        _seed_forms_table(index_db, row_count=1)
    sink = BTSqliteSink(index_db)
    try:
        BTIndexPipeline().run(source, sink)
    finally:
        sink.close()
    return index_db


@pytest.fixture
def sample_index_db(temp_dir: Path) -> Path:
    return _index_fixture(_SAMPLE_LINES, temp_dir)


@pytest.fixture
def corpus_index_db(temp_dir: Path) -> Path:
    return _index_fixture(_CORPUS_SAMPLE, temp_dir)


def test_bt_senses_round_trip_rich_fields(temp_dir: Path) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    _seed_forms_table(index_db, row_count=1)
    entry = BTConsolidatedEntry(
        norm_key="richsense",
        headword_raw="richsense",
        headword_macronized="richsense",
        normalized_title="richsense",
        pos=BTPos.NOUN,
        entry_order=7,
        senses=[
            BTSense(
                gloss_en="meaning one",
                sense_path="1.a",
                parent_path="1",
                source_label_raw="I a",
                source_fragment_raw="raw fragment",
                prefix_fragment_raw="prefix bit",
                modifiers=("mod-one", "mod-two"),
                grammatical_context=("genitive",),
                usage_note="usage note",
            ),
        ],
    )
    sink = BTSqliteSink(index_db)
    try:
        sink.write_entries([entry], [])
    finally:
        sink.close()

    service = BTQueryService(index_db)
    try:
        entries = service.lookup_by_norm_key("richsense", pos="noun")
    finally:
        service.close()

    assert len(entries) == 1
    sense = entries[0].senses[0]
    assert sense.gloss_en == "meaning one"
    assert sense.sense_path == "1.a"
    assert sense.parent_path == "1"
    assert sense.source_label_raw == "I a"
    assert sense.source_fragment_raw == "raw fragment"
    assert sense.prefix_fragment_raw == "prefix bit"
    assert sense.modifiers == ("mod-one", "mod-two")
    assert sense.grammatical_context == ("genitive",)
    assert sense.usage_note == "usage note"
    assert sense.sense_label == "I a"
    assert entries[0].entry_order == 7


def test_lookup_abbod_variant_returns_abbad_noun(sample_index_db: Path) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_lemma("abbod", pos="noun")
    finally:
        service.close()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.norm_key == "abbad"
    assert entry.pos == BTPos.NOUN
    assert {sense.sense_label for sense in entry.senses} >= {"I", "II"}
    assert "abbod" in entry.variants


def test_lookup_by_normalized_title_joins_abbod_variant_to_abbad(
    sample_index_db: Path,
) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_by_normalized_title("abbod", pos="noun")
    finally:
        service.close()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.norm_key == "abbad"
    assert entry.normalized_title == "abbad"
    assert entry.pos == BTPos.NOUN
    assert "abbod" in entry.variants


def test_lookup_by_normalized_title_matches_headword_directly(
    sample_index_db: Path,
) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_by_normalized_title("abbad", pos="noun")
    finally:
        service.close()

    assert len(entries) == 1
    assert entries[0].headword_macronized == "abbad"


def test_lookup_by_norm_key_reconstructs_senses_and_variants(
    sample_index_db: Path,
) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_by_norm_key("abbad", pos="noun")
    finally:
        service.close()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.headword_raw == "abbad"
    assert entry.senses[0].gloss_en.startswith("an abbot")
    assert entry.senses[0].sense_label == "I"
    assert entry.senses[1].sense_label == "II"
    assert entry.senses[0].display_label == "1"
    assert entry.senses[1].display_label == "2"
    assert entry.variants


def test_lookup_a_pos_filter_returns_distinct_homographs(
    corpus_index_db: Path,
) -> None:
    service = BTQueryService(corpus_index_db)
    try:
        adv_entries = service.lookup_lemma("a", pos="adv")
        prep_entries = service.lookup_lemma("a", pos="prep")
        noun_entries = service.lookup_lemma("a", pos="noun")
    finally:
        service.close()

    assert len(adv_entries) == 1
    assert len(prep_entries) == 2
    assert adv_entries[0].pos == BTPos.ADV
    assert all(entry.pos == BTPos.PREP for entry in prep_entries)
    assert adv_entries[0].norm_key == prep_entries[0].norm_key == "a"
    assert adv_entries[0].senses[0].gloss_en != prep_entries[0].senses[0].gloss_en
    assert prep_entries[0].entry_order != prep_entries[1].entry_order
    assert noun_entries == []


def test_lookup_unknown_lemma_returns_empty(sample_index_db: Path) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_lemma("zzzznotaword")
    finally:
        service.close()

    assert entries == []


def test_entry_to_dict_is_json_serializable(sample_index_db: Path) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_lemma("abbod")
    finally:
        service.close()

    payload = entry_to_dict(entries[0])
    encoded = json.dumps(payload, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert decoded["norm_key"] == "abbad"
    assert decoded["pos"] == "noun"
    assert decoded["senses"][0]["gloss_en"].startswith("an abbot")
    assert decoded["senses"][0]["sense_label"] == "1"
    assert decoded["senses"][1]["sense_label"] == "2"


def test_lookup_normalizes_old_english_input(sample_index_db: Path) -> None:
    service = BTQueryService(sample_index_db)
    try:
        entries = service.lookup_lemma("Abbod")
    finally:
        service.close()

    assert len(entries) == 1
    assert entries[0].norm_key == "abbad"


def test_lookup_by_norm_key_uses_normalize_old_english(sample_index_db: Path) -> None:
    service = BTQueryService(sample_index_db)
    try:
        key = normalize_old_english("abbad")
        assert key is not None
        entries = service.lookup_by_norm_key(key)
    finally:
        service.close()

    assert any(entry.norm_key == "abbad" for entry in entries)


def test_lookup_reads_dictionary_rows_from_canonical_db(
    temp_dir: Path,
) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    initial_forms = _seed_forms_table(index_db, row_count=3)
    sink = BTSqliteSink(index_db)
    try:
        BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()

    with sqlite3.connect(index_db) as conn:
        forms_count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
    assert forms_count == initial_forms

    service = BTQueryService(index_db)
    try:
        entries = service.lookup_lemma("abbod", pos="noun")
    finally:
        service.close()

    assert len(entries) == 1
    assert entries[0].norm_key == "abbad"
    assert entries[0].pos == BTPos.NOUN
