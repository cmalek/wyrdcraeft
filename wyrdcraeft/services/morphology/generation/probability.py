"""Probability helpers for parity-preserving morphology generation."""

from __future__ import annotations


def format_probability(probability: str | int | None) -> str:
    """
    Convert a probability scalar to the emitted TSV field representation.

    Side Effects:
        None.

    Args:
        probability: Probability value used in generation.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``""`` when probability is undefined, otherwise stringified scalar.

    """
    if probability is None:
        return ""
    return str(probability)


def probability_or_zero(probability: str | int | None) -> int:
    """
    Coerce a nullable probability scalar to an integer baseline.

    Side Effects:
        None.

    Args:
        probability: Probability value used in generation.

    Keyword Args:
        None.

    Raises:
        ValueError: If a non-numeric non-empty value is provided.

    Returns:
        Integer probability baseline, defaulting to ``0``.

    """
    if probability is None or probability == "":
        return 0
    return int(probability)


def probability_plus(
    probability: str | int | None,
    *,
    delta: int,
    empty_default: int,
) -> int:
    """
    Add a delta to an optional probability using legacy empty-value behavior.

    Side Effects:
        None.

    Args:
        probability: Probability value used in generation.
        delta: Increment to apply when ``probability`` is set.
        empty_default: Value to return when ``probability`` is empty.

    Keyword Args:
        None.

    Raises:
        ValueError: If a non-numeric non-empty value is provided.

    Returns:
        Incremented probability or ``empty_default`` when unset.

    """
    if probability is None or probability == "":
        return empty_default
    return int(probability) + delta
