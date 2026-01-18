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
from ..models.parsing import PreParsedDocument, ProvisionalSection, RawBlock
from ..settings import Settings
from .extractors import (
    AnyLLMConfig,
    LLMExtractor,
)
from .loaders import SourceLoader, from_tei
from .normalizers import normalize_elements_to_blocks

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
# Phase 2: OE filtering
# -----------------------------------------------------------------------------


class OEFilter:
    """
    Logic for filtering Old English text from raw blocks.
    """

    def looks_like_old_english(self, text: str) -> bool:
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

    def filter(self, blocks: Iterable[RawBlock]) -> list[RawBlock]:
        """
        Filter out blocks that do not look like Old English.

        Args:
            blocks: The blocks to filter.

        Returns:
            A list of blocks that look like Old English.

        """
        return [b for b in blocks if self.looks_like_old_english(b.text)]


# ---------- Phase 3: Mixed-mode + speaker-aware structural pre-parse ----------


class StructureParser:
    """
    Builds provisional sections from raw blocks with mixed-mode and speaker detection.
    """

    def detect_speaker(self, text: str) -> str | None:
        """
        Best-effort speaker cue detection.

        A speaker string looks like: "Saturnus:" / "Salomon:"
        or a name like: "Saturnus" / "Salomon"
        or a name like: "Saturnus cwæð:" / "Salomon cwæð:"
        or a name like: "Saturnus cwæð:" / "Salomon cwæð:"

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

    def is_heading(self, text: str) -> bool:
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

    def parse_heading(self, text: str) -> tuple[str | int | None, str | None]:
        """
        Parse a heading from a block of text.

        Args:
            text: The text to parse the heading from.

        Returns:
            A tuple of the heading number and title.

        """
        t = text.strip()
        # Match a year, including the 'A.D.' or 'AD' prefix.
        m = re.match(r"^(?:A\.D\.|AD)\s*(\d{3,4})\b", t)
        if m:
            return int(m.group(1)), None
        # Match a year, including the 'Her' prefix.  This is a common heading
        # format for medieval texts.
        m = re.match(r"^Her\s+(\d{3,4})\b", t)
        if m:
            return int(m.group(1)), None
        # Match a roman numeral chapter heading.
        if re.fullmatch(r"(?:[IVXLCDM]+)\.?", t):
            return t.rstrip("."), None
        # Match a roman numeral chapter heading, including the 'Cap.' prefix.
        m = re.match(r"^Cap\.\s*([IVXLCDM]+|\d+)\b\s*(.*)$", t)
        if m:
            n = int(m.group(1)) if m.group(1).isdigit() else m.group(1)
            return n, m.group(2) or None
        return None, t[:200]

    def get_kind(self, text: str) -> Literal["prose", "verse"]:
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

    def parse(self, blocks: list[RawBlock]) -> PreParsedDocument:
        """
        Build provisional sections from raw blocks and return as
        :class:`~oe_json_extractor.models.PreParsedDocument`.

        Args:
            blocks: The blocks to pre-parse.

        Returns:
            A pre-parsed document.

        """
        sections: list[ProvisionalSection] = []
        cur_title: str | None = None
        cur_number: str | int | None = None
        cur_blocks: list[RawBlock] = []

        def _flush_run(
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

        def _flush_blocks(blocks_for_heading: list[RawBlock]) -> None:
            if not blocks_for_heading:
                return
            run_blocks: list[RawBlock] = []
            run_kind: Literal["prose", "verse"] | None = None
            run_speaker: str | None = None

            for b in blocks_for_heading:
                k = self.get_kind(b.text)
                sp = self.detect_speaker(b.text)

                if run_kind is None:
                    run_kind = k
                    run_speaker = sp
                    run_blocks = [b]
                    continue

                if k != run_kind:
                    _flush_run(run_kind, run_blocks, run_speaker)
                    run_kind = k
                    run_speaker = sp
                    run_blocks = [b]
                    continue

                if sp and sp != run_speaker:
                    _flush_run(run_kind, run_blocks, run_speaker)
                    run_kind = k
                    run_speaker = sp
                    run_blocks = [b]
                    continue

                run_blocks.append(b)

            if run_kind is not None:
                _flush_run(run_kind, run_blocks, run_speaker)

        for b in blocks:
            if self.is_heading(b.text):
                _flush_blocks(cur_blocks)
                cur_blocks = []
                cur_number, cur_title = self.parse_heading(b.text)
                continue
            cur_blocks.append(b)

        _flush_blocks(cur_blocks)

        if not sections and blocks:
            sections = [
                ProvisionalSection(
                    title=None,
                    number=None,
                    kind=self.get_kind(blocks[0].text),
                    blocks=blocks,
                    page=blocks[0].page,
                    speaker_hint=self.detect_speaker(blocks[0].text),
                )
            ]

        return PreParsedDocument(sections=sections)


# ---------- Phase 4: Deterministic baseline ----------


class CanonicalConverter:
    """
    Converts pre-parsed documents into canonical OldEnglishText models.
    """

    def split_sentences(self, text: str) -> list[str]:
        """Split a paragraph of text into sentences."""
        parts = re.split(r"(?<=[\.\?\!])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def build(self, meta: TextMetadata, doc: PreParsedDocument) -> OldEnglishText:
        """Build a canonical document from a pre-parsed document."""
        root = Section(
            title=None, number=None, sections=[], paragraphs=None, lines=None
        )

        for psec in doc.sections:
            if psec.kind == "prose":
                paras: list[Paragraph] = []
                for b in psec.blocks:
                    sents = [
                        Sentence(text=s, source_page=b.page)
                        for s in self.split_sentences(b.text)
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
                            Line(
                                text=_ln,
                                number=line_no,
                                speaker=None,
                                source_page=b.page,
                            )
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

    def _aggregate_confidence(self, sec: Section) -> float | None:
        """Aggregate confidence for a section."""
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
                float(line.confidence)
                for line in sec.lines
                if line.confidence is not None
            )
        if sec.sections:
            for child in sec.sections:
                c = self._aggregate_confidence(child)
                if c is not None:
                    vals.append(float(c))
        return min(vals) if vals else None

    def propagate_confidence(self, doc: OldEnglishText) -> OldEnglishText:
        """Propagate confidence for a document."""

        def walk(sec: Section) -> None:
            if sec.sections:
                for child in sec.sections:
                    walk(child)
            if sec.confidence is None:
                agg = self._aggregate_confidence(sec)
                if agg is not None:
                    sec.confidence = agg  # type: ignore[attr-defined]

        walk(doc.content)
        return doc


class BaseDocumentIngestor:
    """
    Base orchestrator for document ingestion.
    """

    def ingest(
        self, source_path: Path, metadata: TextMetadata | None, **kwargs
    ) -> OldEnglishText:
        """
        Abstract ingest method to be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement ingest()")

    def _get_preparsed_doc(self, source_path: Path) -> PreParsedDocument:
        """
        Common helper to load, normalize, filter, and pre-parse a document.
        """
        elements = SourceLoader().load(source_path)
        blocks = normalize_elements_to_blocks(elements)
        oe_blocks = OEFilter().filter(blocks)
        return StructureParser().parse(oe_blocks)


