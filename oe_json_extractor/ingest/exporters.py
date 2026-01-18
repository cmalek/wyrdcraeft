from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from delb import Document, new_tag_node
from lxml import etree as ET  # noqa: N812

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

        tei.append_children(self._create_header(doc))

        text = new_tag_node(f"{{{TEI_NS}}}text")
        tei.append_children(text)

        body = new_tag_node(f"{{{TEI_NS}}}body")
        text.append_children(body)

        self._emit_section(doc.content, body)

        # For pretty printing, we use lxml directly on the internal object
        # but first we ensure namespaces are consistent
        root_el = tei._etree_obj  # noqa: SLF001
        ET.cleanup_namespaces(root_el)
        return ET.tostring(root_el, encoding="unicode", pretty_print=True)

    def _create_header(self, doc: OldEnglishText) -> Any:
        """
        Create the TEI header with metadata.

        Args:
            doc: The document to export.

        Returns:
            The TEI header as a string.

        """
        header = new_tag_node(f"{{{TEI_NS}}}teiHeader")
        file_desc = new_tag_node(f"{{{TEI_NS}}}fileDesc")
        header.append_children(file_desc)

        title_stmt = new_tag_node(f"{{{TEI_NS}}}titleStmt")
        file_desc.append_children(title_stmt)

        title = new_tag_node(f"{{{TEI_NS}}}title")
        title.append_children(doc.metadata.title)
        title_stmt.append_children(title)

        if doc.metadata.author:
            author = new_tag_node(f"{{{TEI_NS}}}author")
            author.append_children(doc.metadata.author)
            title_stmt.append_children(author)

        file_desc.append_children(self._create_publication_stmt(doc))
        file_desc.append_children(self._create_source_desc(doc))

        return header

    def _create_publication_stmt(self, doc: OldEnglishText) -> Any:
        """
        Create the publication statement.

        Args:
            doc: The document to export.

        Returns:
            The publication statement as a string.

        """
        pub_stmt = new_tag_node(f"{{{TEI_NS}}}publicationStmt")
        p = new_tag_node(f"{{{TEI_NS}}}p")
        p.append_children(doc.metadata.source or "unknown")
        pub_stmt.append_children(p)
        return pub_stmt

    def _create_source_desc(self, doc: OldEnglishText) -> Any:
        """
        Create the source description.

        Args:
            doc: The document to export.

        Returns:
            The source description as a string.

        """
        source_desc = new_tag_node(f"{{{TEI_NS}}}sourceDesc")
        p = new_tag_node(f"{{{TEI_NS}}}p")
        p.append_children(doc.metadata.source or "unknown")
        source_desc.append_children(p)
        return source_desc

    def _emit_section(self, sec: Section, parent: Any) -> None:
        """
        Emit a section and its content recursively.

        Args:
            sec: The section to export.
            parent: The parent node to append the section to.

        """
        div = new_tag_node(f"{{{TEI_NS}}}div")
        parent.append_children(div)

        self._apply_metadata(div, sec)

        if sec.title:
            head = new_tag_node(f"{{{TEI_NS}}}head")
            head.append_children(sec.title)
            div.append_children(head)

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
                sp = new_tag_node(f"{{{TEI_NS}}}sp", attributes={"who": par.speaker})
                parent.append_children(sp)
                container = sp

            p_el = new_tag_node(f"{{{TEI_NS}}}p")
            container.append_children(p_el)
            self._apply_metadata(p_el, par)

            for sent in par.sentences:
                s_el = new_tag_node(f"{{{TEI_NS}}}s")
                p_el.append_children(s_el)
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
                current_sp = new_tag_node(
                    f"{{{TEI_NS}}}sp", attributes={"who": ln.speaker}
                )
                parent.append_children(current_sp)
                current_who = ln.speaker
                lg = None

            target = current_sp if current_sp is not None else parent
            if lg is None:
                lg = new_tag_node(f"{{{TEI_NS}}}lg")
                target.append_children(lg)

            l_el = new_tag_node(f"{{{TEI_NS}}}l")
            lg.append_children(l_el)
            self._apply_metadata(l_el, ln)
            l_el.append_children(ln.text)
