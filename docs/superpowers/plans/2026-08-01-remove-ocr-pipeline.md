# Remove OCR Pipeline (ADR 0007) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the OCR pipeline (code, tests, deps, docs) from wyrdcraeft per ADR 0007, since OCR work now lives in the sibling `bochord` repo, leaving wyrdcraeft focused on Old English grammar/dictionary/morphology/diacritics.

**Architecture:** Deletion-only work, ordered so nothing is left in a broken intermediate state: CLI registration is severed before the CLI module is deleted; the pytest marker/fixtures are removed alongside the last test that uses them; `pyproject.toml` deps/entry-point are dropped after no code imports them; `settings.py`'s OCR field block is deleted only after confirming (done below) nothing outside the deleted code reads it. Historical ADRs 0004-0006 are annotated, not deleted — they document real prior design decisions.

**Tech Stack:** Python (click CLI, pydantic-settings, pytest), uv/pyproject dependency management, Markdown docs.

## Global Constraints

- Do not delete or modify `data/bosworth_toller/oe_bosworthtoller.txt.bz2` or `data/bosworth_toller/oe_bt.txt.bz2` — plain-text BT dictionary source, not OCR output, still consumed by dictionary/morphology code.
- `data/bt_cases/` and `data/ocr/` are already removed from the working tree — nothing to do there.
- ADRs 0004, 0005, 0006 (`docs/adr/000{4,5,6}-*.md`) must be annotated as superseded/relocated, never deleted.
- Every deletion task must leave `uv run pytest` (or the specific test subset named in the task) passing before commit.
- This plan is not done until Task 9's full, unfiltered `uv run pytest` (no `-m` exclusions) passes with zero failures — that is the final completion gate, not any interim subset run in earlier tasks.
- Confirmed via repo grep (see Task 8): no code outside `wyrdcraeft/cli/ocr.py` and `wyrdcraeft/services/ocr/` reads any `settings.ocr_*` field, so the entire block is safe to delete in one task.

---

### Task 1: Sever CLI registration of the OCR command group

**Files:**
- Modify: `wyrdcraeft/cli/cli.py:26` (remove `"ocr"` from `DATABASE_GATE_SKIP_COMMANDS`)
- Modify: `wyrdcraeft/cli/cli.py:232` (remove `from .ocr import ocr_group`)
- Modify: `wyrdcraeft/cli/cli.py:241` (remove `cli.add_command(ocr_group)`)
- Test: `tests/test_cli_commands.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `cli` (the root click group) no longer exposes an `ocr` subcommand. Later tasks (2, 3) rely on this — `wyrdcraeft/cli/ocr.py` and `wyrdcraeft/services/ocr/` can be deleted next only because nothing in `cli.py` imports them anymore.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_cli_commands.py`:

```python
def test_ocr_command_group_removed():
    from click.testing import CliRunner

    from wyrdcraeft.cli.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["ocr", "--help"])
    assert result.exit_code != 0
    assert "ocr" not in cli.commands
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_commands.py::test_ocr_command_group_removed -v`
Expected: FAIL (`"ocr" in cli.commands` is currently `True`)

- [ ] **Step 3: Remove the three registration points**

In `wyrdcraeft/cli/cli.py`:

```python
# before
DATABASE_GATE_SKIP_COMMANDS = frozenset(
    {"version", "settings", "source", "ocr", "diacritic"}
)
# after
DATABASE_GATE_SKIP_COMMANDS = frozenset(
    {"version", "settings", "source", "diacritic"}
)
```

```python
# before
from .diacritic import diacritic_group
from .diacritic_disambiguate import diacritic_disambiguate
from .dictionary import dictionary_group
from .morphology import morphology_group
from .ocr import ocr_group
from .settings import settings_group
from .source import reading_group

cli.add_command(settings_group)
cli.add_command(diacritic_group)
cli.add_command(reading_group)
cli.add_command(morphology_group)
cli.add_command(dictionary_group)
cli.add_command(ocr_group)
diacritic_group.add_command(diacritic_disambiguate)

# after
from .diacritic import diacritic_group
from .diacritic_disambiguate import diacritic_disambiguate
from .dictionary import dictionary_group
from .morphology import morphology_group
from .settings import settings_group
from .source import reading_group

cli.add_command(settings_group)
cli.add_command(diacritic_group)
cli.add_command(reading_group)
cli.add_command(morphology_group)
cli.add_command(dictionary_group)
diacritic_group.add_command(diacritic_disambiguate)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_commands.py::test_ocr_command_group_removed -v`
Expected: PASS

