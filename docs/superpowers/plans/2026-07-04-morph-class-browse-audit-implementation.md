# Morph Class Browse Surfacing + Wright Audit — Implementation Plan

> **For agentic workers:** Use [subagent-driven-development](/Users/cmalek/.cursor/plugins/cache/cursor-public/superpowers/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/skills/subagent-driven-development/SKILL.md) per phase. Each phase ends with **Gate A (spec review)** then **Gate B (code review)** before the next phase starts.
>
> **Design authority:** [docs/superpowers/specs/2026-07-04-morph-class-browse-audit-design.md](../specs/2026-07-04-morph-class-browse-audit-design.md)
>
> **Reuse (do not fork):** Wright catalog Phases 1–2 complete; Phase 4 ingest pattern in [doc/plans/morphology-wright-catalog/phase-4-wright-section-text-ingest.md](../../../doc/plans/morphology-wright-catalog/phase-4-wright-section-text-ingest.md). **Out of scope here:** `forms.morph_class_id` FK propagation ([phase-3-forms-link-and-query.md](../../../doc/plans/morphology-wright-catalog/phase-3-forms-link-and-query.md)) — browse v1 joins at query time only.

**Goal:** Surface deterministic per-POS morph-class metadata and Wright § citations in `lexicon browse` dictionary detail (display-only v1), add inline/overlay Wright § text after ingest, and ship a separate legacy-Wright audit command that never mutates source files.

**Architecture:** Join `lemma_morph_classes` → `morph_classes` → `morph_class_wright_sections` at browse read time via existing `MorphologyCatalogQueryService`. Ingest Wright markdown into `wright_sections.section_text`. Audit reads source lemma files + DB assignments; no build blocking.

**Tech stack:** Python 3.12+, SQLAlchemy 2.x, Textual TUI, Click CLI, pytest, `isolated_morphology_app_data`, `lexicon_source_db` fixture.

---

## Recommended phase order

| Order | Phase | Delivers | Depends on |
|-------|-------|----------|------------|
| **1** | Browse morph-class detail block | Class label, provenance, § list, explicit `Unclassified` in dictionary detail pane | Wright catalog P1–P2 in DB |
| **2** | Wright § text ingest | `wright_sections.section_text` populated from `data/sources/wright.md` | Wright catalog P1 |
| **3** | Browse Wright text pane | Select § citation → inline or overlay text from SQLite | Phases 1 + 2 |
| **4** | Legacy Wright audit command | Human + JSON reports on source files vs deterministic assignments | Wright catalog P2 assignments in DB |

Phase 4 is independent of Phases 2–3 and **may run in parallel** after Phase 1 if staffed. Do not merge audit into browse build paths.

---

## Locked constraints (do not re-litigate)

From design spec + [00-design-decisions.md](../../../doc/plans/morphology-wright-catalog/00-design-decisions.md):

- Canonical truth = per-POS **morph class** (`lemma_morph_classes`), not legacy source `wright`
- Wright § remain **class-linked citations**, not per-lemma guesses from sparse source cells
- Deterministic only: one exact class → assign row; zero or many exact classes → **no row** → browse shows **`Unclassified`**
- Browse v1: **dictionary detail only**, **display-only**, **join-at-browse-time** (no lexicon projection denormalization)
- Show: full class label, assignment provenance (`paradigm` / `features` / `wright_section`), Wright § numbers
- Wright § text: stored DB text only; no runtime markdown/PDF parsing in browse
- Audit: separate command; source lemma files first; generated artifacts second; **no auto-rewrite** of source files in v1
- Reuse `MorphologyCatalogQueryService`, `catalog_pos_from_bt_pos`, `normalize_morphology_title` — no parallel catalog/query stack

---

## Global risks

