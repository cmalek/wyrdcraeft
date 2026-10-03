# Dictionary CLI index gate and morph paths Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move dictionary-query table population checks and morphology default-path resolution out of `cli/dictionary.py` per ADR 0013.

**Architecture:** A module-level `require_populated_dictionary_index(db_path)` in `wyrdcraeft.services.dictionary.query` inspects mapped `BTEntry` / `BTSense` / `BTVariant` counts on a short-lived SQLAlchemy engine, then CLI constructs `BTQueryService` as today. Morphology default files stay the existing generation-runner policy, exported as public functions for `generate-reference-snapshots`. Browse TUI and `db.runtime` are unchanged.

**Tech Stack:** Python 3.11–3.13, SQLAlchemy, Click, pytest, ruff, mypy, `make napoleon-gate`, graphify.

**Spec:** [docs/adr/0013-index-population-gate-stays-on-dictionary-query.md](../../adr/0013-index-population-gate-stays-on-dictionary-query.md). Trello: https://trello.com/c/hZrnEtZD

## Global Constraints

- CLI has no business logic: no sqlite3 `COUNT`, no interpolated table names in `wyrdcraeft/cli/dictionary.py`.
- Do not put emptiness checks in `db.runtime`. Do not add `DictionaryTableStatsService` or a `BTQueryService` method/constructor gate.
- Do not change `browse_tui._ensure_browse_ready`.
- Do not resolve morph paths again in `dictionary build` before `MorphBuildOptions`; the runner already does that.
- Domain error is `DictionaryIndexNotPopulated` with `db_path` and `empty_tables` only. Its `str()` must not contain Click recovery copy (`dictionary build`, `missing required source tables`). CLI formats: `Canonical database {path} is missing required source tables: {names}. Run \`wyrdcraeft dictionary build\`.`
- Treat only SQLite missing-table operational errors as empty; do not swallow locked/corrupt DB as “unpopulated”.
- `require_populated_dictionary_index` must not create a SQLite file: if `db_path.is_file()` is false, raise `FileNotFoundError`.
- `dictionary query` after startup readiness: a “missing app-data DB” CLI test still hits the population gate because `ensure_database_ready` creates schema-empty sqlite first. Do not retarget that test at `_missing_canonical_index_message`.
- Morph path export is for `generate-reference-snapshots` only. Keep CLI `_default_morphology_data_dir` for `audit-wright`. Lazy-import `build_runner` inside the snapshot command (same pattern as `reference_snapshots`).
- After Python edits: `ruff` and `.venv/bin/mypy` on touched files, `make napoleon-gate`, `graphify update .`.
- Do not commit unless the user explicitly asks. Plan commit steps are optional for the implementer.
- Napoleon docs on new public types/functions; no empty sections.

## File map

| File | Role after this plan |
|------|----------------------|
| `wyrdcraeft/services/dictionary/query.py` | `DictionaryIndexNotPopulated` + `require_populated_dictionary_index`. |
| `wyrdcraeft/cli/dictionary.py` | Query maps population errors to Click; snapshots lazy-import runner path helpers; `_default_morphology_data_dir` remains for audit-wright. |
| `wyrdcraeft/services/morphology/build_runner.py` | Public `default_morphology_data_dir`, `resolve_morphology_input_paths`, `validate_morphology_input_paths`. |
| `tests/dictionary/test_query_service.py` | Service tests for the gate. |
| `tests/test_cli_dictionary.py` | Existing empty-index CLI test still passes; no sqlite3 in CLI module. |
| `tests/morphology/test_build_runner_paths.py` | Path default/override/missing-file tests. |
| `CONTEXT.md` / `docs/adr/0013-*.md` | Already written; do not rewrite unless the code forces a name change. |

---

### Task 1: Index population gate

**Files:**
- Modify: `wyrdcraeft/services/dictionary/query.py`
- Modify: `tests/dictionary/test_query_service.py`

**Interfaces:**
- Consumes: `create_sqlalchemy_engine`, mapped `BTEntry`, `BTSense`, `BTVariant`, `upgrade_canonical_db` in tests.
- Produces:
  - `class DictionaryIndexNotPopulated(RuntimeError)` with `db_path: Path` and `empty_tables: tuple[str, ...]`
  - `def require_populated_dictionary_index(db_path: Path) -> None`

- [ ] **Step 1: Write the failing tests**

