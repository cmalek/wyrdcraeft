# Morphology build performance session (2026-07-03)

Handoff note for continuing morphology build optimization work.

## Problem

Full `wyrdcraeft morphology build --full` was taking ~45 minutes. Goal: understand
bottlenecks and reduce wall time without breaking Perl parity.

Scale (full dictionary):

- ~13.6M emitted form rows
- ~1.7 GB TSV
- ~35K dictionary source words

## Root cause (initial analysis)

Primary bottleneck was **SQLite write path**, not CPU generation:

- `SqliteIndexSink.emit_rows()` opened a **new transaction per form emit** (1–2 rows)
- ~13M transactions updating **6 text indexes** on `forms`
- Generation alone (subset baseline) ≈ 177 ms for 41K rows → extrapolated ~1 min for full dict
- Lexicon build already batches at 25K rows; morphology did not

Secondary bottleneck (discovered after SQLite fix): **setup paradigm assignment**

- `set_adj_paradigm()` had O(n²) stem comparison over full word list (~100s)
- `set_noun_paradigm()` stem propagation was O(n²) in places (~33s)

Current dominant stage: **adjective generation** (~92% of rows, ~12.5M forms).

## Changes implemented

### 1. Batched SQLite sink + bulk PRAGMAs (kept)

File: `wyrdcraeft/services/morphology/generation/sinks.py`

- Buffer **25,000 rows** before bulk insert (matches lexicon pattern)
- Flush remainder on `close()`
- PRAGMAs at sink open: `journal_mode=WAL`, `synchronous=OFF`, `temp_store=MEMORY`,
  `cache_size=-64000`
- Optional `sqlite_flush_observer` callback for timing

### 2. Deferred indexes (reverted)

Attempted: drop 6 lookup indexes during load, recreate on `close()`.

Result: **slower** (~19 min vs ~12.5 min). Building 6 indexes on 13.6M text rows at
end cost more than incremental batch updates during insert. Reverted; batched inserts
remain the sweet spot.

### 3. Built-in build profiling (`--profile`)

Files:

- `wyrdcraeft/services/morphology/build_profile.py`
- `wyrdcraeft/cli/morphology.py` (flag wiring)

```bash
wyrdcraeft --quiet morphology build --full --profile
```

Prints stderr summary: per-stage wall time, row counts, setup steps, cumulative
`sqlite_flush` time, total.

### 4. O(n) paradigm assignment (kept)

Files:

- `wyrdcraeft/services/morphology/assigners/adj.py` — stem→paradigm map replaces O(n²) loop
- `wyrdcraeft/services/morphology/assigners/noun.py` — `_NounAssignedIndex` for O(1) exact
  stem + O(1) advanced variant lookup by first assigned index

Tests: `tests/morphology/test_assigner_branches.py` (+ adj stem propagation case)

### 5. Adjective stage cProfile script

File: `scripts/morphology/profile_adj_stage.py`

Runs manual + verb prerequisite stages, then cProfiles `generate_adjforms` only.

```bash
# Full dict, TSV-only (cleanest CPU view)
.venv/bin/python scripts/morphology/profile_adj_stage.py --top 40

# With SQLite (production-like)
.venv/bin/python scripts/morphology/profile_adj_stage.py --with-sqlite --top 40

# Subset smoke
.venv/bin/python scripts/morphology/profile_adj_stage.py --subset --top 25
```

Output: pstats table + `$TMPDIR/wyrdcraeft_adj_stage.prof`

## Timing progression (user-measured, full build)

| Stage of work              | real (approx) | Notes                          |
|----------------------------|---------------|--------------------------------|
| Baseline (per user)        | ~45 min       | Before any changes             |
| Batched SQLite + PRAGMAs   | ~12.5 min     | First big win (~3.6×)          |
| + deferred indexes         | ~19 min       | Reverted (regression)          |
| Batched only (restored)    | ~13.7 min     | After revert                   |
| + O(n) paradigm assignment | ~10.4 min     | Setup 148s → 16s               |

Latest profiled build (`--profile`, 2026-07-03 ~17:04 local):

