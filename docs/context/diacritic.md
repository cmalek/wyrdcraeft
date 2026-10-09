# Diacritic Context

## What This Capability Does

Diacritic workflows restore, curate, and disambiguate Old English forms with
macrons and related normalization helpers.

This capability spans both text restoration and index maintenance.

## Main CLI Entrypoints

- `wyrdcraeft source mark-diacritics`
- `wyrdcraeft diacritic add`
- `wyrdcraeft diacritic delete`
- `wyrdcraeft diacritic import-variants`
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
- hand-edited palatalization exception lists under `wyrdcraeft/etc/diacritic/`
  (`c_palatalization_*.txt` and `g/frontal.txt`)
- Bosworth-Toller assist lookups during interactive disambiguation

Outputs:

- restored text file (additive only; see ADR 0015)
- unaligned-token report JSON
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
- An ambiguous key whose options all share one mark pattern is applied like a
  unique entry by `mark-diacritics` (unless completed), and the
  `diacritic-disambiguate` queue skips it; an explicit key still opens it.
- `--ambiguity-policy auto|leave|union` (CLI default `auto`, `MacronApplicator`
  default `leave`) resolves ambiguous keys that do not collapse; completed keys
  are never guessed; guessed tokens stay in the report with `applied_form` and
  `policy`.
- Standard elements (`wyrdcraeft/etc/diacritic/standard_elements.txt`, hand-edited)
  are spelled as listed in every index form before the transfer and the
  comparison. They count only where BT writes a hyphen after (prefix) or around
  (compound) the element, so `ge-an` and `gēan` stay apart. A source keeps its
  own marks. The file allows inline `#` comments; a conflicting duplicate entry
  logs a warning and the later one wins.
- `diacritic import-variants` (`BTVariantImporter`, `BTVariantFilter`) adds BT
  variants as unique entries, dry run by default. It never changes an existing
  key; collisions, conflicting new keys and below-gate variants go to a review
  report (`bt-variant-import-report.json`).
- Restoration and curation are related but not same thing: restoration consumes
  index data, curation mutates it.
- Macron-index curation is a separate extract from dictionary SQLite access.
  Marking a key completed (`m`) hides it from the default disambiguate queue
  without requiring POS/meaning annotations; `d` still records those senses
  when wanted.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/dictionary.md](dictionary.md)

