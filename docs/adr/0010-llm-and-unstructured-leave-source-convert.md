---
status: accepted
---

# LLM and unstructured leave `source convert`

`wyrdcraeft source convert` stays as a local, deterministic command: TEI/XML and
`.txt` to document JSON via TEI ingest and heuristic ingest. LLM extraction
never worked; it is **abandoned**, not relocated. OCR already left in ADR 0007.
HTML, PDF, HTTP fetch, and `unstructured` were unused or wrong. This repo does
not import or spawn `wordwending`.

Dictionary LLM repair (`BTLLMFixPass`) is abandoned here too. The extract that
`dictionary build` needed now lives in `wordwending`. No leftover convert or
dictionary `--llm-*` flags.

Only current user is the maintainer. Public Python and CLI breaks need no
compat shim.

**Status:** accepted. Code matches. User-facing Sphinx, README, and
`docs/context` already describe TEI + local `.txt` only (docs lead; code
follows). Historical superpowers plans/specs stay as they were.

## `.txt` load (not a heuristic rewrite)

Read the file as UTF-8. Build `RawBlock`s with
`split_prose_and_verse_runs` (no duck-typed `unstructured.Element`). Then the
existing `OEFilter` → `StructureParser` → `CanonicalConverter` path. TEI
loader unchanged (`delb`). That is the whole loader change.

## Removed

Convert / ingest:

- CLI `--use-llm` / `--llm-*`
- `LLMDocumentIngestor`, `LLMExtractor`, `AnyLLMConfig`
- `ingest_auto` / `ingest_without_llm` / `ingest_with_langextract` if they only
  exist to toggle LLM
- `wyrdcraeft/prompts/`
- public export of `AnyLLMConfig` from `wyrdcraeft`

Dictionary:

- `BTLLMFixPass` and tests
- `dictionary build --llm-fix-pass` / `--llm-model` / `--llm-endpoint`

Settings / test / docs-codegen leftovers:

- `Settings.llm_*`, `llm_provider`, API-key fields, `llm_config`
- `WYRDCRAEFT_LLM_*` and related API-key env vars
- pytest `llm` marker, `--run-llm`, golden/live LLM tests
- `HTTPSourceLoader` and the BeautifulSoup `<pre>` fetch path
- `httpx` if nothing else imports it
- napoleon-gate baseline keys for deleted symbols (drop with the code)

Packages: `unstructured[all-docs]`, `langextract`, `any-llm-sdk`.

## Sibling name

Not this ADR. Current name is `wordwending` (formerly `bochord`); see the note
on ADR 0007. Filename `0007-ocr-pipeline-moves-to-bochord.md` stays.

## Not this decision

Heuristic parser rewrite beyond the UTF-8 → `RawBlock` load. Migrating
abandoned convert/dictionary LLM into `wordwending` (not happening).
