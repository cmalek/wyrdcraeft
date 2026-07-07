"""Tests for catalog-backed morph-class metadata in lexicon browse details."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.models.morph_catalog import LemmaMorphClass, MorphClass
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.models.sqlalchemy import BTEntry
from wyrdcraeft.services.dictionary.browse_query import (
    DictionaryBrowseQueryService,
    EntryDetails,
)
from wyrdcraeft.services.dictionary.browse_tui import _format_entry_details
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
            pos_id = session.scalar(
                select(PartOfSpeech.id).where(PartOfSpeech.code == catalog_pos),
            )
            assert pos_id is not None
            session.add(
                LemmaMorphClass(
                    normalized_title=normalized_title,
                    pos_id=pos_id,
                    morph_class_id=morph_class.id,
                    assignment_source=assignment_source,
                    confidence=100,
                )
            )
            session.commit()
    finally:
        engine.dispose()


def _insert_bt_entry(
    db_path: Path,
    *,
    norm_key: str,
    headword: str,
    normalized_title: str,
    catalog_pos: str,
) -> int:
    """
    Insert one minimal ``bt_entries`` row into a temporary lexicon test database.

    Args:
        db_path: Target lexicon test database path.

    Keyword Args:
        norm_key: Diacritic-stripped homograph merge key.
        headword: Display headword spelling.
        normalized_title: Macron/dot-preserving normalized headword.
        catalog_pos: Canonical ``parts_of_speech.code`` value.

    Returns:
        Surrogate ``bt_entries.id`` for the inserted row.

    """
    engine = create_engine(db_path)
    try:
        with Session(engine) as session:
            pos_id = session.scalar(
                select(PartOfSpeech.id).where(PartOfSpeech.code == catalog_pos),
            )
            assert pos_id is not None
            entry = BTEntry(
                norm_key=norm_key,
                headword=headword,
                normalized_title=normalized_title,
                pos_id=pos_id,
                genders_json="[]",
                etymology="",
                see_also_json="[]",
                source_line_nos_json="[]",
            )
            session.add(entry)
            session.commit()
            return int(entry.id)
    finally:
        engine.dispose()


def test_get_details_includes_catalog_morph_class_and_unclassified(
    lexicon_source_db: Path,
) -> None:
    _seed_catalog_assignment(
        lexicon_source_db,
        normalized_title="abbad",
        catalog_pos="noun",
        class_key="noun.masculine.a_stem",
    )
    noun_entry_id = _bt_entry_id(lexicon_source_db, norm_key="abbad")
    unclassified_entry_id = _insert_bt_entry(
        lexicon_source_db,
        norm_key="uncataloged",
        headword="uncataloged",
        normalized_title="uncataloged",
        catalog_pos="noun",
    )

    service = DictionaryBrowseQueryService(lexicon_source_db)
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
    _seed_catalog_assignment(
        lexicon_source_db,
        normalized_title="gl\u00e6d",
        catalog_pos="adjective",
        class_key="adj.strong.a_o_stem",
    )
    entry_id = _insert_bt_entry(
        lexicon_source_db,
        norm_key="glad",
        headword="gl\u00e6d",
        normalized_title="gl\u00e6d",
        catalog_pos="adjective",
    )

    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        details = service.get_details(entry_id)
        assert details is not None
        assert details.pos == "adjective"
        assert details.morph_class is not None
        assert details.morph_class.display_label == "strong a-/\u014d-stem adjective"
        assert details.morph_class.is_unclassified is False
    finally:
        service.close()


def _bt_entry_id(db_path: Path, *, norm_key: str) -> int:
    """Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions."""
    engine = create_engine(db_path)
    try:
        with Session(engine) as session:
            entry_id = session.scalar(
                select(BTEntry.id).where(BTEntry.norm_key == norm_key),
            )
            assert entry_id is not None
            return int(entry_id)
    finally:
        engine.dispose()


def test_format_entry_details_shows_unclassified_for_unmappable_pos() -> None:
    details = EntryDetails(
        entry_id=1,
        headword="and",
        variants=[],
        pos="conjunction",
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


def test_format_entry_details_omits_plain_wright_line_for_selectable_sections() -> None:
    details = EntryDetails(
        entry_id=1,
        headword="abbad",
        variants=[],
        pos="noun",
        class_summary=[],
        genders=["m"],
        persons=[],
        numbers=[],
        summary_sense="an abbot; abbot",
        senses=[],
        etymology="",
        morphology_groups=[],
        declension_paradigm="",
        morph_class=LemmaMorphClassSummary(
            display_label="noun, a-stem",
            assignment_source="paradigm",
            wright_sections=(334, 335),
            is_unclassified=False,
        ),
    )

    rendered = _format_entry_details(details)

    assert "Morph class: noun, a-stem" in rendered
    assert "Provenance: paradigm" in rendered
    assert "Wright \u00a7:" not in rendered