Append to `tests/dictionary/test_query_service.py` (keep existing imports; add `pytest` is already imported; add `from sqlalchemy.exc import OperationalError` only if a test needs it — these tests should not catch SQLAlchemy errors themselves):

```python
def test_require_populated_dictionary_index_rejects_empty_migrated_db(
    tmp_path: Path,
) -> None:
    from wyrdcraeft.services.dictionary.query import (
        DictionaryIndexNotPopulated,
        require_populated_dictionary_index,
    )

    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)

    with pytest.raises(DictionaryIndexNotPopulated) as exc_info:
        require_populated_dictionary_index(db_path)

    assert exc_info.value.db_path == db_path.expanduser().resolve()
    assert exc_info.value.empty_tables == ("bt_entries", "bt_senses", "bt_variants")
    assert "wyrdcraeft dictionary build" not in str(exc_info.value)
    assert "missing required source tables" not in str(exc_info.value)


def test_require_populated_dictionary_index_rejects_missing_bt_tables(
    tmp_path: Path,
) -> None:
    from wyrdcraeft.services.dictionary.query import (
        DictionaryIndexNotPopulated,
        require_populated_dictionary_index,
    )

    db_path = tmp_path / "empty.sqlite3"
    sqlite3.connect(db_path).close()

    with pytest.raises(DictionaryIndexNotPopulated) as exc_info:
        require_populated_dictionary_index(db_path)

    assert exc_info.value.empty_tables == ("bt_entries", "bt_senses", "bt_variants")


def test_require_populated_dictionary_index_does_not_create_missing_file(
    tmp_path: Path,
) -> None:
    from wyrdcraeft.services.dictionary.query import (
        require_populated_dictionary_index,
    )

    db_path = tmp_path / "missing.sqlite3"
    with pytest.raises(FileNotFoundError):
        require_populated_dictionary_index(db_path)
    assert not db_path.exists()


def test_require_populated_dictionary_index_accepts_indexed_fixture(
    tmp_path: Path,
) -> None:
    from wyrdcraeft.services.dictionary.query import (
        require_populated_dictionary_index,
    )

    db_path = _index_fixture(_CORPUS_SAMPLE, tmp_path)
    require_populated_dictionary_index(db_path)


def test_require_populated_dictionary_index_reports_only_empty_tables(
    tmp_path: Path,
) -> None:
    from wyrdcraeft.services.dictionary.query import (
        DictionaryIndexNotPopulated,
        require_populated_dictionary_index,
    )

    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        pos_id = connection.execute(
            "SELECT id FROM parts_of_speech ORDER BY id LIMIT 1"
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO bt_entries (
                norm_key, headword, normalized_title, pos_id, genders_json,
                etymology, see_also_json, source_line_nos_json, entry_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("a", "a", "a", pos_id, "[]", "", "[]", "[]", 1),
        )
        connection.commit()

    with pytest.raises(DictionaryIndexNotPopulated) as exc_info:
        require_populated_dictionary_index(db_path)
    assert exc_info.value.empty_tables == ("bt_senses", "bt_variants")


def test_bt_query_service_constructs_on_empty_migrated_db(tmp_path: Path) -> None:
    from wyrdcraeft.services.dictionary.query import BTQueryService

    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    service = BTQueryService(db_path)
    try:
        assert service.lookup_lemma("abbod") == []
    finally:
        service.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/dictionary/test_query_service.py::test_require_populated_dictionary_index_rejects_empty_migrated_db -v`

Expected: FAIL with `ImportError` or `AttributeError` for `require_populated_dictionary_index`.

- [ ] **Step 3: Implement the gate**

In `wyrdcraeft/services/dictionary/query.py`:

- Import `BTSense` from `wyrdcraeft.models.sqlalchemy` (alongside `BTEntry`, `BTVariant`).
- Import `OperationalError` from `sqlalchemy.exc`.
- Keep `Path` in `TYPE_CHECKING`; add a runtime `from pathlib import Path` only if the exception/function signatures need it at runtime (they do — use `from pathlib import Path`).

Add after the POS maps (before `_normalize_title_key`):

