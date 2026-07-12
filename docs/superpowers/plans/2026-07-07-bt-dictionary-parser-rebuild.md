# BT Dictionary Parser Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Bosworth-Toller parsing so same-spelling homographs survive as separate entries, sense structure is canonicalized without Roman labels, editorial addenda target the right source block conservatively, and packaged dictionary assets live under `wyrdcraeft/etc/dictionary/`.

**Architecture:** Keep one deterministic pipeline, but split responsibilities more cleanly: packaged dictionary resource resolution, source-block entry identity, sense-tree normalization, sense metadata classification, and conservative editorial targeting. Persist richer provenance and structure in `bt_entries`, `bt_senses`, and `bt_edit_log`, while keeping `forms.entry_id = NULL` on ambiguous dictionary joins.

**Tech Stack:** Python 3.11+, Click, SQLAlchemy 2.x, Alembic, SQLite, `importlib.resources`, pytest, `.venv/bin/ruff`, `.venv/bin/mypy`, `make napoleon-gate`.

---

## Spec anchors

- Root glossary: [`/Users/cmalek/src/workspace/wyrdcraeft/CONTEXT.md`](/Users/cmalek/src/workspace/wyrdcraeft/CONTEXT.md)
- Architecture decision: [`/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0003-bt-entry-identity-follows-source-blocks.md`](/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0003-bt-entry-identity-follows-source-blocks.md)
- Prior parser handoff: [`/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/wyrdcraeft-bt-usage-vs-sense-cleanup-handoff.md`](/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/wyrdcraeft-bt-usage-vs-sense-cleanup-handoff.md)
- Live canonical DB used for modifier mining: `~/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3`

## Locked decisions (do not re-litigate)

1. `bt_entries` identity follows Bosworth-Toller source blocks, not `(norm_key, pos)`.
2. Same-spelling same-POS homographs stay as separate `bt_entries` rows.
3. Editorial targeting is conservative:
   - explicit sense labels target one unique block/path when possible
   - otherwise target nearest preceding compatible source block
   - unresolved misses go to `parse_warnings.jsonl`
   - unresolved misses also write unapplied `bt_edit_log` rows with reasons such as `target_ambiguous` / `target_missing`
4. Canonical sense structure drops literal BT labels from normal output but keeps nesting.
5. `bt_senses` persists:
   - `order_index`
   - `sense_path`
   - `parent_path`
   - `source_label_raw`
   - `source_fragment_raw`
   - `prefix_fragment_raw`
6. Sense metadata split:
   - `modifiers_json`
   - `grammatical_context_json`
   - `usage_note`
7. Controlled `modifiers_json` includes sense-specific items such as `intransitive`, `transitive`, `weak`, `participle`, `indeclinable`, `interrogative`.
8. `grammatical_context_json` includes items such as `masculine`, `feminine`, `neuter`, `nominative`, `accusative`, `genitive`, `dative`, `instrumental`.
9. Long phrases such as `with dat. of person`, `in the phrase`, `of persons`, `of things`, `as ecclesiastical term` go to `usage_note`, not controlled vocab.
10. Bare dependency tails such as `i.e`, `of`, `for`, `belonging to` are segmentation failures first, not final cleanup.
11. Orphan/malformed source labels attach by nearest-open-ancestor depth fallback and emit warning.
12. If entry has one sense and that sense has exactly one gender context, promote that gender to `bt_entries.genders_json` only when entry-level gender is empty.
13. `forms.entry_id` stays `NULL` when dictionary match is ambiguous, even after homograph-safe rebuild.
14. Move `oe_bt.txt`, `wright.md`, and `bosworth_and_toller_abbreviations.json` into `wyrdcraeft/etc/dictionary/` and resolve defaults via `importlib.resources`, while keeping explicit CLI `--source` overrides.

## Live corpus findings to design against

Current live `bt_senses` already shows repeated bad prefixes from the canonical DB:

