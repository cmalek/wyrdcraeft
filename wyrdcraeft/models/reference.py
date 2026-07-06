"""SQLAlchemy models for normalized morphology reference tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrdcraeft.db.base import Base

if TYPE_CHECKING:
    from collections.abc import Sequence  # noqa: F401


class PartOfSpeech(Base):
    """
    Canonical part-of-speech reference row for normalized morphology tables.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, each row names one
        canonical Part of Speech shared across the normalized schema and later
        morphology catalog work. Part-of-speech scope: ``cross-PoS``.

    """

    #: Part-of-speech reference table name.
    __tablename__ = "parts_of_speech"
    #: Lookup index for stable POS codes.
    __table_args__ = (Index("idx_parts_of_speech_code", "code", unique=True),)

    #: Surrogate part-of-speech identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Stable part-of-speech code.
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    #: Human-readable label shown for the POS code.
    display_label: Mapped[str] = mapped_column(Text, nullable=False)
    #: Integer boolean indicating whether this POS can inflect.
    is_inflectable: Mapped[int] = mapped_column(nullable=False, server_default="1")
    #: Inflection-code rows linked to this POS.
    inflection_codes: Mapped[list["InflectionCode"]] = relationship(  # noqa: UP037
        back_populates="part_of_speech",
    )


class InflectionCode(Base):
    """
    Canonical inflection-code reference row linked to one part of speech.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, each row stores one
        compact morphology function code and the Part of Speech it belongs to,
        plus JSON display metadata used by later normalized-schema tasks.
        Part-of-speech scope: ``cross-PoS``.

    """

    #: Inflection-code reference table name.
    __tablename__ = "inflection_codes"
    #: Lookup indexes for code and referenced POS.
    __table_args__ = (
        Index("idx_inflection_codes_code", "code", unique=True),
        Index("idx_inflection_codes_pos_id", "pos_id"),
    )

    #: Surrogate inflection-code identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Stable compact inflection code.
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    #: Referenced part-of-speech identifier.
    pos_id: Mapped[int] = mapped_column(
        ForeignKey("parts_of_speech.id"),
        nullable=False,
    )
    #: JSON-encoded display metadata for the code.
    display_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="{}",
    )
    #: Referenced part-of-speech row.
    part_of_speech: Mapped[PartOfSpeech] = relationship(
        back_populates="inflection_codes",
    )
