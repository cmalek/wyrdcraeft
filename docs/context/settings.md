# Settings Context

## What This Capability Does

Settings control CLI defaults, output rendering, and application data path
overrides. LLM and OCR settings are not part of this repo (ADR 0007, ADR 0010).

## Main CLI Entrypoints

- global options on `wyrdcraeft`
- `wyrdcraeft settings`
- `wyrdcraeft settings show`
- `wyrdcraeft settings create`

## Primary Python Entrypoints

- `wyrdcraeft.cli.cli`
- `wyrdcraeft.cli.settings`
- `wyrdcraeft.settings:Settings`
- `wyrdcraeft.paths`

## Key Files

- `wyrdcraeft/cli/cli.py`
- `wyrdcraeft/cli/settings.py`
- `wyrdcraeft/settings.py`
- `wyrdcraeft/paths.py`
- `doc/source/overview/configuration_cli.rst`

## Inputs And Outputs

Inputs:

- CLI flags such as `--verbose`, `--quiet`, `--config-file`, `--output`
- environment variables prefixed with `WYRDCRAEFT_`
- TOML config files

Outputs:

- in-memory `Settings` object stored on click context
- optional `.wyrdcraeft.toml` file from `settings create`
- indirect filesystem effects through app-data path resolution

## Invariants And Sharp Edges

- CLI bootstraps `Settings()` once in root command and stores it on context.
- `--config-file` is passed by setting `WYRDCRAEFT_CONFIG_FILE` before settings
  load.
- Current `Settings.settings_customise_sources` code path deserves close reading
  before changing config precedence semantics.
- App-data override affects default morphology and dictionary SQLite locations.
- `settings create` currently writes JSON text to `.wyrdcraeft.toml`; treat this
  as current behavior, not polished config UX.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/morphology.md](morphology.md)
- [../context/dictionary.md](dictionary.md)
