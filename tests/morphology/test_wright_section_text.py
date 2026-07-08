"""Tests for Wright section markdown parsing and catalog text ingest."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest
from sqlalchemy import select

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import WrightSection
from wyrdcraeft.services.dictionary.resources import default_wright_source_path
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.query import MorphologyCatalogQueryService
from wyrdcraeft.services.morphology.catalog.wright_text import (
    IngestResult,
    WrightSectionTextIngester,
    parse_wright_sections,
    parse_wright_sections_from_path,
)

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))
SECTION_334_SNIPPET = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "wright_nouns.md"
)


@pytest.fixture
def catalog_db(tmp_path: Path):
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
    yield engine, tmp_path
    engine.dispose()


def test_packaged_wright_source_path_is_readable() -> None:
    wright_path = default_wright_source_path()
    assert wright_path.is_file()
    assert wright_path.name == "wright.md"

    sections = parse_wright_sections_from_path(wright_path)
    assert sections


def test_parse_section_334_snippet_preserves_oe_unicode() -> None:
    markdown = SECTION_334_SNIPPET.read_text(encoding="utf-8")
    sections = parse_wright_sections(markdown)

    assert 334 in sections
    section_text = sections[334]
    assert section_text.startswith("§ 334.")
    assert "Masculine" in section_text
    assert "st\u0101n" in section_text
    assert "d\u00e6g" in section_text


def test_parse_section_heading_without_trailing_dot() -> None:
    markdown = "§ 334\nMasculine a-stem intro.\n\n§ 335\nNeuter forms.\n"
    sections = parse_wright_sections(markdown)

    assert sections[334] == "§ 334 Masculine a-stem intro."
    assert sections[335] == "§ 335 Neuter forms."


def test_parse_wright_sections_from_path(tmp_path: Path) -> None:
    md_path = tmp_path / "wright.md"
    md_path.write_text("§ 400\nWeak masculine.\n", encoding="utf-8")

    sections = parse_wright_sections_from_path(md_path)

    assert sections == {400: "§ 400 Weak masculine."}


def test_ingester_updates_null_sections(catalog_db) -> None:
    engine, tmp_path = catalog_db
    markdown_path = tmp_path / "wright.md"
    markdown_path.write_text(
        "§ 334. Masculine a-stem paragraph.\n§ 335. Follow-on paragraph.\n",
        encoding="utf-8",
    )

    result = WrightSectionTextIngester().ingest(engine, markdown_path)

    assert isinstance(result, IngestResult)
    assert result.updated == 2
    assert result.skipped == 0
    assert result.coverage_percent > 0.0

    with engine.connect() as connection:
        row_334 = connection.execute(
            select(WrightSection.section_text).where(WrightSection.section_no == 334),
        ).scalar_one()
        row_335 = connection.execute(
            select(WrightSection.section_text).where(WrightSection.section_no == 335),
        ).scalar_one()

    assert row_334 == "§ 334. Masculine a-stem paragraph."
    assert row_335 == "§ 335. Follow-on paragraph."


def test_ingester_is_idempotent_without_force(catalog_db) -> None:
    engine, tmp_path = catalog_db
    markdown_path = tmp_path / "wright.md"
    markdown_path.write_text("§ 334. Masculine a-stem paragraph.\n", encoding="utf-8")
    ingester = WrightSectionTextIngester()

    first = ingester.ingest(engine, markdown_path)
    second = ingester.ingest(engine, markdown_path)

    assert first.updated == 1
    assert second.updated == 0
    assert second.skipped == 1


def test_ingester_force_overwrites_existing_text(catalog_db) -> None:
    engine, tmp_path = catalog_db
    markdown_path = tmp_path / "wright.md"
    ingester = WrightSectionTextIngester()

    markdown_path.write_text("§ 334. Original text.\n", encoding="utf-8")
    ingester.ingest(engine, markdown_path)

    markdown_path.write_text("§ 334. Replacement text.\n", encoding="utf-8")
    result = ingester.ingest(engine, markdown_path, force=True)

    assert result.updated == 1
    assert result.skipped == 0

    query_service = MorphologyCatalogQueryService(engine)
    assert query_service.lookup_wright_section_text(334) == "§ 334. Replacement text."


def test_ingest_result_counts_and_warnings(catalog_db) -> None:
    engine, tmp_path = catalog_db
    markdown_path = tmp_path / "wright.md"
    markdown_path.write_text(
        "§ 1. Extra markdown section not in catalog.\n§ 334. Catalog section with text.\n",
        encoding="utf-8",
    )

    result = WrightSectionTextIngester().ingest(engine, markdown_path)

    assert result.updated == 1
    assert result.markdown_not_in_catalog == (1,)
    assert 334 not in result.catalog_still_null
    assert result.coverage_percent < 100.0
    assert len(result.catalog_still_null) == 195
    assert any("not in catalog" in warning for warning in result.warnings)
    assert any("still missing text" in warning for warning in result.warnings)


def test_lookup_wright_section_text_returns_stored_value(catalog_db) -> None:
    engine, tmp_path = catalog_db
    markdown_path = tmp_path / "wright.md"
    markdown_path.write_text("§ 334. Stored paragraph text.\n", encoding="utf-8")
    WrightSectionTextIngester().ingest(engine, markdown_path)

    query_service = MorphologyCatalogQueryService(engine)

    assert query_service.lookup_wright_section_text(334) == "§ 334. Stored paragraph text."
    assert query_service.lookup_wright_section_text(9999) is None
