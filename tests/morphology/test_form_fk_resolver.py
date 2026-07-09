"""Tests for morphology form foreign-key resolution."""

from __future__ import annotations

import json
import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from wyrdcraeft.cli import (
    cli as _cli,  # noqa: F401 — load CLI before generation modules
)
from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import LemmaMorphClass, MorphClass
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)
from wyrdcraeft.services.morphology.generation.form_fk_resolver import (
    FormFkResolver,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.morphology

CATALOG_FIXTURE = Path(
    str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")),
)


@pytest.fixture
def resolver_db(tmp_path: Path) -> Iterator[tuple[Path, sqlite3.Connection]]:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    connection = sqlite3.connect(db_path)
    pos_map = ensure_parts_of_speech(connection)
    ensure_inflection_codes(connection, pos_map)
    connection.commit()
    yield db_path, connection
    connection.close()


def _insert_bt_entry(
    connection: sqlite3.Connection,
    *,
    entry_id: int,
    normalized_title: str,
    pos_code: str,
    norm_key: str | None = None,
) -> None:
    pos_id = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = ?",
        (pos_code,),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO bt_entries (
            id,
            norm_key,
            headword,
            normalized_title,
            pos_id,
            genders_json,
            etymology,
            see_also_json,
            source_line_nos_json,
            entry_order
        ) VALUES (?, ?, ?, ?, ?, '[]', '', '[]', '[]', ?)
        """,
        (
            entry_id,
            norm_key or normalized_title,
            normalized_title,
            normalized_title,
            pos_id,
            entry_id,
        ),
    )


def _insert_bt_variant(
    connection: sqlite3.Connection,
    *,
    entry_id: int,
    normalized_title: str,
    spelling: str,
) -> None:
    connection.execute(
        """
        INSERT INTO bt_variants (
            entry_id,
            spelling_raw,
            spelling_macronized,
            normalized_title
        ) VALUES (?, ?, ?, ?)
        """,
        (entry_id, spelling, spelling, normalized_title),
    )


def _insert_lemma_assignment(
    db_path: Path,
    connection: sqlite3.Connection,
    *,
    normalized_title: str,
    pos_code: str,
    morph_class_key: str,
) -> int:
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(CATALOG_FIXTURE)
    engine.dispose()

    pos_id = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = ?",
        (pos_code,),
    ).fetchone()[0]
    morph_class_id = connection.execute(
        "SELECT id FROM morph_classes WHERE class_key = ?",
        (morph_class_key,),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO lemma_morph_classes (
            normalized_title,
            pos_id,
            morph_class_id
        ) VALUES (?, ?, ?)
        """,
        (normalized_title, pos_id, morph_class_id),
    )
    connection.commit()
    return int(morph_class_id)


def test_resolve_wordclass_id_maps_generator_wordclass(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    _, connection = resolver_db
    resolver = FormFkResolver(connection=connection)
    noun_id = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = 'noun'",
    ).fetchone()[0]

    assert resolver.resolve_wordclass_id("noun") == noun_id
    assert resolver.resolve_wordclass_id("  NOUN  ") == noun_id
    assert resolver.resolve_wordclass_id("particle") is None