class HeuristicDocumentIngestor(BaseDocumentIngestor):
    """
    Ingestor that uses deterministic heuristics (non-LLM).
    """

    def ingest(
        self,
        source_path: Path,
        metadata: TextMetadata | None,
        **kwargs,  # noqa: ARG002
    ) -> OldEnglishText:
        """
        Ingest using deterministic heuristics.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.

        Keyword Args:
            kwargs: Additional keyword arguments (ignored).

        Returns:
            A :class:`~oe_json_extractor.models.OldEnglishText` model.

        """
        if metadata is None:
            msg = "Heuristic ingestion requires metadata"
            raise ValueError(msg)
        pre = self._get_preparsed_doc(source_path)
        return CanonicalConverter().build(metadata, pre)


class TEIDocumentIngestor(BaseDocumentIngestor):
    """
    Ingestor for TEI XML documents.
    """

    def ingest(
        self,
        source_path: Path,
        metadata: TextMetadata | None,  # noqa: ARG002
        **kwargs,  # noqa: ARG002
    ) -> OldEnglishText:
        """
        Directly ingest TEI XML.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.

        Keyword Args:
            kwargs: Additional keyword arguments (ignored).

        Returns:
            A :class:`~oe_json_extractor.models.OldEnglishText` model.

        """
        return SourceLoader().load(source_path)


