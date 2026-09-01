# Ingest Context

## What This Capability Does

Ingest converts Old English source material into structured document JSON.
Current paths are:

- deterministic heuristic ingest (local `.txt`)
- TEI/XML ingest

LLM-assisted ingest, HTML/PDF/`unstructured`, and HTTP fetch are out of this
repo (ADR 0010). ML and messy-document work live in `wordwending`.

## Main CLI Entrypoints

- `wyrdcraeft source convert <source> <output>`

## Primary Python Entrypoints

- `wyrdcraeft.cli.source:reading_convert`
- `wyrdcraeft.ingest.pipeline:DocumentIngestor`
- `wyrdcraeft.ingest.loaders`
- `wyrdcraeft.ingest.normalizers`
- `wyrdcraeft.ingest.exporters`

## Key Files

- `wyrdcraeft/cli/source.py`
- `wyrdcraeft/ingest/pipeline.py`
- `wyrdcraeft/models.py`
- `doc/source/overview/using_cli.rst`
- `doc/source/overview/format.rst`

## Inputs And Outputs

Inputs:

- local TEI/XML or `.txt` files
- optional title override

Outputs:

- one JSON file written to caller-provided path

## Invariants And Sharp Edges

- `source convert` is CLI-first; output path is always explicit.
- Local file inputs must exist before conversion starts.
- Convert does not fetch URLs or call an LLM.
- Root pipeline decision point lives in `DocumentIngestor.ingest`; shared ingest
  behavior should usually be fixed there, not in one caller.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/settings.md](settings.md)

