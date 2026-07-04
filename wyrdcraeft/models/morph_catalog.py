"""SQLAlchemy models for the morphology Wright catalog reference schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrdcraeft.db.base import Base

if TYPE_CHECKING:
    from collections.abc import Sequence  # noqa: F401


class MorphSource(Base):
    """Bibliographic source row cited by morphology catalog classes."""

    #: Morphology catalog bibliographic sources table name.
    __tablename__ = "morph_sources"

    #: Surrogate source identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Stable source business key.
    source_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    #: APA citation text.
    citation_apa: Mapped[str] = mapped_column(Text, nullable=False)
    #: Source URL.
    url: Mapped[str] = mapped_column(Text, nullable=False)
    #: ISO date the source was retrieved.
    retrieved_date: Mapped[str] = mapped_column(Text, nullable=False)
    #: Free-form catalog notes.
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    #: Morph-class junction rows citing this source.
    class_links: Mapped[list["MorphClassSource"]] = relationship(  # noqa: UP037
        back_populates="source",
    )


class MorphClass(Base):
    """
    Reference morphological class row from the Wright catalog.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, each row names one
        reusable Old English inflection class and its Wright mapping metadata
        for any Part of Speech in the catalog (``noun``, ``verb``,
        ``adjective``, ``adverb``, ``pronoun``, and later ``numeral``).

    """

    #: Morphology catalog class reference table name.
    __tablename__ = "morph_classes"
    #: Lookup indexes for part of speech and business key.
    __table_args__ = (
        Index("idx_morph_classes_pos", "pos"),
        Index("idx_morph_classes_class_key", "class_key"),
    )

    #: Surrogate class identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Stable dot-id business key (not the primary key).
    class_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    #: Part-of-speech label for this morph class.
    pos: Mapped[str] = mapped_column(Text, nullable=False)
    #: Canonical display name for the class.
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    #: Modern linguistic class label.
    modern_class: Mapped[str] = mapped_column(Text, nullable=False)
    #: Traditional Wright-style class label.
    traditional_class: Mapped[str] = mapped_column(Text, nullable=False)
    #: Wright grammar label for the class.
    wright_label: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    #: Rationale for mapping this class to Wright sections.
    mapping_rationale: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    #: Free-form catalog notes.
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    #: Integer boolean indicating whether lemmas may be assigned to this class.
    is_assignable: Mapped[int] = mapped_column(nullable=False, server_default="1")
    #: JSON-encoded paradigmatic example words.
    paradigmatic_words_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="[]"
    )
    #: JSON-encoded class aliases.
    aliases_json: Mapped[str] = mapped_column(Text, nullable=False, server_default="[]")
    #: JSON-encoded morphological feature flags.
    features_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="{}"
    )
    #: Wright-section junction rows owned by this class.
    wright_section_links: Mapped[list["MorphClassWrightSection"]] = relationship(  # noqa: UP037
        back_populates="morph_class",
        cascade="all, delete-orphan",
    )
    #: Bibliographic source junction rows owned by this class.
    source_links: Mapped[list["MorphClassSource"]] = relationship(  # noqa: UP037
        back_populates="morph_class",
        cascade="all, delete-orphan",
    )


class WrightSection(Base):
    """
    Wright grammar section reference row.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, each row identifies
        one numbered Wright paragraph used to anchor morph-class references
        across all catalog Part-of-Speech scopes.

    """

    #: Wright grammar section reference table name.
    __tablename__ = "wright_sections"

    #: Wright section number (primary key).
    section_no: Mapped[int] = mapped_column(primary_key=True)
    #: Full section text (nullable until Phase 4 ingest).
    section_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Source work title.
    work: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="Wright & Wright, Old English Grammar",
    )
    #: Free-form catalog notes.
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    #: Morph-class junction rows referencing this section.
    morph_class_links: Mapped[list["MorphClassWrightSection"]] = relationship(  # noqa: UP037
        back_populates="wright_section",
    )


class MorphClassWrightSection(Base):
    """
    Junction row linking one morph class to one Wright section.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this records which
        Wright paragraphs document the inflectional behavior of a morph class
        across catalog Part-of-Speech scopes.

    """

    #: Morph-class to Wright-section junction table name.
    __tablename__ = "morph_class_wright_sections"
    #: Uniqueness and lookup indexes for junction rows.
    __table_args__ = (
        UniqueConstraint("morph_class_id", "section_no"),
        Index("idx_morph_class_wright_sections_section_no", "section_no"),
    )

    #: Surrogate junction row identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Owning morph class identifier.
    morph_class_id: Mapped[int] = mapped_column(
        ForeignKey("morph_classes.id"), nullable=False
    )
    #: Referenced Wright section number.
    section_no: Mapped[int] = mapped_column(
        ForeignKey("wright_sections.section_no"), nullable=False
    )
    #: Display ordering among sections for one morph class.
    sort_order: Mapped[int] = mapped_column(nullable=False, server_default="0")
    #: Owning morph class row.
    morph_class: Mapped[MorphClass] = relationship(
        back_populates="wright_section_links",
    )
    #: Referenced Wright section row.
    wright_section: Mapped[WrightSection] = relationship(
        back_populates="morph_class_links",
    )


class MorphClassSource(Base):
    """Junction row linking one morph class to one bibliographic source."""

    #: Morph-class to source junction table name.
    __tablename__ = "morph_class_sources"
    #: Uniqueness constraint for class/source pairs.
    __table_args__ = (UniqueConstraint("morph_class_id", "source_id"),)

    #: Surrogate junction row identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Owning morph class identifier.
    morph_class_id: Mapped[int] = mapped_column(
        ForeignKey("morph_classes.id"), nullable=False
    )
    #: Referenced bibliographic source identifier.
    source_id: Mapped[int] = mapped_column(
        ForeignKey("morph_sources.id"), nullable=False
    )
    #: Owning morph class row.
    morph_class: Mapped[MorphClass] = relationship(back_populates="source_links")
    #: Referenced bibliographic source row.
    source: Mapped[MorphSource] = relationship(back_populates="class_links")
