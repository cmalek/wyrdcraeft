from __future__ import annotations

import json
from pathlib import Path

import click

from wyrdcraeft.services.morphology.generation.query import (
    MorphologyQueryService,
)


@click.group(
    name="morphology",
    help="Old English morphology query commands.",
)
def morphology_group() -> None:
    """Morphology command group."""


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