```python
#: Lookup tables that must contain rows before ``dictionary query``.
_DICTIONARY_INDEX_TABLES: tuple[tuple[str, type[BTEntry] | type[BTSense] | type[BTVariant]], ...] = (
    ("bt_entries", BTEntry),
    ("bt_senses", BTSense),
    ("bt_variants", BTVariant),
)


class DictionaryIndexNotPopulated(RuntimeError):
    """Raised when required Bosworth-Toller lookup tables are missing or empty."""

    #: Canonical SQLite path that was inspected.
    db_path: Path
    #: Table names that were missing or had zero rows, in check order.
    empty_tables: tuple[str, ...]

    def __init__(self, db_path: Path, empty_tables: tuple[str, ...]) -> None:
        """
        Record which required lookup tables were empty or absent.

        Args:
            db_path: Canonical SQLite path that was inspected.
            empty_tables: Table names that were missing or had zero rows.

        """
        self.db_path = db_path
        self.empty_tables = empty_tables
        super().__init__(
            f"{db_path}: empty or missing tables: {', '.join(empty_tables)}"
        )


def require_populated_dictionary_index(db_path: Path) -> None:
    """
    Fail when required ``bt_*`` lookup tables are missing or empty.

    Args:
        db_path: Existing canonical SQLite file to inspect.

    Raises:
        FileNotFoundError: ``db_path`` is not an existing file.
        DictionaryIndexNotPopulated: A required table is absent or has no rows.

    """
    resolved = db_path.expanduser().resolve()
    if not resolved.is_file():
        msg = f"Canonical database not found: {resolved}"
        raise FileNotFoundError(msg)

    engine = create_sqlalchemy_engine(resolved)
    empty: list[str] = []
    try:
        with engine.connect() as connection:
            for table_name, model in _DICTIONARY_INDEX_TABLES:
                try:
                    count = connection.execute(
                        select(func.count()).select_from(model)
                    ).scalar_one()
                except OperationalError as exc:
                    if "no such table" not in str(exc).casefold():
                        raise
                    empty.append(table_name)
                    continue
                if int(count) == 0:
                    empty.append(table_name)
    finally:
        engine.dispose()

    if empty:
        raise DictionaryIndexNotPopulated(resolved, tuple(empty))
```

If the `_DICTIONARY_INDEX_TABLES` union type is too noisy for mypy, use `tuple[tuple[str, type], ...]` and keep the three pairs.

Update `__all__` at the bottom of `query.py` to:

```python
__all__ = [
    "BTQueryService",
    "DictionaryIndexNotPopulated",
    "entry_to_dict",
    "require_populated_dictionary_index",
]
```

Do not export these from `wyrdcraeft/services/dictionary/__init__.py` unless an import already expected them (it does not).

- [ ] **Step 4: Run the new tests**

Run: `.venv/bin/pytest tests/dictionary/test_query_service.py -k "require_populated_dictionary_index or constructs_on_empty_migrated" -v`

Expected: 6 passed (`require_populated_*` plus `test_bt_query_service_constructs_on_empty_migrated_db`).

- [ ] **Step 5: Commit (only if the user asked)**

```bash
git add wyrdcraeft/services/dictionary/query.py tests/dictionary/test_query_service.py
git commit -m "feat: inspect dictionary index population in the query module"
```

---

### Task 2: CLI query uses the gate

**Files:**
- Modify: `wyrdcraeft/cli/dictionary.py`
- Test: `tests/test_cli_dictionary.py`

**Interfaces:**
- Consumes: `require_populated_dictionary_index`, `DictionaryIndexNotPopulated`
- Produces: same Click error text as today for schema-ready empty DB

- [ ] **Step 1: Write / adjust the failing CLI assertion if needed**

Keep `test_dictionary_query_missing_morphology_db_fails` as-is. It does **not** assert the missing-file message: root `cli()` runs `ensure_database_ready` first, which creates schema-empty `wyrdcraeft.sqlite3`, then query hits the population gate. Add an explicit migrate-then-query test:

```python
def test_dictionary_query_empty_canonical_db_fails(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    from wyrdcraeft.db.runtime import upgrade_canonical_db

    upgrade_canonical_db(isolated_morphology_index_db)
    result = runner.invoke(cli, ["dictionary", "query", "abbod"])
    assert result.exit_code != 0
    assert (
        "missing required source tables: bt_entries, bt_senses, bt_variants"
        in result.output
    )
    assert "wyrdcraeft dictionary build" in result.output
```

- [ ] **Step 2: Run the new CLI test to see current behavior**

Run: `.venv/bin/pytest tests/test_cli_dictionary.py::test_dictionary_query_empty_canonical_db_fails tests/test_cli_dictionary.py::test_dictionary_query_missing_morphology_db_fails -v`

Expected: both may already pass via the old sqlite3 helpers. If the new one fails, fix after the CLI switch.

