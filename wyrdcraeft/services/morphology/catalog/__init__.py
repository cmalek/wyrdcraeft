"""Wright morphology reference catalog services."""

from wyrdcraeft.services.morphology.catalog.loader import (
    LoadResult,
    MorphologyCatalogLoader,
)
from wyrdcraeft.services.morphology.catalog.pos import (
    catalog_pos_from_bt_pos,
    catalog_pos_from_wordclass,
)

__all__ = [
    "LoadResult",
    "MorphologyCatalogLoader",
    "catalog_pos_from_bt_pos",
    "catalog_pos_from_wordclass",
]