- editorial debris: `Add` (71), `Take here; in Dict` (111), `For; and add` (14), `Before` (7)
- inflection/gender debris: `es; m.` (125), `es; n.` (76), `e; f.` (73), `g. m. n;` (6)
- grammatical context: `nom. acc;` (38), `nom. acc; gen;` (15), bare `gen` (5)
- sense modifiers: bare `intrans` (28), `intrans. To be ...` (15), `subj. pres; To ...` (17), `part. p. Provided ...` (7)
- usage-note style prefixes: `with dat. of ...` (21), `in the phrase; ...` (10), `as ecclesiastical term, ...` (5), `of persons, ...` (6), `of things. ...` (8)

Implementation should use these as regression seeds.

## File map

### Package/runtime assets

- Create: `wyrdcraeft/etc/dictionary/oe_bt.txt`
- Create: `wyrdcraeft/etc/dictionary/wright.md`
- Create: `wyrdcraeft/etc/dictionary/bosworth_and_toller_abbreviations.json`
- Modify: `pyproject.toml`
- Create or modify: `wyrdcraeft/services/dictionary/resources.py`
- Modify: `wyrdcraeft/cli/dictionary.py`
- Modify: `wyrdcraeft/services/morphology/catalog/wright_text.py`
- Modify: `bin/build_macron_index.py`
- Modify: `bin/build_dictionary_corpus_sample.py`

### Domain/runtime models

- Modify: `wyrdcraeft/models/dictionary.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py`
- Create: `wyrdcraeft/services/dictionary/source_blocks.py`
- Create: `wyrdcraeft/services/dictionary/sense_tree.py`
- Create: `wyrdcraeft/services/dictionary/sense_metadata.py`

### Pipeline/editorial logic

- Modify: `wyrdcraeft/services/dictionary/line_parser.py`
- Modify: `wyrdcraeft/services/dictionary/sense_segmenter.py`
- Modify: `wyrdcraeft/services/dictionary/attestation_stripper.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py`
- Modify: `wyrdcraeft/services/dictionary/target_resolver.py`
- Modify: `wyrdcraeft/services/dictionary/pipeline.py`
- Modify: `wyrdcraeft/services/dictionary/llm_fix_pass.py`
- Modify: `wyrdcraeft/services/dictionary/sinks.py`

### Query/read surfaces

- Modify: `wyrdcraeft/services/dictionary/query.py`
- Modify: `wyrdcraeft/services/dictionary/browse_query.py`
- Modify: `wyrdcraeft/services/dictionary/form_decode.py` only if read DTO changes force it

### Schema

- Create: `wyrdcraeft/db/alembic/versions/20260707_03_bt_source_blocks_and_rich_senses.py`

### Tests/docs

- Modify: `tests/dictionary/test_line_parser.py`
- Modify: `tests/dictionary/test_sense_segmenter.py`
- Modify: `tests/dictionary/test_editorial_merger.py`
- Modify: `tests/dictionary/test_sinks.py`
- Modify: `tests/dictionary/test_query_service.py`
- Modify: `tests/dictionary/test_build_pipeline.py`
- Modify: `tests/dictionary/test_index_pipeline.py`
- Modify: `tests/morphology/test_wright_section_text.py`
- Modify: `tests/test_cli_dictionary.py`
- Modify: `doc/source/architecture/dictionary.rst`
- Modify: `doc/source/overview/command_dictionary_index_bt.rst`
- Modify: `docs/context/dictionary.md`

## Execution order

These tasks are coupled. Execute in order. Do not parallelize implementation tasks 2-7.

### Task 1: Move dictionary assets into packaged resources

**Files:**
- Create: `wyrdcraeft/etc/dictionary/oe_bt.txt`
- Create: `wyrdcraeft/etc/dictionary/wright.md`
- Create: `wyrdcraeft/etc/dictionary/bosworth_and_toller_abbreviations.json`
- Modify: `pyproject.toml`
- Create or modify: `wyrdcraeft/services/dictionary/resources.py`
- Modify: `wyrdcraeft/cli/dictionary.py`
- Modify: `wyrdcraeft/services/morphology/catalog/wright_text.py`
- Modify: `bin/build_macron_index.py`
- Modify: `bin/build_dictionary_corpus_sample.py`
- Test: `tests/morphology/test_wright_section_text.py`
- Test: `tests/test_cli_dictionary.py`

