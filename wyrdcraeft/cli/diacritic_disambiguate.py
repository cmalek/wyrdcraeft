from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..models import (
    POS_CODE_LABELS,
    POS_CODES,
    MacronFormAnnotation,
    MacronFormSense,
)
from ..services.bosworthtoller import (
    closest_entries_for_forms,
    fetch_bt_search_entries,
    merge_bt_entries,
)
from ..services.markup import DEFAULT_MACRON_INDEX_PATH
from .diacritic import _load_macron_index_payload, _write_macron_index_payload
from .utils import console, print_error, print_info

if TYPE_CHECKING:
    from ..models.bosworth_toller import BTSearchEntry


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


def _prompt_pos_code(attested_form: str) -> str | None:
    """
    Prompt for a controlled POS code for one attested form.

    Args:
        attested_form: Candidate display form being annotated.

    Returns:
        Selected POS code, or ``None`` when user cancels this subcommand.

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
        return None
    return POS_CODES[int(choice) - 1]


def _prompt_modern_meaning(attested_form: str) -> str | None:
    """
    Prompt for a non-empty modern English meaning.

    Args:
        attested_form: Candidate display form being annotated.

    Returns:
        Entered meaning text, or ``None`` when user cancels this subcommand.

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
            return None
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


def _prompt_attested_form(existing_forms: list[str]) -> str | None:
    """
    Prompt for a new attested form that is non-empty and not a duplicate.

    Args:
        existing_forms: Existing candidate forms for the normalized key.

    Returns:
        New attested form string, or ``None`` when user cancels this subcommand.

    """
    existing_lookup = {unicodedata.normalize("NFC", form) for form in existing_forms}
    while True:
        entered = unicodedata.normalize(
            "NFC",
            _prompt_text_input("New attested form to add (or q to close): ").strip(),
        )
        if entered.lower() == "q":
            return None
        if not entered:
            print_error("Attested form cannot be empty.")
            continue
        if entered in existing_lookup:
            print_error(f"'{entered}' already exists for this normalized form.")
            continue
        return entered


def _prompt_unique_replacement() -> str | None:
    """
    Prompt for a replacement unique form value.

    Returns:
        Replacement unique form text, or ``None`` when user cancels this subcommand.

    """
    while True:
        entered = unicodedata.normalize(
            "NFC",
            _prompt_text_input("Replacement unique form (or q to close): ").strip(),
        )
        if entered.lower() == "q":
            return None
        if entered:
            return entered
        print_error("Replacement form cannot be empty.")


def _prompt_form_annotation(attested_form: str) -> MacronFormAnnotation | None:
    """
    Prompt for POS and meaning annotation for one attested form.

    Args:
        attested_form: Candidate display form being annotated.

    Returns:
        Built form annotation, or ``None`` when user cancels this subcommand.

    """
    senses: list[MacronFormSense] = []
    while True:
        pos_code = _prompt_pos_code(attested_form)
        if pos_code is None:
            return None
        meaning = _prompt_modern_meaning(attested_form)
        if meaning is None:
            return None
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
            return None
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


@click.command(
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

    for offset, key in enumerate(target_keys, start=1):
        while True:
            options = payload.ambiguous.get(key)
            if options is None:
                break

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
                print_info("Closed disambiguation session.")
                return
            if action == "s":
                break
            if action == "c":
                selection = Prompt.ask(
                    "Choose candidate number (or q to close)",
                    choices=[*[str(i) for i in range(1, len(options) + 1)], "q"],
                )
                if selection == "q":
                    continue
                chosen_form = options[int(selection) - 1]
                confirm_commit = Prompt.ask(
                    f"Commit unique[{key}] = {chosen_form} and remove ambiguous entry? "
                    "(y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_commit == "q":
                    continue
                if confirm_commit != "y":
                    break

                payload.unique[key] = chosen_form
                payload.ambiguous.pop(key, None)
                payload.ambiguous_completed.discard(key)
                payload.ambiguous_metadata.pop(key, None)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Committed '{key}' -> '{chosen_form}'.")
                break

            if action == "r":
                replacement_form = _prompt_unique_replacement()
                if replacement_form is None:
                    continue
                confirm_commit = Prompt.ask(
                    "Commit "
                    f"unique[{key}] = {replacement_form} and remove ambiguous "
                    "entry? (y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_commit == "q":
                    continue
                if confirm_commit != "y":
                    break

                payload.unique[key] = replacement_form
                payload.ambiguous.pop(key, None)
                payload.ambiguous_completed.discard(key)
                payload.ambiguous_metadata.pop(key, None)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Committed '{key}' -> '{replacement_form}'.")
                break

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
                    continue
                if confirm_completed != "y":
                    break

                payload.ambiguous_completed.add(key)
                _write_macron_index_payload(index_path, payload)
                print_info(f"Marked '{key}' as completed.")
                break

            if action == "a":
                new_form = _prompt_attested_form(options)
                if new_form is None:
                    continue
                new_annotation = _prompt_form_annotation(new_form)
                if new_annotation is None:
                    continue
                form_annotations: dict[str, MacronFormAnnotation] = {
                    new_form: new_annotation
                }
                cancelled = False
                for form in options:
                    form_annotation = _prompt_form_annotation(form)
                    if form_annotation is None:
                        cancelled = True
                        break
                    form_annotations[form] = form_annotation
                if cancelled:
                    continue

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
                    continue
                deleted_form = options[int(selection) - 1]

                confirm_delete = Prompt.ask(
                    f"Delete '{deleted_form}' from ambiguous[{key}]? (y/n/q)",
                    choices=["y", "n", "q"],
                    default="n",
                )
                if confirm_delete == "q":
                    continue
                if confirm_delete != "y":
                    break

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

            define_annotations: dict[str, MacronFormAnnotation] = {}
            cancelled = False
            for form in options:
                form_annotation = _prompt_form_annotation(form)
                if form_annotation is None:
                    cancelled = True
                    break
                define_annotations[form] = form_annotation
            if cancelled:
                continue

            payload.ambiguous_completed.discard(key)
            payload.ambiguous_metadata[key] = define_annotations
            _write_macron_index_payload(index_path, payload)
            print_info(f"Saved annotations for '{key}'.")
            continue

    print_info("Disambiguation session complete.")
