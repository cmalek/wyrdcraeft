# Phase 4 — Wright Section Text Ingest

> **Prerequisites:** Phase 1 gates passed (may run in parallel with Phase 2/3 after P1)  
> **REQUIRED SUB-SKILL:** subagent-driven-development

**Goal:** Populate `wright_sections.section_text` from `data/sources/wright.md` so UI can show Wright paragraph text without runtime file parsing.

**Architecture:** `WrightSectionTextIngester` parses `§ N.` headings from markdown; upserts text into existing `wright_sections` rows; idempotent; optional CLI subcommand.

---

## Task 1: Section parser

**Files:**
- Create: `wyrdcraeft/services/morphology/catalog/wright_text.py`
- Test: `tests/morphology/test_wright_section_text.py`

- [ ] Parse `data/sources/wright.md` — sections marked `§ 334.` or `§ 334` at line start
- [ ] Capture body text until next § heading
- [ ] Normalize whitespace; preserve OE characters
- [ ] Return `dict[int, str]` mapping `section_no` → text
- [ ] Test against known §334 snippet (masculine a-stem intro)

---

## Task 2: DB upsert

**Files:**
- Modify: `wyrdcraeft/services/morphology/catalog/loader.py` or create `wright_text_ingest.py`

- [ ] `WrightSectionTextIngester.ingest(engine, md_path) -> IngestResult`
- [ ] Update only rows where `section_text IS NULL` unless `--force` 
- [ ] Warn on § numbers in markdown not in `wright_sections` table
- [ ] Warn on catalog § rows still NULL after ingest

---

## Task 3: CLI hook

**Files:**
- Modify: `wyrdcraeft/cli/morphology.py`

- [ ] Option A: `wyrdcraeft morphology ingest-wright-text --source data/sources/wright.md`
- [ ] Option B: auto after catalog seed when `section_text` all null
- [ ] Document chosen behavior in command help

---

## Task 4: Query enrichment

**Files:**
- Modify: `wyrdcraeft/services/morphology/catalog/query.py`

- [ ] Include `section_text` in Wright section detail (truncate in CLI if > N chars; full in JSON)

---

## Phase 4 validation

```bash
.venv/bin/pytest tests/morphology/test_wright_section_text.py -q
.venv/bin/ruff check wyrdcraeft/services/morphology/catalog/
.venv/bin/mypy wyrdcraeft/services/morphology/catalog/
make napoleon-gate
```

Spot-check: §334 text non-empty after ingest; stored once (not per morph class).

---

## Phase 4 — Gate A: Spec review

Verify:

- Text on `wright_sections`, not junction
- No duplicate text across morph classes sharing a §
- Parser handles Wright markdown format in repo

## Phase 4 — Gate B: Code review

Standard bugbot pass.

---

## Known limitations

- `wright.md` may not cover all 196 § in fixture — document coverage % in ingest summary
- Multiple Wright editions — `work` column distinguishes source
