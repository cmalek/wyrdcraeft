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
from collections.abc import Callable
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
from .loaders import SourceLoader
from .normalizers import normalize_elements_to_blocks

if TYPE_CHECKING:
    from collections.abc import Iterable

ProgressCallback = Callable[[int, int, str | None], None]


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
    "se",
    "þā",
    "þām",
    "hwæt",
    "wæs",
    "wǣron",
    "hē",
    "ne",
    "fela",
    "ymb",
    "hine",
    "mid",
    "ofer",
    "mon",
    "sum",
    "ānne",
    "bi",
    "beforan",
    "būtan",
    "foran",
    "fram",
    "innan",
    "neah",
    "toweard",
    "utan",
    "monig",
    "manig",
    "ilca",
    "ylca",
    "eal",
    "eall",
    "nan",
}
#: Old English inflectional endings
OLD_ENGLISH_ENDINGS: Final[set[str]] = {
    "um",
    "an",
    "ena",
    "as",
    "on",
    "að",
    "eþ",
    "edon",
    "don",
    "odon",
}
#: Roman to Arabic numeral mapping.
ROMAN_NUMBER_MAP: dict[str, int] = {
    "m": 1000,
    "d": 500,
    "c": 100,
    "l": 50,
    "x": 10,
    "v": 5,
    "i": 1,
}


def roman_to_arabic(source: str) -> int:
    """
    Convert a roman numeral string to an arabic integer.

    Args:
        source: The roman numeral string (e.g. "XIV").

    Returns:
        The arabic integer value.

    """
    n = [ROMAN_NUMBER_MAP[i] for i in source.lower() if i in ROMAN_NUMBER_MAP]
    if not n:
        return 0
    return sum([i if i >= n[min(j + 1, len(n) - 1)] else -i for j, i in enumerate(n)])


def is_roman_numeral(source: str) -> bool:
    """
    Check if a string is a roman numeral.
    """
    return bool(re.fullmatch(r"[IVXLCDMivxlcdm]+", source))


#: The regular expression to match speaker hints.
SPEAKER_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*([A-ZÆÞÐ][A-Za-zÆÞÐæþð\-]+)\s+(?:cwæ(?:ð|þ)|cwæð|andswarode|andswarode\b|sæde|sprec|andcwæ(?:ð|þ))\b",
    re.IGNORECASE,
)
#: The regular expression to match structural number markers.
MARKER_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*([\[\(]?[0-9]+[\]\.\)]?|[IVXLCDMivxlcdm]+[\]\.\)]?)(?:\s+|$)"
)

# -----------------------------------------------------------------------------
# Phase 2: OE filtering
# -----------------------------------------------------------------------------


