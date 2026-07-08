"""CLI smoke tests for Bosworth-Toller dictionary commands."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.services.dictionary.resources import (
    default_bt_abbreviations_path,
    default_bt_source_path,
    default_wright_source_path,
)

_SAMPLE_LINES = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _morphology_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "wyrdcraeft" / "etc" / "morphology"


def _subset_dictionary() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "fixtures"
        / "morphology"
        / "test_dict.txt"
    )


def _pos_id(connection: sqlite3.Connection, code: str) -> int:
    row = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = ?",
        (code,),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _insert_form(
    connection: sqlite3.Connection,
    *,
    normalized_title: str,
    wordclass_code: str,
    entry_id: int | None = None,
) -> None:
    token = normalized_title
    connection.execute(
        """
        INSERT INTO forms (
            counter,
            formi,
            BT,
            title,
            normalized_title,
            stem,
            form,
            formParts,
            var,
            probability,
            comment,
            bt_key,
            title_key,
            stem_key,
            form_key,
            formi_key,
            wordclass_id,
            entry_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            token,
            token,
            token,
            normalized_title,
            token,
            token,
            "",
            "0",
            "0",
            "",
            token,
            token,
            token,
            token,
            token,
            _pos_id(connection, wordclass_code),
            entry_id,
        ),
    )


def _fetch_form_entry_id(connection: sqlite3.Connection, *, normalized_title: str) -> int | None:
    row = connection.execute(
        "SELECT entry_id FROM forms WHERE normalized_title = ?",
        (normalized_title,),
    ).fetchone()
    assert row is not None
    return None if row[0] is None else int(row[0])


def _fetch_entry_id(connection: sqlite3.Connection, *, normalized_title: str) -> int:
    row = connection.execute(
        "SELECT id FROM bt_entries WHERE normalized_title = ?",
        (normalized_title,),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _build_unified_source_db(
    runner,
    target_db: Path,
    *,
    extra_args: list[str] | None = None,
):
    """Bootstrap canonical DB with dictionary + limited morphology generation."""
    target_db.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "dictionary",
        "build",
        "--source",
        str(_SAMPLE_LINES),
        "--data-dir",
        str(_morphology_data_dir()),
        "--dictionary",
        str(_subset_dictionary()),
        "--limit",
        "50",
        "--output",
        str(target_db.parent / "morphology.tsv"),
    ]
    if extra_args:
        args.extend(extra_args)
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    return result


def test_dictionary_group_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "--help"])
    assert result.exit_code == 0
    assert "build" in result.output
    assert "clean-headwords" in result.output
    assert "query" in result.output
    assert "browse" in result.output
    assert "ingest-wright-text" in result.output
    assert "audit-wright" in result.output
    assert "generate-reference-snapshots" in result.output


def test_dictionary_clean_headwords_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "clean-headwords", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output


def test_dictionary_generate_reference_snapshots_help(runner) -> None:
    result = runner.invoke(
        cli,
        ["dictionary", "generate-reference-snapshots", "--help"],
    )
    assert result.exit_code == 0
    assert "--include-full" in result.output


def test_dictionary_query_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "query", "--help"])
    assert result.exit_code == 0
    assert "--pos" in result.output
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
    assert "--standalone" not in result.output
    assert "--json-output" in result.output


def test_dictionary_browse_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "browse", "--help"])
    assert result.exit_code == 0
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output


def test_lexicon_group_removed(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "--help"])
    assert result.exit_code != 0
    assert "No such command 'lexicon'" in result.output


def test_lexicon_build_command_moved_to_dictionary(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "build", "--help"])
    assert result.exit_code != 0
    assert "No such command 'lexicon'" in result.output


def test_dictionary_ingest_wright_text_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "ingest-wright-text", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "--force" in result.output


def test_dictionary_audit_wright_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "audit-wright", "--help"])
    assert result.exit_code == 0
    assert "--json" in result.output
    assert "--data-dir" in result.output
    assert "--db" in result.output


def test_dictionary_index_bt_command_is_gone(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "index-bt", "--help"])
    assert result.exit_code != 0
    assert "No such command 'index-bt'" in result.output


