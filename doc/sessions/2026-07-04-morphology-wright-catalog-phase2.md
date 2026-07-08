# Session: Morphology Wright Catalog — Phase 2 complete

**Date:** 2026-07-04  
**Branch:** `codex/canonical-db-migration`

## Summary

Phase 2 (lemma assignment + read API) is complete and passed Gate A/B review.
Phase 1 reference catalog was prerequisite.

## Deliverables

| Task | Commit(s) | Key files |
|------|-----------|-----------|
| 1 Schema + migration | `0a66a51` | `20260704_02`, `LemmaMorphClass`, `recognition_hints_json` |
| 2 POS normalization | `1db38d7` | `catalog/pos.py` |
| 3 Paradigm mapper | `f392cee`, `1f7f5c4` | `catalog/paradigm_map.py`, `paradigm_exemplar_map.json` |
| 4 Assignment engine | `41ffbd2` | `catalog/assigner.py`, CLI hook |
| 5 Read API | `adea92c` | `catalog/query.py`, `MorphClassView` |
| Gate B fix | `b9b1d65` | Honor `--data-dir` / `--verbal-paradigms` in mapper |
| DB naming | `f366f3b` | Makefile/tests use `wyrdcraeft.sqlite3` |

## Architecture

- Assignment key: `(normalized_title, pos)` using catalog POS vocabulary
- Priority: paradigm/`paraID` → features → Wright § (≥330) → skip (no row)
- Participles: dictionary `pspart`/`papart` lemmas → `(title, adjective)` with
  participial `class_key`; pure verb lemmas → `(title, verb)`
- Source contract: `wright_paradigms.json` + `para_vb.txt`; not legacy
  `wright_*_paradigm_mapping.json`

## Validation

```bash
.venv/bin/pytest tests/morphology/test_morph_catalog.py \
  tests/morphology/test_morph_catalog_pos.py \
  tests/morphology/test_paradigm_map.py \
  tests/morphology/test_lemma_morph_assignment.py \
  tests/morphology/test_morph_catalog_query.py -q
# 61+ tests passed at gate time; refactor_baseline.json unchanged
```

## Known limitations (deferred)

- Verb-generated participles in `session.adjectives` not assigned at build time
- Dual-POS dictionary rows get one assignment pass (first matching POS flag)
- `forms.morph_class_id` FK — Phase 3
- Stale `lemma_morph_classes` rows not pruned on rebuild

## Next

Phase 3: link generated forms to morph classes; lexicon/query integration.
