from __future__ import annotations

import json
import logging
import os
import re
import sys
import unicodedata
from importlib.metadata import Distribution
from pathlib import Path

import click
from pydantic import ValidationError
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.prompt import Prompt
from rich.table import Table

import wyrdcraeft

from ..ingest.pipeline import DocumentIngestor
from ..models import (
    POS_CODE_LABELS,
    POS_CODES,
    MacronFormAnnotation,
    MacronFormSense,
    MacronIndexPayload,
    TextMetadata,
)
from ..services.bosworthtoller import (
    BTSearchEntry,
    closest_entries_for_forms,
    fetch_bt_search_entries,
    merge_bt_entries,
)
from ..services.markup import DEFAULT_MACRON_INDEX_PATH, DiacriticRestorer
from ..settings import Settings
from .utils import console, print_error, print_info


def _configure_logging(settings: Settings) -> None:
    """
    Configure application logging from settings.

    Args:
        settings: Loaded application settings.

    """
    level = getattr(logging, settings.log_level, logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    root_logger.setLevel(level)
    logging.getLogger("wyrdcraeft").setLevel(level)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.option(
    "--config-file", type=click.Path(exists=True), help="Custom configuration file path"
)
@click.option(
    "--output",
    type=click.Choice(["json", "table", "text"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(
    ctx: click.Context, verbose: bool, quiet: bool, config_file: str | None, output: str
):
    """
    Wyrdcraeft command line interface.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["output"] = output
    ctx.obj["config_file"] = config_file

    if config_file:
        # This will be picked up by the Settings class's
        # settings_customise_sources method
        os.environ["WYRDCRAEFT_CONFIG_FILE"] = config_file

    # Load settings
    try:
        settings = Settings()
        ctx.obj["settings"] = settings
        _configure_logging(settings)
    except Exception as e:  # noqa: BLE001
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Configure console based on quiet mode
    if quiet:
        console.quiet = True


@cli.command(name="version", help="Print some version info.")
def version() -> None:
    """
    Print the some version info of this package,
    """
    table = Table(title="wyrdcraeft Version Info")
    table.add_column("Package", justify="left", style="cyan", no_wrap=True)
    table.add_column("Version", justify="left", style="yellow", no_wrap=True)

    table.add_row("wyrdcraeft", str(wyrdcraeft.__version__))
    table.add_row("click", str(Distribution.from_name("click").version))
    table.add_row("rich", str(Distribution.from_name("rich").version))
    table.add_row("pydantic", str(Distribution.from_name("pydantic").version))

    console.print(table)


@cli.group(name="settings", invoke_without_command=True)
@click.pass_context
def settings_group(ctx: click.Context):
    """
    Settings-related commands.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(show_settings)


@settings_group.command(name="show", help="Show the current settings.")
@click.pass_context
def show_settings(ctx: click.Context):
    """
    Settings-related commands.
    """
    output_format = ctx.obj.get("output", "table")
    verbose = ctx.obj.get("verbose", False)
    settings = ctx.obj.get("settings")

    if output_format == "json":
        click.echo(json.dumps(settings.model_dump()))
    elif output_format == "table":
        table = Table(title="Settings", show_header=True, header_style="bold magenta")
        table.add_column("Setting Name", style="cyan")
        table.add_column("Value", style="green")

        for setting_name, setting_value in settings.model_dump().items():
            table.add_row(setting_name, str(setting_value))

        console.print(table)
    else:  # text format
        for setting_name, setting_value in settings.model_dump().items():
            click.echo(f"{setting_name}: {setting_value}")
            click.echo()

    if verbose:
        print_info(f"Found {len(settings.model_dump())} settings")


@settings_group.command(name="create", help="Create a new settings file.")
@click.pass_context
def create_settings(ctx: click.Context):
    """
    Create a new settings file.
    """
    settings_path = Settings.default_settings_path()
    settings_path.touch()

    # Write all the non-frozen settings to the file with the default TOML format
    # and our Settings default values
    with settings_path.open("w", encoding="utf-8") as f:
        f.write(Settings().model_dump_json(indent=2))

    print_info(f"Settings file created at {settings_path}")
    if ctx.obj.get("verbose"):
        # print a table with the settings and their values
        table = Table(title="Settings", show_header=True, header_style="bold magenta")
        table.add_column("Setting Name", style="cyan")
        table.add_column("Value", style="green")

        for setting_name, setting_value in Settings().model_dump().items():
            # skip the frozen settings
            if setting_name in ["app_name", "app_version"]:
                continue
            table.add_row(setting_name, str(setting_value))

        console.print(table)


class _CloseDisambiguation(Exception):
    """
    Internal sentinel used to exit interactive disambiguation.
    """


#: Minimum number of candidate forms required to allow delete action.
MIN_DELETE_CANDIDATE_COUNT = 2


_MACRON_VOWEL_MAP = {
    "a": "ā",
    "e": "ē",
    "i": "ī",
    "o": "ō",
    "u": "ū",
    "y": "ȳ",
    "æ": "ǣ",
    "A": "Ā",
    "E": "Ē",
    "I": "Ī",
    "O": "Ō",
    "U": "Ū",
    "Y": "Ȳ",
    "Æ": "Ǣ",
}


def _normalize_option_key_sequences(raw_text: str) -> str:
    """
    Convert common terminal Option-key escape sequences into Unicode letters.

    Some terminal setups send Option-based dead-key sequences as ``ESC`` prefixes,
    e.g. ``ESC a a`` instead of ``ā``. This normalizes those to expected forms.

    Args:
        raw_text: Raw line text from input stream.

    Returns:
        Normalized text with supported ESC sequences converted.

    """
    # Some terminals display escape as the printable sequence "^[".
    normalized = raw_text.replace("^[", "\x1b")

    def _replace_macron(match: re.Match[str]) -> str:
        return _MACRON_VOWEL_MAP.get(match.group(1), match.group(1))

    normalized = re.sub(r"\x1b[aA]([AEIOUYaeiouyÆæ])", _replace_macron, normalized)
    # Drop any unsupported stray ESC prefix characters.
    return normalized.replace("\x1b", "")


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


def _render_disambiguation_layout(  # noqa: PLR0913
    *,
    normalized_form: str,
    options: list[str],
    annotations: dict[str, MacronFormAnnotation],
    bt_matches: dict[str, BTSearchEntry | None],
    bt_warning: str | None,
    progress_label: str,
    unique_count: int,
    ambiguous_count: int,
    completed_count: int,
) -> Layout:
    """
    Build one rich layout frame for a disambiguation step.

    Args:
        normalized_form: Current normalized key.
        options: Candidate attested forms.
        annotations: Per-form annotations already stored for this key.
        bt_matches: Best BT match per attested form.
        bt_warning: Optional warning text for BT lookup issues.
        progress_label: Human-readable iteration progress.
        unique_count: Current unique mapping count.
        ambiguous_count: Current ambiguous mapping count.
        completed_count: Current completed ambiguous key count.

    Returns:
        A rendered rich layout.

    """
    counts_table = Table.grid(expand=True)
    counts_table.add_column(justify="left", style="cyan")
    counts_table.add_column(justify="left")
    counts_table.add_row("Progress", progress_label)
    counts_table.add_row("Unique entries", str(unique_count))
    counts_table.add_row("Ambiguous entries", str(ambiguous_count))
    counts_table.add_row("Completed ambiguous", str(completed_count))

    options_table = Table(show_header=True, header_style="bold magenta")
    options_table.add_column("#", style="cyan", no_wrap=True)
    options_table.add_column("Attested Form", style="green")
    options_table.add_column("POS", style="yellow", no_wrap=True)
    options_table.add_column("Meaning", style="white")
    for idx, form in enumerate(options, start=1):
        annotation = annotations.get(form)
        if annotation is None:
            options_table.add_row(str(idx), form, "—", "—")
            continue
        pos_text = " | ".join(
            dict.fromkeys(sense.part_of_speech_code for sense in annotation.senses)
        )
        meaning_text = " | ".join(
            sense.modern_english_meaning for sense in annotation.senses
        )
        options_table.add_row(
            str(idx),
            form,
            pos_text,
            meaning_text,
        )

    actions_table = Table.grid(expand=True)
    actions_table.add_column(style="yellow")
    actions_table.add_column()
    actions_table.add_row("c", "Choose one form and commit")
    actions_table.add_row("r", "Replace with an explicit unique form")
    actions_table.add_row("d", "Define POS code + modern meaning for each form")
    actions_table.add_row("m", "Mark ambiguous entry as completed")
    actions_table.add_row("a", "Add a new entry, then annotate all forms")
    actions_table.add_row("x", "Delete one entry (requires 2+ forms)")
    actions_table.add_row("s", "Skip with no changes")
    actions_table.add_row("q", "Close session immediately")

    bt_table = Table(show_header=True, header_style="bold cyan")
    bt_table.add_column("Attested", style="green")
    bt_table.add_column("BT Spelling", style="yellow")
    bt_table.add_column("POS", style="magenta", no_wrap=True)
    bt_table.add_column("Meanings", style="white")
    for form in options:
        match = bt_matches.get(form)
        if match is None:
            bt_table.add_row(form, "—", "—", "—")
            continue
        bt_meanings = " | ".join(match.meanings) if match.meanings else "—"
        bt_pos = match.pos or "—"
        bt_table.add_row(form, match.headword_macronized, bt_pos, bt_meanings)

    bt_panel_content = (
        Group(f"[yellow]{bt_warning}[/yellow]", bt_table) if bt_warning else bt_table
    )

    candidate_layout = Layout()
    candidate_layout.split_row(
        Layout(
            Panel(options_table, title="Attested Forms", border_style="green"),
            ratio=1,
        ),
        Layout(
            Panel(
                bt_panel_content,
                title="Bosworth-Toller Assist (Page 1)",
                border_style="cyan",
            ),
            ratio=1,
        ),
    )

    layout = Layout()
    layout.split_column(
        Layout(
            Panel(
                counts_table,
                title=f"Disambiguating normalized form: {normalized_form}",
                border_style="blue",
            ),
            size=6,
        ),
        Layout(Panel(candidate_layout, title="Candidate Forms", border_style="green")),
        Layout(
            Panel(
                actions_table,
                title="Actions (Close button: press q)",
                border_style="red",
            ),
            size=8,
        ),
    )
    return layout


def _close_disambiguation() -> None:
    """
    Exit the current disambiguation session.

    Raises:
        _CloseDisambiguation: Always raised.

    """
    raise _CloseDisambiguation


def _prompt_pos_code(attested_form: str) -> str:
    """
    Prompt for a controlled POS code for one attested form.

    Args:
        attested_form: Candidate display form being annotated.

    Raises:
        _CloseDisambiguation: If user requests close.

    Returns:
        Selected POS code.

    """
    pos_table = Table(show_header=True, header_style="bold magenta")
    pos_table.add_column("#", style="cyan", no_wrap=True)
    pos_table.add_column("Code", style="green", no_wrap=True)
    pos_table.add_column("Part of Speech", style="white")
    for idx, pos_code in enumerate(POS_CODES, start=1):
        pos_table.add_row(str(idx), pos_code, POS_CODE_LABELS[pos_code])
    console.print(
        Panel(pos_table, title=f"POS selector for {attested_form}", border_style="cyan")
    )

    choices = [str(i) for i in range(1, len(POS_CODES) + 1)]
    choice = Prompt.ask(
        "Select POS number (or q to close)",
        choices=[*choices, "q"],
    )
    if choice == "q":
        raise _CloseDisambiguation
    return POS_CODES[int(choice) - 1]


def _prompt_modern_meaning(attested_form: str) -> str:
    """
    Prompt for a non-empty modern English meaning.

    Args:
        attested_form: Candidate display form being annotated.

    Raises:
        _CloseDisambiguation: If user requests close.

    Returns:
        Entered meaning text.

    """
    while True:
        entered = unicodedata.normalize(
            "NFC",
            _prompt_text_input(
                f"Modern English meaning for [bold]{attested_form}[/bold] "
                "(or q to close): "
            ).strip(),
        )
        if entered.lower() == "q":
            raise _CloseDisambiguation
        if entered:
            return entered
        print_error("Meaning cannot be empty.")


def _prompt_text_input(prompt: str) -> str:
    """
    Prompt for free-form text using UTF-8 decoding when possible.

    Args:
        prompt: Prompt text shown to user.

    Returns:
        Raw text line (without trailing newline).

    """
    console.print(prompt, end="", markup=True, emoji=True)
    return _normalize_option_key_sequences(input())


def _prompt_attested_form(existing_forms: list[str]) -> str:
    """
    Prompt for a new attested form that is non-empty and not a duplicate.

    Args:
        existing_forms: Existing candidate forms for the normalized key.

    Raises:
        _CloseDisambiguation: If user requests close.

    Returns:
        New attested form string.

    """
    existing_lookup = {unicodedata.normalize("NFC", form) for form in existing_forms}
    while True:
        entered = unicodedata.normalize(
            "NFC",
            _prompt_text_input("New attested form to add (or q to close): ").strip(),
        )
        if entered.lower() == "q":
            raise _CloseDisambiguation
        if not entered:
            print_error("Attested form cannot be empty.")
            continue
        if entered in existing_lookup:
            print_error(f"'{entered}' already exists for this normalized form.")
            continue
        return entered


def _prompt_unique_replacement() -> str:
    """
    Prompt for a replacement unique form value.

    Raises:
        _CloseDisambiguation: If user requests close.

    Returns:
        Replacement unique form text.

    """
    while True:
        entered = unicodedata.normalize(
            "NFC",
            _prompt_text_input("Replacement unique form (or q to close): ").strip(),
        )
        if entered.lower() == "q":
            raise _CloseDisambiguation
        if entered:
            return entered
        print_error("Replacement form cannot be empty.")


def _prompt_form_annotation(attested_form: str) -> MacronFormAnnotation:
    """
    Prompt for POS and meaning annotation for one attested form.

    Args:
        attested_form: Candidate display form being annotated.

    Raises:
        _CloseDisambiguation: If user requests close.

    Returns:
        Built form annotation.

    """
    senses: list[MacronFormSense] = []
    while True:
        pos_code = _prompt_pos_code(attested_form)
        meaning = _prompt_modern_meaning(attested_form)
        senses.append(
            MacronFormSense(
                part_of_speech_code=pos_code,
                modern_english_meaning=meaning,
            )
        )
        another = Prompt.ask(
            f"Add another POS/meaning sense for {attested_form}? (y/n/q)",
            choices=["y", "n", "q"],
            default="n",
        )
        if another == "q":
            raise _CloseDisambiguation
        if another == "n":
            break

    return MacronFormAnnotation(senses=senses)


def _can_mark_completed(
    *,
    key: str,
    options: list[str],
    metadata: dict[str, dict[str, MacronFormAnnotation]],
) -> bool:
    """
    Check whether an ambiguous key has complete per-form annotations.

    Args:
        key: Ambiguous normalized key.
        options: Attested forms for the key.
        metadata: Full ambiguous metadata mapping.

    Returns:
        ``True`` when every form has at least one recorded sense.

    """
    form_annotations = metadata.get(key, {})
    for form in options:
        annotation = form_annotations.get(form)
        if annotation is None or not annotation.senses:
            return False
    return True


@cli.group(name="diacritic")
def diacritic_group():
    """
    Diacritic index maintenance commands.
    """


@diacritic_group.command(
    name="disambiguate",
    help="Interactively resolve or annotate ambiguous macron index entries.",
)
@click.argument("normalized_form", required=False)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    default=DEFAULT_MACRON_INDEX_PATH,
    show_default=True,
    help="Macron index JSON path.",
)
def diacritic_disambiguate(  # noqa: PLR0912, PLR0915
    normalized_form: str | None,
    index_path: Path,
) -> None:
    """
    Resolve or annotate ambiguous normalized entries in the macron index.

    Args:
        normalized_form: Optional single normalized key to edit.
        index_path: Path to macron index JSON file.

    """
    payload = _load_macron_index_payload(index_path)

    if normalized_form is not None:
        target_keys = [normalized_form]
        if normalized_form not in payload.ambiguous:
            msg = (
                f"Normalized form '{normalized_form}' is not present in ambiguous "
                f"entries at {index_path}."
            )
            raise click.ClickException(msg)
    else:
        target_keys = sorted(
            key for key in payload.ambiguous if key not in payload.ambiguous_completed
        )
        if not target_keys:
            print_info(
                "No unresolved ambiguous entries found "
                f"in {index_path} (completed={len(payload.ambiguous_completed)})."
            )
            return

    bt_cache: dict[str, list[BTSearchEntry]] = {}

    try:
        for offset, key in enumerate(target_keys, start=1):
            options = payload.ambiguous.get(key)
            if options is None:
                continue

            bt_warning: str | None = None
            lookup_queries = list(dict.fromkeys([key, *options]))
            fetched_groups: list[list[BTSearchEntry]] = []
            failed_queries: list[str] = []
            for query in lookup_queries:
                cached_entries = bt_cache.get(query)
                if cached_entries is not None:
                    fetched_groups.append(cached_entries)
                    continue
                try:
                    queried_entries = fetch_bt_search_entries(query)
                    bt_cache[query] = queried_entries
                    fetched_groups.append(queried_entries)
                except Exception:  # noqa: BLE001
                    failed_queries.append(query)

            bt_entries = merge_bt_entries(fetched_groups)
            if failed_queries:
                failed_label = ", ".join(f"'{query}'" for query in failed_queries)
                bt_warning = (
                    "Bosworth-Toller lookup unavailable for query "
                    f"{failed_label}."
                )
            bt_matches = closest_entries_for_forms(options, bt_entries)

            console.print(
                _render_disambiguation_layout(
                    normalized_form=key,
                    options=options,
                    annotations=payload.ambiguous_metadata.get(key, {}),
                    bt_matches=bt_matches,
                    bt_warning=bt_warning,
                    progress_label=f"{offset}/{len(target_keys)}",
                    unique_count=len(payload.unique),
                    ambiguous_count=len(payload.ambiguous),
                    completed_count=len(payload.ambiguous_completed),
                )
            )
            action = Prompt.ask(
                "Action",
                choices=["c", "r", "d", "m", "a", "x", "s", "q"],
                default="s",
            )

            if action == "q":
                _close_disambiguation()
            if action == "s":
                continue
            if action == "c":
                selection = Prompt.ask(
                    "Choose candidate number (or q to close)",
                    choices=[*[str(i) for i in range(1, len(options) + 1)], "q"],
                )
                if selection == "q":
                    _close_disambiguation()
                chosen_form = options[int(selection) - 1]
                confirm_commit = Prompt.ask(
                    f"Commit unique[{key}] = {chosen_form} and remove ambiguous entry? "
                    "(y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_commit == "q":
                    _close_disambiguation()
                if confirm_commit != "y":
                    continue

                payload.unique[key] = chosen_form
                payload.ambiguous.pop(key, None)
                payload.ambiguous_completed.discard(key)
                payload.ambiguous_metadata.pop(key, None)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Committed '{key}' -> '{chosen_form}'.")
                continue

            if action == "r":
                replacement_form = _prompt_unique_replacement()
                confirm_commit = Prompt.ask(
                    "Commit "
                    f"unique[{key}] = {replacement_form} and remove ambiguous "
                    "entry? (y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_commit == "q":
                    _close_disambiguation()
                if confirm_commit != "y":
                    continue

                payload.unique[key] = replacement_form
                payload.ambiguous.pop(key, None)
                payload.ambiguous_completed.discard(key)
                payload.ambiguous_metadata.pop(key, None)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Committed '{key}' -> '{replacement_form}'.")
                continue

            if action == "m":
                if not _can_mark_completed(
                    key=key,
                    options=options,
                    metadata=payload.ambiguous_metadata,
                ):
                    print_error(
                        "Cannot mark completed: each attested form must have at least "
                        "one POS/meaning annotation."
                    )
                    continue
                confirm_completed = Prompt.ask(
                    "Mark "
                    f"ambiguous[{key}] as completed and hide from default iteration? "
                    "(y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_completed == "q":
                    _close_disambiguation()
                if confirm_completed != "y":
                    continue

                payload.ambiguous_completed.add(key)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Marked '{key}' as completed.")
                continue

            if action == "a":
                new_form = _prompt_attested_form(options)
                form_annotations: dict[str, MacronFormAnnotation] = {
                    new_form: _prompt_form_annotation(new_form)
                }
                for form in options:
                    form_annotations[form] = _prompt_form_annotation(form)
                payload.ambiguous[key] = [*options, new_form]
                payload.ambiguous_completed.discard(key)
                payload.ambiguous_metadata[key] = form_annotations
                _write_macron_index_payload(index_path, payload)
                print_info(f"Added and annotated '{new_form}' for '{key}'.")
                continue

            if action == "x":
                if len(options) < MIN_DELETE_CANDIDATE_COUNT:
                    print_error("Cannot delete an entry when fewer than 2 forms exist.")
                    continue

                selection = Prompt.ask(
                    "Choose candidate number to delete (or q to close)",
                    choices=[*[str(i) for i in range(1, len(options) + 1)], "q"],
                )
                if selection == "q":
                    _close_disambiguation()
                deleted_form = options[int(selection) - 1]

                confirm_delete = Prompt.ask(
                    f"Delete '{deleted_form}' from ambiguous[{key}]? (y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_delete == "q":
                    _close_disambiguation()
                if confirm_delete != "y":
                    continue

                payload.ambiguous[key] = [
                    form for form in options if form != deleted_form
                ]
                if key in payload.ambiguous_metadata:
                    payload.ambiguous_metadata[key].pop(deleted_form, None)
                    if not payload.ambiguous_metadata[key]:
                        payload.ambiguous_metadata.pop(key, None)
                payload.ambiguous_completed.discard(key)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Deleted '{deleted_form}' from '{key}'.")
                continue

            form_annotations = {
                form: _prompt_form_annotation(form) for form in options
            }
            payload.ambiguous_completed.discard(key)
            payload.ambiguous_metadata[key] = form_annotations
            _write_macron_index_payload(index_path, payload)
            print_info(f"Saved annotations for '{key}'.")

    except _CloseDisambiguation:
        print_info("Closed disambiguation session.")
        return

    print_info("Disambiguation session complete.")


@cli.group(name="source")
@click.pass_context
def reading_group(ctx: click.Context):
    """
    OE Source text-related commands.
    """


@reading_group.command(name="convert", help="Convert a source document to JSON.")
@click.argument("source", type=str)
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--use-llm/--no-use-llm",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use LLM for extraction",
)
@click.option(
    "--llm-model",
    type=click.Choice(["qwen2.5:14b-instruct", "gpt-4o", "gemini-3-flash-preview"]),
    help="LLM model ID",
)
@click.option("--llm-temperature", type=float, help="LLM temperature")
@click.option("--llm-max-tokens", type=int, help="LLM max tokens")
@click.option("--llm-timeout", type=int, help="LLM timeout in seconds")
@click.option("--title", type=str, help="Title of the text")
@click.pass_context
def reading_convert(  # noqa: PLR0913
    ctx: click.Context,
    source: str,
    output: Path,
    use_llm: bool,
    llm_model: str | None,
    llm_temperature: float | None,
    llm_max_tokens: int | None,
    llm_timeout: int | None,
    title: str | None,
):
    """
    Convert a source document to JSON.
    """
    settings: Settings = ctx.obj["settings"]
    source_ref: str | Path = source
    if not source.startswith(("http://", "https://")):
        source_ref = Path(source)
        if not source_ref.exists():
            msg = f"Source file not found: {source_ref}"
            raise click.ClickException(msg)

    # Override settings with flags
    if llm_model:
        settings.llm_model_id = llm_model
    if llm_temperature is not None:
        settings.llm_temperature = llm_temperature
    if llm_max_tokens is not None:
        settings.llm_max_tokens = llm_max_tokens
    if llm_timeout is not None:
        settings.llm_timeout_s = llm_timeout

    metadata = TextMetadata(
        title=title
        or (source_ref.stem if isinstance(source_ref, Path) else source_ref),
        source=str(source_ref),
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.fields[phase]}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing...", total=1, phase="")

        def progress_callback(current: int, total: int, message: str | None = None):
            phase_label = ""
            if message:
                m_lower = message.lower()
                if any(
                    x in m_lower
                    for x in [
                        "loading",
                        "normalizing",
                        "filtering",
                        "parsing",
                        "pre-parsing",
                    ]
                ):
                    phase_label = "[bold blue]Analyzing[/bold blue]"
                elif "found" in m_lower and "chunks" in m_lower:
                    phase_label = "[bold cyan]Planning[/bold cyan]"
                elif "extracting" in m_lower or "extraction" in m_lower:
                    phase_label = "[bold green]Extracting[/bold green]"
                elif "complete" in m_lower:
                    phase_label = "[bold green]Complete[/bold green]"
                else:
                    phase_label = f"[dim]{message}[/dim]"

            progress.update(
                task,
                total=total,
                completed=current,
                description=message or "Processing...",
                phase=f" {phase_label}" if phase_label else "",
            )

        try:
            doc = DocumentIngestor().ingest(
                source_path=(
                    source_ref
                    if isinstance(source_ref, Path)
                    else Path(source_ref)
                ),
                metadata=metadata,
                use_llm=use_llm,
                progress_callback=progress_callback,
                llm_config=settings.llm_config,
            )

            output.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

            if not ctx.obj.get("quiet"):
                print_info(f"Successfully converted {source_ref} to {output}")
        except Exception as e:
            if ctx.obj.get("verbose"):
                raise
            print_error(f"Conversion failed: {e}")
            sys.exit(1)


@reading_group.command(
    name="mark-diacritics",
    help="Restore macrons and dot diacritics in an Old English text file.",
)
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--ambiguities-output",
    required=True,
    type=click.Path(path_type=Path),
    help="Output path for ambiguity report JSON.",
)
def reading_mark_diacritics(
    source: Path,
    output: Path,
    ambiguities_output: Path,
) -> None:
    """
    Restore diacritics in a source text and emit ambiguity report JSON.

    Args:
        source: Input text file path.
        output: Marked output text file path.
        ambiguities_output: Output path for ambiguity report JSON.

    """
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as e:
        msg = f"Failed to read source file {source}: {e}"
        raise click.ClickException(msg) from e

    restorer = DiacriticRestorer()
    result = restorer.restore_text(text)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.marked_text, encoding="utf-8")

    ambiguities_output.parent.mkdir(parents=True, exist_ok=True)
    ambiguities_output.write_text(
        json.dumps(
            [item.model_dump() for item in result.ambiguities],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print_info(
        f"Successfully restored diacritics for {source} -> {output}. "
        f"Ambiguities: {len(result.ambiguities)}"
    )


@cli.command(name="convert", help="Convert a source document to JSON.")
@click.argument("source", type=str)
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--use-llm/--no-use-llm",
    is_flag=True,
    default=True,
    show_default=True,
    help="Use LLM for extraction",
)
@click.option(
    "--llm-model",
    type=click.Choice(["qwen2.5:14b-instruct", "gpt-4o", "gemini-3-flash-preview"]),
    help="LLM model ID",
)
@click.option("--llm-temperature", type=float, help="LLM temperature")
@click.option("--llm-max-tokens", type=int, help="LLM max tokens")
@click.option("--llm-timeout", type=int, help="LLM timeout in seconds")
@click.option("--title", type=str, help="Title of the text")
@click.pass_context
def convert(  # noqa: PLR0913
    ctx: click.Context,
    source: str,
    output: Path,
    use_llm: bool,
    llm_model: str | None,
    llm_temperature: float | None,
    llm_max_tokens: int | None,
    llm_timeout: int | None,
    title: str | None,
) -> None:
    """
    Backward-compatible top-level alias for ``source convert``.
    """
    ctx.invoke(
        reading_convert,
        source=source,
        output=output,
        use_llm=use_llm,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        llm_timeout=llm_timeout,
        title=title,
    )