- [ ] **Step 1: Add packaged dictionary asset directory**

Create `wyrdcraeft/etc/dictionary/` and move:

```text
data/oe_bt.txt
data/sources/wright.md
data/bosworth_and_toller_abbreviations.json
```

Do not keep runtime code depending on `data/...` relative paths.

- [ ] **Step 2: Extend package-data config**

Modify `pyproject.toml` so wheel/sdist includes:

```toml
[tool.setuptools.package-data]
wyrdcraeft = [
  "etc/diacritic/*.json",
  "etc/diacritic/*.txt",
  "etc/diacritic/*/*.txt",
  "etc/morphology/*.txt",
  "etc/morphology/*.json",
  "etc/dictionary/*.txt",
  "etc/dictionary/*.md",
  "etc/dictionary/*.json",
]
```

- [ ] **Step 3: Add one shared dictionary resource resolver**

Implement minimal helper in `wyrdcraeft/services/dictionary/resources.py`:

```python
from importlib import resources
from pathlib import Path


def default_bt_source_path() -> Path: ...
def default_wright_source_path() -> Path: ...
def default_bt_abbreviations_path() -> Path: ...
```

Use `Path(str(resources.files("wyrdcraeft").joinpath(...)))` pattern already used by morphology defaults.

- [ ] **Step 4: Swap CLI/runtime defaults to packaged resources**

Update `wyrdcraeft/cli/dictionary.py`:

```python
def _default_source_path() -> Path:
    return default_bt_source_path()
```

Also update Wright ingest/audit default messaging if they still point users at `data/sources/wright.md`.

- [ ] **Step 5: Update helper scripts that still read old `data/...` paths**

Change `bin/build_macron_index.py` and `bin/build_dictionary_corpus_sample.py` to use the new packaged source path helper instead of hard-coded `project_root / "data" / ...`.

- [ ] **Step 6: Update tests around default path behavior**

Add/adjust assertions so CLI defaults still work when current working directory is not repo root.

Run:

```bash
.venv/bin/pytest tests/test_cli_dictionary.py tests/morphology/test_wright_section_text.py -q
```

Expected: PASS

### Task 2: Add schema support for source-block entry identity and rich senses

**Files:**
- Modify: `wyrdcraeft/models/dictionary.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py`
- Create: `wyrdcraeft/db/alembic/versions/20260707_03_bt_source_blocks_and_rich_senses.py`
- Test: `tests/dictionary/test_sinks.py`
- Test: `tests/dictionary/test_query_service.py`

- [ ] **Step 1: Write failing schema/model tests**

Add tests that prove `bt_entries` can hold two rows with same `norm_key` + same `pos_id`, and that `bt_senses` rows can round-trip rich fields:

```python
assert len(service.lookup_by_norm_key("mægeþ", pos="noun")) == 3
assert sense.sense_path == "1.2"
assert sense.source_label_raw == "IVa."
```

- [ ] **Step 2: Add new Python-domain structures first**

Update `wyrdcraeft/models/dictionary.py` so `BTSense` and `BTConsolidatedEntry` can represent:

```python
@dataclass(frozen=True)
class BTSense:
    gloss_en: str
    sense_path: str
    parent_path: str | None
    source_label_raw: str
    source_fragment_raw: str
    prefix_fragment_raw: str
    modifiers: tuple[str, ...]
    grammatical_context: tuple[str, ...]
    usage_note: str
```

Also add entry-level source-block identity fields if needed, but keep them minimal. Do not add speculative abstractions.

- [ ] **Step 3: Update SQLAlchemy models**

Modify `wyrdcraeft/models/sqlalchemy.py`:

```python
class BTEntry(Base):
    __table_args__ = (
        Index("idx_bt_entries_norm_key", "norm_key"),
        Index("idx_bt_entries_normalized_title", "normalized_title"),
        Index("idx_bt_entries_entry_order", "entry_order"),
    )
    entry_order: Mapped[int] = mapped_column(nullable=False)
```

and:

```python
class BTSense(Base):
    sense_path: Mapped[str]
    parent_path: Mapped[str | None]
    source_label_raw: Mapped[str]
    source_fragment_raw: Mapped[str]
    prefix_fragment_raw: Mapped[str]
    modifiers_json: Mapped[str]
    grammatical_context_json: Mapped[str]
    usage_note: Mapped[str]
```

Drop `UniqueConstraint("norm_key", "pos_id")`. Replace with ordering/indexes only.

- [ ] **Step 4: Write Alembic migration**

Migration must:

1. rebuild `bt_entries` without unique `(norm_key, pos_id)`
2. add `entry_order`
3. rebuild `bt_senses` with new columns
4. preserve current data best-effort for old rows:
   - `sense_path = CAST(order_index + 1 AS TEXT)`
   - `parent_path = NULL`
   - `source_label_raw = sense_label`
   - `source_fragment_raw = gloss_en`
   - `prefix_fragment_raw = ""`
   - `modifiers_json = "[]"`
   - `grammatical_context_json = "[]"`
   - `usage_note = ""`

- [ ] **Step 5: Run migration-focused tests**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_sinks.py tests/dictionary/test_query_service.py -q
```

Expected: failing tests now pass with new schema

### Task 3: Build deterministic sense-tree normalization

**Files:**
- Create: `wyrdcraeft/services/dictionary/sense_tree.py`
- Modify: `wyrdcraeft/services/dictionary/sense_segmenter.py`
- Test: `tests/dictionary/test_sense_segmenter.py`

- [ ] **Step 1: Add failing tests for label-to-path normalization**

Cover:

- Roman top-level labels
- `IVa.` / `IVc.` children
- `B. I.` style children
- out-of-order numerals
- orphan labels using nearest-open-ancestor fallback

Example:

```python
assert [s.sense_path for s in senses] == ["1", "2", "2.1", "2.3"]
assert senses[2].source_label_raw == "IVa."
```

- [ ] **Step 2: Implement one focused normalizer**

Create `SenseTreeNormalizer` in `sense_tree.py`:

```python
class SenseTreeNormalizer:
    def normalize(self, fragments: list[RawSenseFragment]) -> list[CanonicalSenseFragment]:
        ...
```

Responsibilities only:

- infer depth from source label form
- assign canonical `sense_path` in encounter order
- preserve `source_label_raw`
- apply nearest-open-ancestor fallback
- emit warning metadata for fallback cases

Do not let this class strip attestations or parse modifiers.

- [ ] **Step 3: Refactor segmenter to use tree normalizer**

`BTSenseSegmenter` should:

1. split raw body into source fragments
2. normalize fragment tree/path
3. pass each fragment through gloss cleanup + metadata classification
4. return rich `BTSense` rows

Keep Roman-label parsing local to this stage only.

- [ ] **Step 4: Verify tree normalization tests**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_sense_segmenter.py -q
```

Expected: PASS for new path/fallback cases

### Task 4: Add sense prefix classifier for modifiers, grammatical context, and usage notes

**Files:**
- Create: `wyrdcraeft/services/dictionary/sense_metadata.py`
- Modify: `wyrdcraeft/services/dictionary/attestation_stripper.py`
- Modify: `wyrdcraeft/services/dictionary/sense_segmenter.py`
- Test: `tests/dictionary/test_sense_segmenter.py`

- [ ] **Step 1: Add focused failing tests from real bad prefixes**

Use representative live cases:

```python
assert sense.modifiers == ("intransitive",)
assert sense.grammatical_context == ("feminine",)
assert sense.usage_note == "with dative of person"
assert sense.gloss_en == "An offence, wrong, anger"
```

Explicitly cover:

- `e; f.`
- `es; m.`
- `nom. acc;`
- `g.`
- `dat.`
- `part.`
- `indecl`
- `with dat. of person`
- `in the phrase`
- `as ecclesiastical term`