| Risk | Mitigation in plan |
|------|-------------------|
| **Ambiguity** (multiple candidate classes) | Assigner already skips row; browse must show `Unclassified`, never pick arbitrarily |
| **POS mismatch** (BT `adj` vs catalog `adjective`, empty POS, inferred POS wrong) | Always map via `catalog_pos_from_bt_pos`; unmappable/empty POS → `Unclassified`; tests for `adj`→`adjective` |
| **Browse query performance** | One catalog lookup per `get_details()`; share engine with `LexiconQueryService`; no N+1 on § list (already joined in query service) |
| **Wright text coverage gaps** | Phase 2 ingest summary reports coverage %; Phase 3 overlay shows explicit “text not ingested” for NULL `section_text` |
| **Dirty worktree / unrelated changes** | Subagents touch only files listed in phase; coordinator runs `git diff --stat` before each dispatch; do not commit `.aidex/index.db` or unrelated help assets |
| **Legacy `_format_class_lines` drift** | Phase 1 replaces legacy form-derived class lines with catalog block; keep morphology sidebar unchanged |
| **Circular import** (morphology test collection) | Phases 1–3 run targeted lexicon + catalog tests; note pre-existing `build_profile` cycle separately if full `tests/morphology` collection required |

---

## Orchestration (subagent-driven)

```text
1. Coordinator reads this plan + design spec + AGENTS.md
2. Record BASE commit before Phase N implementer
3. Run: scripts/task-brief <this-plan> N  → brief path
4. Dispatch implementer (one task group per subagent; sequential tasks within phase OK for one subagent if small)
5. Implementer writes report to matching task-N-report.md path
6. Coordinator runs validation commands for phase
7. Gate A: code-reviewer subagent (spec compliance) with brief + report + review-package diff
8. Gate B: bugbot subagent (quality) with same diff
9. Append progress to git-path sdd/progress.md: Task N complete (commits BASE..HEAD, review clean)
10. Next phase only after both gates pass
```

Review package:

```bash
scripts/review-package <BASE_COMMIT> HEAD
```

---

## Phase 1 — Browse morph-class detail block

### Objective

Enrich `lexicon browse` dictionary detail with Wright catalog assignment: full class label, provenance, Wright § numbers, or explicit **`Unclassified`**. Join at read time; no lexicon table DDL changes.

### Exact files likely touched

| Action | Path |
|--------|------|
| Modify | `wyrdcraeft/services/morphology/catalog/query.py` |
| Modify | `wyrdcraeft/services/lexicon/query.py` |
| Modify | `wyrdcraeft/services/lexicon/tui.py` |
| Modify | `wyrdcraeft/services/lexicon/__init__.py` (exports if needed) |
| Create/Modify | `tests/lexicon/test_morph_class_browse.py` (preferred) or extend `test_query_service.py` / `test_tui.py` |
| Modify | `tests/morphology/test_morph_catalog_query.py` (if extending `MorphClassView`) |

### Subagent task breakdown

#### Task 1.1 — Extend catalog read DTO

- Add `assignment_source: str` to `MorphClassView` (load from `LemmaMorphClass.assignment_source` in `lookup_lemma_class`)
- Add frozen helper dataclass e.g. `LemmaMorphClassSummary` with:
  - `display_label: str` — prefer human label like `{pos}, {modern_class}` or `canonical_name` when richer (document rule in test)
  - `assignment_source: str`
  - `wright_sections: tuple[int, ...]`
  - `is_unclassified: bool`
- Add `format_morph_class_display_label(view: MorphClassView) -> str` in catalog query module (single formatter, reused by browse + audit)

#### Task 1.2 — Browse-time join in `LexiconQueryService`

- Compose `MorphologyCatalogQueryService` sharing `self._engine` (construct once in `LexiconQueryService.__init__`)
- In `get_details()`:
  - Normalize headword: `normalize_morphology_title(details.headword)`
  - Map POS: `catalog_pos_from_bt_pos(entry_pos)` inside try/except → unmappable → unclassified summary
  - Call `lookup_lemma_class(title, catalog_pos)` → map to `LemmaMorphClassSummary` or unclassified sentinel
- Add optional field on `EntryDetails`: `morph_class: LemmaMorphClassSummary | None` (None = unmappable POS; use `is_unclassified=True` inside summary when lookup returns None)

#### Task 1.3 — Details pane rendering

- Replace `_format_class_lines()` Wright block with catalog-driven lines, e.g.:
  - `Morph class: noun, a-stem` (exact format locked by test)
  - `Provenance: paradigm` (omit line when unclassified)
  - `Wright §: 334, 335, …` (omit when none)
  - `Morph class: Unclassified` when no assignment