class OEFilter:
    """
    Logic for filtering Old English text from raw blocks.
    """

    def __init__(self):
        self.oe_mode = False
        self._parser = StructureParser()

    def looks_like_old_english(self, text: str) -> bool:
        """
        Test if a block of text looks like Old English.

        Args:
            text: The text to test.

        Returns:
            True if the text looks like Old English, False otherwise.

        """
        lowered = text.lower()
        # Remove diacritics for token matching
        unmarked = (
            lowered.replace("ā", "a")
            .replace("ē", "e")
            .replace("ī", "i")
            .replace("ō", "o")
            .replace("ū", "u")
            .replace("ȳ", "y")
            .replace("ġ", "g")
            .replace("ċ", "c")
        )

        if len(lowered) < MIN_LENGTH_FOR_OE_DETECTION and not self.oe_mode:
            return False

        score = 0
        # Heavily weight special characters
        for ch in ("þ", "ð", "æ"):
            score += lowered.count(ch) * 4
        # Other markers
        for ch in ("ā", "ē", "ī", "ō", "ū", "ȳ", "ġ", "ċ"):
            score += lowered.count(ch) * 2

        # Token matching
        words = re.findall(r"\w+", lowered)
        unmarked_words = re.findall(r"\w+", unmarked)

        for token in OLD_ENGLISH_TOKENS:
            if token in words or token in unmarked_words:
                score += 3

        # Ending matching
        for ending in OLD_ENGLISH_ENDINGS:
            if any(w.endswith(ending) for w in words):
                score += 2

        # Negative markers for Modern English
        for token in ("the ", "that ", "with ", "from "):
            if token in lowered:
                score -= 4

        # Thresholds
        strong_oe_threshold = 6
        exit_oe_threshold = -2

        if score >= strong_oe_threshold:
            self.oe_mode = True
            return True

        if self.oe_mode:
            if score <= exit_oe_threshold:
                self.oe_mode = False
                return False
            return True

        return score >= MIN_SCORE_FOR_OE_DETECTION

    def filter(self, blocks: Iterable[RawBlock]) -> list[RawBlock]:
        """
        Filter out blocks that do not look like Old English.

        A block is kept if at least one non-empty line within the block
        looks like Old English OR is a heading. This avoids rejecting
        long verse blocks that contain a small amount of editorial or
        Modern English text (e.g. titles in <pre> blocks).
        """
        kept: list[RawBlock] = []

        for b in blocks:
            lines = [ln for ln in b.text.splitlines() if ln.strip()]
            if not lines:
                continue

            if any(
                self.looks_like_old_english(ln) or self._parser.is_heading(ln)
                for ln in lines
            ):
                kept.append(b)

        return kept


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
        # Roman numeral chapter heading: "I. THE PASSING OF SCYLD." or just "I."
        if re.match(r"^[IVXLCDM]+\.?(\s+|$)", t):
            return True
        # All caps heading: "BEÓWULF."
        if re.fullmatch(r"[A-ZÆÞÐ\s\-]{3,}\.?", t):
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

        # Match a roman numeral chapter heading with optional title.
        m = re.match(r"^([IVXLCDM]+)\.?\s+(.*)$", t)
        if m:
            return roman_to_arabic(m.group(1)), m.group(2).strip()

        # Match a standalone roman numeral chapter heading.
        if re.fullmatch(r"(?:[IVXLCDM]+)\.?", t):
            return roman_to_arabic(t.rstrip(".")), None

        # Match a roman numeral chapter heading, including the 'Cap.' prefix.
        m = re.match(r"^Cap\.\s*([IVXLCDM]+|\d+)\b\s*(.*)$", t)
        if m:
            val = m.group(1)
            if val.isdigit():
                n = int(val)
            elif is_roman_numeral(val):
                n = roman_to_arabic(val)
            else:
                n = val
            return n, m.group(2) or None

        # Otherwise treat the whole thing as a title
        return None, t.rstrip(".")

    def parse(self, blocks: list[RawBlock]) -> PreParsedDocument:
        """
        Build provisional sections from raw blocks and return as
        :class:`~wyrdcraeft.models.PreParsedDocument`.

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
                k = b.kind
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
            # Check for kind switch within a block if it's not a heading
            if self.is_heading(b.text):
                _flush_blocks(cur_blocks)
                cur_blocks = []
                cur_number, cur_title = self.parse_heading(b.text)
                continue
            cur_blocks.append(b)

        _flush_blocks(cur_blocks)

        if not sections and blocks:
            # If no sections were created (e.g. no headings), create one
            # based on the runs detected in _flush_blocks
            _flush_blocks(blocks)

        return PreParsedDocument(sections=sections)


# ---------- Phase 4: Deterministic baseline ----------


class CanonicalConverter:
    """
    Converts pre-parsed documents into canonical OldEnglishText models.
    """

    def extract_marker(self, text: str) -> tuple[str | None, str]:
        """
        Extract a structural number marker from the start of a string.

        Args:
            text: The text to extract the marker from.

        Returns:
            A tuple of the marker (as a string) and the remaining text.

        """
        match = MARKER_RE.match(text)
        if match:
            marker = match.group(1)
            # Strip punctuation around the marker before returning it
            clean_marker = marker.strip("[]().")
            # Remove the marker and any trailing whitespace from the start
            remaining = text[match.end() :]
            return clean_marker, remaining
        return None, text

    def split_sentences(self, text: str) -> list[str]:
        """
        Split a paragraph of text into sentences, handling terminal
        punctuation inside quotes or parentheses.

        Args:
            text: The text to split into sentences.

        Returns:
            A list of sentences.

        """
        # Split at standard sentence ends followed by space.
        # We use a non-lookbehind approach to avoid fixed-width limitations.
        # This matches punctuation (optionally followed by quote/paren) AND the space.
        pattern = r"([\.\?\!][\"\'\)]?\s+)"
        parts = re.split(pattern, text.strip())

        sentences = []
        # re.split with capturing group returns [text, separator, text, separator...]
        for i in range(0, len(parts) - 1, 2):
            sentences.append((parts[i] + parts[i + 1]).strip())  # noqa: PERF401
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1].strip())

        return [s for s in sentences if s]

    def build(self, meta: TextMetadata, doc: PreParsedDocument) -> OldEnglishText:  # noqa: PLR0912
        """
        Build a canonical document from a pre-parsed document.

        Args:
            meta: The metadata for the document.
            doc: The pre-parsed document.

        Returns:
            A canonical document.

        """
        root = Section(
            title=None, number=None, sections=[], paragraphs=None, lines=None
        )

        for psec in doc.sections:
            if psec.kind == "prose":
                paras: list[Paragraph] = []
                for b in psec.blocks:
                    sents: list[Sentence] = []
                    for s in self.split_sentences(b.text):
                        marker, cleaned_text = self.extract_marker(s)
                        if marker and marker.isdigit():
                            final_marker = int(marker)
                        elif marker and is_roman_numeral(marker):
                            final_marker = roman_to_arabic(marker)
                        else:
                            final_marker = marker

                        sents.append(
                            Sentence(
                                text=cleaned_text,
                                number=final_marker,
                                source_page=b.page,
                            )
                        )
                    if sents:
                        paras.append(
                            Paragraph(
                                speaker=psec.speaker_hint,
                                sentences=sents,
                                source_page=b.page,
                            )
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
                pending_marker: str | None = None
                for b in psec.blocks:
                    for ln in b.text.splitlines():
                        if not ln.strip():
                            continue
                        marker, cleaned_text = self.extract_marker(ln)

                        # If the line was ONLY a marker, save it for the next line
                        if marker and not cleaned_text.strip():
                            pending_marker = marker
                            continue

                        # If we have a marker on this line, use it.
                        # Otherwise use the pending marker if available.
                        effective_marker = marker or pending_marker
                        pending_marker = None  # Reset

                        if effective_marker and effective_marker.isdigit():
                            final_number = int(effective_marker)
                        elif effective_marker and is_roman_numeral(effective_marker):
                            final_number = roman_to_arabic(effective_marker)
                        else:
                            final_number = None

                        # For verse, we want to keep leading whitespace of the
                        # cleaned text if the marker was removed.
                        lines.append(
                            Line(
                                text=cleaned_text.rstrip(),
                                number=final_number,
                                speaker=psec.speaker_hint,
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
        """
        Aggregate confidence for a section.

        Args:
            sec: The section to aggregate confidence for.

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
        """
        Propagate confidence for a document.

        Args:
            doc: The document to propagate confidence for.

        Returns:
            The document with confidence propagated.

        """

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
        self,
        source_path: Path,
        metadata: TextMetadata | None,
        progress_callback: ProgressCallback | None = None,
        **kwargs,
    ) -> OldEnglishText:
        """
        Abstract ingest method to be overridden by subclasses.
        """
        msg = "Subclasses must implement ingest()"
        raise NotImplementedError(msg)

    def _get_preparsed_doc(
        self, source_path: Path, progress_callback: ProgressCallback | None = None
    ) -> PreParsedDocument:
        """
        Common helper to load, normalize, filter, and pre-parse a document.
        """
        if progress_callback:
            progress_callback(0, 100, "Loading source document")
        elements = SourceLoader().load(source_path)
        raw_text = (
            source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        )

        if progress_callback:
            progress_callback(25, 100, "Normalizing text blocks")
        blocks = normalize_elements_to_blocks(elements, raw_text=raw_text)

        if progress_callback:
            progress_callback(50, 100, "Filtering Old English content")
        oe_blocks = OEFilter().filter(blocks)

        if progress_callback:
            progress_callback(75, 100, "Parsing document structure")
        result = StructureParser().parse(oe_blocks)

        if progress_callback:
            progress_callback(100, 100, "Pre-parsing complete")
        return result


