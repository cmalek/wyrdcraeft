from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import click

from wyrdcraeft.services.morphology.dictionary_cleanup import (
    MorphologyDictionaryCleaner,
)
from wyrdcraeft.services.morphology.generation.query import (
    MorphologyQueryService,
)


@click.group(
    name="morphology",
    help="Old English morphology query commands.",
)
def morphology_group() -> None:
    """Morphology command group."""


def _default_morphology_data_dir() -> Path:
    """
    Resolve the packaged default morphology data directory.

    Returns:
        Directory containing bundled morphology source files.

    """
    return Path(str(resources.files("wyrdcraeft").joinpath("etc/morphology")))


def _format_dictionary_join_text(entry: dict[str, object]) -> str:
    """
    Render one dictionary join entry as human-readable text.

    Args:
        entry: Dictionary join payload from ``dictionary_join_entry_to_dict``.

    Returns:
        Multi-line text block without attestations.

    """
    headword = str(entry["headword"])
    pos = str(entry["pos"])
    genders = entry.get("genders", [])
    gender_text = ""
    if isinstance(genders, list) and genders:
        gender_text = f"  Gender: {', '.join(str(value) for value in genders)}"

    lines = [f"Dictionary: {headword}", f"POS: {pos}{gender_text}", "Senses:"]
    senses = entry.get("senses", [])
    if isinstance(senses, list):
        for sense in senses:
            if not isinstance(sense, dict):
                continue
            label = str(sense.get("sense_label", "")).strip()
            gloss = str(sense.get("gloss_en", "")).strip()
            prefix = f"  {label}. " if label and not label.endswith(".") else "  "
            if label and label.endswith("."):
                prefix = f"  {label} "
            lines.append(f"{prefix}{gloss}".rstrip())

    etymology = str(entry.get("etymology", "")).strip()
    if etymology:
        lines.append(f"Etymology: {etymology}")

    return "\n".join(lines)


@morphology_group.command(
    name="clean-dictionary",
    help=(
        "Backup, lowercase column-2 lemma titles, and deduplicate the "
        "morphology dictionary TSV."
    ),
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory containing bundled morphology source files.",
)
@click.option(
    "--dictionary",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Explicit path to dict_adj-vb-part-num-adv-noun.txt.",
)
def clean_dictionary(
    data_dir: Path | None,
    dictionary: Path | None,
) -> None:
    """
    Normalize and deduplicate the morphology dictionary source file.

    Note:
        Cleanup follows morphology source conventions from
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, it lowercases all-uppercase lemma titles in column 2 and
        removes rows that duplicate all other columns. Part-of-speech scope:
        ``cross-PoS``.

    Args:
        data_dir: Optional base directory for bundled morphology source files.
        dictionary: Optional explicit dictionary TSV path.

    Side Effects:
        Creates a timestamped backup and overwrites the dictionary source file.

    Raises:
        click.ClickException: The dictionary file is missing or cleanup fails.

    """
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    dictionary_path = dictionary or (
        resolved_data_dir / "dict_adj-vb-part-num-adv-noun.txt"
    )
    if not dictionary_path.exists():
        msg = (
            f"Missing dictionary file: {dictionary_path}. "
            "Provide an explicit path via --dictionary or --data-dir."
        )
        raise click.ClickException(msg)

    try:
        result = MorphologyDictionaryCleaner(dictionary_path).run()
    except OSError as exc:
        msg = f"Failed to clean morphology dictionary {dictionary_path}: {exc}"
        raise click.ClickException(msg) from exc

    click.echo(
        "\n".join(
            [
                "Morphology dictionary cleanup complete.",
                f"dictionary={dictionary_path}",
                f"backup={result.backup_path}",
                f"rows_read={result.rows_read}",
                f"lowercase_changes={result.lowercase_changes}",
                f"duplicates_removed={result.duplicates_removed}",
                f"rows_written={result.rows_written}",
            ]
        )
    )


@morphology_group.command(
    name="query",
    help="Query generated morphology rows from a SQLite index.",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to morphology SQLite index database.",
)
@click.option("--lemma", default=None, help="Lookup rows by lemma/root token.")
@click.option(
    "--form",
    "surface_form",
    default=None,
    help="Lookup rows by surface form.",
)
@click.option("--limit", default=200, type=int, show_default=True, help="Maximum rows.")
@click.option(
    "--json-output/--no-json-output",
    default=False,
    show_default=True,
    help="Render query output as JSON.",
)
@click.option(
    "--with-dictionary",
    is_flag=True,
    default=False,
    help="Attach matching Bosworth-Toller dictionary entries to the output.",
)
@click.option(
    "--dictionary-db",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "Dictionary SQLite index path (defaults to sibling dictionary.sqlite3 "
        "or bt_* tables inside the morphology database)."
    ),
)
def query(  # noqa: PLR0913
    db_path: Path,
    lemma: str | None,
    surface_form: str | None,
    limit: int,
    json_output: bool,
    with_dictionary: bool,
    dictionary_db: Path | None,
) -> None:
    """
    Query morphology rows by lemma or surface form.

    Note:
        Query keys are normalized in line with morphology conventions from
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this searches inflected forms across all Parts of Speech.

    Args:
        db_path: SQLite morphology index path.
        lemma: Optional lemma/root lookup key.
        surface_form: Optional surface form lookup key.
        limit: Maximum number of rows to emit.
        json_output: When true, print JSON instead of tab-separated rows.
        with_dictionary: When true, attach Bosworth-Toller dictionary entries.
        dictionary_db: Optional explicit dictionary SQLite index path.

    Side Effects:
        Reads the SQLite morphology index and writes rows to stdout.

    Raises:
        click.ClickException: Neither or both lookup modes are requested.

    """
    if (lemma is None) == (surface_form is None):
        msg = "Provide exactly one of --lemma or --form."
        raise click.ClickException(msg)

    query_service = MorphologyQueryService(db_path)
    try:
        if lemma is not None:
            rows = query_service.lookup_by_lemma(lemma, limit=max(1, limit))
            lookup_token = lemma
        else:
            rows = query_service.lookup_by_form(surface_form or "", limit=max(1, limit))
            lookup_token = rows[0].BT if rows else (surface_form or "")

        dictionary_entries: list[dict[str, object]] = []
        if with_dictionary:
            dictionary_entries = query_service.lookup_dictionary_entries(
                lookup_token,
                rows,
                dictionary_db_path=dictionary_db,
            )
    finally:
        query_service.close()

    if json_output:
        if with_dictionary:
            payload: dict[str, object] = {
                "forms": [row.model_dump() for row in rows],
                "dictionary": dictionary_entries,
            }
            click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            click.echo(
                json.dumps(
                    [row.model_dump() for row in rows],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    for row in rows:
        click.echo(
            f"{row.counter}\t{row.form}\t{row.BT}\t{row.function}\t{row.probability}"
        )

    if with_dictionary and dictionary_entries:
        click.echo("")
        for index, entry in enumerate(dictionary_entries):
            if index:
                click.echo("")
            click.echo(_format_dictionary_join_text(entry))