Note: `wyrdcraeft/cli/ocr.py` still exists on disk at this point and will fail to import cleanly once Task 2 deletes `wyrdcraeft/services/ocr/` — that's fine, Task 1 must land first so `cli.py` no longer imports it, then Task 2 deletes the file itself. Do not run the full test suite between Task 1 and Task 2; run only `tests/test_cli_commands.py` here.

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/cli/cli.py tests/test_cli_commands.py
git commit -m "refactor: remove ocr command group registration from root CLI"
```

---

### Task 2: Delete the OCR CLI module and its dedicated tests

**Files:**
- Delete: `wyrdcraeft/cli/ocr.py`
- Delete: `tests/test_cli_ocr.py`
- Delete: `tests/test_cli_ocr_bosworth_toller.py`

**Interfaces:**
- Consumes: Task 1's removal of the `ocr_group` import/registration (this task cannot land first — `cli.py` would fail to import).
- Produces: no more `wyrdcraeft.cli.ocr` module. Task 8 (settings.py cleanup) relies on this — it's the last reader of the `settings.ocr_*` block.

- [ ] **Step 1: Delete the files**

```bash
git rm wyrdcraeft/cli/ocr.py tests/test_cli_ocr.py tests/test_cli_ocr_bosworth_toller.py
```

- [ ] **Step 2: Run the full CLI test suite to verify nothing else imports the deleted module**

Run: `uv run pytest tests/test_cli_commands.py tests/test_cli_dictionary.py tests/test_cli_morphology.py -v`
Expected: PASS, no `ModuleNotFoundError` for `wyrdcraeft.cli.ocr`

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor: delete ocr CLI module and its tests"
```

---

### Task 3: Delete the OCR proxy service and its tests

**Files:**
- Delete: `wyrdcraeft/services/ocr_proxy/` (`__init__.py`, `config.py`, `server.py`, `proxy.py`, `runtime.py`)
- Delete: `tests/test_ocr_proxy.py`
- Delete: `tests/test_ocr_proxy_runtime.py`

**Interfaces:**
- Consumes: Task 2 having removed `wyrdcraeft/cli/ocr.py` (the only in-repo caller of `wyrdcraeft.services.ocr_proxy`).
- Produces: no more `wyrdcraeft.services.ocr_proxy` package. Independent of Task 4 — can run in parallel with it (no shared files).

- [ ] **Step 1: Confirm no remaining importers**

Run: `grep -rn "services.ocr_proxy\|services\.ocr_proxy" wyrdcraeft/ tests/ scripts/ --include="*.py"`
Expected: no output (or only matches inside the files about to be deleted)

- [ ] **Step 2: Delete the files**

```bash
git rm -r wyrdcraeft/services/ocr_proxy tests/test_ocr_proxy.py tests/test_ocr_proxy_runtime.py
```

- [ ] **Step 3: Run the full test suite excluding live OCR integration**

Run: `uv run pytest -m "not ocr_integration and not llm"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: delete ocr_proxy service and its tests"
```

---

### Task 4: Delete the OCR pipeline service and its tests

**Files:**
- Delete: `wyrdcraeft/services/ocr/` (`__init__.py`, `bt_tile_ocr.py`, `bt_witness_ocr.py`, `old_english_pipeline.py`, `bt_witness_prep/`)
- Delete: `tests/ocr/` (directory, incl. `test_bt_tile_ocr.py`, `test_bt_page_batch_ocr.py`, `test_bt_witness_prep_manifest.py`, `test_bt_witness_prep_pipeline.py`, `test_bt_witness_prep_quality.py`, `test_old_english_input.py`)
- Delete: `tests/test_old_english_ocr_pipeline_olmocr.py`
- Delete: `tests/test_ocr_live_integration.py`
- Delete: `tests/ocr_metrics.py`
- Delete: `tests/fixtures/ocr/` (directory)

