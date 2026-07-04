"""Load packaged Wright morph-class catalog fixtures into canonical SQLite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import sessionmaker

from wyrdcraeft.models.morph_catalog import (
    LemmaMorphClass,
    MorphClass,
    MorphClassSource,
    MorphClassWrightSection,
    MorphSource,
    WrightSection,
)

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

#: Required top-level keys in ``wright_paradigms.json``.
_REQUIRED_FIXTURE_KEYS: tuple[str, ...] = ("schema_version", "sources", "morph_classes")
#: Required keys on each ``sources`` fixture row.
_REQUIRED_SOURCE_KEYS: tuple[str, ...] = (
    "source_key",
    "citation_apa",
    "url",
    "retrieved_date",
)
#: Required keys on each ``morph_classes`` fixture row.
_REQUIRED_MORPH_CLASS_KEYS: tuple[str, ...] = (
    "id",
    "pos",
    "canonical_name",
    "modern_class",
    "traditional_class",
)


@dataclass(frozen=True)
class LoadResult:
    """Row counts written while loading one Wright catalog fixture."""

    #: Number of bibliographic source rows upserted.
    sources_loaded: int
    #: Number of morph-class reference rows upserted.
    classes_loaded: int
    #: Number of Wright section rows upserted.
    sections_loaded: int


class MorphologyCatalogLoader:
    """
    Load ``wright_paradigms.json`` into morph catalog tables.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this loader seeds
        reusable Old English inflection-class metadata and Wright section
        anchors for every Part of Speech in the catalog (``noun``, ``verb``,
        ``adjective``, ``adverb``, ``pronoun``, and later ``numeral``).

    Args:
        engine: SQLAlchemy engine bound to a canonical SQLite database.

    """

    #: SQLAlchemy engine bound to the canonical database.
    _engine: Engine
    #: SQLAlchemy session factory for catalog writes.
    _session_factory: sessionmaker[Session]

    def __init__(self, engine: Engine) -> None:
        """
        Initialize a catalog loader for one canonical database engine.

        Args:
            engine: SQLAlchemy engine bound to a canonical SQLite database.

        """
        #: SQLAlchemy engine bound to the canonical database.
        self._engine = engine
        #: SQLAlchemy session factory for catalog writes.
        self._session_factory = sessionmaker(bind=self._engine, future=True)

    def is_catalog_populated(self) -> bool:
        """
        Return whether the catalog already contains morph-class rows.

        Returns:
            ``True`` when ``morph_classes`` has at least one row.

        """
        with self._engine.connect() as connection:
            count = connection.execute(
                select(func.count()).select_from(MorphClass),
            ).scalar_one()
        return int(count) >= 1

    def load_fixture(self, path: Path, *, refresh: bool = False) -> LoadResult:
        """
        Upsert catalog rows from one packaged Wright fixture JSON file.

        Args:
            path: Path to ``wright_paradigms.json``.

        Keyword Args:
            refresh: When ``True``, delete existing catalog rows before loading.

        Returns:
            Counts of sources, classes, and Wright sections written.

        Raises:
            ValueError: Fixture structure is invalid or references unknown sources.

        Side Effects:
            Upserts ``morph_sources``, ``morph_classes``, ``wright_sections``,
            and replaces per-class junction rows inside one transaction.

        """
        payload = self._read_fixture(path)
        self._validate_fixture(payload)
        section_numbers = self._collect_section_numbers(payload["morph_classes"])

        with self._session_factory.begin() as session:
            if refresh:
                self._clear_catalog_tables(session)

            source_key_to_id = self._upsert_sources(session, payload["sources"])
            class_key_to_id = self._upsert_morph_classes(
                session,
                payload["morph_classes"],
            )
            sections_loaded = self._upsert_wright_sections(session, section_numbers)
            self._replace_all_junctions(
                session,
                payload["morph_classes"],
                class_key_to_id,
                source_key_to_id,
            )
            classes_loaded = len(payload["morph_classes"])

        return LoadResult(
            sources_loaded=len(payload["sources"]),
            classes_loaded=classes_loaded,
            sections_loaded=sections_loaded,
        )

    def ensure_seeded(self, path: Path, *, refresh: bool = False) -> bool:
        """
        Load the fixture when the catalog is empty or refresh is requested.

        Args:
            path: Path to ``wright_paradigms.json``.

        Keyword Args:
            refresh: When ``True``, reload even if rows already exist.

        Returns:
            ``True`` when ``load_fixture`` ran; otherwise ``False``.

        """
        if refresh or not self.is_catalog_populated():
            self.load_fixture(path, refresh=refresh)
            return True
        return False

    @staticmethod
    def _read_fixture(path: Path) -> dict[str, Any]:
        """
        Read and parse one Wright catalog fixture file.

        Args:
            path: Path to the JSON fixture.

        Returns:
            Parsed fixture payload.

        """
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _validate_fixture(payload: dict[str, Any]) -> None:
        """
        Validate required fixture structure before writing catalog rows.

        Args:
            payload: Parsed fixture payload.

        Raises:
            ValueError: Required keys are missing or source keys are unknown.

        """
        missing = [key for key in _REQUIRED_FIXTURE_KEYS if key not in payload]
        if missing:
            msg = f"Fixture missing required keys: {missing}"
            raise ValueError(msg)

        for index, source in enumerate(payload["sources"]):
            missing_source = [
                key for key in _REQUIRED_SOURCE_KEYS if key not in source
            ]
            if missing_source:
                msg = (
                    f"Fixture source row {index} missing required keys: "
                    f"{missing_source}"
                )
                raise ValueError(msg)

        for morph_class in payload["morph_classes"]:
            class_key = str(morph_class.get("id", "<missing id>"))
            missing_class = [
                key for key in _REQUIRED_MORPH_CLASS_KEYS if key not in morph_class
            ]
            if missing_class:
                msg = (
                    f"Morph class {class_key!r} missing required keys: "
                    f"{missing_class}"
                )
                raise ValueError(msg)

        known_source_keys = {
            str(source["source_key"])
            for source in payload["sources"]
            if "source_key" in source
        }
        for morph_class in payload["morph_classes"]:
            class_key = str(morph_class.get("id", ""))
            unknown_keys = [
                source_key
                for source_key in morph_class.get("source_keys", [])
                if source_key not in known_source_keys
            ]
            if unknown_keys:
                msg = (
                    f"Unknown source_keys {unknown_keys!r} for morph class "
                    f"{class_key!r}"
                )
                raise ValueError(msg)

    @staticmethod
    def _collect_section_numbers(morph_classes: list[dict[str, Any]]) -> list[int]:
        """
        Collect unique Wright section numbers referenced by morph classes.

        Args:
            morph_classes: Parsed ``morph_classes`` fixture rows.

        Returns:
            Sorted unique Wright section numbers.

        """
        section_numbers = {
            int(section_no)
            for morph_class in morph_classes
            for section_no in morph_class.get("wright_sections", [])
        }
        return sorted(section_numbers)

    @staticmethod
    def _json_dump(value: object, *, default: str) -> str:
        """
        Serialize one fixture list or object to a JSON string.

        Args:
            value: Fixture value to serialize.

        Keyword Args:
            default: Fallback JSON text when ``value`` is missing.

        Returns:
            JSON-encoded text suitable for catalog columns.

        """
        if value is None:
            return default
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _clear_catalog_tables(session: Session) -> None:
        """
        Delete all catalog rows in child-to-parent order.

        Args:
            session: Active SQLAlchemy session receiving delete statements.

        Side Effects:
            Truncates catalog junction and parent tables.

        """
        session.execute(delete(MorphClassWrightSection))
        session.execute(delete(MorphClassSource))
        session.execute(delete(LemmaMorphClass))
        session.execute(delete(MorphClass))
        session.execute(delete(WrightSection))
        session.execute(delete(MorphSource))

    def _upsert_sources(
        self,
        session: Session,
        sources: list[dict[str, Any]],
    ) -> dict[str, int]:
        """
        Upsert bibliographic source rows keyed by ``source_key``.

        Args:
            session: Active SQLAlchemy session.
            sources: Parsed ``sources`` fixture rows.

        Returns:
            Mapping from ``source_key`` to surrogate ``morph_sources.id``.

        """
        source_keys = [str(source["source_key"]) for source in sources]
        existing_rows = {
            row.source_key: row
            for row in session.scalars(
                select(MorphSource).where(MorphSource.source_key.in_(source_keys)),
            ).all()
        }

        source_key_to_id: dict[str, int] = {}
        for source in sources:
            source_key = str(source["source_key"])
            row = existing_rows.get(source_key)
            if row is None:
                row = MorphSource(
                    source_key=source_key,
                    citation_apa=str(source["citation_apa"]),
                    url=str(source["url"]),
                    retrieved_date=str(source["retrieved_date"]),
                    notes=str(source.get("notes", "")),
                )
                session.add(row)
                session.flush()
            else:
                row.citation_apa = str(source["citation_apa"])
                row.url = str(source["url"])
                row.retrieved_date = str(source["retrieved_date"])
                row.notes = str(source.get("notes", ""))
            source_key_to_id[source_key] = int(row.id)
        return source_key_to_id

    def _upsert_wright_sections(
        self,
        session: Session,
        section_numbers: list[int],
    ) -> int:
        """
        Upsert Wright section rows with ``section_text`` left NULL.

        Args:
            session: Active SQLAlchemy session.
            section_numbers: Sorted unique Wright section numbers.

        Returns:
            Number of section rows upserted.

        """
        if not section_numbers:
            return 0

        existing_rows = {
            int(row.section_no): row
            for row in session.scalars(
                select(WrightSection).where(
                    WrightSection.section_no.in_(section_numbers),
                ),
            ).all()
        }
        for section_no in section_numbers:
            if section_no not in existing_rows:
                session.add(WrightSection(section_no=section_no, section_text=None))
        return len(section_numbers)

    def _upsert_morph_classes(
        self,
        session: Session,
        morph_classes: list[dict[str, Any]],
    ) -> dict[str, int]:
        """
        Upsert morph-class reference rows keyed by ``class_key``.

        Args:
            session: Active SQLAlchemy session.
            morph_classes: Parsed ``morph_classes`` fixture rows.

        Returns:
            Mapping from ``class_key`` to surrogate ``morph_classes.id``.

        """
        class_keys = [str(morph_class["id"]) for morph_class in morph_classes]
        existing_rows = {
            row.class_key: row
            for row in session.scalars(
                select(MorphClass).where(MorphClass.class_key.in_(class_keys)),
            ).all()
        }

        class_key_to_id: dict[str, int] = {}
        for morph_class in morph_classes:
            class_key = str(morph_class["id"])
            row = existing_rows.get(class_key)
            if row is None:
                row = MorphClass(class_key=class_key)
                session.add(row)
            self._apply_morph_class_fields(row, morph_class)
            session.flush()
            class_key_to_id[class_key] = int(row.id)
        return class_key_to_id

    @staticmethod
    def _replace_all_junctions(
        session: Session,
        morph_classes: list[dict[str, Any]],
        class_key_to_id: dict[str, int],
        source_key_to_id: dict[str, int],
    ) -> None:
        """
        Replace Wright-section and source junction rows for every morph class.

        Args:
            session: Active SQLAlchemy session.
            morph_classes: Parsed ``morph_classes`` fixture rows.
            class_key_to_id: Mapping from ``class_key`` to morph-class row id.
            source_key_to_id: Mapping from ``source_key`` to source row id.

        Side Effects:
            Deletes prior junction rows per class and inserts replacements.

        """
        for morph_class in morph_classes:
            class_key = str(morph_class["id"])
            MorphologyCatalogLoader._replace_class_junctions(
                session,
                class_key_to_id[class_key],
                morph_class,
                source_key_to_id,
            )

    @staticmethod
    def _apply_morph_class_fields(
        row: MorphClass,
        morph_class: dict[str, Any],
    ) -> None:
        """
        Copy one fixture morph-class payload onto an ORM row.

        Args:
            row: Target ``MorphClass`` ORM instance.
            morph_class: Parsed fixture row.

        """
        row.pos = str(morph_class["pos"])
        row.canonical_name = str(morph_class["canonical_name"])
        row.modern_class = str(morph_class["modern_class"])
        row.traditional_class = str(morph_class["traditional_class"])
        row.wright_label = str(morph_class.get("wright_label", ""))
        row.mapping_rationale = str(morph_class.get("mapping_rationale", ""))
        row.notes = str(morph_class.get("notes", ""))
        row.is_assignable = int(morph_class.get("is_assignable", 1))
        row.paradigmatic_words_json = MorphologyCatalogLoader._json_dump(
            morph_class.get("paradigmatic_words"),
            default="[]",
        )
        row.aliases_json = MorphologyCatalogLoader._json_dump(
            morph_class.get("aliases"),
            default="[]",
        )
        row.features_json = MorphologyCatalogLoader._json_dump(
            morph_class.get("features"),
            default="{}",
        )
        row.recognition_hints_json = MorphologyCatalogLoader._json_dump(
            morph_class.get("recognition_hints"),
            default="{}",
        )

    @staticmethod
    def _replace_class_junctions(
        session: Session,
        morph_class_id: int,
        morph_class: dict[str, Any],
        source_key_to_id: dict[str, int],
    ) -> None:
        """
        Replace Wright-section and source junction rows for one morph class.

        Args:
            session: Active SQLAlchemy session.
            morph_class_id: Surrogate ``morph_classes.id``.
            morph_class: Parsed fixture row.
            source_key_to_id: Mapping from ``source_key`` to source row id.

        Side Effects:
            Deletes prior junction rows for the class and inserts replacements.

        """
        session.execute(
            delete(MorphClassWrightSection).where(
                MorphClassWrightSection.morph_class_id == morph_class_id,
            ),
        )
        session.execute(
            delete(MorphClassSource).where(
                MorphClassSource.morph_class_id == morph_class_id,
            ),
        )

        wright_rows = [
            {
                "morph_class_id": morph_class_id,
                "section_no": int(section_no),
                "sort_order": sort_order,
            }
            for sort_order, section_no in enumerate(
                morph_class.get("wright_sections", []),
            )
        ]
        if wright_rows:
            session.execute(insert(MorphClassWrightSection), wright_rows)

        source_rows = [
            {
                "morph_class_id": morph_class_id,
                "source_id": source_key_to_id[str(source_key)],
            }
            for source_key in morph_class.get("source_keys", [])
        ]
        if source_rows:
            session.execute(insert(MorphClassSource), source_rows)
