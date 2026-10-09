"""Assemble Wright-style paradigm grids for the dictionary browse sidebar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from wyrdcraeft.services.dictionary.form_decode import (
    _ADJ_PATTERN,
    _GENDER_LABELS,
    _IMP_PATTERN,
    _MOOD_LABELS,
    _NOUN_LIKE_PATTERN,
    _NUMBER_LABELS,
    _TENSE_LABELS,
    _VERB_FINITE_PATTERN,
    _VERB_FINITE_SG_PATTERN,
    _VERB_FUNCTION_LABELS,
    _decode_noun_like,
    _label,
    _pick_inflection,
    build_morphology_table,
    decode_function_dimensions,
    format_bt_gender_label,
)
from wyrdcraeft.services.morphology.text_utils import canonicalize_inflection_code

#: Short case labels used in POS paradigm sidebar grids.
_PARADIGM_CASE_CODE_TO_LABEL: Final[dict[str, str]] = {
    "No": "Nom",
    "Ac": "Acc",
    "Ge": "Gen",
    "Da": "Dat",
    "Is": "Inst",
}


@dataclass(frozen=True)
class ParadigmTableSection:
    """
    One titled paradigm grid section for the browse sidebar.

    Attributes:
        title: Section heading shown above the grid.
        columns: Ordered column headers.
        rows: Cell values aligned to ``columns``.

    """

    #: Section heading shown above the grid.
    title: str
    #: Ordered column headers.
    columns: tuple[str, ...]
    #: Cell values aligned to ``columns``.
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ParadigmSidebarSpec:
    """
    Ordered paradigm table sections for one POS-filtered morphology sidebar.

    Attributes:
        sections: Sidebar sections in display order.

    """

    #: Sidebar sections in display order.
    sections: tuple[ParadigmTableSection, ...]


@dataclass(frozen=True)
class MorphologyRowPayload:
    """
    Minimal morphology payload consumed by paradigm grid builders.

    Attributes:
        form: Surface spelling.
        formi: Alternate surface spelling.
        function: Morphology function code.
        wordclass: Morphology wordclass label.
        class1: First morphology class column.
        class2: Second morphology class column.
        class3: Third morphology class column.
        inflection: FK-backed strong/weak label when legacy classes are empty.

    """

    #: Surface spelling.
    form: str
    #: Alternate surface spelling.
    formi: str
    #: Morphology function code.
    function: str
    #: Morphology wordclass label.
    wordclass: str
    #: First morphology class column.
    class1: str
    #: Second morphology class column.
    class2: str
    #: Third morphology class column.
    class3: str
    #: FK-backed strong/weak label when legacy classes are empty.
    inflection: str = ""


def _surface_form(form: str, formi: str) -> str:
    """
    Pick the preferred surface spelling for one morphology row.

    Args:
        form: Primary surface spelling.
        formi: Alternate surface spelling.

    Returns:
        Non-empty surface spelling.

    """
    return form.strip() or formi.strip()


def _paradigm_grid_case_label(code: str) -> str | None:
    """
    Map one morphology case code to a short paradigm grid row label.

    Args:
        code: Morphology case code such as ``No`` or ``Is``.

    Returns:
        Grid row label, or ``None`` when the code is unsupported.

    """
    return _PARADIGM_CASE_CODE_TO_LABEL.get(code.strip())


def _join_surfaces(values: set[str]) -> str:
    """
    Join distinct surface spellings for one paradigm cell.

    Args:
        values: Distinct non-empty surface spellings.

    Returns:
        Comma-separated spellings, or ``-`` when empty.

    """
    ordered = sorted(value for value in values if value.strip())
    if not ordered:
        return "-"
    return ", ".join(ordered)


def _gender_code_from_label(label: str) -> str:
    """
    Map one decoded gender label back to a morphology gender code.

    Args:
        label: Decoded gender label.

    Returns:
        ``Ma``, ``Fe``, or ``Ne`` when recognized.

    """
    normalized = label.strip().casefold()
    for code, mapped in _GENDER_LABELS.items():
        if mapped == normalized:
            return code
    return ""


def _append_surface(
    target: dict[tuple[str, ...], set[str]],
    key: tuple[str, ...],
    surface: str,
) -> None:
    """
    Append one surface spelling to a paradigm cell bucket.

    Args:
        target: Paradigm cell map.
        key: Cell coordinate tuple.
        surface: Surface spelling to append.

    Side Effects:
        Mutates ``target`` when ``surface`` is non-empty.

    """
    if not surface.strip():
        return
    target.setdefault(key, set()).add(surface.strip())


def _sidebar_has_content(sidebar: ParadigmSidebarSpec) -> bool:
    """
    Return whether a paradigm sidebar contains any non-empty cell values.

    Args:
        sidebar: Candidate sidebar specification.

    Returns:
        ``True`` when at least one cell has a real form value.

    """
    for section in sidebar.sections:
        for row in section.rows:
            data_cells = row[1:] if len(row) > 1 else row
            for cell in data_cells:
                if cell.strip() not in {"", "-"}:
                    return True
    return False


def build_paradigm_sidebar(
    rows: list[MorphologyRowPayload],
    *,
    wordclass: str,
    entry_genders: tuple[str, ...] = (),
) -> ParadigmSidebarSpec:
    """
    Build POS-aware paradigm grids for the browse morphology sidebar.

    Args:
        rows: Morphology rows sharing one dictionary entry POS filter.

    Keyword Args:
        wordclass: Dominant morphology wordclass for the sidebar.
        entry_genders: Gender markers stored on the dictionary entry.

    Returns:
        Ordered paradigm table sections for sidebar rendering.

    """
    pos = wordclass.strip().casefold()
    if pos in {"verb", "participle"}:
        sidebar = _build_verb_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "noun":
        sidebar = _build_noun_sidebar(rows, entry_genders=entry_genders)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "adjective":
        sidebar = _build_adjective_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "pronoun":
        sidebar = _build_pronoun_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "adverb":
        sidebar = _build_adverb_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    table = build_morphology_table(
        [
            (
                row.form,
                row.function,
                row.class1,
                row.class2,
                row.class3,
                row.formi,
                row.inflection,
            )
            for row in rows
        ],
        wordclass=wordclass,
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Forms",
                columns=table.columns,
                rows=table.rows,
            ),
        )
    )


def _build_verb_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:  # noqa: PLR0912, PLR0915
    """
    Build the Wright-style verb conjugation grid.

    Args:
        rows: Verb morphology rows.

    Returns:
        Verb sidebar specification.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    infinitive = ""
    for row in rows:
        surface = _surface_form(row.form, row.formi)
        code = canonicalize_inflection_code(row.function)
        exact = _VERB_FUNCTION_LABELS.get(code)
        if exact is not None and exact.get("form") == "infinitive":
            infinitive = surface or infinitive
            continue
        if code in {"If", "Inf"}:
            infinitive = surface or infinitive
            continue
        if code == "IdIf":
            _append_surface(cells, ("Inflected Infin", "present"), surface)
            continue
        if code in {"PsPa", "PsPt", "Pp"}:
            _append_surface(cells, ("Participles", "present"), surface)
            continue
        if code == "PaPt":
            _append_surface(cells, ("Participles", "past"), surface)
            continue
        imperative = _IMP_PATTERN.fullmatch(code)
        if imperative is not None:
            number = _label(_NUMBER_LABELS, imperative.group("number"))
            label = "Imperative Pl" if number == "plural" else "Imperative Sing"
            _append_surface(cells, (label, "present"), surface)
            continue
        finite_sg = _VERB_FINITE_SG_PATTERN.fullmatch(code)
        if finite_sg is not None:
            tense = _label(_TENSE_LABELS, finite_sg.group("tense"))
            mood = _label(_MOOD_LABELS, finite_sg.group("mood"))
            person = finite_sg.group("person")
            if mood == "indicative":
                row_label = "Indicative Sing"
            elif mood == "subjunctive":
                row_label = "Subjunctive Sing"
            else:
                row_label = mood.title()
            _append_surface(cells, (row_label, person, tense), surface)
            continue
        finite = _VERB_FINITE_PATTERN.fullmatch(code)
        if finite is not None:
            tense = _label(_TENSE_LABELS, finite.group("tense"))
            mood = _label(_MOOD_LABELS, finite.group("mood"))
            number = _label(_NUMBER_LABELS, finite.group("number"))
            if mood == "indicative":
                row_label = "Indicative Pl"
            elif mood == "subjunctive":
                row_label = (
                    "Subjunctive Sing" if number == "singular" else "Subjunctive Pl"
                )
            else:
                row_label = mood.title()
            _append_surface(cells, (row_label, "1,2,3", tense), surface)
            continue
    table_rows: list[tuple[str, ...]] = []
    if infinitive:
        table_rows.append(("Infinitive", "", infinitive, ""))
    table_rows.append(("", "Present", "Past"))
    row_order = (
        ("Indicative Sing", "1"),
        ("Indicative Sing", "2"),
        ("Indicative Sing", "3"),
        ("Indicative Pl", "1,2,3"),
        ("Subjunctive Sing", "1,2,3"),
        ("Subjunctive Pl", "1,2,3"),
        ("Participles", ""),
        ("Imperative Sing", ""),
        ("Imperative Pl", ""),
        ("Inflected Infin", ""),
    )
    for label, person in row_order:
        if person:
            table_rows.append(
                (
                    label,
                    person,
                    _join_surfaces(cells.get((label, person, "present"), set())),
                    _join_surfaces(cells.get((label, person, "past"), set())),
                )
            )
        else:
            table_rows.append(
                (
                    label,
                    "",
                    _join_surfaces(cells.get((label, "present"), set())),
                    _join_surfaces(cells.get((label, "past"), set())),
                )
            )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Verb",
                columns=("", "Person", "Present", "Past"),
                rows=tuple(table_rows),
            ),
        )
    )


