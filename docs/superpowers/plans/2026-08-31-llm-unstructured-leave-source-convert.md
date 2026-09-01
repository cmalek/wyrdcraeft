# LLM and unstructured leave `source convert` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ADR 0010: keep `wyrdcraeft source convert` as local TEI/XML + `.txt` only; abandon LLM ingest, dictionary LLM repair, HTML/PDF/HTTP loaders, and the `unstructured` / `langextract` / `any-llm-sdk` packages.

**Architecture:** Deletion plus one loader change. `.txt` is UTF-8 → `split_prose_and_verse_runs` → existing `OEFilter` → `StructureParser` → `CanonicalConverter`. TEI path stays `TEISourceLoader` / `delb`. No `import wordwending`, no spawn. Docs already match; code follows.

**Tech Stack:** Python 3.11–3.13, Click, Pydantic settings, pytest, uv, ruff, mypy, `make napoleon-gate`.

**Spec:** [docs/adr/0010-llm-and-unstructured-leave-source-convert.md](../../adr/0010-llm-and-unstructured-leave-source-convert.md)

## Global Constraints

- Follow [AGENTS.md](../../../AGENTS.md): `graphify` before exploring; after Python edits `ruff`, `.venv/bin/mypy`, `make napoleon-gate` on touched files; `graphify update .` after code changes.
- Do not import or subprocess `wordwending`. LLM convert and `BTLLMFixPass` are abandoned, not migrated.
- Do not rewrite `OEFilter`, `StructureParser`, or `CanonicalConverter`.
- Keep `httpx` and `beautifulsoup4` — `wyrdcraeft/services/bosworthtoller.py` still uses them.
- Keep `ingest_auto` and `ingest_from_tei` as thin wrappers **without** `use_llm` / `llm_config`.
- Delete `ingest_without_llm` and `ingest_with_langextract`.
- User-facing Sphinx/README/`docs/context` already describe the end state. Do not resurrect LLM/HTML/PDF/HTTP convert docs. Do not rewrite historical `docs/superpowers/` plans.
- No compat shims for removed flags or `AnyLLMConfig`.
- This plan is not done until Task 8's full `uv run pytest` (no `-m` exclusions) is green and ADR 0010 `status` is `accepted`.
- Workspace rules: models in `wyrdcraeft.models`, services in `wyrdcraeft.services`, CLI in `wyrdcraeft.cli` only.

## File map

| File | Role after this plan |
|------|----------------------|
| `wyrdcraeft/ingest/loaders.py` | TEI + local `.txt` only. `FileSourceLoader` returns `list[RawBlock]`. No HTTP/HTML/PDF/`unstructured`. |
| `wyrdcraeft/ingest/pipeline.py` | Heuristic + TEI + `DocumentIngestor`. No LLM class or `use_llm`. `_get_preparsed_doc` takes `list[RawBlock]`. |
| `wyrdcraeft/ingest/normalizers.py` | Keep `split_prose_and_verse_runs`. Delete `normalize_elements_to_blocks` and `match_normalized_to_original` if unused. |
| `wyrdcraeft/ingest/extractors.py` | Delete file. |
| `wyrdcraeft/models/llm.py` | Delete file. |
| `wyrdcraeft/prompts/` | Delete directory. |
| `wyrdcraeft/cli/source.py` | `convert`: local path + `--title` only. |
| `wyrdcraeft/cli/dictionary.py` | No `--llm-fix-pass` / `--llm-model` / `--llm-endpoint`. |
| `wyrdcraeft/services/dictionary/llm_fix_pass.py` | Delete after moving **non-LLM** warning types/I/O: `BTParseWarning`, `write_parse_warnings`, `append_parse_warnings`. Drop `BTLLMFixPass`, `LLMFixResponseModel`, `LLMFixStats`, `DEFAULT_OLLAMA_ENDPOINT`. |
| `wyrdcraeft/services/dictionary/editorial_merger.py` | Keep importing `BTParseWarning` from the new home (not `llm_fix_pass`). |
| `wyrdcraeft/settings.py` | No LLM fields or `llm_config`. |
| `pyproject.toml` | Drop the three packages; drop pytest `llm` marker. |

