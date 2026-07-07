"""SQLAlchemy models for the canonical wyrdcraeft SQLite schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrdcraeft.db.base import Base

if TYPE_CHECKING:
    from wyrdcraeft.models.morph_catalog import MorphClass
    from wyrdcraeft.models.reference import InflectionCode, PartOfSpeech


class Form(Base):
    """Canonical morphology form row used for generated form lookup."""

    #: Canonical morphology forms table name.
    __tablename__ = "forms"
    #: Lookup indexes for normalized morphology search keys and foreign keys.
    __table_args__ = (
        Index("idx_forms_bt_key", "bt_key"),
        Index("idx_forms_title_key", "title_key"),
        Index("idx_forms_stem_key", "stem_key"),
        Index("idx_forms_form_key", "form_key"),
        Index("idx_forms_formi_key", "formi_key"),
        Index("idx_forms_normalized_title", "normalized_title"),
        Index("idx_forms_wordclass_id", "wordclass_id"),
        Index("idx_forms_inflection_code_id", "inflection_code_id"),
        Index("idx_forms_morph_class_id", "morph_class_id"),
        Index("idx_forms_entry_id", "entry_id"),
    )

    #: Surrogate row identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Legacy emitted row counter.
    counter: Mapped[int] = mapped_column(nullable=False)
    #: Normalized emitted form.
    formi: Mapped[str] = mapped_column(Text, nullable=False)
    #: Bosworth-Toller lemma text.
    BT: Mapped[str] = mapped_column(Text, nullable=False)
    #: Source lemma title.
    title: Mapped[str] = mapped_column(Text, nullable=False)
    #: Macron/dot-preserving normalized lemma title for dictionary joins.
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    #: Morphological stem.
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    #: Emitted form text.
    form: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy form-part trace.
    form_parts: Mapped[str] = mapped_column("formParts", Text, nullable=False)
    #: Legacy variant marker.
    var: Mapped[str] = mapped_column(Text, nullable=False)
    #: Generation probability marker.
    probability: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy morphological function label; superseded by inflection_code_id.
    function: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy Wright source marker; superseded by morph_class_id.
    wright: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy paradigm label; superseded by morph_class_id.
    paradigm: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy paradigm identifier; superseded by morph_class_id.
    para_id: Mapped[str] = mapped_column("paraID", Text, nullable=False)
    #: Legacy part-of-speech word class; superseded by wordclass_id.
    wordclass: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy primary class label; superseded by morph_class_id.
    class1: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy secondary class label; superseded by morph_class_id.
    class2: Mapped[str] = mapped_column(Text, nullable=False)
    #: Legacy tertiary class label; superseded by morph_class_id.
    class3: Mapped[str] = mapped_column(Text, nullable=False)
    #: Free-form generation comment.
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    #: Normalized Bosworth-Toller lookup key.
    bt_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Normalized title lookup key.
    title_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Normalized stem lookup key.
    stem_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Normalized form lookup key.
    form_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Normalized formi lookup key.
    formi_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Referenced canonical part-of-speech identifier.
    wordclass_id: Mapped[int | None] = mapped_column(
        ForeignKey("parts_of_speech.id"),
    )
    #: Referenced canonical inflection-code identifier.
    inflection_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("inflection_codes.id"),
    )
    #: Referenced morphology catalog class identifier.
    morph_class_id: Mapped[int | None] = mapped_column(
        ForeignKey("morph_classes.id"),
    )
    #: Referenced Bosworth-Toller dictionary entry identifier.
    entry_id: Mapped[int | None] = mapped_column(ForeignKey("bt_entries.id"))
    #: Referenced canonical part-of-speech row.
    part_of_speech: Mapped[PartOfSpeech | None] = relationship()
    #: Referenced canonical inflection-code row.
    inflection_code: Mapped[InflectionCode | None] = relationship()
    #: Referenced morphology catalog class row.
    morph_class: Mapped[MorphClass | None] = relationship()
    #: Referenced Bosworth-Toller dictionary entry row.
    dictionary_entry: Mapped[BTEntry | None] = relationship()


class BTEntry(Base):
    """
    Canonical Bosworth-Toller dictionary entry row keyed by normalized form and POS.

    The row stores one display headword plus a foreign-key reference to the
    canonical ``parts_of_speech`` lookup table used by normalized dictionary and
    morphology joins.

    """

    #: Canonical Bosworth-Toller dictionary entries table name.
    __tablename__ = "bt_entries"
    #: Dictionary entry uniqueness and lookup indexes.
    __table_args__ = (
        UniqueConstraint("norm_key", "pos_id"),
        Index("idx_bt_entries_norm_key", "norm_key"),
        Index("idx_bt_entries_normalized_title", "normalized_title"),
    )

    #: Surrogate dictionary entry identifier.
    id: Mapped[int] = mapped_column(primary_key=True)
    #: Normalized dictionary key.
    norm_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Display headword spelling preserved for dictionary and lexicon output.
    headword: Mapped[str] = mapped_column(Text, nullable=False)
    #: Macron/dot-preserving normalized headword for morphology joins.
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    #: Referenced canonical part-of-speech identifier.
    pos_id: Mapped[int] = mapped_column(
        ForeignKey("parts_of_speech.id"),
        nullable=False,
    )
    #: JSON-encoded gender labels.
    genders_json: Mapped[str] = mapped_column(Text, nullable=False)
    #: Etymology text.
    etymology: Mapped[str] = mapped_column(Text, nullable=False)
    #: JSON-encoded cross references.
    see_also_json: Mapped[str] = mapped_column(Text, nullable=False)
    #: JSON-encoded source line numbers.
    source_line_nos_json: Mapped[str] = mapped_column(Text, nullable=False)
    #: Referenced canonical part-of-speech row.
    part_of_speech: Mapped[PartOfSpeech] = relationship()


class BTSense(Base):
    """Canonical Bosworth-Toller sense row for one dictionary entry."""

    #: Canonical Bosworth-Toller senses table name.
    __tablename__ = "bt_senses"

    #: Surrogate sense identifier.
    id: Mapped[int] = mapped_column(primary_key=True)
    #: Owning dictionary entry identifier.
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("bt_entries.id"), nullable=False
    )
    #: Source sense label.
    sense_label: Mapped[str] = mapped_column(Text, nullable=False)
    #: English gloss text.
    gloss_en: Mapped[str] = mapped_column(Text, nullable=False)
    #: Sense ordering within the entry.
    order_index: Mapped[int] = mapped_column(nullable=False)


class BTVariant(Base):
    """Canonical Bosworth-Toller spelling variant row."""

    #: Canonical Bosworth-Toller spelling variants table name.
    __tablename__ = "bt_variants"
    #: Lookup index for macronized spelling variants.
    __table_args__ = (
        Index("idx_bt_variants_spelling", "spelling_macronized"),
        Index("idx_bt_variants_normalized_title", "normalized_title"),
    )

    #: Owning dictionary entry identifier.
    entry_id: Mapped[int] = mapped_column(ForeignKey("bt_entries.id"), nullable=False)
    #: Raw spelling variant.
    spelling_raw: Mapped[str] = mapped_column(Text, nullable=False)
    #: Macronized spelling variant.
    spelling_macronized: Mapped[str] = mapped_column(Text, nullable=False)
    #: Macron/dot-preserving normalized variant title for morphology joins.
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    #: Mapper-only key for the legacy table, which has no declared primary key.
    __mapper_args__ = {  # noqa: RUF012
        "primary_key": [entry_id, spelling_raw]
    }


class BTEditLog(Base):
    """Canonical Bosworth-Toller editorial merge audit row."""

    #: Canonical Bosworth-Toller edit audit table name.
    __tablename__ = "bt_edit_log"

    #: Surrogate audit row identifier.
    id: Mapped[int] = mapped_column(primary_key=True)
    #: Editorial operation name.
    op: Mapped[str] = mapped_column(Text, nullable=False)
    #: Source line number for the edit instruction.
    source_line_no: Mapped[int] = mapped_column(nullable=False)
    #: Target normalized dictionary key.
    target_norm_key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Target part-of-speech label.
    target_pos: Mapped[str] = mapped_column(Text, nullable=False)
    #: Edit scope label.
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    #: Integer boolean indicating whether the edit applied.
    applied: Mapped[int] = mapped_column(nullable=False)
    #: Human-readable edit note.
    note: Mapped[str] = mapped_column(Text, nullable=False)


class SearchKey(Base):
    """Canonical normalized search key row for lexicon browsing."""

    #: Canonical search keys table name.
    __tablename__ = "search_keys"
    #: Lookup and deduplication indexes for search keys.
    __table_args__ = (
        Index("idx_search_keys_key_text", "key_text"),
        Index("idx_search_keys_entry_id", "entry_id"),
        Index("idx_search_keys_form_id", "form_id"),
        Index(
            "idx_search_keys_dedupe",
            text("TRIM(key_text)"),
            "key_kind",
            "rank_tier",
            text("COALESCE(entry_id, -1)"),
            text("COALESCE(form_id, -1)"),
            text("TRIM(display_text)"),
            unique=True,
        ),
    )

    #: Surrogate search-key identifier.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Normalized search key text.
    key_text: Mapped[str] = mapped_column(Text, nullable=False)
    #: Search key kind label.
    key_kind: Mapped[str] = mapped_column(Text, nullable=False)
    #: Search ranking tier.
    rank_tier: Mapped[int] = mapped_column(nullable=False)
    #: Optional joined dictionary entry identifier.
    entry_id: Mapped[int | None] = mapped_column(ForeignKey("bt_entries.id"))
    #: Optional joined morphology form identifier.
    form_id: Mapped[int | None] = mapped_column(ForeignKey("forms.id"))
    #: Display text shown for search hits.
    display_text: Mapped[str] = mapped_column(Text, nullable=False)


class SearchBuildMeta(Base):
    """Canonical search-index build metadata key/value row."""

    #: Canonical search build metadata table name.
    __tablename__ = "search_build_meta"

    #: Metadata key.
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    #: Metadata value.
    value: Mapped[str] = mapped_column(Text, nullable=False)
