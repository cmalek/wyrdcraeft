"""SQLite-backed query service for lexicon browse search and details."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.lexicon.form_decode import (
    filter_display_variants,
    lexical_distance,
    normalized_query_at_affix,
)
from wyrdcraeft.services.markup import normalize_old_english

from .build import _normalize_dictionary_key, _normalize_morph_key
from .schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    KEY_KIND_STEM,
    KEY_KIND_VARIANT,
    RANK_TIER_EXACT_ENTRY,
    migrate_lexicon_schema,
)

if TYPE_CHECKING:
    from pathlib import Path


#: Stable precedence order for representative match selection within one rank tier.
_KEY_KIND_ORDER = {
    KEY_KIND_LEMMA: 0,
    KEY_KIND_VARIANT: 1,
    KEY_KIND_STEM: 2,
    KEY_KIND_FORM: 3,
}

#: Recognized gender markers derivable from morphology class metadata.
_GENDER_MARKERS = {"m", "f", "n"}
#: Recognized number markers derivable from morphology function labels.
_NUMBER_MARKERS = ("singular", "plural", "dual")
#: Recognized person markers derivable from morphology function labels.
_PERSON_MARKERS = ("first", "second", "third")


@dataclass(frozen=True)
class SearchHit:
    """
    One deduplicated dictionary-entry search result row.

    Attributes:
        entry_id: Matching dictionary entry identifier.
        headword: Preferred dictionary headword for the entry.
        pos: Part of speech stored on the dictionary entry.
        summary_sense: First non-empty gloss summary for the entry.
        rank_tier: Best locked ranking tier matched by the query.
        key_kind: Search-key kind responsible for the selected match row.
        matched_text: Display spelling from the matched search key.

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
    #: Search-key kind responsible for the selected match row.
    key_kind: str
    #: Display spelling from the matched search key.
    matched_text: str


@dataclass(frozen=True)
class OrphanHit:
    """
    One morphology-only search result row with no dictionary join.

    Attributes:
        form_id: Matching morphology form identifier.
        lemma: Best lemma-like display text for the orphan row.
        wordclass: Morphology wordclass label.
        function: Morphology function label.
        rank_tier: Locked orphan ranking tier.
        key_kind: Search-key kind responsible for the selected match row.
        matched_text: Display spelling from the matched search key.

    """

    #: Matching morphology form identifier.
    form_id: int
    #: Best lemma-like display text for the orphan row.
    lemma: str
    #: Morphology wordclass label.
    wordclass: str
    #: Morphology function label.
    function: str
    #: Locked orphan ranking tier.
    rank_tier: int
    #: Search-key kind responsible for the selected match row.
    key_kind: str
    #: Display spelling from the matched search key.
    matched_text: str


@dataclass(frozen=True)
class SearchResults:
    """
    Unified lexicon search payload for browse consumers.

    Attributes:
        main_entries: Deduplicated dictionary-entry hits ordered by rank.
        orphans: Morphology-only hits kept in a separate section.

    """

    #: Deduplicated dictionary-entry hits ordered by rank.
    main_entries: list[SearchHit]
    #: Morphology-only hits kept in a separate section.
    orphans: list[OrphanHit]

    @property
    def main_entry_count(self) -> int:
        """
        Count dictionary-entry hits so callers can detect single-result focus.

        Returns:
            Number of dictionary-entry hits in ``main_entries``.

        """
        return len(self.main_entries)


@dataclass(frozen=True)
class EntrySense:
    """
    One ordered dictionary sense used in lexicon details.

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
        class1: First morphology class label.
        class2: Second morphology class label.
        class3: Third morphology class label.
        paradigm: Morphology paradigm exemplar label.

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
    Full details payload for one dictionary-backed lexicon entry.

    Attributes:
        entry_id: Dictionary entry identifier.
        headword: Preferred dictionary headword.
        variants: Alternate spellings captured during lexicon build.
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

    """

    #: Dictionary entry identifier.
    entry_id: int
    #: Preferred dictionary headword.
    headword: str
    #: Alternate spellings captured during lexicon build.
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


