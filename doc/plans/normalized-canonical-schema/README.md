# Normalized Canonical Schema — Phased Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.
> One implementer subagent per task. **Do not start the next phase until Gate A, Gate B,
> and the phase commit all pass.**

**Goal:** Normalize `wyrdcraeft.sqlite3` around `parts_of_speech` and `inflection_codes`,
add real FKs on `forms` and `bt_entries`, shrink lexicon to `search_keys` only, then drop
legacy string columns.

**Architecture:** Four sequential phases (A→D) aligned with
[`docs/adr/0002-normalized-canonical-schema.md`](../../../docs/adr/0002-normalized-canonical-schema.md)
and [`doc/plans/morphology-wright-catalog/00-design-decisions.md`](../morphology-wright-catalog/00-design-decisions.md).
Each phase lands schema + code + tests together. No production backwards compatibility.

**Tech stack:** Python 3.12+, SQLAlchemy 2.x, Alembic, SQLite, Click CLI, pytest,
`isolated_morphology_app_data`, `make napoleon-gate`.

---

## Locked decisions (do not re-litigate)

| # | Decision |
|---|----------|
| 1 | `parts_of_speech` is single POS truth; product tables use FKs only |
| 2 | `forms.entry_id` NULL when homograph join ambiguous |
| 3 | Flat `inflection_codes` + `forms.inflection_code_id` |
| 4 | Drop `lexicon_entries` / `lexicon_forms`; keep slim `search_keys` |
| 5 | `forms.morph_class_id` denormalized at morphology build |
| 6 | Keep materialized `*_key` columns on `forms` |
| 7 | Two-step `forms` migration: FKs in Phase B, legacy strings out in Phase D |
| 8 | Keep CLI `wyrdcraeft lexicon build`; scope = search index only |
| 9 | Rename `lexicon_search_keys` → `search_keys`, `lexicon_build_meta` → `search_build_meta` |
| 10 | `bt_entries` headword + `pos_id` same migration as `parts_of_speech` seed |

---

## Phases

| Phase | Document | Delivers | Alembic (expected) |
|-------|----------|----------|-------------------|
| **A** | [phase-a-reference-and-dictionary.md](./phase-a-reference-and-dictionary.md) | `parts_of_speech`, `inflection_codes`, `bt_entries`/`morph_classes`/`lemma_morph_classes` POS FKs | `20260706_01` |
| **B** | [phase-b-forms-foreign-keys.md](./phase-b-forms-foreign-keys.md) | `forms` FK cols populated at sink; legacy strings remain | `20260706_02` |
| **C** | [phase-c-lexicon-shrink.md](./phase-c-lexicon-shrink.md) | Drop projection tables; rename search tables; browse reads source tables | `20260706_03` |
| **D** | [phase-d-legacy-column-drop.md](./phase-d-legacy-column-drop.md) | Drop legacy `forms` strings; refresh ER docs | `20260706_04` |

**Prerequisite:** Alembic head at `20260704_02` (lemma morph classes). Wright catalog Phases 1–2
should already be merged on the working branch.

---

## Subagent orchestration (every phase)

```text
1. Coordinator reads phase doc + ADR-0002 + 00-design-decisions.md
2. Coordinator creates TodoWrite from phase task list
3. For each task:
   a. Dispatch implementer subagent (generalPurpose) with:
      - Full task text from phase doc (do not summarize)
      - Paths under doc/plans/normalized-canonical-schema/
      - AGENTS.md constraints (napoleon-gate, isolated_morphology_app_data, parity)
   b. Implementer runs quality gates listed in task
4. After ALL tasks in phase:
   a. Run phase validation commands (coordinator)
   b. Gate A — Spec review (code-reviewer, readonly)
   c. Gate B — Code review (bugbot, readonly)
   d. Commit (coordinator) — only if A and B pass
5. Start next phase
```

---

## Gate A — Spec review (required after each phase)

