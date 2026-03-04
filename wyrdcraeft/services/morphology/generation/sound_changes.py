"""Sound change helpers for parity-preserving morphology generation."""

from __future__ import annotations

import re
from collections.abc import Callable

from .probability import probability_plus

#: Ordered sequential substitutions for ``PsInSg2`` forms.
PSINSG2_SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    ("dst", "tst"),
    ("þst", "tst"),
    ("tst", "st"),
    ("ngst", "ncst"),
    ("ncst", "nst"),
    ("gst", "hst"),
    ("hst", "xst"),
)

#: Callback signature for emitting one sound-changed manual form row.
SoundManualEmitter = Callable[[str, str, str, str | int | None], None]
#: Callback signature for emitting one source form prior to sound changes.
SoundSourceFormEmitter = Callable[[], tuple[str, str]]


def derive_sound_changed_forms(*, function: str, form: str) -> list[str]:
    """
    Return sequentially mutated forms for sound-change emission branches.

    Side Effects:
        None.

    Args:
        function: Morphology function code, such as ``PsInSg2``.
        form: Base generated form before sound changes.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Ordered list of derived forms that should be emitted.

    """
    if function == "PsInSg2":
        return _derive_psinsg2_sound_changes(form)
    if function == "PsInSg3":
        return _derive_psinsg3_sound_changes(form)
    return []


def derive_papt_sound_changed_forms(form: str) -> list[str]:
    """
    Return sequential ``PaPt`` sound-change derivations.

    Side Effects:
        None.

    Args:
        form: Base past-participle form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Ordered list of derived forms emitted after ``ted``/``tt`` rules.

    """
    derived: list[str] = []
    current = form
    if current.endswith("ted"):
        current = re.sub(r"ted$", "tt", current)
        derived.append(current)
    if current.endswith("tt"):
        current = re.sub(r"tt$", "t", current)
        derived.append(current)
    return derived


def _derive_psinsg2_sound_changes(form: str) -> list[str]:
    """
    Apply ordered ``PsInSg2`` substitutions using Perl-style mutation flow.

    Side Effects:
        None.

    Args:
        form: Base generated form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Derived forms emitted after each successful substitution.

    """
    derived: list[str] = []
    current = form
    for source, target in PSINSG2_SUBSTITUTIONS:
        if source in current:
            current = current.replace(source, target)
            derived.append(current)
    return derived


def _derive_psinsg3_sound_changes(form: str) -> list[str]:
    """
    Apply ordered ``PsInSg3`` substitutions using Perl-style mutation flow.

    Side Effects:
        None.

    Args:
        form: Base generated form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Derived forms emitted after each successful substitution.

    """
    derived: list[str] = []
    current = form

    if re.search(r"[td]þ$", current):
        current = re.sub(r"[td]þ$", "tt", current)
        derived.append(current)
    if re.search(r"[dt]t$", current):
        current = re.sub(r"[dt]t$", "t", current)
        derived.append(current)
    if "þþ" in current:
        current = current.replace("þþ", "þ")
        derived.append(current)
    if current.endswith("þ"):
        current = f"{current[:-1]}t"
        derived.append(current)
    if current.endswith("sþ"):
        current = f"{current[:-2]}st"
        derived.append(current)
    if current.endswith("ngþ"):
        current = f"{current[:-3]}ncþ"
        derived.append(current)
    if current.endswith("gþ"):
        current = f"{current[:-2]}hþ"
        derived.append(current)
    return derived


def emit_sound_changed_forms(  # noqa: PLR0913
    *,
    function: str,
    form: str,
    form_parts: str,
    probability: str | int | None,
    sound_change_prob_delta: int,
    emit_manual: SoundManualEmitter,
) -> None:
    """
    Emit manual rows for all derived sound-change forms of one base form.

    Side Effects:
        Invokes ``emit_manual`` once for each derived sound-change form.

    Args:
        function: Morphology function code driving substitution rules.
        form: Base generated surface form.
        form_parts: Canonical form-parts representation for manual rows.
        probability: Base probability scalar for the source form.
        sound_change_prob_delta: Delta applied to source probability.
        emit_manual: Callback that emits one manual row.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Raises:
        Does not raise directly.

    Returns:
        ``None``.

    """
    sound_prob = probability_plus(
        probability,
        delta=sound_change_prob_delta,
        empty_default=0,
    )
    for sound_changed_form in derive_sound_changed_forms(
        function=function,
        form=form,
    ):
        emit_manual(
            sound_changed_form,
            form_parts,
            function,
            sound_prob,
        )


def emit_sound_changed_from_source(
    *,
    function: str,
    probability: str | int | None,
    sound_change_prob_delta: int,
    emit_source_form: SoundSourceFormEmitter,
    emit_manual: SoundManualEmitter,
) -> None:
    """
    Emit sound-change rows after emitting one source form row.

    Side Effects:
        Invokes ``emit_source_form`` and then emits derived manual rows.

    Args:
        function: Morphology function code driving substitution rules.
        probability: Base probability scalar for the source form.
        sound_change_prob_delta: Delta applied to source probability.
        emit_source_form: Callback returning ``(form, form_parts)``.
        emit_manual: Callback that emits one derived manual row.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    source_form, source_form_parts = emit_source_form()
    emit_sound_changed_forms(
        function=function,
        form=source_form,
        form_parts=source_form_parts,
        probability=probability,
        sound_change_prob_delta=sound_change_prob_delta,
        emit_manual=emit_manual,
    )
