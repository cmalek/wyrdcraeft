"""End-to-end Bosworth-Toller dictionary indexing pipeline."""

from __future__ import annotations

import dataclasses
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wyrdcraeft.models.dictionary import BTLineKind, BTPos
from wyrdcraeft.services.dictionary.attestation_stripper import (
    _substantive_html_content,
)
from wyrdcraeft.services.dictionary.editorial_merger import BTEditorialMerger
from wyrdcraeft.services.dictionary.etymology_display import (
    relocate_misplaced_etymology_attestations,
)
from wyrdcraeft.services.dictionary.line_parser import BTLineParser, ParsedBTLine
from wyrdcraeft.services.dictionary.llm_fix_pass import (
    BTLLMFixPass,
    BTParseWarning,
    append_parse_warnings,
    write_parse_warnings,
)
from wyrdcraeft.services.dictionary.sense_segmenter import BTSenseSegmenter

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.services.dictionary.sinks import BTSqliteSink


@dataclass
class IndexReport:
    """
    Summary statistics produced by one dictionary index run.

    Attributes:
        source: Source ``oe_bt.txt`` path that was indexed.
        index_db: SQLite database path written by the sink.
        lines_read: Total non-empty source lines read from disk.
        parsed: Parsed lines accepted by the line parser.
        skipped: Parsed lines rejected with a ``skip_reason``.
        merged: Consolidated entries written to SQLite.
        senses_written: Sense rows written to SQLite.
        variants_written: Variant rows written to SQLite.
        edit_log_written: Editorial audit rows written to SQLite.
        pos_counts: Entry counts grouped by normalized POS label.
        skipped_by_reason: Skip counts grouped by parser skip reason.
        warning_counts: Diagnostic counts grouped by warning kind.
        entries: Alias of ``merged`` for report consumers expecting that key.

    """

    #: Source file path indexed in this run.
    source: Path
    #: SQLite database path written by the sink.
    index_db: Path
    #: Total non-empty source lines read.
    lines_read: int = 0
    #: Parsed lines accepted by the line parser.
    parsed: int = 0
    #: Parsed lines rejected with a skip reason.
    skipped: int = 0
    #: Consolidated entries written to SQLite.
    merged: int = 0
    #: Sense rows written to SQLite.
    senses_written: int = 0
    #: Variant rows written to SQLite.
    variants_written: int = 0
    #: Editorial audit rows written to SQLite.
    edit_log_written: int = 0
    #: Entry counts grouped by normalized POS label.
    pos_counts: dict[str, int] = field(default_factory=dict)
    #: Skip counts grouped by parser skip reason.
    skipped_by_reason: dict[str, int] = field(default_factory=dict)
    #: Diagnostic counts grouped by warning kind.
    warning_counts: dict[str, int] = field(default_factory=dict)

    @property
    def entries(self) -> int:
        """
        Return consolidated entry count for report consumers.

        Returns:
            Number of consolidated entries written to SQLite.

        """
        return self.merged

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the report to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "source": str(self.source),
            "index_db": str(self.index_db),
            "lines_read": self.lines_read,
            "parsed": self.parsed,
            "skipped": self.skipped,
            "merged": self.merged,
            "entries": self.entries,
            "senses_written": self.senses_written,
            "variants_written": self.variants_written,
            "edit_log_written": self.edit_log_written,
            "pos_counts": dict(self.pos_counts),
            "skipped_by_reason": dict(self.skipped_by_reason),
            "warning_counts": dict(self.warning_counts),
        }

    def write_json(self, report_path: Path) -> None:
        """
        Write the report as formatted JSON to disk.

        Args:
            report_path: Destination JSON file path.

        Side Effects:
            Creates parent directories and writes UTF-8 JSON.

        """
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


