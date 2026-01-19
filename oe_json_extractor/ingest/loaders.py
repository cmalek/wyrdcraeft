from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Final

import httpx
from acdh_tei_pyutils.tei import TeiReader
from delb import Document
from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text

from ..models import (
    Line,
    OldEnglishText,
    Paragraph,
    Section,
    Sentence,
    TextMetadata,
)

if TYPE_CHECKING:
    from unstructured.documents.elements import Element

#: The TEI namespace.
TEI_NS: Final[str] = "http://www.tei-c.org/ns/1.0"


class BaseSourceLoader:
    """Base class for source loaders."""

    def load(self, source: str | Path) -> list[Element] | OldEnglishText:
        """
        Load elements or canonical text from a source.

        Args:
            source: The source to load the document from.

        Returns:
            A list of :class:`~unstructured.documents.elements.Element`
            or an :class:`~oe_json_extractor.models.OldEnglishText` model.

        """
        raise NotImplementedError

    def load_from_file(self, source_path: Path) -> list[Element]:
        """
        Load elements from a source path using unstructured.

        Args:
            source_path: The path to the source file.

        Returns:
            A list of elements.

        """
        suffix = source_path.suffix.lower()

        if suffix in {".html", ".htm", ".php"}:
            return partition_html(filename=str(source_path), include_metadata=True)
        if suffix == ".pdf":
            return partition_pdf(
                filename=str(source_path),
                extract_images_in_pdf=False,
                infer_table_structure=False,
                include_metadata=True,
            )
        if suffix in {".txt", ".text"}:
            return partition_text(filename=str(source_path), include_metadata=True)
        msg = f"Unsupported source format: {suffix}"
        raise ValueError(msg)


class FileSourceLoader(BaseSourceLoader):
    """Loader for local files."""

    def load(self, source: str | Path) -> list[Element]:
        """
        Load elements from a local file.

        Args:
            source: The source path load the document from.

        Returns:
            A list of :class:`~unstructured.documents.elements.Element`.

        """
        return self.load_from_file(Path(source))


class HTTPSourceLoader(BaseSourceLoader):
    """Loader for HTTP/HTTPS URLs."""

    def load(self, source: str | Path) -> list[Element]:
        """
        Load elements from a HTTP/HTTPS URL.

        Args:
            source: The URL to load the document from.

        Returns:
            A list of :class:`~unstructured.documents.elements.Element`.

        """
        url = str(source)
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            suffix = Path(url).suffix.lower()
            if not suffix:
                content_type = response.headers.get("Content-Type", "")
                if "html" in content_type:
                    suffix = ".html"
                elif "pdf" in content_type:
                    suffix = ".pdf"
                else:
                    suffix = ".txt"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = Path(tmp.name)

            try:
                return self.load_from_file(tmp_path)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()


class TEISourceLoader(BaseSourceLoader):
    """Loader for TEI XML documents."""

    def load(self, source: str | Path) -> OldEnglishText:
        """
        Load a TEI XML document.

        Args:
            source: The source to load the document from.

        Returns:
            An :class:`~oe_json_extractor.models.OldEnglishText` model.

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
            An :class:`~oe_json_extractor.models.OldEnglishText` model.

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
            A :class:`~oe_json_extractor.models.TextMetadata` model.

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
            A :class:`~oe_json_extractor.models.Section` model.

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
            A :class:`~oe_json_extractor.models.Section` model.

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
        lines = []

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
            A :class:`~oe_json_extractor.models.Paragraph` model.

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
            A list of :class:`~oe_json_extractor.models.Line` models.

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

        - If the source is a URL, return an instance of
          :class:`~oe_json_extractor.ingest.loaders.HTTPSourceLoader`.
        - If the source is a local file, return an instance of
          :class:`~oe_json_extractor.ingest.loaders.FileSourceLoader`.
        - If the source is a TEI XML string, return an instance of
          :class:`~oe_json_extractor.ingest.loaders.TEISourceLoader`.

        Args:
            source: The source to load the document from.

        Returns:
            A subclass of
            :class:`~oe_json_extractor.ingest.loaders.BaseSourceLoader`.

        """
        source_str = str(source)
        if source_str.startswith(("http://", "https://")):
            return HTTPSourceLoader()

        source_path = Path(source)
        if source_path.suffix.lower() in {".xml", ".tei"} or (
            not source_path.exists() and "<TEI" in source_str
        ):
            return TEISourceLoader()

        return FileSourceLoader()

    def load(self, source: str | Path) -> list[Element] | OldEnglishText:
        """
        Load from the appropriate source loader.

        Args:
            source: The source to load the document from.

        Returns:
            A list of :class:`~unstructured.documents.elements.Element`
            or an :class:`~oe_json_extractor.models.OldEnglishText` model.

        """
        loader = self.get_loader(source)
        return loader.load(source)
