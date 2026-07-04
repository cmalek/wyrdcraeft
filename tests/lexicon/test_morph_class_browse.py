"""Tests for catalog-backed morph-class metadata in lexicon browse details."""

from __future__ import annotations

import sqlite3
from importlib.resources import files
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.models.morph_catalog import LemmaMorphClass, MorphClass
from wyrdcraeft.services.lexicon.build import rebuild_lexicon
from wyrdcraeft.services.lexicon.query import EntryDetails, LexiconQueryService
from wyrdcraeft.services.lexicon.tui import _format_entry_details
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.query import LemmaMorphClassSummary

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))


def _seed_catalog_assignment(
    db_path: Path,
    *,
    normalized_title: str,
    catalog_pos: str,
    class_key: str,
    assignment_source: str = "paradigm",
) -> None:
    """Seed one catalog assignment row into a temporary lexicon test database."""
    engine = create_engine(db_path)
    try:
        MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
        with Session(engine) as session:
            morph_class = session.scalar(
                select(MorphClass).where(MorphClass.class_key == class_key),
            )
            assert morph_class is not None
            session.add(
                LemmaMorphClass(
                    normalized_title=normalized_title,
                    pos=catalog_pos,
                    morph_class_id=morph_class.id,
                    assignment_source=assignment_source,
                    confidence=100,
                )
            )
            session.commit()
    finally:
        engine.dispose()


def test_get_details_includes_catalog_morph_class_and_unclassified(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)
    _seed_catalog_assignment(
        lexicon_source_db,
        normalized_title="abbad",
        catalog_pos="noun",
        class_key="noun.masculine.a_stem",
    )
    with sqlite3.connect(lexicon_source_db) as connection:
        noun_entry_id = int(
            connection.execute(
                "SELECT entry_id FROM lexicon_entries WHERE norm_key = ?",
                ("abbad",),
            ).fetchone()[0]
        )
        unclassified_entry_id = int(
            connection.execute("SELECT COALESCE(MAX(entry_id), 0) + 1 FROM lexicon_entries")
            .fetchone()[0]
        )
        connection.execute(
            """
            INSERT INTO lexicon_entries (
                entry_id,
                norm_key,
                pos,
                headword,
                summary_sense,
                etymology,
                variants_json,
                genders_json,
                senses_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                unclassified_entry_id,
                "uncataloged",
                "noun",
                "uncataloged",
                "an uncataloged noun",
                "",
                "[]",
                "[]",
                "[]",
            ),
        )
        connection.commit()

    service = LexiconQueryService(lexicon_source_db)
    try:
        noun_details = service.get_details(noun_entry_id)
        assert noun_details is not None
        assert noun_details.morph_class is not None
        assert noun_details.morph_class.display_label == "noun, a-stem"
        assert noun_details.morph_class.assignment_source == "paradigm"
        assert noun_details.morph_class.wright_sections == (
            334,
            335,
            336,
            337,
            338,
            339,
            340,
            341,
        )
        assert noun_details.morph_class.is_unclassified is False

        unclassified_details = service.get_details(unclassified_entry_id)
        assert unclassified_details is not None
        assert unclassified_details.morph_class is not None
        assert unclassified_details.morph_class.display_label == "Unclassified"
        assert unclassified_details.morph_class.assignment_source == ""
        assert unclassified_details.morph_class.wright_sections == ()
        assert unclassified_details.morph_class.is_unclassified is True
    finally:
        service.close()


def test_get_details_maps_adj_to_catalog_adjective_lookup(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)
    _seed_catalog_assignment(
        lexicon_source_db,
        normalized_title="gl\u00e6d",
        catalog_pos="adjective",
        class_key="adj.strong.a_o_stem",
    )
    with sqlite3.connect(lexicon_source_db) as connection:
        entry_id = int(
            connection.execute("SELECT COALESCE(MAX(entry_id), 0) + 1 FROM lexicon_entries")
            .fetchone()[0]
        )
        connection.execute(
            """
            INSERT INTO lexicon_entries (
                entry_id,
                norm_key,
                pos,
                headword,
                summary_sense,
                etymology,
                variants_json,
                genders_json,
                senses_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                "glad",
                "adj",
                "gl\u00e6d",
                "glad",
                "",
                "[]",
                "[]",
                "[]",
            ),
        )
        connection.commit()

    service = LexiconQueryService(lexicon_source_db)
    try:
        details = service.get_details(entry_id)
        assert details is not None
        assert details.pos == "adj"
        assert details.morph_class is not None
        assert details.morph_class.display_label == "strong a-/\u014d-stem adjective"
        assert details.morph_class.is_unclassified is False
    finally:
        service.close()


def test_format_entry_details_shows_unclassified_for_unmappable_pos() -> None:
    details = EntryDetails(
        entry_id=1,
        headword="and",
        variants=[],
        pos="conj",
        class_summary=[],
        genders=[],
        persons=[],
        numbers=[],
        summary_sense="and",
        senses=[],
        etymology="",
        morphology_groups=[],
        declension_paradigm="",
        morph_class=None,
    )

    rendered = _format_entry_details(details)

    assert "Morph class: Unclassified" in rendered
    assert "Provenance:" not in rendered
    assert "Wright \u00a7:" not in rendered


def test_format_entry_details_shows_unclassified_for_missing_assignment() -> None:
    details = EntryDetails(
        entry_id=1,
        headword="uncataloged",
        variants=[],
        pos="noun",
        class_summary=[],
        genders=[],
        persons=[],
        numbers=[],
        summary_sense="an uncataloged noun",
        senses=[],
        etymology="",
        morphology_groups=[],
        declension_paradigm="",
        morph_class=LemmaMorphClassSummary(
            display_label="Unclassified",
            assignment_source="",
            wright_sections=(),
            is_unclassified=True,
        ),
    )

    rendered = _format_entry_details(details)

    assert "Morph class: Unclassified" in rendered
    assert "Provenance:" not in rendered
    assert "Wright \u00a7:" not in rendered
