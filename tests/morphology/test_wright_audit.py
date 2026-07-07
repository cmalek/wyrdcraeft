"""
Tests for legacy Wright source auditing.

Phase D source contract:
    The audit compares bundled morphology source files to deterministic
    ``lemma_morph_classes`` assignments. Legacy Wright values come from the
    dictionary ``wright`` column in ``dict_adj-vb-part-num-adv-noun.txt`` and
    from ``manual_forms.txt`` via :func:`~wyrdcraeft.services.morphology.loaders.load_dictionary`
    and :func:`~wyrdcraeft.services.morphology.loaders.load_forms`. It does
    not read the dropped ``forms.wright`` SQL column.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import (
    LemmaMorphClass,
    MorphClass,
    MorphClassWrightSection,
)
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.paths import CANONICAL_DB_FILENAME
from wyrdcraeft.services.markup import normalize_morphology_title
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.wright_audit import WrightAuditService

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))


def _dictionary_line(  # noqa: PLR0913
    *,
    nid: int,
    title: str,
    wright: str,
    noun: int = 0,
    pronoun: int = 0,
    adjective: int = 0,
    verb: int = 0,
    participle: int = 0,
    adverb: int = 0,
    preposition: int = 0,
    conjunction: int = 0,
    interjection: int = 0,
    numeral: int = 0,
    vb_weak: int = 0,
    vb_strong: int = 0,
    vb_contracted: int = 0,
    vb_pretpres: int = 0,
    vb_anomalous: int = 0,
    vb_uncertain: int = 0,
    n_masc: int = 0,
    n_fem: int = 0,
    n_neut: int = 0,
    n_uncert: int = 0,
) -> str:
    """Build one dictionary fixture line with the expected 23 columns."""
    return "\t".join(
        str(value)
        for value in (
            nid,
            title,
            wright,
            noun,
            pronoun,
            adjective,
            verb,
            participle,
            adverb,
            preposition,
            conjunction,
            interjection,
            numeral,
            vb_weak,
            vb_strong,
            vb_contracted,
            vb_pretpres,
            vb_anomalous,
            vb_uncertain,
            n_masc,
            n_fem,
            n_neut,
            n_uncert,
        )
    )


def _manual_form_line(  # noqa: PLR0913
    *,
    bt: str,
    title: str,
    form: str,
    function: str,
    wright: str,
    wordclass: str,
) -> str:
    """Build one ``manual_forms.txt`` fixture line with the expected 16 columns."""
    parts = [
        bt,
        title,
        "",
        form,
        "",
        "",
        "",
        function,
        wright,
        "",
        "",
        wordclass,
        "",
        "",
        "",
        "",
    ]
    return "\t".join(parts)


def _para_vb_line(*, para_id: int, title: str, wright: str) -> str:
    """Build one ``para_vb.txt`` fixture line for malformed-token scanning."""
    return "\t".join(
        [
            str(para_id),
            title,
            "pp",
            "3",
            "0",
            "a",
            wright,
            "0",
            "If",
            "0",
            "0",
            "u",
            "0",
            "nn",
            "0",
            "ende",
        ]
    )


def _seed_catalog_db(tmp_path: Path) -> tuple[Path, object]:
    """Create a temporary canonical DB and seed the Wright catalog fixture."""
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
    return db_path, engine


def _seed_assignment(engine, *, title: str, pos: str, class_key: str) -> None:
    """Insert one deterministic lemma assignment row for audit testing."""
    normalized_title = normalize_morphology_title(title)
    with Session(engine) as session:
        morph_class_id = session.execute(
            select(MorphClass.id).where(MorphClass.class_key == class_key)
        ).scalar_one()
        pos_id = session.execute(
            select(PartOfSpeech.id).where(PartOfSpeech.code == pos)
        ).scalar_one()
        session.add(
            LemmaMorphClass(
                normalized_title=normalized_title,
                pos_id=pos_id,
                morph_class_id=morph_class_id,
                assignment_source="test_fixture",
                confidence=100,
            )
        )
        session.commit()


def _verb_class_key_for_section(engine, section_no: int) -> str:
    """Return one seeded verb class key linked to the requested Wright section."""
    with Session(engine) as session:
        class_key = session.execute(
            select(MorphClass.class_key)
            .join(
                MorphClassWrightSection,
                MorphClassWrightSection.morph_class_id == MorphClass.id,
            )
            .join(
                PartOfSpeech,
                PartOfSpeech.id == MorphClass.pos_id,
            )
            .where(
                PartOfSpeech.code == "verb",
                MorphClassWrightSection.section_no == section_no,
            )
            .limit(1)
        ).scalar_one()
    return str(class_key)


def _make_audit_source_dir(tmp_path: Path) -> Path:
    """Write minimal bundled-source fixtures for Phase 4 audit tests."""
    data_dir = tmp_path / "morphology-data"
    data_dir.mkdir()
    (data_dir / "dict_adj-vb-part-num-adv-noun.txt").write_text(
        "\n".join(
            [
                _dictionary_line(
                    nid=1,
                    title="contradictverb",
                    wright="334",
                    verb=1,
                    vb_strong=1,
                ),
                _dictionary_line(
                    nid=2,
                    title="unclassnoun",
                    wright="334",
                    noun=1,
                    n_masc=1,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "manual_forms.txt").write_text(
        _manual_form_line(
            bt="000001",
            title="emptynoun",
            form="emptynoun",
            function="Ns",
            wright="",
            wordclass="noun",
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "para_vb.txt").write_text(
        _para_vb_line(
            para_id=116,
            title="unnan",
            wright="Camp",
        )
        + "\n",
        encoding="utf-8",
    )
    return data_dir


def test_wright_audit_reports_all_phase4_categories(tmp_path: Path) -> None:
    """The audit should report malformed, contradictory, blank, and unclassified rows."""
    _db_path, engine = _seed_catalog_db(tmp_path)
    data_dir = _make_audit_source_dir(tmp_path)
    try:
        contradiction_class_key = _verb_class_key_for_section(engine, 490)
        _seed_assignment(
            engine,
            title="contradictverb",
            pos="verb",
            class_key=contradiction_class_key,
        )
        _seed_assignment(
            engine,
            title="emptynoun",
            pos="noun",
            class_key="noun.masculine.a_stem",
        )

        result = WrightAuditService(engine).audit(
            dictionary_path=data_dir / "dict_adj-vb-part-num-adv-noun.txt",
            manual_forms_path=data_dir / "manual_forms.txt",
            para_vb_path=data_dir / "para_vb.txt",
        )
    finally:
        engine.dispose()

    assert result.source_row_counts == {
        "dict_adj-vb-part-num-adv-noun.txt": 2,
        "manual_forms.txt": 1,
        "para_vb.txt": 1,
    }
    assert len(result.malformed_legacy_wright) == 1
    assert result.malformed_legacy_wright[0].row.source_file == "para_vb.txt"
    assert result.malformed_legacy_wright[0].invalid_tokens == ("camp",)

    assert len(result.contradictions) == 1
    assert result.contradictions[0].row.lemma == "contradictverb"
    assert result.contradictions[0].source_sections == (334,)

    assert len(result.unclassified) == 1
    assert result.unclassified[0].row.lemma == "unclassnoun"

    assert len(result.blank_legacy_but_classified) == 1
    assert result.blank_legacy_but_classified[0].row.lemma == "emptynoun"
    assert (
        result.blank_legacy_but_classified[0].assigned_class_key
        == "noun.masculine.a_stem"
    )


def test_wright_audit_reads_bundled_dict_source_not_forms_wright(
    tmp_path: Path,
) -> None:
    """Legacy Wright findings must come from bundled source files, not ``forms.wright``."""
    _db_path, engine = _seed_catalog_db(tmp_path)
    data_dir = tmp_path / "morphology-data"
    data_dir.mkdir()
    distinctive_wright = "334;335"
    (data_dir / "dict_adj-vb-part-num-adv-noun.txt").write_text(
        _dictionary_line(
            nid=99,
            title="dictsourceverb",
            wright=distinctive_wright,
            verb=1,
            vb_strong=1,
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "manual_forms.txt").write_text(
        _manual_form_line(
            bt="000099",
            title="manualsource",
            form="manualsource",
            function="Ns",
            wright="",
            wordclass="noun",
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "para_vb.txt").write_text("", encoding="utf-8")
    try:
        contradiction_class_key = _verb_class_key_for_section(engine, 490)
        _seed_assignment(
            engine,
            title="dictsourceverb",
            pos="verb",
            class_key=contradiction_class_key,
        )
        _seed_assignment(
            engine,
            title="manualsource",
            pos="noun",
            class_key="noun.masculine.a_stem",
        )

        result = WrightAuditService(engine).audit(
            dictionary_path=data_dir / "dict_adj-vb-part-num-adv-noun.txt",
            manual_forms_path=data_dir / "manual_forms.txt",
            para_vb_path=data_dir / "para_vb.txt",
        )
    finally:
        engine.dispose()

    assert len(result.contradictions) == 1
    contradiction = result.contradictions[0]
    assert contradiction.row.source_file == "dict_adj-vb-part-num-adv-noun.txt"
    assert contradiction.row.raw_legacy_wright == distinctive_wright
    assert contradiction.source_sections == (334, 335)

    assert len(result.blank_legacy_but_classified) == 1
    blank_issue = result.blank_legacy_but_classified[0]
    assert blank_issue.row.source_file == "manual_forms.txt"
    assert blank_issue.row.raw_legacy_wright == ""


def test_wright_audit_json_payload_schema_smoke(tmp_path: Path) -> None:
    """The audit payload should expose stable summary counts and full finding lists."""
    _db_path, engine = _seed_catalog_db(tmp_path)
    data_dir = _make_audit_source_dir(tmp_path)
    try:
        contradiction_class_key = _verb_class_key_for_section(engine, 490)
        _seed_assignment(
            engine,
            title="contradictverb",
            pos="verb",
            class_key=contradiction_class_key,
        )
        _seed_assignment(
            engine,
            title="emptynoun",
            pos="noun",
            class_key="noun.masculine.a_stem",
        )

        payload = WrightAuditService(engine).audit(
            dictionary_path=data_dir / "dict_adj-vb-part-num-adv-noun.txt",
            manual_forms_path=data_dir / "manual_forms.txt",
            para_vb_path=data_dir / "para_vb.txt",
        ).to_payload()
    finally:
        engine.dispose()

    assert payload["summary"]["source_rows_scanned"] == 4
    assert payload["summary"]["malformed_legacy_wright"] == 1
    assert payload["summary"]["contradictions"] == 1
    assert payload["summary"]["unclassified"] == 1
    assert payload["summary"]["blank_legacy_but_classified"] == 1
    assert payload["malformed_legacy_wright"][0]["row"]["source_file"] == "para_vb.txt"
    assert payload["contradictions"][0]["row"]["lemma"] == "contradictverb"
    assert payload["blank_legacy_but_classified"][0]["row"]["lemma"] == "emptynoun"


def test_morphology_audit_wright_cli_json_does_not_rewrite_source_files(
    runner,
    tmp_path: Path,
    isolated_morphology_app_data: Path,
) -> None:
    """CLI audit should emit JSON and leave the source files unchanged."""
    db_path, engine = _seed_catalog_db(tmp_path)
    data_dir = _make_audit_source_dir(tmp_path)
    default_db_path = isolated_morphology_app_data / CANONICAL_DB_FILENAME
    upgrade_canonical_db(default_db_path)
    try:
        contradiction_class_key = _verb_class_key_for_section(engine, 490)
        _seed_assignment(
            engine,
            title="contradictverb",
            pos="verb",
            class_key=contradiction_class_key,
        )
        _seed_assignment(
            engine,
            title="emptynoun",
            pos="noun",
            class_key="noun.masculine.a_stem",
        )

        before = {
            path.name: path.read_text(encoding="utf-8")
            for path in data_dir.iterdir()
            if path.is_file()
        }
        result = runner.invoke(
            cli,
            [
                "morphology",
                "audit-wright",
                "--json",
                "--data-dir",
                str(data_dir),
                "--db",
                str(db_path),
            ],
        )
        after = {
            path.name: path.read_text(encoding="utf-8")
            for path in data_dir.iterdir()
            if path.is_file()
        }
    finally:
        engine.dispose()

    assert result.exit_code == 0
    payload = json.loads(result.output[result.output.find("{") :])
    assert payload["summary"]["malformed_legacy_wright"] == 1
    assert payload["summary"]["contradictions"] == 1
    assert payload["summary"]["unclassified"] == 1
    assert payload["summary"]["blank_legacy_but_classified"] == 1
    assert before == after