def _collect_noun_sidebar_cells(
    rows: list[MorphologyRowPayload],
    *,
    allowed_genders: frozenset[str] | None = None,
) -> dict[tuple[str, ...], set[str]]:
    """
    Collect noun declension cells keyed by case and number labels.

    Args:
        rows: Noun morphology rows.

    Keyword Args:
        allowed_genders: Morphology gender codes to keep; ``None`` keeps all.

    Returns:
        Case/number cell map for noun sidebar rendering.

    Note:
        Per ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``,
        noun paradigms are keyed by case and number; optional gender filtering
        follows dictionary-entry gender tags when they agree with form codes.
        PoS scope: ``noun``.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        decoded = _decode_noun_like(row.function.strip())
        if "case" not in decoded:
            continue
        match = _NOUN_LIKE_PATTERN.fullmatch(row.function.strip())
        if match is None:
            continue
        gender_code = match.group("gender")
        if allowed_genders and gender_code not in allowed_genders:
            continue
        case_label = _paradigm_grid_case_label(match.group("case"))
        if case_label is None:
            continue
        number_label = "Singular" if match.group("number") == "Sg" else "Plural"
        _append_surface(
            cells,
            (case_label, number_label),
            _surface_form(row.form, row.formi),
        )
    return cells


def _build_noun_sidebar(
    rows: list[MorphologyRowPayload],
    *,
    entry_genders: tuple[str, ...],
) -> ParadigmSidebarSpec:
    """
    Build the case-by-number noun declension grid.

    Args:
        rows: Noun morphology rows.

    Keyword Args:
        entry_genders: Gender markers stored on the dictionary entry.

    Returns:
        Noun sidebar specification.

    Note:
        Per ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``,
        noun paradigms group surface forms by case and number. When entry gender
        tags disagree with generated masculine/feminine/neuter form codes, the
        grid falls back to unfiltered cells so mis-tagged lemmas still display.
        PoS scope: ``noun``.

    """
    allowed_genders = frozenset(
        {
            _gender_code_from_label(format_bt_gender_label(gender))
            for gender in entry_genders
            if gender.strip()
        }
    )
    cells = _collect_noun_sidebar_cells(
        rows,
        allowed_genders=allowed_genders or None,
    )
    if not cells and rows and allowed_genders:
        cells = _collect_noun_sidebar_cells(rows)
    case_order: tuple[str, ...] = ("Nom", "Acc", "Gen", "Dat")
    if any(cells.get(("Inst", number)) for number in ("Singular", "Plural")):
        case_order = (*case_order, "Inst")
    table_rows = tuple(
        (
            case,
            _join_surfaces(cells.get((case, "Singular"), set())),
            _join_surfaces(cells.get((case, "Plural"), set())),
        )
        for case in case_order
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Noun",
                columns=("", "Singular", "Plural"),
                rows=table_rows,
            ),
        )
    )


def _build_adjective_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build Wright-style adjective grids grouped by inflection and degree.

    Args:
        rows: Adjective morphology rows.

    Returns:
        Adjective sidebar specification.

    """
    sections: list[ParadigmTableSection] = []
    for inflection in ("strong", "weak"):
        for degree_label, degree_code in (
            ("Positive", "Po"),
            ("Comparative", "Co"),
            ("Superlative", "Sp"),
        ):
            section = _build_adjective_degree_section(
                rows,
                inflection=inflection,
                degree_code=degree_code,
                title=f"{inflection.title()} · {degree_label}",
            )
            if section is not None:
                sections.append(section)
    return ParadigmSidebarSpec(sections=tuple(sections))