- [ ] **Step 3: Wire CLI and delete sqlite3 probes**

In `wyrdcraeft/cli/dictionary.py`:

1. Remove `import sqlite3`.
2. Change the query import to:

```python
from wyrdcraeft.services.dictionary.query import (
    BTQueryService,
    DictionaryIndexNotPopulated,
    entry_to_dict,
    require_populated_dictionary_index,
)
```

3. Delete `_count_table_rows` and `_require_non_empty_tables` entirely.

4. In `query()`, keep the missing-file `ClickException` using `_missing_canonical_index_message`. Replace `_require_non_empty_tables(...)` with:

```python
    try:
        require_populated_dictionary_index(resolved_index_db)
    except DictionaryIndexNotPopulated as exc:
        missing_text = ", ".join(exc.empty_tables)
        raise click.ClickException(
            f"Canonical database {exc.db_path} is missing required source tables: "
            f"{missing_text}. Run `wyrdcraeft dictionary build`."
        ) from exc
```

5. Confirm `rg sqlite3 wyrdcraeft/cli/dictionary.py` has no remaining import or `COUNT`.

- [ ] **Step 4: Run CLI dictionary tests**

Run: `.venv/bin/pytest tests/test_cli_dictionary.py -v`

Expected: all passed. In particular both empty-index tests still mention `bt_entries, bt_senses, bt_variants` and `dictionary build`, not `morphology build`.

- [ ] **Step 5: Commit (only if the user asked)**

```bash
git add wyrdcraeft/cli/dictionary.py tests/test_cli_dictionary.py
git commit -m "refactor: map dictionary query population errors from the query module"
```

---

### Task 3: Export morph path policy from the generation runner

**Files:**
- Modify: `wyrdcraeft/services/morphology/build_runner.py`
- Create: `tests/morphology/test_build_runner_paths.py`
- Modify: `wyrdcraeft/cli/dictionary.py` (`generate-reference-snapshots` only; keep `_default_morphology_data_dir` for `audit-wright`)

**Interfaces:**
- Consumes: existing `_default_morphology_data_dir`, `_resolve_input_paths`, `_validate_inputs`, `MorphologyBuildRunnerError`
- Produces:
  - `def default_morphology_data_dir() -> Path`
  - `def resolve_morphology_input_paths(*, data_dir: Path, dictionary: Path | None, manual_forms: Path | None, verbal_paradigms: Path | None, prefixes: Path | None) -> tuple[Path, Path, Path, Path]`
  - `def validate_morphology_input_paths(paths: tuple[Path, Path, Path, Path]) -> None` raising `MorphologyBuildRunnerError`

- [ ] **Step 1: Write failing path tests**

Create `tests/morphology/test_build_runner_paths.py`:

```python
"""Morphology input path defaults live on the generation runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from wyrdcraeft.services.morphology.build_runner import (
    MorphologyBuildRunnerError,
    default_morphology_data_dir,
    resolve_morphology_input_paths,
    validate_morphology_input_paths,
)


def test_resolve_morphology_input_paths_uses_data_dir_defaults(
    tmp_path: Path,
) -> None:
    dictionary, manual, paradigms, prefixes = resolve_morphology_input_paths(
        data_dir=tmp_path,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    assert dictionary == tmp_path / "dict_adj-vb-part-num-adv-noun.txt"
    assert manual == tmp_path / "manual_forms.txt"
    assert paradigms == tmp_path / "para_vb.txt"
    assert prefixes == tmp_path / "prefixes.txt"


def test_resolve_morphology_input_paths_keeps_overrides(tmp_path: Path) -> None:
    override = tmp_path / "custom.txt"
    dictionary, _, _, _ = resolve_morphology_input_paths(
        data_dir=tmp_path,
        dictionary=override,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    assert dictionary == override


def test_validate_morphology_input_paths_raises_for_missing_file(
    tmp_path: Path,
) -> None:
    paths = resolve_morphology_input_paths(
        data_dir=tmp_path,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    with pytest.raises(MorphologyBuildRunnerError, match="Missing dictionary file"):
        validate_morphology_input_paths(paths)


def test_packaged_default_morphology_data_dir_exists() -> None:
    data_dir = default_morphology_data_dir()
    assert data_dir.is_dir()
    assert (data_dir / "dict_adj-vb-part-num-adv-noun.txt").is_file()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/morphology/test_build_runner_paths.py -v`

Expected: FAIL on import of the public names.

- [ ] **Step 3: Rename internals to public functions**

