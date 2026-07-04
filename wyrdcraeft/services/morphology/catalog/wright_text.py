"""Parse Wright markdown sections and ingest paragraph text into the catalog."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from wyrdcraeft.models.morph_catalog import WrightSection

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.engine import Engine

#: Matches ``§ N.`` or ``§ N`` at the start of a markdown line.
_SECTION_HEADING_RE = re.compile(r"^§\s+(\d+)\.?(?:\s|$)", re.MULTILINE)

#: Module logger for ingest warnings.
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestResult:
    """
    Summary counts from one Wright section-text ingest run.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this reports how many
        Wright paragraph rows were filled from markdown and which catalog
        sections still lack text after ingest. Part-of-speech scope:
        ``cross-PoS``.

    Attributes:
        updated: Wright section rows written or overwritten.
        skipped: Catalog rows left unchanged because text was already present.
        markdown_not_in_catalog: Section numbers parsed from markdown but
            absent from ``wright_sections``.
        catalog_still_null: Catalog section numbers still missing text after
            ingest.
        coverage_percent: Percentage of catalog sections with non-null text.
        warnings: Human-readable warning messages emitted during ingest.

    """

    #: Wright section rows written or overwritten.
    updated: int
    #: Catalog rows left unchanged because text was already present.
    skipped: int
    #: Section numbers parsed from markdown but absent from ``wright_sections``.
    markdown_not_in_catalog: tuple[int, ...]
    #: Catalog section numbers still missing text after ingest.
    catalog_still_null: tuple[int, ...]
    #: Percentage of catalog sections with non-null text.
    coverage_percent: float
    #: Human-readable warning messages emitted during ingest.
    warnings: tuple[str, ...]


def _normalize_section_text(text: str) -> str:
    """
    Normalize whitespace in one Wright section body.

    Args:
        text: Raw section body extracted from markdown.

    Returns:
        Text with outer whitespace removed and internal runs collapsed.

    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return re.sub(r"\s+", " ", normalized)


def parse_wright_sections(markdown: str) -> dict[int, str]:
    """
    Parse Wright markdown into section-number to body-text mappings.

    Note:
        Section headings follow Wright's numbered paragraphs in
        ``data/OldEnglishGrammar.pdf`` and the markdown corpus derived from it.
        In plain terms, each ``§ N`` line starts one paragraph block that runs
        until the next section heading. Part-of-speech scope: ``cross-PoS``.

    Args:
        markdown: Full Wright markdown document text.

    Returns:
        Mapping from Wright section number to normalized section body text.

    """
    matches = list(_SECTION_HEADING_RE.finditer(markdown))
    sections: dict[int, str] = {}
    for index, match in enumerate(matches):
        section_no = int(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[section_no] = _normalize_section_text(markdown[start:end])
    return sections


def parse_wright_sections_from_path(path: Path) -> dict[int, str]:
    """
    Parse Wright markdown from one filesystem path.

    Args:
        path: Markdown file containing Wright ``§`` section headings.

    Returns:
        Mapping from Wright section number to normalized section body text.

    Side Effects:
        Reads the markdown file from disk.

    """
    return parse_wright_sections(path.read_text(encoding="utf-8"))


class WrightSectionTextIngester:
    """
    Ingest Wright paragraph text from markdown into ``wright_sections``.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this fills the
        canonical Wright paragraph table so browse and audit commands can read
        stored text instead of parsing markdown at runtime. Part-of-speech scope:
        ``cross-PoS``.

    """

    def ingest(
        self,
        engine: Engine,
        md_path: Path,
        *,
        force: bool = False,
    ) -> IngestResult:
        """
        Upsert Wright section text parsed from one markdown source file.

        Keyword Args:
            force: When ``True``, overwrite rows that already contain text.

        Args:
            engine: SQLAlchemy engine bound to a seeded canonical morphology DB.
            md_path: Markdown file containing Wright ``§`` section headings.

        Returns:
            Ingest summary with counts, coverage, and warning messages.

        Side Effects:
            Updates ``wright_sections.section_text`` for matching catalog rows.

        """
        parsed_sections = parse_wright_sections_from_path(md_path)
        session_factory = sessionmaker(bind=engine, future=True)

        updated = 0
        skipped = 0
        markdown_not_in_catalog: list[int] = []

        with session_factory.begin() as session:
            catalog_section_nos = {
                int(section_no)
                for section_no in session.scalars(
                    select(WrightSection.section_no),
                ).all()
            }

            for section_no, section_text in parsed_sections.items():
                if section_no not in catalog_section_nos:
                    markdown_not_in_catalog.append(section_no)
                    continue

                row = session.get(WrightSection, section_no)
                if row is None:
                    markdown_not_in_catalog.append(section_no)
                    continue

                if row.section_text is not None and not force:
                    skipped += 1
                    continue

                row.section_text = section_text
                updated += 1

        warnings = self._build_warnings(
            markdown_not_in_catalog=markdown_not_in_catalog,
            catalog_still_null=self._catalog_null_sections(session_factory),
        )
        for warning in warnings:
            logger.warning("%s", warning)

        catalog_total = self._catalog_section_total(session_factory)
        catalog_still_null = self._catalog_null_sections(session_factory)
        coverage_percent = self._coverage_percent(
            catalog_total=catalog_total,
            catalog_still_null=catalog_still_null,
        )

        return IngestResult(
            updated=updated,
            skipped=skipped,
            markdown_not_in_catalog=tuple(sorted(markdown_not_in_catalog)),
            catalog_still_null=catalog_still_null,
            coverage_percent=coverage_percent,
            warnings=warnings,
        )

    @staticmethod
    def _catalog_section_total(session_factory: sessionmaker[Session]) -> int:
        """
        Count Wright section rows present in the catalog.

        Args:
            session_factory: Session factory bound to the canonical database.

        Returns:
            Total number of ``wright_sections`` rows.

        """
        with session_factory() as session:
            total = session.scalar(select(func.count()).select_from(WrightSection))
        return int(total or 0)

    @staticmethod
    def _catalog_null_sections(
        session_factory: sessionmaker[Session],
    ) -> tuple[int, ...]:
        """
        List catalog section numbers whose ``section_text`` is still NULL.

        Args:
            session_factory: Session factory bound to the canonical database.

        Returns:
            Sorted Wright section numbers missing paragraph text.

        """
        with session_factory() as session:
            rows = session.scalars(
                select(WrightSection.section_no)
                .where(WrightSection.section_text.is_(None))
                .order_by(WrightSection.section_no),
            ).all()
        return tuple(int(section_no) for section_no in rows)

    @staticmethod
    def _coverage_percent(
        *,
        catalog_total: int,
        catalog_still_null: tuple[int, ...],
    ) -> float:
        """
        Compute catalog text coverage as a percentage.

        Keyword Args:
            catalog_total: Total Wright section rows in the catalog.
            catalog_still_null: Section numbers still missing text.

        Returns:
            Percentage of catalog sections with non-null text.

        """
        if catalog_total <= 0:
            return 0.0
        filled = catalog_total - len(catalog_still_null)
        return round((filled / catalog_total) * 100.0, 2)

    @staticmethod
    def _build_warnings(
        *,
        markdown_not_in_catalog: list[int],
        catalog_still_null: tuple[int, ...],
    ) -> tuple[str, ...]:
        """
        Build human-readable warning messages for one ingest run.

        Keyword Args:
            markdown_not_in_catalog: Markdown section numbers absent from catalog.
            catalog_still_null: Catalog section numbers still missing text.

        Returns:
            Warning messages suitable for CLI or log output.

        """
        warnings: list[str] = []
        if markdown_not_in_catalog:
            sample = ", ".join(str(value) for value in markdown_not_in_catalog[:10])
            extra = len(markdown_not_in_catalog) - 10
            suffix = f" (+{extra} more)" if extra > 0 else ""
            warnings.append(
                "Markdown sections not in catalog: "
                f"{sample}{suffix}",
            )
        if catalog_still_null:
            sample = ", ".join(str(value) for value in catalog_still_null[:10])
            extra = len(catalog_still_null) - 10
            suffix = f" (+{extra} more)" if extra > 0 else ""
            warnings.append(
                "Catalog sections still missing text after ingest: "
                f"{sample}{suffix}",
            )
        return tuple(warnings)


__all__ = [
    "IngestResult",
    "WrightSectionTextIngester",
    "parse_wright_sections",
    "parse_wright_sections_from_path",
]