---

### Task 1: Local `.txt` loader returns `RawBlock`s

**Files:**
- Modify: `wyrdcraeft/ingest/loaders.py`
- Modify: `wyrdcraeft/ingest/pipeline.py` (`BaseDocumentIngestor._get_preparsed_doc`)
- Modify: `tests/test_loaders.py`
- Modify: `tests/test_pipeline_classes.py` (if Task 1 would otherwise leave it red)
- Modify: `wyrdcraeft/ingest/normalizers.py` (delete `normalize_elements_to_blocks` only after pipeline no longer calls it)
- Modify: deterministic fixtures only if Step 4 fails on **structure**, not kwargs

**Interfaces:**
- Consumes: `split_prose_and_verse_runs(text: str, category: str | None, page: int | None = None) -> list[RawBlock]`
- Produces: `FileSourceLoader.load(source) -> list[RawBlock]`. `SourceLoader.get_loader` never returns HTTP. `_get_preparsed_doc` does not call `normalize_elements_to_blocks`.

**Intended load-path change (not a heuristic rewrite):** Today `_get_preparsed_doc` wraps the file as an `unstructured` element, then `normalize_elements_to_blocks` drops footnote-like lines and short ALL-CAPS headers before `split_prose_and_verse_runs`. ADR 0010 replaces that with UTF-8 → `split_prose_and_verse_runs` only. Losing those filters is **intended**. If `tests/test_deterministic_regression.py` fails on document shape, update fixtures. Do **not** restore `normalize_elements_to_blocks`, and do **not** change `OEFilter`, `StructureParser`, or `CanonicalConverter`.

- [ ] **Step 1: Replace `test_load_from_file_text` and URL tests**

In `tests/test_loaders.py`, replace `test_load_from_file_text` and delete `test_source_loader_load_url` and `test_source_loader_load_url_content_type`. Add:

```python
from wyrdcraeft.models.parsing import RawBlock


def test_load_from_file_text(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("þæt wæs god cyning.\n", encoding="utf-8")

    blocks = FileSourceLoader().load(file_path)
    assert len(blocks) >= 1
    assert all(isinstance(b, RawBlock) for b in blocks)
    assert "þæt wæs god cyning" in "".join(b.text for b in blocks)


def test_source_loader_rejects_http_url():
    with pytest.raises(ValueError, match="local"):
        SourceLoader().get_loader("https://example.com/a.txt")


def test_load_from_file_rejects_pdf():
    loader = FileSourceLoader()
    with pytest.raises(ValueError, match="Unsupported source format"):
        loader.load(Path("scan.pdf"))
```

Retarget `test_load_from_file_unsupported` to `FileSourceLoader().load(...)` if `load_from_file` is deleted. Keep `test_source_loader_load_file` without `partition_text` mocks. Keep `test_tei_source_loader_load_tei`.

