"""Morphology paradigm assigners."""

from .adj import set_adj_paradigm
from .noun import set_noun_paradigm
from .verb import set_verb_paradigm

__all__ = ["set_adj_paradigm", "set_noun_paradigm", "set_verb_paradigm"]