- [ ] **Step 2: Implement a single metadata classifier**

Create:

```python
class SenseMetadataClassifier:
    def classify(self, text: str) -> SenseMetadata:
        ...
```

Normalization rules:

- `intrans.` -> `intransitive`
- `trans.` -> `transitive`
- `wk.` -> `weak`
- `part.` -> `participle`
- `indecl.` -> `indeclinable`
- `nom.` -> `nominative`
- `acc.` -> `accusative`
- `gen.` / `g.` -> `genitive`
- `dat.` -> `dative`
- `m.` / `f.` / `n.` -> `masculine` / `feminine` / `neuter`
- `instr.` / `inst.` if present -> `instrumental`

Drop inflection endings such as `e`, `es`, `an`, etc. unless future evidence proves otherwise.

- [ ] **Step 3: Keep local-only attachment rule**

Implement strict rule:

- `intrans. To break` -> same sense, modifier attached
- `To break, intrans.` -> same sense, modifier attached
- bare `intrans.` -> no sense row, warning only
- no borrowing across neighboring fragments

- [ ] **Step 4: Capture provenance fields**

Ensure final `BTSense` row includes:

- `source_fragment_raw`
- `prefix_fragment_raw`
- `source_label_raw`

These are for debugging/provenance, not primary UI.

- [ ] **Step 5: Re-run rich sense-segmentation tests**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_sense_segmenter.py -q
```

Expected: PASS

### Task 5: Refactor editorial merge around source blocks and canonical sense paths

**Files:**
- Create: `wyrdcraeft/services/dictionary/source_blocks.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py`
- Modify: `wyrdcraeft/services/dictionary/target_resolver.py`
- Modify: `wyrdcraeft/models/dictionary.py`
- Test: `tests/dictionary/test_editorial_merger.py`

- [ ] **Step 1: Add failing homograph-preservation tests**

Add real `mǣgþ`-style coverage with separate same-POS entries:

```python
assert len(entries) == 3
assert [e.senses[0].gloss_en for e in entries] == [
    "A maid, virgin, girl, maiden, woman",
    "Importunate desire, ambition",
    "A collection of kinsmen, a family",
]
```

- [ ] **Step 2: Introduce source-block grouping before merge**

Add one class, likely:

```python
class BTSourceBlockBuilder:
    def build(self, parsed_lines: list[ParsedBTLine]) -> list[BTSourceBlock]:
        ...
```

Responsibilities:

- preserve source-order entry blocks
- attach nearby `ADD` / `SUBSTITUTE` / `DELE` lines to candidate blocks
- keep same-spelling same-POS blocks separate

- [ ] **Step 3: Make editorial merge target canonical paths, not raw Roman labels**

Once block chosen, edit operations should resolve labels via canonical paths:

- `I` -> `1`
- `IVa` -> `4.1`
- `IVc` -> `4.3`

No downstream code should need to understand Roman labels.

- [ ] **Step 4: Implement conservative target resolution**

Rules:

1. explicit label -> unique block/path when possible
2. else nearest preceding compatible block
3. else unresolved warning + unapplied edit log

No guessing across ambiguous same-headword homographs.

- [ ] **Step 5: Re-run merger tests**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_editorial_merger.py -q
```

Expected: PASS, including new homograph cases

### Task 6: Expand warning and audit plumbing

**Files:**
- Modify: `wyrdcraeft/services/dictionary/pipeline.py`
- Modify: `wyrdcraeft/services/dictionary/llm_fix_pass.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py`
- Modify: `wyrdcraeft/services/dictionary/sinks.py`
- Test: `tests/dictionary/test_build_pipeline.py`
- Test: `tests/dictionary/test_index_pipeline.py`
- Test: `tests/dictionary/test_llm_fix_pass.py`

- [ ] **Step 1: Add failing tests for new warning reasons**

Cover:

- `modifier_only_fragment`
- `editorial_fragment_without_gloss`
- `orphan_source_label_depth_fallback`
- `target_missing`
- `target_ambiguous`

