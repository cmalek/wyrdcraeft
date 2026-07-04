"""Read-only lookup API for lemma-to-morph-class assignments in the Wright catalog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.morph_catalog import (
    LemmaMorphClass,
    MorphClass,
    MorphClassSource,
    MorphClassWrightSection,
    MorphSource,
)
from wyrdcraeft.services.markup import normalize_morphology_title

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class MorphSourceCitation:
    """
    Bibliographic citation linked to one morph class.

    Attributes:
        source_key: Stable source business key.
        citation_apa: APA citation text.
        url: Source URL.
        retrieved_date: ISO date the source was retrieved.
        notes: Free-form catalog notes for the source.

    """

    #: Stable source business key.
    source_key: str
    #: APA citation text.
    citation_apa: str
    #: Source URL.
    url: str
    #: ISO date the source was retrieved.
    retrieved_date: str
    #: Free-form catalog notes for the source.
    notes: str


@dataclass(frozen=True)
class MorphClassView:
    """
    Read-only view of one assigned Wright morph class for a lemma.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, each view names one
        reusable Old English inflection class and its Wright mapping metadata
        for a catalog Part of Speech (``noun``, ``verb``, ``adjective``,
        ``adverb``, ``pronoun``, and later ``numeral``).

    Attributes:
        class_key: Stable catalog business key for the morph class.
        pos: Catalog part-of-speech label.
        canonical_name: Canonical display name for the class.
        modern_class: Modern linguistic class label.
        wright_label: Wright grammar label for the class.
        wright_sections: Wright section numbers in catalog sort order.
        sources: Bibliographic citations linked to the morph class.

    """

    #: Stable catalog business key for the morph class.
    class_key: str
    #: Catalog part-of-speech label.
    pos: str
    #: Canonical display name for the class.
    canonical_name: str
    #: Modern linguistic class label.
    modern_class: str
    #: Wright grammar label for the class.
    wright_label: str
    #: Wright section numbers in catalog sort order.
    wright_sections: tuple[int, ...]
    #: Bibliographic citations linked to the morph class.
    sources: tuple[MorphSourceCitation, ...]


class MorphologyCatalogQueryService:
    """
    Read-only query interface over lemma morph-class assignments.

    Note:
        Lookup follows Wright's inflection taxonomy in
        ``data/OldEnglishGrammar.pdf`` and catalog POS vocabulary in
        ``data/Ondej_Tich_40-54-1.pdf``. Each lemma is keyed by
        ``(normalized_title, pos)`` where ``pos`` uses catalog labels such as
        ``noun``, ``verb``, and ``adjective``. Part-of-speech scope:
        ``cross-PoS``.

    Args:
        engine: SQLAlchemy engine bound to a seeded canonical morphology DB.

    """

    #: SQLAlchemy engine bound to the canonical morphology database.
    _engine: Engine

    def __init__(self, engine: Engine) -> None:
        """
        Initialize a read-only catalog query service.

        Args:
            engine: SQLAlchemy engine bound to a seeded canonical morphology DB.

        """
        #: SQLAlchemy engine bound to the canonical morphology database.
        self._engine = engine

    @classmethod
    def from_db_path(cls, db_path: Path) -> MorphologyCatalogQueryService:
        """
        Build a query service from one canonical SQLite database path.

        Args:
            db_path: Path to ``wyrdcraeft.sqlite3`` containing catalog tables.

        Returns:
            Query service bound to the resolved database engine.

        """
        return cls(create_sqlalchemy_engine(db_path))

    def lookup_lemma_class(
        self,
        normalized_title: str,
        pos: str,
    ) -> MorphClassView | None:
        """
        Resolve one lemma assignment to its assigned morph-class view.

        Args:
            normalized_title: Lemma title; normalized with
                ``normalize_morphology_title`` before lookup.
            pos: Catalog part-of-speech label (for example ``noun``).

        Returns:
            Assigned morph-class view, or ``None`` when no assignment exists.

        """
        title_key = normalize_morphology_title(normalized_title)
        if not title_key:
            return None
        pos_key = pos.strip().lower()
        if not pos_key:
            return None

        with Session(self._engine) as session:
            assignment = session.scalar(
                select(LemmaMorphClass).where(
                    LemmaMorphClass.normalized_title == title_key,
                    LemmaMorphClass.pos == pos_key,
                ),
            )
            if assignment is None:
                return None

            morph_class = session.get(MorphClass, assignment.morph_class_id)
            if morph_class is None:
                return None

            section_rows = session.scalars(
                select(MorphClassWrightSection)
                .where(MorphClassWrightSection.morph_class_id == morph_class.id)
                .order_by(
                    MorphClassWrightSection.sort_order,
                    MorphClassWrightSection.section_no,
                ),
            ).all()
            source_rows = session.scalars(
                select(MorphSource)
                .join(
                    MorphClassSource,
                    MorphClassSource.source_id == MorphSource.id,
                )
                .where(MorphClassSource.morph_class_id == morph_class.id)
                .order_by(MorphSource.source_key),
            ).all()

        return MorphClassView(
            class_key=morph_class.class_key,
            pos=morph_class.pos,
            canonical_name=morph_class.canonical_name,
            modern_class=morph_class.modern_class,
            wright_label=morph_class.wright_label,
            wright_sections=tuple(row.section_no for row in section_rows),
            sources=tuple(
                MorphSourceCitation(
                    source_key=row.source_key,
                    citation_apa=row.citation_apa,
                    url=row.url,
                    retrieved_date=row.retrieved_date,
                    notes=row.notes,
                )
                for row in source_rows
            ),
        )


__all__ = [
    "MorphClassView",
    "MorphSourceCitation",
    "MorphologyCatalogQueryService",
]