In `tests/test_pipeline_classes.py`, drop or rewrite anything that imports `LLMDocumentIngestor` or patches `normalize_elements_to_blocks` (do not wait for Task 3 if those tests make this task's pytest red).

Remove `HTTPSourceLoader` from the test import.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_loaders.py -v`
Expected: FAIL (`HTTPSourceLoader` still imported; `.txt` still goes through `partition_text`; HTTP URLs still accepted)

- [ ] **Step 3: Implement loader + `_get_preparsed_doc`**

`wyrdcraeft/ingest/loaders.py`:

- Drop `httpx`, `tempfile`, `BeautifulSoup`, all `unstructured` imports.
- Delete `HTTPSourceLoader` and `load_from_file` HTML/PDF/`partition_text` branches.
- `FileSourceLoader.load`:

```python
def load(self, source: str | Path) -> list[RawBlock]:
    source_path = Path(source)
    suffix = source_path.suffix.lower()
    if suffix not in {".txt", ".text"}:
        msg = f"Unsupported source format: {suffix}"
        raise ValueError(msg)
    text = source_path.read_text(encoding="utf-8")
    from wyrdcraeft.ingest.normalizers import split_prose_and_verse_runs

    return split_prose_and_verse_runs(text, category=None, page=None)
```

(Import `split_prose_and_verse_runs` at module top if that does not create a cycle; if it does, keep the local import.)

- `SourceLoader.get_loader`: if `str(source).startswith(("http://", "https://"))`, raise `ValueError("source convert accepts a local .txt or TEI/XML path only")`. Else TEI vs `FileSourceLoader` as today (`.xml`/`.tei` or raw `<TEI`).
- Update `BaseSourceLoader` / `load` docstrings: return `list[RawBlock] | OldEnglishText`, not `unstructured.Element`.
- Delete `load_from_file` if unused.

`wyrdcraeft/ingest/pipeline.py` `_get_preparsed_doc`:

```python
elements = SourceLoader().load(source_path)
if isinstance(elements, OldEnglishText):
    msg = "TEI must be handled by TEIDocumentIngestor, not heuristic pre-parse"
    raise TypeError(msg)
blocks = elements  # list[RawBlock]
# remove normalize_elements_to_blocks(...)
oe_blocks = OEFilter().filter(blocks)
```

Keep the progress_callback calls; change the "Normalizing" message to something true ("Building text blocks") or drop that tick. Also delete the unused `raw_text = source_path.read_text(...)` in `_get_preparsed_doc` once `normalize_elements_to_blocks` is gone (otherwise ruff unused-variable).

Delete `normalize_elements_to_blocks` from `normalizers.py` if nothing else imports it (`rg normalize_elements_to_blocks`). If that leaves `match_normalized_to_original` unused, delete it too (`rg match_normalized_to_original`).

- [ ] **Step 4: Run loader + heuristic tests**

Run: `uv run pytest tests/test_loaders.py tests/test_deterministic_regression.py tests/test_pipeline_classes.py tests/test_preparse_speaker_mixed.py -v`

Expected:

- FAIL only on `ingest_auto(..., use_llm=False)` → leave that kwarg for Task 2/3.
- FAIL on **document structure / golden text** → update those fixtures here (see intended load-path change). Do not restore the old normalizer.
- PASS otherwise.

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/ingest/loaders.py wyrdcraeft/ingest/pipeline.py wyrdcraeft/ingest/normalizers.py tests/test_loaders.py tests/test_pipeline_classes.py
git commit -m "$(cat <<'EOF'
feat: load local txt as RawBlocks without unstructured

EOF
)"
```

(Skip files you did not touch. Include any fixture files you updated in Step 4.)

---

### Task 2: Strip LLM from convert CLI and `DocumentIngestor`

**Files:**
- Modify: `wyrdcraeft/cli/source.py` (`reading_convert`)
- Modify: `wyrdcraeft/ingest/pipeline.py` (`DocumentIngestor.ingest`, `ingest_auto`)
- Modify: `tests/test_cli_convert.py`
- Modify: `tests/test_pipeline_classes.py`, `tests/test_deterministic_regression.py` (drop `use_llm=`)

**Interfaces:**
- Consumes: Task 1 loader.
- Produces: `DocumentIngestor.ingest(source_path, metadata, *, progress_callback=None, **kwargs) -> OldEnglishText` with no `use_llm` / `llm_config`. CLI: `source convert SOURCE OUTPUT [--title]`. SOURCE must be an existing local path (reject `http://`).

- [ ] **Step 1: Write failing CLI tests**

Replace `test_convert_command_llm_flags` in `tests/test_cli_convert.py`:

```python
def test_convert_rejects_use_llm_flag(runner, temp_dir):
    source_file = temp_dir / "test.txt"
    source_file.write_text("þæt wæs god cyning.", encoding="utf-8")
    output_file = temp_dir / "output.json"
    result = runner.invoke(
        cli,
        ["source", "convert", str(source_file), str(output_file), "--use-llm"],
    )
    assert result.exit_code != 0


def test_convert_rejects_http_source(runner, temp_dir):
    output_file = temp_dir / "output.json"
    result = runner.invoke(
        cli,
        ["source", "convert", "https://example.com/a.txt", str(output_file)],
    )
    assert result.exit_code != 0
```

Change `test_convert_command_no_llm` to invoke without `--no-use-llm`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli_convert.py -v`
Expected: FAIL (`--use-llm` still a valid option, exit 0)

- [ ] **Step 3: Implement CLI + facade**

`reading_convert`: delete `--use-llm` and all `--llm-*` options and the settings overrides. Change `source` to `click.Path(exists=True, dir_okay=False, path_type=Path)` (or keep `str` and raise `click.ClickException` if it starts with `http://` or `https://`). Call:

```python
doc = DocumentIngestor().ingest(
    source_path=source_ref,
    metadata=metadata,
    progress_callback=progress_callback,
)
```

`DocumentIngestor.ingest`: delete `use_llm` and `llm_config`. Keep TEI suffix branch, then always `HeuristicDocumentIngestor`.

`ingest_auto`: same — no LLM kwargs.

Update tests that pass `use_llm=False`.

- [ ] **Step 4: Run convert tests**

Run: `uv run pytest tests/test_cli_convert.py tests/test_deterministic_regression.py tests/test_pipeline_classes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/cli/source.py wyrdcraeft/ingest/pipeline.py tests/test_cli_convert.py tests/test_deterministic_regression.py tests/test_pipeline_classes.py
git commit -m "$(cat <<'EOF'
feat: drop LLM flags from source convert

EOF
)"
```

---

### Task 3: Delete LLM ingest types, extractors, prompts

**Files:**
- Delete: `wyrdcraeft/ingest/extractors.py`
- Delete: `wyrdcraeft/models/llm.py`
- Delete: `wyrdcraeft/prompts/` (entire tree)
- Delete: `tests/test_extractors.py`, `tests/test_llm.py`, `tests/test_pipeline_llm.py`, `tests/test_golden_regression.py`
- Modify: `wyrdcraeft/ingest/pipeline.py` (delete `LLMDocumentIngestor`, `ingest_without_llm`, `ingest_with_langextract`)
- Modify: `wyrdcraeft/__init__.py`, `wyrdcraeft/models/__init__.py`

**Interfaces:**
- Consumes: Task 2 facade with no LLM branch.
- Produces: no `AnyLLMConfig`, no `LLMExtractor`, no `LLMDocumentIngestor`. `from wyrdcraeft import AnyLLMConfig` fails.

- [ ] **Step 1: Write failing export test**

Add to `tests/test_pipeline_classes.py` (or a tiny `tests/test_public_api.py`):

```python
def test_any_llm_config_not_exported():
    import wyrdcraeft

    assert not hasattr(wyrdcraeft, "AnyLLMConfig")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pipeline_classes.py::test_any_llm_config_not_exported -v`
Expected: FAIL (`AnyLLMConfig` still exported)

- [ ] **Step 3: Delete the LLM ingest surface**

- Remove `LLMDocumentIngestor` and the two legacy wrappers from `pipeline.py`. Remove `AnyLLMConfig` imports.
- Delete `extractors.py`, `models/llm.py`, `prompts/`.
- `__init__.py`: `from .models import TextMetadata` only; drop `AnyLLMConfig` from `__all__`.
- `models/__init__.py`: drop `AnyLLMConfig` import and `__all__` entry.
- Delete the four test modules listed above.
- Finish `tests/test_pipeline_classes.py`: no `LLMDocumentIngestor`, no `normalize_elements_to_blocks` patch.
- `rg AnyLLMConfig wyrdcraeft tests` — zero hits except this plan / ADR. If `settings.py` still imports it, Task 5 will remove that; for now leave Settings compiling (Task 5) **or** stub-break is OK if you do Task 5 immediately after in the same agent session. Prefer finishing this task only if Settings still imports `AnyLLMConfig` — **do Task 5 next in the same work stream if import errors block pytest.** If needed, land Tasks 3 and 5 in one commit rather than a red tree.

If `settings.py` import breaks collection, fold Task 5 into this commit.

- [ ] **Step 4: Run a focused suite**

Run: `uv run pytest tests/test_pipeline_classes.py tests/test_cli_convert.py tests/test_loaders.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A wyrdcraeft/ingest wyrdcraeft/models wyrdcraeft/prompts wyrdcraeft/__init__.py tests
git commit -m "$(cat <<'EOF'
feat: remove LLM ingest types and prompts

EOF
)"
```

---

### Task 4: Delete dictionary LLM repair

**Files:**
- Modify: `wyrdcraeft/cli/dictionary.py`
- Modify: `wyrdcraeft/services/dictionary/pipeline.py`
- Modify: `wyrdcraeft/services/dictionary/build_pipeline.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py` (imports `BTParseWarning` from `llm_fix_pass`)
- Modify: `wyrdcraeft/services/dictionary/__init__.py`
- Create or extend: `wyrdcraeft/models/dictionary.py` (or keep helpers next to `pipeline.py`) for the non-LLM warning types/I/O
- Delete: `wyrdcraeft/services/dictionary/llm_fix_pass.py` (only after the move below)
- Delete: `tests/dictionary/test_llm_fix_pass.py`
- Grep/fix any other test that passes `llm_fix_pass=`

**Interfaces:**
- Consumes: nothing from Tasks 1–3 except “no `AnyLLMConfig`”.
- Produces: `dictionary build` has no `--llm-fix-pass` / `--llm-model` / `--llm-endpoint`. Pipelines take no `llm_fix_pass` collaborator. Warning JSONL I/O still works.

**Must move before delete (used by non-LLM dictionary index):** `BTIndexPipeline` calls `write_parse_warnings` / `append_parse_warnings`; `editorial_merger.py` and `pipeline.py` import `BTParseWarning`. All three live in `llm_fix_pass.py` today. Move them first:

- Prefer `BTParseWarning` on `wyrdcraeft.models` (project rule: models in `wyrdcraeft.models`).
- Keep `write_parse_warnings` / `append_parse_warnings` as a small helper next to `pipeline.py`, or in the same models module if they stay trivial JSONL writers.

**Delete with the LLM class:** `BTLLMFixPass`, `LLMFixResponseModel`, `LLMFixStats`, `DEFAULT_OLLAMA_ENDPOINT`.

- [ ] **Step 1: Write failing CLI test**

Add to `tests/test_cli_commands.py` (or existing dictionary CLI test module if one already invokes `build --help`):

```python
def test_dictionary_build_has_no_llm_flags():
    from click.testing import CliRunner

    from wyrdcraeft.cli.cli import cli

    result = CliRunner().invoke(cli, ["dictionary", "build", "--help"])
    assert result.exit_code == 0
    assert "llm-fix-pass" not in result.output
    assert "llm-model" not in result.output
    assert "llm-endpoint" not in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_commands.py::test_dictionary_build_has_no_llm_flags -v`
Expected: FAIL (help still lists those options)

- [ ] **Step 3: Remove flags and collaborator**

- Delete the three `@click.option`s and the `llm_fix_pass` / `llm_model` / `llm_endpoint` parameters from `build()`.
- Stop constructing `BTLLMFixPass(...)`.
- Remove `llm_fix_pass` from `BTIndexPipeline` / `DictionaryBuildPipeline` signatures and call sites.
- Drop `BTLLMFixPass`, `LLMFixStats`, and `DEFAULT_OLLAMA_ENDPOINT` from `services/dictionary/__init__.py`. Re-export `BTParseWarning` from its new home. Keep exporting warning I/O if it is part of the package API today.
- **Move** `BTParseWarning`, `write_parse_warnings`, and `append_parse_warnings`. Update `pipeline.py`, `editorial_merger.py`, and any remaining imports.
- Then delete `llm_fix_pass.py` and `tests/dictionary/test_llm_fix_pass.py`.
- `rg llm_fix_pass|BTLLMFixPass|DEFAULT_OLLAMA_ENDPOINT|write_parse_warnings|append_parse_warnings|BTParseWarning` — zero imports from the deleted module.

- [ ] **Step 4: Run dictionary tests**

Run: `uv run pytest tests/dictionary tests/test_cli_commands.py::test_dictionary_build_has_no_llm_flags -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/cli/dictionary.py wyrdcraeft/services/dictionary wyrdcraeft/models tests
git commit -m "$(cat <<'EOF'
feat: remove dictionary LLM fix pass

EOF
)"
```

(Include the new warning-type home if you created `wyrdcraeft/models/dictionary.py`.)

---

### Task 5: Strip Settings LLM fields and tests

**Files:**
- Modify: `wyrdcraeft/settings.py` (fields ~53–71, validator ~264–326, `llm_config`)
- Delete: `tests/test_settings_llm.py`
- Modify: `tests/test_configuration.py` and any fixture that sets `llm_*` / API keys
- Modify: `tests/conftest.py` (`mock_settings` if it sets LLM fields)

**Interfaces:**
- Consumes: no `AnyLLMConfig`.
- Produces: `Settings()` constructs without LLM attributes.

- [ ] **Step 1: Write failing settings test**

Add to `tests/test_configuration.py`:

```python
def test_settings_has_no_llm_fields():
    from wyrdcraeft.settings import Settings

    s = Settings()
    assert not hasattr(s, "llm_model_id")
    assert not hasattr(s, "llm_config")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_configuration.py::test_settings_has_no_llm_fields -v`
Expected: FAIL

- [ ] **Step 3: Delete LLM settings**

Remove the LLM field block, `get_model_provider`, `llm_config`, and LLM branches in any `model_validator`. Remove `from .models import AnyLLMConfig`.

Delete `tests/test_settings_llm.py`. Fix `test_configuration.py` / fixtures that assign `llm_model_id` etc. Also `tests/test_cli_commands.py` — it currently asserts `"llm_model_id" in data` from `settings show`; drop that assertion.

- [ ] **Step 4: Run settings/config tests**

Run: `uv run pytest tests/test_configuration.py tests/test_cli_commands.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/settings.py tests/test_configuration.py tests/test_settings_llm.py tests/conftest.py tests/test_cli_commands.py
git commit -m "$(cat <<'EOF'
feat: remove LLM fields from Settings

EOF
)"
```

---

### Task 6: Pytest marker, live-LLM fixtures, package deps

**Files:**
- Modify: `tests/conftest.py` (drop `--run-llm`, `pytest_collection_modifyitems` llm skip, `ensure_llama_server` and helpers, `httpx` import if unused)
- Modify: `pyproject.toml` dependencies + `[tool.pytest.ini_options].markers`
- Modify or delete leftover LLM comments in `tests/test_prompt_regression.py` (schema tests can stay; strip `langextract` “future” comments or delete the placeholder snapshot test)
- Grep: `Makefile` / CI for `--run-llm` or `-m llm`

**Interfaces:**
- Consumes: no remaining `@pytest.mark.llm` tests.
- Produces: `uv sync` lock without `unstructured`, `langextract`, `any-llm-sdk`.

- [ ] **Step 1: Confirm no remaining `mark.llm` tests**

Run: `rg -n "pytest.mark.llm|--run-llm|mark.llm" tests wyrdcraeft`
Expected after this task: no code hits. If any remain, delete those tests here.

- [ ] **Step 2: Remove conftest LLM harness**

Delete `pytest_addoption` `--run-llm`, the `llm` skip loop, `ensure_llama_server`, `_is_llama_server_healthy`, llama path helpers, and unused `httpx` import. Keep unrelated fixtures.

- [ ] **Step 3: Drop packages**

In `pyproject.toml` `dependencies`, delete:

```
"unstructured[all-docs]>=0.15",
"langextract>=0.0.0",
"any-llm-sdk[gemini,ollama,openai]",
```

Remove the `llm:` pytest marker line.

Run: `uv lock && uv sync`

- [ ] **Step 4: Grep imports**

Run: `rg -n "unstructured|langextract|any_llm|any-llm" wyrdcraeft tests pyproject.toml`
Expected: no runtime hits (ADR/plan mentions OK). `tests/test_prompt_regression.py` currently mentions langextract in comments only — strip those comments here or in Task 7 so the leftover search is clean.

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_prompt_regression.py pyproject.toml uv.lock
git commit -m "$(cat <<'EOF'
chore: drop unstructured, langextract, and any-llm-sdk

EOF
)"
```

(Skip `tests/test_prompt_regression.py` if you leave it for Task 7.)

---

### Task 7: Napoleon baseline + leftover references

**Files:**
- `doc/quality/napoleon_gate_baseline.json` (regenerate or delete keys for removed symbols)
- Any leftover `rg` hits in `wyrdcraeft/`, `tests/`, `doc/source/` (not historical `docs/superpowers/`)

- [ ] **Step 1: Search leftovers**

Run:

```bash
rg -n "LLMDocumentIngestor|AnyLLMConfig|LLMExtractor|BTLLMFixPass|ingest_with_langextract|use_llm|partition_text|HTTPSourceLoader|langextract|normalize_elements_to_blocks" \
  wyrdcraeft tests doc/source CONTEXT.md docs/context docs/adr/0010-llm-and-unstructured-leave-source-convert.md
