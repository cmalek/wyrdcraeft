from __future__ import annotations

from importlib import resources
from pathlib import Path

import click

from wyrdcraeft.services.morphology.generators.common import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.processors import (
    set_adj_paradigm,
    set_noun_paradigm,
    set_verb_paradigm,
)
from wyrdcraeft.services.morphology.reference_snapshots import (
    format_reference_snapshot_result,
    generate_reference_snapshots,
)
from wyrdcraeft.services.morphology.session import GeneratorSession


def _default_morphology_data_dir() -> Path:
    return Path(str(resources.files("wyrdcraeft").joinpath("etc/morphology")))


def _resolve_input_paths(
    *,
    data_dir: Path,
    dictionary: Path | None,
    manual_forms: Path | None,
    verbal_paradigms: Path | None,
    prefixes: Path | None,
) -> tuple[Path, Path, Path, Path]:
    resolved_dictionary = dictionary or (data_dir / "dict_adj-vb-part-num-adv-noun.txt")
    resolved_manual = manual_forms or (data_dir / "manual_forms.txt")
    resolved_para = verbal_paradigms or (data_dir / "para_vb.txt")
    resolved_prefixes = prefixes or (data_dir / "prefixes.txt")
    return resolved_dictionary, resolved_manual, resolved_para, resolved_prefixes


def _validate_inputs(paths: tuple[Path, Path, Path, Path]) -> None:
    labels = ("dictionary", "manual forms", "verbal paradigms", "prefixes")
    for label, path in zip(labels, paths, strict=True):
        if not path.exists():
            msg = (
                f"Missing {label} file: {path}. "
                "Provide an explicit path via command flags or --data-dir."
            )
            raise click.ClickException(msg)


@click.group(
    name="morphology",
    help=(
        "Old English morphology generator commands. "
        "Default data files are loaded from wyrdcraeft/etc/morphology."
    ),
)
def morphology_group() -> None:
    """Morphology command group."""


@morphology_group.command(
    name="generate",
    help="Generate Old English morphological forms.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory containing default morphology data files.",
)
@click.option(
    "--dictionary",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Dictionary file path.",
)
@click.option(
    "--manual-forms",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Manual forms file path.",
)
@click.option(
    "--verbal-paradigms",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Verbal paradigms file path.",
)
@click.option(
    "--prefixes",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Prefixes file path.",
)
@click.option(
    "--output",
    default=Path("output.txt"),
    type=click.Path(path_type=Path),
    help="Output file path.",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Limit number of words processed.",
)
@click.option(
    "--enable-r-stem-nouns",
    is_flag=True,
    default=False,
    help="Enable opt-in non-parity r-stem noun generation.",
)
@click.option(
    "--full/--no-full",
    default=False,
    show_default=True,
    help="Generate full dictionary output (equivalent to legacy generate-full).",
)
def generate(  # noqa: PLR0913
    data_dir: Path | None,
    dictionary: Path | None,
    manual_forms: Path | None,
    verbal_paradigms: Path | None,
    prefixes: Path | None,
    output: Path,
    limit: int | None,
    enable_r_stem_nouns: bool,
    full: bool,
) -> None:
    """Generate Old English morphological forms."""
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    resolved_paths = _resolve_input_paths(
        data_dir=resolved_data_dir,
        dictionary=dictionary,
        manual_forms=manual_forms,
        verbal_paradigms=verbal_paradigms,
        prefixes=prefixes,
    )
    _validate_inputs(resolved_paths)

    session = GeneratorSession()
    try:
        session.load_all(*(str(path) for path in resolved_paths))
    except OSError as e:
        msg = f"Unable to read morphology input data: {e}"
        raise click.ClickException(msg) from e

    session.enable_r_stem_nouns = enable_r_stem_nouns

    if not full and limit:
        session.words = session.words[:limit]
        session.verbs = [
            w for w in session.words if w.verb == 1 and (w.pspart + w.papart == 0)
        ]
        session.adjectives = [
            w
            for w in session.words
            if w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)
        ]
        session.nouns = [w for w in session.words if w.noun == 1]

    session.remove_prefixes()
    session.remove_hyphens()
    session.count_syllables()

    set_verb_paradigm(session)
    set_adj_paradigm(session)
    set_noun_paradigm(session)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as out_handle:
            output_manual_forms(session, out_handle)
            generate_vbforms(session, out_handle)
            generate_adjforms(session, out_handle)
            generate_advforms(session, out_handle)
            generate_numforms(session, out_handle)
            generate_nounforms(session, out_handle)
    except OSError as e:
        msg = f"Failed to write morphology output to {output}: {e}"
        raise click.ClickException(msg) from e

    click.echo(
        "\n".join(
            [
                "Morphology generation complete.",
                f"output={output}",
                f"forms_written={session.output_counter}",
                f"limit_applied={'none' if full or not limit else limit}",
                f"full_mode={full}",
            ]
        )
    )


@morphology_group.command(
    name="generate-reference-snapshots",
    help="Generate canonical Python-reference morphology snapshots.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("tests/python_reference/data"),
    show_default=True,
    help="Directory where compressed snapshot files are written.",
)
@click.option(
    "--update",
    is_flag=True,
    default=False,
    help="Allow overwriting existing snapshot files.",
)
@click.option(
    "--include-full",
    is_flag=True,
    default=False,
    help="Also generate optional full-dataset smoke metadata snapshot.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory containing default morphology data files.",
)
@click.option(
    "--subset-dictionary",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("tests/fixtures/morphology/test_dict.txt"),
    show_default=True,
    help="Subset dictionary for default reference snapshots.",
)
def generate_reference_snapshots_command(
    output_dir: Path,
    update: bool,
    include_full: bool,
    data_dir: Path | None,
    subset_dictionary: Path,
) -> None:
    """Generate Python-reference snapshot fixtures via CLI."""
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    full_dictionary, manual_forms, verbal_paradigms, prefixes = _resolve_input_paths(
        data_dir=resolved_data_dir,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    _validate_inputs((full_dictionary, manual_forms, verbal_paradigms, prefixes))

    if not subset_dictionary.exists():
        msg = f"Missing subset dictionary: {subset_dictionary}"
        raise click.ClickException(msg)

    try:
        result = generate_reference_snapshots(
            output_dir=output_dir,
            update=update,
            include_full=include_full,
            subset_dictionary=subset_dictionary,
            full_dictionary=full_dictionary,
            manual_forms=manual_forms,
            verbal_paradigms=verbal_paradigms,
            prefixes=prefixes,
        )
    except (OSError, ValueError, FileExistsError) as e:
        raise click.ClickException(str(e)) from e

    click.echo(format_reference_snapshot_result(result))