- [ ] **Step 2: Emit parse warnings from the right stage**

Segmentation/root-cause issues should come from parser/segmenter stage, not from final query rendering.

Examples:

- dependency tails like `poor wretches, i.e` -> segmentation warning, no stored sense
- bare `Add` / `Before` -> editorial warning, no stored sense

- [ ] **Step 3: Persist unapplied edit rows with clear reasons**

Update `BTEditRecord.note` / `scope` usage so unapplied `bt_edit_log` rows carry machine-friendly reasons:

```python
note="target_ambiguous"
note="target_missing"
```

Keep human-readable context too.

- [ ] **Step 4: Keep `parse_warnings.jsonl` compatible with LLM repair pass**

Extend `BTParseWarning` carefully so existing JSONL repair machinery still loads warning rows. If needed, add optional fields instead of breaking required ones.

- [ ] **Step 5: Re-run build/warning tests**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_build_pipeline.py tests/dictionary/test_index_pipeline.py tests/dictionary/test_llm_fix_pass.py -q
```

Expected: PASS

### Task 7: Update sink and query layers for rich senses and duplicate homographs

**Files:**
- Modify: `wyrdcraeft/services/dictionary/sinks.py`
- Modify: `wyrdcraeft/services/dictionary/query.py`
- Modify: `wyrdcraeft/services/dictionary/browse_query.py`
- Test: `tests/dictionary/test_sinks.py`
- Test: `tests/dictionary/test_query_service.py`
- Test: `tests/dictionary/test_browse_query.py`

- [ ] **Step 1: Add failing round-trip tests for rich sense rows**

Verify sink writes and query reads:

- multiple same-`norm_key` same-POS entries
- `sense_path`
- `parent_path`
- `source_label_raw`
- JSON-decoded modifiers / grammatical context
- `usage_note`

- [ ] **Step 2: Update sink serialization**

`BTSqliteSink.write_entries()` must JSON-encode list fields and preserve source order:

```python
json.dumps(list(sense.modifiers), ensure_ascii=False)
json.dumps(list(sense.grammatical_context), ensure_ascii=False)
```

Also write `entry_order` on `bt_entries`.

- [ ] **Step 3: Update query loaders**

`BTQueryService` and browse loaders should materialize rich `BTSense` objects but keep outward-facing user output compact by default:

- no normal display of `source_label_raw`
- no normal display of provenance fragments unless explicitly requested later

- [ ] **Step 4: Keep ambiguous morphology join behavior unchanged**

Do not change `forms.entry_id` policy. Add regression test if necessary.

- [ ] **Step 5: Run read/write query tests**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_sinks.py tests/dictionary/test_query_service.py tests/dictionary/test_browse_query.py -q
```

Expected: PASS

### Task 8: Corpus-driven regression coverage for real weird senses

**Files:**
- Modify: `tests/dictionary/test_sense_segmenter.py`
- Modify: `tests/dictionary/test_editorial_merger.py`
- Modify: `tests/dictionary/test_index_pipeline.py`
- Modify: `tests/fixtures/dictionary/golden_senses.jsonl`
- Modify: `tests/fixtures/dictionary/golden_merged.jsonl`

- [ ] **Step 1: Add representative regression cases from live corpus**

Include at least one test each for:

- `mǣgþ` multi-entry homographs
- `e; f.` cleanup
- `es; m.` cleanup
- `nom. acc;` grammatical context
- `part.` -> `participle`
- `indecl` -> `indeclinable`
- `with dat. of person` -> `usage_note`
- dependency tail parse failure such as `poor wretches, i.e`
- editorial `Before` / `and add` fragment that should warn, not store

- [ ] **Step 2: Refresh golden fixtures only where deterministic output intentionally changes**

Do not broad-rewrite fixtures. Update only records affected by:

- sense-path output
- homograph separation
- cleaned gloss / metadata split

- [ ] **Step 3: Re-run dictionary test suite**

Run:

```bash
.venv/bin/pytest tests/dictionary -q
```