Dispatch **`code-reviewer`** subagent (`readonly: true`):

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Plan: doc/plans/normalized-canonical-schema/phase-<letter>-*.md
Design: docs/adr/0002-normalized-canonical-schema.md
       doc/plans/morphology-wright-catalog/00-design-decisions.md
Diff: branch changes (uncommitted + commits since phase start)

Verify implementation matches the phase spec and locked decisions.
Report: missing requirements, wrong table/column names, scope creep into
        later phases, missing tests, free-text POS left on product tables
        when phase requires FKs.
```

**Pass criteria:** Zero unresolved spec deviations, or explicit user-approved waivers.

---

## Gate B — Code review (required after each phase)

Dispatch **`bugbot`** subagent (`readonly: true`):

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Diff: branch changes (uncommitted + commits since phase start)
Custom Instructions: Follow AGENTS.md. Flag morphology tests writing real
  app-data DB without isolated_morphology_app_data. Flag nullable entry_id
  violations (must stay NULL on ambiguous homographs). Flag dropped lexicon
  projection tables still referenced. Flag napoleon/doc-contract regressions.
```

**Pass criteria:** No blocking issues; phase validation commands all green.

---

## Phase commit (required after Gates A and B)

Coordinator runs:

```bash
git status
git diff
```

Stage only files touched in the phase. Commit with HEREDOC message from the phase doc
(**one commit per phase**). Do not batch phases into one commit.

Example:

```bash
git add <phase files>
git commit -m "$(cat <<'EOF'
Normalize schema phase A: parts_of_speech and dictionary POS FKs.

Seed reference POS/inflection tables; migrate bt_entries, morph_classes,
and lemma_morph_classes to pos_id foreign keys; rename headword column.
EOF
)"
git status
```

---

## Global validation (all phases)

After implementer finishes tasks in a phase, coordinator runs:

```bash
.venv/bin/ruff check <touched-py-files>
.venv/bin/mypy <touched-py-files>
make napoleon-gate
```

Phases touching morphology generation also:

```bash
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
.venv/bin/pytest tests/morphology -m "morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

Phases touching lexicon also:

```bash
.venv/bin/pytest tests/lexicon -q
```

Phases touching dictionary also:

```bash
.venv/bin/pytest tests/dictionary -q
```

---

## File map (expected end state)

| Path | Responsibility |
|------|----------------|
| `wyrdcraeft/models/reference.py` | `PartOfSpeech`, `InflectionCode` SQLAlchemy models |
| `wyrdcraeft/etc/morphology/parts_of_speech_seed.json` | Canonical POS seed data |
| `wyrdcraeft/etc/morphology/inflection_codes_seed.json` | Function-code seed data |
| `wyrdcraeft/services/morphology/catalog/pos.py` | Extend with `pos_id` resolvers |
| `wyrdcraeft/services/morphology/catalog/pos_seed.py` | Load/ensure POS + inflection reference rows |
| `wyrdcraeft/db/alembic/versions/20260706_01_*.py` | Phase A migration |
| `wyrdcraeft/db/alembic/versions/20260706_02_*.py` | Phase B migration |
| `wyrdcraeft/db/alembic/versions/20260706_03_*.py` | Phase C migration |
| `wyrdcraeft/db/alembic/versions/20260706_04_*.py` | Phase D migration |
| `wyrdcraeft/services/lexicon/schema.py` | `search_keys` / `search_build_meta` constants |
| `wyrdcraeft/services/lexicon/build.py` | Search-index-only rebuild |
| `wyrdcraeft/services/lexicon/query.py` | Join `bt_*` + `forms` at read time |
| `docs/adr/0002-normalized-canonical-schema.md` | Architecture decision (already accepted) |

---

## Execution options

**1. Subagent-driven (recommended)** — one implementer subagent per task; gates + commit per phase.

**2. Inline** — parent agent executes phase tasks sequentially with same gates and commits.

Start with **Phase A** only.
