"""ADR 0011: verb engines live in per-class modules; ``common.py`` is gone."""

from __future__ import annotations

import importlib

import pytest


def test_verb_form_generator_imports_from_verb_forms() -> None:
    from wyrdcraeft.services.morphology.generation.verb_forms import VerbFormGenerator

    assert VerbFormGenerator.__name__ == "VerbFormGenerator"


def test_strong_verb_generator_imports_from_strong_verb_forms() -> None:
    from wyrdcraeft.services.morphology.generation.strong_verb_forms import (
        StrongVerbGenerator,
    )

    assert StrongVerbGenerator.__name__ == "StrongVerbGenerator"


def test_weak_verb_generator_imports_from_weak_verb_forms() -> None:
    from wyrdcraeft.services.morphology.generation.weak_verb_forms import (
        WeakVerbGenerator,
    )

    assert WeakVerbGenerator.__name__ == "WeakVerbGenerator"


def test_generation_common_module_is_removed() -> None:
    with pytest.raises(ModuleNotFoundError) as excinfo:
        importlib.import_module("wyrdcraeft.services.morphology.generation.common")

    assert excinfo.value.name == "wyrdcraeft.services.morphology.generation.common"