```

Fix code/docs that still claim those APIs exist. ADR 0010 may still *name* them as removed — that is OK. Historical `docs/superpowers/` plans stay as they were.

- [ ] **Step 2: Napoleon gate**

Run: `make napoleon-gate`
If it fails only because deleted symbols left stale baseline keys, update the baseline the same way this repo already does (re-run the gate’s update path or edit `doc/quality/napoleon_gate_baseline.json` to drop those keys). Do not add new violations.

- [ ] **Step 3: Lint/type touched packages**

Run:

```bash
uv run ruff check wyrdcraeft/ingest wyrdcraeft/cli/source.py wyrdcraeft/cli/dictionary.py wyrdcraeft/settings.py wyrdcraeft/models wyrdcraeft/__init__.py wyrdcraeft/services/dictionary
.venv/bin/mypy wyrdcraeft/ingest wyrdcraeft/cli/source.py wyrdcraeft/cli/dictionary.py wyrdcraeft/settings.py wyrdcraeft/models wyrdcraeft/__init__.py wyrdcraeft/services/dictionary
```

Expected: clean. Fix everything you introduced.

- [ ] **Step 4: Commit**

```bash
git add doc/quality/napoleon_gate_baseline.json
git commit -m "$(cat <<'EOF'
chore: refresh napoleon baseline after LLM removal

