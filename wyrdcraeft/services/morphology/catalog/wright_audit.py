"""Audit legacy Wright source values against deterministic lemma assignments."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from wyrdcraeft.models.morph_catalog import (
    LemmaMorphClass,
    MorphClass,
    MorphClassWrightSection,
)
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.services.markup import normalize_morphology_title
from wyrdcraeft.services.morphology.catalog.pos import catalog_pos_from_wordclass
from wyrdcraeft.services.morphology.loaders import load_dictionary, load_forms
from wyrdcraeft.services.morphology.text_utils import OENormalizer

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from sqlalchemy.engine import Engine

    from wyrdcraeft.models.morphology import Word

#: Legal non-blank legacy Wright value shape: semicolon-separated integers.
_LEGAL_WRIGHT_RE = re.compile(r"^\d+(;\d+)*$")

#: Wright inflection paragraphs begin at this section number in the catalog.
_INFLECTION_SECTION_MIN = 330

#: Regex used to extract section numbers from legacy Wright strings.
_WRIGHT_SECTION_RE = re.compile(r"\d+")

#: Human-readable placeholder for malformed empty tokens such as ``334;;335``.
_EMPTY_TOKEN_LABEL = "(empty-token)"  # noqa: S105


@dataclass(frozen=True)
class LegacyWrightRow:
    """
    One source row carrying a legacy Wright value for audit purposes.

    Note:
        Legacy Wright values come from the bundled morphology source files used
        alongside ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this row keeps the
        original source-side annotation for one lemma or paradigm entry without
        treating it as canonical truth. Part-of-speech scope: ``cross-PoS``.

    Attributes:
        source_file: Bundled source filename.
        line_no: One-based row number in that source file.
        source_record_id: Source-native identifier such as ``nid`` when present.
        lemma: Surface lemma or paradigm title from the source file.
        normalized_title: Macron-preserving normalized lemma title.
        pos: Catalog part-of-speech label used for assignment lookup.
        raw_legacy_wright: Unnormalized legacy Wright string from the source row.
        legacy_wright: Normalized audit value, with ``NULL`` treated as blank.
        eligible_for_assignment_checks: Whether contradiction and assignment
            checks should run for this row.

    """

    #: Bundled source filename.
    source_file: str
    #: One-based row number in that source file.
    line_no: int
    #: Source-native identifier such as ``nid`` when present.
    source_record_id: str
    #: Surface lemma or paradigm title from the source file.
    lemma: str
    #: Macron-preserving normalized lemma title.
    normalized_title: str
    #: Catalog part-of-speech label used for assignment lookup.
    pos: str
    #: Unnormalized legacy Wright string from the source row.
    raw_legacy_wright: str
    #: Normalized audit value, with ``NULL`` treated as blank.
    legacy_wright: str
    #: Whether contradiction and assignment checks should run for this row.
    eligible_for_assignment_checks: bool


@dataclass(frozen=True)
class MalformedLegacyWrightIssue:
    """
    Audit finding for one malformed legacy Wright source value.

    Attributes:
        row: Source row that carried the malformed value.
        invalid_tokens: Tokens or shape markers that made the value invalid.

    """

    #: Source row that carried the malformed value.
    row: LegacyWrightRow
    #: Tokens or shape markers that made the value invalid.
    invalid_tokens: tuple[str, ...]


@dataclass(frozen=True)
class ContradictionIssue:
    """
    Audit finding where legacy Wright sections contradict the assigned class.

    Attributes:
        row: Source row under audit.
        source_sections: Wright sections parsed from the source value.
        assigned_class_key: Deterministically assigned morph class key.
        assigned_sections: Wright sections linked to the assigned morph class.
        assignment_source: Provenance label stored on the assignment row.

    """

    #: Source row under audit.
    row: LegacyWrightRow
    #: Wright sections parsed from the source value.
    source_sections: tuple[int, ...]
    #: Deterministically assigned morph class key.
    assigned_class_key: str
    #: Wright sections linked to the assigned morph class.
    assigned_sections: tuple[int, ...]
    #: Provenance label stored on the assignment row.
    assignment_source: str


@dataclass(frozen=True)
class UnclassifiedIssue:
    """
    Audit finding for one inflectable row lacking a deterministic assignment.

    Attributes:
        row: Source row under audit.

    """

    #: Source row under audit.
    row: LegacyWrightRow


@dataclass(frozen=True)
class BlankLegacyButClassifiedIssue:
    """
    Audit finding where a blank legacy value still has a deterministic class.

    Attributes:
        row: Source row under audit.
        assigned_class_key: Deterministically assigned morph class key.
        assigned_sections: Wright sections linked to the assigned morph class.
        assignment_source: Provenance label stored on the assignment row.

    """

    #: Source row under audit.
    row: LegacyWrightRow
    #: Deterministically assigned morph class key.
    assigned_class_key: str
    #: Wright sections linked to the assigned morph class.
    assigned_sections: tuple[int, ...]
    #: Provenance label stored on the assignment row.
    assignment_source: str


@dataclass(frozen=True)
class WrightAuditResult:
    """
    Structured Phase 4 audit output for human and JSON reporting.

    Note:
        The audit compares legacy source annotations against deterministic
        lemma-to-class assignments grounded in ``data/OldEnglishGrammar.pdf``
        and ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, it reports source
        data quality and assignment coverage without mutating the source files.
        Part-of-speech scope: ``cross-PoS``.

    Attributes:
        source_row_counts: Number of scanned rows per bundled source file.
        malformed_legacy_wright: Rows whose legacy Wright value is malformed.
        contradictions: Rows whose encoded and assigned Wright section sets do
            not overlap.
        unclassified: Inflectable rows with no deterministic assignment row.
        blank_legacy_but_classified: Rows where legacy Wright is blank or ``0``
            but an assignment exists.

    """

    #: Number of scanned rows per bundled source file.
    source_row_counts: dict[str, int]
    #: Rows whose legacy Wright value is malformed.
    malformed_legacy_wright: tuple[MalformedLegacyWrightIssue, ...]
    #: Rows whose encoded and assigned Wright section sets do not overlap.
    contradictions: tuple[ContradictionIssue, ...]
    #: Inflectable rows with no deterministic assignment row.
    unclassified: tuple[UnclassifiedIssue, ...]
    #: Rows where legacy Wright is blank or ``0`` but an assignment exists.
    blank_legacy_but_classified: tuple[BlankLegacyButClassifiedIssue, ...]

    @property
    def source_rows_scanned(self) -> int:
        """
        Return the total number of scanned source rows.

        Returns:
            Sum of all per-source row counts.

        """
        return sum(self.source_row_counts.values())

    def to_payload(self) -> dict[str, object]:
        """
        Convert the full audit result into a JSON-friendly payload.

        Returns:
            Nested dictionary containing summary counts and full finding lists.

        """
        return {
            "summary": {
                "source_row_counts": dict(sorted(self.source_row_counts.items())),
                "source_rows_scanned": self.source_rows_scanned,
                "malformed_legacy_wright": len(self.malformed_legacy_wright),
                "contradictions": len(self.contradictions),
                "unclassified": len(self.unclassified),
                "blank_legacy_but_classified": len(self.blank_legacy_but_classified),
            },
            "malformed_legacy_wright": [
                asdict(issue) for issue in self.malformed_legacy_wright
            ],
            "contradictions": [asdict(issue) for issue in self.contradictions],
            "unclassified": [asdict(issue) for issue in self.unclassified],
            "blank_legacy_but_classified": [
                asdict(issue) for issue in self.blank_legacy_but_classified
            ],
        }


@dataclass(frozen=True)
class _AssignedMorphClass:
    """In-memory deterministic assignment payload keyed by lemma title and POS."""

    #: Deterministically assigned morph class key.
    class_key: str
    #: Provenance label stored on the assignment row.
    assignment_source: str
    #: Wright sections linked to the assigned morph class.
    wright_sections: tuple[int, ...]


class WrightAuditService:
    """
    Audit legacy Wright source annotations against deterministic catalog rows.

    Note:
        This service compares the bundled legacy source files against
        ``lemma_morph_classes`` and class-linked Wright citations documented by
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``. In
        plain terms, it reports source quality problems and coverage gaps for
        verbs, nouns, adjectives, adverbs, and pronouns without changing source
        files. Part-of-speech scope: ``cross-PoS``.

    Args:
        engine: SQLAlchemy engine bound to the canonical morphology database.

    """

    #: SQLAlchemy session factory bound to the canonical morphology database.
    _session_factory: sessionmaker[Session]

    def __init__(self, engine: Engine) -> None:
        """
        Build a read-only audit service bound to one canonical database.

        Args:
            engine: SQLAlchemy engine bound to the canonical morphology database.

        """
        #: SQLAlchemy session factory bound to the canonical morphology database.
        self._session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def audit(
        self,
        *,
        dictionary_path: Path,
        manual_forms_path: Path,
        para_vb_path: Path,
    ) -> WrightAuditResult:
        """
        Run the wright audit over bundled legacy source files.

        Keyword Args:
            dictionary_path: Path to ``dict_adj-vb-part-num-adv-noun.txt``.
            manual_forms_path: Path to ``manual_forms.txt``.
            para_vb_path: Path to ``para_vb.txt``.

        Returns:
            Structured audit result ready for human or JSON reporting.

        Side Effects:
            Reads the source files and canonical database, but does not mutate
            either one.

        """
        dictionary_rows = self._read_dictionary_rows(dictionary_path)
        manual_rows = self._read_manual_rows(manual_forms_path)
        para_rows = self._read_verbal_paradigm_rows(para_vb_path)
        assignment_by_key = self._load_assignments()

        malformed: list[MalformedLegacyWrightIssue] = []
        contradictions: list[ContradictionIssue] = []
        unclassified: list[UnclassifiedIssue] = []
        blank_but_classified: list[BlankLegacyButClassifiedIssue] = []

        for row in [*dictionary_rows, *manual_rows, *para_rows]:
            invalid_tokens = self._invalid_legacy_wright_tokens(row.legacy_wright)
            if invalid_tokens:
                malformed.append(
                    MalformedLegacyWrightIssue(
                        row=row,
                        invalid_tokens=invalid_tokens,
                    )
                )

            if not row.eligible_for_assignment_checks:
                continue

            assignment = assignment_by_key.get((row.normalized_title, row.pos))
            if assignment is None:
                unclassified.append(UnclassifiedIssue(row=row))
                continue

            if row.legacy_wright in {"", "0"}:
                blank_but_classified.append(
                    BlankLegacyButClassifiedIssue(
                        row=row,
                        assigned_class_key=assignment.class_key,
                        assigned_sections=assignment.wright_sections,
                        assignment_source=assignment.assignment_source,
                    )
                )
                continue

            source_sections = tuple(
                sorted(_parse_encoded_wright_sections(row.legacy_wright))
            )
            if (
                source_sections
                and assignment.wright_sections
                and set(source_sections).isdisjoint(assignment.wright_sections)
            ):
                contradictions.append(
                    ContradictionIssue(
                        row=row,
                        source_sections=source_sections,
                        assigned_class_key=assignment.class_key,
                        assigned_sections=assignment.wright_sections,
                        assignment_source=assignment.assignment_source,
                    )
                )

        return WrightAuditResult(
            source_row_counts={
                dictionary_path.name: len(dictionary_rows),
                manual_forms_path.name: len(manual_rows),
                para_vb_path.name: len(para_rows),
            },
            malformed_legacy_wright=tuple(
                sorted(malformed, key=lambda issue: self._row_sort_key(issue.row))
            ),
            contradictions=tuple(
                sorted(contradictions, key=lambda issue: self._row_sort_key(issue.row))
            ),
            unclassified=tuple(
                sorted(unclassified, key=lambda issue: self._row_sort_key(issue.row))
            ),
            blank_legacy_but_classified=tuple(
                sorted(
                    blank_but_classified,
                    key=lambda issue: self._row_sort_key(issue.row),
                )
            ),
        )

    def _load_assignments(self) -> dict[tuple[str, str], _AssignedMorphClass]:
        """
        Load deterministic lemma assignments and linked Wright sections into memory.

        Returns:
            Mapping keyed by ``(normalized_title, pos)``.

        """
        with self._session_factory() as session:
            sections_by_class = self._load_sections_by_class(session)
            assignment_rows = session.execute(
                select(
                    LemmaMorphClass.normalized_title,
                    PartOfSpeech.code,
                    LemmaMorphClass.assignment_source,
                    LemmaMorphClass.morph_class_id,
                    MorphClass.class_key,
                )
                .join(
                    MorphClass,
                    MorphClass.id == LemmaMorphClass.morph_class_id,
                )
                .join(
                    PartOfSpeech,
                    PartOfSpeech.id == LemmaMorphClass.pos_id,
                )
            ).all()

        assignments: dict[tuple[str, str], _AssignedMorphClass] = {}
        for (
            normalized_title,
            pos,
            assignment_source,
            morph_class_id,
            class_key,
        ) in assignment_rows:
            assignments[(str(normalized_title), str(pos))] = _AssignedMorphClass(
                class_key=str(class_key),
                assignment_source=str(assignment_source),
                wright_sections=sections_by_class.get(int(morph_class_id), ()),
            )
        return assignments

    @staticmethod
    def _load_sections_by_class(session: Session) -> dict[int, tuple[int, ...]]:
        """
        Group Wright section numbers by morph-class identifier.

        Args:
            session: Open SQLAlchemy session.

        Returns:
            Mapping from ``morph_classes.id`` to sorted Wright section tuples.

        """
        rows = session.execute(
            select(
                MorphClassWrightSection.morph_class_id,
                MorphClassWrightSection.section_no,
            ).order_by(
                MorphClassWrightSection.morph_class_id,
                MorphClassWrightSection.sort_order,
                MorphClassWrightSection.section_no,
            )
        ).all()

        sections_by_class: dict[int, list[int]] = {}
        for morph_class_id, section_no in rows:
            sections_by_class.setdefault(int(morph_class_id), []).append(
                int(section_no)
            )
        return {
            morph_class_id: tuple(section_nos)
            for morph_class_id, section_nos in sections_by_class.items()
        }

    @staticmethod
    def _read_dictionary_rows(path: Path) -> list[LegacyWrightRow]:
        """
        Read inflectable dictionary rows from the bundled source file.

        Args:
            path: Path to ``dict_adj-vb-part-num-adv-noun.txt``.

        Returns:
            Audit-ready source rows keyed by lemma title and catalog POS.

        Side Effects:
            Reads the dictionary source file from disk.

        """
        rows: list[LegacyWrightRow] = []
        for line_no, word in enumerate(load_dictionary(str(path)), start=1):
            catalog_pos = _catalog_pos_from_word(word)
            if catalog_pos is None:
                continue
            rows.append(
                LegacyWrightRow(
                    source_file=path.name,
                    line_no=line_no,
                    source_record_id=str(word.nid),
                    lemma=word.title,
                    normalized_title=normalize_morphology_title(word.title),
                    pos=catalog_pos,
                    raw_legacy_wright=str(word.wright),
                    legacy_wright=WrightAuditService._normalize_legacy_wright(
                        str(word.wright)
                    ),
                    eligible_for_assignment_checks=True,
                )
            )
        return rows

    @staticmethod
    def _read_manual_rows(path: Path) -> list[LegacyWrightRow]:
        """
        Read manual-form rows that map cleanly to catalog POS vocabulary.

        Args:
            path: Path to ``manual_forms.txt``.

        Returns:
            Audit-ready source rows keyed by lemma title and catalog POS.

        Side Effects:
            Reads the manual forms file from disk.

        """
        rows: list[LegacyWrightRow] = []
        for line_no, form in enumerate(load_forms(str(path)), start=1):
            catalog_pos = catalog_pos_from_wordclass(form.wordclass)
            if catalog_pos is None:
                continue
            rows.append(
                LegacyWrightRow(
                    source_file=path.name,
                    line_no=line_no,
                    source_record_id=str(form.id),
                    lemma=form.title,
                    normalized_title=form.normalized_title,
                    pos=catalog_pos,
                    raw_legacy_wright=str(form.wright),
                    legacy_wright=WrightAuditService._normalize_legacy_wright(
                        str(form.wright)
                    ),
                    eligible_for_assignment_checks=True,
                )
            )
        return rows

    @staticmethod
    def _read_verbal_paradigm_rows(path: Path) -> list[LegacyWrightRow]:
        """
        Read verb paradigm rows for malformed legacy Wright token scanning.

        Args:
            path: Path to ``para_vb.txt``.

        Returns:
            Audit-ready source rows for malformed-token reporting.

        Side Effects:
            Reads the verbal paradigms file from disk.

        """
        rows: list[LegacyWrightRow] = []
        raw_lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, raw_line in enumerate(raw_lines, start=1):
            parts = raw_line.split("\t")
            if len(parts) < 7:  # noqa: PLR2004
                continue
            title = OENormalizer.eth2thorn(parts[1].lower())
            raw_legacy_wright = parts[6].strip()
            rows.append(
                LegacyWrightRow(
                    source_file=path.name,
                    line_no=line_no,
                    source_record_id=parts[0].strip(),
                    lemma=title,
                    normalized_title=normalize_morphology_title(title),
                    pos="verb",
                    raw_legacy_wright=raw_legacy_wright,
                    legacy_wright=WrightAuditService._normalize_legacy_wright(
                        OENormalizer.eth2thorn(raw_legacy_wright.lower())
                    ),
                    eligible_for_assignment_checks=False,
                )
            )
        return rows

    @staticmethod
    def _normalize_legacy_wright(raw_value: str) -> str:
        """
        Normalize one legacy Wright value for auditing.

        Args:
            raw_value: Source-side Wright string.

        Returns:
            Trimmed audit value, with ``NULL`` normalized to blank.

        """
        normalized = raw_value.strip()
        if normalized.lower() == "null":
            return ""
        return normalized

    @staticmethod
    def _invalid_legacy_wright_tokens(legacy_wright: str) -> tuple[str, ...]:
        """
        Return malformed tokens or shape markers for one legacy Wright value.

        Args:
            legacy_wright: Normalized legacy Wright value.

        Returns:
            Empty tuple when the value is legal, otherwise the invalid tokens.

        """
        if legacy_wright in {"", "0"} or _LEGAL_WRIGHT_RE.fullmatch(legacy_wright):
            return ()

        invalid_tokens: list[str] = []
        for token in legacy_wright.split(";"):
            stripped = token.strip()
            if not stripped:
                invalid_tokens.append(_EMPTY_TOKEN_LABEL)
                continue
            if not stripped.isdigit():
                invalid_tokens.append(stripped)
        if invalid_tokens:
            return tuple(invalid_tokens)
        return (legacy_wright,)

    @staticmethod
    def _row_sort_key(row: LegacyWrightRow) -> tuple[str, int, str, str]:
        """
        Build a stable sort key for source rows and issue samples.

        Args:
            row: Source row being ordered.

        Returns:
            Source-file-first tuple for stable report ordering.

        """
        return (row.source_file, row.line_no, row.pos, row.lemma)


def format_wright_audit_text(
    result: WrightAuditResult,
    *,
    index_db: Path,
    sample_limit: int = 10,
) -> str:
    """
    Render a human-readable summary of one Wright audit run.

    Note:
        The report stays source-first and sample-capped so humans can inspect
        the highest-value legacy Wright mismatches without overwhelming stderr
        or treating legacy annotations as canonical truth. Part-of-speech scope:
        ``cross-PoS``.

    Keyword Args:
        index_db: Canonical database path used for deterministic assignment reads.
        sample_limit: Maximum number of sample rows shown per finding category.

    Args:
        result: Structured audit result from :class:`WrightAuditService`.

    Returns:
        Multi-line human-readable summary.

    """
    lines = [
        "Wright legacy audit complete.",
        f"index_db={index_db}",
        f"source_rows_scanned={result.source_rows_scanned}",
        "",
        "Source rows:",
    ]
    for source_file, count in sorted(result.source_row_counts.items()):
        lines.append(f"  {source_file}={count}")

    lines.extend(
        [
            "",
            "Findings:",
            f"  malformed_legacy_wright={len(result.malformed_legacy_wright)}",
            f"  contradictions={len(result.contradictions)}",
            f"  unclassified={len(result.unclassified)}",
            f"  blank_legacy_but_classified={len(result.blank_legacy_but_classified)}",
        ]
    )

    _append_sample_block(
        lines,
        heading="Malformed legacy Wright",
        issues=result.malformed_legacy_wright,
        sample_limit=sample_limit,
        formatter=_format_malformed_issue,
    )
    _append_sample_block(
        lines,
        heading="Contradictions",
        issues=result.contradictions,
        sample_limit=sample_limit,
        formatter=_format_contradiction_issue,
    )
    _append_sample_block(
        lines,
        heading="Unclassified",
        issues=result.unclassified,
        sample_limit=sample_limit,
        formatter=_format_unclassified_issue,
    )
    _append_sample_block(
        lines,
        heading="Blank legacy but classified",
        issues=result.blank_legacy_but_classified,
        sample_limit=sample_limit,
        formatter=_format_blank_but_classified_issue,
    )

    return "\n".join(lines)


def _append_sample_block(
    lines: list[str],
    *,
    heading: str,
    issues: Sequence[object],
    sample_limit: int,
    formatter,
) -> None:
    """
    Append one capped sample block to the human-readable audit report.

    Keyword Args:
        heading: Block title shown in the report.
        issues: Finding list for one category.
        sample_limit: Maximum number of sample rows to render.
        formatter: Callable that renders one issue as text.

    Args:
        lines: Mutable list of output lines being assembled.

    Side Effects:
        Appends formatted sample text to ``lines``.

    """
    if not issues:
        return
    lines.extend(
        [
            "",
            f"{heading} sample (up to {sample_limit}):",
        ]
    )
    lines.extend(f"  - {formatter(issue)}" for issue in issues[:sample_limit])


def _catalog_pos_from_word(word: Word) -> str | None:
    """
    Map one loaded dictionary ``Word`` to the catalog POS used by assignments.

    Args:
        word: Loaded dictionary lemma row.

    Returns:
        Catalog POS label, or ``None`` when the row is not inflectable.

    """
    if word.pspart == 1 or word.papart == 1:
        return "adjective"
    pos_flags: tuple[tuple[int, str], ...] = (
        (word.verb, "verb"),
        (word.noun, "noun"),
        (word.adjective, "adjective"),
        (word.adverb, "adverb"),
        (word.pronoun, "pronoun"),
    )
    for flag, catalog_pos in pos_flags:
        if flag == 1:
            return catalog_pos
    return None


def _parse_encoded_wright_sections(legacy_wright: str) -> set[int]:
    """
    Parse inflection-relevant Wright section numbers from one legacy value.

    Args:
        legacy_wright: Normalized legacy Wright string from a source row.

    Returns:
        Wright section numbers at or above ``_INFLECTION_SECTION_MIN``.

    """
    if not legacy_wright or legacy_wright.strip() in {"", "0"}:
        return set()
    sections: set[int] = set()
    for match in _WRIGHT_SECTION_RE.finditer(legacy_wright):
        section_no = int(match.group())
        if section_no >= _INFLECTION_SECTION_MIN:
            sections.add(section_no)
    return sections


def _format_malformed_issue(issue: MalformedLegacyWrightIssue) -> str:
    """
    Render one malformed legacy Wright finding as a single line.

    Args:
        issue: Finding to render.

    Returns:
        Human-readable single-line summary.

    """
    invalid = ", ".join(issue.invalid_tokens)
    return (
        f"{_format_row_prefix(issue.row)} legacy={_display_legacy_wright(issue.row)} "
        f"invalid_tokens={invalid}"
    )


def _format_contradiction_issue(issue: ContradictionIssue) -> str:
    """
    Render one contradiction finding as a single line.

    Args:
        issue: Finding to render.

    Returns:
        Human-readable single-line summary.

    """
    source_sections = ",".join(str(value) for value in issue.source_sections)
    assigned_sections = ",".join(str(value) for value in issue.assigned_sections)
    return (
        f"{_format_row_prefix(issue.row)} legacy={_display_legacy_wright(issue.row)} "
        f"source_sections={source_sections} assigned_class={issue.assigned_class_key} "
        f"assigned_sections={assigned_sections} "
        f"assignment_source={issue.assignment_source}"
    )


def _format_unclassified_issue(issue: UnclassifiedIssue) -> str:
    """
    Render one unclassified finding as a single line.

    Args:
        issue: Finding to render.

    Returns:
        Human-readable single-line summary.

    """
    return f"{_format_row_prefix(issue.row)} legacy={_display_legacy_wright(issue.row)}"


def _format_blank_but_classified_issue(issue: BlankLegacyButClassifiedIssue) -> str:
    """
    Render one blank-but-classified finding as a single line.

    Args:
        issue: Finding to render.

    Returns:
        Human-readable single-line summary.

    """
    assigned_sections = ",".join(str(value) for value in issue.assigned_sections)
    return (
        f"{_format_row_prefix(issue.row)} assigned_class={issue.assigned_class_key} "
        f"assigned_sections={assigned_sections} "
        f"assignment_source={issue.assignment_source}"
    )


def _format_row_prefix(row: LegacyWrightRow) -> str:
    """
    Build the shared source-row prefix used across sample lines.

    Args:
        row: Source row to render.

    Returns:
        Shared row-identifying prefix.

    """
    return (
        f"{row.source_file}:{row.line_no} record={row.source_record_id} "
        f"lemma={row.lemma!r} pos={row.pos}"
    )


def _display_legacy_wright(row: LegacyWrightRow) -> str:
    """
    Format one row's legacy Wright value for human-readable output.

    Args:
        row: Source row being rendered.

    Returns:
        Quoted legacy Wright display string.

    """
    display = row.raw_legacy_wright.strip() or row.legacy_wright or "<blank>"
    return repr(display)


__all__ = [
    "BlankLegacyButClassifiedIssue",
    "ContradictionIssue",
    "LegacyWrightRow",
    "MalformedLegacyWrightIssue",
    "UnclassifiedIssue",
    "WrightAuditResult",
    "WrightAuditService",
    "format_wright_audit_text",
]
