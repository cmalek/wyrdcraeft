"""In-memory macron index model for diacritic restoration."""

from dataclasses import dataclass

from .diacritics import MacronFormAnnotation


@dataclass(frozen=True)
class MacronIndex:
    """
    In-memory lookup maps for macron restoration.
    """

    #: Deterministic normalized -> marked mapping.
    unique: dict[str, str]
    #: Ambiguous normalized -> marked candidates mapping.
    ambiguous: dict[str, list[str]]
    #: Optional per-form metadata for ambiguous entries.
    ambiguous_metadata: dict[str, dict[str, MacronFormAnnotation]]