Expected: PASS

### Task 9: Documentation and operator-facing cleanup

**Files:**
- Modify: `doc/source/architecture/dictionary.rst`
- Modify: `doc/source/overview/command_dictionary_index_bt.rst`
- Modify: `docs/context/dictionary.md`
- Modify: `README.md` only if user-visible default paths are mentioned

- [ ] **Step 1: Update runtime-path docs**

Replace `data/oe_bt.txt` / `data/sources/wright.md` default claims with packaged-resource wording plus explicit `--source` override examples.

- [ ] **Step 2: Document new parser behavior**

Explain:

- source-block entry identity
- homograph preservation
- canonical sense paths
- warning/audit behavior
- `parse_warnings.jsonl` + `bt_edit_log` interplay

- [ ] **Step 3: Keep docs honest about ambiguity**

State clearly that:

- `forms.entry_id` remains `NULL` when ambiguous
- canonical sense labels are internal paths, not literal BT numerals

### Task 10: Full validation and handoff

**Files:**
- No planned code changes unless validation reveals bug

- [ ] **Step 1: Run focused quality gates on touched Python files**

Run:

```bash
.venv/bin/ruff check \
  wyrdcraeft/services/dictionary \
  wyrdcraeft/models/dictionary.py \
  wyrdcraeft/models/sqlalchemy.py \
  wyrdcraeft/services/morphology/catalog/wright_text.py \
  bin/build_macron_index.py \
  bin/build_dictionary_corpus_sample.py
```

Expected: PASS

- [ ] **Step 2: Run mypy on touched Python files**

Run:

```bash
.venv/bin/mypy \
  wyrdcraeft/services/dictionary \
  wyrdcraeft/models/dictionary.py \
  wyrdcraeft/models/sqlalchemy.py \
  wyrdcraeft/services/morphology/catalog/wright_text.py
```

Expected: PASS

- [ ] **Step 3: Run required doc gate**

Run:

```bash
make napoleon-gate
```

Expected: PASS

- [ ] **Step 4: Run full dictionary regression**

Run:

```bash
.venv/bin/pytest tests/dictionary tests/test_cli_dictionary.py tests/morphology/test_wright_section_text.py -q
```

Expected: PASS

- [ ] **Step 5: Rebuild dictionary on isolated app-data and inspect warnings**

Run:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-bt-rebuild \
  .venv/bin/wyrdcraeft dictionary build --with-morphology \
  --warnings-file /tmp/wc-bt-rebuild/parse_warnings.jsonl
```

Expected:

- build succeeds
- homograph entries survive in DB
- warnings file contains unresolved editorial / modifier-only / fallback cases, not garbage sense rows

- [ ] **Step 6: Capture post-build verification queries**

Run:

```bash
sqlite3 "/tmp/wc-bt-rebuild/wyrdcraeft.sqlite3" \
  "select norm_key, count(*) from bt_entries group by norm_key having count(*) > 1 order by count(*) desc limit 20;"
sqlite3 "/tmp/wc-bt-rebuild/wyrdcraeft.sqlite3" \
  "select source_label_raw, sense_path, gloss_en from bt_senses where entry_id in (select id from bt_entries where norm_key='mægeþ');"
```

Expected:

- duplicate `norm_key` rows now exist legitimately for homographs
- `mægeþ` shows separate entries/sense paths instead of one merged blob

## Commit strategy

Keep commits bite-sized and reviewable:

1. package resources move
2. schema/models
3. sense tree + metadata parser
4. editorial/source-block merge
5. query/sink adaptation
6. docs/final cleanup

Do not batch all parser work into one mega-commit.

## Review loop

After plan save, use one plan-document reviewer subagent before execution. Review against:

- this plan file
- `CONTEXT.md`
- `docs/adr/0003-bt-entry-identity-follows-source-blocks.md`
- `docs/superpowers/specs/wyrdcraeft-bt-usage-vs-sense-cleanup-handoff.md`

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-bt-dictionary-parser-rebuild.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints
