from __future__ import annotations

from typing import Final
from xml.etree import ElementTree as ET

from ..models import (
    Line,
    OldEnglishText,
    Paragraph,
    Section,
    Sentence,
)

#: The TEI namespace.
TEI_NS: Final[str] = "http://www.tei-c.org/ns/1.0"


def _el(tag: str) -> ET.Element:
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
    Export canonical JSON structure to a minimal TEI XML document.

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
    ET.register_namespace("", TEI_NS)

    tei = _el("TEI")
    header = _el("teiHeader")
    tei.append(header)

    file_desc = _el("fileDesc")
    header.append(file_desc)

    title_stmt = _el("titleStmt")
    file_desc.append(title_stmt)
    title = _el("title")
    title.text = doc.metadata.title
    title_stmt.append(title)

    if doc.metadata.author:
        author = _el("author")
        author.text = doc.metadata.author
        title_stmt.append(author)

    pub_stmt = _el("publicationStmt")
    file_desc.append(pub_stmt)
    p = _el("p")
    p.text = doc.metadata.source or "unknown"
    pub_stmt.append(p)

    source_desc = _el("sourceDesc")
    file_desc.append(source_desc)
    p2 = _el("p")
    p2.text = doc.metadata.source or "unknown"
    source_desc.append(p2)

    text = _el("text")
    body = _el("body")
    tei.append(text)
    text.append(body)

    def emit_section(parent: ET.Element, sec: Section) -> None:
        """
        Emit a section into the TEI XML document.

        Args:
            parent: The parent element to emit the section into.
            sec: The section to emit.

        """
        div = _el("div")
        if sec.number is not None:
            div.set("n", str(sec.number))
        if sec.title:
            head = _el("head")
            head.text = sec.title
            div.append(head)
        if sec.source_page is not None:
            div.set("source_page", str(sec.source_page))
        if sec.confidence is not None:
            div.set("confidence", str(sec.confidence))

        # Prose
        if sec.paragraphs:
            for par in sec.paragraphs:
                container = div
                if par.speaker:
                    sp = _el("sp")
                    sp.set("who", par.speaker)
                    div.append(sp)
                    container = sp

                p_el = _el("p")
                if par.confidence is not None:
                    p_el.set("confidence", str(par.confidence))
                if par.source_page is not None:
                    p_el.set("source_page", str(par.source_page))
                container.append(p_el)

                for sent in par.sentences:
                    s_el = _el("s")
                    if sent.number is not None:
                        s_el.set("n", str(sent.number))
                    if sent.source_page is not None:
                        s_el.set("source_page", str(sent.source_page))
                    if sent.confidence is not None:
                        s_el.set("confidence", str(sent.confidence))
                    s_el.text = sent.text
                    p_el.append(s_el)

        # Verse
        if sec.lines:
            current_sp: ET.Element | None = None
            current_who: str | None = None
            lg: ET.Element | None = None

            def ensure_lg(parent_el: ET.Element) -> ET.Element:
                nonlocal lg
                if lg is None:
                    lg = _el("lg")
                    parent_el.append(lg)
                return lg

            for ln in sec.lines:
                if ln.speaker and ln.speaker != current_who:
                    current_sp = _el("sp")
                    current_sp.set("who", ln.speaker)
                    div.append(current_sp)
                    current_who = ln.speaker
                    lg = None

                parent_for_lg = current_sp if current_sp is not None else div
                lg_el = ensure_lg(parent_for_lg)

                l_el = _el("l")
                if ln.number is not None:
                    l_el.set("n", str(ln.number))
                if ln.source_page is not None:
                    l_el.set("source_page", str(ln.source_page))
                if ln.confidence is not None:
                    l_el.set("confidence", str(ln.confidence))
                l_el.text = ln.text
                lg_el.append(l_el)

        if sec.sections:
            for child in sec.sections:
                emit_section(div, child)

        parent.append(div)

    emit_section(body, doc.content)
    return ET.tostring(tei, encoding="unicode")


