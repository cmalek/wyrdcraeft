"""Lexicon read-model table names and build metadata constants."""

from __future__ import annotations

from typing import Final

#: Lexicon dictionary-entry table storing one row per real Bosworth-Toller entry.
TABLE_LEXICON_ENTRIES: Final = "lexicon_entries"
#: Lexicon morphology projection table; rows may exist without a dictionary entry.
TABLE_LEXICON_FORMS: Final = "lexicon_forms"
#: Lexicon normalized search keys used for unified lookup and ranking.
TABLE_LEXICON_SEARCH_KEYS: Final = "lexicon_search_keys"
#: Lexicon build metadata key/value store.
TABLE_LEXICON_BUILD_META: Final = "lexicon_build_meta"

#: Ordered lexicon table names managed by Alembic and truncated during rebuild.
LEXICON_TABLE_NAMES: Final = (
    TABLE_LEXICON_ENTRIES,
    TABLE_LEXICON_FORMS,
    TABLE_LEXICON_SEARCH_KEYS,
    TABLE_LEXICON_BUILD_META,
)

#: Metadata key storing the ISO-8601 UTC timestamp of the last rebuild.
META_KEY_BUILT_AT: Final = "built_at"
#: Metadata key storing the source ``forms`` row count at rebuild time.
META_KEY_FORMS_SOURCE_COUNT: Final = "forms_source_count"
#: Metadata key storing the source ``bt_entries`` row count at rebuild time.
META_KEY_BT_ENTRIES_SOURCE_COUNT: Final = "bt_entries_source_count"

#: Search-key kind for dictionary headword matches.
KEY_KIND_LEMMA: Final = "lemma"
#: Search-key kind for dictionary variant spelling matches.
KEY_KIND_VARIANT: Final = "variant"
#: Search-key kind for morphology lemma/stem matches.
KEY_KIND_STEM: Final = "stem"
#: Search-key kind for inflected morphology form matches.
KEY_KIND_FORM: Final = "form"

#: Highest-priority rank tier for exact dictionary lemma or variant hits.
RANK_TIER_EXACT_ENTRY: Final = 1
#: Rank tier for morphology lemma or stem hits joined to a dictionary entry.
RANK_TIER_MORPH_LEMMA_STEM: Final = 2
#: Rank tier for morphology form hits joined to a dictionary entry.
RANK_TIER_MORPH_FORM: Final = 3
#: Rank tier for morphology-only hits with no dictionary entry join.
RANK_TIER_ORPHAN: Final = 4
