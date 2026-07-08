"""Parse Bosworth-Toller etymology blocks into browse table rows."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from wyrdcraeft.services.dictionary.line_parser import ParsedBTLine

#: Canonical Bosworth-Toller attestation separator used when relocating quotes.
_ATTESTATION_TAIL_SEPARATOR: Final[str] = " :-- "

#: Italic span splitter preserving language and gloss tags.
_ITALIC_SPAN_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>([^<]*)</I>",
    flags=re.IGNORECASE,
)
#: Trailing citation references such as ``Lay. 16487`` or ``Rel. Ant. ii. 224``.
_CITATION_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<![A-Za-z0-9])([A-Z][A-Za-z.&ÆæÉéÓóÜüċġþð]*(?:\s+[A-Za-z.&]+)*\s+"
    r"(?:\d+|[ivxlc]+(?:\s*\.\s*[ivxlc]+)?)"
    r"(?:\s*,\s*\d+)*(?:\s*,\s*\d+)*)"
)
#: Old/Middle English characters that suggest a misplaced attestation quote.
_OE_ATTESTATION_CHARS_RE: Final[re.Pattern[str]] = re.compile(r"[þðȝæœǣēīōū]")
#: Known comparative language/source labels in BT etymology blocks.
_LANG_SOURCE_LABELS: Final[frozenset[str]] = frozenset(
    {
        "lat.",
        "gr.",
        "ger.",
        "icel.",
        "o. fr.",
        "o. h. ger.",
        "o. nrs.",
        "o.nrs.",
        "o. sax.",
        "o. scand.",
        "mid. e.",
        "a. s.",
        "a.-sax.",
        "a. sax.",
        "dut.",
        "fr.",
        "goth.",
        "heb.",
        "ir.",
        "l. l.",
        "prov. e.",
        "sansk.",
        "sw.",
        "wel.",
    }
)


@dataclass(frozen=True)
class EtymologyTableRow:
    """
    One parsed etymology table row for dictionary browse rendering.

    Attributes:
        lang_source: Comparative language or source label.
        word: Cognate or source-language form.
        meaning: Gloss or Latin meaning text.
        source: Bibliographic citation when present.
        is_attestation: Whether the row is a misplaced attestation quote.

    """

    #: Comparative language or source label.
    lang_source: str
    #: Cognate or source-language form.
    word: str
    #: Gloss or Latin meaning text.
    meaning: str
    #: Bibliographic citation when present.
    source: str
    #: Whether the row is a misplaced attestation quote.
    is_attestation: bool = False


@dataclass(frozen=True)
class EtymologyDisplay:
    """
    Parsed etymology payload for one dictionary entry.

    Attributes:
        references: Comparative etymology rows.
        attestations: Misplaced OE attestation quotes.
        unparsed: Residual text that could not be structured safely.

    """

    #: Comparative etymology rows.
    references: tuple[EtymologyTableRow, ...]
    #: Misplaced OE attestation quotes.
    attestations: tuple[EtymologyTableRow, ...]
    #: Residual text that could not be structured safely.
    unparsed: tuple[str, ...]


def parse_etymology_text(text: str) -> EtymologyDisplay:
    """
    Parse one stored etymology string into structured browse rows.

    Args:
        text: Raw ``bt_entries.etymology`` text, often wrapped in brackets.

    Returns:
        Structured etymology references, attestations, and residual fragments.

    """
    cleaned = text.strip()
    if not cleaned:
        return EtymologyDisplay(references=(), attestations=(), unparsed=())

    blocks = _split_bracket_blocks(cleaned)
    references: list[EtymologyTableRow] = []
    attestations: list[EtymologyTableRow] = []
    unparsed: list[str] = []
    for block in blocks:
        block_text = _strip_outer_brackets(block)
        if re.search(r"\bCf\.\s", block_text, flags=re.IGNORECASE):
            parts = re.split(r"\bCf\.\s*", block_text, maxsplit=1, flags=re.IGNORECASE)
            if parts[0].strip():
                attestations.extend(_parse_attestation_block(parts[0]))
            if len(parts) > 1 and parts[1].strip():
                parsed_refs, residual = _parse_reference_block(parts[1])
                references.extend(parsed_refs)
                if residual:
                    unparsed.append(residual)
            continue
        if _looks_like_attestation(block_text):
            attestations.extend(_parse_attestation_block(block_text))
            continue
        parsed_refs, residual = _parse_reference_block(block_text)
        references.extend(parsed_refs)
        if residual:
            unparsed.append(residual)
    return EtymologyDisplay(
        references=tuple(references),
        attestations=tuple(attestations),
        unparsed=tuple(unparsed),
    )


def partition_etymology_blocks(
    blocks: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """
    Split raw bracket blocks into etymology and misplaced attestation tails.

    Args:
        blocks: Trailing ``[...]`` blocks extracted from one BT line body.

    Returns:
        Clean etymology blocks plus citation-tail text for sense relocation.

    """
    clean_blocks: list[str] = []
    attestation_tails: list[str] = []
    for block in blocks:
        etymology_block, attestation_tail = _partition_one_block(block)
        if etymology_block:
            clean_blocks.append(etymology_block)
        if attestation_tail:
            attestation_tails.append(attestation_tail)
    return tuple(clean_blocks), tuple(attestation_tails)


def relocate_misplaced_etymology_attestations(parsed: ParsedBTLine) -> ParsedBTLine:
    """
    Move misplaced attestation quotes out of etymology into sense citations.

    Args:
        parsed: Parsed and segmented BT line payload.

    Returns:
        Parsed line with cleaned ``etymology_blocks`` and relocated attestation
        tails appended to the last sense ``source_fragment_raw`` when possible.

    """
    if not parsed.etymology_blocks:
        return parsed

    clean_blocks, attestation_tails = partition_etymology_blocks(
        parsed.etymology_blocks,
    )
    if not attestation_tails:
        if clean_blocks == parsed.etymology_blocks:
            return parsed
        return dataclasses.replace(parsed, etymology_blocks=clean_blocks)

    senses = list(parsed.senses)
    warnings = list(parsed.segment_warnings)
    if not senses:
        warnings.append("misplaced_attestation_without_sense")
        return dataclasses.replace(
            parsed,
            etymology_blocks=clean_blocks,
            segment_warnings=tuple(warnings),
        )

    last_sense = senses[-1]
    relocated_tail = _ATTESTATION_TAIL_SEPARATOR.join(attestation_tails)
    fragment = last_sense.source_fragment_raw.strip()
    if fragment.endswith(_ATTESTATION_TAIL_SEPARATOR.strip()):
        new_fragment = f"{fragment}{relocated_tail}"
    elif _ATTESTATION_TAIL_SEPARATOR.strip() in fragment:
        new_fragment = f"{fragment} {relocated_tail}"
    else:
        new_fragment = f"{fragment}{_ATTESTATION_TAIL_SEPARATOR}{relocated_tail}"
    senses[-1] = dataclasses.replace(
        last_sense,
        source_fragment_raw=new_fragment,
    )
    return dataclasses.replace(
        parsed,
        etymology_blocks=clean_blocks,
        senses=tuple(senses),
        segment_warnings=tuple(warnings),
    )


def _partition_one_block(block: str) -> tuple[str | None, str | None]:
    """
    Partition one bracket block into etymology and attestation fragments.

    Args:
        block: One raw ``[...]`` block from the BT line body.

    Returns:
        Optional cleaned etymology block and optional attestation tail text.

    """
    stripped = block.strip()
    if not stripped:
        return None, None

    normalized_block = stripped
    if not normalized_block.startswith("["):
        normalized_block = f"[{stripped}]"

    block_text = _strip_outer_brackets(normalized_block)
    if re.search(r"\bCf\.\s", block_text, flags=re.IGNORECASE):
        parts = re.split(r"\bCf\.\s*", block_text, maxsplit=1, flags=re.IGNORECASE)
        attestation_tail = (
            _format_attestation_tail(parts[0]) if parts[0].strip() else None
        )
        etymology_block = None
        if len(parts) > 1 and parts[1].strip():
            etymology_block = f"[Cf. {parts[1].strip().rstrip('.')}.]"
        return etymology_block, attestation_tail

    if _looks_like_attestation(block_text):
        return None, _format_attestation_tail(block_text)

    return normalized_block, None


def _format_attestation_tail(block_text: str) -> str:
    """
    Format one attestation block body as a BT citation tail.

    Args:
        block_text: Inner text from one bracket block.

    Returns:
        Plain citation-tail text suitable for ``source_fragment_raw`` append.

    """
    rows = _parse_attestation_block(block_text)
    if not rows:
        return re.sub(r"\s+", " ", block_text).strip(" .;")
    parts: list[str] = []
    for row in rows:
        text = row.word.strip()
        if row.source:
            text = f"{text} {row.source}".strip() if text else row.source
        if text:
            parts.append(text)
    if parts:
        return "; ".join(parts)
    return re.sub(r"\s+", " ", block_text).strip(" .;")


def format_etymology_display(display: EtymologyDisplay) -> str:
    """
    Render parsed etymology rows as fixed-width browse text.

    Args:
        display: Parsed etymology payload.

    Returns:
        Multi-line etymology section text for the details pane.

    """
    lines: list[str] = ["Etymology"]
    if display.references:
        lines.extend(_format_reference_table(display.references))
    elif not display.attestations and display.unparsed:
        lines.append(display.unparsed[0])
    if display.references:
        lines.extend(
            f"Note: {fragment}"
            for fragment in display.unparsed
            if display.references
        )
    if display.attestations:
        lines.append("")
        lines.append("WARNING: misplaced attestations (not etymology)")
        for row in display.attestations:
            text = row.word.strip()
            if row.source:
                text = f"{text} [{row.source}]" if text else row.source
            if text:
                lines.append(text)
    if not display.references and not display.attestations and not display.unparsed:
        return ""
    return "\n".join(lines)


def _split_bracket_blocks(text: str) -> list[str]:
    """
    Split one etymology string into top-level bracket blocks.

    Args:
        text: Raw etymology text.

    Returns:
        Bracket-delimited blocks in source order.

    """
    blocks: list[str] = []
    depth = 0
    start = -1
    for index, char in enumerate(text):
        if char == "[":
            if depth == 0:
                start = index
            depth += 1
        elif char == "]":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start >= 0:
                blocks.append(text[start : index + 1])
                start = -1
    if not blocks and text.strip():
        return [text.strip()]
    trailing = ""
    if blocks:
        last_end = text.rfind(blocks[-1]) + len(blocks[-1])
        trailing = text[last_end:].strip()
    if trailing:
        blocks.append(trailing)
    return blocks


def _strip_outer_brackets(text: str) -> str:
    """
    Remove one surrounding ``[...]`` wrapper when present.

    Args:
        text: Candidate bracket block.

    Returns:
        Inner block text without outer brackets.

    """
    stripped = text.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped[1:-1].strip()
    return stripped


def _looks_like_attestation(text: str) -> bool:
    """
    Return whether one block looks like a misplaced OE attestation quote.

    Args:
        text: Candidate etymology block body.

    Returns:
        ``True`` when the block lacks comparative language tags and resembles
        an OE citation quote.

    """
    lang_tags = [
        _normalize_lang_label(match.group(1))
        for match in _ITALIC_SPAN_RE.finditer(text)
    ]
    has_lang_tag = any(
        label in _LANG_SOURCE_LABELS or _looks_like_lang_label(label)
        for label in lang_tags
    )
    if has_lang_tag:
        return False
    lowered = text.casefold()
    if _OE_ATTESTATION_CHARS_RE.search(text):
        return True
    if " cf. " in f" {lowered} ":
        return False
    return bool(_CITATION_RE.search(text) and not lang_tags)


def _parse_attestation_block(text: str) -> list[EtymologyTableRow]:
    """
    Parse one misplaced attestation block into warning rows.

    Args:
        text: Attestation block body.

    Returns:
        Warning rows for the browse details pane.

    """
    citations = [match.group(1).strip() for match in _CITATION_RE.finditer(text)]
    body = text
    for citation in citations:
        body = body.replace(citation, " ")
    body = re.sub(r"\s+", " ", body).strip(" .;")
    source = "; ".join(citations)
    if not body and not source:
        return []
    return [
        EtymologyTableRow(
            lang_source="",
            word=body,
            meaning="",
            source=source,
            is_attestation=True,
        )
    ]


def _parse_reference_block(text: str) -> tuple[list[EtymologyTableRow], str]:  # noqa: PLR0912, PLR0915
    """
    Parse one comparative etymology block into structured rows.

    Args:
        text: Comparative etymology block body.

    Returns:
        Parsed rows plus any residual unparsed text.

    """
    working = re.sub(r"^\s*Cf\.\s*", "", text, flags=re.IGNORECASE).strip()
    citations = [match.group(1).strip() for match in _CITATION_RE.finditer(working)]
    for citation in citations:
        working = working.replace(citation, f" @@CIT@@{citation}@@CIT@@ ")
    parts = _ITALIC_SPAN_RE.split(working)
    rows: list[EtymologyTableRow] = []
    pending_lang = ""
    pending_word = ""
    pending_meaning = ""
    pending_source = ""
    residual_parts: list[str] = []

    def flush_row() -> None:
        nonlocal pending_lang, pending_word, pending_meaning, pending_source
        if not any((pending_lang, pending_word, pending_meaning, pending_source)):
            return
        rows.append(
            EtymologyTableRow(
                lang_source=pending_lang,
                word=_clean_field(pending_word),
                meaning=_clean_field(pending_meaning),
                source=_clean_field(pending_source),
            )
        )
        pending_lang = ""
        pending_word = ""
        pending_meaning = ""
        pending_source = ""

    index = 0
    while index < len(parts):
        chunk = parts[index].strip()
        if not chunk:
            index += 1
            continue
        if index % 2 == 1:
            label = _normalize_lang_label(chunk)
            if label in _LANG_SOURCE_LABELS or _looks_like_lang_label(label):
                flush_row()
                pending_lang = chunk.strip()
            elif (pending_word and not pending_meaning) or pending_meaning:
                pending_meaning = _join_unique(pending_meaning, chunk.strip())
            elif not pending_meaning:
                pending_word = chunk.strip()
            index += 1
            continue

        chunk, chunk_citations = _extract_chunk_citations(chunk)
        if chunk_citations:
            pending_source = _join_unique(pending_source, chunk_citations)
        if ":" in chunk and pending_lang and not pending_word:
            before, after = chunk.split(":", 1)
            pending_word = before.strip(" ,;.")
            chunk = after
        chunk = chunk.strip(" ,:;.")
        if not chunk:
            index += 1
            continue
        if pending_lang and not pending_word:
            pending_word = chunk
        elif pending_lang and pending_word and not pending_meaning:
            if _looks_like_lang_label(_normalize_lang_label(chunk)):
                residual_parts.append(chunk)
            else:
                pending_meaning = chunk
        elif not pending_lang:
            if _looks_like_proper_name(chunk):
                flush_row()
                pending_lang = chunk
            else:
                residual_parts.append(chunk)
        else:
            pending_meaning = _join_unique(pending_meaning, chunk)
        index += 1

    flush_row()
    if citations:
        if rows and not rows[-1].source:
            rows[-1] = EtymologyTableRow(
                lang_source=rows[-1].lang_source,
                word=rows[-1].word,
                meaning=rows[-1].meaning,
                source=_join_unique("", "; ".join(citations)),
            )
    residual = "; ".join(part for part in residual_parts if part.strip())
    return rows, residual


def _extract_chunk_citations(chunk: str) -> tuple[str, str]:
    """
    Split inline citation markers out of one free-text chunk.

    Args:
        chunk: Free-text etymology fragment.

    Returns:
        Cleaned chunk text and joined citation labels.

    """
    citations = [
        match.group(1).strip()
        for match in re.finditer(r"@@CIT@@(.*?)@@CIT@@", chunk)
    ]
    cleaned = re.sub(r"@@CIT@@.*?@@CIT@@", " ", chunk)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, "; ".join(citations)


def _format_reference_table(rows: tuple[EtymologyTableRow, ...]) -> list[str]:
    """
    Render structured etymology rows as aligned text columns.

    Args:
        rows: Parsed comparative etymology rows.

    Returns:
        Header and body lines for fixed-width display.

    """
    headers = ("Lang/Source", "Word", "Meaning", "Source")
    widths = [len(header) for header in headers]
    rendered = [
        (
            row.lang_source,
            row.word,
            row.meaning,
            row.source,
        )
        for row in rows
    ]
    for cells in rendered:
        widths = [
            max(width, len(cell))
            for width, cell in zip(widths, cells, strict=True)
        ]
    header_line = "  ".join(
        header.ljust(width) for header, width in zip(headers, widths, strict=True)
    )
    body_lines = [
        "  ".join(cell.ljust(width) for cell, width in zip(cells, widths, strict=True))
        for cells in rendered
    ]
    return [header_line, *body_lines]


def _normalize_lang_label(label: str) -> str:
    """
    Normalize one language/source label for lookup comparisons.

    Args:
        label: Raw language/source label.

    Returns:
        Collapsed lowercase label used for set membership checks.

    """
    collapsed = re.sub(r"\s+", " ", label.strip().casefold())
    return collapsed.replace(". ", ".").replace(" .", ".")


def _looks_like_lang_label(label: str) -> bool:
    """
    Return whether one label resembles a BT comparative language tag.

    Args:
        label: Normalized language/source label.

    Returns:
        ``True`` when the label matches known BT abbreviation patterns.

    """
    if label in _LANG_SOURCE_LABELS:
        return True
    return bool(
        re.fullmatch(
            r"(?:o\.\s*)?[a-z]{1,6}(?:\.\s*[a-z]{1,6})*\.?",
            label,
        )
    )


def _looks_like_proper_name(text: str) -> bool:
    """
    Return whether one chunk looks like a bare proper-name source label.

    Args:
        text: Candidate source label chunk.

    Returns:
        ``True`` when the chunk is a single capitalized proper name.

    """
    return bool(re.fullmatch(r"[A-Z][A-Za-z.-]+", text.strip()))


def _clean_field(text: str) -> str:
    """
    Normalize one parsed etymology field for display.

    Args:
        text: Raw parsed field text.

    Returns:
        Trimmed single-line field value.

    """
    return re.sub(r"\s+", " ", text.strip(" ,:;."))


def _join_unique(left: str, right: str) -> str:
    """
    Join two semicolon-delimited field fragments without duplicates.

    Args:
        left: Existing field text.
        right: Additional field text.

    Returns:
        Combined field text with duplicate right-hand fragments removed.

    """
    if not left.strip():
        return right.strip()
    if not right.strip():
        return left.strip()
    if right.strip() in left:
        return left.strip()
    return f"{left.strip()}; {right.strip()}"