def _build_adjective_degree_section(
    rows: list[MorphologyRowPayload],
    *,
    inflection: str,
    degree_code: str,
    title: str,
) -> ParadigmTableSection | None:
    """
    Build one adjective degree grid for a single inflection type.

    Args:
        rows: Adjective morphology rows.

    Keyword Args:
        inflection: ``strong`` or ``weak`` inflection label.
        degree_code: Degree code prefix such as ``Po`` or ``Co``.
        title: Section title.

    Returns:
        Grid section when any cells are populated, otherwise ``None``.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        inflection_label = _pick_inflection(
            row.class1,
            row.class2,
            row.class3,
            morph_class_inflection=row.inflection,
        ).casefold()
        if inflection_label != inflection:
            continue
        match = _ADJ_PATTERN.fullmatch(row.function.strip())
        if match is None or match.group("degree") != degree_code:
            continue
        case_label = _paradigm_grid_case_label(match.group("case"))
        if case_label is None:
            continue
        if match.group("number") == "Pl":
            column = "Plural"
        else:
            gender_code = match.group("gender")
            column = {
                "Ma": "Masc sg",
                "Fe": "Fem sg",
                "Ne": "Neut sg",
            }.get(gender_code, "")
        if not column:
            continue
        _append_surface(cells, (case_label, column), _surface_form(row.form, row.formi))
    if not cells:
        return None
    case_order: tuple[str, ...] = ("Nom", "Acc", "Gen", "Dat")
    if any(
        cells.get((case, column))
        for case in ("Inst",)
        for column in ("Masc sg", "Fem sg", "Neut sg", "Plural")
    ):
        case_order = (*case_order, "Inst")
    table_rows = tuple(
        (
            case,
            _join_surfaces(cells.get((case, "Masc sg"), set())),
            _join_surfaces(cells.get((case, "Fem sg"), set())),
            _join_surfaces(cells.get((case, "Neut sg"), set())),
            _join_surfaces(cells.get((case, "Plural"), set())),
        )
        for case in case_order
    )
    return ParadigmTableSection(
        title=title,
        columns=("", "Masc sg", "Fem sg", "Neut sg", "Plural"),
        rows=table_rows,
    )


def _build_pronoun_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build a pronoun case grid using the adjective column layout.

    Args:
        rows: Pronoun morphology rows.

    Returns:
        Pronoun sidebar specification.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        match = _NOUN_LIKE_PATTERN.fullmatch(row.function.strip())
        if match is None:
            continue
        case_label = _paradigm_grid_case_label(match.group("case"))
        if case_label is None:
            continue
        if match.group("number") == "Pl":
            column = "Plural"
        else:
            column = {
                "Ma": "Masc sg",
                "Fe": "Fem sg",
                "Ne": "Neut sg",
            }.get(match.group("gender"), "")
        if not column:
            continue
        _append_surface(cells, (case_label, column), _surface_form(row.form, row.formi))
    if not cells:
        table = build_morphology_table(
            [
                (
                    row.form,
                    row.function,
                    row.class1,
                    row.class2,
                    row.class3,
                    row.formi,
                )
                for row in rows
            ],
            wordclass="pronoun",
        )
        return ParadigmSidebarSpec(
            sections=(
                ParadigmTableSection(
                    title="Pronoun",
                    columns=table.columns,
                    rows=table.rows,
                ),
            )
        )
    case_order: tuple[str, ...] = ("Nom", "Acc", "Gen", "Dat")
    if any(
        cells.get((case, column))
        for case in ("Inst",)
        for column in ("Masc sg", "Fem sg", "Neut sg", "Plural")
    ):
        case_order = (*case_order, "Inst")
    table_rows = tuple(
        (
            case,
            _join_surfaces(cells.get((case, "Masc sg"), set())),
            _join_surfaces(cells.get((case, "Fem sg"), set())),
            _join_surfaces(cells.get((case, "Neut sg"), set())),
            _join_surfaces(cells.get((case, "Plural"), set())),
        )
        for case in case_order
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Pronoun",
                columns=("", "Masc sg", "Fem sg", "Neut sg", "Plural"),
                rows=table_rows,
            ),
        )
    )


def _build_adverb_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build a simple adverb degree list.

    Args:
        rows: Adverb morphology rows.

    Returns:
        Adverb sidebar specification.

    """
    cells: dict[str, set[str]] = {}
    for row in rows:
        decoded = decode_function_dimensions(
            function=row.function,
            wordclass="adverb",
            class1=row.class1,
            class2=row.class2,
            class3=row.class3,
        )
        degree = decoded.get("degree", "")
        if not degree:
            continue
        cells.setdefault(degree.title(), set()).add(_surface_form(row.form, row.formi))
    if not cells:
        table = build_morphology_table(
            [
                (
                    row.form,
                    row.function,
                    row.class1,
                    row.class2,
                    row.class3,
                    row.formi,
                )
                for row in rows
            ],
            wordclass="adverb",
        )
        return ParadigmSidebarSpec(
            sections=(
                ParadigmTableSection(
                    title="Adverb",
                    columns=table.columns,
                    rows=table.rows,
                ),
            )
        )
    table_rows = tuple(
        (degree, _join_surfaces(cells[degree]))
        for degree in ("Positive", "Comparative", "Superlative")
        if degree in cells
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Adverb",
                columns=("Degree", "Form"),
                rows=table_rows,
            ),
        )
    )
