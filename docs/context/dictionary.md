# Dictionary Context

## What This Capability Does

Dictionary workflows parse Bosworth-Toller source text into SQLite lookup data
and expose lookup helpers for dictionary-only and morphology-joined queries.

## Main CLI Entrypoints

- `wyrdcraeft dictionary index-bt`
- `wyrdcraeft dictionary lookup`

## Primary Python Entrypoints

- `wyrdcraeft.cli.dictionary`
- `wyrdcraeft.services.dictionary.pipeline:BTIndexPipeline`
- `wyrdcraeft.services.dictionary.query:BTQueryService`
- `wyrdcraeft.paths:resolve_morphology_index_db_path`

## Key Files

- `wyrdcraeft/cli/dictionary.py`
- `wyrdcraeft/paths.py`
- `wyrdcraeft/services/dictionary/pipeline.py`
- `wyrdcraeft/services/dictionary/line_parser.py`
- `wyrdcraeft/services/dictionary/sense_segmenter.py`
- `wyrdcraeft/services/dictionary/editorial_merger.py`
- `wyrdcraeft/services/dictionary/query.py`

## Inputs And Outputs

Inputs:

- Bosworth-Toller source text, default `data/oe_bt.txt`
- optional report output
- optional warning log path
- optional LLM fix pass for warning lines
- optional attach target: existing morphology SQLite DB

Outputs:

- attached `bt_*` tables inside `morphology.sqlite3` by default
- or a standalone `dictionary.sqlite3` with `--standalone`
- optional JSON report and parse warnings file

## Invariants And Sharp Edges

- Default mode attaches `bt_*` tables to an existing morphology database and
  preserves `forms`.
- `--standalone` writes a fresh `dictionary.sqlite3` instead.
- `--index-db` / `--index-dir` target `morphology.sqlite3` by default, or
  `dictionary.sqlite3` with `--standalone`.
- Dictionary lookup normalizes forms; display spelling and normalized key are
  intentionally different concerns.
- Dictionary indexing is separate from morphology generation even when data is
  later attached into one SQLite file.
- Optional LLM repair path is warning-only, not primary parser path.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/morphology.md](morphology.md)
