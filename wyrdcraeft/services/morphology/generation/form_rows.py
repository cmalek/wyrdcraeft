"""Shared form-row emission helpers used across morphology generators."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

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