**Interfaces:**
- Consumes: Task 2 having removed `wyrdcraeft/cli/ocr.py` (the only in-repo caller of `wyrdcraeft.services.ocr`).
- Produces: no more `wyrdcraeft.services.ocr` package, no more `tests.ocr_metrics` module. Task 5 relies on `tests/ocr_metrics.py` being gone (it deletes `scripts/ocr/benchmark_wright_live.py`, which is the only importer of `tests.ocr_metrics.compute_ocr_metrics` — confirm order doesn't matter since both are deleted, but do not delete `tests/ocr_metrics.py` before this task's own scan finds it clean). Independent of Task 3 — can run in parallel with it (no shared files).

- [ ] **Step 1: Confirm no remaining importers outside what's being deleted**

Run: `grep -rln "services\.ocr\b\|services/ocr/\|from wyrdcraeft.services.ocr" wyrdcraeft/ tests/ scripts/ --include="*.py" | grep -v "wyrdcraeft/services/ocr/\|scripts/ocr/"`
Expected: no output

- [ ] **Step 2: Delete the files**

```bash
git rm -r wyrdcraeft/services/ocr tests/ocr tests/test_old_english_ocr_pipeline_olmocr.py tests/test_ocr_live_integration.py tests/ocr_metrics.py tests/fixtures/ocr
```

- [ ] **Step 3: Run the full test suite excluding live OCR integration**

Run: `uv run pytest -m "not ocr_integration and not llm"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: delete ocr pipeline service and its tests"
```

---

### Task 5: Delete `scripts/ocr/` and its `pyproject.toml` entry point

**Files:**
- Delete: `scripts/ocr/` (`__init__.py`, `benchmark_bt_witness_prep.py`, `benchmark_wright_live.py`, `benchmark_wright_matrix.py`, `old_english_ocr_pipeline.py`, `olmocr_hf.py`)
- Modify: `pyproject.toml:86` (remove `olmocr_hf = "scripts.ocr.olmocr_hf:main"` from `[project.scripts]`)

**Interfaces:**
- Consumes: Task 3 (deletes `wyrdcraeft.services.ocr_proxy`, imported by these scripts) and Task 4 (deletes `wyrdcraeft.services.ocr`, imported by `benchmark_bt_witness_prep.py`) — must run after both.
- Produces: no more `scripts.ocr` package, no more `olmocr_hf` console entry point. Task 6 relies on this — it removes the `olmocr` dependency that `scripts/ocr/olmocr_hf.py` was the last user of.

- [ ] **Step 1: Confirm no remaining importers**

Run: `grep -rln "scripts\.ocr\|scripts/ocr" --include="*.py" --include="*.toml" .`
Expected: only `pyproject.toml:86` and files under `scripts/ocr/` itself

- [ ] **Step 2: Delete the scripts directory**

```bash
git rm -r scripts/ocr
```

- [ ] **Step 3: Remove the entry point from `pyproject.toml`**

```toml
# before
[project.scripts]
wyrdcraeft = "wyrdcraeft.main:main"
olmocr_hf = "scripts.ocr.olmocr_hf:main"

# after
[project.scripts]
wyrdcraeft = "wyrdcraeft.main:main"
```

- [ ] **Step 4: Regenerate the lockfile entry point metadata**

Run: `uv sync`
Expected: succeeds, `olmocr_hf` console script no longer installed

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "refactor: delete scripts/ocr and its console entry point"
```

---

### Task 6: Drop OCR-only dependencies and the `ocr_integration` pytest marker

**Files:**
- Modify: `pyproject.toml:42` (remove `"olmocr>=0.4.25",`)
- Modify: `pyproject.toml:45-46` (remove `"ocrmypdf>=17.3.0",` and `"ocrmypdf-appleocr>=0.3.3",`)
- Modify: `pyproject.toml:124` (remove the `ocr_integration` marker line)
- Modify: `pyproject.toml` (remove the `--run-ocr-integration` pytest CLI option, if defined in `[tool.pytest.ini_options]` or a `conftest.py` — search first, see Step 1)

**Interfaces:**
- Consumes: Tasks 4 and 5 (nothing left in the repo imports `olmocr`, `ocrmypdf`, or `ocrmypdf-appleocr`, and no test uses the `ocr_integration` marker).
- Produces: a `pyproject.toml` with zero OCR-related dependencies or pytest configuration. This is the last task with any dependency on prior OCR-deletion tasks; Tasks 7-9 are independent of each other and of this task.

- [ ] **Step 1: Find the `--run-ocr-integration` option definition**

Run: `grep -rn "run-ocr-integration\|run_ocr_integration" tests/ pyproject.toml`

If found in a `conftest.py`, note the file path — remove that `addoption`/marker-skip block in this task too (it will otherwise reference a marker that Step 3 removes, and `pytest --run-ocr-integration` would silently no-op instead of erroring, masking the fact the flag is dead).

- [ ] **Step 2: Confirm no code imports the OCR-only packages**

Run: `grep -rln "^import olmocr\|from olmocr\|^import ocrmypdf\|from ocrmypdf" --include="*.py" .`
Expected: no output

- [ ] **Step 3: Remove the dependency lines from `pyproject.toml`**

```toml
# before
  "pdfminer-six>=20260107",
  "wheel>=0.46.3",
  "olmocr>=0.4.25",
  "uvicorn>=0.30.0",
  "huggingface-hub[cli]>=0.36.2",
  "ocrmypdf>=17.3.0",
  "ocrmypdf-appleocr>=0.3.3",
  "textual>=6.2.1",

