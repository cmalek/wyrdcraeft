"""Bosworth-Toller dictionary parsing and indexing services."""

from wyrdcraeft.models.dictionary import BTParseWarning

from .attestation_stripper import BTAttestationStripper
from .browse_query import BrowseSearchHit, DictionaryBrowseQueryService
from .bt_spelling import BTSpellingNormalizer
from .build_pipeline import (
    DictionaryBuildPipeline,
    DictionaryBuildReport,
    MorphBuildOptions,
)
from .editorial_merger import BTEditorialMerger, BTEditRecord
from .forms_entry_relinker import FormsEntryRelinker
from .line_parser import BTLineParser, ParsedBTLine
from .line_splitter import BTLineSplitter, BTSplitLine
from .parse_warnings import append_parse_warnings, write_parse_warnings
from .pipeline import BTIndexPipeline, IndexReport
from .pos_gender import BTPosGenderExtractor, PosGenderResult
from .query import BTQueryService
from .sense_segmenter import BTSenseSegmenter
from .sinks import BTSqliteSink
from .target_resolver import BTTargetResolver

__all__ = [
    "BTAttestationStripper",
    "BTEditRecord",
    "BTEditorialMerger",
    "BTIndexPipeline",
    "BTLineParser",
    "BTLineSplitter",
    "BTParseWarning",
    "BTPosGenderExtractor",
    "BTQueryService",
    "BTSenseSegmenter",
    "BTSpellingNormalizer",
    "BTSplitLine",
    "BTSqliteSink",
    "BTTargetResolver",
    "BrowseSearchHit",
    "DictionaryBrowseQueryService",
    "DictionaryBuildPipeline",
    "DictionaryBuildReport",
    "FormsEntryRelinker",
    "IndexReport",
    "MorphBuildOptions",
    "ParsedBTLine",
    "PosGenderResult",
    "append_parse_warnings",
    "write_parse_warnings",
]
