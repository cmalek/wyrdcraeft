# Morphology Context

## What This Capability Does

Morphology generates inflected Old English forms, writes lookup artifacts, and
supports query-time retrieval of those forms.

## Main CLI Entrypoints

- `wyrdcraeft morphology generate`
- `wyrdcraeft morphology query`

## Primary Python Entrypoints

- `wyrdcraeft.cli.morphology`
- `wyrdcraeft.services.morphology.session:GeneratorSession`
- `wyrdcraeft.services.morphology.processors`
- `wyrdcraeft.services.morphology.generation.dispatch`
- `wyrdcraeft.services.morphology.generation.query:MorphologyQueryService`
- `wyrdcraeft.paths:resolve_morphology_index_db_path`

## Key Files

- `wyrdcraeft/cli/morphology.py`
- `wyrdcraeft/paths.py`
- `wyrdcraeft/services/morphology/processors.py`
- `wyrdcraeft/services/morphology/session.py`
- `wyrdcraeft/services/morphology/generation/dispatch.py`
- `wyrdcraeft/services/morphology/generation/query.py`
- `doc/source/overview/command_morphology_generate.rst`
- `doc/source/overview/command_morphology_query.rst`
- `doc/source/overview/morphology_perl_quirks_ledger.rst`

## Inputs And Outputs

Inputs:

- bundled morphology source files under `wyrdcraeft/etc/morphology`
- optional overrides for dictionary, manual forms, paradigms, and prefixes
- optional output/index path overrides

Outputs:

- TSV form output
- SQLite lookup DB `morphology.sqlite3`
- optional query results in text or JSON

## Invariants And Sharp Edges

- Default output behavior writes real app-data `morphology.sqlite3`.
- Tests that touch default-path generation must isolate app-data writes.
- Current generation code is parity-sensitive with historical Perl behavior; read
  quirks ledger before “cleaning up” surprising output.
- Query behavior can optionally attach dictionary data; morphology and
  dictionary are separate capabilities but share lookup join points.
- Main orchestration is spread across session/setup/dispatch helpers; changes to
  one stage can ripple into parity baselines.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/dictionary.md](dictionary.md)
- [../context/settings.md](settings.md)