- **Do not** add browse filters, form-row decoration, or morphology sidebar changes
- Keep senses/etymology/gender lines unchanged

#### Task 1.4 — Tests

- Catalog query test: `assignment_source` populated for known lemma (extend `test_lookup_stan_noun_returns_masculine_a_stem`)
- Lexicon test with `lexicon_source_db` + seeded catalog + assignment:
  - rebuild lexicon after morphology build path seeds assignments OR insert fixture assignment in test DB
  - assert `get_details()` morph_class fields for one noun + one unclassified lemma
  - assert TUI `_format_entry_details` contains `Unclassified` for missing assignment
- POS mapping test: entry with `pos='adj'` resolves catalog `adjective` lookup key

### Validation commands

```bash
.venv/bin/ruff check wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/services/lexicon/tui.py tests/lexicon/test_morph_class_browse.py tests/morphology/test_morph_catalog_query.py
.venv/bin/mypy wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/services/lexicon/tui.py
make napoleon-gate
.venv/bin/pytest tests/morphology/test_morph_catalog_query.py tests/lexicon/test_morph_class_browse.py tests/lexicon/test_query_service.py tests/lexicon/test_tui.py -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

### Gate A — Spec review checklist

- [ ] Join-at-browse-time only; no `lexicon_entries` / `lexicon_forms` schema change
- [ ] Uses `MorphologyCatalogQueryService.lookup_lemma_class`, not legacy `forms.wright`
- [ ] Explicit `Unclassified` when no assignment or unmappable POS
- [ ] Shows provenance + Wright § numbers from class junction, not source file `wright` column
- [ ] Dictionary detail only; no new filters or analysis UX
- [ ] `assignment_source` exposed to browse layer

### Gate B — Code review checklist

- [ ] No real app-data writes in tests without `isolated_morphology_app_data` / `lexicon_source_db`
- [ ] Shared SQLAlchemy engine; no per-lookup engine leak
- [ ] Napoleon/doc contract on new public types
- [ ] No scope creep into `forms.morph_class_id` migration

### Acceptance criteria

- Selecting a classified dictionary entry shows morph class label, provenance, and Wright § list in detail pane
- Selecting an entry with no `lemma_morph_classes` row shows **`Morph class: Unclassified`**
- Empty/unmapped POS shows `Unclassified`, not an exception
- Existing lexicon search/sidebar behavior unchanged
- All validation commands green

### Subagent dispatch packet — Phase 1

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Role: Implementer
Model: gpt-5.4-medium (integration + multi-file)

Read first (requirements, verbatim values):
  docs/superpowers/plans/2026-07-04-morph-class-browse-audit-implementation.md — Phase 1 section only
  docs/superpowers/specs/2026-07-04-morph-class-browse-audit-design.md

Context:
  - Wright catalog Phases 1–2 done: lemma_morph_classes + MorphologyCatalogQueryService.lookup_lemma_class
  - Lexicon browse: LexiconQueryService.get_details + tui._format_entry_details
  - POS map: wyrdcraeft/services/morphology/catalog/pos.py catalog_pos_from_bt_pos
  - Title normalize: normalize_morphology_title (same as assigner)

Implement Phase 1 Tasks 1.1–1.4. Do NOT add forms.morph_class_id, lexicon build denormalization, browse filters, or audit command.

Report file: doc/sessions/task-phase1-morph-class-browse-report.md
Report must include: status (DONE|BLOCKED|NEEDS_CONTEXT), commits, test commands + output summary, self-review.

Quality gates: run Phase 1 validation commands before reporting DONE.
AGENTS.md: napoleon-gate, morphology test isolation, class-oriented service boundaries.
```

---

## Phase 2 — Wright § text ingest

### Objective

Populate `wright_sections.section_text` from `data/sources/wright.md` so browse can read paragraph text from SQLite. Idempotent ingest; no duplicate text on junction rows.

### Exact files likely touched