class BTIndexPipeline:
    """
    Stream-parse, merge, and persist Bosworth-Toller dictionary source lines.

    Args:
        line_parser: Optional line parser collaborator.
        sense_segmenter: Optional sense segmentation collaborator.
        editorial_merger: Optional editorial merge collaborator.

    """

    def __init__(
        self,
        *,
        line_parser: BTLineParser | None = None,
        sense_segmenter: BTSenseSegmenter | None = None,
        editorial_merger: BTEditorialMerger | None = None,
    ) -> None:
        """
        Initialize pipeline collaborators.

        Keyword Args:
            line_parser: Optional line parser collaborator.
            sense_segmenter: Optional sense segmentation collaborator.
            editorial_merger: Optional editorial merge collaborator.

        """
        #: Raw line parser collaborator.
        self.line_parser = line_parser or BTLineParser()
        #: Sense segmentation collaborator.
        self.sense_segmenter = sense_segmenter or BTSenseSegmenter()
        #: Editorial merge collaborator.
        self.editorial_merger = editorial_merger or BTEditorialMerger()

    def run(  # noqa: PLR0912
        self,
        source: Path,
        sink: BTSqliteSink,
        *,
        warnings_path: Path | None = None,
        llm_fix_pass: BTLLMFixPass | None = None,
    ) -> IndexReport:
        """
        Index one Bosworth-Toller source file into SQLite.

        Reads ``source`` line-by-line, parses and segments each accepted line,
        merges editorial siblings into consolidated entries, and writes the
        result through ``sink``.

        Args:
            source: Path to ``oe_bt.txt`` or a stratified corpus fixture.
            sink: SQLite sink receiving consolidated entries.

        Keyword Args:
            warnings_path: Optional path for ``parse_warnings.jsonl`` output.
            llm_fix_pass: Optional LLM repair pass applied to warning lines only.

        Returns:
            Summary report with parse, merge, and write statistics.

        Side Effects:
            Writes consolidated dictionary rows through ``sink`` and optionally
            emits ``parse_warnings.jsonl``.

        """
        parsed_lines: list[ParsedBTLine] = []
        skipped_by_reason: Counter[str] = Counter()
        parse_warnings: list[BTParseWarning] = []
        lines_read = 0

        with source.open(encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                lines_read += 1
                parsed = self._parse_and_segment(line_no, stripped)
                if parsed.skip_reason is not None:
                    skipped_by_reason[parsed.skip_reason] += 1
                else:
                    parse_warnings.extend(self._collect_parse_warnings(parsed))
                parsed_lines.append(parsed)

        if warnings_path is not None:
            write_parse_warnings(warnings_path, parse_warnings)

        if llm_fix_pass is not None and warnings_path is not None:
            llm_fix_pass.apply_fixes(warnings_path, parsed_lines)

        entries, edit_records = self.editorial_merger.merge(parsed_lines)
        editorial_warnings = self.editorial_merger.collect_editorial_warnings(
            parsed_lines,
            edit_records,
        )
        if editorial_warnings:
            parse_warnings.extend(editorial_warnings)
            if warnings_path is not None:
                append_parse_warnings(warnings_path, editorial_warnings)
        (
            entries_written,
            senses_written,
            variants_written,
            edit_log_written,
        ) = sink.write_entries(entries, edit_records)

        pos_counts = Counter(entry.pos.value for entry in entries)
        warning_counts: Counter[str] = Counter(
            {f"skip:{reason}": count for reason, count in skipped_by_reason.items()}
        )
        for warning in parse_warnings:
            warning_counts[f"parse:{warning.failure_reason}"] += 1
        for record in edit_records:
            if not record.applied:
                reason = record.note.split(":", maxsplit=1)[0]
                if reason in {"target_missing", "target_ambiguous"}:
                    warning_counts[f"edit_unapplied:{reason}"] += 1
                else:
                    warning_counts[f"edit_unapplied:{record.op.value}"] += 1

        return IndexReport(
            source=source.resolve(),
            index_db=sink.db_path,
            lines_read=lines_read,
            parsed=sum(1 for line in parsed_lines if line.skip_reason is None),
            skipped=sum(skipped_by_reason.values()),
            merged=entries_written,
            senses_written=senses_written,
            variants_written=variants_written,
            edit_log_written=edit_log_written,
            pos_counts=dict(sorted(pos_counts.items())),
            skipped_by_reason=dict(sorted(skipped_by_reason.items())),
            warning_counts=dict(sorted(warning_counts.items())),
        )

    def _parse_and_segment(self, line_no: int, line: str) -> ParsedBTLine:
        """
        Parse one source line and attach segmented senses when accepted.

        Args:
            line_no: One-based source line number.
            line: Stripped raw source line text.

        Returns:
            Parsed line payload, possibly carrying a skip reason.

        """
        parsed = self.line_parser.parse(line_no, line)
        if parsed.skip_reason is not None or parsed.raw_line is None:
            return parsed
        segment_result = self.sense_segmenter.segment_parsed_line(
            parsed.raw_line.raw_text
        )
        return relocate_misplaced_etymology_attestations(
            dataclasses.replace(
                parsed,
                senses=segment_result.senses,
                segment_warnings=segment_result.warnings,
            )
        )

    def _collect_parse_warnings(self, parsed: ParsedBTLine) -> list[BTParseWarning]:
        """
        Collect parse warnings for one accepted parsed line.

        Args:
            parsed: Parsed and segmented line payload.

        Returns:
            Warning records for optional LLM repair.

        """
        if parsed.raw_line is None:
            return []

        body = parsed.raw_line.raw_text
        headword = parsed.headword_macronized or parsed.raw_line.headword_raw
        pos_hint = parsed.pos.value
        line_no = parsed.raw_line.line_no
        warnings: list[BTParseWarning] = []

        warnings.extend(
            BTParseWarning(
                line_no=line_no,
                body=body,
                headword=headword,
                pos_hint=pos_hint,
                failure_reason=code,
            )
            for code in parsed.segment_warnings
        )

        if parsed.raw_line.kind == BTLineKind.MAIN and parsed.pos == BTPos.UNKNOWN:
            warnings.append(
                BTParseWarning(
                    line_no=line_no,
                    body=body,
                    headword=headword,
                    pos_hint=pos_hint,
                    failure_reason="pos_unknown_main",
                )
            )

        if not parsed.senses and _substantive_html_content(body):
            warnings.append(
                BTParseWarning(
                    line_no=line_no,
                    body=body,
                    headword=headword,
                    pos_hint=pos_hint,
                    failure_reason="empty_senses_nonempty_body",
                )
            )

        if self._attestation_strip_low_confidence(parsed):
            warnings.append(
                BTParseWarning(
                    line_no=line_no,
                    body=body,
                    headword=headword,
                    pos_hint=pos_hint,
                    failure_reason="attestation_strip_low_confidence",
                )
            )

        return warnings

    def _attestation_strip_low_confidence(self, parsed: ParsedBTLine) -> bool:
        """
        Return ``True`` when attestation stripping likely produced weak glosses.

        Args:
            parsed: Parsed and segmented line payload.

        Returns:
            ``True`` when the stripper confidence heuristic fires.

        """
        if parsed.raw_line is None:
            return False

        body = parsed.raw_line.raw_text
        stripper = self.sense_segmenter.stripper
        if parsed.senses:
            return any(
                stripper.is_low_confidence(body, sense.gloss_en)
                for sense in parsed.senses
            )
        return stripper.is_low_confidence(body, stripper.strip(body))
