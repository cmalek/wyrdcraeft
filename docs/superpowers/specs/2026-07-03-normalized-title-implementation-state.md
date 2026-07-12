# normalized_title — checkpoint 2026-07-03T12:10

## Done
- Full normalized_title pipeline (models, SQLAlchemy, loaders, sinks, lexicon join)
- `BTQueryService.lookup_by_normalized_title()` mirrors lexicon join semantics
- `MorphologyQueryService.lookup_dictionary_entries` uses normalized_title path
- Integration tests: dictionary lookup + lexicon variant join + morphology join
- CONTEXT.md glossary entries for `norm_key` and `normalized_title`
- Napoleon gate: PASS (class Args docstrings fixed in markup.py)

## Remain
- [ ] Commit Alembic migration `20260703_01_add_normalized_title_columns.py` (untracked)

## Gates (2026-07-03 follow-up)
- ruff: PASS
- mypy: PASS
- napoleon-gate: PASS
- pytest (57 in follow-up set): PASS