EOF
)"
```

(Skip empty commit if baseline already clean.)

---

### Task 8: Accept ADR 0010 and full verification

**Files:**
- Modify: `docs/adr/0010-llm-and-unstructured-leave-source-convert.md` frontmatter `status: accepted`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: ADR matches the tree.

- [ ] **Step 1: Set status accepted**

Change `status: proposed` → `status: accepted`.

- [ ] **Step 2: Full pytest**

Run: `uv run pytest`
Expected: PASS, zero failures, no `-m` exclusions.

- [ ] **Step 3: Quality gate + graph**

```bash
make napoleon-gate
graphify update .
```

- [ ] **Step 4: Commit**

```bash
git add docs/adr/0010-llm-and-unstructured-leave-source-convert.md
git commit -m "$(cat <<'EOF'
docs: accept ADR 0010 after implementation

EOF
)"
```

---

## Self-review (spec coverage)

| ADR requirement | Task |
|-----------------|------|
| Convert stays; TEI + local `.txt` | 1, 2 |
| UTF-8 → `split_prose_and_verse_runs` → existing heuristic | 1 |
| Abandon LLM (not migrate); no wordwending import | 3, global |
| Remove convert LLM CLI/types/prompts/export | 2, 3 |
| Keep `ingest_auto` without LLM kwargs; drop LLM-only wrappers | 2, 3 |
| Dictionary `BTLLMFixPass` + flags gone; keep warning JSONL helpers | 4 |
| Settings / env / pytest llm / golden tests | 5, 6 |
| HTTP loader gone; keep httpx if bosworthtoller needs it | 1, 6 |
| Packages removed | 6 |
| Napoleon keys | 7 |
| Docs already done; ADR accepted when code matches | 8 |
| No heuristic rewrite | 1 (loader only) |
