"""Wright morphology reference catalog services."""

from wyrdcraeft.services.morphology.catalog.assigner import (
    AssignmentResult,
    LemmaMorphClassAssigner,
)
from wyrdcraeft.services.morphology.catalog.loader import (
    LoadResult,
    MorphologyCatalogLoader,
)
from wyrdcraeft.services.morphology.catalog.paradigm_map import ParadigmClassMapper
from wyrdcraeft.services.morphology.catalog.pos import (
    catalog_pos_from_bt_pos,
    catalog_pos_from_wordclass,
)
from wyrdcraeft.services.morphology.catalog.query import (
    MorphClassView,
    MorphologyCatalogQueryService,
    MorphSourceCitation,
)

__all__ = [
    "AssignmentResult",
    "LemmaMorphClassAssigner",
    "LoadResult",
    "MorphClassView",
    "MorphologyCatalogLoader",
    "MorphologyCatalogQueryService",
    "MorphSourceCitation",
    "ParadigmClassMapper",
    "catalog_pos_from_bt_pos",
    "catalog_pos_from_wordclass",
]
