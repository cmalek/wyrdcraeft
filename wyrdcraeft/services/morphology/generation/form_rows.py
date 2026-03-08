"""Shared form-row emission helpers used across morphology generators."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .form_assembly import assemble_form_parts, materialize_form
from .probability import format_probability
from .sinks import TsvParitySink

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GeneratorSession

    from .shared import FormOutput, FormWriter


def print_one_form(
    session: GeneratorSession, form_data: dict[str, str], output_file: FormOutput
) -> None:
    r"""
    Print one form to the output sink using parity-preserving semantics.

    Notes:
        Matches Perl implementation of print_one_form function:

        .. code-block:: perl

            print(OUTPUT "$main::output_counter\t$formi\t$form{BT}\t$form{title}\t"
                . "$form{stem}\t"
                . "$form{form}\t$form{formParts}\t$form{var}\t"
                . (defined $form{probability} ? $form{probability} : "")
                . "\t$form{function}\t$form{wright}\t$form{paradigm}\t$form{paraID}\t"
                . "$form{wordclass}\t$form{class1}\t$form{class2}\t$form{class3}\t"
                . "$form{comment}\n");

        - In Perl, ``$form{probability}`` prints as empty string if undefined.
        - In Perl, if ``$count`` is greater than 0, a second line is printed
          with the probability incremented by 1.

    Args:
        session: Active generation session.
        form_data: Row payload fields to emit.
        output_file: Output sink receiving emitted rows.

    """
    emit_form_data = getattr(output_file, "emit_form_data", None)
    if callable(emit_form_data):
        emit_form_data(session, form_data)
        return
    TsvParitySink(cast("FormWriter", output_file)).emit_form_data(session, form_data)


def output_manual_forms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Emit manually curated forms before generated paradigmatic forms.

    Args:
        session: Active generation session containing ``manual_forms`` rows.
        output_file: Output sink receiving emitted rows.

    """
    for mf in session.manual_forms:
        form_data = {
            "BT": mf.BT,
            "title": mf.title,
            "stem": mf.stem,
            "form": mf.form,
            "formParts": mf.form_parts,
            "var": mf.var,
            "probability": mf.probability,
            "function": mf.function,
            "wright": mf.wright,
            "paradigm": mf.paradigm,
            "paraID": mf.para_id,
            "wordclass": mf.wordclass,
            "class1": mf.class1,
            "class2": mf.class2,
            "class3": mf.class3,
            "comment": mf.comment,
        }
        print_one_form(session, form_data, output_file)


def generate_and_print_form(  # noqa: PLR0913
    session: GeneratorSession,
    output_file: FormOutput,
    formhash: dict[str, str],
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str | None,
    ending: str,
    function: str,
    *,
    prob: str | int | None = None,
) -> tuple[str, str]:
    """
    Assemble one generated form row and emit it to the output sink.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        session: Active generation session containing output counters.
        output_file: Output sink receiving emitted rows.
        formhash: Mutable form metadata hash.
        prefix: Prefix segment.
        pre_vowel: Stem segment before the active vowel.
        vowel: Active vowel segment.
        post_vowel: Stem segment after the active vowel.
        boundary: Boundary consonant segment.
        dental: Optional weak-form dental segment.
        ending: Morphological ending segment.
        function: Morphological function code.

    Keyword Args:
        prob: Optional probability annotation.

    Returns:
        Two-item tuple of emitted ``(form, form_parts)``.

    """
    fh = formhash.copy()
    fh["function"] = function

    form_parts_raw = assemble_form_parts(
        class1=fh["class1"],
        prefix=prefix,
        pre_vowel=pre_vowel,
        vowel=vowel,
        post_vowel=post_vowel,
        boundary=boundary,
        dental=dental,
        ending=ending,
    )
    form, form_parts = materialize_form(form_parts_raw)

    fh["form"] = form
    fh["formParts"] = form_parts
    fh["probability"] = format_probability(prob)
    print_one_form(session, fh, output_file)
    return form, form_parts


def generate_and_print_manual(  # noqa: PLR0913
    session: GeneratorSession,
    output_file: FormOutput,
    formhash: dict[str, str],
    form: str,
    form_parts: str,
    function: str,
    prob: str | int | None,
) -> None:
    """
    Emit one manually assembled form row.

    Side Effects:
        Writes one row to the morphology output stream.

    Args:
        session: Active generation session containing output counters.
        output_file: Output sink receiving emitted rows.
        formhash: Mutable form metadata hash.
        form: Generated form text.
        form_parts: Generated form-parts payload.
        function: Morphological function code.
        prob: Optional probability annotation.

    """
    fh = formhash.copy()
    fh["form"] = form
    fh["formParts"] = form_parts
    fh["function"] = function
    fh["probability"] = format_probability(prob)
    print_one_form(session, fh, output_file)
