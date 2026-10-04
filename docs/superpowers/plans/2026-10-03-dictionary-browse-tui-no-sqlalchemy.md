# Dictionary browse TUI must not touch SQLAlchemy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the dictionary browse Textual module from running SQLAlchemy, put `bt_entries` readiness and ranking-helper ownership on `DictionaryBrowseQueryService` / `browse_query.py`, and delete the unused ranking copies in `form_decode.py`.

**Architecture:** `DictionaryBrowseQueryService.ensure_ready()` counts `bt_entries` on the existing connection and raises `DictionaryBrowseDataError` defined in `browse_query.py`. `create_dictionary_browse_app` calls that method and closes the service on failure. Live `lexical_distance` / `normalized_query_at_affix` / `filter_display_variants` stay in `browse_query`; `form_decode` keeps decode and paradigm grids.

**Tech Stack:** Python 3.11–3.13, SQLAlchemy, Textual, pytest, ruff, mypy, `make napoleon-gate`, graphify.

**Spec:** [docs/adr/0014-dictionary-browse-tui-is-a-shell.md](../../adr/0014-dictionary-browse-tui-is-a-shell.md). Trello: https://trello.com/c/zHZpvqfk (ADR overrides the card). Related: ADR 0013, backlog grid split https://trello.com/c/OW5yM68o.

## Global Constraints

- `wyrdcraeft/services/dictionary/browse_tui.py` must not `import sqlalchemy` or execute SQL.
- Browse readiness is `DictionaryBrowseQueryService.ensure_ready()` counting `bt_entries` only. Do not call `require_populated_dictionary_index`.
- Do not rank in SQL. Do not add rapidfuzz. Do not change `search()` to stop loading all entries/variants.
- Do not move `build_paradigm_sidebar` or POS `_build_*_sidebar` helpers (OW5yM68o). Do not move TUI row-filter / dedupe / `DataTable` painting.
- Do not add a third helper module. Ranking helpers live in `browse_query.py`.
- `DictionaryBrowseDataError` is defined in `browse_query.py`. `browse_query` must not import `browse_tui`.
- Preserve existing user-facing ready-failure copy: `"tables are missing"` and `"tables are empty"` (tests match those substrings).
- After Python edits: `ruff` and `.venv/bin/mypy` on touched files, `make napoleon-gate`, `graphify update .`.
- Do not commit unless the user explicitly asks. Plan commit steps are optional.
- Napoleon docs on new public types/methods; no empty sections. Methods ≤ 60 lines.

## File map

| File | Role after this plan |
|------|----------------------|
| `wyrdcraeft/services/dictionary/browse_query.py` | `DictionaryBrowseDataError`, `ensure_ready()`, live ranking/display helpers. |
| `wyrdcraeft/services/dictionary/browse_tui.py` | Textual shell + factory calling `ensure_ready()`; re-export the error type; no SQLAlchemy. |
| `wyrdcraeft/services/dictionary/form_decode.py` | Decode + grids only; ranking/display helper duplicates deleted. |
| `wyrdcraeft/cli/dictionary.py` | Unchanged. Keep `DictionaryBrowseDataError` via the `browse_tui` re-export. |
| `tests/dictionary/test_browse_query.py` | Direct `ensure_ready` tests, including entries-without-senses. |
| `tests/dictionary/test_browse_tui.py` | Existing factory missing/empty tests, no-sqlalchemy/`_connection` source assertion, factory close-on-failure. |
| `tests/lexicon/test_form_decode.py` | Ranking/variant helper tests import `browse_query`. |

## Review Focus

- Empty `bt_senses` / `bt_variants` with at least one `bt_entries` row: `ensure_ready()` succeeds (not ADR 0013).
- Missing `bt_entries` table vs migrated empty table: distinct `"missing"` vs `"empty"` messages.
- `browse_tui.py` source has no `from sqlalchemy` / `import sqlalchemy` and no `query_service._connection` after Task 1.
- `form_decode` has no `def lexical_distance` / `def normalized_query_at_affix` / `def filter_display_variants` after Task 2.
- Failed `create_dictionary_browse_app` calls `close()` on the query service (`test_create_app_closes_service_when_unready`).