# after
  "pdfminer-six>=20260107",
  "wheel>=0.46.3",
  "uvicorn>=0.30.0",
  "huggingface-hub[cli]>=0.36.2",
  "textual>=6.2.1",
```

(Keep `uvicorn` and `huggingface-hub[cli]` — confirm in Step 4 whether anything non-OCR still uses them before assuming they're OCR-only; do not remove them speculatively.)

- [ ] **Step 4: Confirm `uvicorn` and `huggingface-hub` still have non-OCR consumers, or remove them too**

Run: `grep -rln "^import uvicorn\|from uvicorn\|huggingface_hub" --include="*.py" wyrdcraeft/ scripts/ | grep -v "wyrdcraeft/services/ocr\|scripts/ocr"`

If no output, add their removal to this same task's diff before committing. If output exists, leave them and note the non-OCR consumer file(s) in the commit message.

- [ ] **Step 5: Remove the `ocr_integration` marker**

```toml
# before
markers = [
    "llm: tests that require live LLM access (run with --run-llm)",
    "ocr_integration: live OCR integration tests requiring local model server (run with --run-ocr-integration)",
    "morphology: Morphology generator tests and reference contracts",
    "morphology_full: Optional full-dataset morphology smoke checks",

# after
markers = [
    "llm: tests that require live LLM access (run with --run-llm)",
    "morphology: Morphology generator tests and reference contracts",
    "morphology_full: Optional full-dataset morphology smoke checks",
```

- [ ] **Step 6: Regenerate lockfile and reinstall**

Run: `uv sync`
Expected: succeeds, `olmocr`/`ocrmypdf`/`ocrmypdf-appleocr` no longer installed

- [ ] **Step 7: Run the full test suite**

Run: `uv run pytest`
Expected: PASS, no `ocr_integration` marker warnings, no skipped OCR tests (there are none left)

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: drop olmocr/ocrmypdf deps and ocr_integration pytest marker"
```

---

### Task 7: Relocate OCR-specific docs and superpowers artifacts, annotate superseded ADRs

**Files:**
- Delete: `docs/context/ocr.md` (move content to `bochord` repo out of band — this task only removes it from wyrdcraeft and fixes the dangling reference)
- Modify: `docs/context/settings.md:60` (remove the `- [../context/ocr.md](ocr.md)` link)
- Delete: `docs/superpowers/plans/2026-07-10-bt-ocr-stage-b-live-pairing-and-clamp-regression.md`
- Delete: `docs/superpowers/plans/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md`
- Delete: `docs/superpowers/plans/2026-07-10-bt-ocr-witness-preparation.md`
- Delete: `docs/superpowers/specs/2026-07-10-bt-ocr-stage-b-live-pairing-and-clamp-regression-design.md`
- Delete: `docs/superpowers/specs/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md`
- Delete: `docs/superpowers/specs/2026-07-10-bt-ocr-witness-preparation-design.md`
- Delete: `docs/superpowers/handoffs/2026-07-09-bt-ocr-structured-data-plan.md`
- Modify: `docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md` (prepend superseded banner)
- Modify: `docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md` (prepend superseded banner)
- Modify: `docs/adr/0006-bt-jp2-witness-preparation-is-library-first.md` (prepend superseded banner)

**Interfaces:**
- Consumes: nothing (pure docs, no code dependency — can run in parallel with any of Tasks 1-6).
- Produces: no dangling links to `docs/context/ocr.md`; ADRs 0004-0006 remain readable as historical record but are clearly marked non-current.

- [ ] **Step 1: Copy the OCR-specific docs to bochord before deleting (outside this repo, manual step)**

```bash
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/context/ocr.md /Users/cmalek/src/workspace/bochord/docs/context/ocr.md
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/plans/2026-07-10-bt-ocr-stage-b-live-pairing-and-clamp-regression.md /Users/cmalek/src/workspace/bochord/docs/superpowers/plans/
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/plans/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md /Users/cmalek/src/workspace/bochord/docs/superpowers/plans/
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/plans/2026-07-10-bt-ocr-witness-preparation.md /Users/cmalek/src/workspace/bochord/docs/superpowers/plans/
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-07-10-bt-ocr-stage-b-live-pairing-and-clamp-regression-design.md /Users/cmalek/src/workspace/bochord/docs/superpowers/specs/
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md /Users/cmalek/src/workspace/bochord/docs/superpowers/specs/
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-07-10-bt-ocr-witness-preparation-design.md /Users/cmalek/src/workspace/bochord/docs/superpowers/specs/
cp /Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/handoffs/2026-07-09-bt-ocr-structured-data-plan.md /Users/cmalek/src/workspace/bochord/docs/superpowers/handoffs/
```

If `bochord`'s `docs/superpowers/{plans,specs,handoffs}/` directories don't exist yet, create them first (`mkdir -p`) — this is a one-time bootstrap, not a recurring step.

- [ ] **Step 2: Delete the docs from wyrdcraeft**

```bash
git rm docs/context/ocr.md \
  docs/superpowers/plans/2026-07-10-bt-ocr-stage-b-live-pairing-and-clamp-regression.md \
  docs/superpowers/plans/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md \
  docs/superpowers/plans/2026-07-10-bt-ocr-witness-preparation.md \
  docs/superpowers/specs/2026-07-10-bt-ocr-stage-b-live-pairing-and-clamp-regression-design.md \
  docs/superpowers/specs/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md \
  docs/superpowers/specs/2026-07-10-bt-ocr-witness-preparation-design.md \
  docs/superpowers/handoffs/2026-07-09-bt-ocr-structured-data-plan.md
```

- [ ] **Step 3: Fix the dangling link in `docs/context/settings.md`**

Remove line 60: `- [../context/ocr.md](ocr.md)`

- [ ] **Step 4: Annotate ADR 0004 as superseded**

Prepend to `docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md`, immediately after the `# ` title line:

```markdown
> **Superseded:** The OCR/witness-prep pipeline this ADR describes has moved to the `bochord` repo (see [ADR 0007](0007-ocr-pipeline-moves-to-bochord.md)). Kept here as historical record of the original design rationale.
```

- [ ] **Step 5: Annotate ADR 0005 as superseded**

Prepend to `docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md`, immediately after the `# ` title line:

```markdown
> **Superseded:** The OCR/witness-prep pipeline this ADR describes has moved to the `bochord` repo (see [ADR 0007](0007-ocr-pipeline-moves-to-bochord.md)). Kept here as historical record of the original design rationale.
```

- [ ] **Step 6: Annotate ADR 0006 as superseded**

Prepend to `docs/adr/0006-bt-jp2-witness-preparation-is-library-first.md`, immediately after the `# ` title line:

```markdown
> **Superseded:** The OCR/witness-prep pipeline this ADR describes has moved to the `bochord` repo (see [ADR 0007](0007-ocr-pipeline-moves-to-bochord.md)). Kept here as historical record of the original design rationale.
```

- [ ] **Step 7: Verify no remaining links to the deleted docs**

Run: `grep -rln "context/ocr.md\|bt-ocr-stage-b-live-pairing\|wyrdcraeft-ocr-bosworth-toller\|bt-ocr-witness-preparation\|bt-ocr-structured-data-plan" docs/ | grep -v "docs/adr/0007-ocr-pipeline-moves-to-bochord.md\|docs/superpowers/plans/2026-08-01-remove-ocr-pipeline.md"`
Expected: no output (the two excluded files are this plan and ADR 0007 itself, which legitimately name `docs/context/ocr.md` as removed/relocated — everything else must be clean)

- [ ] **Step 8: Commit**

```bash
git add docs/
git commit -m "docs: relocate OCR-specific docs to bochord, mark ADRs 0004-0006 superseded"
```

---

### Task 8: Delete the OCR/olmocr settings block from `settings.py`

**Files:**
- Modify: `wyrdcraeft/settings.py:73-196` (delete the entire `# OCR + olmocr settings` / `# OCR proxy settings` field block)
- Test: `tests/test_cli_commands.py` (extend the existing settings-loading smoke test, or add a small dedicated one below)

**Interfaces:**
- Consumes: Task 2 (deletes `wyrdcraeft/cli/ocr.py`, the last and only reader of every `settings.ocr_*` field — confirmed by repo-wide grep during planning; see Global Constraints).
- Produces: `Settings` with no `ocr_*` fields at all. No later task depends on this.

- [ ] **Step 1: Confirm (again, post-deletion) that nothing reads `settings.ocr_*`**

Run: `grep -rn "\.ocr_upstream_base_url\|\.ocr_olmocr_\|\.ocr_api_key\|\.ocr_legacy_\|\.ocr_skip_ocr\|\.ocr_proxy_" --include="*.py" wyrdcraeft/ tests/ scripts/`
Expected: no output (Task 2 already deleted the only caller, `wyrdcraeft/cli/ocr.py`)

- [ ] **Step 2: Write the failing test**

Add to `tests/test_cli_commands.py`:

```python
def test_settings_has_no_ocr_fields():
    from wyrdcraeft.settings import Settings

    field_names = Settings.model_fields.keys()
    ocr_fields = [name for name in field_names if name.startswith("ocr_")]
    assert ocr_fields == []
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_commands.py::test_settings_has_no_ocr_fields -v`
Expected: FAIL (24 `ocr_*` fields currently present)

- [ ] **Step 4: Delete lines 73-196 of `wyrdcraeft/settings.py`**

Delete the full block from the `# OCR + olmocr settings` comment (line 73) through the last `ocr_proxy_startup_timeout_seconds` field's closing `)` (line 195), plus the blank line at 196, leaving the `# Write-able settings` section header (former line 197) directly after `gemini_api_key`'s field definition.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_commands.py::test_settings_has_no_ocr_fields -v`
Expected: PASS

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/settings.py tests/test_cli_commands.py
git commit -m "refactor: delete unused OCR/olmocr settings block"
```

---

### Task 9: Repo-wide sweep for stragglers

**Files:**
- No fixed file list — this task greps for anything the prior 8 tasks missed and fixes what it finds.

**Interfaces:**
- Consumes: Tasks 1-8 all complete.
- Produces: a repo with zero remaining OCR-pipeline references outside `docs/adr/0004-0006` (intentionally kept, annotated) and this plan/ADR themselves.

- [ ] **Step 1: Sweep for leftover imports or references**

```bash
grep -rln "services\.ocr\b\|services\.ocr_proxy\|scripts\.ocr\|olmocr\|ocrmypdf" \
  --include="*.py" --include="*.toml" --include="*.md" . \
  | grep -v "docs/adr/0004\|docs/adr/0005\|docs/adr/0006\|docs/adr/0007\|docs/superpowers/plans/2026-08-01-remove-ocr-pipeline.md\|uv.lock"
```

Expected: no output. If anything shows up, fix it as part of this task (small targeted edit — do not add new scope).

- [ ] **Step 2: Confirm `uv.lock` has no stale OCR packages**

Run: `grep -n "^name = \"olmocr\"\|^name = \"ocrmypdf\"\|^name = \"ocrmypdf-appleocr\"" uv.lock`
Expected: no output (should already be gone after Task 6's `uv sync`; if present, run `uv sync` again)

- [ ] **Step 3: Run the full test suite, unfiltered — this is the plan's completion gate**

Run: `uv run pytest`
Expected: every test in the suite PASSES with zero failures and zero errors — no `-m` marker exclusions this time (earlier tasks' `-m "not ocr_integration and not llm"` runs were interim checks only). Do not mark this plan complete, and do not report the ADR 0007 work as done, until this exact command is green. If anything fails, fix it (it means an earlier task missed a reference) and rerun this step before proceeding to Step 4.

- [ ] **Step 4: Commit (only if Step 1 found something to fix)**

```bash
git add -A
git commit -m "chore: clean up remaining OCR pipeline references"
```

If Step 1 found nothing, skip this commit — there's nothing to record.
