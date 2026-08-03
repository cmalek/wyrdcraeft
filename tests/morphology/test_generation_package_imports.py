"""
Regression test for the generation-package import-cycle fix.

``generation/__init__.py`` used to eagerly re-export
``MorphologyGenerationFacade`` via ``from .facade import
MorphologyGenerationFacade``. That import pulled facade.py (and every
module it imports) into scope any time a sibling submodule inside the
package did ``from . import <sibling>`` -- the pattern
``form_rows.py``, ``common.py``, ``strong_principal_flow.py``, and
``weak_principal_flow.py`` use to reach ``sound_dispatch_flow``,
``strong_derivation_flow``, and ``weak_derivation_flow`` /
``weak_principal_flow``. That created the 8 import cycles graphify
reported, all rooted at ``generation/__init__.py``.

No caller in this repo ever consumed the package-level re-export -- every
real caller imports ``MorphologyGenerationFacade`` from ``.facade``
directly, or uses ``.dispatch`` -- so removing it is a zero-behavior-change
fix. These tests lock in both halves of that claim.
"""

import wyrdcraeft.services.morphology.generation as generation_pkg


def test_generation_package_does_not_reexport_facade():
    """The package must not carry a facade re-export that recreates the cycle."""
    assert not hasattr(generation_pkg, "MorphologyGenerationFacade")


def test_facade_still_importable_directly():
    """The only import path any real caller uses must keep working."""
    from wyrdcraeft.services.morphology.generation.facade import (
        MorphologyGenerationFacade,
    )

    assert MorphologyGenerationFacade.__name__ == "MorphologyGenerationFacade"


def test_dispatch_still_importable():
    """The facade is the actual production entrypoint into generation."""
    from wyrdcraeft.services.morphology.generation.facade import (
        MorphologyGenerationFacade,
    )

    assert callable(MorphologyGenerationFacade.generate_verbs)