def test_resolve_inflection_code_id_empty_function_uses_unknown_seed_row(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    _, connection = resolver_db
    resolver = FormFkResolver(connection=connection)
    unknown_code_id = connection.execute(
        "SELECT id FROM inflection_codes WHERE code = ''",
    ).fetchone()[0]

    assert resolver.resolve_inflection_code_id("", "noun") == unknown_code_id
    assert resolver.resolve_inflection_code_id("   ", "verb") == unknown_code_id


def test_resolve_inflection_code_id_known_function(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    _, connection = resolver_db
    resolver = FormFkResolver(connection=connection)
    ps_in_sg1_id = connection.execute(
        "SELECT id FROM inflection_codes WHERE code = 'PsInSg1'",
    ).fetchone()[0]

    assert resolver.resolve_inflection_code_id("PsInSg1", "verb") == ps_in_sg1_id
    assert resolver.resolve_inflection_code_id("missing", "verb") is None


def test_resolve_entry_id_returns_known_lemma(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    _, connection = resolver_db
    _insert_bt_entry(
        connection,
        entry_id=42,
        normalized_title="st\u0101n",
        pos_code="noun",
    )
    connection.commit()
    resolver = FormFkResolver(connection=connection)

    assert resolver.resolve_entry_id("st\u0101n", "noun") == 42


def test_resolve_entry_id_returns_none_for_ambiguous_homograph(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    _, connection = resolver_db
    _insert_bt_entry(
        connection,
        entry_id=1,
        normalized_title="alpha",
        pos_code="noun",
    )
    _insert_bt_entry(
        connection,
        entry_id=2,
        normalized_title="beta",
        pos_code="noun",
    )
    _insert_bt_variant(
        connection,
        entry_id=1,
        normalized_title="alias",
        spelling="alias",
    )
    _insert_bt_variant(
        connection,
        entry_id=2,
        normalized_title="alias",
        spelling="alias",
    )
    connection.commit()
    resolver = FormFkResolver(connection=connection)

    assert resolver.resolve_entry_id("alias", "noun") is None


def test_resolve_morph_class_id_returns_assigned_lemma(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = resolver_db
    expected_id = _insert_lemma_assignment(
        db_path,
        connection,
        normalized_title="helpan",
        pos_code="verb",
        morph_class_key="verb.strong_3.liquid_cluster",
    )
    resolver = FormFkResolver(connection=connection)

    assert resolver.resolve_morph_class_id("helpan", "verb", "If") == expected_id


def test_resolve_morph_class_id_verbal_participle_uses_verb_assignment(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = resolver_db
    expected_id = _insert_lemma_assignment(
        db_path,
        connection,
        normalized_title="helpan",
        pos_code="verb",
        morph_class_key="verb.strong_3.liquid_cluster",
    )
    resolver = FormFkResolver(connection=connection)

    assert resolver.resolve_morph_class_id("helpan", "verb", "PsPt") == expected_id
    assert resolver.resolve_morph_class_id("helpan", "verb", "PaPt") == expected_id


def test_resolve_morph_class_id_strong_adjective_maps_to_strong_catalog_class(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = resolver_db
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(CATALOG_FIXTURE)
    engine.dispose()
    connection.commit()
    resolver = FormFkResolver(connection=connection)

    morph_class_id = resolver.resolve_morph_class_id(
        "blind",
        "adjective",
        "SgMaSt",
        class1="strong",
    )
    assert morph_class_id is not None
    class_key, features_json = connection.execute(
        """
        SELECT class_key, features_json
        FROM morph_classes
        WHERE id = ?
        """,
        (morph_class_id,),
    ).fetchone()
    features = json.loads(features_json)

    assert class_key == "adj.strong.a_o_stem"
    assert features.get("strength") == "strong"


def test_resolve_morph_class_id_returns_none_when_unassigned(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = resolver_db
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(CATALOG_FIXTURE)
    engine.dispose()
    connection.commit()
    resolver = FormFkResolver(connection=connection)

    assert resolver.resolve_morph_class_id("unmappednoun", "noun", "SgMaNo") is None


def test_preloaded_maps_without_connection() -> None:
    join_index = NormalizedTitleJoinIndex.from_entry_variant_rows(
        [(7, "abbad", "noun")],
        [],
    )
    resolver = FormFkResolver(
        join_index=join_index,
        inflection_code_ids={"": 99, "PsInSg1": 12},
        morph_class_ids={("helpan", 3): 55},
        morph_class_ids_by_key={"adj.weak": 88},
        pos_ids_by_code={"noun": 1, "verb": 3},
    )

    assert resolver.resolve_wordclass_id("noun") == 1
    assert resolver.resolve_inflection_code_id("", "noun") == 99
    assert resolver.resolve_entry_id("abbad", "noun") == 7
    assert resolver.resolve_morph_class_id("helpan", "verb", "PsPt") == 55


def test_catalog_loader_assignment_visible_via_sqlalchemy(
    resolver_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = resolver_db
    _insert_lemma_assignment(
        db_path,
        connection,
        normalized_title="helpan",
        pos_code="verb",
        morph_class_key="verb.strong_3.liquid_cluster",
    )
    engine = create_engine(db_path)
    with engine.connect() as conn:
        row = conn.execute(
            select(LemmaMorphClass.morph_class_id, MorphClass.class_key)
            .join(MorphClass, MorphClass.id == LemmaMorphClass.morph_class_id)
            .join(PartOfSpeech, PartOfSpeech.id == LemmaMorphClass.pos_id)
            .where(
                LemmaMorphClass.normalized_title == "helpan",
                PartOfSpeech.code == "verb",
            ),
        ).one()
    engine.dispose()

    assert row.class_key == "verb.strong_3.liquid_cluster"
