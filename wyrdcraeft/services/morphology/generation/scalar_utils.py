"""Shared scalar coercion helpers for parity-locked generation flows."""

from __future__ import annotations

import re


def nz(val: str | int | None) -> str:
    """
    Treat ``None`` and Perl-falsy ``0`` values as empty string.

    Args:
        val: Raw scalar value from a parsed morphology slot.

    Returns:
        Empty string for ``None``/``0``; otherwise stringified ``val``.

    """
    if val is None or val in {"0", 0}:
        return ""
    return str(val)


def perl_numify(val: str) -> float:
    """
    Approximate Perl scalar-to-number coercion for ``==`` comparisons.

    Args:
        val: Value to coerce.

    Returns:
        Numeric value extracted from the start of ``val``, or ``0.0``.

    """
    match = re.match(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))", val)
    if not match:
        return 0.0
    try:
        return float(match.group(1))
    except ValueError:
        return 0.0