| Action | Path |
|--------|------|
| Create | `wyrdcraeft/services/morphology/catalog/wright_text.py` |
| Modify | `wyrdcraeft/services/morphology/catalog/query.py` (optional `lookup_section_text(section_no)`) |
| Modify | `wyrdcraeft/cli/morphology.py` |
| Create | `tests/morphology/test_wright_section_text.py` |
| Modify | `doc/source/overview/command_morphology_generate.rst` (CLI help only, if subcommand added) |

Follow task breakdown in [phase-4-wright-section-text-ingest.md](../../../doc/plans/morphology-wright-catalog/phase-4-wright-section-text-ingest.md) with these plan-specific choices:

- **CLI:** `wyrdcraeft morphology ingest-wright-text --source data/sources/wright.md` (explicit command; do not auto-run on every build in v1)
- **Upsert policy:** update rows where `section_text IS NULL`; `--force` overwrites non-null
- **IngestResult:** counts updated/skipped, markdown § not in catalog, catalog § still null after ingest (coverage %)

### Subagent task breakdown

#### Task 2.1 — Markdown § parser

- Parse `§ N.` / `§ N` at line start; body until next §
- Return `dict[int, str]`; preserve OE Unicode; normalize whitespace only
- Test against §334 snippet from repo markdown

#### Task 2.2 — `WrightSectionTextIngester`

- `ingest(engine, md_path, *, force=False) -> IngestResult`
- Warn on extra markdown §; warn on catalog § still NULL post-ingest

#### Task 2.3 — CLI subcommand

- Wire into `wyrdcraeft morphology ingest-wright-text`
- Respect canonical DB readiness gate (`ensure_database_ready`)

#### Task 2.4 — Query helper (minimal)

- Add `lookup_wright_section_text(section_no: int) -> str | None` on `MorphologyCatalogQueryService` (single-row select)

### Validation commands

```bash
.venv/bin/pytest tests/morphology/test_wright_section_text.py tests/morphology/test_morph_catalog_query.py -q
.venv/bin/ruff check wyrdcraeft/services/morphology/catalog/wright_text.py wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/cli/morphology.py
.venv/bin/mypy wyrdcraeft/services/morphology/catalog/wright_text.py wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/cli/morphology.py
make napoleon-gate
```

Manual spot-check:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-wright-text .venv/bin/wyrdcraeft morphology build --limit 5
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-wright-text .venv/bin/wyrdcraeft morphology ingest-wright-text --source data/sources/wright.md
# sqlite: SELECT section_no, length(section_text) FROM wright_sections WHERE section_no=334;
```

### Gate A — Spec review checklist

- [ ] Text stored on `wright_sections`, not junction
- [ ] Idempotent default; `--force` documented
- [ ] Parser matches repo `wright.md` heading format
- [ ] Ingest summary reports coverage gaps

### Gate B — Code review checklist

- [ ] No runtime markdown read from browse/audit commands
- [ ] Tests use temp DB only
- [ ] CLI does not block `morphology build`

### Acceptance criteria

- §334 (and tested sections) have non-empty `section_text` after ingest
- Re-run without `--force` is no-op for populated rows
- Ingest prints/warns uncovered catalog § numbers

### Subagent dispatch packet — Phase 2

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Role: Implementer
Model: composer-2.5-fast (mechanical parser + CLI if spec followed closely)

Read first:
  docs/superpowers/plans/2026-07-04-morph-class-browse-audit-implementation.md — Phase 2
  doc/plans/morphology-wright-catalog/phase-4-wright-section-text-ingest.md (full task text)

Implement Tasks 2.1–2.4. Reuse MorphologyCatalogQueryService patterns. Explicit CLI subcommand only.

Report: doc/sessions/task-phase2-wright-text-ingest-report.md
Run Phase 2 validation commands before DONE.
```

---

## Phase 3 — Browse Wright § text pane

### Objective

When user selects a Wright § citation in dictionary detail, show stored section text inline or in Textual overlay/modal. Handle missing text gracefully.

### Exact files likely touched

| Action | Path |
|--------|------|
| Modify | `wyrdcraeft/services/lexicon/tui.py` |
| Modify | `wyrdcraeft/services/lexicon/query.py` (only if detail payload needs § text prefetch) |
| Modify | `tests/lexicon/test_tui.py` and/or `tests/lexicon/test_morph_class_browse.py` |