def from_tei(tei_xml: str) -> OldEnglishText:
    """
    Import the minimal TEI subset produced by `to_tei`.

    Args:
        tei_xml: The TEI XML document to import.

    Returns:
        A validated :class:`~oe_json_extractor.schema.models.OldEnglishText`.

    """
    ns = {"tei": TEI_NS}
    root = ET.fromstring(tei_xml)

    title_el = root.find(".//tei:titleStmt/tei:title", ns)
    author_el = root.find(".//tei:titleStmt/tei:author", ns)
    source_el = root.find(".//tei:publicationStmt/tei:p", ns)

    from oe_json_extractor.schema.models import (  # noqa: PLC0415
        OldEnglishText,
        Section,
        TextMetadata,
    )

    meta = TextMetadata(
        title=(title_el.text if title_el is not None and title_el.text else "unknown"),
        author=(author_el.text if author_el is not None and author_el.text else None),
        source=(source_el.text if source_el is not None and source_el.text else None),
    )

    # xml.etree lacks parent pointers; we do a best-effort speaker inference by
    # containment searches.
    def speaker_for_l(div_el: ET.Element, l_el: ET.Element) -> str | None:
        """
        Determine the speaker for a line.

        Args:
            div_el: The div element containing the line.
            l_el: The line element.

        Returns:
            The speaker for the line.

        """
        for sp_el in div_el.findall("tei:sp", ns):
            if l_el in sp_el.findall(".//tei:lg/tei:l", ns):
                return sp_el.get("who")
        return None

    def parse_div(div_el: ET.Element) -> Section:
        """
        Parse a div element into a section.

        Args:
            div_el: The div element to parse.

        Returns:
            A section.

        """
        n = div_el.get("n")
        head = div_el.find("tei:head", ns)
        title = head.text if head is not None and head.text else None

        sec = Section(
            title=title,
            number=n if n is not None else None,
            sections=None,
            paragraphs=None,
            lines=None,
            source_page=div_el.get("source_page"),
            confidence=float(div_el.get("confidence"))
            if div_el.get("confidence")
            else None,
        )

        paragraphs = []
        lines = []

        # prose paragraphs directly under div
        for p_el in div_el.findall("tei:p", ns):
            sents = []
            for s_el in p_el.findall("tei:s", ns):
                sents.append(  # noqa: PERF401
                    Sentence(
                        text=s_el.text or "",
                        number=s_el.get("n"),
                        source_page=s_el.get("source_page"),
                        confidence=float(s_el.get("confidence"))
                        if s_el.get("confidence")
                        else None,
                    )
                )
            if sents:
                paragraphs.append(
                    Paragraph(
                        speaker=None,
                        sentences=sents,
                        source_page=p_el.get("source_page"),
                        confidence=float(p_el.get("confidence"))
                        if p_el.get("confidence")
                        else None,
                    )
                )

        # dialogue prose: <sp>
        for sp_el in div_el.findall("tei:sp", ns):
            who = sp_el.get("who")
            for p_el in sp_el.findall("tei:p", ns):
                sents = []
                for s_el in p_el.findall("tei:s", ns):
                    sents.append(
                        Sentence(
                            text=s_el.text or "",
                            number=s_el.get("n"),
                            source_page=s_el.get("source_page"),
                            confidence=float(s_el.get("confidence"))
                            if s_el.get("confidence")
                            else None,
                        )
                    )
                if sents:
                    paragraphs.append(
                        Paragraph(
                            speaker=who,
                            sentences=sents,
                            source_page=p_el.get("source_page"),
                            confidence=float(p_el.get("confidence"))
                            if p_el.get("confidence")
                            else None,
                        )
                    )

        # verse lines
        for l_el in div_el.findall(".//tei:lg/tei:l", ns):
            lines.append(  # noqa: PERF401
                Line(
                    text=l_el.text or "",
                    number=int(l_el.get("n"))
                    if l_el.get("n") and l_el.get("n").isdigit()
                    else None,
                    speaker=speaker_for_l(div_el, l_el),
                    source_page=l_el.get("source_page"),
                    confidence=float(l_el.get("confidence"))
                    if l_el.get("confidence")
                    else None,
                )
            )

        children = [parse_div(ch) for ch in div_el.findall("tei:div", ns)]
        if children:
            sec.sections = children
        if paragraphs:
            sec.paragraphs = paragraphs
        if lines:
            if sec.paragraphs:
                child = Section(
                    title="Verse",
                    number=None,
                    lines=lines,
                    paragraphs=None,
                    sections=None,
                )
                sec.sections = (sec.sections or []) + [child]
            else:
                sec.lines = lines

        return sec

    body_div = root.find(".//tei:text/tei:body/tei:div", ns)
    content = (
        parse_div(body_div)
        if body_div is not None
        else Section(
            title=None, number=None, sections=None, paragraphs=None, lines=None
        )
    )

    return OldEnglishText(metadata=meta, content=content)
