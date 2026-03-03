"""Sound change helpers for parity-preserving morphology generation."""

from __future__ import annotations

import re

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

