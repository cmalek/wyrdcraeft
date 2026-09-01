from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from acdh_tei_pyutils.tei import TeiReader  # type: ignore[import-untyped]
from delb import Document

from ..models import (
    Line,
    OldEnglishText,
    Paragraph,
    Section,
    Sentence,
    TextMetadata,
)
from .normalizers import split_prose_and_verse_runs

if TYPE_CHECKING:
    from ..models.parsing import RawBlock

#: The TEI namespace.
TEI_NS: Final[str] = "http://www.tei-c.org/ns/1.0"


class BaseSourceLoader:
    """Base class for source loaders."""

    def load(self, source: str | Path) -> list[RawBlock] | OldEnglishText:
        """
        Load raw blocks or canonical text from a source.

        Args:
            source: The source to load the document from.

        Returns:
            A list of :class:`~wyrdcraeft.models.parsing.RawBlock`
            or an :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        raise NotImplementedError


class FileSourceLoader(BaseSourceLoader):
    """Loader for local UTF-8 ``.txt`` files."""

    def load(self, source: str | Path) -> list[RawBlock]:
        """
        Load a local ``.txt`` file as prose/verse :class:`RawBlock` runs.

        Args:
            source: The source path to load the document from.

        Returns:
            A list of :class:`~wyrdcraeft.models.parsing.RawBlock`.

        Raises:
            ValueError: If the source suffix is not ``.txt`` or ``.text``.

        """
        source_path = Path(source)
        suffix = source_path.suffix.lower()
        if suffix not in {".txt", ".text"}:
            msg = f"Unsupported source format: {suffix}"
            raise ValueError(msg)
        text = source_path.read_text(encoding="utf-8")
        return split_prose_and_verse_runs(text, category=None, page=None)


class TEISourceLoader(BaseSourceLoader):
    """Loader for TEI XML documents."""

    def load(self, source: str | Path) -> OldEnglishText:
        """
        Load a TEI XML document.

        Args:
            source: The source to load the document from.

        Returns:
            An :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        source_path = Path(source)
        if source_path.exists():
            xml = source_path.read_text(encoding="utf-8")
        else:
            # Handle source as raw XML string if it doesn't exist as a path
            xml = str(source)
        return self.load_from_tei(xml)

    def load_from_tei(self, tei_xml: str) -> OldEnglishText:
        """
        Import TEI XML using delb and acdh-tei-pyutils.

        Args:
            tei_xml: The TEI XML to import.

        Returns:
            An :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        tei_reader = TeiReader(tei_xml)
        ns = tei_reader.ns_tei
        doc = Document(tei_xml)

        meta = self._extract_metadata(tei_reader)
        content = self._parse_body(doc, ns)

        return OldEnglishText(metadata=meta, content=content)

    def _extract_metadata(self, tei_reader: TeiReader) -> TextMetadata:
        """
        Extract metadata from TEI header.

        Args:
            tei_reader: The TEI reader to extract metadata from.

        Returns:
            A :class:`~wyrdcraeft.models.TextMetadata` model.

        """
        title_els = tei_reader.any_xpath(".//tei:titleStmt/tei:title")
        author_els = tei_reader.any_xpath(".//tei:titleStmt/tei:author")
        source_els = tei_reader.any_xpath(".//tei:publicationStmt/tei:p")

        return TextMetadata(
            title=title_els[0].text.strip()
            if title_els and title_els[0].text
            else "unknown",
            author=author_els[0].text.strip()
            if author_els and author_els[0].text
            else None,
            source=source_els[0].text.strip()
            if source_els and source_els[0].text
            else None,
        )

    def _parse_body(self, doc: Document, ns: dict) -> Section:
        """
        Parse the TEI body.

        Args:
            doc: The document to parse the body from.
            ns: The namespace to use.

        Returns:
            A :class:`~wyrdcraeft.models.Section` model.

        """
        body_els = doc.xpath("//tei:body", namespaces=ns)
        if not body_els:
            return Section(title=None, number=None)

        body = body_els[0]
        body_divs = body.xpath("./tei:div", namespaces=ns)
        return self._parse_section(body_divs[0] if body_divs else body, ns)

    def _parse_section(self, section_node, ns: dict) -> Section:
        """
        Parse a <div> into a Section model.

        Args:
            section_node: The node to parse the section from.
            ns: The namespace to use.

        Returns:
            A :class:`~wyrdcraeft.models.Section` model.

        """
        n_attr = section_node.attributes.get("n")
        head_el = section_node.xpath("./tei:head", namespaces=ns)
        sp_attr = section_node.attributes.get("source_page")
        conf_attr = section_node.attributes.get("confidence")

        sec = Section(
            title=head_el[0].full_text.strip() if head_el else None,
            number=str(n_attr) if n_attr is not None else None,
            source_page=str(sp_attr) if sp_attr is not None else None,
            confidence=float(str(conf_attr)) if conf_attr is not None else None,
        )

        self._fill_section_content(sec, section_node, ns)
        return sec

    def _fill_section_content(self, sec: Section, node, ns: dict) -> None:
        """
        Fill paragraphs, lines, and subsections for a section.

        Args:
            sec: The section to fill the content for.
            node: The node to fill the content from.
            ns: The namespace to use.

        """
        paragraphs = []
        lines: list[Line] = []

        for child in node.xpath(
            "./tei:p | ./tei:sp | ./tei:lg | ./tei:div", namespaces=ns
        ):
            if child.local_name == "p":
                paragraphs.append(self._parse_paragraph(child, ns))
            elif child.local_name == "sp":
                self._handle_sp(child, paragraphs, lines, ns)
            elif child.local_name == "lg":
                lines.extend(self._parse_lg(child, ns))
            elif child.local_name == "div":
                if sec.sections is None:
                    sec.sections = []
                sec.sections.append(self._parse_section(child, ns))

        if paragraphs:
            sec.paragraphs = paragraphs
        if lines:
            if sec.paragraphs:
                if sec.sections is None:
                    sec.sections = []
                sec.sections.append(Section(title="Verse", lines=lines))
            else:
                sec.lines = lines

    def _parse_paragraph(
        self, p_node, ns: dict, speaker: str | None = None
    ) -> Paragraph:
        """
        Parse a <p> element.

        Args:
            p_node: The node to parse the paragraph from.
            ns: The namespace to use.
            speaker: The speaker to use.

        Returns:
            A :class:`~wyrdcraeft.models.Paragraph` model.

        """
        sents = []
        for s in p_node.xpath(".//tei:s", namespaces=ns):
            s_n = s.attributes.get("n")
            s_sp = s.attributes.get("source_page")
            s_conf = s.attributes.get("confidence")
            sents.append(
                Sentence(
                    text=s.full_text.strip(),
                    number=str(s_n) if s_n is not None else None,
                    source_page=str(s_sp) if s_sp is not None else None,
                    confidence=float(str(s_conf)) if s_conf is not None else None,
                )
            )

        if not sents and p_node.full_text.strip():
            sents = [Sentence(text=p_node.full_text.strip())]

        p_sp = p_node.attributes.get("source_page")
        p_conf = p_node.attributes.get("confidence")
        return Paragraph(
            speaker=speaker,
            sentences=sents,
            source_page=str(p_sp) if p_sp is not None else None,
            confidence=float(str(p_conf)) if p_conf is not None else None,
        )

    def _handle_sp(
        self, sp_node, paragraphs: list[Paragraph], lines: list[Line], ns: dict
    ) -> None:
        """
        Handle <sp> elements containing prose or verse.

        Args:
            sp_node: The node to handle the <sp> element from.
            paragraphs: The list of paragraphs to append the <p> elements to.
            lines: The list of lines to append the <lg> elements to.
            ns: The namespace to use.

        """
        who = str(who_attr) if (who_attr := sp_node.attributes.get("who")) else None
        for child in sp_node.xpath("./tei:p | ./tei:lg", namespaces=ns):
            if child.local_name == "p":
                paragraphs.append(self._parse_paragraph(child, ns, speaker=who))
            elif child.local_name == "lg":
                lines.extend(self._parse_lg(child, ns, speaker=who))

    def _parse_lg(self, lg_node, ns: dict, speaker: str | None = None) -> list[Line]:
        """
        Parse an <lg> element into Line models.

        Args:
            lg_node: The node to parse the <lg> element from.
            ns: The namespace to use.
            speaker: The speaker to use.

        Returns:
            A list of :class:`~wyrdcraeft.models.Line` models.

        """
        lines = []
        if speaker is None:
            curr = lg_node
            while curr is not None:
                if curr.local_name == "sp":
                    speaker = str(who) if (who := curr.attributes.get("who")) else None
                    break
                curr = curr.parent

        for l_el in lg_node.xpath(".//tei:l", namespaces=ns):
            l_n = l_el.attributes.get("n")
            l_sp = l_el.attributes.get("source_page")
            l_conf = l_el.attributes.get("confidence")
            lines.append(
                Line(
                    text=l_el.full_text.strip(),
                    number=int(str(l_n)) if l_n and str(l_n).isdigit() else None,
                    speaker=speaker,
                    source_page=str(l_sp) if l_sp is not None else None,
                    confidence=float(str(l_conf)) if l_conf is not None else None,
                )
            )
        return lines


class SourceLoader:
    """Factory class for creating and using the correct source loader."""

    @staticmethod
    def get_loader(source: str | Path) -> BaseSourceLoader:
        """
        Factory method to choose the right loader from what type of source is
        provided.

        - HTTP/HTTPS URLs are rejected; ``source convert`` is local-only.
        - If the source is a local file, return an instance of
          :class:`~wyrdcraeft.ingest.loaders.FileSourceLoader`.
        - If the source is a TEI XML string, return an instance of
          :class:`~wyrdcraeft.ingest.loaders.TEISourceLoader`.

        Args:
            source: The source to load the document from.

        Returns:
            A subclass of
            :class:`~wyrdcraeft.ingest.loaders.BaseSourceLoader`.

        Raises:
            ValueError: If the source is an HTTP or HTTPS URL.

        """
        source_str = str(source)
        if source_str.startswith(("http://", "https://")):
            msg = "source convert accepts a local .txt or TEI/XML path only"
            raise ValueError(msg)

        source_path = Path(source)
        if source_path.suffix.lower() in {".xml", ".tei"} or (
            not source_path.exists() and "<TEI" in source_str
        ):
            return TEISourceLoader()

        return FileSourceLoader()

    def load(self, source: str | Path) -> list[RawBlock] | OldEnglishText:
        """
        Load from the appropriate source loader.

        Args:
            source: The source to load the document from.

        Returns:
            A list of :class:`~wyrdcraeft.models.parsing.RawBlock`
            or an :class:`~wyrdcraeft.models.OldEnglishText` model.

        """
        loader = self.get_loader(source)
        return loader.load(source)
