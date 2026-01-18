from __future__ import annotations

from typing import TYPE_CHECKING

from lxml import etree as ET  # noqa: N812

from .loaders import TEI_NS

if TYPE_CHECKING:
    from ..models import (
        OldEnglishText,
        Section,
    )


def _el(tag: str) -> ET._Element:
    """
    Create a new element in the TEI namespace.

    Args:
        tag: The tag name.

    Returns:
        The new element.

    """
    return ET.Element(f"{{{TEI_NS}}}{tag}")


def to_tei(doc: OldEnglishText) -> str:
    """
    Export canonical JSON structure to a minimal TEI XML document using lxml.

    Mapping:
    - Section => <div>
    - Prose paragraph => <p> containing <s>
    - Verse lines => <lg><l>
    - Dialogue:

      - prose: <sp who="..."><p>...</p></sp>
      - verse: <sp who="..."><lg><l>...</l></lg></sp>

    Args:
        doc: The OldEnglishText to export.

    Returns:
        The TEI XML document.

    """
    # lxml handles namespaces very well
    nsmap = {None: TEI_NS}
    tei = ET.Element(f"{{{TEI_NS}}}TEI", nsmap=nsmap)

    header = ET.SubElement(tei, f"{{{TEI_NS}}}teiHeader")
    file_desc = ET.SubElement(header, f"{{{TEI_NS}}}fileDesc")
    title_stmt = ET.SubElement(file_desc, f"{{{TEI_NS}}}titleStmt")

    title = ET.SubElement(title_stmt, f"{{{TEI_NS}}}title")
    title.text = doc.metadata.title

    if doc.metadata.author:
        author = ET.SubElement(title_stmt, f"{{{TEI_NS}}}author")
        author.text = doc.metadata.author

    pub_stmt = ET.SubElement(file_desc, f"{{{TEI_NS}}}publicationStmt")
    p = ET.SubElement(pub_stmt, f"{{{TEI_NS}}}p")
    p.text = doc.metadata.source or "unknown"

    source_desc = ET.SubElement(file_desc, f"{{{TEI_NS}}}sourceDesc")
    p2 = ET.SubElement(source_desc, f"{{{TEI_NS}}}p")
    p2.text = doc.metadata.source or "unknown"

    text = ET.SubElement(tei, f"{{{TEI_NS}}}text")
    body = ET.SubElement(text, f"{{{TEI_NS}}}body")

    def emit_section(parent: ET._Element, sec: Section) -> None:
        """
        Emit a section into the TEI XML document.
        """
        div = ET.SubElement(parent, f"{{{TEI_NS}}}div")
        if sec.number is not None:
            div.set("n", str(sec.number))
        if sec.title:
            head = ET.SubElement(div, f"{{{TEI_NS}}}head")
            head.text = sec.title
        if sec.source_page is not None:
            div.set("source_page", str(sec.source_page))
        if sec.confidence is not None:
            div.set("confidence", str(sec.confidence))

        # Prose
        if sec.paragraphs:
            for par in sec.paragraphs:
                container = div
                if par.speaker:
                    sp = ET.SubElement(div, f"{{{TEI_NS}}}sp")
                    sp.set("who", par.speaker)
                    container = sp

                p_el = ET.SubElement(container, f"{{{TEI_NS}}}p")
                if par.confidence is not None:
                    p_el.set("confidence", str(par.confidence))
                if par.source_page is not None:
                    p_el.set("source_page", str(par.source_page))

                for sent in par.sentences:
                    s_el = ET.SubElement(p_el, f"{{{TEI_NS}}}s")
                    if sent.number is not None:
                        s_el.set("n", str(sent.number))
                    if sent.source_page is not None:
                        s_el.set("source_page", str(sent.source_page))
                    if sent.confidence is not None:
                        s_el.set("confidence", str(sent.confidence))
                    s_el.text = sent.text

        # Verse
        if sec.lines:
            current_sp: ET._Element | None = None
            current_who: str | None = None
            lg: ET._Element | None = None

            def ensure_lg(parent_el: ET._Element) -> ET._Element:
                nonlocal lg
                if lg is None:
                    lg = ET.SubElement(parent_el, f"{{{TEI_NS}}}lg")
                return lg

            for ln in sec.lines:
                if ln.speaker and ln.speaker != current_who:
                    current_sp = ET.SubElement(div, f"{{{TEI_NS}}}sp")
                    current_sp.set("who", ln.speaker)
                    current_who = ln.speaker
                    lg = None

                parent_for_lg = current_sp if current_sp is not None else div
                lg_el = ensure_lg(parent_for_lg)

                l_el = ET.SubElement(lg_el, f"{{{TEI_NS}}}l")
                if ln.number is not None:
                    l_el.set("n", str(ln.number))
                if ln.source_page is not None:
                    l_el.set("source_page", str(ln.source_page))
                if ln.confidence is not None:
                    l_el.set("confidence", str(ln.confidence))
                l_el.text = ln.text

        if sec.sections:
            for child in sec.sections:
                emit_section(div, child)

    emit_section(body, doc.content)
    return ET.tostring(tei, encoding="unicode", pretty_print=True)
