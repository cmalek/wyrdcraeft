"""Deprecated compatibility wrappers for migrated morphology generation code."""

from __future__ import annotations

from ..generation.common import (  # noqa: F401
    VerbFormGenerator,
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
    perl_numify,
    print_one_form,
)

__all__ = [
    "VerbFormGenerator",
    "generate_adjforms",
    "generate_advforms",
    "generate_nounforms",
    "generate_numforms",
    "generate_vbforms",
    "output_manual_forms",
    "perl_numify",
    "print_one_form",
]
