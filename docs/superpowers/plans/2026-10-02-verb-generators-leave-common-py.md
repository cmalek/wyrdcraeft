# Verb generators leave `common.py` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ADR 0011: split `VerbFormGenerator`, `StrongVerbGenerator`, and `WeakVerbGenerator` out of `generation/common.py` into one class per file, then delete `common.py` with no stub.

**Architecture:** Same three engines as today. `facade.generate_verbs()` still constructs `VerbFormGenerator`. That orchestrator still constructs Strong/Weak in `__init__` from `word_pool` / `run_state` / `output_file`. Those names are engines, not Wright conjugation classes: Strong is ablaut (`type == "s"`); Weak emits Weak I/II derivation plus item-shape for Weak III, preterite-present (`pp`), and anomalous (`a`). Do not add a generator per linguistic group.

**Tech Stack:** Python 3.11–3.13, pytest, uv, ruff, mypy, `make napoleon-gate`, graphify.

**Spec:** [docs/adr/0011-verb-generators-leave-common-py.md](../../adr/0011-verb-generators-leave-common-py.md). Perl is not an oracle: [ADR 0012](../../adr/0012-morphology-generation-not-perl-parity-bound.md).

## Global Constraints

- One landing: after the implementation commit, `generation/common.py` must not exist and must not re-export anything.
- Do not inject Strong/Weak through `MorphologyGenerationFacade`.
- Do not copy `common.py`'s file-level `# ruff: noqa: I001,PLR0913,ARG002,D417,RUF100,PLC0415`. Keep per-method `# noqa:` that already exist. That file-level line currently covers ~80 methods; only ~32 defs have their own `# noqa:`. After the split, ruff `select = ["ALL"]` will flag many moved methods (`PLR0913`, `ARG002`, `D417`, leftover `RUF100`, `PLC0415`). **Extend the `# noqa:` on those function defs** (same codes the file used to swallow). Do **not** add a module-top `# ruff: noqa:`. `I001` may be `--fix`ed (import sort).
- Move `_emit_weak_derived_from_inf_by_class2` **verbatim**, including the unreachable `elif class2 == "2"` `-ig-`/`-ige-` loop. Do **not** change `elif` to `if` (Trello https://trello.com/c/s0IpN3s9).
- Drop unused `VerbFormGenerator.S2_CHANGES` and `S3_CHANGES`.
- Drop `VerbFormGenerator._add_participle_to_adjectives` (leftover forward). Strong and Weak keep their own `_add_participle_to_adjectives` methods.
- Bind `form_rows` / `participles` helpers as **module-level aliases** on each generator file that uses them, so tests patch that module. Import `nz` / `perl_numify` from `scalar_utils`. Callers of `print_one_form` import `form_rows`.
- `verb_forms.py` imports strong/weak modules; strong and weak must not import `verb_forms.py`.
- Keep generation order: manual, verb, adjective, adverb, numeral, noun.
- Do not rewrite historical `docs/superpowers/` plans or ADR 0008/0009 text that still says `common.py`.
- After Python edits: `ruff` and `.venv/bin/mypy` on touched files, `make napoleon-gate`, `graphify update .`.
- Workspace: models in `wyrdcraeft.models`, services in `wyrdcraeft.services`, CLI in `wyrdcraeft.cli` only.
- If this branch lacks the `AGENTS.md` bullet that the orchestrator may construct private collaborators in `__init__`, copy that bullet; do not revert it.

## File map

| File | Role after this plan |
|------|----------------------|
| `wyrdcraeft/services/morphology/generation/strong_verb_forms.py` | `StrongVerbGenerator` only. |
| `wyrdcraeft/services/morphology/generation/weak_verb_forms.py` | `WeakStemParts` alias + `WeakVerbGenerator`. |
| `wyrdcraeft/services/morphology/generation/verb_forms.py` | `VerbFormGenerator` orchestrator; constructs Strong/Weak in `__init__`. |
| `wyrdcraeft/services/morphology/generation/common.py` | **Deleted.** |
| `wyrdcraeft/services/morphology/generation/facade.py` | `from .verb_forms import VerbFormGenerator`. `generate_verbs()` body unchanged. |
| `tests/morphology/test_generation_branches.py` | Import generators from the three new modules; patch `weak_verb_forms` not `common`. |
| `tests/morphology/test_query_service.py` | `print_one_form` from `form_rows`. |
| `tests/lexicon/source_db.py` | `print_one_form` from `form_rows`. |
| `tests/morphology/test_verb_generator_modules.py` | Import-location contract for ADR 0011. |

Line numbers below are for `common.py` at plan time (`StrongVerbGenerator` L107–L1066, `WeakStemParts` L1068–L1069, `WeakVerbGenerator` L1072–L2856, `VerbFormGenerator` L2858–L3344). Re-confirm with `rg -n "^class "` before slicing if the file drifted.

---

### Task 1: Import-location contract tests

**Files:**
- Create: `tests/morphology/test_verb_generator_modules.py`

**Interfaces:**
- Consumes: nothing from later tasks.
- Produces: tests that require `verb_forms.VerbFormGenerator`, `strong_verb_forms.StrongVerbGenerator`, `weak_verb_forms.WeakVerbGenerator`, and that `generation.common` is gone.

- [ ] **Step 1: Write the failing tests**

Create `tests/morphology/test_verb_generator_modules.py`:

```python
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
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("wyrdcraeft.services.morphology.generation.common")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/morphology/test_verb_generator_modules.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `verb_forms` / `strong_verb_forms` / `weak_verb_forms`. At this step `common.py` still exists, so `test_generation_common_module_is_removed` fails with `Failed: DID NOT RAISE ModuleNotFoundError`.

Do **not** commit this file yet. A red pytest in an isolated commit will fail if hooks run tests. Leave `test_verb_generator_modules.py` unstaged until Task 2 Step 8 (one green landing with the split).

---

### Task 2: Split modules, retarget callers, delete `common.py`

**Files:**
- Create: `wyrdcraeft/services/morphology/generation/strong_verb_forms.py`
- Create: `wyrdcraeft/services/morphology/generation/weak_verb_forms.py`
- Create: `wyrdcraeft/services/morphology/generation/verb_forms.py`
- Delete: `wyrdcraeft/services/morphology/generation/common.py`
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (import only)
- Modify: `tests/morphology/test_generation_branches.py`
- Modify: `tests/morphology/test_query_service.py`
- Modify: `tests/lexicon/source_db.py`

**Interfaces:**
- Consumes: classes currently in `common.py` (unchanged public constructors).
- Produces:
  - `StrongVerbGenerator(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput)`
  - `WeakVerbGenerator(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput)`
  - `VerbFormGenerator(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress: MorphologyGenerateProgressCoordinator | None = None)` with `self._strong_generator` / `self._weak_generator` built in `__init__`.
  - `VerbFormGenerator.generate() -> None` unchanged (skip `pspart+papart != 0`; route `vp.type == "s"` to Strong, else Weak).

- [ ] **Step 1: Confirm slice lines**

Run:

```bash
rg -n "^class (StrongVerbGenerator|WeakVerbGenerator|VerbFormGenerator)|^WeakStemParts" \
  wyrdcraeft/services/morphology/generation/common.py
```

Expected (or adjacent if the file drifted; use the printed lines):

```
107:class StrongVerbGenerator:
1068:WeakStemParts = tuple[str, str, str, str]
1072:class WeakVerbGenerator:
2858:class VerbFormGenerator:
```

- [ ] **Step 2: Create `strong_verb_forms.py`**

Write this header, then paste `class StrongVerbGenerator` through its last method (plan-time L107–L1066) **unchanged**, including existing per-method `# noqa:`:

```python
"""Strong-verb ablaut generation engine."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    _StrongInfDerivationContext,
    _StrongPrincipalPartContext,
    Word,
)
from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_rows import emit_form_for_context as _emit_form_for_context_row
from .form_rows import emit_imsg_for_context as _emit_imsg_for_context_row
from .form_rows import (
    emit_sound_changed_form_for_context as _emit_sound_changed_form_for_context_row,
)
from .form_rows import generate_and_print_form as _generate_and_print_form
from .form_rows import generate_and_print_manual as _generate_and_print_manual
from .form_rows import (
    generate_and_print_form_with_sound_changes
    as _generate_and_print_form_with_sound_changes_row,
)
from .participles import (
    add_participle_to_adjectives as _add_participle_to_adjectives_session,
)
from .probability import probability_or_zero, probability_plus
from .scalar_utils import nz, perl_numify
from .shared import FormOutput
from .sound_changes import derive_papt_sound_changed_forms
```

Do **not** add local `def nz` / `def perl_numify` / `def print_one_form` wrappers. After paste, run ruff (Step 6) and **delete unused imports** rather than adding a file-level noqa. Keep any import the class body still references.

If a name is imported in this header but unused in Strong, drop it in the ruff cleanup (Weak and Verb will have their own subsets). A safe first paste is “same import block as `common.py` minus the three wrapper functions,” then ruff F401.

- [ ] **Step 3: Create `weak_verb_forms.py`**

Header:

```python
"""Weak-verb generation engine (derived Weak I/II plus item-shape tables)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    _WeakInfDerivationContext,
    _WeakPainsg1DerivationContext,
    _WeakPrincipalPartContext,
    _WeakPsinsg2DerivationContext,
    Word,
)
from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_rows import emit_form_for_context as _emit_form_for_context_row
from .form_rows import emit_imsg_for_context as _emit_imsg_for_context_row
from .form_rows import (
    emit_sound_changed_form_for_context as _emit_sound_changed_form_for_context_row,
)
from .form_rows import generate_and_print_form as _generate_and_print_form
from .form_rows import generate_and_print_manual as _generate_and_print_manual
from .form_rows import (
    generate_and_print_form_with_sound_changes
    as _generate_and_print_form_with_sound_changes_row,
)
from .participles import (
    add_participle_to_adjectives as _add_participle_to_adjectives_session,
)
from .probability import probability_or_zero, probability_plus
from .scalar_utils import nz, perl_numify
from .shared import FormOutput
from .sound_changes import derive_papt_sound_changed_forms
```

Then paste, in order:

1. `WeakStemParts = tuple[str, str, str, str]` and its Napoleon `#:` comment (plan-time L1068–L1069).
2. `class WeakVerbGenerator` through `generate_verb_parts` (plan-time L1072–L2856).

Do not edit `_emit_weak_derived_from_inf_by_class2`. After paste it must still contain:

```python
        if class2 in {"", "1", "2"}:
            ...
        # Perl: if ($word->{class2} == 2)
        elif class2 == "2":
            for iending in ["ig", "ige", ""]:
```

- [ ] **Step 4: Create `verb_forms.py`**

Header:

```python
"""Verb generation orchestrator: walk words/paradigms and route to Strong or Weak."""

from __future__ import annotations

import re
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
    _ParadigmVariantDispatchContext,
    _VariantPartDispatchContext,
)
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologyStage,
)
from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .scalar_utils import nz
from .shared import FormOutput
from .strong_verb_forms import StrongVerbGenerator
from .weak_verb_forms import WeakVerbGenerator
```

Then paste `class VerbFormGenerator` (plan-time L2858–L3344) with these **required edits** only:

1. Delete the class attributes `S2_CHANGES` and `S3_CHANGES` (plan-time L2869–L2888) and drop `Final` from the import if nothing else uses it.
2. Delete `VerbFormGenerator._add_participle_to_adjectives` (plan-time L3314–L3344) and any now-unused `participles` import (this file should not import `participles`).
3. Keep `__init__` constructing collaborators:

```python
        self._strong_generator = StrongVerbGenerator(word_pool, run_state, output_file)
        self._weak_generator = WeakVerbGenerator(word_pool, run_state, output_file)
```

4. Keep `_process_part` routing:

```python
        if vp.type == "s":
            self._strong_generator.generate_verb_parts(...)
            return
        self._weak_generator.generate_verb_parts(...)
```

Do not add Strong/Weak constructor parameters to the facade or to `VerbFormGenerator.__init__`.

Do not import `verb_forms` from `strong_verb_forms.py` or `weak_verb_forms.py`.

- [ ] **Step 5: Retarget callers and delete `common.py`**

In `facade.py` replace:

```python
from .common import VerbFormGenerator
```

with:

```python
from .verb_forms import VerbFormGenerator
```

Leave `generate_verbs()` as:

```python
        VerbFormGenerator(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        ).generate()
```

In `tests/morphology/test_generation_branches.py` replace the `common` imports with:

```python
from wyrdcraeft.services.morphology.generation import weak_verb_forms as generation_weak
from wyrdcraeft.services.morphology.generation.strong_verb_forms import (
    StrongVerbGenerator,
)
from wyrdcraeft.services.morphology.generation.verb_forms import VerbFormGenerator
from wyrdcraeft.services.morphology.generation.weak_verb_forms import WeakVerbGenerator
```

Replace the only `generation_common` monkeypatch (around the `_generate_and_print_form_with_sound_changes_row` setattr) with:

```python
    monkeypatch.setattr(
        generation_weak,
        "_generate_and_print_form_with_sound_changes_row",
        _emit_sound,
    )
```

Change `test_add_participle_to_adjectives_respects_prefix_numeric_match` to construct `StrongVerbGenerator` (or `WeakVerbGenerator`) instead of `VerbFormGenerator`, because the orchestrator no longer forwards `_add_participle_to_adjectives`:

```python
def test_add_participle_to_adjectives_respects_prefix_numeric_match() -> None:
    session = GeneratorSession()
    output = io.StringIO()
    generator = StrongVerbGenerator(session.word_pool, session.run_state, output)
    word = _make_word(prefix="1")

    generator._add_participle_to_adjectives(
        word,
        "ge",
        "ge-l-a-m",
        is_past=False,
    )

    assert session.adjectives == []
```

In `tests/morphology/test_query_service.py` and `tests/lexicon/source_db.py` replace:

```python
from wyrdcraeft.services.morphology.generation.common import print_one_form
```

with:

```python
from wyrdcraeft.services.morphology.generation.form_rows import print_one_form
```

Delete `wyrdcraeft/services/morphology/generation/common.py`.

Confirm no remaining product/test imports:

```bash
rg -n "generation\\.common|generation import common|from \\.common import" \
  --glob "*.py" wyrdcraeft tests
```

Expected: no matches (historical markdown/rst may still say `common.py`; leave those).

- [ ] **Step 6: Ruff unused imports on the three new modules**

Run:

```bash
.venv/bin/ruff check --fix \
  wyrdcraeft/services/morphology/generation/strong_verb_forms.py \
  wyrdcraeft/services/morphology/generation/weak_verb_forms.py \
  wyrdcraeft/services/morphology/generation/verb_forms.py \
  wyrdcraeft/services/morphology/generation/facade.py \
  tests/morphology/test_generation_branches.py \
  tests/morphology/test_query_service.py \
  tests/lexicon/source_db.py \
  tests/morphology/test_verb_generator_modules.py
```

Expected: unused-import noise reduced. Do **not** add a file-level ruff noqa. Remaining `PLR0913` / `ARG002` / `D417` / `PLC0415` / unused `RUF100` on moved methods are Task 3: extend each def’s `# noqa:` (see Global Constraints). `I001` is allowed to be auto-fixed here.

`--fix` must **not** drop aliases tests patch. Immediately after ruff, confirm this name is still bound in `weak_verb_forms.py`:

```bash
rg -n "_generate_and_print_form_with_sound_changes_row" \
  wyrdcraeft/services/morphology/generation/weak_verb_forms.py
```

Expected: the `form_rows` import alias (and any call sites). If ruff removed it, restore:

```python
from .form_rows import (
    generate_and_print_form_with_sound_changes
    as _generate_and_print_form_with_sound_changes_row,
)
```

If ruff removes any other alias a class method still calls (`_emit_form_for_context_row`, `_add_participle_to_adjectives_session`, etc.), restore that import too. Each generator file that calls those names **must** keep the alias at module level (ADR 0011 patch surface).

- [ ] **Step 7: Run contract + generation branch tests**

Run:

```bash
.venv/bin/pytest \
  tests/morphology/test_verb_generator_modules.py \
  tests/morphology/test_generation_branches.py -v
```

Expected: all pass (`test_generation_branches.py` plus the four module-location tests).

- [ ] **Step 8: Commit the split**

```bash
git add \
  wyrdcraeft/services/morphology/generation/strong_verb_forms.py \
  wyrdcraeft/services/morphology/generation/weak_verb_forms.py \
  wyrdcraeft/services/morphology/generation/verb_forms.py \
  wyrdcraeft/services/morphology/generation/facade.py \
  tests/morphology/test_generation_branches.py \
  tests/morphology/test_query_service.py \
  tests/lexicon/source_db.py \
  tests/morphology/test_verb_generator_modules.py
git add -u wyrdcraeft/services/morphology/generation/common.py
git commit -m "$(cat <<'EOF'
refactor: move verb generators out of common.py

EOF
)"
```

---

### Task 3: Quality gate and graph refresh

**Files:**
- Modify: only if ruff/mypy/napoleon report issues in files from Task 2
- Touch: `graphify-out/` via `graphify update .` (expected dirty graph files)

**Interfaces:**
- Consumes: Task 2 modules.
- Produces: green ruff, mypy, napoleon-gate, morphology tests; updated graphify AST.

- [ ] **Step 1: Ruff, mypy, napoleon-gate**

Run:

```bash
.venv/bin/ruff check \
  wyrdcraeft/services/morphology/generation/strong_verb_forms.py \
  wyrdcraeft/services/morphology/generation/weak_verb_forms.py \
  wyrdcraeft/services/morphology/generation/verb_forms.py \
  wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy \
  wyrdcraeft/services/morphology/generation/strong_verb_forms.py \
  wyrdcraeft/services/morphology/generation/weak_verb_forms.py \
  wyrdcraeft/services/morphology/generation/verb_forms.py \
  wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

Expected: ruff clean; mypy exit 0; napoleon-gate no new violations vs baseline. For ruff on the new modules: **per-def `# noqa:` only** (Global Constraints). Do not reintroduce `common.py`’s module-top `# ruff: noqa:`. Fix every remaining reported problem in the touched generator files before continuing.

- [ ] **Step 2: Broader tests that imported `common.print_one_form`**

Run:

```bash
.venv/bin/pytest tests/morphology/test_query_service.py tests/lexicon -q
```

Expected: pass.

- [ ] **Step 3: `graphify update .`**

Run:

```bash
graphify update .
```

Expected: completes without rewriting product Python.

- [ ] **Step 4: Commit quality-gate fixes if any**

If Step 1–2 required code fixes:

```bash
git add -u
git commit -m "$(cat <<'EOF'
fix: satisfy ruff/mypy/napoleon after verb generator split

EOF
)"
```

If graphify-out is the only diff, leave it uncommitted unless project hooks already staged it.

---

## Out of scope

- Wright class-II `-ig-`/`-ige-` enablement (`elif` → `if`) — Trello https://trello.com/c/s0IpN3s9
- New Python classes for preterite-present or anomalous verbs
- Facade injection of Strong/Weak
- Renaming `WeakVerbGenerator` because `pp`/`a` ride it
- Snapshot / Perl-parity fights (ADR 0012)