@dataclass(frozen=True)
class OrphanDetails:
    """
    Full details payload for one morphology-only orphan row.

    Attributes:
        form_id: Morphology form identifier.
        lemma: Lemma-like BT display spelling.
        class_summary: Distinct non-empty morphology class labels.
        genders: Distinct gender markers derivable from stored data.
        persons: Distinct person markers derivable from stored data.
        numbers: Distinct number markers derivable from stored data.
        morphology_groups: Morphology rows grouped for sidebar rendering.

    """

    #: Morphology form identifier.
    form_id: int
    #: Lemma-like BT display spelling.
    lemma: str
    #: Distinct non-empty morphology class labels derivable from the row.
    class_summary: list[str]
    #: Distinct gender markers derivable from stored data.
    genders: list[str]
    #: Distinct person markers derivable from stored data.
    persons: list[str]
    #: Distinct number markers derivable from stored data.
    numbers: list[str]
    #: Morphology rows grouped for sidebar rendering.
    morphology_groups: list[MorphologyGroup]


def _json_string_list(payload: str) -> list[str]:
    """
    Deserialize a JSON string array from the lexicon read model.

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


def _entry_senses_from_json(payload: str) -> list[EntrySense]:
    """
    Deserialize ordered sense payloads from ``lexicon_entries.senses_json``.

    Args:
        payload: JSON array of ordered sense mappings.

    Returns:
        Ordered lexicon sense dataclasses.

    """
    raw_values = json.loads(payload)
    return [
        EntrySense(
            sense_label=str(value.get("sense_label", "")),
            gloss_en=str(value.get("gloss_en", "")).strip(),
            order_index=int(value.get("order_index", 0)),
        )
        for value in raw_values
    ]


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


def _search_candidate_keys(
    query: str,
    spelling_normalizer: BTSpellingNormalizer,
) -> list[str]:
    """
    Normalize a raw query into the key shapes stored by the builder.

    Args:
        query: Raw user-entered search string.
        spelling_normalizer: Dictionary spelling normalizer shared with the builder.

    Returns:
        Distinct normalized lookup keys suitable for ``lexicon_search_keys``.

    """
    text = query.strip()
    if not text:
        return []
    return _ordered_distinct(
        [
            _normalize_dictionary_key(text, spelling_normalizer),
            _normalize_morph_key(text),
            normalize_old_english(text) or "",
        ]
    )


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


def _row_to_morphology(row: sqlite3.Row) -> MorphologyRow:
    """
    Project one SQLite row into a ``MorphologyRow`` dataclass.

    Args:
        row: SQLite row from ``lexicon_forms``.

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
        class1=str(row["class1"]),
        class2=str(row["class2"]),
        class3=str(row["class3"]),
        paradigm=str(row["paradigm"]) if "paradigm" in row else "",
    )


def _hit_sort_key(hit: SearchHit) -> tuple[int, int]:
    """
    Return the sortable rank tuple for one search hit.

    Args:
        hit: Candidate search hit.

    Returns:
        Tuple of ``(rank_tier, key_kind_order)`` for dedupe comparisons.

    """
    return (hit.rank_tier, _KEY_KIND_ORDER.get(hit.key_kind, 99))


def _hit_lexical_distance(query: str, hit: SearchHit) -> int:
    """
    Return the closest lexical distance between a query and one search hit.

    Args:
        query: Raw user query.
        hit: Candidate dictionary-backed search hit.

    Returns:
        Minimum edit distance across headword and matched surface text.

    """
    distances = [
        lexical_distance(text, query)
        for text in (hit.headword, hit.matched_text)
        if text.strip()
    ]
    return min(distances) if distances else 9999


def _orphan_lexical_distance(query: str, hit: OrphanHit) -> int:
    """
    Return the closest lexical distance between a query and one orphan hit.

    Args:
        query: Raw user query.
        hit: Candidate orphan morphology hit.

    Returns:
        Minimum edit distance across lemma and matched surface text.

    """
    distances = [
        lexical_distance(text, query)
        for text in (hit.lemma, hit.matched_text)
        if text.strip()
    ]
    return min(distances) if distances else 9999


def _main_results_sort_key(query: str, hit: SearchHit) -> tuple[int, int, int, str]:
    """
    Return the browse sort key for one dictionary-backed search hit.

    Args:
        query: Raw user query.
        hit: Candidate dictionary-backed search hit.

    Returns:
        Sort tuple ordered by rank tier, key kind, lexical distance, headword.

    """
    return (
        hit.rank_tier,
        _KEY_KIND_ORDER.get(hit.key_kind, 99),
        _hit_lexical_distance(query, hit),
        normalize_old_english(hit.headword) or hit.headword.casefold(),
    )


def _orphan_results_sort_key(query: str, hit: OrphanHit) -> tuple[int, int, int, str]:
    """
    Return the browse sort key for one orphan morphology hit.

    Args:
        query: Raw user query.
        hit: Candidate orphan morphology hit.

    Returns:
        Sort tuple ordered by rank tier, key kind, lexical distance, lemma.

    """
    return (
        hit.rank_tier,
        _KEY_KIND_ORDER.get(hit.key_kind, 99),
        _orphan_lexical_distance(query, hit),
        normalize_old_english(hit.lemma) or hit.lemma.casefold(),
    )


