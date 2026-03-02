from __future__ import annotations

import json
from pathlib import Path

import click
from pydantic import ValidationError
from rich.prompt import Prompt

from ..models import MacronIndexPayload
from ..services.markup import (
    DEFAULT_MACRON_INDEX_PATH,
    normalize_old_english,
)
from .utils import print_info


def _load_macron_index_payload(index_path: Path) -> MacronIndexPayload:
    """
    Load and validate the macron index payload from disk.

    Args:
        index_path: Path to index JSON file.

    Raises:
        click.ClickException: If the file is missing, unreadable, or invalid.

    Returns:
        Parsed macron index payload.

    """
    if not index_path.exists():
        msg = f"Macron index file not found: {index_path}"
        raise click.ClickException(msg)

    try:
        raw_payload = index_path.read_text(encoding="utf-8")
    except OSError as e:
        msg = f"Failed to read macron index file {index_path}: {e}"
        raise click.ClickException(msg) from e

    try:
        return MacronIndexPayload.model_validate_json(raw_payload)
    except ValidationError as e:
        msg = (
            f"Invalid macron index payload at {index_path}: "
            f"{e.errors()[0]['msg'] if e.errors() else e}"
        )
        raise click.ClickException(msg) from e


def _write_macron_index_payload(index_path: Path, payload: MacronIndexPayload) -> None:
    """
    Write macron index payload atomically to disk.

    Args:
        index_path: Destination JSON path.
        payload: Payload to serialize.

    Raises:
        click.ClickException: If write fails.

    """
    meta = dict(payload.meta)
    meta["unique_count"] = len(payload.unique)
    meta["ambiguous_count"] = len(payload.ambiguous)

    serialized = payload.model_dump(mode="json")
    serialized["meta"] = meta
    serialized["ambiguous_completed"] = sorted(payload.ambiguous_completed)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = index_path.with_suffix(f"{index_path.suffix}.tmp")
    try:
        temp_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(index_path)
    except OSError as e:
        msg = f"Failed to write macron index file {index_path}: {e}"
        raise click.ClickException(msg) from e


@click.group(name="diacritic")
def diacritic_group() -> None:
    """
    Diacritic index maintenance commands.
    """


@diacritic_group.command(
    name="add",
    help="Add a normalized/macron pair to the unique list of the macron index.",
)
@click.argument("normalized", type=str)
@click.argument("macron_form", type=str)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    default=DEFAULT_MACRON_INDEX_PATH,
    show_default=True,
    help="Macron index JSON path.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing unique entry if the normalized key already exists.",
)
def diacritic_add(
    normalized: str,
    macron_form: str,
    index_path: Path,
    force: bool,
) -> None:
    """
    Add a normalized/macron-ed pair to the unique list of the macron index.

    The normalized argument is normalized (lowercase, ð→þ, strip diacritics,
    internal hyphens) before storage so the key matches index convention.

    Args:
        normalized: Key form (will be normalized before lookup/insert).
        macron_form: Display form with macrons; stored as-is in unique.
        index_path: Path to macron index JSON file.
        force: If True, overwrite when key already exists in unique.

    Raises:
        click.ClickException: If key is invalid, key is in ambiguous (--force
            does not apply), or key exists in unique and --force not set.

    """
    payload = _load_macron_index_payload(index_path)
    key = normalize_old_english(normalized)
    if not key:
        msg = f"Normalized form is empty after normalization: {normalized!r}"
        raise click.ClickException(msg)
    if key in payload.ambiguous:
        msg = (
            f"Normalized key {key!r} is in the ambiguous list; resolve it via "
            "'diacritic disambiguate' first. --force does not apply."
        )
        raise click.ClickException(msg)
    if key in payload.unique and not force:
        existing = payload.unique[key]
        msg = (
            f"Entry already exists for normalized key {key!r} "
            f"(macron={existing!r}). Use --force to overwrite."
        )
        raise click.ClickException(msg)
    payload.unique[key] = macron_form
    _write_macron_index_payload(index_path, payload)
    print_info(f"Added pair: normalized={key!r} macron={macron_form!r}.")


@diacritic_group.command(
    name="delete",
    help="Delete a normalized/macron pair from the unique list of the macron index.",
)
@click.argument("normalized", type=str)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    default=DEFAULT_MACRON_INDEX_PATH,
    show_default=True,
    help="Macron index JSON path.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt.",
)
def diacritic_delete(
    normalized: str,
    index_path: Path,
    yes: bool,
) -> None:
    """
    Delete a normalized/macron-ed pair from the unique list.

    Prompts for confirmation showing both normalized and macron forms unless
    --yes is passed.

    Args:
        normalized: Key to remove (normalized before lookup).
        index_path: Path to macron index JSON file.
        yes: If True, skip confirmation.

    Raises:
        click.ClickException: If key is invalid or not in unique.

    """
    payload = _load_macron_index_payload(index_path)
    key = normalize_old_english(normalized)
    if not key:
        msg = f"Normalized form is empty after normalization: {normalized!r}"
        raise click.ClickException(msg)
    if key not in payload.unique:
        msg = f"Normalized key {key!r} not found in unique list at {index_path}."
        raise click.ClickException(msg)
    macron_form = payload.unique[key]
    if not yes:
        confirm_choice = Prompt.ask(
            f"Remove pair: normalized={key!r} macron={macron_form!r}. Continue? [y/N]",
            choices=["y", "n"],
            default="n",
        )
        if confirm_choice != "y":
            print_info("Delete cancelled.")
            return
    del payload.unique[key]
    _write_macron_index_payload(index_path, payload)
    print_info(f"Deleted pair: normalized={key!r} macron={macron_form!r}.")
