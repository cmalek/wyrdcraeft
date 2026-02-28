from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, cast

from delb import Document, tag

from .loaders import TEI_NS

if TYPE_CHECKING:
    from ..models import (
        Line,
        OldEnglishText,
        Paragraph,
        Section,
        Sentence,
    )


class BaseExporter(ABC):
    """
    Base class for all exporters.
    """

    @abstractmethod
    def export(self, doc: OldEnglishText) -> str:
        """
        Export an OldEnglishText document to a string representation.

        Args:
            doc: The document to export.

        Returns:
            The exported document as a string.

        """


class TEIExporter(BaseExporter):
    """
    Exporter for TEI XML format using delb for XML manipulation.
    """

    def export(self, doc: OldEnglishText) -> str:
        """
        Export an OldEnglishText document to TEI XML.

        Args:
            doc: The document to export.

        Returns:
            The TEI XML document as a string.

        """
        # Create a document with the default namespace set correctly
        tei_doc = Document(f'<TEI xmlns="{TEI_NS}"/>')
        tei = tei_doc.root

        self._create_header(doc, tei)

        text = self._append_tag(tei, "text")

        body = self._append_tag(text, "body")

        self._emit_section(doc.content, body)

        return str(tei_doc)

    def _append_tag(
        self,
        parent: Any,
        name: str,
        attributes: dict[str, str] | None = None,
    ) -> Any:
        """
        Append a tag node to a parent and return the created node.

        Args:
            parent: The parent node.
            name: The local tag name.
            attributes: Optional XML attributes.

        Returns:
            The created tag node.

        """
        definition = (
            tag(name, cast("Any", attributes))
            if attributes is not None
            else tag(name)
        )
        (node,) = parent.append_children(definition)
        return node

    def _create_header(self, doc: OldEnglishText, parent: Any) -> Any:
        """
        Create the TEI header with metadata.

        Args:
            doc: The document to export.
            parent: The parent node to append the TEI header to.

        Returns:
            The TEI header node.

        """
        header = self._append_tag(parent, "teiHeader")
        file_desc = self._append_tag(header, "fileDesc")

        title_stmt = self._append_tag(file_desc, "titleStmt")

        title = self._append_tag(title_stmt, "title")
        title.append_children(doc.metadata.title)

        if doc.metadata.author:
            author = self._append_tag(title_stmt, "author")
            author.append_children(doc.metadata.author)

        self._create_publication_stmt(doc, file_desc)
        self._create_source_desc(doc, file_desc)

        return header

    def _create_publication_stmt(self, doc: OldEnglishText, parent: Any) -> Any:
        """
        Create the publication statement.

        Args:
            doc: The document to export.
            parent: The parent node to append the publication statement to.

        Returns:
            The publication statement node.

        """
        pub_stmt = self._append_tag(parent, "publicationStmt")
        p = self._append_tag(pub_stmt, "p")
        p.append_children(doc.metadata.source or "unknown")
        return pub_stmt

    def _create_source_desc(self, doc: OldEnglishText, parent: Any) -> Any:
        """
        Create the source description.

        Args:
            doc: The document to export.
            parent: The parent node to append the source description to.

        Returns:
            The source description node.

        """
        source_desc = self._append_tag(parent, "sourceDesc")
        p = self._append_tag(source_desc, "p")
        p.append_children(doc.metadata.source or "unknown")
        return source_desc

    def _emit_section(self, sec: Section, parent: Any) -> None:
        """
        Emit a section and its content recursively.

        Args:
            sec: The section to export.
            parent: The parent node to append the section to.

        """
        div = self._append_tag(parent, "div")

        self._apply_metadata(div, sec)

        if sec.title:
            head = self._append_tag(div, "head")
            head.append_children(sec.title)

        if sec.paragraphs:
            self._emit_paragraphs(sec.paragraphs, div)

        if sec.lines:
            self._emit_lines(sec.lines, div)

        if sec.sections:
            for child in sec.sections:
                self._emit_section(child, div)

    def _apply_metadata(
        self, node: Any, item: Section | Paragraph | Sentence | Line
    ) -> None:
        """
        Apply common metadata attributes to a node.

        Args:
            node: The node to apply the metadata to.
            item: The item to apply the metadata to.

        """
        if hasattr(item, "number") and item.number is not None:
            node.attributes["n"] = str(item.number)
        if hasattr(item, "source_page") and item.source_page is not None:
            node.attributes["source_page"] = str(item.source_page)
        if hasattr(item, "confidence") and item.confidence is not None:
            node.attributes["confidence"] = str(item.confidence)

    def _emit_paragraphs(self, paragraphs: list[Paragraph], parent: Any) -> None:
        """
        Emit prose paragraphs, handling speakers.

        Args:
            paragraphs: The paragraphs to export.
            parent: The parent node to append the paragraphs to.

        """
        for par in paragraphs:
            container = parent
            if par.speaker:
                sp = self._append_tag(parent, "sp", {"who": par.speaker})
                container = sp

            p_el = self._append_tag(container, "p")
            self._apply_metadata(p_el, par)

            for sent in par.sentences:
                s_el = self._append_tag(p_el, "s")
                self._apply_metadata(s_el, sent)
                s_el.append_children(sent.text)

    def _emit_lines(self, lines: list[Line], parent: Any) -> None:
        """
        Emit verse lines, grouped by speaker into line groups (lg).

        Args:
            lines: The lines to export.
            parent: The parent node to append the lines to.

        """
        current_sp: Any = None
        current_who: str | None = None
        lg: Any = None

        for ln in lines:
            if ln.speaker and ln.speaker != current_who:
                current_sp = self._append_tag(parent, "sp", {"who": ln.speaker})
                current_who = ln.speaker
                lg = None

            target = current_sp if current_sp is not None else parent
            if lg is None:
                lg = self._append_tag(target, "lg")

            l_el = self._append_tag(lg, "l")
            self._apply_metadata(l_el, ln)
            l_el.append_children(ln.text)
