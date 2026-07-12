# wyrdcraeft OCR Bosworth-Toller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to implement this plan phase-by-phase.
> After **each phase**: run spec compliance review, then code quality review.
> Do **not** start the next phase until both reviews pass.
>
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `wyrdcraeft ocr bosworth-toller` for BT JP2 witness prep (and optional
tile OCR), and narrow `old-english` back to literary edition PDFs.

**Architecture:** Extend `bt_witness_prep` input/pipeline for overlap + page
filtering; add thin `BTWitnessOCROrchestrator` for output-dir safety and stage
dispatch; wire Click command in `cli/ocr.py`. Phase 2 promotes benchmark OCR
helpers into product code. Phase 3 tightens `old_english_pipeline` input rules.
Phase 4 updates docs/glossary.

**Tech stack:** Python 3.12+, Click, Pillow, existing `bt_witness_prep` +
`old_english_pipeline` + `ocr_proxy`.

**Spec:** `docs/superpowers/specs/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md`

**Repo:** `/Users/cmalek/src/workspace/wyrdcraeft`

**Quality gates (every phase, touched Python only):**

```bash
cd /Users/cmalek/src/workspace/wyrdcraeft
ruff check <touched-files>
.venv/bin/mypy <touched-files>
make napoleon-gate
pytest <relevant-tests> -q
```

**Branch:** create `feature/ocr-bosworth-toller` from current HEAD before Phase 1.
Do not commit on `main` without explicit user consent.

**Commits:** create one commit at the end of each phase (after quality gates pass).
Do not batch multiple phases into one commit.

---

## Orchestration protocol (controller)

Use **subagent-driven-development** strictly. **Never implement phase work inline in the
parent session.** One phase at a time. **Never parallelize implementation subagents**
on this plan (same files).

### Per-phase loop (mandatory)

```text
1. Dispatch IMPLEMENTER subagent (generalPurpose) with Phase N prompt below
2. If BLOCKED / NEEDS_CONTEXT → answer, re-dispatch
3. Implementer runs quality gates; parent does NOT patch code inline
4. Dispatch SPEC REVIEWER subagent (generalPurpose, readonly) — Phase N checklist
5. If ❌ → dispatch IMPLEMENTER fix subagent → re-run SPEC REVIEWER
6. Dispatch CODE REVIEWER subagent (code-reviewer) — BASE_SHA = pre-phase, HEAD_SHA = post-phase
7. If issues → IMPLEMENTER fix subagent → re-run CODE REVIEWER
8. Parent commits phase (after gates + both reviews ✅)
9. Mark Phase N complete; proceed to Phase N+1
```

Parent session role: **dispatch, answer questions, commit, track checklist** — not implement.

### Implementer dispatch skeleton

```text
Task / generalPurpose:
  description: "Phase N: ..."
  prompt: |
    [Paste full Phase N section from this plan]
    [Paste spec excerpts for that phase from spec file]
    Work from: /Users/cmalek/src/workspace/wyrdcraeft
    Read AGENTS.md. Run quality gates before reporting DONE.
    Status report: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

### Spec reviewer dispatch skeleton

```text
Task / generalPurpose, readonly: true:
  description: "Spec review Phase N"
  prompt: |
    Spec: docs/superpowers/specs/2026-07-12-wyrdcraeft-ocr-bosworth-toller.md
    Phase N requirements: [paste Phase N acceptance criteria]
    Verify by reading code. Do not trust implementer report.
    Return ✅ or ❌ with file:line citations.
```

### Code reviewer dispatch skeleton

```text
Task / code-reviewer:
  description: "Code review Phase N"
  prompt: |
    Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
    Diff: branch changes (phase N commits only)
    Change Description: [phase summary]
    Custom Instructions: Check AGENTS.md doc contract, class-oriented design,
      ponytail minimal diff, tests meaningful not mock-only.
```

---

## File map

| File | Phase | Role |
|------|-------|------|
| `wyrdcraeft/services/ocr/bt_witness_prep/models.py` | 1 | extend `BTWitnessPrepInput` |
| `wyrdcraeft/services/ocr/bt_witness_prep/pipeline.py` | 1 | overlap + page filter in `prepare` |
| `wyrdcraeft/services/ocr/bt_witness_ocr.py` | 1, 2 | orchestrator + OCR stage |
| `wyrdcraeft/services/ocr/bt_tile_ocr.py` | 2 | promoted tile OCR helpers |
| `wyrdcraeft/cli/ocr.py` | 1, 2, 3 | CLI commands + shared options |
| `wyrdcraeft/services/ocr/old_english_pipeline.py` | 3 | input narrowing |
| `wyrdcraeft/services/ocr/__init__.py` | 1, 2 | exports |
| `tests/test_cli_ocr_bosworth_toller.py` | 1, 2 | new CLI tests |
| `tests/ocr/test_bt_witness_prep_pipeline.py` | 1 | overlap/filter unit tests |
| `tests/test_cli_ocr.py` | 3 | old-english rejection tests |
| `scripts/ocr/benchmark_bt_witness_prep.py` | 2 | thin shim → product imports |
| `doc/source/commands/ocr_bosworth_toller.rst` | 4 | Sphinx |
| `docs/context/ocr.md` | 4 | context doc |
| `CONTEXT.md` | 4 | capability map |
| `docs/adr/0006-bt-jp2-witness-preparation-is-library-first.md` | 4 | CLI follow-up note |

---

## Phase 1: Prep-only CLI + library hooks

**Delivers:** `wyrdcraeft ocr bosworth-toller` default prep run with
`--source-dir`, `--output-dir`, `--recipe-id`, `--overlap-px`, `--pages`,
`--limit`, `--force`. No `--ocr` yet.

### Phase 1 acceptance criteria (spec review checklist)

- [ ] `wyrdcraeft ocr --help` lists `bosworth-toller`
- [ ] Defaults: `data/bosworth_toller/jp2`, `data/ocr/bosworth-toller/prep`
- [ ] Prep-only default; no olmocr subprocess
- [ ] `--overlap-px` reaches `BTTilingConfig.overlap_px`
- [ ] `--pages` filters by `page_id` slug in memory after enumerate
- [ ] `--limit` applied after `--pages` filter
- [ ] Zero pages after filter → clear `click.ClickException`
- [ ] Non-empty output (`manifests/` or `tiles/`) blocked without `--force`
- [ ] Prep artifact tree unchanged vs existing `prepare_pages`
- [ ] Quality gates pass

---

### Task 1.1: Extend `BTWitnessPrepInput`

**Files:**
- Modify: `wyrdcraeft/services/ocr/bt_witness_prep/models.py`
- Test: `tests/ocr/test_bt_witness_prep_pipeline.py`

- [ ] **Step 1: Write failing test for overlap in prep run**

Add test that passes `overlap_px=40` and asserts tile `overlap_px` metadata in
run output (or inspect tiler via mock). Use fixtures under
`tests/fixtures/ocr/bt_witness_prep/`.

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/ocr/test_bt_witness_prep_pipeline.py -k overlap -v
```

- [ ] **Step 3: Add optional fields to `BTWitnessPrepInput`**

```python
# New optional fields on BTWitnessPrepInput:
overlap_px: int | None = None
page_ids: tuple[str, ...] | None = None
limit: int | None = None
```

Update `to_dict()` serialization. Document in class docstring + Napoleon `#:`.

- [ ] **Step 4: Run test — expect PASS**

---

### Task 1.2: Pipeline overlap + in-memory page filter

**Files:**
- Modify: `wyrdcraeft/services/ocr/bt_witness_prep/pipeline.py`
- Test: `tests/ocr/test_bt_witness_prep_pipeline.py`

- [ ] **Step 1: Write failing tests**

1. `test_prepare_filters_page_ids_in_memory` — 5 fixture JP2s, request 2 ids,
   assert run has exactly 2 pages.
2. `test_prepare_limit_after_page_filter` — `--pages` then `--limit 1`.
3. `test_prepare_zero_pages_raises` — filter matches nothing → `ValueError`
   with requested ids in message.

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement in `BTWitnessPrepPipeline.prepare`**

After `enumerator.enumerate()`:

```python
source_pages = _filter_source_pages(
    source_pages,
    page_ids=prep_input.page_ids,
    limit=prep_input.limit,
)
```

Build tiling config:

```python
tiling = self._tiling_config
if prep_input.overlap_px is not None:
    tiling = replace(tiling, overlap_px=prep_input.overlap_px)
    self._tiler = BTPageTiler(tiling)
```

Add module-level `_filter_source_pages()` helper in `pipeline.py` or small
`filtering.py` if pipeline grows.

Update `prepare_pages()` to pass `tiling_config` when `overlap_px` set.

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/ocr/test_bt_witness_prep_pipeline.py -q
```

---

### Task 1.3: Output-dir guard + orchestrator

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_ocr.py`
- Test: `tests/test_cli_ocr_bosworth_toller.py`

- [ ] **Step 1: Write failing tests for guard**

```python
def test_prep_refuses_nonempty_output_without_force(tmp_path, ...):
    # create manifests/ under output_dir
    # expect RuntimeError or ClickException when force=False

def test_prep_allows_nonempty_output_with_force(tmp_path, ...):
    # mock prepare_pages; assert called when force=True
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `BTWitnessOCROrchestrator`**

Class with constructor-injected collaborators (ponytail: one orchestrator, not
free functions pile).

```python
@dataclass(frozen=True)
class BTWitnessOCRConfig:
    source_dir: Path
    output_dir: Path
    recipe_id: str = "bt-two-column-v1"
    overlap_px: int = 30
    page_ids: tuple[str, ...] | None = None
    limit: int | None = None
    force: bool = False

class BTWitnessOCROrchestrator:
    def run_prep(self, config: BTWitnessOCRConfig) -> BTWitnessPrepRun:
        self._assert_output_dir_writable(config.output_dir, config.force)
        prep_input = BTWitnessPrepInput(...)
        return prepare_pages(prep_input)
```

`_assert_output_dir_writable`: true when `manifests/` or `tiles/` exists.

- [ ] **Step 4: Export from `wyrdcraeft/services/ocr/__init__.py` if needed**

- [ ] **Step 5: Run unit tests — expect PASS**

---

### Task 1.4: CLI command

**Files:**
- Modify: `wyrdcraeft/cli/ocr.py`
- Test: `tests/test_cli_ocr_bosworth_toller.py`

- [ ] **Step 1: Write failing CLI tests**

```python
def test_ocr_group_lists_bosworth_toller(runner):
    result = runner.invoke(cli, ["ocr", "--help"])
    assert "bosworth-toller" in result.output

def test_bosworth_toller_help_shows_flags(runner):
    ...

@patch("wyrdcraeft.cli.ocr.BTWitnessOCROrchestrator")
def test_bosworth_toller_default_prep(mock_orch, runner, tmp_path):
    # invoke with --source-dir fixture path, --output-dir tmp
    # assert run_prep called, echo summary
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Add `@ocr_group.command(name="bosworth-toller")`**

Options per spec. Parse `--pages` comma list → lowercase slugs. Wire to
orchestrator `run_prep`. Catch errors → `click.ClickException`.

Echo concise summary: output dir, page count, manifest paths.

- [ ] **Step 4: Run CLI tests**

```bash
pytest tests/test_cli_ocr_bosworth_toller.py tests/test_cli_ocr.py -q
```

- [ ] **Step 5: Quality gates**

```bash
ruff check wyrdcraeft/services/ocr/bt_witness_prep/models.py \
  wyrdcraeft/services/ocr/bt_witness_prep/pipeline.py \
  wyrdcraeft/services/ocr/bt_witness_ocr.py \
  wyrdcraeft/cli/ocr.py \
  tests/test_cli_ocr_bosworth_toller.py \
  tests/ocr/test_bt_witness_prep_pipeline.py
.venv/bin/mypy [same files]
make napoleon-gate
```

- [ ] **Step 6: Commit**

```bash
git add ...
git commit -m "$(cat <<'EOF'
Add bosworth-toller OCR prep CLI and library hooks.

Expose BT JP2 witness preparation as wyrdcraeft ocr bosworth-toller with
page filtering, overlap tuning, and output-dir safety guards.
EOF
)"
```

### Phase 1 spec review prompt (paste to subagent)

Verify Phase 1 acceptance criteria against spec sections: Flags, Stage semantics
(prep-only), Output safety, Required library adjustments, Phase 1 tests.

### Phase 1 code review focus

- `BTWitnessOCROrchestrator` single responsibility
- No temp JP2 copy for filtering
- Doc contract on new public types
- Tests hit real filter logic, not only mocks

---

## Phase 2: Tile OCR + `witnesses/` layout

**Delivers:** `--ocr`, `--skip-prep`, `--skip-ocr`, minimal olmocr overrides.

### Phase 2 acceptance criteria

- [ ] `--ocr` runs prep then tile OCR when prep absent
- [ ] `--skip-prep --ocr` requires `manifests/` + `tiles/`
- [ ] Per-tile output: `witnesses/tiles/<tile_id>/03_normalized.txt`
- [ ] Page join: `witnesses/pages/<page_id>.md` in geometry reading order
- [ ] `--skip-ocr` reuses cached tile text
- [ ] Minimal flags: `--olmocr-workers`, `--olmocr-target-longest-image-dim`,
  `--upstream-base-url`
- [ ] Benchmark script imports from product module (shim retained)
- [ ] Quality gates pass

---

### Task 2.1: Promote tile OCR helpers

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_tile_ocr.py`
- Modify: `scripts/ocr/benchmark_bt_witness_prep.py`
- Test: `tests/ocr/test_bt_tile_ocr.py`

- [ ] **Step 1: Write failing tests**

Port/adapt from `tests/ocr/test_benchmark_bt_witness_prep.py`:
- `discover_tile_images` reading order
- `concatenate_tile_texts` blank-line join
- `run_tile_ocr` mocked `run_old_english_ocr_pipeline`

- [ ] **Step 2: Move functions from benchmark → `bt_tile_ocr.py`**

Rename for product clarity:
- `discover_candidate_tile_images` → `discover_tile_images`
- `concatenate_candidate_ocr_texts` → `concatenate_tile_texts`
- `run_page_ocr` → `run_tile_ocr`
- `run_candidate_page_ocr` → `run_page_witness_ocr`

Keep `CANDIDATE_TILE_READING_ORDER` constant in product module.

Benchmark script: `from wyrdcraeft.services.ocr.bt_tile_ocr import ...`

- [ ] **Step 3: Run tests — expect PASS**

---

### Task 2.2: Witness writer + orchestrator OCR stage

**Files:**
- Modify: `wyrdcraeft/services/ocr/bt_witness_ocr.py`
- Test: `tests/test_cli_ocr_bosworth_toller.py`

- [ ] **Step 1: Write failing tests**

```python
def test_run_ocr_writes_witness_tree(tmp_path, monkeypatch):
    # prep fixture workspace or mock prep
    # mock run_tile_ocr to write normalized text
    # assert witnesses/tiles/<tile_id>/03_normalized.txt
    # assert witnesses/pages/<page_id>.md
```

- [ ] **Step 2: Implement `run_ocr` on orchestrator**

For each page in `manifests/pages.jsonl` (or from prep run):
1. `discover_tile_images(output_dir, page_id)`
2. OCR each tile to `witnesses/tiles/<tile_id>/`
3. Join → `witnesses/pages/<page_id>.md`

Use `OldEnglishOCRConfig` with settings-resolved proxy fields; only 3 CLI
overrides exposed.

- [ ] **Step 3: Wire CLI `--ocr`, `--skip-prep`, `--skip-ocr`**

Validate flag combos:
- `--ocr` alone → prep + ocr
- `--skip-prep --ocr` → ocr only
- `--skip-ocr` → no subprocess, reuse cache

- [ ] **Step 4: Quality gates + commit**

```bash
git commit -m "$(cat <<'EOF'
Add bosworth-toller tile OCR witness stage.

Promote benchmark tile OCR helpers into product code and emit witnesses/
artifacts with page-level markdown joins.
EOF
)"
```

### Phase 2 spec review prompt

Verify spec sections: `--ocr` stage, Output layout `witnesses/`, Stage semantics,
Phase 2 tests, minimal override flags.

### Phase 2 code review focus

- Tile id in path matches manifest `tile_id` (colon → filesystem-safe if needed)
- No case-bundle writes
- Benchmark shim still works: `pytest tests/ocr/test_benchmark_bt_witness_prep.py -q`

---

## Phase 3: Narrow `old-english` inputs

**Delivers:** reject JP2 + image directories with actionable message.

### Phase 3 acceptance criteria

- [ ] `.pdf` still works
- [ ] single loose image still works
- [ ] `.jp2` file → error with bosworth-toller hint
- [ ] image directory → same error
- [ ] Existing `test_cli_ocr.py` still pass
- [ ] Quality gates pass

---

### Task 3.1: Input validation

**Files:**
- Modify: `wyrdcraeft/services/ocr/old_english_pipeline.py`
- Test: `tests/test_cli_ocr.py` or `tests/ocr/test_old_english_input.py`

- [ ] **Step 1: Write failing tests**

```python
def test_old_english_rejects_jp2_file(tmp_path):
    jp2 = tmp_path / "scan.jp2"
    jp2.write_bytes(b"...")
    with pytest.raises(RuntimeError, match="bosworth-toller"):
        run_old_english_ocr_pipeline(OldEnglishOCRConfig(input_path=jp2, ...))

def test_old_english_rejects_image_directory(tmp_path):
    ...
```

- [ ] **Step 2: Implement early validation in `_resolve_input_pdf` or pipeline entry**

Before image-dir handling:

```python
_BT_WITNESS_HINT = (
    "JP2 scans and image directories are Bosworth-Toller witness input. "
    "Use: wyrdcraeft ocr bosworth-toller --source-dir <jp2-dir>"
)
```

- [ ] **Step 3: Quality gates + commit**

```bash
git commit -m "$(cat <<'EOF'
Narrow old-english OCR input to literary PDFs and loose images.

Reject JP2 files and image directories with a pointer to ocr bosworth-toller.
EOF
)"
```

### Phase 3 spec review prompt

Verify spec section: `old-english narrowing (phase 3)` + acceptance criteria line
about JP2 directories.

### Phase 3 code review focus

- Error message exact per spec
- No regression for PDF path in CLI integration tests

---

## Phase 4: Documentation + glossary

**Delivers:** operator docs and CONTEXT updates.

### Phase 4 acceptance criteria

- [ ] Sphinx command page for `bosworth-toller`
- [ ] `docs/context/ocr.md` lists new CLI
- [ ] `CONTEXT.md` capability map updated (bt witness prep has CLI)
- [ ] ADR 0006 CLI follow-up paragraph added
- [ ] `make napoleon-gate` still passes (no new Python required)

---

### Task 4.1: Docs

**Files:**
- Create: `doc/source/commands/ocr_bosworth_toller.rst`
- Modify: `docs/context/ocr.md`, `CONTEXT.md`
- Modify: `docs/adr/0006-bt-jp2-witness-preparation-is-library-first.md`
- Modify: Sphinx toctree if needed

- [ ] Document all flags, defaults, examples from spec
- [ ] Note: run from repo root; extract JP2 zip to `data/bosworth_toller/jp2`
- [ ] Note: horizontal split is geometry + overlap, not line-aware (v2)
- [ ] Cross-link `bt_ocr_witness_preparation.rst`

- [ ] **Commit**

```bash
git commit -m "$(cat <<'EOF'
Document wyrdcraeft ocr bosworth-toller command and update OCR context.

EOF
)"
```

### Phase 4 spec review prompt

Verify spec section: Documentation updates + Acceptance criteria doc items.

### Phase 4 code review focus

- CONTEXT.md stays glossary-only (no implementation detail creep)
- ADR amendment is short follow-up, not rewrite

---

## Final integration review

After Phase 4, dispatch **code-reviewer** on full branch vs `feature/ocr-bosworth-toller` base:

```text
Diff: branch changes (all phases)
Custom Instructions: Verify end-to-end spec acceptance criteria, phase boundaries,
  no scope creep into case-bundle parsing or line-aware tiling.
```

Optional smoke (operator, not CI gate):

```bash
wyrdcraeft ocr bosworth-toller \
  --source-dir tests/fixtures/ocr/bt_witness_prep \
  --output-dir /tmp/bt-prep-smoke \
  --pages bt-0002
```

---

## Controller checklist

| Phase | Implementer | Spec review ✅ | Code review ✅ |
|-------|-------------|----------------|----------------|
| 1 Prep CLI | | | |
| 2 Tile OCR | | | |
| 3 old-english narrow | | | |
| 4 Docs | | | |
| Final | | | N/A |

**Stop conditions:** BLOCKED on missing JP2 at default path is OK for tests (use
fixtures). Live `--ocr` integration stays behind existing `ocr_integration` marker.