class LLMDocumentIngestor(BaseDocumentIngestor):
    """
    Ingestor that uses LLM-based extraction (langextract).
    """

    #: The directory containing the prompts.
    PROMPT_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "prompts"
    #: The non-model and non-mode specific prompt that details the output
    #: schema and general instructions.
    BASE_PROMPT: Final[str] = PROMPT_DIR / "general.md"

    def model_prompt(
        self, config: AnyLLMConfig, mode: Literal["verse", "prose"]
    ) -> str:
        """
        Get the model specific prompt for the model.

        Args:
            config: The configuration for the model.
            mode: The mode of the prompt: "verse" or "prose".

        Raises:
            ValueError: If the model is unknown.

        Returns:
            The model specific prompt.

        """
        if config.model == "qwen":
            prompt_file = self.PROMPT_DIR / "qwen" / f"{mode}.md"
        if config.model == "gemini":
            prompt_file = self.PROMPT_DIR / "gemini" / f"{mode}.md"
        if config.model == "openai":
            prompt_file = self.PROMPT_DIR / "openai" / f"{mode}.md"
        return prompt_file.read_text(encoding="utf-8").strip()

    def general_prompt(self) -> str:
        """
        Get the general prompt.
        """
        return self.BASE_PROMPT.read_text(encoding="utf-8").strip()

    def mode_prompt(self, mode: Literal["verse", "prose"]) -> str:
        """
        Get the mode specific prompt for the mode.

        Args:
            mode: The mode of the prompt: "verse" or "prose".

        Returns:
            The mode specific prompt.

        """
        prompt_file = self.PROMPT_DIR / f"{mode}.md"
        return prompt_file.read_text(encoding="utf-8").strip()

    def _build_prompt(
        self, config: AnyLLMConfig, mode: Literal["verse", "prose"]
    ) -> str:
        """
        Build a prompt for LLM extraction.

        There are three parts to the prompt:

        1. The model specific prompt for the mode: "verse" or "prose"
        2. The general prompt which defines the output schema
        3. The mode specific prompt: "verse" or "prose"

        Args:
            config: The configuration for the model.
            mode: The mode of the prompt: "verse" or "prose".

        Returns:
            The full prompt as a string.

        """
        return (
            self.model_prompt(config, mode)
            + "\n\n"
            + self.general_prompt()
            + "\n\n"
            + self.mode_prompt(mode)
        )

    def ingest(
        self,
        source_path: Path,
        metadata: TextMetadata | None,
        **kwargs,  # noqa: ARG002
    ) -> OldEnglishText:
        """
        Ingest using LLM extraction.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.

        Keyword Args:
            kwargs: Additional keyword arguments (ignored).

        Returns:
            A :class:`~oe_json_extractor.models.OldEnglishText` model.

        """
        settings = Settings()
        llm_config = settings.llm_config
        pre = self._get_preparsed_doc(source_path)

        extractor = LLMExtractor(config=llm_config)
        section_nodes: list[Section] = []

        for psec in pre.sections:
            chunk_text = "\n\n".join(b.text for b in psec.blocks if b.text.strip())
            if not chunk_text.strip():
                continue
            prompt = self._build_prompt(llm_config, psec.kind)
            meta = metadata
            if psec.speaker_hint:
                meta = TextMetadata(
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

            partial = extractor.extract(
                text=chunk_text,
                metadata=meta,
                prompt=prompt,
                prompt_preamble=preamble,
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
        return CanonicalConverter().propagate_confidence(doc)


class DocumentIngestor:
    """
    High-level orchestrator for document ingestion.
    """

    def ingest(
        self,
        source_path: Path,
        metadata: TextMetadata | None,
        *,
        use_llm: bool = True,
        **kwargs,
    ) -> OldEnglishText:
        """
        General-purpose ingest entrypoint.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.

        Keyword Args:
            use_llm: Whether to use LLM extraction.
            kwargs: Additional keyword arguments (ignored).

        """
        suffix = source_path.suffix.lower()
        if suffix in {".tei", ".xml"}:
            return TEIDocumentIngestor().ingest(source_path, metadata, **kwargs)

        if use_llm:
            return LLMDocumentIngestor().ingest(source_path, metadata, **kwargs)

        return HeuristicDocumentIngestor().ingest(source_path, metadata, **kwargs)


# -----------------------------------------------------------------------------
# Auto mode
# -----------------------------------------------------------------------------


def ingest_auto(
    source_path: Path,
    metadata: TextMetadata | None,
    *,
    prefer_tei: bool = True,
    use_langextract: bool = True,
    **kwargs,
) -> OldEnglishText:
    """
    Convenience entrypoint.
    """
    return DocumentIngestor().ingest(
        source_path,
        metadata,
        use_llm=use_langextract,
        prefer_tei=prefer_tei,
        **kwargs,
    )


def ingest_without_llm(
    source_path: Path, metadata: TextMetadata | None
) -> OldEnglishText:
    """Legacy wrapper for HeuristicDocumentIngestor().ingest."""
    return HeuristicDocumentIngestor().ingest(source_path, metadata)


def ingest_from_tei(source_path: Path) -> OldEnglishText:
    """Legacy wrapper for TEIDocumentIngestor().ingest."""
    return TEIDocumentIngestor().ingest(source_path, None)


def ingest_with_langextract(
    source_path: Path,
    metadata: TextMetadata | None,
    **kwargs,
) -> OldEnglishText:
    """Legacy wrapper for LLMDocumentIngestor().ingest."""
    return LLMDocumentIngestor().ingest(source_path, metadata, **kwargs)
