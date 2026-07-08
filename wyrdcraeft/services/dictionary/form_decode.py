"""Decode morphology ``function`` codes into browse table dimensions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Final

from wyrdcraeft.services.dictionary.wordclass_pos import (
    WORDCLASS_TO_BT_POS,
    infer_bt_pos_from_wordclasses,
)
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.morphology.text_utils import canonicalize_inflection_code

__all__ = ["WORDCLASS_TO_BT_POS", "infer_bt_pos_from_wordclasses"]

#: Dictionary POS labels mapped to morphology ``wordclass`` values for filtering.
BT_POS_TO_WORDCLASSES: Final[dict[str, tuple[str, ...]]] = {
    "noun": ("noun",),
    "verb": ("verb", "participle"),
    "adj": ("adjective",),
    "adv": ("adverb",),
    "numeral": ("numeral",),
    "pron": ("pronoun",),
    "prep": ("preposition",),
    "conj": ("conjunction",),
    "interj": ("interjection",),
    "indecl": ("indeclinable",),
}

#: Number-code labels used when decoding morphology function strings.
_NUMBER_LABELS: Final[dict[str, str]] = {
    "Sg": "singular",
    "Pl": "plural",
    "Du": "dual",
}
#: Gender-code labels used when decoding morphology function strings.
_GENDER_LABELS: Final[dict[str, str]] = {
    "Ma": "masculine",
    "Fe": "feminine",
    "Ne": "neuter",
}
#: Case-code labels used when decoding morphology function strings.
_CASE_LABELS: Final[dict[str, str]] = {
    "No": "nominative",
    "Ac": "accusative",
    "Ge": "genitive",
    "Da": "dative",
    "Is": "instrumental",
}
#: Short case labels used in POS paradigm sidebar grids.
_PARADIGM_CASE_CODE_TO_LABEL: Final[dict[str, str]] = {
    "No": "Nom",
    "Ac": "Acc",
    "Ge": "Gen",
    "Da": "Dat",
    "Is": "Inst",
}
#: Degree-code labels used when decoding morphology function strings.
_DEGREE_LABELS: Final[dict[str, str]] = {
    "Po": "positive",
    "Co": "comparative",
    "Sp": "superlative",
}
#: Tense-code labels used when decoding morphology function strings.
_TENSE_LABELS: Final[dict[str, str]] = {
    "Ps": "present",
    "Pa": "past",
}
#: Mood-code labels used when decoding morphology function strings.
_MOOD_LABELS: Final[dict[str, str]] = {
    "Im": "imperative",
    "In": "indicative",
    "Su": "subjunctive",
}
#: Person-code labels used when decoding morphology function strings.
_PERSON_LABELS: Final[dict[str, str]] = {
    "1": "1st",
    "2": "2nd",
    "3": "3rd",
}

#: Exact verb/participle function codes from the morphology generator glossary.
_VERB_FUNCTION_LABELS: Final[dict[str, dict[str, str]]] = {
    "If": {"form": "infinitive"},
    "IdIf": {"form": "inflected infinitive"},
    "Inf": {"form": "infinitive"},
    "PsPa": {"form": "participle", "tense": "present"},
    "PsPt": {"form": "participle", "tense": "present"},
    "Pp": {"form": "participle", "tense": "present"},
    "PaPt": {"form": "participle", "tense": "past"},
    "PsSug": {"tense": "present", "mood": "subjunctive"},
}

#: Regex for noun-like morphology function codes.
_NOUN_LIKE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<number>Sg|Pl|Du)(?P<gender>Ma|Fe|Ne)(?P<case>No|Ac|Ge|Da|Is)$"
)
#: Regex for adjective morphology function codes.
_ADJ_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<degree>Po|Co|Sp)(?P<number>Sg|Pl|Du)(?P<gender>Ma|Fe|Ne)(?P<case>No|Ac|Ge|Da|Is)$"
)
#: Regex for finite verb morphology function codes.
_VERB_FINITE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<tense>Ps|Pa)(?P<mood>In|Su)(?P<number>Sg|Pl)(?P<person>[123])?$"
)
#: Regex for singular finite verb morphology function codes.
_VERB_FINITE_SG_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<tense>Ps|Pa)(?P<mood>In|Su)Sg(?P<person>[123])$"
)
#: Regex for imperative verb morphology function codes.
_IMP_PATTERN: Final[re.Pattern[str]] = re.compile(r"^Im(?:p)?(?P<number>Sg|Pl)$")


@dataclass(frozen=True)
class MorphologyTableSpec:
    """
    Column headers and row cell values for one morphology sidebar table.

    Attributes:
        columns: Ordered column labels for the browse table.
        rows: One list of cell strings per morphology row, aligned to ``columns``.

    """

    #: Ordered column labels for the browse table.
    columns: tuple[str, ...]
    #: One list of cell strings per morphology row, aligned to ``columns``.
    rows: tuple[tuple[str, ...], ...]


def wordclasses_for_entry_pos(pos: str) -> frozenset[str]:
    """
    Return morphology wordclass labels that match one dictionary POS label.

    Args:
        pos: Part-of-speech label stored on a dictionary entry.

    Returns:
        Allowed morphology ``wordclass`` values for sidebar filtering.

    """
    normalized = pos.strip().casefold()
    if not normalized:
        return frozenset()
    for bt_pos, wordclasses in BT_POS_TO_WORDCLASSES.items():
        if bt_pos.casefold() == normalized:
            return frozenset(wordclasses)
    return frozenset()


def morphology_row_matches_pos(*, wordclass: str, entry_pos: str) -> bool:
    """
    Return whether one morphology row belongs to the dictionary entry POS.

    Keyword Args:
        wordclass: Morphology ``wordclass`` label on the form row.
        entry_pos: Dictionary entry POS label.

    Returns:
        ``True`` when the row should appear in the POS-filtered sidebar.

    """
    allowed = wordclasses_for_entry_pos(entry_pos)
    if not allowed:
        return True
    return wordclass.strip().casefold() in allowed


def _label(mapping: dict[str, str], code: str) -> str:
    """
    Map one morphology code fragment to a human-readable label.

    Args:
        mapping: Code-to-label mapping for one dimension.
        code: Source code fragment.

    Returns:
        Human-readable label, or the original code when unknown.

    """
    return mapping.get(code, code)


def inflection_strength_from_morph_class(
    *,
    traditional_class: str = "",
    features_json: str = "",
) -> str:
    """
    Derive strong/weak inflection labels from catalog morph-class metadata.

    Keyword Args:
        traditional_class: Wright traditional class label from ``morph_classes``.
        features_json: Serialized ``morph_classes.features_json`` payload.

    Returns:
        ``strong``, ``weak``, or an empty string when unknown.

    """
    if features_json.strip():
        try:
            features = json.loads(features_json)
        except json.JSONDecodeError:
            features = {}
        strength = str(features.get("strength", "")).strip().casefold()
        if strength in {"strong", "weak"}:
            return strength
    normalized = traditional_class.strip().casefold()
    if normalized.startswith("strong") or " strong" in f" {normalized} ":
        return "strong"
    if normalized.startswith("weak") or " weak" in f" {normalized} ":
        return "weak"
    return ""


def _pick_inflection(*class_values: str, morph_class_inflection: str = "") -> str:
    """
    Derive adjective inflection metadata from morphology class columns.

    Args:
        class_values: ``class1`` through ``class3`` values from one form row.

    Keyword Args:
        morph_class_inflection: FK-backed strong/weak label when legacy classes
            are empty.

    Returns:
        Strong/weak inflection label when present, otherwise joined classes.

    """
    explicit = morph_class_inflection.strip().casefold()
    if explicit in {"strong", "weak"}:
        return explicit
    for value in class_values:
        normalized = value.strip().casefold()
        if normalized in {"strong", "weak"}:
            return normalized
    return ", ".join(value.strip() for value in class_values if value.strip())


def decode_function_dimensions(  # noqa: PLR0911, PLR0913
    *,
    function: str,
    wordclass: str,
    class1: str = "",
    class2: str = "",
    class3: str = "",
    morph_class_inflection: str = "",
) -> dict[str, str]:
    """
    Decode one morphology function code into POS-specific table dimensions.

    Keyword Args:
        function: Morphology function code such as ``PaInSg2`` or ``PlNeAc``.
        wordclass: Morphology wordclass label for the row.
        class1: First morphology class column.
        class2: Second morphology class column.
        class3: Third morphology class column.
        morph_class_inflection: FK-backed strong/weak label when legacy classes
            are empty.

    Returns:
        Dimension labels keyed by browse-table column name.

    """
    code = canonicalize_inflection_code(function)
    if not code:
        return {}

    pos = wordclass.strip().casefold()
    if pos in {"noun", "preposition", "conjunction", "interjection", "indeclinable"}:
        return _decode_noun_like(code)
    if pos == "adjective":
        return _decode_adjective(
            code,
            class1,
            class2,
            class3,
            morph_class_inflection=morph_class_inflection,
        )
    if pos in {"verb", "participle"}:
        return _decode_verb(code)
    if pos == "pronoun":
        decoded = _decode_noun_like(code)
        if decoded:
            return decoded
        return {"function": code}
    if pos == "adverb":
        if code in _DEGREE_LABELS:
            return {"degree": _label(_DEGREE_LABELS, code)}
        if code.startswith(("Po", "Co", "Sp")):
            degree_code = code[:2]
            return {"degree": _label(_DEGREE_LABELS, degree_code)}
        return {"function": code}
    if pos == "numeral":
        decoded = _decode_adjective(
            code,
            class1,
            class2,
            class3,
            morph_class_inflection=morph_class_inflection,
        )
        if decoded:
            return decoded
        return _decode_noun_like(code)
    return {"function": code}


#: Browse sort order for adjective degree labels.
_ADJECTIVE_DEGREE_ORDER: Final[dict[str, int]] = {
    "positive": 0,
    "comparative": 1,
    "superlative": 2,
}
#: Browse sort order for adjective inflection labels.
_ADJECTIVE_INFLECTION_ORDER: Final[dict[str, int]] = {
    "strong": 0,
    "weak": 1,
}
#: Browse sort order for gender labels.
_ADJECTIVE_GENDER_ORDER: Final[dict[str, int]] = {
    "masculine": 0,
    "feminine": 1,
    "neuter": 2,
}
#: Browse sort order for case labels.
_ADJECTIVE_CASE_ORDER: Final[dict[str, int]] = {
    "nominative": 0,
    "accusative": 1,
    "genitive": 2,
    "dative": 3,
    "instrumental": 4,
}
#: Browse sort order for number labels.
_ADJECTIVE_NUMBER_ORDER: Final[dict[str, int]] = {
    "singular": 0,
    "plural": 1,
    "dual": 2,
}


#: Minimum morphology table row width for sort-key extraction.
_MORPHOLOGY_TABLE_MIN_COLUMNS: Final[int] = 2
#: Row width when an explicit inflection label is supplied.
_MORPHOLOGY_TABLE_WITH_INFLECTION_COLUMNS: Final[int] = 7
#: Input row tuple accepted by ``build_morphology_table``.
MorphologyTableInputRow = (
    tuple[str, str, str, str, str, str] | tuple[str, str, str, str, str, str, str]
)


def _adjective_row_sort_key(row: tuple[str, ...], *, wordclass: str) -> tuple[int, ...]:
    """
    Build the browse sort key for one adjective morphology table row.

    Args:
        row: Rendered morphology table row cells.

    Keyword Args:
        wordclass: Morphology wordclass label for the table.

    Returns:
        Sort key ordered by degree, inflection, gender, case, and number.

    """
    if (
        wordclass.strip().casefold() != "adjective"
        or len(row) < _MORPHOLOGY_TABLE_MIN_COLUMNS
    ):
        return (99,)
    dimensions = dict(
        zip(
            morphology_table_columns(wordclass)[1:],
            row[1:],
            strict=False,
        )
    )
    inflection = dimensions.get("inflection", "").casefold()
    return (
        _ADJECTIVE_DEGREE_ORDER.get(dimensions.get("degree", "").casefold(), 99),
        _ADJECTIVE_INFLECTION_ORDER.get(inflection, 99),
        _ADJECTIVE_GENDER_ORDER.get(dimensions.get("gender", "").casefold(), 99),
        _ADJECTIVE_CASE_ORDER.get(dimensions.get("case", "").casefold(), 99),
        _ADJECTIVE_NUMBER_ORDER.get(dimensions.get("number", "").casefold(), 99),
    )


def _decode_noun_like(code: str) -> dict[str, str]:
    """
    Decode noun-like case/gender/number function codes.

    Args:
        code: Morphology function code.

    Returns:
        Dimension labels for noun-like browse columns.

    """
    match = _NOUN_LIKE_PATTERN.fullmatch(code)
    if match is None:
        return {"function": code}
    return {
        "case": _label(_CASE_LABELS, match.group("case")),
        "gender": _label(_GENDER_LABELS, match.group("gender")),
        "number": _label(_NUMBER_LABELS, match.group("number")),
    }


def _decode_adjective(
    code: str,
    class1: str,
    class2: str,
    class3: str,
    *,
    morph_class_inflection: str = "",
) -> dict[str, str]:
    """
    Decode adjective degree/case/gender/number function codes.

    Args:
        code: Morphology function code.
        class1: First morphology class column.
        class2: Second morphology class column.
        class3: Third morphology class column.

    Keyword Args:
        morph_class_inflection: FK-backed strong/weak label when legacy classes
            are empty.

    Returns:
        Dimension labels for adjective browse columns.

    """
    match = _ADJ_PATTERN.fullmatch(code)
    if match is None:
        noun_like = _decode_noun_like(code)
        if noun_like:
            return noun_like
        return {"function": code}
    return {
        "degree": _label(_DEGREE_LABELS, match.group("degree")),
        "inflection": _pick_inflection(
            class1,
            class2,
            class3,
            morph_class_inflection=morph_class_inflection,
        ),
        "case": _label(_CASE_LABELS, match.group("case")),
        "gender": _label(_GENDER_LABELS, match.group("gender")),
        "number": _label(_NUMBER_LABELS, match.group("number")),
    }


def _decode_verb(code: str) -> dict[str, str]:
    """
    Decode verb tense/mood/person/number/participle function codes.

    Args:
        code: Morphology function code.

    Returns:
        Dimension labels for verb browse columns.

    """
    exact = _VERB_FUNCTION_LABELS.get(code)
    if exact is not None:
        return dict(exact)

    imperative = _IMP_PATTERN.fullmatch(code)
    if imperative is not None:
        return {
            "mood": "imperative",
            "number": _label(_NUMBER_LABELS, imperative.group("number")),
        }

    finite_sg = _VERB_FINITE_SG_PATTERN.fullmatch(code)
    if finite_sg is not None:
        return {
            "tense": _label(_TENSE_LABELS, finite_sg.group("tense")),
            "mood": _label(_MOOD_LABELS, finite_sg.group("mood")),
            "number": "singular",
            "person": _label(_PERSON_LABELS, finite_sg.group("person")),
        }

    finite = _VERB_FINITE_PATTERN.fullmatch(code)
    if finite is not None:
        dimensions = {
            "tense": _label(_TENSE_LABELS, finite.group("tense")),
            "mood": _label(_MOOD_LABELS, finite.group("mood")),
            "number": _label(_NUMBER_LABELS, finite.group("number")),
        }
        person = finite.group("person")
        if person:
            dimensions["person"] = _label(_PERSON_LABELS, person)
        return dimensions

    return {"function": code}


def morphology_table_columns(wordclass: str) -> tuple[str, ...]:
    """
    Return browse-table column headers for one morphology wordclass.

    Args:
        wordclass: Morphology wordclass label.

    Returns:
        Ordered column headers including the surface ``form`` column.

    """
    pos = wordclass.strip().casefold()
    if pos in {"verb", "participle"}:
        return (
            "form",
            "tense",
            "mood",
            "person",
            "number",
            "form_type",
            "object_case",
        )
    if pos == "adjective":
        return ("form", "degree", "inflection", "case", "gender", "number")
    if pos == "pronoun":
        return ("form", "case", "gender", "number", "person")
    if pos == "adverb":
        return ("form", "degree")
    if pos in {"noun", "preposition", "conjunction", "interjection", "indeclinable"}:
        return ("form", "case", "gender", "number")
    return ("form", "function")


def build_morphology_table(
    rows: list[MorphologyTableInputRow],
    *,
    wordclass: str,
) -> MorphologyTableSpec:
    """
    Build one morphology browse table for rows sharing a wordclass.

    Args:
        rows: Tuple payloads of
            ``(form, function, class1, class2, class3, formi[, inflection])``.

    Keyword Args:
        wordclass: Shared morphology wordclass label for the table.

    Returns:
        Column headers and aligned row cells for sidebar rendering.

    """
    columns = morphology_table_columns(wordclass)
    table_rows: list[tuple[str, ...]] = []
    for row in rows:
        values = [*row, "", "", "", "", "", "", ""]
        form, function, class1, class2, class3, formi, inflection = values[:7]
        surface = form.strip() or formi.strip()
        dimensions = decode_function_dimensions(
            function=function,
            wordclass=wordclass,
            class1=class1,
            class2=class2,
            class3=class3,
            morph_class_inflection=inflection,
        )
        if wordclass.strip().casefold() in {"verb", "participle"}:
            form_type = dimensions.pop("form", "")
            if form_type:
                dimensions["form_type"] = form_type
        cells = [surface, *[dimensions.get(column, "") for column in columns[1:]]]
        table_rows.append(tuple(cells))
    if wordclass.strip().casefold() == "adjective":
        table_rows.sort(
            key=lambda table_row: _adjective_row_sort_key(
                table_row,
                wordclass=wordclass,
            )
        )
    return MorphologyTableSpec(columns=columns, rows=tuple(table_rows))


#: Weak noun genitive endings that must not appear as spelling variants.
GENITIVE_VARIANT_ENDINGS: Final[frozenset[str]] = frozenset(
    {"es", "as", "an", "a", "e", "um"}
)

#: Single-letter BT gender codes mapped to browse labels.
BT_GENDER_LABELS: Final[dict[str, str]] = {
    "m": "masculine",
    "f": "feminine",
    "n": "neuter",
}

#: Morphology noun-paradigm exemplars mapped to Wright declension labels.
NOUN_PARADIGM_TO_DECLENSION: Final[dict[str, str]] = {
    "stán": "masculine a-stem",
    "cynn": "neuter a-stem",
    "word": "neuter a-stem",
    "hof": "neuter a-stem",
    "dæg": "masculine a-stem",
    "fæt": "neuter a-stem",
    "ár": "feminine ō-stem",
    "strengu": "feminine ō-stem",
    "hand": "feminine ō-stem",
    "feld": "masculine a-stem",
    "sunu": "masculine u-stem",
    "duru": "feminine u-stem",
    "bearu": "masculine wa-stem",
    "bealu": "neuter wa-stem",
    "guma": "masculine n-stem",
    "fréa": "masculine n-stem",
    "tunge": "feminine ō-stem",
    "éage": "neuter n-stem",
    "wígend": "nd-stem",
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


def is_genitive_variant_token(token: str) -> bool:
    """
    Return whether one variant token is a weak-noun genitive ending.

    Args:
        token: Candidate variant spelling.

    Returns:
        ``True`` when the token is a genitive ending, not a true variant.

    """
    return token.strip().casefold() in GENITIVE_VARIANT_ENDINGS


def format_bt_gender_label(code: str) -> str:
    """
    Map one BT gender code to a full browse label.

    Args:
        code: Single-letter or already-expanded gender label.

    Returns:
        Full gender label when recognized, otherwise the original code.

    """
    normalized = code.strip().casefold()
    return BT_GENDER_LABELS.get(normalized, code.strip())


def format_verb_class(class1: str, class2: str, class3: str = "") -> str | None:
    """
    Map morphology verb class columns to one Wright-style class label.

    Args:
        class1: Verb type code such as ``s``, ``w``, ``pp``, or ``a``.
        class2: Verb class number.
        class3: Verb subdivision code (ignored for browse labels).

    Returns:
        Human-readable verb class label, or ``None`` when unknown.

    """
    _ = class3
    verb_type = class1.strip().casefold()
    verb_class = class2.strip()
    if verb_type == "s" and verb_class.isdigit():
        return f"Strong {verb_class}"
    if verb_type == "w" and verb_class in {"1", "2", "3"}:
        weak_labels = {"1": "Weak I", "2": "Weak II", "3": "Weak III"}
        return weak_labels[verb_class]
    if verb_type == "pp":
        return "Preterite-Present"
    if verb_type == "a":
        return "Anomalous"
    return None


def format_noun_declension(paradigm: str) -> str | None:
    """
    Map one morphology noun-paradigm exemplar to a Wright declension label.

    Args:
        paradigm: Paradigm exemplar stored on morphology rows.

    Returns:
        Declension label when mapped, otherwise the raw paradigm name.

    """
    normalized = paradigm.strip().casefold()
    if not normalized:
        return None
    for key, label in NOUN_PARADIGM_TO_DECLENSION.items():
        if key.casefold() == normalized:
            return label
    return paradigm.strip()


def filter_display_variants(variants: list[str]) -> list[str]:
    """
    Drop genitive-ending tokens from dictionary variant spellings.

    Args:
        variants: Variant spellings from dictionary entry metadata.

    Returns:
        Variants with genitive endings removed.

    """
    return [
        variant
        for variant in variants
        if variant.strip() and not is_genitive_variant_token(variant)
    ]


def normalized_query_at_affix(text: str, query: str) -> bool:
    """
    Return whether a normalized query matches the start, end, or whole text.

    Args:
        text: Candidate display or headword text.
        query: Raw user query.

    Returns:
        ``True`` when the normalized query is an exact or affix match.

    """
    norm_query = normalize_old_english(query) or ""
    norm_text = normalize_old_english(text) or ""
    if not norm_query or not norm_text:
        return False
    return (
        norm_text == norm_query
        or norm_text.startswith(norm_query)
        or norm_text.endswith(norm_query)
    )


def lexical_distance(left: str, query: str) -> int:
    """
    Return the Levenshtein distance between one query and candidate text.

    Args:
        left: Candidate display or headword text.
        query: Raw user query.

    Returns:
        Edit distance between normalized strings, or a large sentinel when empty.

    """
    norm_left = normalize_old_english(left) or left.casefold()
    norm_query = normalize_old_english(query) or query.casefold()
    if not norm_left and not norm_query:
        return 0
    if not norm_left or not norm_query:
        return max(len(norm_left), len(norm_query))

    if len(norm_left) < len(norm_query):
        norm_left, norm_query = norm_query, norm_left

    previous = list(range(len(norm_query) + 1))
    for left_index, left_char in enumerate(norm_left, start=1):
        current = [left_index]
        for query_index, query_char in enumerate(norm_query, start=1):
            insert_cost = current[query_index - 1] + 1
            delete_cost = previous[query_index] + 1
            replace_cost = previous[query_index - 1] + (
                0 if left_char == query_char else 1
            )
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


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
                row_label = "Subjunctive Pl"
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

    """
    allowed_genders = {
        _gender_code_from_label(format_bt_gender_label(gender))
        for gender in entry_genders
        if gender.strip()
    }
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
