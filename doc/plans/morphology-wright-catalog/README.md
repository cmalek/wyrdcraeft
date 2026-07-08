# Morphology Wright Catalog — Phased Implementation Plan

> **For agentic workers:** Use [subagent-driven-development](https://github.com/obra/superpowers) per phase. Each phase ends with **two mandatory gates** before starting the next phase: **spec review**, then **code review**.

**Goal:** Replace ad-hoc Wright/paradigm JSON and unreliable legacy `forms.paradigm` / `paraID` / `wright` strings with a normalized morphology reference catalog, lemma-level class assignment, and optional form-level propagation.

**Architecture:** Staged canonical replacement (A′): (1) reference catalog tables seeded from `wright_paradigms.json`, (2) lemma assignment on `(normalized_title, pos)`, (3) denormalized `forms.morph_class_id`, (4) Wright § text ingest from `data/sources/wright.md`.

**Tech stack:** Python 3.12+, SQLAlchemy 2.x, Alembic, SQLite (`wyrdcraeft.sqlite3`), Click CLI, pytest, `isolated_morphology_app_data` test fixture.

---

## Design decisions (locked)

See [00-design-decisions.md](./00-design-decisions.md) for the full grilling outcome.
Schema normalization ADR: [`docs/adr/0002-normalized-canonical-schema.md`](../../../docs/adr/0002-normalized-canonical-schema.md).
Do not re-litigate without an ADR.

| Decision | Choice |
|----------|--------|
| Long-term direction | Staged **A** — catalog becomes source of truth; legacy columns deprecated later |
| Assignment grain | **Lemma-level** |
| Assignment key | **`(normalized_title, pos_id)`** via **`parts_of_speech`** FK |
| Participles | Verbal → `(verb_lemma, verb)`; declined participial lemmas → `(title, adjective)` → `adj.present_participle` / `adj.past_participle` |
| Participial catalog `pos` | **`adjective`** + `features.participle` (fixture already models this) |
| Wright § storage | **`wright_sections`** table + junction; **`section_text` lazy** |
| `MorphClass` PK | **Int surrogate** + unique **`class_key`** (not text PK) |
| POS source of truth | **`parts_of_speech`** table; product tables use FKs only |
| Form inflection | **`inflection_codes`** + **`forms.inflection_code_id`** |
| Dictionary link on forms | **`forms.entry_id`** FK; **NULL** when homograph ambiguous |
| Form morph class | **`forms.morph_class_id`** denormalized at morphology build |
| Lexicon read model | Drop **`lexicon_entries`** / **`lexicon_forms`**; keep **`search_keys`** only |
| Lexicon CLI | Keep **`wyrdcraeft lexicon build`**; rebuilds search index only |
| Slice 1 scope | Catalog + sources + Wright § links; **no** `recognition_hints`, **no** assignment tables |
| Catalog seeding | Auto on first build if empty; **`--refresh-catalog`** to re-upsert |

---

## Phases

| Phase | Document | Delivers | Depends on |
|-------|----------|----------|------------|
| **1** | [phase-1-reference-catalog.md](./phase-1-reference-catalog.md) | Alembic migration, SQLAlchemy models, fixture loader, build hook, tests | — |
| **2** | [phase-2-lemma-assignment.md](./phase-2-lemma-assignment.md) | `lemma_morph_classes`, recognition hints, assigner → class mapping | Phase 1 gates passed |
| **3** | [phase-3-forms-link-and-query.md](./phase-3-forms-link-and-query.md) | `forms.morph_class_id`, query/lexicon surfacing, legacy column deprecation plan | Phase 2 gates passed |
| **4** | [phase-4-wright-section-text-ingest.md](./phase-4-wright-section-text-ingest.md) | Populate `wright_sections.section_text` from `wright.md` | Phase 1 gates passed (can parallelize after P1 with P2/P3 if staffed) |

**Out of scope (future):** numeral morph classes (fixture lacks them), `parent_id` hierarchy, retiring per-PoS `wright_*_paradigm_mapping.json` files (do in Phase 2 cleanup task).

---

## Subagent orchestration

### Per phase workflow

```text
1. Coordinator reads phase-N doc + 00-design-decisions.md
2. Coordinator creates TodoWrite from phase task list
3. For each task in phase:
   a. Dispatch implementer subagent (generalPurpose) with:
      - Full task text copied from plan (do not summarize)
      - Paths: doc/plans/morphology-wright-catalog/phase-N-*.md
      - AGENTS.md constraints (napoleon-gate, isolated_morphology_app_data, parity)
   b. Implementer runs quality gates listed in task
4. After ALL tasks in phase complete:
   a. Gate A — Spec review (see below)
   b. Gate B — Code review (see below)
5. Only then start next phase
```

### Gate A — Spec review (required after each phase)

Dispatch **`code-reviewer`** subagent (`readonly: true`):

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Plan: doc/plans/morphology-wright-catalog/phase-N-<name>.md
Design: doc/plans/morphology-wright-catalog/00-design-decisions.md
Diff: branch changes

Verify the implementation matches the phase spec and design decisions.
Report: missing requirements, spec deviations, wrong table/column names,
        scope creep into later phases, missing tests for stated behaviors.
Do NOT approve if recognition_hints or lemma assignment appear in Phase 1.
```

**Pass criteria:** Zero unresolved spec deviations, or explicit user-approved waivers.

### Gate B — Code review (required after each phase)

Dispatch **`bugbot`** subagent (`readonly: true`):

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Diff: branch changes
Custom Instructions: Follow AGENTS.md. Flag morphology tests that write real
  app-data DB without isolated_morphology_app_data. Flag text PK on morph_classes.
  Flag section_text duplicated on junction rows.
```

**Pass criteria:** No blocking issues; quality gate commands in phase doc all green.

### Phase validation commands (all phases)

After implementer finishes a phase, coordinator runs:

```bash
.venv/bin/ruff check <touched-py-files>
.venv/bin/mypy <touched-py-files>
make napoleon-gate
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
```

Phase 1+ additionally:

```bash
.venv/bin/pytest tests/morphology/test_morph_catalog.py -q
```

Phases touching generation must also:

```bash
.venv/bin/pytest tests/morphology -m "morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

---

## File map (expected end state)

| Path | Responsibility |
|------|----------------|
| `wyrdcraeft/models/morph_catalog.py` | SQLAlchemy models for catalog tables |
| `wyrdcraeft/db/alembic/versions/20260704_01_morph_catalog_tables.py` | Migration |
| `wyrdcraeft/services/morphology/catalog/loader.py` | Fixture → SQLite upsert |
| `wyrdcraeft/services/morphology/catalog/query.py` | Read-only catalog lookups (Phase 1 minimal) |
| `wyrdcraeft/cli/morphology.py` | `--refresh-catalog` flag on `build` |
| `tests/morphology/test_morph_catalog.py` | Catalog loader + schema tests |
| `wyrdcraeft/etc/morphology/wright_paradigms.json` | Source fixture (existing) |
| `wyrdcraeft/etc/morphology/wright-morphology-fixture.schema.json` | JSON Schema (existing) |

---

## Execution options

**1. Subagent-driven (recommended)** — one implementer subagent per task, spec + code review gates per phase.

**2. Inline** — parent agent executes phase tasks sequentially with same gates.

Start with **Phase 1** only. Do not batch phases without passing both gates.
