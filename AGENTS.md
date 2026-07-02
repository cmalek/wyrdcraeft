# AGENTS.md

## Agent skills

- Tracker: Trello `wyrdcraft`. See `docs/agents/issue-tracker.md`.
- Labels: `needs-triage`, `needs-info`, `ready-for-agent`,
  `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.
- Domain: single-context; read root `CONTEXT.md` and `docs/adr/` when present.
  See `docs/agents/domain.md`.

## Required workflow

- Before plan/code: run one `memory_search`, `aidex_session` plus one more
  `aidex` call, and one `code-index` call. Use `context7` and/or
  `package-registry-mcp` only for external package behavior/version details.
- Early update: name tools used plus one-line result for each. If tool not
  relevant, say so.
- After edits, if any Python files were touched, run `ruff check` on touched
  files or a broader needed target, `.venv/bin/mypy` on touched files or a
  broader needed target, and `make napoleon-gate`.
- Fix failures you introduced. Report unrelated/pre-existing failures
  separately.

## Implementation priorities

- Ship direct product-code fix, not workaround for doc-gate/baseline noise.
- No runtime patching, indirection, monkey-patching, startup hooks, or similar
  tricks just to avoid real source.
- If right fix lives in noisy legacy file, edit it there.
- For non-trivial behavior, prefer cohesive classes over loose function piles.
  Avoid namespace-only classes. Use explicit collaborators/constructor
  injection when clearer.

## Python documentation contract

For non-test Python:

- Class docstring: class contract; ctor `Args:` when needed.
- Fn/method docstring: brief desc; add only real `Side Effects:`, `Args:`,
  `Keyword Args:`, `Raises:`, `Returns:`, `Yields:`. No empty sections. No
  placeholder `None.`
- Add Napoleon `#:` for module globals, class attrs, and `__init__` instance
  attrs.
- Morphology logic needs `Note:` citing
  `data/OldEnglishGrammar.pdf` and `data/Ondej_Tich_40-54-1.pdf`, explaining
  behavior plainly, and naming PoS scope: `verb`, `noun`, `adjective`,
  `adverb`, `numeral`, or `cross-PoS`.
- `make napoleon-gate` = no new baseline violations.
- `make napoleon-gate-strict` only if asked.

## Human-Comprehensible Architecture Preference (Required)

For most non-trivial behavior in this repository, prefer implementing cohesive,
human-comprehensible classes over large collections of loosely related free
functions, even when those classes are mostly stateless.

Reason:

1. Clear class responsibilities and interactions make it easier for humans to
   cognitively model the system.
2. Prefer classes that represent real workflow boundaries, owned
   responsibilities, or stable concepts in the domain.
3. Avoid creating classes that are just arbitrary namespaces, but when the
   alternative is a mass of individual functions with shared implicit context,
   prefer the class-oriented design.
4. Favor constructor injection and explicit collaborators when that improves
   readability and makes the system easier for humans to follow.

## Morphology test safety

- `wyrdcraeft morphology generate` writes real app-data `morphology.sqlite3` by
  default. Can overwrite user data.
- Any test that triggers morphology generation, writes SQLite index, or
  resolves default index path must isolate output with one of:
  1. `isolated_morphology_app_data` fixture
     - preferred for default-path behavior
     - sets `WYRDCRAEFT_APP_DATA_DIR` to temp dir
  2. `--index-dir <temp dir>`
     - use for CLI tests with explicit override
- Never hit real default path unless path resolution mocked and no real write
  happens.