```
total             618.98s   (~10.3 min)
setup              16.10s
sqlite_flush      337.99s
adj stage           493.40s   (12,561,991 rows)
verbs                72.16s
nouns                30.71s
manual/adv/num         ~3s
```

Setup breakdown after O(n) fix:

- assign adjective paradigms: **0.10s** (was ~100s)
- assign noun paradigms: **1.17s** (was ~33s)
- assign verb paradigms: **14.26s** (still visible; check for O(n²))

## cProfile: adjective stage (full dict, TSV-only)

Run date: 2026-07-03. Script: `profile_adj_stage.py` (no SQLite).

| Metric              | Value        |
|---------------------|--------------|
| adj CPU (cProfile)  | 212.69s      |
| adj wall (build)    | ~493s        |
| adj rows            | 12,561,991   |
| function calls      | ~802M        |

Wall − CPU ≈ **~280s** → SQLite + I/O during real build (matches `sqlite_flush` share).

### Top CPU hotspots (cumtime, TSV-only)

| Function / area                         | cumtime | Notes                          |
|-----------------------------------------|---------|--------------------------------|
| `print_one_form` / `emit_form_data`     | ~183s   | 11.5M calls; every row         |
| `_gen_superlative`                      | **117s**| 36K calls — **#1 adj logic**     |
| `_gen_comparative`                      | **47s** | 36K calls — **#2 adj logic**   |
| `normalize_output`                      | 64s     | 11.5M calls                    |
| `_row_from_form_data` + Pydantic        | ~70s    | FormRow validate per row       |
| `_gen_weak`                             | 27s     |                                |
| `re.sub` / compile (scattered)          | ~50s+   |                                |

**~77% of adj CPU** in `_gen_superlative` + `_gen_comparative`.

## Decisions / non-goals

- **ProcessPool**: deferred until adj CPU profiled; SQLite was main issue first; adj gen
  is now the CPU story but superlative/comparative should be optimized before multiprocessing
- **Deferred indexes**: wrong shape for this workload (6 wide text indexes × 13.6M rows)
- **Lexicon build**: out of scope for this session (~30 min separate concern)

## Recommended next steps (priority order)

1. **Deep-dive `_gen_superlative` / `_gen_comparative`** in
   `wyrdcraeft/services/morphology/generation/adj_forms.py` — 77% of adj CPU
2. **Check `set_verb_paradigm`** for O(n²) like adj had (~14s setup)
3. **FormRow hot path** — Pydantic validation ~70s on 12.5M rows; lighter emit struct?
4. **`normalize_output` caching** — 64s, 11.5M calls
5. **SQLite tuning** — larger batch size (50K–100K)? diminishing returns (~10–15%)
6. **ProcessPool** — only if adj CPU still >40% wall after #1–4; requires ordered counter
   merge + parity care

## Key files

| Path | Role |
|------|------|
| `wyrdcraeft/services/morphology/generation/sinks.py` | Batched SQLite sink |
| `wyrdcraeft/services/morphology/build_profile.py` | `--profile` timing |
| `wyrdcraeft/cli/morphology.py` | build command, `--profile` flag |
| `wyrdcraeft/services/morphology/assigners/adj.py` | O(n) adj paradigm assign |
| `wyrdcraeft/services/morphology/assigners/noun.py` | `_NounAssignedIndex` |
| `wyrdcraeft/services/morphology/generation/adj_forms.py` | Adj gen hot path |
| `scripts/morphology/profile_adj_stage.py` | Adj-only cProfile |

## Commands to reproduce

```bash
# Timed full build with stage summary
/usr/bin/time -p wyrdcraeft --quiet morphology build --full --profile

# Adj stage cProfile (full dict)
.venv/bin/python scripts/morphology/profile_adj_stage.py --top 40

# Quality gates (after Python edits)
.venv/bin/ruff check <touched files>
.venv/bin/mypy <touched files>
make napoleon-gate
.venv/bin/pytest tests/morphology/test_assigner_branches.py tests/morphology/test_build_profile.py -q
```

## Parity constraints

- Perl parity is non-negotiable for morphology output
- `tests/morphology/data/refactor_baseline.json` must remain unchanged for refactor guardrails
- Morphology tests: use `isolated_morphology_app_data` fixture for DB writes in tests
