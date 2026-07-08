"""Query-time dictionary browse search and detail loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.dictionary import format_sense_display_label, sense_path_sort_key
from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.markup import normalize_morphology_title, normalize_old_english
from wyrdcraeft.services.morphology.catalog.pos import catalog_pos_from_bt_pos
from wyrdcraeft.services.morphology.catalog.query import (
    LemmaMorphClassSummary,
    MorphologyCatalogQueryService,
    format_morph_class_display_label,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from sqlalchemy.engine import Connection, Engine, RowMapping


@dataclass(frozen=True)
class BrowseSearchHit:
    """
    One deduplicated dictionary-entry search result row.

    Attributes:
        entry_id: Matching dictionary entry identifier.
        headword: Preferred dictionary headword for the entry.
        pos: Part of speech stored on the dictionary entry.
        summary_sense: First non-empty gloss summary for the entry.
        rank_tier: Best locked ranking tier matched by the query.
        matched_text: Headword or variant spelling responsible for the match.

    """

    #: Matching dictionary entry identifier.
    entry_id: int
    #: Preferred dictionary headword for the entry.
    headword: str
    #: Part of speech stored on the dictionary entry.
    pos: str
    #: First non-empty gloss summary for the entry.
    summary_sense: str
    #: Best locked ranking tier matched by the query.
    rank_tier: int
    #: Headword or variant spelling responsible for the match.
    matched_text: str


@dataclass(frozen=True)
class EntrySense:
    """
    One ordered dictionary sense used in browse details.

    Attributes:
        sense_label: Source sense label such as ``I`` or ``II``.
        gloss_en: English gloss text for the sense.
        order_index: Stable stored ordering from the builder payload.

    """

    #: Source sense label such as ``I`` or ``II``.
    sense_label: str
    #: English gloss text for the sense.
    gloss_en: str
    #: Stable stored ordering from the builder payload.
    order_index: int


@dataclass(frozen=True)
class MorphologyRow:
    """
    One raw projected morphology row for sidebar rendering.

    Note:
        ``wordclass`` and ``function`` are read from the ``parts_of_speech`` and
        ``inflection_codes`` foreign-key joins. ``class1``-``class3`` and
        ``paradigm`` have no FK replacement column on ``forms`` after the
        Phase D legacy-string drop and are always empty pending FK-backed
        class/paradigm display sourced from ``morph_classes``.

    Attributes:
        form_id: Morphology form identifier.
        lemma: Lemma-like BT display spelling.
        title: Title display spelling.
        stem: Stem spelling used for generation.
        form: Surface form spelling.
        formi: Alternate surface spelling.
        wordclass: Morphology wordclass label.
        function: Morphology function label.
        probability: Stored probability marker.
        class1: First morphology class label (always empty; see Note).
        class2: Second morphology class label (always empty; see Note).
        class3: Third morphology class label (always empty; see Note).
        paradigm: Morphology paradigm exemplar label (always empty; see Note).

    """

    #: Morphology form identifier.
    form_id: int
    #: Lemma-like BT display spelling.
    lemma: str
    #: Title display spelling.
    title: str
    #: Stem spelling used for generation.
    stem: str
    #: Surface form spelling.
    form: str
    #: Alternate surface spelling.
    formi: str
    #: Morphology wordclass label.
    wordclass: str
    #: Morphology function label.
    function: str
    #: Stored probability marker.
    probability: str
    #: First morphology class label.
    class1: str
    #: Second morphology class label.
    class2: str
    #: Third morphology class label.
    class3: str
    #: Morphology paradigm exemplar label.
    paradigm: str


@dataclass(frozen=True)
class MorphologyGroup:
    """
    Sidebar grouping of morphology rows by wordclass and function.

    Attributes:
        wordclass: Shared wordclass label for the group.
        function: Shared function label for the group.
        rows: Morphology rows appearing in the group.

    """

    #: Shared wordclass label for the group.
    wordclass: str
    #: Shared function label for the group.
    function: str
    #: Morphology rows appearing in the group.
    rows: list[MorphologyRow]


@dataclass(frozen=True)
class EntryDetails:
    """
    Full details payload for one dictionary-backed browse entry.

    Note:
        ``class_summary`` and ``declension_paradigm`` are always empty because
        ``forms.class1``-``class3``/``paradigm`` have no FK replacement column
        after the Phase D legacy-string drop; see ``MorphologyRow``.

    Attributes:
        entry_id: Dictionary entry identifier.
        headword: Preferred dictionary headword.
        variants: Alternate spellings captured during dictionary build.
        pos: Part of speech stored on the dictionary entry.
        class_summary: Distinct non-empty morphology class labels.
        genders: Distinct gender markers derivable from stored data.
        persons: Distinct person markers derivable from stored data.
        numbers: Distinct number markers derivable from stored data.
        summary_sense: First non-empty gloss summary.
        senses: Ordered full sense list.
        etymology: Dictionary etymology text.
        morphology_groups: Morphology rows grouped for sidebar rendering.
        declension_paradigm: Dominant morphology paradigm exemplar for the entry.
        morph_class: Catalog-backed morph-class summary, or ``None`` when the
            dictionary POS has no catalog mapping.

    """

    #: Dictionary entry identifier.
    entry_id: int
    #: Preferred dictionary headword.
    headword: str
    #: Alternate spellings captured during dictionary build.
    variants: list[str]
    #: Part of speech stored on the dictionary entry.
    pos: str
    #: Distinct non-empty morphology class labels.
    class_summary: list[str]
    #: Distinct gender markers derivable from stored data.
    genders: list[str]
    #: Distinct person markers derivable from stored data.
    persons: list[str]
    #: Distinct number markers derivable from stored data.
    numbers: list[str]
    #: First non-empty gloss summary.
    summary_sense: str
    #: Ordered full sense list.
    senses: list[EntrySense]
    #: Dictionary etymology text.
    etymology: str
    #: Morphology rows grouped for sidebar rendering.
    morphology_groups: list[MorphologyGroup]
    #: Dominant morphology paradigm exemplar for the entry.
    declension_paradigm: str
    #: Catalog-backed morph-class summary, or ``None`` when unmappable.
    morph_class: LemmaMorphClassSummary | None


@dataclass(frozen=True)
class _QueryKeys:
    """Normalized query forms used by browse search ranking."""

    #: Raw user-entered query string.
    raw_query: str
    #: Display-form query normalized with Bosworth-Toller spelling rules.
    display_query: str
    #: Macron-preserving normalized title used for dictionary joins.
    normalized_title: str
    #: Diacritic-stripped lookup key used for broad matching.
    norm_key: str


#: Recognized gender markers derivable from morphology class metadata.
_GENDER_MARKERS = {"m", "f", "n"}
#: Recognized number markers derivable from morphology function labels.
_NUMBER_MARKERS = ("singular", "plural", "dual")
#: Recognized person markers derivable from morphology function labels.
_PERSON_MARKERS = ("first", "second", "third")
#: Weak noun genitive endings that must not appear as spelling variants.
_GENITIVE_VARIANT_ENDINGS = frozenset({"es", "as", "an", "a", "e", "um"})


def _json_string_list(payload: str) -> list[str]:
    """
    Deserialize a JSON string array stored in SQLite text columns.

    Args:
        payload: JSON array payload stored in SQLite text columns.

    Returns:
        Parsed string list with whitespace trimmed and empty members removed.

    """
    raw_values = json.loads(payload)
    values: list[str] = []
    for value in raw_values:
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def _append_unique(values: list[str], value: str) -> None:
    """
    Append a string to a list when it is non-empty and not already present.

    Args:
        values: Destination list preserving insertion order.
        value: Candidate value to append.

    Side Effects:
        Mutates ``values`` when ``value`` is unique and non-empty.

    """
    candidate = value.strip()
    if candidate and candidate not in values:
        values.append(candidate)


def _ordered_distinct(values: list[str]) -> list[str]:
    """
    Return non-empty distinct strings preserving first-seen order.

    Args:
        values: Candidate string values.

    Returns:
        Ordered distinct strings.

    """
    result: list[str] = []
    for value in values:
        _append_unique(result, value)
    return result


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
        if variant.strip()
        and variant.strip().casefold() not in _GENITIVE_VARIANT_ENDINGS
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


def _extract_gender_person_number(
    *,
    functions: list[str],
    class_values: list[str],
    entry_genders: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """
    Derive display-friendly gender, person, and number markers from stored data.

    Keyword Args:
        functions: Morphology function labels collected from linked rows.
        class_values: Morphology class labels collected from linked rows.
        entry_genders: Gender labels already stored on the dictionary entry.

    Returns:
        Tuple of ``(genders, persons, numbers)`` lists in stable order.

    """
    genders = _ordered_distinct(entry_genders)
    for class_value in class_values:
        if class_value.casefold() in _GENDER_MARKERS:
            _append_unique(genders, class_value.casefold())

    persons: list[str] = []
    numbers: list[str] = []
    for function in functions:
        tokens = function.casefold()
        for marker in _PERSON_MARKERS:
            if marker in tokens:
                _append_unique(persons, marker)
        for marker in _NUMBER_MARKERS:
            if marker in tokens:
                _append_unique(numbers, marker)

    return genders, persons, numbers


def _row_to_morphology(row: RowMapping | Mapping[str, Any]) -> MorphologyRow:
    """
    Project one SQLite row into a ``MorphologyRow`` dataclass.

    Args:
        row: Mapping row from a ``forms``-joined query.

    Returns:
        Typed morphology row payload.

    """
    return MorphologyRow(
        form_id=int(row["form_id"]),
        lemma=str(row["bt"]),
        title=str(row["title"]),
        stem=str(row["stem"]),
        form=str(row["form"]),
        formi=str(row["formi"]),
        wordclass=str(row["wordclass"]),
        function=str(row["function"]),
        probability=str(row["probability"]),
        class1="",
        class2="",
        class3="",
        paradigm="",
    )


def _dominant_paradigm(rows: list[MorphologyRow]) -> str:
    """
    Pick the most common non-empty morphology paradigm label for one entry.

    Args:
        rows: Morphology rows linked to one dictionary entry.

    Returns:
        Dominant paradigm exemplar, or an empty string when none exist.

    """
    counts: dict[str, int] = {}
    for row in rows:
        paradigm = row.paradigm.strip()
        if not paradigm:
            continue
        counts[paradigm] = counts.get(paradigm, 0) + 1
    if not counts:
        return ""
    return max(counts, key=lambda key: counts[key])


def _group_morphology_rows(rows: list[MorphologyRow]) -> list[MorphologyGroup]:
    """
    Group raw morphology rows by ``wordclass`` and ``function``.

    Args:
        rows: Morphology rows in desired display order.

    Returns:
        Sidebar groups preserving first-seen ordering.

    """
    grouped: dict[tuple[str, str], list[MorphologyRow]] = {}
    order: list[tuple[str, str]] = []
    for row in rows:
        key = (row.wordclass, row.function)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(row)
    return [
        MorphologyGroup(
            wordclass=wordclass,
            function=function,
            rows=grouped[(wordclass, function)],
        )
        for wordclass, function in order
    ]


def _unclassified_morph_class_summary() -> LemmaMorphClassSummary:
    """
    Build the browse sentinel used when no deterministic assignment exists.

    Returns:
        Summary payload marking the lemma as explicitly unclassified.

    """
    return LemmaMorphClassSummary(
        display_label="Unclassified",
        assignment_source="",
        wright_sections=(),
        is_unclassified=True,
    )


def _normalize_query(
    query: str,
    spelling_normalizer: BTSpellingNormalizer,
) -> _QueryKeys | None:
    """
    Normalize a browse query into display, title, and lookup-key forms.

    Args:
        query: Raw user-entered browse query.
        spelling_normalizer: Dictionary spelling normalizer shared with indexing.

    Returns:
        Distinct normalized query forms, or ``None`` when the query is blank.

    """
    raw_query = query.strip()
    if not raw_query:
        return None
    return _QueryKeys(
        raw_query=raw_query,
        display_query=spelling_normalizer.normalize(raw_query),
        normalized_title=normalize_morphology_title(raw_query),
        norm_key=normalize_old_english(raw_query) or "",
    )


def _normalized_affix_match(candidate: str, query: str) -> bool:
    """
    Return whether a normalized query matches candidate start, end, or whole text.

    Args:
        candidate: Pre-normalized candidate string.
        query: Pre-normalized query string.

    Returns:
        ``True`` when the query is an exact, prefix, or suffix match.

    """
    if not candidate or not query:
        return False
    return (
        candidate == query
        or candidate.startswith(query)
        or candidate.endswith(query)
    )


def _rank_candidate(  # noqa: PLR0911, PLR0913
    *,
    query_keys: _QueryKeys,
    display_text: str,
    normalized_title: str,
    norm_key: str,
    exact_display_tier: int,
    exact_normalized_title_tier: int,
    exact_norm_key_tier: int,
    affix_display_tier: int,
    affix_normalized_title_tier: int,
    affix_norm_key_tier: int,
) -> int | None:
    """
    Rank one headword or variant candidate against the locked browse ladder.

    Keyword Args:
        query_keys: Normalized browse query forms.
        display_text: Candidate display spelling.
        normalized_title: Candidate macron-preserving normalized title.
        norm_key: Candidate diacritic-stripped lookup key.
        exact_display_tier: Tier for exact display spelling equality.
        exact_normalized_title_tier: Tier for exact normalized-title equality.
        exact_norm_key_tier: Tier for exact normalized-key equality.
        affix_display_tier: Tier for display prefix/suffix match.
        affix_normalized_title_tier: Tier for normalized-title affix match.
        affix_norm_key_tier: Tier for normalized-key affix match.

    Returns:
        Best matching tier, or ``None`` when the candidate does not match.

    """
    if display_text.casefold() == query_keys.display_query.casefold():
        return exact_display_tier
    if normalized_title == query_keys.normalized_title:
        return exact_normalized_title_tier
    if norm_key == query_keys.norm_key:
        return exact_norm_key_tier
    if normalized_query_at_affix(display_text, query_keys.raw_query):
        return affix_display_tier
    if _normalized_affix_match(normalized_title, query_keys.normalized_title):
        return affix_normalized_title_tier
    if _normalized_affix_match(norm_key, query_keys.norm_key):
        return affix_norm_key_tier
    return None


def _hit_lexical_distance(query: str, hit: BrowseSearchHit) -> int:
    """
    Return the closest lexical distance between a query and one browse hit.

    Args:
        query: Raw user query.
        hit: Candidate browse hit.

    Returns:
        Minimum edit distance across headword and matched surface text.

    """
    distances = [
        lexical_distance(text, query)
        for text in (hit.headword, hit.matched_text)
        if text.strip()
    ]
    return min(distances) if distances else 9999


def _browse_hit_sort_key(query: str, hit: BrowseSearchHit) -> tuple[int, int, str]:
    """
    Return the locked browse ordering for one dictionary result row.

    Args:
        query: Raw user query.
        hit: Candidate browse hit.

    Returns:
        Sort tuple ordered by rank tier, lexical distance, then headword.

    """
    return (
        hit.rank_tier,
        _hit_lexical_distance(query, hit),
        normalize_old_english(hit.headword) or hit.headword.casefold(),
    )


def _best_hit(
    query: str,
    left: BrowseSearchHit | None,
    right: BrowseSearchHit | None,
) -> BrowseSearchHit | None:
    """
    Pick the better browse hit under tier and lexical-distance ordering.

    Args:
        query: Raw user query.
        left: Existing best hit for one entry.
        right: Newly ranked candidate hit.

    Returns:
        Better-ranked hit, or ``None`` when neither hit exists.

    """
    if left is None:
        return right
    if right is None:
        return left
    if _browse_hit_sort_key(query, right) < _browse_hit_sort_key(query, left):
        return right
    return left


class DictionaryBrowseQueryService:
    """
    Query-time dictionary browse service over canonical ``bt_*`` and ``forms`` tables.

    Args:
        db_path: Path to ``wyrdcraeft.sqlite3`` containing ``bt_*`` and ``forms``
            tables.

    """

    #: SQLAlchemy engine bound to the canonical dictionary database.
    _engine: Engine
    #: Active SQLAlchemy connection for browse search and detail lookups.
    _connection: Connection
    #: Dictionary spelling normalizer reused for browse query normalization.
    _spelling_normalizer: BTSpellingNormalizer
    #: Read-only Wright catalog query service sharing the same engine.
    _catalog_query_service: MorphologyCatalogQueryService

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a query-time browse service for one SQLite database.

        Args:
            db_path: Path to SQLite database file containing ``bt_*`` and ``forms``
                tables.

        """
        #: SQLAlchemy engine bound to the canonical dictionary database.
        self._engine = create_sqlalchemy_engine(db_path)
        #: Active SQLAlchemy connection for browse search and detail lookups.
        self._connection = self._engine.connect()
        #: Dictionary spelling normalizer reused for browse query normalization.
        self._spelling_normalizer = BTSpellingNormalizer()
        #: Read-only Wright catalog query service sharing the same engine.
        self._catalog_query_service = MorphologyCatalogQueryService(self._engine)

    def search(self, query: str) -> list[BrowseSearchHit]:
        """
        Search dictionary headwords and variants at query time.

        Args:
            query: Raw query string entered by the user.

        Returns:
            Deduplicated browse hits ordered by the locked rank ladder.

        """
        query_keys = _normalize_query(query, self._spelling_normalizer)
        if query_keys is None:
            return []

        entry_rows = self._connection.execute(
            text(
                """
                WITH first_senses AS (
                    SELECT entry_id, gloss_en
                    FROM (
                        SELECT
                            entry_id,
                            gloss_en,
                            ROW_NUMBER() OVER (
                                PARTITION BY entry_id
                                ORDER BY order_index ASC, id ASC
                            ) AS row_no
                        FROM bt_senses
                    )
                    WHERE row_no = 1
                )
                SELECT
                    e.id AS entry_id,
                    e.headword AS headword,
                    e.normalized_title AS normalized_title,
                    e.norm_key AS norm_key,
                    e.pos_id AS pos_id,
                    p.code AS pos,
                    COALESCE(fs.gloss_en, '') AS summary_sense
                FROM bt_entries e
                JOIN parts_of_speech p ON p.id = e.pos_id
                LEFT JOIN first_senses fs ON fs.entry_id = e.id
                ORDER BY e.entry_order ASC, e.id ASC
                """
            )
        ).mappings().all()
        variant_rows = self._connection.execute(
            text(
                """
                SELECT entry_id, spelling_macronized, normalized_title
                FROM bt_variants
                ORDER BY entry_id ASC, spelling_raw ASC, spelling_macronized ASC
                """
            )
        ).mappings().all()

        variants_by_entry: dict[int, list[tuple[str, str]]] = {}
        for row in variant_rows:
            variants_by_entry.setdefault(int(row["entry_id"]), []).append(
                (
                    str(row["spelling_macronized"]),
                    str(row["normalized_title"]),
                )
            )

        best_hits: dict[tuple[int, int], BrowseSearchHit] = {}
        for row in entry_rows:
            entry_id = int(row["entry_id"])
            pos_id = int(row["pos_id"])
            headword = str(row["headword"])
            pos = str(row["pos"])
            summary_sense = str(row["summary_sense"]).strip()
            best_for_entry: BrowseSearchHit | None = None

            headword_tier = _rank_candidate(
                query_keys=query_keys,
                display_text=headword,
                normalized_title=str(row["normalized_title"]),
                norm_key=str(row["norm_key"]),
                exact_display_tier=1,
                exact_normalized_title_tier=3,
                exact_norm_key_tier=5,
                affix_display_tier=7,
                affix_normalized_title_tier=9,
                affix_norm_key_tier=11,
            )
            if headword_tier is not None:
                best_for_entry = BrowseSearchHit(
                    entry_id=entry_id,
                    headword=headword,
                    pos=pos,
                    summary_sense=summary_sense,
                    rank_tier=headword_tier,
                    matched_text=headword,
                )

            for spelling_macronized, normalized_title in variants_by_entry.get(
                entry_id,
                [],
            ):
                variant_tier = _rank_candidate(
                    query_keys=query_keys,
                    display_text=spelling_macronized,
                    normalized_title=normalized_title,
                    norm_key=normalize_old_english(spelling_macronized) or "",
                    exact_display_tier=2,
                    exact_normalized_title_tier=4,
                    exact_norm_key_tier=6,
                    affix_display_tier=8,
                    affix_normalized_title_tier=10,
                    affix_norm_key_tier=12,
                )
                if variant_tier is None:
                    continue
                best_for_entry = _best_hit(
                    query,
                    best_for_entry,
                    BrowseSearchHit(
                        entry_id=entry_id,
                        headword=headword,
                        pos=pos,
                        summary_sense=summary_sense,
                        rank_tier=variant_tier,
                        matched_text=spelling_macronized,
                    ),
                )

            if best_for_entry is None:
                continue
            dedupe_key = (entry_id, pos_id)
            best_hits[dedupe_key] = _best_hit(
                query,
                best_hits.get(dedupe_key),
                best_for_entry,
            ) or best_for_entry

        return sorted(
            best_hits.values(),
            key=lambda hit: _browse_hit_sort_key(query, hit),
        )

    def get_details(self, entry_id: int) -> EntryDetails | None:
        """
        Load the full browse details payload for one dictionary-backed entry.

        Note:
            Senses and variants are read directly from ``bt_senses`` and
            ``bt_variants``. Morphology rows are read from ``forms`` filtered by
            ``entry_id`` and, when set, by ``wordclass_id`` matching the entry's own
            ``pos_id`` so wordclass-ambiguous form links cannot leak into the sidebar.

        Args:
            entry_id: Dictionary entry identifier from browse results.

        Returns:
            Entry details payload, or ``None`` when the entry is absent.

        """
        entry_row = self._connection.execute(
            text(
                """
                SELECT
                    bt_entries.id AS entry_id,
                    bt_entries.headword AS headword,
                    bt_entries.etymology AS etymology,
                    bt_entries.genders_json AS genders_json,
                    bt_entries.pos_id AS pos_id,
                    parts_of_speech.code AS pos
                FROM bt_entries
                JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
                WHERE bt_entries.id = :entry_id
                """
            ),
            {"entry_id": entry_id},
        ).mappings().first()
        if entry_row is None:
            return None

        variant_rows = self._connection.execute(
            text(
                """
                SELECT spelling_macronized
                FROM bt_variants
                WHERE entry_id = :entry_id
                ORDER BY spelling_raw ASC
                """
            ),
            {"entry_id": entry_id},
        ).scalars().all()

        senses = self._load_entry_senses(entry_id)
        summary_sense = next((sense.gloss_en for sense in senses if sense.gloss_en), "")

        form_rows = self._connection.execute(
            text(
                """
                SELECT
                    forms.id AS form_id,
                    forms.BT AS bt,
                    forms.title AS title,
                    forms.stem AS stem,
                    forms.form AS form,
                    forms.formi AS formi,
                    COALESCE(wordclass_pos.code, '') AS wordclass,
                    COALESCE(inflection_codes.code, '') AS function,
                    forms.probability AS probability
                FROM forms
                LEFT JOIN parts_of_speech AS wordclass_pos
                    ON wordclass_pos.id = forms.wordclass_id
                LEFT JOIN inflection_codes
                    ON inflection_codes.id = forms.inflection_code_id
                WHERE forms.entry_id = :entry_id
                    AND (forms.wordclass_id IS NULL OR forms.wordclass_id = :pos_id)
                ORDER BY wordclass ASC, function ASC, forms.id ASC
                """
            ),
            {"entry_id": entry_id, "pos_id": int(entry_row["pos_id"])},
        ).mappings().all()

        morphology_rows = [_row_to_morphology(row) for row in form_rows]
        class_summary: list[str] = []
        entry_genders = _json_string_list(str(entry_row["genders_json"]))
        genders, persons, numbers = _extract_gender_person_number(
            functions=[row.function for row in morphology_rows],
            class_values=class_summary,
            entry_genders=entry_genders,
        )
        headword = str(entry_row["headword"])
        entry_pos = str(entry_row["pos"])

        return EntryDetails(
            entry_id=int(entry_row["entry_id"]),
            headword=headword,
            variants=filter_display_variants([str(value) for value in variant_rows]),
            pos=entry_pos,
            class_summary=class_summary,
            genders=genders,
            persons=persons,
            numbers=numbers,
            summary_sense=summary_sense,
            senses=senses,
            etymology=str(entry_row["etymology"]),
            morphology_groups=_group_morphology_rows(morphology_rows),
            declension_paradigm=_dominant_paradigm(morphology_rows),
            morph_class=self._lookup_entry_morph_class(
                headword=headword,
                entry_pos=entry_pos,
            ),
        )

    def _load_entry_senses(self, entry_id: int) -> list[EntrySense]:
        """
        Load ordered ``bt_senses`` rows for one dictionary entry.

        Args:
            entry_id: Dictionary entry identifier.

        Returns:
            Ordered browse sense dataclasses.

        """
        sense_rows = self._connection.execute(
            text(
                """
                SELECT
                    sense_label,
                    gloss_en,
                    order_index,
                    source_label_raw,
                    sense_path
                FROM bt_senses
                WHERE entry_id = :entry_id
                ORDER BY order_index ASC, id ASC
                """
            ),
            {"entry_id": entry_id},
        ).mappings().all()
        sorted_rows = sorted(
            sense_rows,
            key=lambda row: sense_path_sort_key(str(row["sense_path"])),
        )
        return [
            EntrySense(
                sense_label=(
                    format_sense_display_label(str(row["sense_path"]))
                    if str(row.get("source_label_raw") or "").strip()
                    else ""
                ),
                gloss_en=str(row["gloss_en"]).strip(),
                order_index=int(row["order_index"]),
            )
            for row in sorted_rows
        ]

    def _lookup_entry_morph_class(
        self,
        *,
        headword: str,
        entry_pos: str,
    ) -> LemmaMorphClassSummary | None:
        """
        Resolve catalog-backed morph-class metadata for one dictionary entry.

        Keyword Args:
            headword: Dictionary headword for the selected entry.
            entry_pos: Dictionary part-of-speech label for the selected entry.

        Returns:
            Summary payload for the entry, an unclassified sentinel when no
            assignment exists, or ``None`` when the entry POS cannot map to the
            catalog vocabulary.

        """
        normalized_title = normalize_morphology_title(headword)
        if not normalized_title:
            return _unclassified_morph_class_summary()
        try:
            catalog_pos = catalog_pos_from_bt_pos(entry_pos)
        except ValueError:
            return None
        view = self._catalog_query_service.lookup_lemma_class(
            normalized_title,
            catalog_pos,
        )
        if view is None:
            return _unclassified_morph_class_summary()
        return LemmaMorphClassSummary(
            display_label=format_morph_class_display_label(view),
            assignment_source=view.assignment_source,
            wright_sections=view.wright_sections,
            is_unclassified=False,
        )

    def lookup_wright_section_text(self, section_no: int) -> str | None:
        """
        Resolve stored Wright section text for browse detail interactions.

        Args:
            section_no: Wright grammar section number selected in the TUI.

        Returns:
            Stored section text, or ``None`` when the section has not been ingested.

        """
        return self._catalog_query_service.lookup_wright_section_text(section_no)

    def close(self) -> None:
        """
        Close the SQLAlchemy query connection.

        Side Effects:
            Releases the underlying SQLAlchemy connection and engine.

        """
        self._connection.close()
        self._engine.dispose()


__all__ = ["BrowseSearchHit", "DictionaryBrowseQueryService"]
