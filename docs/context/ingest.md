# Ingest Context

## What This Capability Does

Ingest converts Old English source material into structured document JSON.
Current paths are:

- deterministic heuristic ingest
- TEI/XML ingest
- optional LLM-assisted ingest

## Main CLI Entrypoints

- `wyrdcraeft source convert <source> <output>`

## Primary Python Entrypoints

- `wyrdcraeft.cli.source:reading_convert`
- `wyrdcraeft.ingest.pipeline:DocumentIngestor`
- `wyrdcraeft.ingest.loaders`
- `wyrdcraeft.ingest.extractors`
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

- local source files
- `http://` and `https://` source references
- optional title override
- optional LLM settings overrides

Outputs:

- one JSON file written to caller-provided path

## Invariants And Sharp Edges

- `source convert` is CLI-first; output path is always explicit.
- Local file inputs must exist before conversion starts.
- Remote source handling is wired through `source` string detection, not a
  separate command.
- LLM extraction remains optional and is not default path.
- Root pipeline decision point lives in `DocumentIngestor.ingest`; shared ingest
  behavior should usually be fixed there, not in one caller.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/settings.md](settings.md)

