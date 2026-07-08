# Dictionary Context

## What This Capability Does

Dictionary workflows parse Bosworth-Toller source text into SQLite lookup data,
relink morphology `forms.entry_id` values after each rebuild, and expose
lookup and browse helpers over the attached `bt_*` tables.

## Main CLI Entrypoints

- `wyrdcraeft dictionary build`
- `wyrdcraeft dictionary query`
- `wyrdcraeft dictionary browse`
- `wyrdcraeft dictionary ingest-wright-text`
- `wyrdcraeft dictionary audit-wright`

## Primary Python Entrypoints

- `wyrdcraeft.cli.dictionary`
- `wyrdcraeft.services.dictionary.pipeline:BTIndexPipeline`
- `wyrdcraeft.services.dictionary.build_pipeline:DictionaryBuildPipeline`
- `wyrdcraeft.services.dictionary.query:BTQueryService`
- `wyrdcraeft.services.dictionary.browse_query:DictionaryBrowseQueryService`
- `wyrdcraeft.services.dictionary.resources:default_bt_source_path`

## Key Files

- `wyrdcraeft/cli/dictionary.py`
- `wyrdcraeft/services/dictionary/resources.py`
- `wyrdcraeft/services/dictionary/pipeline.py`
- `wyrdcraeft/services/dictionary/source_blocks.py`
- `wyrdcraeft/services/dictionary/sense_tree.py`
- `wyrdcraeft/services/dictionary/editorial_merger.py`
- `wyrdcraeft/services/dictionary/forms_entry_relinker.py`

## Inputs And Outputs

Inputs:

- Bosworth-Toller source text; default is the packaged
  `wyrdcraeft/etc/dictionary/oe_bt.txt` (override with `--source PATH`)
- optional report output
- optional warning log path (`parse_warnings.jsonl`, default beside the index DB)
- optional LLM fix pass for warning lines
- Wright markdown for `ingest-wright-text` (bundled corpus at
  `wyrdcraeft/etc/dictionary/wright.md`; always passed via `--source`)

Outputs:

- attached `bt_*` tables inside canonical `wyrdcraeft.sqlite3`
- `bt_edit_log` editorial audit rows
- relinked `forms.entry_id` values (NULL when join is ambiguous or unmatched)
- optional JSON report and parse warnings file

## Invariants And Sharp Edges

- One source block → one `bt_entries` row; `entry_order` preserves source-block
  identity. Homographs sharing `(norm_key, pos)` stay separate blocks rather
  than merging.
- `bt_senses.sense_path` values such as `1.2` are internal hierarchical paths,
  not literal Bosworth-Toller labels; original markers live in
  `source_label_raw` only.
- `parse_warnings.jsonl` collects parser warnings first, then editorial debris
  and unapplied-edit warnings after merge. Unapplied `bt_edit_log` rows with
  `target_missing` / `target_ambiguous` notes are mirrored into the warnings
  file for operator review.
- `FormsEntryRelinker` clears and recomputes every `forms.entry_id` after each
  dictionary rebuild; ambiguous or missing joins leave `entry_id` NULL.
- Dictionary build writes into the canonical app-data database; use
  `dictionary build --with-morphology` when `forms` is empty or morphology must
  be regenerated.
- Optional LLM repair path is warning-only, not the primary parser path.
- Wright section paragraph text requires explicit `dictionary ingest-wright-text`;
  dictionary build does not ingest Wright prose automatically.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/morphology.md](morphology.md)
