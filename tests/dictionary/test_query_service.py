"""Unit and integration tests for BTQueryService."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wyrdcraeft.models.dictionary import BTPos
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


def _index_fixture(source: Path, temp_dir: Path) -> Path:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
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
    assert len(prep_entries) == 1
    assert adv_entries[0].pos == BTPos.ADV
    assert prep_entries[0].pos == BTPos.PREP
    assert adv_entries[0].norm_key == prep_entries[0].norm_key == "a"
    assert adv_entries[0].senses[0].gloss_en != prep_entries[0].senses[0].gloss_en
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
