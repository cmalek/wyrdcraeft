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
        if code == "Su":
            return {"degree": "superlative"}
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
