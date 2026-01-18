"""
End-to-end ingestion pipeline with:
- unstructured loading (HTML/PDF/TXT)
- Old English filtering
- mixed prose/verse splitting
- speaker-aware splitting heuristics
- optional langextract semantic structuring
- TEI override mode (direct canonical import)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from ..models import (
    Line,
    OldEnglishText,
    Paragraph,
    Section,
    Sentence,
    TextMetadata,
)
from .loaders import load_elements
from .normalizers import (
    normalize_elements_to_blocks,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

#: The minimum length of a block of text to be tested for Old English.
MIN_LENGTH_FOR_OE_DETECTION: Final[int] = 10
#: The minimum score for a block of text to be considered Old English.
MIN_SCORE_FOR_OE_DETECTION: Final[int] = 3
#: Old English marker characters (lower-case)
OLD_ENGLISH_MARKER_CHARS: Final[set[str]] = {
    "þ",
    "ð",
    "æ",
    "ā",
    "ē",
    "ī",
    "ō",
    "ū",
    "ȳ",
    "ġ",
    "ċ",
}
#: Common Old English tokens
OLD_ENGLISH_TOKENS: Final[set[str]] = {
    "þæt",
    "ond",
    "seo",
    "heo",
    "hie",
    "þa",
    "þu",
    "þe",
    "ic",
}
#: The minimum number of lines in a verse block to be considered verse.
NUM_VERSE_LINES: Final[int] = 2
#: The minimum average length of a line in a verse block to
#: be considered verse.
MIN_AVG_VERSE_LINE_LENGTH: Final[int] = 60
#: The regular expression to match speaker hints.
SPEAKER_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*([A-ZÆÞÐ][A-Za-zÆÞÐæþð\-]+)\s+(?:cwæ(?:ð|þ)|cwæð|andswarode|andswarode\b|sæde|sprec|andcwæ(?:ð|þ))\b",
    re.IGNORECASE,
)

# -----------------------------------------------------------------------------
# Phase 1: Source acquisition
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class RawBlock:
    """
    A raw block is a block of text that has been extracted from the source document.
    """

    #: The text of the block.
    text: str
    #: The category of the block.
    category: str
    #: The page number of the block.
    page: int | None = None


@dataclass(frozen=True)
class ProvisionalSection:
    """
    A provisional section is a section that has been parsed from the raw blocks,
    but not yet validated or structured.
    """

    #: The title of the section.
    title: str | None
    #: The number of the section.
    number: str | int | None
    #: The kind of the section: prose or verse.
    kind: Literal["prose", "verse"]
    #: Any :class:`RawBlock` objects that make up the section.
    blocks: list[RawBlock]
    #: The page number of the section.
    page: int | None = None
    #: An optional hint for dialogue chunks.
    speaker_hint: str | None = None  # Optional hint for dialogue chunks


@dataclass(frozen=True)
class PreParsedDocument:
    """
    A pre-parsed document is a document that has been parsed from the raw blocks,
    but not yet validated or structured.
    """

    #: The provisional sections of the document.
    sections: list[ProvisionalSection]


# -----------------------------------------------------------------------------
# Phase 2: OE filtering
# -----------------------------------------------------------------------------


def looks_like_old_english(text: str) -> bool:
    """
    Test if a block of text looks like Old English.

    Args:
        text: The text to test.

    Returns:
        True if the text looks like Old English, False otherwise.

    """
    lowered = text.lower()
    if len(lowered) < MIN_LENGTH_FOR_OE_DETECTION:
        return False

    score = 0
    for ch in OLD_ENGLISH_MARKER_CHARS:
        score += lowered.count(ch) * 2
    for token in ("þæt", "ond", "seo", "þa", "þe", "ic", "he", "hie", "we", "ge"):
        if token in lowered:
            score += 2
    for token in ("the ", "and ", "that ", "with ", "from "):
        if token in lowered:
            score -= 3

    return score >= MIN_SCORE_FOR_OE_DETECTION


def filter_old_english_blocks(blocks: Iterable[RawBlock]) -> list[RawBlock]:
    """
    Filter out blocks that do not look like Old English, based on a minimum
    length and score.

    Args:
        blocks: The blocks to filter.

    Returns:
        A list of blocks that look like Old English.

    """
    return [b for b in blocks if looks_like_old_english(b.text)]


# ---------- Phase 3: Mixed-mode + speaker-aware structural pre-parse ----------


def detect_speaker_hint(text: str) -> str | None:
    """
    Best-effort speaker cue detection. We do NOT remove speaker lines from text.
    We only use this to split chunks so langextract can label speakers more reliably.

    Args:
        text: The text to detect the speaker hint from.

    Returns:
        The speaker hint if detected, None otherwise.

    """
    for ln in text.splitlines():
        _ln = ln.strip()
        if not _ln:
            continue
        m = SPEAKER_RE.match(ln)
        if m:
            return m.group(1)
        # Common printed-dialogue style: "Saturnus:" / "Salomon:"
        m2 = re.match(r"^\s*([A-ZÆÞÐ][A-Za-zÆÞÐæþð\-]+)\s*:\s*$", ln)
        if m2:
            return m2.group(1)
        break
    return None


def preparse_structure(blocks: list[RawBlock]) -> PreParsedDocument:
    """
    Build provisional sections from raw blocks.

    Features:

    - Heading detection (chapters, annals, Roman numerals)
    - Block-level prose/verse detection
    - Automatic splitting of mixed prose/verse into separate sections
    - Speaker-aware splitting: If consecutive blocks are same kind but speaker
      hint changes, split into new provisional section.

    Args:
        blocks: The blocks to pre-parse.

    Returns:
        A pre-parsed document.

    """

    def is_heading(text: str) -> bool:
        """
        Test if a block of text is a heading.

        Args:
            text: The text to test.

        Returns:
            True if the text is a heading, False otherwise.

        """
        t = text.strip()
        if not t:
            return False
        if re.fullmatch(r"(?:[IVXLCDM]+)\.?", t):
            return True
        if re.match(r"^(Cap\.|CAP\.|Chapter\b|CHAPTER\b)", t):
            return True
        if re.match(r"^(?:A\.D\.|AD)\s*\d{3,4}\b", t):
            return True
        return bool(re.match(r"^Her\s+\d{3,4}\b", t))

    def parse_heading(text: str):
        """
        Parse a heading from a block of text.

        Args:
            text: The text to parse the heading from.

        Returns:
            A tuple of the heading number and title.

        """
        t = text.strip()
        m = re.match(r"^(?:A\.D\.|AD)\s*(\d{3,4})\b", t)
        if m:
            return int(m.group(1)), None
        m = re.match(r"^Her\s+(\d{3,4})\b", t)
        if m:
            return int(m.group(1)), None
        if re.fullmatch(r"(?:[IVXLCDM]+)\.?", t):
            return t.rstrip("."), None
        m = re.match(r"^Cap\.\s*([IVXLCDM]+|\d+)\b\s*(.*)$", t)
        if m:
            n = int(m.group(1)) if m.group(1).isdigit() else m.group(1)
            return n, m.group(2) or None
        return None, t[:200]

    def block_kind(text: str) -> Literal["prose", "verse"]:
        """
        Determine the kind of a block of text.

        Args:
            text: The text to determine the kind of.

        Returns:
            The kind of the block of text.

        """
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if len(lines) >= NUM_VERSE_LINES:
            avg = sum(len(ln) for ln in lines) / len(lines)
            if avg <= MIN_AVG_VERSE_LINE_LENGTH:
                return "verse"
        return "prose"

    sections: list[ProvisionalSection] = []
    cur_title: str | None = None
    cur_number: str | int | None = None
    cur_blocks: list[RawBlock] = []

    def flush_run(
        run_kind: Literal["prose", "verse"],
        run_blocks: list[RawBlock],
        speaker_hint: str | None,
    ) -> None:
        if not run_blocks:
            return
        sections.append(
            ProvisionalSection(
                title=cur_title,
                number=cur_number,
                kind=run_kind,
                blocks=run_blocks,
                page=run_blocks[0].page,
                speaker_hint=speaker_hint,
            )
        )

    def flush_blocks(blocks_for_heading: list[RawBlock]) -> None:
        """
        Flush blocks for a heading.  This means we are done with the heading and
        we are starting a new section.

        Args:
            blocks_for_heading: The blocks to flush for a heading.

        """
        if not blocks_for_heading:
            return
        # split by kind and speaker-hint runs
        run_blocks: list[RawBlock] = []
        run_kind: Literal["prose", "verse"] | None = None
        run_speaker: str | None = None

        for b in blocks_for_heading:
            k = block_kind(b.text)
            sp = detect_speaker_hint(b.text)

            if run_kind is None:
                run_kind = k
                run_speaker = sp
                run_blocks = [b]
                continue

            if k != run_kind:
                flush_run(run_kind, run_blocks, run_speaker)
                run_kind = k
                run_speaker = sp
                run_blocks = [b]
                continue

            # Same kind: split if speaker changes and is non-null (speaker-aware)
            if sp and sp != run_speaker:
                flush_run(run_kind, run_blocks, run_speaker)
                run_kind = k
                run_speaker = sp
                run_blocks = [b]
                continue

            run_blocks.append(b)

        if run_kind is not None:
            flush_run(run_kind, run_blocks, run_speaker)

    for b in blocks:
        if is_heading(b.text):
            flush_blocks(cur_blocks)
            cur_blocks = []
            cur_number, cur_title = parse_heading(b.text)
            continue
        cur_blocks.append(b)

    flush_blocks(cur_blocks)

    if not sections and blocks:
        sections = [
            ProvisionalSection(
                title=None,
                number=None,
                kind=block_kind(blocks[0].text),
                blocks=blocks,
                page=blocks[0].page,
                speaker_hint=detect_speaker_hint(blocks[0].text),
            )
        ]

    return PreParsedDocument(sections=sections)


# ---------- Phase 4: Deterministic baseline ----------


def split_sentences_oe(paragraph_text: str) -> list[str]:
    """
    Split a paragraph of text into sentences.

    Args:
        paragraph_text: The paragraph of text to split into sentences.

    Returns:
        A list of sentences.

    """
    parts = re.split(r"(?<=[\.\?\!])\s+", paragraph_text.strip())
    return [p.strip() for p in parts if p.strip()]


def build_canonical_from_preparse(
    meta: TextMetadata, doc: PreParsedDocument
) -> OldEnglishText:
    """
    Build a canonical document from a pre-parsed document.

    Args:
        meta: The metadata for the document.
        doc: The pre-parsed document.

    Returns:
        A canonical document.

    """
    root = Section(title=None, number=None, sections=[], paragraphs=None, lines=None)

    for psec in doc.sections:
        if psec.kind == "prose":
            paras: list[Paragraph] = []
            for b in psec.blocks:
                sents = [
                    Sentence(text=s, source_page=b.page)
                    for s in split_sentences_oe(b.text)
                ]
                if sents:
                    paras.append(
                        Paragraph(speaker=None, sentences=sents, source_page=b.page)
                    )
            sec = Section(
                title=psec.title,
                number=psec.number,
                paragraphs=paras or None,
                lines=None,
                sections=None,
                source_page=psec.page,
            )
        else:
            lines: list[Line] = []
            line_no = 1
            for b in psec.blocks:
                for ln in b.text.splitlines():
                    _ln = ln.strip()
                    if not _ln:
                        continue
                    lines.append(
                        Line(text=_ln, number=line_no, speaker=None, source_page=b.page)
                    )
                    line_no += 1
            sec = Section(
                title=psec.title,
                number=psec.number,
                paragraphs=None,
                lines=lines or None,
                sections=None,
                source_page=psec.page,
            )

        root.sections.append(sec)

    return OldEnglishText(metadata=meta, content=root)


def ingest_without_llm(source_path: Path, metadata: TextMetadata) -> OldEnglishText:
    """
    Ingest a document without using an LLM.

    Args:
        source_path: The path to the source document.
        metadata: The metadata for the document.

    Returns:
        A canonical document.

    """
    elements = load_elements(source_path)
    blocks = normalize_elements_to_blocks(elements)
    oe_blocks = filter_old_english_blocks(blocks)
    pre = preparse_structure(oe_blocks)
    return build_canonical_from_preparse(metadata, pre)


# ---------- TEI override mode ----------


def ingest_from_tei(source_path: Path) -> OldEnglishText:
    """
    Directly ingest TEI XML into canonical schema.  TEI XML is a standard XML
    format for representing text in a structured way in the humanities.

    This bypasses unstructured + langextract and is preferred when TEI is
    available.

    Args:
        source_path: The path to the source document.

    Returns:
        A canonical document.

    """
    from oe_json_extractor.ingest.exporters.tei import from_tei  # noqa: PLC0415

    xml = Path(source_path).read_text(encoding="utf-8")
    return from_tei(xml)


# ---------- Confidence aggregation ----------


def _aggregate_confidence_for_section(sec: Section) -> float | None:
    """
    Aggregate the confidence for a section.

    Args:
        sec: The section to aggregate the confidence for.

    Returns:
        The aggregated confidence.

    """
    vals: list[float] = []
    if sec.confidence is not None:
        vals.append(float(sec.confidence))
    if sec.paragraphs:
        for p in sec.paragraphs:
            if p.confidence is not None:
                vals.append(float(p.confidence))
            vals.extend(
                float(s.confidence) for s in p.sentences if s.confidence is not None
            )
    if sec.lines:
        vals.extend(
            float(line.confidence) for line in sec.lines if line.confidence is not None
        )
    if sec.sections:
        for child in sec.sections:
            c = _aggregate_confidence_for_section(child)
            if c is not None:
                vals.append(float(c))
    return min(vals) if vals else None


def propagate_confidence(doc: OldEnglishText) -> OldEnglishText:
    """
    Propagate the confidence for a document.

    Args:
        doc: The document to propagate the confidence for.

    Returns:
        The document with the confidence propagated.

    """

    def walk(sec: Section) -> None:
        """
        Walk the section and propagate the confidence.

        Args:
            sec: The section to walk and propagate the confidence for.

        """
        if sec.sections:
            for child in sec.sections:
                walk(child)
        if sec.confidence is None:
            agg = _aggregate_confidence_for_section(sec)
            if agg is not None:
                sec.confidence = agg  # type: ignore[attr-defined]

    walk(doc.content)
    return doc


# -----------------------------------------------------------------------------
# Phase 5: langextract integration (chunked + mixed-aware + speaker-aware)
# -----------------------------------------------------------------------------


def ingest_with_langextract(
    source_path: Path,
    metadata: TextMetadata,
    *,
    default_prompt_name: str = "oe_extract_v1.1.md",
    model_id: str = "gemini-2.5-flash",
) -> OldEnglishText:
    """
    Uses langextract to extract the structure of the document.  This is the
    preferred method of ingestion if TEI XML is not available.

    Args:
        source_path: The path to the source document.
        metadata: The metadata for the document.

    Keyword Args:
        default_prompt_name: The name of the default prompt to use.
        model_id: The ID of the model to use.

    Returns:
        A canonical document.

    """
    from oe_json_extractor.ingest.extractors.langextract_runner import (  # noqa: PLC0415
        LangExtractConfig,
        run_langextract_to_canonical,
    )

    elements = load_elements(source_path)
    blocks = normalize_elements_to_blocks(elements)
    oe_blocks = filter_old_english_blocks(blocks)
    pre = preparse_structure(oe_blocks)

    prompts = Path(__file__).resolve().parents[2] / "prompts"
    default_prompt = prompts / default_prompt_name
    prose_prompt = prompts / "oe_extract_prose_v1.1.md"
    verse_prompt = prompts / "oe_extract_verse_v1.1.md"

    cfg = LangExtractConfig(model_id=model_id)
    section_nodes: list[Section] = []

    for psec in pre.sections:
        chunk_text = "\n\n".join(b.text for b in psec.blocks if b.text.strip())
        if not chunk_text.strip():
            continue

        prompt_path = verse_prompt if psec.kind == "verse" else prose_prompt
        if not prompt_path.exists():
            prompt_path = default_prompt

        # Optionally include speaker hint to improve dialogue labeling (no text
        # modification)
        meta = metadata
        if psec.speaker_hint:
            # embed in metadata.source as an LLM hint without altering core
            # metadata fields (downstream can ignore this; it's purely a
            # prompt-side hint)
            meta = TextMetadata(  # noqa: F841
                title=metadata.title,
                author=metadata.author,
                source=(
                    f"{metadata.source} | speaker_hint={psec.speaker_hint}"
                    if metadata.source
                    else f"speaker_hint={psec.speaker_hint}"
                ),
                year=metadata.year,
                language=metadata.language,
                editor=metadata.editor,
                license=metadata.license,
            )

        preamble = None
    if psec.speaker_hint:
        preamble = (
            "DIALOGUE CONTEXT:\n"
            f"The following passage is spoken primarily by "
            f"{psec.speaker_hint}. Use this as a strong hint "
            "when assigning speakers.\n"
        )

    partial = run_langextract_to_canonical(
        text=chunk_text,
        metadata=metadata,
        prompt_path=prompt_path,
        prompt_preamble=preamble,
        config=cfg,
    )
    if partial.content.sections:
        section_nodes.extend(partial.content.sections)

    root_section = Section(
        title=None,
        number=None,
        sections=section_nodes or None,
        paragraphs=None,
        lines=None,
        source_page=None,
    )
    doc = OldEnglishText(metadata=metadata, content=root_section)
    return propagate_confidence(doc)


# -----------------------------------------------------------------------------
# Auto mode
# -----------------------------------------------------------------------------


def ingest_auto(
    source_path: Path,
    metadata: TextMetadata,
    *,
    prefer_tei: bool = True,
    use_langextract: bool = True,
    **kwargs,
) -> OldEnglishText:
    """
    Convenience entrypoint.

    If a TEI file is provided (suffix .tei/.xml) and prefer_tei=True, use TEI
    override.  Otherwise, use langextract pipeline if use_langextract=True, else
    deterministic baseline.

    Note:
        TEI XML is a standard XML format for representing text in a structured way
        in the humanities.

    Args:
        source_path: The path to the source document.
        metadata: The metadata for the document.

    Keyword Args:
        prefer_tei: Whether to prefer TEI over langextract.
        use_langextract: Whether to use langextract.
        **kwargs: Additional keyword arguments to pass to the langextract pipeline.

    Returns:
        A canonical document.

    """
    suffix = source_path.suffix.lower()
    if prefer_tei and suffix in {".tei", ".xml"}:
        return ingest_from_tei(source_path)
    if use_langextract:
        return ingest_with_langextract(source_path, metadata, **kwargs)
    return ingest_without_llm(source_path, metadata)
