# normalized_title + lexicon browse — checkpoint 2026-07-03T12:15

## User requirement (confirmed)

| Layer | Normalizer | Status |
|-------|------------|--------|
| Lexicon browse search + search-key index | `normalize_old_english` | Verified unchanged |
| Form ↔ BT entry join at lexicon build | `normalized_title` | Implemented |

## Done this session

- Regression tests: `_search_candidate_keys` strips macrons; `abbod`/`abbōd`/`ABBOD` search → abbad
- CONTEXT.md: `lexicon browse search normalization` glossary entry
- `build.py` Note blocks documenting the split in `_select_entry_id` and `_build_search_keys`
- Full normalized_title feature + follow-ups (see prior checkpoint)

## Gates

- ruff, mypy, napoleon-gate, lexicon query tests: PASS

## Ready to commit

All product files + Alembic migration `20260703_01_add_normalized_title_columns.py`.
Exclude `.aidex/index.db` from commit.