### Subagent task breakdown

#### Task 3.1 — Selectable § citations in detail pane

- Render Wright § list as Textual `Button` or `ListView` items below morph-class block (dictionary detail column only)
- Store `section_no` on each widget; multiple § all selectable (no fake primary §)

#### Task 3.2 — Overlay / inline text pane

- On § select: call `MorphologyCatalogQueryService.lookup_wright_section_text(section_no)`
- If text present: show `ModalScreen` or dedicated `#wright-text-pane` Static with scroll
- If NULL: show short message “Wright § N text not ingested — run morphology ingest-wright-text”
- Dismiss via Esc / close button

#### Task 3.3 — Tests

- Textual async test: open detail → click § → modal contains substring from fixture ingested text
- Test NULL `section_text` path shows not-ingested message (no crash)

### Validation commands

```bash
.venv/bin/ruff check wyrdcraeft/services/lexicon/tui.py wyrdcraeft/services/lexicon/query.py
.venv/bin/mypy wyrdcraeft/services/lexicon/tui.py
make napoleon-gate
.venv/bin/pytest tests/lexicon/test_tui.py tests/lexicon/test_morph_class_browse.py -q
```

### Gate A — Spec review checklist

- [ ] Reads § text from SQLite only
- [ ] Works for any linked § on class (multi-§ classes)
- [ ] No browse filters or form-row decoration added
- [ ] Missing text is explicit, not blank failure

### Gate B — Code review checklist

- [ ] Textual focus/keyboard sane (Esc closes overlay)
- [ ] No markdown file I/O in TUI path
- [ ] Tests do not require interactive terminal beyond Textual run_test

### Acceptance criteria

- User can open Wright § text from dictionary detail for ingested sections
- Missing ingest shows actionable message
- Phase 1 detail lines still correct

### Subagent dispatch packet — Phase 3

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Role: Implementer
Model: gpt-5.4-medium (Textual UX judgment)

Depends on: Phase 1 browse morph block + Phase 2 ingest API lookup_wright_section_text

Read: Phase 3 section of docs/superpowers/plans/2026-07-04-morph-class-browse-audit-implementation.md

Implement Tasks 3.1–3.3. Overlay/modal acceptable; keep morphology sidebar unchanged.

Report: doc/sessions/task-phase3-wright-text-pane-report.md
```

---

## Phase 4 — Legacy Wright audit command

### Objective

Separate CLI reporting legacy source `wright` field quality vs deterministic `lemma_morph_classes` assignments. Human-readable default; optional JSON. **Never** mutates source files or blocks build.

### Exact files likely touched

| Action | Path |
|--------|------|
| Create | `wyrdcraeft/services/morphology/catalog/wright_audit.py` |
| Modify | `wyrdcraeft/cli/morphology.py` |
| Create | `tests/morphology/test_wright_audit.py` |
| Modify | `tests/test_cli_morphology.py` (CLI smoke) |

### Subagent task breakdown

#### Task 4.1 — Source file readers (priority 1)

Parse inflectable rows from bundled sources (reuse morphology loader paths / `Word` model):

- `dict_adj-vb-part-num-adv-noun.txt`
- `manual_forms.txt`
- `para_vb.txt` (for invalid token scan)

For each lemma+POS row extract legacy `wright` string.

#### Task 4.2 — Audit checks (design spec)

1. **Malformed legacy Wright:** legal = blank, `0`, or semicolon-separated integers; flag tokens like `Camp`
2. **Contradiction:** encoded Wright § set vs assigned class Wright § set (from DB) — report when intersection empty but both non-empty
3. **Unclassified:** inflectable lemma+POS with no `lemma_morph_classes` row after deterministic assigner rules
4. **Blank legacy but classified:** source `wright` blank/`0` yet DB has assignment row

Priority order in report: source files first, then optional secondary pass on `forms`/`manual` artifacts (counts only in v1 if timeboxed).

#### Task 4.3 — CLI

- `wyrdcraeft morphology audit-wright [--json] [--data-dir …] [--db PATH]`
- Default: summary counts + small sample rows per category (cap samples e.g. 10)
- `--json`: machine-readable full lists
- Exit code 0 always in v1 (report-only); document that build is never blocked

#### Task 4.4 — Tests

- Fixture rows: malformed `Camp`, blank wright + classified assignment, contradiction case with mocked class §
- JSON output schema smoke test
- CLI invokes without writing source files

### Validation commands

```bash
.venv/bin/ruff check wyrdcraeft/services/morphology/catalog/wright_audit.py wyrdcraeft/cli/morphology.py
.venv/bin/mypy wyrdcraeft/services/morphology/catalog/wright_audit.py wyrdcraeft/cli/morphology.py
make napoleon-gate
.venv/bin/pytest tests/morphology/test_wright_audit.py tests/test_cli_morphology.py -q
```

Manual:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-audit .venv/bin/wyrdcraeft morphology build --limit 100
.venv/bin/wyrdcraeft morphology audit-wright --db /tmp/wc-audit/wyrdcraeft.sqlite3
.venv/bin/wyrdcraeft morphology audit-wright --json | head
```

