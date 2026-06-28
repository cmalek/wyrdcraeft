# Diacritic Context

## What This Capability Does

Diacritic workflows restore, curate, and disambiguate Old English forms with
macrons and related normalization helpers.

This capability spans both text restoration and index maintenance.

## Main CLI Entrypoints

- `wyrdcraeft source mark-diacritics`
- `wyrdcraeft diacritic add`
- `wyrdcraeft diacritic delete`
- `wyrdcraeft diacritic-disambiguate`

## Primary Python Entrypoints

- `wyrdcraeft.cli.source:reading_mark_diacritics`
- `wyrdcraeft.cli.diacritic`
- `wyrdcraeft.cli.diacritic_disambiguate`
- `wyrdcraeft.services.markup:DiacriticRestorer`
- `wyrdcraeft.services.markup:normalize_old_english`

## Key Files

- `wyrdcraeft/cli/source.py`
- `wyrdcraeft/cli/diacritic.py`
- `wyrdcraeft/cli/diacritic_disambiguate.py`
- `wyrdcraeft/services/markup.py`
- `doc/source/overview/command_diacritic_add.rst`
- `doc/source/overview/command_diacritic_disambiguate.rst`

## Inputs And Outputs

Inputs:

- source text files for restoration
- macron index JSON payload
- Bosworth-Toller assist lookups during interactive disambiguation

Outputs:

- restored text file
- ambiguity report JSON
- unknown-word report JSON
- updated macron index JSON

## Invariants And Sharp Edges

- Default macron index path is packaged repo data under
  `wyrdcraeft/etc/diacritic/oe_bt_macron_index.json`.
- Normalized keys are lowercased, de-diacriticized, and `ð` becomes `þ`.
- `diacritic add` will not overwrite ambiguous entries; those must go through
  disambiguation flow.
- Interactive disambiguation has stateful counts and completion semantics; `q`
  exits session immediately.
- Restoration and curation are related but not same thing: restoration consumes
  index data, curation mutates it.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/dictionary.md](dictionary.md)

