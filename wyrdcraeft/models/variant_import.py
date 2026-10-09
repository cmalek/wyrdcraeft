"""Models for the Bosworth-Toller variant import report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VariantRow(BaseModel):
    """
    One variant spelling found in a Bosworth-Toller entry.
    """

    #: Reject unknown fields.
    model_config = ConfigDict(extra="forbid")

    #: Variant spelling exactly as BT prints it.
    spelling: str = Field(..., min_length=1)
    #: Normalized index key of the spelling.
    key: str = Field(..., min_length=1)
    #: Canonical headword of the entry that lists the variant.
    headword: str = Field(..., min_length=1)
    #: 1-based line number in the Bosworth-Toller source.
    line_no: int = Field(..., ge=1)


class CollisionRow(BaseModel):
    """
    A variant whose key already exists with marks the importer will not change.
    """

    #: Reject unknown fields.
    model_config = ConfigDict(extra="forbid")

    #: The variant that collides.
    variant: VariantRow
    #: Existing forms for the key: one for a unique key, the options if ambiguous.
    existing: list[str]
    #: ``more_marks`` and ``conflicting_marks`` for a unique key, ``new_pattern``
    #: for an undecided ambiguous key.
    reason: Literal["more_marks", "conflicting_marks", "new_pattern"]


class ConflictingNewKey(BaseModel):
    """
    A new key proposed by several variants with different mark patterns.
    """

    #: Reject unknown fields.
    model_config = ConfigDict(extra="forbid")

    #: The normalized key.
    key: str = Field(..., min_length=1)
    #: Every variant proposing the key.
    variants: list[VariantRow]


class VariantImportReport(BaseModel):
    """
    Everything a variant import would do, and everything it leaves for review.
    """

    #: Reject unknown fields.
    model_config = ConfigDict(extra="forbid")

    #: New key -> stored form (BT spelling, lowercased).
    additions: dict[str, str] = Field(default_factory=dict)
    #: Variants colliding with an existing key, left for the user.
    collisions: list[CollisionRow] = Field(default_factory=list)
    #: New keys whose variants disagree on marks; none is added.
    conflicting_new: list[ConflictingNewKey] = Field(default_factory=list)
    #: Variants that are not spellings of their headword, for keys not in the index.
    below_gate: list[VariantRow] = Field(default_factory=list)
    #: Row counts by outcome (see the importer for the names).
    counts: dict[str, int] = Field(default_factory=dict)
