# Morphology Generation Package Import-Cycle Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the 8 import cycles graphify reports in
`wyrdcraeft/services/morphology/generation/` by removing the dead,
unused package-level re-export of `MorphologyGenerationFacade` from
`generation/__init__.py`.

**Architecture:** This is candidate #2 from the 2026-08-01 architecture
review (`docs/adr/0008-architecture-review-2026-08-01.md`). Root-cause
investigation (this session) found the review's original guess — "move
`facade.py` to import submodules directly instead of routing through
`__init__.py`" — was already true: `facade.py` already imports
`.adj_forms`, `.adv_forms`, `.common`, `.form_rows`, `.noun_forms`,
`.num_forms` directly. The actual cycle root is
`generation/__init__.py:3` — `from .facade import MorphologyGenerationFacade`
— which pulls facade.py (and everything it imports) into module scope every
time *any* submodule inside the package does `from . import <sibling>`
(a pattern used by `form_rows.py`, `common.py`, `strong_principal_flow.py`,
and `weak_principal_flow.py` to reach `sound_dispatch_flow`,
`strong_derivation_flow`, and `weak_derivation_flow`/`weak_principal_flow`).
That eager re-export is unused: a full-repo grep found no caller anywhere
(`wyrdcraeft/`, `tests/`, `scripts/`, `bin/`) importing
`MorphologyGenerationFacade` via the package (`from
wyrdcraeft.services.morphology.generation import MorphologyGenerationFacade`).
Every real caller (`build_runner.py`, `reference_snapshots.py`, all
morphology tests) already imports from `.dispatch` or `.facade` directly.
Deleting the re-export is therefore a zero-behavior-change fix: no
caller's import statement changes.

Not in scope: `common.py`'s deferred in-function imports of `.adj_forms` /
`.adv_forms` / `.num_forms` / `.noun_forms` / `.verb_engine` (lines
~1941-1998) are a **separate, genuine** cycle (`common.py` <-> `verb_engine.py`
import each other) unrelated to the 8 cycles graphify flagged, and are left
untouched by this plan.

**Tech Stack:** Python 3, pytest, ruff, mypy, graphify (static import-cycle
detection already installed in this repo at `graphify-out/`).

## Global Constraints

- Post-implementation quality gate (from `AGENTS.md`, Python files only):
  `ruff` on touched files, `.venv/bin/mypy` on touched files, `make
  napoleon-gate` — fix all reported problems before finishing.
- No monkey-patching, runtime patching, or indirection to dodge doc-gate or
  cycle noise — fix the root cause in the correct source file (`AGENTS.md`
  Implementation Priority).
- After code changes, run `graphify update .` (AST-only, no API cost) to
  keep the graph current, then re-check `graphify-out/GRAPH_REPORT.md`'s
  Import Cycles section.
- TDD: write the failing test before the fix, per
  `superpowers:test-driven-development`.

---

## File Structure

- **Modify:** `wyrdcraeft/services/morphology/generation/__init__.py` —
  drop the eager `MorphologyGenerationFacade` re-export; leave as a
  docstring-only package marker.
- **Create:** `tests/morphology/test_generation_package_imports.py` — locks
  in that the package no longer re-exports the facade, and that direct
  imports of the facade (the only way any real caller uses it) keep working.

No other files change. `facade.py`, `dispatch.py`, and every submodule under
`generation/` are untouched — their imports of each other are unaffected by
this fix.

---

### Task 1: Remove the dead facade re-export from `generation/__init__.py`

**Files:**
- Create: `tests/morphology/test_generation_package_imports.py`
- Modify: `wyrdcraeft/services/morphology/generation/__init__.py` (currently
  5 lines, full current contents below)

Current full contents of `wyrdcraeft/services/morphology/generation/__init__.py`:

```python
"""Morphology generation package."""

from .facade import MorphologyGenerationFacade

__all__ = ["MorphologyGenerationFacade"]
```

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing new. `wyrdcraeft.services.morphology.generation.facade.MorphologyGenerationFacade`
  (the class itself, in `facade.py`) is unchanged and remains importable at
  its current dotted path — only the package-level re-export is removed.

- [ ] **Step 1: Write the failing test**

Create `tests/morphology/test_generation_package_imports.py`:

```python
"""Regression test for the generation-package import-cycle fix.

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
    """dispatch.py is the actual production entrypoint into the facade."""
    from wyrdcraeft.services.morphology.generation.dispatch import (
        generate_vbforms,
    )

    assert callable(generate_vbforms)
```

- [ ] **Step 2: Run test to verify the first assertion fails**

Run: `pytest tests/morphology/test_generation_package_imports.py -v`

Expected: `test_generation_package_does_not_reexport_facade` **FAILS**
(`hasattr` is currently `True`, because `__init__.py` still does `from
.facade import MorphologyGenerationFacade`). The other two tests should
already PASS (they describe today's working direct-import paths, which the
fix must not break).

- [ ] **Step 3: Remove the eager re-export**

Replace the full contents of
`wyrdcraeft/services/morphology/generation/__init__.py` with:

```python
"""Morphology generation package."""
```

(Delete the `from .facade import MorphologyGenerationFacade` line and the
`__all__` line entirely — nothing in the repo consumes them, per the grep
audit in this plan's Architecture section.)

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `pytest tests/morphology/test_generation_package_imports.py -v`

Expected: all 3 tests PASS.

- [ ] **Step 5: Run the full morphology and lexicon test suites for regressions**

Run: `pytest tests/morphology/ tests/lexicon/ -v`

Expected: PASS, same as before this change (this step exists to catch any
test that unexpectedly relied on the package-level re-export via `dir()`,
wildcard import, or similar introspection that a plain grep would miss).

- [ ] **Step 6: Run the post-implementation quality gate**

Run, in order, fixing anything reported before moving on:

```bash
ruff check wyrdcraeft/services/morphology/generation/__init__.py tests/morphology/test_generation_package_imports.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/__init__.py
make napoleon-gate
```

Expected: no new violations from any of the three (the `__init__.py`
change only removes lines and the file has no class/function docstring
obligations left to satisfy).

- [ ] **Step 7: Refresh the graph and confirm the cycles are gone**

Run: `graphify update .`

Then inspect `graphify-out/GRAPH_REPORT.md`'s `## Import Cycles` section.

Expected: none of the 8 previously-listed cycles rooted at
`wyrdcraeft/services/morphology/generation/__init__.py -> ... -> facade.py
-> ...` remain. (The unrelated `common.py <-> verb_engine.py` cycle, if
graphify was tracking it separately, is out of scope for this task and may
still appear — that's expected and not a regression.)

- [ ] **Step 8: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/__init__.py tests/morphology/test_generation_package_imports.py
git commit -m "fix: drop dead facade re-export from generation/__init__.py, breaking import cycle"
```