---

### Task 1: Browse readiness on the query service

**Files:**
- Modify: `wyrdcraeft/services/dictionary/browse_query.py`
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py`
- Test: `tests/dictionary/test_browse_query.py`
- Test: `tests/dictionary/test_browse_tui.py`
- Do not modify: `wyrdcraeft/cli/dictionary.py`

**Interfaces:**
- Consumes: `DictionaryBrowseQueryService._connection`, existing `create_dictionary_browse_app` factory flow.
- Produces:
  - `class DictionaryBrowseDataError(RuntimeError)`
  - `def DictionaryBrowseQueryService.ensure_ready(self) -> None`
  - `create_dictionary_browse_app` calls `query_service.ensure_ready()` and `query_service.close()` on that error.

- [ ] **Step 1: Write the failing tests**

In `tests/dictionary/test_browse_query.py`, add `DictionaryBrowseDataError` to the existing import:

```python
from wyrdcraeft.services.dictionary.browse_query import (
    DictionaryBrowseDataError,
    DictionaryBrowseQueryService,
)
```

Do not add a second import of `DictionaryBrowseQueryService`. Append (reuse `_pos_id`):

```python
def test_ensure_ready_rejects_missing_bt_entries_table(tmp_path: Path) -> None:
    db_path = tmp_path / "no-tables.sqlite3"
    db_path.touch()
    service = DictionaryBrowseQueryService(db_path)
    try:
        with pytest.raises(DictionaryBrowseDataError, match="tables are missing"):
            service.ensure_ready()
    finally:
        service.close()


def test_ensure_ready_rejects_empty_bt_entries(tmp_path: Path) -> None:
    db_path = tmp_path / "empty-entries.sqlite3"
    upgrade_canonical_db(db_path)
    service = DictionaryBrowseQueryService(db_path)
    try:
        with pytest.raises(DictionaryBrowseDataError, match="tables are empty"):
            service.ensure_ready()
    finally:
        service.close()


def test_ensure_ready_accepts_populated_fixture(lexicon_source_db: Path) -> None:
    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        service.ensure_ready()
    finally:
        service.close()


