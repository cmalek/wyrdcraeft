"""
Compatibility layer for morphology paradigm assignment.

The implementation was mechanically extracted into dedicated modules:

- :mod:`wyrdcraeft.services.morphology.assigners.verb`
- :mod:`wyrdcraeft.services.morphology.assigners.adj`
- :mod:`wyrdcraeft.services.morphology.assigners.noun`

This module keeps the historical import surface stable.
"""

from __future__ import annotations

from .assigners.adj import set_adj_paradigm
from .assigners.noun import (
    R_STEM_PARADIGM_BY_STEM,
    _get_r_stem_paradigm,
    _wright_has_token,
    set_noun_paradigm,
)
from .assigners.verb import (
    _assign_verb_by_advanced_diacritics,
    _assign_verb_by_advanced_stem,
    _assign_verb_by_diacritics,
    _assign_verb_by_example,
    _assign_verb_by_stem,
    _assign_verb_by_wright,
    _assign_verb_fallback,
    _assign_verb_heuristics,
    set_verb_paradigm,
)

__all__ = [
    "R_STEM_PARADIGM_BY_STEM",
    "_assign_verb_by_advanced_diacritics",
    "_assign_verb_by_advanced_stem",
    "_assign_verb_by_diacritics",
    "_assign_verb_by_example",
    "_assign_verb_by_stem",
    "_assign_verb_by_wright",
    "_assign_verb_fallback",
    "_assign_verb_heuristics",
    "_get_r_stem_paradigm",
    "_wright_has_token",
    "set_adj_paradigm",
    "set_noun_paradigm",
    "set_verb_paradigm",
]