def _hit_matches_query_intent(query: str, hit: SearchHit) -> bool:
    """
    Return whether one dictionary-backed hit matches the user's search intent.

    Args:
        query: Raw user query.
        hit: Candidate dictionary-backed search hit.

    Returns:
        ``True`` when the hit should remain in main results.

    """
    if hit.rank_tier == RANK_TIER_EXACT_ENTRY:
        return True
    matched = normalized_query_at_affix(hit.matched_text, query)
    headword = normalized_query_at_affix(hit.headword, query)
    return matched or headword


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


class LexiconQueryService:
    """
    Query interface over lexicon browse search and details tables in SQLite.

    Args:
        db_path: Path to ``morphology.sqlite3`` containing ``lexicon_*`` tables.

    """

    #: Active SQLite connection for search and details lookups.
    _connection: sqlite3.Connection
    #: Dictionary spelling normalizer reused for unified query normalization.
    _spelling_normalizer: BTSpellingNormalizer

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a lexicon query service for one SQLite database.

        Args:
            db_path: Path to SQLite database file containing ``lexicon_*`` tables.

        """
        #: Active SQLite connection for search and details lookups.
        self._connection = sqlite3.connect(str(db_path.expanduser().resolve()))
        self._connection.row_factory = sqlite3.Row
        migrate_lexicon_schema(self._connection)
        self._connection.commit()
        #: Dictionary spelling normalizer reused for unified query normalization.
        self._spelling_normalizer = BTSpellingNormalizer()

    def search(self, query: str) -> SearchResults:
        """
        Search unified lexicon keys and return entry-backed hits plus orphans.

        Args:
            query: Raw query string entered by the user.

        Returns:
            Deduplicated main results plus a separate orphan section.

        """
        lookup_keys = _search_candidate_keys(query, self._spelling_normalizer)
        if not lookup_keys:
            return SearchResults(main_entries=[], orphans=[])

        rows = self._connection.execute(
            """
            SELECT
                sk.key_kind,
                sk.rank_tier,
                sk.entry_id,
                sk.form_id,
                sk.display_text,
                e.headword,
                e.pos,
                e.summary_sense,
                f.bt,
                f.wordclass,
                f.function
            FROM lexicon_search_keys sk
            LEFT JOIN lexicon_entries e ON e.entry_id = sk.entry_id
            LEFT JOIN lexicon_forms f ON f.form_id = sk.form_id
            WHERE sk.key_text IN (
                SELECT value
                FROM json_each(?)
            )
            ORDER BY
                sk.rank_tier ASC,
                CASE sk.key_kind
                    WHEN 'lemma' THEN 0
                    WHEN 'variant' THEN 1
                    WHEN 'stem' THEN 2
                    WHEN 'form' THEN 3
                    ELSE 99
                END ASC,
                COALESCE(e.headword, f.bt, sk.display_text) ASC,
                COALESCE(sk.entry_id, 0) ASC,
                COALESCE(sk.form_id, 0) ASC
            """,
            (json.dumps(lookup_keys),),
        ).fetchall()

        main_entries: list[SearchHit] = []
        orphans: list[OrphanHit] = []
        best_main_hits: dict[tuple[str, str], SearchHit] = {}
        main_hit_order: list[tuple[str, str]] = []
        seen_form_ids: set[int] = set()

        for row in rows:
            entry_id = row["entry_id"]
            form_id = row["form_id"]
            rank_tier = int(row["rank_tier"])
            key_kind = str(row["key_kind"])
            matched_text = str(row["display_text"])
            if entry_id is not None:
                entry_id_int = int(entry_id)
                hit = SearchHit(
                    entry_id=entry_id_int,
                    headword=str(row["headword"]),
                    pos=str(row["pos"]),
                    summary_sense=str(row["summary_sense"]),
                    rank_tier=rank_tier,
                    key_kind=key_kind,
                    matched_text=matched_text,
                )
                if not _hit_matches_query_intent(query, hit):
                    continue
                dedupe_key = (
                    normalize_old_english(hit.headword) or "",
                    hit.pos.strip().casefold(),
                )
                existing = best_main_hits.get(dedupe_key)
                if existing is not None and _hit_sort_key(hit) >= _hit_sort_key(
                    existing
                ):
                    continue
                if existing is None:
                    main_hit_order.append(dedupe_key)
                best_main_hits[dedupe_key] = hit
                continue

            if form_id is None:
                continue
            form_id_int = int(form_id)
            if form_id_int in seen_form_ids:
                continue
            seen_form_ids.add(form_id_int)
            orphans.append(
                OrphanHit(
                    form_id=form_id_int,
                    lemma=str(row["bt"]),
                    wordclass=str(row["wordclass"]),
                    function=str(row["function"]),
                    rank_tier=rank_tier,
                    key_kind=key_kind,
                    matched_text=matched_text,
                )
            )

        main_entries = [best_main_hits[key] for key in main_hit_order]
        main_entries.sort(key=lambda hit: _main_results_sort_key(query, hit))
        orphans.sort(key=lambda hit: _orphan_results_sort_key(query, hit))

        return SearchResults(main_entries=main_entries, orphans=orphans)

    def get_details(self, entry_id: int) -> EntryDetails | None:
        """
        Load the full browse details payload for one dictionary-backed entry.

        Args:
            entry_id: Dictionary entry identifier from search results.

        Returns:
            Entry details payload, or ``None`` when the entry is absent.

        """
        entry_row = self._connection.execute(
            """
            SELECT
                entry_id,
                headword,
                pos,
                summary_sense,
                etymology,
                variants_json,
                genders_json,
                senses_json
            FROM lexicon_entries
            WHERE entry_id = ?
            """,
            (entry_id,),
        ).fetchone()
        if entry_row is None:
            return None

        form_rows = self._connection.execute(
            """
            SELECT
                form_id,
                bt,
                title,
                stem,
                form,
                formi,
                wordclass,
                function,
                probability,
                class1,
                class2,
                class3,
                paradigm
            FROM lexicon_forms
            WHERE entry_id = ?
            ORDER BY wordclass ASC, function ASC, form_id ASC
            """,
            (entry_id,),
        ).fetchall()

        morphology_rows = [_row_to_morphology(row) for row in form_rows]
        class_summary = _ordered_distinct(
            [
                value
                for row in morphology_rows
                for value in (row.class1, row.class2, row.class3)
            ]
        )
        entry_genders = _json_string_list(str(entry_row["genders_json"]))
        genders, persons, numbers = _extract_gender_person_number(
            functions=[row.function for row in morphology_rows],
            class_values=class_summary,
            entry_genders=entry_genders,
        )

        return EntryDetails(
            entry_id=int(entry_row["entry_id"]),
            headword=str(entry_row["headword"]),
            variants=filter_display_variants(
                _json_string_list(str(entry_row["variants_json"]))
            ),
            pos=str(entry_row["pos"]),
            class_summary=class_summary,
            genders=genders,
            persons=persons,
            numbers=numbers,
            summary_sense=str(entry_row["summary_sense"]),
            senses=_entry_senses_from_json(str(entry_row["senses_json"])),
            etymology=str(entry_row["etymology"]),
            morphology_groups=_group_morphology_rows(morphology_rows),
            declension_paradigm=_dominant_paradigm(morphology_rows),
        )

    def get_orphan_details(self, form_id: int) -> OrphanDetails | None:
        """
        Load a details payload for one morphology orphan row.

        Args:
            form_id: Morphology form identifier from orphan search results.

        Returns:
            Orphan details payload, or ``None`` when the row is absent or linked.

        """
        row = self._connection.execute(
            """
            SELECT
                form_id,
                bt,
                title,
                stem,
                form,
                formi,
                wordclass,
                function,
                probability,
                class1,
                class2,
                class3,
                paradigm
            FROM lexicon_forms
            WHERE form_id = ? AND entry_id IS NULL
            """,
            (form_id,),
        ).fetchone()
        if row is None:
            return None

        morphology_row = _row_to_morphology(row)
        class_summary = _ordered_distinct(
            [morphology_row.class1, morphology_row.class2, morphology_row.class3]
        )
        genders, persons, numbers = _extract_gender_person_number(
            functions=[morphology_row.function],
            class_values=class_summary,
            entry_genders=[],
        )
        return OrphanDetails(
            form_id=morphology_row.form_id,
            lemma=morphology_row.lemma,
            class_summary=class_summary,
            genders=genders,
            persons=persons,
            numbers=numbers,
            morphology_groups=_group_morphology_rows([morphology_row]),
        )

    def close(self) -> None:
        """
        Close the SQLite query connection.

        Side Effects:
            Releases the underlying SQLite connection.

        """
        self._connection.close()