def test_dictionary_query_smoke(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_unified_source_db(runner, isolated_morphology_index_db)
    assert isolated_morphology_index_db.exists()

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "query",
            "abbad",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    assert "No dictionary entries found" not in lookup_result.output
    assert "Lemma:" in lookup_result.output
    assert "POS: noun" in lookup_result.output
    assert "Senses:" in lookup_result.output
    assert "Variants:" in lookup_result.output


def test_dictionary_query_json_output(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_unified_source_db(runner, isolated_morphology_index_db)
    assert isolated_morphology_index_db.exists()

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "query",
            "abbod",
            "--json-output",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    json_start = next(
        index for index, line in enumerate(lookup_result.output.splitlines()) if line.startswith("[")
    )
    payload = json.loads("\n".join(lookup_result.output.splitlines()[json_start:]))
    assert payload[0]["norm_key"] == "abbad"
    assert payload[0]["pos"] == "noun"


def test_dictionary_build_default_source_is_cwd_independent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = default_bt_source_path()
    assert source.is_file()
    assert source.name == "oe_bt.txt"
    assert "etc/dictionary" in source.as_posix()

    abbreviations = default_bt_abbreviations_path()
    assert abbreviations.is_file()
    assert abbreviations.name == "bosworth_and_toller_abbreviations.json"

    wright = default_wright_source_path()
    assert wright.is_file()
    assert wright.name == "wright.md"

    monkeypatch.chdir(tmp_path)
    assert default_bt_source_path().is_file()


def test_dictionary_build_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "build", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
    assert "--standalone" not in result.output
    assert "--report" in result.output
    assert "--with-morphology" in result.output
    assert "--data-dir" in result.output
    assert "--dictionary" in result.output
    assert "--manual-forms" in result.output
    assert "--verbal-paradigms" in result.output
    assert "--prefixes" in result.output
    assert "--output" in result.output
    assert "--limit" in result.output
    assert "--progress-every INTEGER" in result.output
    assert "--enable-r-stem-nouns" in result.output
    assert "--full / --no-full" in result.output
    assert "--profile" in result.output
    assert "--refresh-catalog" in result.output
    assert "wyrdcraeft/etc/dictionary/oe_bt.txt" in result.output


def test_dictionary_build_smoke(
    runner,
    isolated_morphology_index_db: Path,
    temp_dir,
) -> None:
    report_path = temp_dir / "report.json"
    result = _build_unified_source_db(
        runner,
        isolated_morphology_index_db,
        extra_args=["--report", str(report_path)],
    )
    assert "Dictionary index complete." in result.output
    assert f"index_db={isolated_morphology_index_db.resolve()}" in result.output
    assert isolated_morphology_index_db.is_file()
    assert report_path.is_file()
    assert '"pos_counts"' in report_path.read_text(encoding="utf-8")
    assert "bt_entries_written=" in result.output
    assert "forms_regenerated=" in result.output
    assert "entry_ids_linked=" in result.output
    assert "pos_inferred=" in result.output


def test_dictionary_build_bootstraps_empty_app_data_dir(
    runner,
    isolated_morphology_app_data: Path,
) -> None:
    index_db = isolated_morphology_app_data / "wyrdcraeft.sqlite3"
    assert not index_db.exists()

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--limit",
            "20",
        ],
    )

    assert result.exit_code == 0, result.output
    assert index_db.exists()
    assert "Dictionary index complete." in result.output
    assert "forms_regenerated=True" in result.output


def test_dictionary_build_runs_morphology_when_forms_table_is_empty(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    upgrade_canonical_db(isolated_morphology_index_db)

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--limit",
            "20",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "forms_regenerated=True" in result.output
    with sqlite3.connect(isolated_morphology_index_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0] > 0


def test_dictionary_build_skips_morphology_when_forms_exist_unless_requested(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    upgrade_canonical_db(isolated_morphology_index_db)
    with sqlite3.connect(isolated_morphology_index_db) as connection:
        _insert_form(
            connection,
            normalized_title="abbad",
            wordclass_code="noun",
        )
        connection.commit()

    skipped = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
            "--limit",
            "1",
            "--full",
        ],
    )
    assert skipped.exit_code == 0, skipped.output
    assert "forms_regenerated=False" in skipped.output

    rebuilt = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
            "--with-morphology",
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--limit",
            "20",
        ],
    )
    assert rebuilt.exit_code == 0, rebuilt.output
    assert "forms_regenerated=True" in rebuilt.output


def test_dictionary_build_relinks_forms_after_dictionary_rebuild(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    upgrade_canonical_db(isolated_morphology_index_db)
    with sqlite3.connect(isolated_morphology_index_db) as connection:
        _insert_form(
            connection,
            normalized_title="abbad",
            wordclass_code="noun",
            entry_id=999,
        )
        connection.commit()

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "entry_ids_linked=" in result.output
    with sqlite3.connect(isolated_morphology_index_db) as connection:
        linked_entry_id = _fetch_form_entry_id(connection, normalized_title="abbad")
        current_entry_id = _fetch_entry_id(connection, normalized_title="abbad")
    assert linked_entry_id == current_entry_id
    assert linked_entry_id != 999


def test_dictionary_query_morphology_default(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_unified_source_db(runner, isolated_morphology_index_db)
    assert isolated_morphology_index_db.exists()

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "query",
            "abbod",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    assert "No dictionary entries found" not in lookup_result.output
    assert "Lemma:" in lookup_result.output
    assert "POS:" in lookup_result.output


def test_dictionary_query_missing_morphology_db_fails(
    runner,
    isolated_morphology_app_data: Path,
) -> None:
    assert not (isolated_morphology_app_data / "wyrdcraeft.sqlite3").exists()

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "query",
            "abbod",
        ],
    )

    assert result.exit_code != 0
    assert "missing required source tables: bt_entries, bt_senses, bt_variants" in result.output
    assert "wyrdcraeft dictionary build" in result.output
    assert "wyrdcraeft morphology build" not in result.output