class HeuristicDocumentIngestor(BaseDocumentIngestor):
    """
    Ingestor that uses deterministic heuristics (non-LLM).
    """

    def ingest(
        self,
        source_path: Path,
        metadata: TextMetadata | None,
        progress_callback: ProgressCallback | None = None,
        **kwargs,  # noqa: ARG002
    ) -> OldEnglishText:
        """
        Ingest using deterministic heuristics.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.
            progress_callback: Optional callback for progress reporting.

        Keyword Args:
            kwargs: Additional keyword arguments (ignored).

        Returns:
            A :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        if progress_callback:
            progress_callback(0, 1, "Starting heuristic ingestion")
        if metadata is None:
            msg = "Heuristic ingestion requires metadata"
            raise ValueError(msg)
        pre = self._get_preparsed_doc(source_path, progress_callback=progress_callback)
        result = CanonicalConverter().build(metadata, pre)
        if progress_callback:
            progress_callback(1, 1, "Heuristic ingestion complete")
        return result


class TEIDocumentIngestor(BaseDocumentIngestor):
    """
    Ingestor for TEI XML documents.
    """

    def ingest(
        self,
        source_path: Path,
        metadata: TextMetadata | None,  # noqa: ARG002
        progress_callback: ProgressCallback | None = None,
        **kwargs,  # noqa: ARG002
    ) -> OldEnglishText:
        """
        Directly ingest TEI XML.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.
            progress_callback: Optional callback for progress reporting.

        Keyword Args:
            kwargs: Additional keyword arguments (ignored).

        Returns:
            A :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        if progress_callback:
            progress_callback(0, 1, "Starting TEI ingestion")
        result = SourceLoader().load(source_path)
        if progress_callback:
            progress_callback(1, 1, "TEI ingestion complete")
        return result


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
            prompt_file = self.PROMPT_DIR / "models" / "qwen" / f"{mode}.md"
        if config.model == "gemini":
            prompt_file = self.PROMPT_DIR / "models" / "gemini" / f"{mode}.md"
        if config.model == "openai":
            prompt_file = self.PROMPT_DIR / "models" / "openai" / f"{mode}.md"
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
        general = self.general_prompt()
        if mode == "verse":
            # Remove Paragraph and Sentence schemas to prevent the LLM from using them
            general = re.sub(
                r"---.*PARAGRAPH SCHEMA.*?---", "---", general, flags=re.DOTALL
            )
            general = re.sub(
                r"---.*SENTENCE SCHEMA.*?---", "---", general, flags=re.DOTALL
            )
            # Remove prose rules from Section schema
            general = general.replace("- paragraphs (prose)\n", "")
            general = general.replace(
                "- Never populate more than one of: sections, paragraphs, lines.",
                "- NEVER populate paragraphs or sentences; ONLY use lines.",
            )

        return (
            self.model_prompt(config, mode)
            + "\n\n"
            + general
            + "\n\n"
            + self.mode_prompt(mode)
        )

    def ingest(  # noqa: PLR0912
        self,
        source_path: Path,
        metadata: TextMetadata | None,
        progress_callback: ProgressCallback | None = None,
        llm_config: AnyLLMConfig | None = None,
        **kwargs,  # noqa: ARG002
    ) -> OldEnglishText:
        """
        Ingest using LLM extraction.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.
            progress_callback: Optional callback for progress reporting.
            llm_config: Optional LLM configuration to use.

        Keyword Args:
            kwargs: Additional keyword arguments (ignored).

        Returns:
            A :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        if llm_config is None:
            settings = Settings()
            llm_config = settings.llm_config

        pre = self._get_preparsed_doc(source_path, progress_callback=progress_callback)

        extractor = LLMExtractor(config=llm_config)
        section_nodes: list[Section] = []

        total_sections = len(pre.sections)
        if progress_callback:
            progress_callback(
                0, total_sections, f"Found {total_sections} chunks. Starting extraction"
            )

        for i, psec in enumerate(pre.sections):
            if progress_callback:
                progress_callback(
                    i, total_sections, f"Extracting chunk {i + 1}/{total_sections}"
                )

            if psec.kind == "verse":
                chunk_text = "\n".join(b.text for b in psec.blocks if b.text.strip())
            else:
                chunk_text = "\n\n".join(b.text for b in psec.blocks if b.text.strip())

            if not chunk_text.strip():
                continue
            prompt = self._build_prompt(llm_config, psec.kind)
            meta = metadata
            if psec.speaker_hint:
                meta = TextMetadata(
                    title=metadata.title if metadata else None,
                    author=metadata.author if metadata else None,
                    source=(
                        f"{metadata.source} | speaker_hint={psec.speaker_hint}"
                        if metadata and metadata.source
                        else f"speaker_hint={psec.speaker_hint}"
                    ),
                    year=metadata.year if metadata else None,
                    language=metadata.language if metadata else None,
                    editor=metadata.editor if metadata else None,
                    license=metadata.license if metadata else None,
                )

            preamble = None
            if psec.speaker_hint:
                preamble = (
                    "DIALOGUE CONTEXT:\n"
                    f"The following passage is spoken primarily by "
                    f"{psec.speaker_hint}. Use this as a strong hint "
                    "when assigning speakers.\n"
                )

            if psec.kind == "verse":
                verse_preamble = (
                    "VERSE EXTRACTION MODE (EXTREMELY STRICT):\n"
                    "- Input text is line-broken Old English poetry.\n"
                    "- Each physical line MUST become EXACTLY one 'Line' object.\n"
                    "- DO NOT split lines at periods, semicolons, or gaps.\n"
                    "- DO NOT merge lines into paragraphs or sentences.\n"
                    "- PRESERVE all internal spaces (the caesura). If a line has 6 spaces, keep 6 spaces.\n"  # noqa: E501
                    "- PRESERVE all leading spaces/indentation.\n"
                    "- IGNORE all grammatical rules; follow physical line breaks ONLY.\n"  # noqa: E501
                    "- The number of 'Line' objects in your JSON MUST match the number of lines in the input.\n"  # noqa: E501
                )
                preamble = (preamble or "") + verse_preamble

            partial = extractor.extract(
                text=chunk_text,
                metadata=meta,
                prompt=prompt,
                prompt_preamble=preamble,
            )

            # SAFETY NET: If we are in verse mode but the LLM returned
            # paragraphs/sentences, force-convert them back to lines using the
            # original physical line breaks.
            if psec.kind == "verse" and partial.content.paragraphs:
                # Re-extract lines from chunk_text directly
                lines: list[Line] = []
                for j, ln in enumerate(chunk_text.splitlines(), 1):
                    _ln = ln.rstrip()
                    if not _ln:
                        continue
                    # Try to see if the LLM found a speaker for this chunk
                    speaker = (
                        partial.content.paragraphs[0].speaker
                        if partial.content.paragraphs
                        else None
                    )
                    lines.append(
                        Line(
                            text=_ln,
                            number=j,
                            speaker=speaker,
                            source_page=psec.page,
                        )
                    )
                partial.content.paragraphs = None
                partial.content.lines = lines

            # If the LLM returned a section with content, use it.
            # If it returned a section with subsections, use those.
            if partial.content.sections:
                section_nodes.extend(partial.content.sections)
            elif partial.content.paragraphs or partial.content.lines:
                section_nodes.append(partial.content)

        if progress_callback:
            progress_callback(total_sections, total_sections, "Extraction complete")

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
        use_llm: bool = False,
        progress_callback: ProgressCallback | None = None,
        llm_config: AnyLLMConfig | None = None,
        **kwargs,
    ) -> OldEnglishText:
        """
        General-purpose ingest entrypoint.

        Args:
            source_path: The path to the source document.
            metadata: The metadata for the document.

        Keyword Args:
            use_llm: Whether to use LLM extraction.
            progress_callback: Optional callback for progress reporting.
            llm_config: Optional LLM configuration to use.
            kwargs: Additional keyword arguments (ignored).

        """
        if isinstance(source_path, Path):
            suffix = source_path.suffix.lower()
            if suffix in {".tei", ".xml"}:
                return TEIDocumentIngestor().ingest(
                    source_path, metadata, progress_callback=progress_callback, **kwargs
                )

        if use_llm:
            return LLMDocumentIngestor().ingest(
                source_path,
                metadata,
                progress_callback=progress_callback,
                llm_config=llm_config,
                **kwargs,
            )

        return HeuristicDocumentIngestor().ingest(
            source_path, metadata, progress_callback=progress_callback, **kwargs
        )


# -----------------------------------------------------------------------------
# Auto mode
# -----------------------------------------------------------------------------


def ingest_auto(
    source_path: Path,
    metadata: TextMetadata | None,
    *,
    use_llm: bool = False,
    progress_callback: ProgressCallback | None = None,
    llm_config: AnyLLMConfig | None = None,
    **kwargs,
) -> OldEnglishText:
    """
    Convenience entrypoint.

    Args:
        source_path: The path to the source document.
        metadata: The metadata for the document.
        use_llm: Whether to use LLM extraction.
        progress_callback: Optional callback for progress reporting.
        llm_config: Optional LLM configuration to use.
        kwargs: Additional keyword arguments (ignored).

    Returns:
        A :class:`~wyrdcraeft.models.OldEnglishText` model.

    """
    return DocumentIngestor().ingest(
        source_path,
        metadata,
        use_llm=use_llm,
        progress_callback=progress_callback,
        llm_config=llm_config,
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