def test_ensure_ready_accepts_entries_without_senses(tmp_path: Path) -> None:
    db_path = tmp_path / "entries-only.sqlite3"
    upgrade_canonical_db(db_path)
    pos_id = _pos_id(db_path, code="noun")
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO bt_entries (
                norm_key, headword, normalized_title, pos_id,
                genders_json, etymology, see_also_json,
                source_line_nos_json, entry_order
            ) VALUES ('abbad', 'abbad', 'abbad', ?, '[]', '', '[]', '[]', 1)
            """,
            (pos_id,),
        )
    service = DictionaryBrowseQueryService(db_path)
    try:
        service.ensure_ready()
    finally:
        service.close()
```

In `tests/dictionary/test_browse_tui.py`, add these tests (the file already imports `Path` and `DictionaryBrowseQueryService`; keep existing `test_shell_rejects_*` tests):

```python
from wyrdcraeft.services.dictionary import browse_tui as browse_tui_module


def test_browse_tui_source_does_not_import_sqlalchemy() -> None:
    source = Path(browse_tui_module.__file__).read_text(encoding="utf-8")
    assert "from sqlalchemy" not in source
    assert "import sqlalchemy" not in source
    assert "query_service._connection" not in source
    assert "._connection" not in source


def test_create_app_closes_service_when_unready(
    empty_browse_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[object] = []
    real_close = DictionaryBrowseQueryService.close

    def tracking_close(self: DictionaryBrowseQueryService) -> None:
        closed.append(self)
        real_close(self)

    monkeypatch.setattr(DictionaryBrowseQueryService, "close", tracking_close)
    with pytest.raises(DictionaryBrowseDataError):
        create_dictionary_browse_app(empty_browse_db)
    assert closed
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/dictionary/test_browse_query.py::test_ensure_ready_rejects_missing_bt_entries_table tests/dictionary/test_browse_query.py::test_ensure_ready_rejects_empty_bt_entries tests/dictionary/test_browse_query.py::test_ensure_ready_accepts_populated_fixture tests/dictionary/test_browse_query.py::test_ensure_ready_accepts_entries_without_senses tests/dictionary/test_browse_tui.py::test_browse_tui_source_does_not_import_sqlalchemy tests/dictionary/test_browse_tui.py::test_create_app_closes_service_when_unready -v
```

Expected: FAIL — `ensure_ready` missing and/or sqlalchemy / `_connection` still in `browse_tui.py`. `test_create_app_closes_service_when_unready` may already pass (factory already closes today); keep it as a regression lock.

- [ ] **Step 3: Implement readiness on the query service**

In `browse_query.py`, add `from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError` next to the existing `from sqlalchemy import text`.

Add the error class above `DictionaryBrowseQueryService` (after the helper functions is also fine; keep it module-level):

```python
class DictionaryBrowseDataError(RuntimeError):
    """Raised when dictionary browse data is unavailable for the TUI shell."""
```

Napoleon: class docstring only (no constructor args).

Add this method on `DictionaryBrowseQueryService` immediately before `close`:

```python
    def ensure_ready(self) -> None:
        """
        Validate that ``bt_entries`` exists and contains searchable rows.

        Raises:
            DictionaryBrowseDataError: The table is missing or has no rows.

        """
        try:
            counts = self._connection.execute(
                text("SELECT COUNT(*) AS entry_count FROM bt_entries")
            ).mappings().first()
        except SQLAlchemyOperationalError as exc:
            msg = (
                "Dictionary browse tables are missing. "
                "Run `wyrdcraeft dictionary build` for this database first."
            )
            raise DictionaryBrowseDataError(msg) from exc

        if counts is not None and int(counts["entry_count"]) > 0:
            return

        msg = (
            "Dictionary browse tables are empty. "
            "Run `wyrdcraeft dictionary build` for this database first."
        )
        raise DictionaryBrowseDataError(msg)
```

Do not wrap non-operational SQLAlchemy errors. Do not inspect `bt_senses` or `bt_variants`.

Update `__all__`:

```python
__all__ = [
    "BrowseSearchHit",
    "DictionaryBrowseDataError",
    "DictionaryBrowseQueryService",
]
```

In `browse_tui.py`:

1. Delete `from sqlalchemy import text` and `from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError`.
2. Extend the existing `browse_query` import to include `DictionaryBrowseDataError` (remove the local `class DictionaryBrowseDataError`).
3. Delete `_ensure_browse_ready` entirely.
4. Change `create_dictionary_browse_app` to:

```python
    query_service = DictionaryBrowseQueryService(db_path)
    try:
        query_service.ensure_ready()
    except DictionaryBrowseDataError:
        query_service.close()
        raise
    return DictionaryBrowseApp(
        query_service=query_service,
        db_path=db_path,
        initial_details_message=_format_browse_connect_message(db_path),
    )
```

Keep `DictionaryBrowseDataError` in `browse_tui.__all__` as a re-export so CLI and TUI tests need no import-path change.

- [ ] **Step 4: Run Task 1 tests plus existing factory tests**

```bash
.venv/bin/pytest tests/dictionary/test_browse_query.py::test_ensure_ready_rejects_missing_bt_entries_table tests/dictionary/test_browse_query.py::test_ensure_ready_rejects_empty_bt_entries tests/dictionary/test_browse_query.py::test_ensure_ready_accepts_populated_fixture tests/dictionary/test_browse_query.py::test_ensure_ready_accepts_entries_without_senses tests/dictionary/test_browse_tui.py::test_browse_tui_source_does_not_import_sqlalchemy tests/dictionary/test_browse_tui.py::test_create_app_closes_service_when_unready tests/dictionary/test_browse_tui.py::test_shell_rejects_missing_lexicon_tables tests/dictionary/test_browse_tui.py::test_shell_rejects_empty_lexicon_tables tests/dictionary/test_browse_tui.py::test_shell_run_entrypoint_uses_textual_app -v
```

Expected: PASS.

- [ ] **Step 5: Quality gate for Task 1 files**

```bash
.venv/bin/ruff check wyrdcraeft/services/dictionary/browse_query.py wyrdcraeft/services/dictionary/browse_tui.py tests/dictionary/test_browse_query.py tests/dictionary/test_browse_tui.py
.venv/bin/mypy wyrdcraeft/services/dictionary/browse_query.py wyrdcraeft/services/dictionary/browse_tui.py
make napoleon-gate
graphify update .
```

Expected: ruff/mypy clean on those files; napoleon-gate no new violations; graph updated.

- [ ] **Step 6: Commit (only if the user asked)**

```bash
git add wyrdcraeft/services/dictionary/browse_query.py wyrdcraeft/services/dictionary/browse_tui.py tests/dictionary/test_browse_query.py tests/dictionary/test_browse_tui.py
git commit -m "$(cat <<'EOF'
Move dictionary browse readiness off the TUI connection.

EOF
)"
```

---

### Task 2: Ranking helpers stay on browse_query

**Files:**
- Modify: `wyrdcraeft/services/dictionary/form_decode.py`
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py`
- Modify: `tests/lexicon/test_form_decode.py`

**Interfaces:**
- Consumes: existing `browse_query.filter_display_variants`, `lexical_distance`, `normalized_query_at_affix`.
- Produces: those names exist only in `browse_query.py` (plus tests importing them from there). `form_decode` still exports decode/grid APIs.

- [ ] **Step 1: Write the failing import/source tests**

In `tests/lexicon/test_form_decode.py`, change the ranking/variant imports to `browse_query` and add a source assertion. Replace the current `form_decode` import block with:

```python
from pathlib import Path

from wyrdcraeft.services.dictionary.browse_query import (
    filter_display_variants,
    lexical_distance,
    normalized_query_at_affix,
)
from wyrdcraeft.services.dictionary.form_decode import (
    MorphologyRowPayload,
    build_morphology_table,
    build_paradigm_sidebar,
    decode_function_dimensions,
    format_verb_class,
    infer_bt_pos_from_wordclasses,
    morphology_row_matches_pos,
)
from wyrdcraeft.services.dictionary import form_decode as form_decode_module


def test_form_decode_does_not_define_ranking_helpers() -> None:
    source = Path(form_decode_module.__file__).read_text(encoding="utf-8")
    assert "def lexical_distance(" not in source
    assert "def normalized_query_at_affix(" not in source
    assert "def filter_display_variants(" not in source
```

Leave `test_filter_display_variants_drops_genitive_endings`, `test_normalized_query_at_affix_requires_start_or_end`, and `test_lexical_distance_prefers_exact_matches` in this file; they now hit `browse_query`.

- [ ] **Step 2: Run tests to verify the source assertion fails**

```bash
.venv/bin/pytest tests/lexicon/test_form_decode.py::test_form_decode_does_not_define_ranking_helpers tests/lexicon/test_form_decode.py::test_filter_display_variants_drops_genitive_endings tests/lexicon/test_form_decode.py::test_normalized_query_at_affix_requires_start_or_end tests/lexicon/test_form_decode.py::test_lexical_distance_prefers_exact_matches -v
```

Expected: `test_filter_display_variants_drops_genitive_endings`, `test_normalized_query_at_affix_requires_start_or_end`, and `test_lexical_distance_prefers_exact_matches` PASS (they already call `browse_query`). `test_form_decode_does_not_define_ranking_helpers` FAIL while those `def` lines still exist in `form_decode.py`.

- [ ] **Step 3: Delete form_decode duplicates and retarget the TUI import**

In `form_decode.py`, delete the unused ranking/display copies and the helpers that exist only to serve them:

- `filter_display_variants`, `normalized_query_at_affix`, `lexical_distance` (ADR list)
- `GENITIVE_VARIANT_ENDINGS` and `is_genitive_variant_token` (only used by `filter_display_variants` in this file)

Do not delete `format_bt_gender_label`, `format_verb_class`, `format_noun_declension`, decode functions, or grid builders.

In `browse_tui.py`, add `filter_display_variants` to the existing Task 1 `browse_query` import and remove it from the `form_decode` import. Do not replace the whole import block from scratch. After the edit it should look like:

```python
from wyrdcraeft.services.dictionary.browse_query import (
    BrowseSearchHit,
    DictionaryBrowseDataError,
    DictionaryBrowseQueryService,
    EntryDetails,
    MorphologyGroup,
    MorphologyRow,
    filter_display_variants,
)
from wyrdcraeft.services.dictionary.form_decode import (
    MorphologyRowPayload,
    ParadigmSidebarSpec,
    build_paradigm_sidebar,
    format_bt_gender_label,
    morphology_row_matches_pos,
)
```

Do not rewrite `_normalized_affix_match` or `_rank_candidate`. Do not add rapidfuzz.

- [ ] **Step 4: Run ranking, TUI, and browse-query tests**

```bash
.venv/bin/pytest tests/lexicon/test_form_decode.py tests/dictionary/test_browse_query.py tests/dictionary/test_browse_tui.py tests/lexicon/test_morph_class_browse.py -v
```

Expected: PASS. Confirm:

```bash
rg "def lexical_distance|def normalized_query_at_affix|def filter_display_variants" wyrdcraeft/services/dictionary/form_decode.py
rg "from sqlalchemy|import sqlalchemy" wyrdcraeft/services/dictionary/browse_tui.py
```

Expected: both empty.

- [ ] **Step 5: Quality gate + graphify**

```bash
.venv/bin/ruff check wyrdcraeft/services/dictionary/browse_query.py wyrdcraeft/services/dictionary/browse_tui.py wyrdcraeft/services/dictionary/form_decode.py tests/dictionary/test_browse_query.py tests/dictionary/test_browse_tui.py tests/lexicon/test_form_decode.py
.venv/bin/mypy wyrdcraeft/services/dictionary/browse_query.py wyrdcraeft/services/dictionary/browse_tui.py wyrdcraeft/services/dictionary/form_decode.py
make napoleon-gate
graphify update .
```

Expected: gates clean; graph updated. Do not edit `graphify-out/` by hand.

- [ ] **Step 6: Commit (only if the user asked)**

```bash
git add wyrdcraeft/services/dictionary/form_decode.py wyrdcraeft/services/dictionary/browse_tui.py tests/lexicon/test_form_decode.py
git commit -m "$(cat <<'EOF'
Keep browse ranking helpers on the query module.

EOF
)"
```

---

## Spec coverage (self-review)

| ADR 0014 requirement | Task |
|----------------------|------|
| TUI must not import/execute SQLAlchemy | Task 1 |
| `ensure_ready()` counts `bt_entries` on the service connection | Task 1 |
| `DictionaryBrowseDataError` lives in `browse_query.py` | Task 1 |
| Factory calls `ensure_ready`, closes on failure | Task 1 `test_create_app_closes_service_when_unready` |
| Not `require_populated_dictionary_index` | Task 1 `test_ensure_ready_accepts_entries_without_senses` |
| Ranking helpers stay on `browse_query`; delete `form_decode` copies | Task 2 |
| No rapidfuzz, no SQL ranking, no full-table-load rewrite | Global constraint; no task changes `search()` |
| Grids stay in `form_decode` | Global constraint; Task 2 does not move them |
| TUI filter/dedupe/`DataTable` stay | Global constraint |

Package advisor: DIY Levenshtein already selected in the ADR; no new dependency.