### Gate A — Spec review checklist

- [ ] Separate command; not hooked into `morphology build` or `lexicon build`
- [ ] Source lemma files audited before generated artifacts
- [ ] Four check categories implemented
- [ ] No source file auto-rewrite
- [ ] Does not treat legacy `wright` as canonical truth

### Gate B — Code review checklist

- [ ] Uses existing DB assignment tables + catalog § links
- [ ] Tests isolated; no default app-data path writes
- [ ] Sample caps prevent huge stderr dumps

### Acceptance criteria

- Command prints summary of malformed, contradictory, unclassified, and blank-but-classified rows
- `--json` suitable for later analysis scripts
- Running audit does not modify `wyrdcraeft/etc/morphology/*.txt`

### Subagent dispatch packet — Phase 4

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Role: Implementer
Model: gpt-5.4-medium

Read:
  docs/superpowers/plans/2026-07-04-morph-class-browse-audit-implementation.md — Phase 4
  docs/superpowers/specs/2026-07-04-morph-class-browse-audit-design.md — Audit Command section

Implement wright_audit service + morphology audit-wright CLI. Report-only v1.

Report: doc/sessions/task-phase4-wright-audit-report.md
```

---

## Final whole-branch review

After Phase 4 gates pass:

```bash
git merge-base main HEAD   # MERGE_BASE
scripts/review-package <MERGE_BASE> HEAD
```

Dispatch **code-reviewer** (`readonly: true`, most capable model) with:

- This plan + design spec
- Review package path
- Verify all acceptance criteria across phases
- Confirm no scope creep: no browse filters, no `forms.morph_class_id`, no source rewrites

---

## Explicitly deferred (not in this plan)

| Item | Where tracked |
|------|----------------|
| `forms.morph_class_id` FK + morphology query payload | [phase-3-forms-link-and-query.md](../../../doc/plans/morphology-wright-catalog/phase-3-forms-link-and-query.md) |
| Denormalize morph class into `lexicon_entries` | Design: only if join-at-browse-time proves slow |
| Browse filters by class / Wright | Design non-goal for v1 |
| Auto-fix source `wright` cells | Audit v1 report-only |
| Probabilistic classification queue | Design non-goal |

---

## Open questions

**None blocking.** Coordinator defaults:

- Phase 2 uses **explicit** `ingest-wright-text` subcommand (not auto on build)
- Phase 3 uses **modal overlay** unless implementer finds existing Textual pattern in repo for inline expansion (either OK if spec criteria met)
- Phase 1 **replaces** legacy `_format_class_lines` catalog display with Wright catalog block (sidebar paradigm grids unchanged)

---

## Coordinator quick reference — phase order summary

```text
P1: browse detail ← catalog lookup (no schema change)
P2: wright.md → wright_sections.section_text
P3: browse § overlay ← P1 citations + P2 text
P4: audit-wright CLI (parallel after P1 OK)

Gates: spec review → code review → next phase
Reuse: MorphologyCatalogQueryService, pos.py, LemmaMorphClassAssigner outputs
Skip: forms.morph_class_id, lexicon denorm, browse filters
```