In `wyrdcraeft/services/morphology/build_runner.py`:

- Rename `_default_morphology_data_dir` → `default_morphology_data_dir`
- Rename `_resolve_input_paths` → `resolve_morphology_input_paths`
- Rename `_validate_inputs` → `validate_morphology_input_paths`
- Update `run_morphology_generation` to call the new names (same bodies, same `MorphologyBuildRunnerError` messages).
- Do not change filename defaults (`dict_adj-vb-part-num-adv-noun.txt`, `manual_forms.txt`, `para_vb.txt`, `prefixes.txt`).

- [ ] **Step 4: Point CLI snapshots at the runner (lazy import)**

In `generate_reference_snapshots_command` only (do **not** add a module-level `build_runner` import; do **not** delete `_default_morphology_data_dir`; leave `audit-wright` filename joins as they are):

- Delete `_resolve_morphology_input_paths` and `_validate_morphology_inputs`.
- Inside the command, lazy-import like `reference_snapshots`:

```python
    from wyrdcraeft.services.morphology.build_runner import (  # noqa: PLC0415
        MorphologyBuildRunnerError,
        default_morphology_data_dir,
        resolve_morphology_input_paths,
        validate_morphology_input_paths,
    )

    resolved_data_dir = data_dir or default_morphology_data_dir()
    resolved_paths = resolve_morphology_input_paths(
        data_dir=resolved_data_dir,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    try:
        validate_morphology_input_paths(resolved_paths)
    except MorphologyBuildRunnerError as exc:
        raise click.ClickException(str(exc)) from exc
    full_dictionary, manual_forms, verbal_paradigms, prefixes = resolved_paths
```

Keep the existing `subset_dictionary` missing-file `ClickException`. Fold `MorphologyBuildRunnerError` into the generate `try` as well:

```python
    except (OSError, ValueError, FileExistsError, MorphologyBuildRunnerError) as e:
        raise click.ClickException(str(e)) from e
```

Leave `wyrdcraeft/cli/morphology.py` default-dir helper alone (out of this card).

- [ ] **Step 5: Run path tests and CLI snapshot help/smoke**

Run:

```bash
.venv/bin/pytest tests/morphology/test_build_runner_paths.py tests/test_cli_dictionary.py -v
```

Expected: all passed. `rg "_resolve_morphology_input_paths|_count_table_rows" wyrdcraeft/cli/dictionary.py` empty.

- [ ] **Step 6: Quality gate + graphify**

```bash
.venv/bin/ruff check wyrdcraeft/services/dictionary/query.py wyrdcraeft/cli/dictionary.py wyrdcraeft/services/morphology/build_runner.py tests/dictionary/test_query_service.py tests/test_cli_dictionary.py tests/morphology/test_build_runner_paths.py
.venv/bin/mypy wyrdcraeft/services/dictionary/query.py wyrdcraeft/cli/dictionary.py wyrdcraeft/services/morphology/build_runner.py
make napoleon-gate
graphify update .
```

Expected: ruff/mypy clean on touched files; napoleon-gate no new violations; graphify AST update succeeds.

- [ ] **Step 7: Commit (only if the user asked)**

```bash
git add wyrdcraeft/services/morphology/build_runner.py wyrdcraeft/cli/dictionary.py tests/morphology/test_build_runner_paths.py
git commit -m "refactor: share morphology input path policy from the generation runner"
```

---

## Spec coverage

| ADR / card requirement | Task |
|------------------------|------|
| Gate not in `db.runtime` | 1 |
| Module-level inspect, not `BTQueryService` method | 1 |
| SQLAlchemy mapped counts, no CLI sqlite3 interpolation | 1–2 |
| CLI maps domain error + `dictionary build` hint | 2 |
| Missing file does not create sqlite | 1 |
| Browse unchanged | (explicit non-goal) |
| Morph resolver exported; snapshots stop duplicating; build still passes overrides; audit-wright data-dir helper stays | 3 |
| Tests in `test_cli_dictionary.py` + service tests | 1–2 |
| Quality gate + `graphify update .` | 3 |

## Self-review

- No TBD placeholders.
- Public names are consistent across tasks: `require_populated_dictionary_index`, `DictionaryIndexNotPopulated`, `resolve_morphology_input_paths`, `validate_morphology_input_paths`, `default_morphology_data_dir`.
- `_DICTIONARY_INDEX_TABLES` typing may need a mypy simplification; that is called out in Task 1.
