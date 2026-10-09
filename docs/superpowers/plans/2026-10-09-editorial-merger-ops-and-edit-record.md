# Editorial merger ops and edit record Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ADR 0021: move `BTEditRecord` into dictionary models, extract over-budget Substitute/Dele/Dele-and-add ops into private collaborators, shrink `_merge_block`, and leave Add plus cross-refs on the merger.

**Architecture:** `BTEditorialMerger` stays the facade (`merge`, `collect_editorial_warnings`). It constructs `BTSubstituteOp`, `BTDeleOp`, and `BTDeleAndAddOp` in `__init__` from the already-injected `resolver`. Those three classes plus `append_senses` live in one `editorial_ops.py`. Substitute may audit a foreign source block via `all_blocks`. Do not add constructor args for ops. Do not re-export `BTEditRecord` from `wyrdcraeft.services.dictionary`.

**Tech Stack:** Python 3.11–3.13, stdlib `@dataclass`, pytest, ruff, mypy, `make napoleon-gate`, graphify.

**Spec:** [docs/adr/0021-editorial-merger-ops-and-edit-record.md](../../adr/0021-editorial-merger-ops-and-edit-record.md). Trello https://trello.com/c/Gwr8hysN (ADR overrides the card on injection, Add-as-class, services re-export, and a separate models module).

## Global Constraints

- Structure only. Editorial merge results and edit-record fields must match current characterization tests. Do not “fix” substitute/dele while moving them.
- Canonical import: `from wyrdcraeft.models.dictionary import BTEditRecord`. Export it from `wyrdcraeft.models`. No alias on `wyrdcraeft.services.dictionary`.
- Public merger constructor stays `(resolver=None, block_builder=None)`. Ops are private, built inside `__init__`.
- One file `editorial_ops.py`. Classes: `BTSubstituteOp`, `BTDeleOp`, `BTDeleAndAddOp`. No `BTAddOp`. No op registry.
- Every new or moved method/function body ≤ 60 lines. No new `PLR0912` / `PLR0915` noqa. Moving a 165-line method is not done. Methods that do not use instance state are `@staticmethod` (no `# noqa: ARG002`).
- Line-budget tests walk functions defined in `editorial_ops.py` and methods on `BTEditorialMerger`. They must not name collaborator private methods. Skip only `collect_editorial_warnings` (pre-existing, out of this card).
- `append_senses` is a module-level function in `editorial_ops.py`. `_extend_senses` / `_next_top_level_path` stay on the merger.
- `_apply_cross_refs` stays on the merger, unchanged.
- `_plain`, `_target_note`, Substitute/Dele regexes move with the ops. `_edit_note_reason` / `_edit_note_detail` stay on the merger (warnings).
- No new packages. Package-advisor planning lookup: `status=no_match`.
- Napoleon on new public classes/functions; `#:` on `__init__` attributes; no empty docstring sections.
- After Python edits: `.venv/bin/ruff check` and `.venv/bin/mypy` on touched files, `make napoleon-gate`, `graphify update .`.
- Do not commit unless the user explicitly asks. Plan commit steps are optional.
- Do not assert collaborator internals in merger tests (no `merger._substitute_op`).

## File map

| File | Role after this plan |
|------|----------------------|
| `wyrdcraeft/models/dictionary.py` | `BTEditRecord` next to `BTEditorialOp`. |
| `wyrdcraeft/models/__init__.py` | Export `BTEditRecord`. |
| `wyrdcraeft/services/dictionary/editorial_ops.py` | Regexes, `_plain`, `_target_note`, `_make_edit_record`, `append_senses`, three op classes. |
| `wyrdcraeft/services/dictionary/editorial_merger.py` | Facade: seed/`_merge_block` dispatch, Add, cross-refs, warnings. No `BTEditRecord` class. |
| `wyrdcraeft/services/dictionary/__init__.py` | `BTEditorialMerger` only from this package; no `BTEditRecord`. |
| `wyrdcraeft/services/dictionary/sinks.py` | `TYPE_CHECKING` import of `BTEditRecord` from models. |
| `tests/dictionary/test_editorial_merger.py` | Import `BTEditRecord` from models. Existing merge tests unchanged. |
| `tests/dictionary/test_editorial_op_modules.py` | Import-home + line-budget + constructor-seam contract. |
| `docs/adr/0021-editorial-merger-ops-and-edit-record.md` | Status → accepted after the landing. |
| `CONTEXT.md` | ADR 0021 index bullet: drop “proposed; not implemented”. |

## Review Focus

- `sinks.py` imports models, not `editorial_merger`.
- `BTEditorialMerger.__init__` still has only `resolver` and `block_builder`.
- Substitute `for_X_in_Dict` still records `applied=False` and does not rewrite the foreign block (current behavior).
- `_merge_block` after split is dispatch-only and ≤ 60 lines.
- No `BTEditRecord` in `wyrdcraeft.services.dictionary.__all__`.
- Unused-`self` methods are `@staticmethod`. Line-budget test does not name `_for_x_in_dict` or other op privates.

---

### Task 1: Import-home contract tests

**Files:**
- Create: `tests/dictionary/test_editorial_op_modules.py`

**Interfaces:**
- Consumes: nothing from later tasks.
- Produces: failing tests that require `BTEditRecord` on `wyrdcraeft.models.dictionary` and that `wyrdcraeft.services.dictionary` does not export it.

- [ ] **Step 1: Write the failing tests**

Create `tests/dictionary/test_editorial_op_modules.py`:

```python
"""ADR 0021: edit record lives in models; merger does not re-export it."""

from __future__ import annotations

import inspect

from wyrdcraeft.services.dictionary.editorial_merger import BTEditorialMerger


def test_bt_edit_record_imports_from_models_dictionary() -> None:
    from wyrdcraeft.models.dictionary import BTEditRecord

    assert BTEditRecord.__name__ == "BTEditRecord"


def test_bt_edit_record_exported_from_wyrdcraeft_models() -> None:
    from wyrdcraeft.models import BTEditRecord

    assert BTEditRecord.__module__ == "wyrdcraeft.models.dictionary"


def test_services_dictionary_does_not_export_bt_edit_record() -> None:
    from wyrdcraeft.services import dictionary as dictionary_pkg

    assert "BTEditRecord" not in dictionary_pkg.__all__
    assert not hasattr(dictionary_pkg, "BTEditRecord")


def test_merger_constructor_only_resolver_and_block_builder() -> None:
    params = inspect.signature(BTEditorialMerger.__init__).parameters
    assert set(params) == {"self", "resolver", "block_builder"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/dictionary/test_editorial_op_modules.py -v
```

Expected: `test_bt_edit_record_imports_from_models_dictionary` FAIL (`ImportError`). `test_services_dictionary_does_not_export_bt_edit_record` FAIL (name is still in `__all__` / attributes). Constructor test PASS already.

Do **not** commit this file red. Leave it unstaged until Task 2 is green.

---

### Task 2: Move `BTEditRecord` to models

**Files:**
- Modify: `wyrdcraeft/models/dictionary.py` (insert after `BTEditorialOp`, before `format_sense_display_label`)
- Modify: `wyrdcraeft/models/__init__.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py`
- Modify: `wyrdcraeft/services/dictionary/__init__.py`
- Modify: `wyrdcraeft/services/dictionary/sinks.py`
- Modify: `tests/dictionary/test_editorial_merger.py`
- Test: `tests/dictionary/test_editorial_op_modules.py`
- Test: `tests/dictionary/test_editorial_merger.py`

**Interfaces:**
- Consumes: Task 1 tests.
- Produces: `@dataclass class BTEditRecord` in `wyrdcraeft.models.dictionary` with fields `op: BTEditorialOp`, `source_line_no: int`, `target_norm_key: str`, `target_pos: BTPos`, `scope: str`, `applied: bool`, `note: str = ""`, `entry_order: int = 0`, `source_block_index: int = 0`.

- [ ] **Step 1: Add the dataclass next to `BTEditorialOp`**

In `wyrdcraeft/models/dictionary.py`, ensure `dataclass` is already imported (it is). Insert immediately after the `BTEditorialOp` enum (after `DELE_AND_ADD = "dele_and_add"` and the enum’s closing), before `format_sense_display_label`:

```python
@dataclass
class BTEditRecord:
    """
    Audit record for one editorial operation applied during entry consolidation.

    Suitable for storage in a ``bt_edit_log`` SQLite table in later phases.

    Attributes:
        op: The editorial operation kind.
        source_line_no: One-based source line number that triggered this operation.
        target_norm_key: Normalised lookup key of the entry being modified.
        target_pos: Part of speech of the entry being modified.
        scope: Human-readable description of what was affected (``all_senses``,
            ``sense_path:1``, ``for_X_in_Dict``, etc.).
        applied: Whether the operation was actually applied or skipped.
        note: Additional diagnostic text.
        entry_order: Stable source-block ordering for homograph disambiguation.
        source_block_index: Zero-based source block index for audit joins.

    """

    #: Editorial operation kind.
    op: BTEditorialOp
    #: Source file line number.
    source_line_no: int
    #: Norm key of the modified entry.
    target_norm_key: str
    #: POS of the modified entry.
    target_pos: BTPos
    #: Scope description for audit.
    scope: str
    #: Whether the op was applied.
    applied: bool
    #: Diagnostic note.
    note: str = ""
    #: Stable source-block ordering for homograph disambiguation.
    entry_order: int = 0
    #: Zero-based source block index for audit joins.
    source_block_index: int = 0
```

Copy this verbatim from the current class in `editorial_merger.py` (lines 72–110). Then delete that class from `editorial_merger.py`. If `dataclass` is unused after the move, drop it from the merger import but **keep** `replace` (`_extend_senses` still uses it).

- [ ] **Step 2: Point merger, models barrel, sinks, tests, and the services package at the new home**

`editorial_merger.py` import block — add `BTEditRecord` to the existing models import:

```python
from ...models.dictionary import (
    BTConsolidatedEntry,
    BTEditRecord,
    BTEditorialOp,
    BTLineKind,
    BTParseWarning,
    BTPos,
    BTSense,
)
```

`wyrdcraeft/models/__init__.py` — add `BTEditRecord` to the `.dictionary` import and to `__all__` (after `BTEditorialOp`):

```python
from .dictionary import (
    BTConsolidatedEntry,
    BTEditRecord,
    BTEditorialOp,
    BTGender,
    BTLineKind,
    BTParseWarning,
    BTPos,
    BTSense,
    RawBTLine,
)
```

```python
    "BTEditRecord",
    "BTEditorialOp",
```

`wyrdcraeft/services/dictionary/__init__.py`:

```python
from .editorial_merger import BTEditorialMerger
```

Remove `"BTEditRecord"` from `__all__`.

`sinks.py` TYPE_CHECKING block:

```python
    from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTEditRecord, BTGender
```

Delete `from wyrdcraeft.services.dictionary.editorial_merger import BTEditRecord`.

`tests/dictionary/test_editorial_merger.py`:

```python
from wyrdcraeft.models.dictionary import (
    BTConsolidatedEntry,
    BTEditRecord,
    BTLineKind,
    BTPos,
)
from wyrdcraeft.services.dictionary.editorial_merger import BTEditorialMerger
```

- [ ] **Step 3: Run contract + characterization tests**

```bash
.venv/bin/pytest tests/dictionary/test_editorial_op_modules.py tests/dictionary/test_editorial_merger.py -v
```

Expected: PASS.

- [ ] **Step 4: Quality on the moved model**

```bash
.venv/bin/ruff check wyrdcraeft/models/dictionary.py wyrdcraeft/models/__init__.py wyrdcraeft/services/dictionary/editorial_merger.py wyrdcraeft/services/dictionary/__init__.py wyrdcraeft/services/dictionary/sinks.py tests/dictionary/test_editorial_merger.py tests/dictionary/test_editorial_op_modules.py
.venv/bin/mypy wyrdcraeft/models/dictionary.py wyrdcraeft/models/__init__.py wyrdcraeft/services/dictionary/editorial_merger.py wyrdcraeft/services/dictionary/__init__.py wyrdcraeft/services/dictionary/sinks.py tests/dictionary/test_editorial_merger.py tests/dictionary/test_editorial_op_modules.py
make napoleon-gate
```

Expected: ruff/mypy clean on these paths; napoleon-gate no new violations.

---

### Task 3: `editorial_ops.py` collaborators and merger wiring

**Files:**
- Create: `wyrdcraeft/services/dictionary/editorial_ops.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py`
- Test: `tests/dictionary/test_editorial_merger.py` (run only; do not add collaborator-internal asserts)

**Interfaces:**
- Consumes: `BTEditRecord` from Task 2; `BTTargetResolver`.
- Produces:
  - `append_senses(entry: BTConsolidatedEntry, new_senses: tuple[BTSense, ...]) -> int`
  - `BTSubstituteOp(resolver: BTTargetResolver)` with `apply(entry, line, all_blocks, block) -> list[BTEditRecord]`
  - `BTDeleOp(resolver: BTTargetResolver)` with `apply(entry, line, block) -> list[BTEditRecord]`
  - `BTDeleAndAddOp(resolver: BTTargetResolver)` with `apply(entry, line, block) -> list[BTEditRecord]`
  - Merger attributes `self._substitute_op`, `self._dele_op`, `self._dele_and_add_op` constructed in `__init__` from `self.resolver`.

- [ ] **Step 1: Add the line-budget tests to the contract file (they will fail until Step 4 of this task if you implement fat methods — implement the split in the same task so this stays one green landing)**

Append to `tests/dictionary/test_editorial_op_modules.py`:

```python
import ast
import inspect
import textwrap
from collections.abc import Iterator

from wyrdcraeft.services.dictionary import editorial_ops
from wyrdcraeft.services.dictionary.editorial_merger import BTEditorialMerger

# Pre-existing, out of ADR 0021. Do not treat as a collaborator split.
_LINE_BUDGET_SKIP = frozenset({"collect_editorial_warnings"})


def _body_line_count(obj: object) -> int:
    source = textwrap.dedent(inspect.getsource(obj))
    tree = ast.parse(source)
    node = tree.body[0]
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if not body:
        return 0
    start = body[0].lineno
    end = max(getattr(stmt, "end_lineno", stmt.lineno) or stmt.lineno for stmt in body)
    return end - start + 1


def _local_functions(container: object) -> Iterator[object]:
    home = container.__name__ if inspect.ismodule(container) else container.__module__
    for name, obj in inspect.getmembers(container, inspect.isfunction):
        if name.startswith("__"):
            continue
        if inspect.ismodule(container) and obj.__module__ != home:
            continue
        if inspect.isclass(container) and obj.__module__ != container.__module__:
            continue
        yield obj


def test_editorial_op_method_bodies_within_line_budget() -> None:
    targets: list[object] = list(_local_functions(editorial_ops))
    for _cls_name, cls in inspect.getmembers(editorial_ops, inspect.isclass):
        if cls.__module__ != editorial_ops.__name__:
            continue
        targets.extend(_local_functions(cls))
    for obj in _local_functions(BTEditorialMerger):
        if obj.__name__ in _LINE_BUDGET_SKIP:
            continue
        targets.append(obj)
    offenders = [
        f"{obj.__qualname__}={_body_line_count(obj)}"
        for obj in targets
        if _body_line_count(obj) > 60
    ]
    assert not offenders, "method bodies exceed 60 lines: " + ", ".join(offenders)


def test_editorial_ops_module_exists() -> None:
    assert editorial_ops.__name__ == "wyrdcraeft.services.dictionary.editorial_ops"
```

- [ ] **Step 2: Run to verify new imports fail**

```bash
.venv/bin/pytest tests/dictionary/test_editorial_op_modules.py -v
```

Expected: FAIL `ModuleNotFoundError` for `editorial_ops`.

- [ ] **Step 3: Create `wyrdcraeft/services/dictionary/editorial_ops.py`**

Paste the file below. Behavior must match today’s `_apply_substitute` / `_apply_dele` / `_apply_dele_and_add` / `_append_senses` (including `for_X_in_Dict` remaining `applied=False`). `BTDeleOp.apply` must fall through to `unknown` when the Dele HTML match has non-empty `scope_text` and there are no `dele_refs` — do not return `[]` from that branch.

```python
"""Editorial operation collaborators for Bosworth-Toller consolidation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from ...models.dictionary import BTEditRecord, BTEditorialOp, BTPos, BTSense
from ..markup import normalize_old_english

if TYPE_CHECKING:
    from ...models.dictionary import BTConsolidatedEntry
    from .line_parser import ParsedBTLine
    from .source_blocks import BTSourceBlock
    from .target_resolver import BTTargetResolver

_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
_FOR_ALL_BUT_RE: Final[re.Pattern[str]] = re.compile(
    r"for all but\s+(.+?)(?:\s*$|:)",
    re.IGNORECASE,
)
_SUBSTITUTE_FOR_X_RE: Final[re.Pattern[str]] = re.compile(
    r"substitute the following for\s+(.+?)\s+in\s+Dict",
    re.IGNORECASE,
)
_SUBSTITUTE_FOLLOWING_RE: Final[re.Pattern[str]] = re.compile(
    r"substitute the following[:\s]",
    re.IGNORECASE,
)
_DELE_SCOPE_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>\s*Dele\b([^<]*)</I>",
    re.IGNORECASE,
)


def _plain(text: str) -> str:
    """
    Strip HTML tags and collapse whitespace from *text*.

    Args:
        text: Input HTML string.

    Returns:
        Plain-text string with normalised whitespace.

    """
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


def _target_note(reason: str, detail: str) -> str:
    """
    Format one standardized edit-log note with human context.

    Args:
        reason: Machine-readable note code such as ``target_missing``.
        detail: Human-readable diagnostic context.

    Returns:
        Combined note string for ``bt_edit_log``.

    """
    detail = detail.strip()
    if detail:
        return f"{reason}: {detail}"
    return reason


def _make_edit_record(
    *,
    op: BTEditorialOp,
    line: ParsedBTLine,
    entry: BTConsolidatedEntry,
    block: BTSourceBlock,
    scope: str,
    applied: bool,
    note: str = "",
    target_norm_key: str | None = None,
    target_pos: BTPos | None = None,
    entry_order: int | None = None,
    source_block_index: int | None = None,
) -> BTEditRecord:
    """
    Build one :class:`BTEditRecord` from a line and source block.

    Keyword Args:
        op: Editorial operation kind.
        line: Parsed editorial line; ``raw_line`` must be set.
        entry: Entry used for default target key and POS.
        block: Source block used for default audit indices.
        scope: Audit scope string.
        applied: Whether the operation took effect.
        note: Diagnostic note.
        target_norm_key: Override for the target key.
        target_pos: Override for the target POS.
        entry_order: Override for ``entry_order``.
        source_block_index: Override for ``source_block_index``.

    Returns:
        Populated audit record.

    Raises:
        ValueError: If *line* has no ``raw_line``.

    """
    raw = line.raw_line
    if raw is None:
        msg = "editorial line is missing raw_line"
        raise ValueError(msg)
    return BTEditRecord(
        op=op,
        source_line_no=raw.line_no,
        target_norm_key=entry.norm_key if target_norm_key is None else target_norm_key,
        target_pos=entry.pos if target_pos is None else target_pos,
        scope=scope,
        applied=applied,
        note=note,
        entry_order=block.entry_order if entry_order is None else entry_order,
        source_block_index=(
            block.source_block_index if source_block_index is None else source_block_index
        ),
    )


def append_senses(
    entry: BTConsolidatedEntry,
    new_senses: tuple[BTSense, ...],
) -> int:
    """
    Append supplemental senses using label-aware deduplication.

    Unlabelled senses always append. Labelled senses append only when their
    ``source_label_raw`` is not already present on the entry.

    Args:
        entry: Entry being augmented.
        new_senses: Candidate senses from one ADD or DELE_AND_ADD line.

    Returns:
        Number of senses appended.

    """
    existing_labels = {
        sense.source_label_raw.rstrip(".") for sense in entry.senses
    }
    appended = 0
    for sense in new_senses:
        raw_label = sense.source_label_raw.rstrip(".")
        if raw_label not in existing_labels or not raw_label:
            entry.senses.append(sense)
            existing_labels.add(raw_label)
            appended += 1
    return appended


class BTSubstituteOp:
    """
    Apply one SUBSTITUTE line to the current entry or a cross-entry target.

    Args:
        resolver: Target-resolver used for ``for all but`` sense paths.

    """

    def __init__(self, resolver: BTTargetResolver) -> None:
        """
        Bind the resolver used for sense-path lookup.

        Args:
            resolver: Target-resolver collaborator.

        """
        #: Sense-path resolver.
        self.resolver: BTTargetResolver = resolver

    def apply(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        all_blocks: list[BTSourceBlock],
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Dispatch one SUBSTITUTE line.

        Args:
            entry: Entry for the current source block.
            line: Parsed SUBSTITUTE line.
            all_blocks: All blocks, for ``for X in Dict`` lookup.
            block: Current source block for audit metadata.

        Returns:
            Audit records. Cross-entry hits stay ``applied=False``.

        """
        if line.raw_line is None:
            return []
        plain_body = _plain(line.raw_line.raw_text)
        if _SUBSTITUTE_FOR_X_RE.search(plain_body):
            return self._for_x_in_dict(entry, line, all_blocks, block, plain_body)
        if _SUBSTITUTE_FOLLOWING_RE.search(plain_body):
            return self._replace_following(entry, line, block)
        if _FOR_ALL_BUT_RE.search(plain_body):
            return self._for_all_but(entry, line, block, plain_body)
        return self._fallback(entry, line, block)

    @staticmethod
    def _for_x_in_dict(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        all_blocks: list[BTSourceBlock],
        block: BTSourceBlock,
        plain_body: str,
    ) -> list[BTEditRecord]:
        match = _SUBSTITUTE_FOR_X_RE.search(plain_body)
        if match is None:
            return []
        target_text = match.group(1).strip()
        target_norm = normalize_old_english(target_text) or ""
        target_blocks = [
            candidate for candidate in all_blocks if candidate.norm_key == target_norm
        ]
        scope = f"for_X_in_Dict:{target_text}"
        if len(target_blocks) == 1:
            target = target_blocks[0]
            return [
                _make_edit_record(
                    op=BTEditorialOp.SUBSTITUTE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope=scope,
                    applied=False,
                    note="cross-entry substitute deferred; target in different block",
                    target_norm_key=target_norm,
                    target_pos=target.pos,
                    entry_order=target.entry_order,
                    source_block_index=target.source_block_index,
                )
            ]
        if not target_blocks:
            return [
                _make_edit_record(
                    op=BTEditorialOp.SUBSTITUTE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope=scope,
                    applied=False,
                    note=_target_note(
                        "target_missing",
                        f"cross-entry target {target_text!r} not found",
                    ),
                    target_norm_key=target_norm,
                )
            ]
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope=scope,
                applied=False,
                note=_target_note(
                    "target_ambiguous",
                    f"multiple blocks match {target_text!r}",
                ),
                target_norm_key=target_norm,
            )
        ]

    @staticmethod
    def _replace_following(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        if line.senses:
            entry.senses = list(line.senses)
            return [
                _make_edit_record(
                    op=BTEditorialOp.SUBSTITUTE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope="all_senses",
                    applied=True,
                )
            ]
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope="all_senses",
                applied=False,
                note="substitute line has no parsed senses",
            )
        ]

    def _for_all_but(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
        plain_body: str,
    ) -> list[BTEditRecord]:
        match = _FOR_ALL_BUT_RE.search(plain_body)
        if match is None:
            return []
        pinned_raw = match.group(1).strip()
        pinned_paths: set[str] = set()
        for label in re.split(r"[,;]", pinned_raw):
            cleaned = label.strip().rstrip(".")
            if not cleaned:
                continue
            path = self.resolver.resolve_sense_path(cleaned, entry.senses)
            if path is not None:
                pinned_paths.add(path)
        kept = [sense for sense in entry.senses if sense.sense_path in pinned_paths]
        entry.senses = kept + list(line.senses)
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope=f"for_all_but:{pinned_raw}",
                applied=True,
            )
        ]

    @staticmethod
    def _fallback(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        if not line.senses:
            return []
        entry.senses = list(line.senses)
        return [
            _make_edit_record(
                op=BTEditorialOp.SUBSTITUTE,
                line=line,
                entry=entry,
                block=block,
                scope="all_senses_fallback",
                applied=True,
            )
        ]


class BTDeleOp:
    """
    Apply one DELE line to the current entry.

    Args:
        resolver: Target-resolver used for ``dele_refs`` sense paths.

    """

    def __init__(self, resolver: BTTargetResolver) -> None:
        """
        Bind the resolver used for sense-path lookup.

        Args:
            resolver: Target-resolver collaborator.

        """
        #: Sense-path resolver.
        self.resolver: BTTargetResolver = resolver

    def apply(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Dispatch one DELE line.

        Args:
            entry: Entry to modify.
            line: Parsed DELE line.
            block: Current source block for audit metadata.

        Returns:
            Audit records describing what was removed.

        """
        if line.raw_line is None:
            return []
        body = line.raw_line.raw_text
        match = _DELE_SCOPE_RE.search(body)
        if match and not line.dele_refs:
            scoped = self._bare_or_scoped(
                entry, line, block, match.group(1).strip()
            )
            if scoped:
                return scoped
        if line.dele_refs:
            return self._by_refs(entry, line, block)
        return [
            _make_edit_record(
                op=BTEditorialOp.DELE,
                line=line,
                entry=entry,
                block=block,
                scope="unknown",
                applied=False,
                note="dele line had no recognisable scope",
            )
        ]

    @staticmethod
    def _bare_or_scoped(
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
        scope_text: str,
    ) -> list[BTEditRecord]:
        if scope_text:
            return []
        entry.senses = []
        return [
            _make_edit_record(
                op=BTEditorialOp.DELE,
                line=line,
                entry=entry,
                block=block,
                scope="bare_dele",
                applied=True,
                note="bare Dele; entry marked deprecated",
            )
        ]

    def _by_refs(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        paths, note = self.resolver.resolve_sense_paths_for_refs(
            list(line.dele_refs),
            entry.senses,
        )
        if not paths:
            return [
                _make_edit_record(
                    op=BTEditorialOp.DELE,
                    line=line,
                    entry=entry,
                    block=block,
                    scope="sense_paths:none",
                    applied=False,
                    note=_target_note(
                        note or "target_missing",
                        "dele_refs did not match any sense paths",
                    ),
                )
            ]
        removed = [
            path
            for path in paths
            if any(sense.sense_path == path for sense in entry.senses)
        ]
        entry.senses = [
            sense for sense in entry.senses if sense.sense_path not in set(paths)
        ]
        scope = "sense_paths:" + ",".join(removed) if removed else "no_match"
        return [
            _make_edit_record(
                op=BTEditorialOp.DELE,
                line=line,
                entry=entry,
                block=block,
                scope=scope,
                applied=bool(removed),
                note=(
                    ""
                    if removed
                    else _target_note(note or "target_missing", "dele_refs did not match")
                ),
            )
        ]


class BTDeleAndAddOp:
    """
    Apply one DELE_AND_ADD line: remove matching senses, then append.

    Args:
        resolver: Target-resolver used for the dele pass.

    """

    def __init__(self, resolver: BTTargetResolver) -> None:
        """
        Bind the resolver used for sense-path lookup.

        Args:
            resolver: Target-resolver collaborator.

        """
        #: Sense-path resolver.
        self.resolver: BTTargetResolver = resolver

    def apply(
        self,
        entry: BTConsolidatedEntry,
        line: ParsedBTLine,
        block: BTSourceBlock,
    ) -> list[BTEditRecord]:
        """
        Run the dele pass then the add pass for one line.

        Args:
            entry: Entry to modify.
            line: Parsed DELE_AND_ADD line.
            block: Current source block for audit metadata.

        Returns:
            Audit records for both passes.

        """
        if line.raw_line is None:
            return []
        records: list[BTEditRecord] = []
        if line.dele_refs:
            paths, note = self.resolver.resolve_sense_paths_for_refs(
                list(line.dele_refs),
                entry.senses,
            )
            removed = [
                path
                for path in paths
                if any(sense.sense_path == path for sense in entry.senses)
            ]
            if paths:
                entry.senses = [
                    sense for sense in entry.senses if sense.sense_path not in set(paths)
                ]
            records.append(
                _make_edit_record(
                    op=BTEditorialOp.DELE_AND_ADD,
                    line=line,
                    entry=entry,
                    block=block,
                    scope="dele_pass:" + (",".join(removed) if removed else "no_match"),
                    applied=bool(removed),
                    note=note or "dele pass of dele_and_add",
                )
            )
        if line.senses:
            appended = append_senses(entry, line.senses)
            records.append(
                _make_edit_record(
                    op=BTEditorialOp.DELE_AND_ADD,
                    line=line,
                    entry=entry,
                    block=block,
                    scope=f"add_pass:{appended}_senses",
                    applied=appended > 0,
                    note="add pass of dele_and_add",
                )
            )
        entry.source_line_nos.append(line.raw_line.line_no)
        return records
```

- [ ] **Step 4: Wire the merger**

Update `editorial_merger.py`:

1. Imports — add:

```python
from .editorial_ops import (
    BTDeleAndAddOp,
    BTDeleOp,
    BTSubstituteOp,
    append_senses,
)
```

Remove moved regexes `_FOR_ALL_BUT_RE`, `_SUBSTITUTE_FOR_X_RE`, `_SUBSTITUTE_FOLLOWING_RE`, `_DELE_SCOPE_RE`. Keep `_EDITORIAL_LINE_KINDS`, `_CROSS_REF_TARGET_RE`. Remove `_TAG_RE` / `_WS_RE` only if nothing remaining in this file uses them (warnings do not). Delete `_plain`, `_target_note`, `_append_senses`, `_apply_substitute`, `_apply_dele`, `_apply_dele_and_add`, `_audit_context`.

2. `__init__` — after assigning `block_builder`:

```python
        #: Substitute collaborator.
        self._substitute_op: BTSubstituteOp = BTSubstituteOp(self.resolver)
        #: Dele collaborator.
        self._dele_op: BTDeleOp = BTDeleOp(self.resolver)
        #: Dele-and-add collaborator.
        self._dele_and_add_op: BTDeleAndAddOp = BTDeleAndAddOp(self.resolver)
```

Do not add constructor parameters.

3. Replace `_merge_block` and add seed helpers (this also satisfies ADR decision 9):

```python
    def _merge_block(
        self,
        block: BTSourceBlock,
        all_blocks: list[BTSourceBlock],
    ) -> tuple[BTConsolidatedEntry | None, list[BTEditRecord]]:
        """
        Build one consolidated entry from all lines in *block*.

        Args:
            block: One dictionary source block.
            all_blocks: Full block list for cross-entry substitute resolution.

        Returns:
            A pair ``(entry, audit_records)`` where *entry* may be ``None`` when
            the block contains no usable seed line.

        """
        sorted_lines = sorted(
            block.lines,
            key=lambda ln: ln.raw_line.line_no if ln.raw_line else 0,
        )
        mains = self._of_kind(sorted_lines, BTLineKind.MAIN)
        substitutes = self._of_kind(sorted_lines, BTLineKind.SUBSTITUTE)
        deles = self._of_kind(sorted_lines, BTLineKind.DELE)
        dele_and_adds = self._of_kind(sorted_lines, BTLineKind.DELE_AND_ADD)
        adds = self._of_kind(sorted_lines, BTLineKind.ADD)
        seed, substitute_seed, substitutes, adds = self._pick_seed(
            mains, substitutes, adds
        )
        if seed is None or seed.raw_line is None:
            return None, []
        entry = self._new_entry(block, seed)
        self._absorb_main_follow_ons(entry, mains[1:])
        audit: list[BTEditRecord] = []
        if substitute_seed:
            audit.extend(
                self._substitute_op.apply(entry, seed, all_blocks, block)
            )
        for ln in substitutes:
            if ln.raw_line is not None:
                audit.extend(self._substitute_op.apply(entry, ln, all_blocks, block))
        for ln in deles:
            if ln.raw_line is not None:
                audit.extend(self._dele_op.apply(entry, ln, block))
        for ln in dele_and_adds:
            if ln.raw_line is not None:
                audit.extend(self._dele_and_add_op.apply(entry, ln, block))
        for ln in adds:
            if ln.raw_line is not None:
                audit.extend(self._apply_add(entry, ln, block))
        entry.genders = list(
            promote_entry_gender_from_senses(
                tuple(entry.genders),
                tuple(entry.senses),
            )
        )
        return entry, audit

    @staticmethod
    def _of_kind(
        sorted_lines: list[ParsedBTLine], kind: BTLineKind
    ) -> list[ParsedBTLine]:
        """
        Return lines whose raw kind is *kind*.

        Args:
            sorted_lines: Block lines in source order.
            kind: Line kind to keep.

        Returns:
            Matching parsed lines.

        """
        return [
            ln for ln in sorted_lines if ln.raw_line and ln.raw_line.kind == kind
        ]

    @staticmethod
    def _pick_seed(
        mains: list[ParsedBTLine],
        substitutes: list[ParsedBTLine],
        adds: list[ParsedBTLine],
    ) -> tuple[ParsedBTLine | None, bool, list[ParsedBTLine], list[ParsedBTLine]]:
        """
        Choose the seed line and remaining editorial lists.

        Pops the chosen substitute or add from the corresponding list when there
        is no MAIN line.

        Args:
            mains: MAIN lines in the block.
            substitutes: SUBSTITUTE lines; may be mutated.
            adds: ADD lines; may be mutated.

        Returns:
            ``(seed, substitute_seed, remaining_substitutes, remaining_adds)``.

        """
        if mains:
            return mains[0], False, substitutes, adds
        if substitutes:
            seed = substitutes.pop(0)
            return seed, True, substitutes, adds
        if adds and adds[0].senses:
            seed = adds.pop(0)
            return seed, False, substitutes, adds
        return None, False, substitutes, adds

    @staticmethod
    def _new_entry(
        block: BTSourceBlock, seed: ParsedBTLine
    ) -> BTConsolidatedEntry:
        """
        Construct the consolidated entry from the seed line and block.

        Args:
            block: Source block supplying identity and POS fallback.
            seed: Seed line; caller guarantees ``raw_line`` is set.

        Returns:
            New consolidated entry.

        """
        if seed.raw_line is None:
            msg = "seed line is missing raw_line"
            raise ValueError(msg)
        pos = block.pos if block.pos != BTPos.UNKNOWN else seed.pos
        return BTConsolidatedEntry(
            norm_key=block.norm_key,
            headword_raw=seed.raw_line.headword_raw,
            headword_macronized=seed.headword_macronized,
            normalized_title=normalize_morphology_title(seed.headword_macronized),
            pos=pos,
            genders=list(seed.genders),
            variants=list(seed.variants),
            senses=list(seed.senses),
            etymology=" ".join(seed.etymology_blocks),
            see_also=[],
            source_line_nos=[seed.raw_line.line_no],
            entry_order=block.entry_order,
        )

    def _absorb_main_follow_ons(
        self, entry: BTConsolidatedEntry, follow_ons: list[ParsedBTLine]
    ) -> None:
        """
        Merge later MAIN lines into *entry*.

        Args:
            entry: Seed entry being built.
            follow_ons: MAIN lines after the seed.

        """
        for ln in follow_ons:
            if ln.raw_line is None:
                continue
            entry.source_line_nos.append(ln.raw_line.line_no)
            self._extend_senses(entry, ln.senses)
            for variant in ln.variants:
                if variant not in entry.variants:
                    entry.variants.append(variant)
            if not entry.etymology and ln.etymology_blocks:
                entry.etymology = " ".join(ln.etymology_blocks)
```

Keep `_extend_senses` and `_next_top_level_path` on the merger unchanged.

4. `_apply_add` — replace `self._append_senses` with `append_senses` and inline audit fields from `block` (no `_audit_context`):

```python
        appended = append_senses(entry, line.senses)
        entry.source_line_nos.append(line.raw_line.line_no)
        records.append(
            BTEditRecord(
                op=BTEditorialOp.ADD,
                source_line_no=line.raw_line.line_no,
                target_norm_key=entry.norm_key,
                target_pos=entry.pos,
                scope=f"append:{appended}_senses",
                applied=appended > 0,
                note="" if appended else "add line had no parseable senses",
                entry_order=block.entry_order,
                source_block_index=block.source_block_index,
            )
        )
```

Leave `_apply_cross_refs` / `_extract_cross_ref_targets` in place.

- [ ] **Step 5: Run tests**

```bash
.venv/bin/pytest tests/dictionary/test_editorial_op_modules.py tests/dictionary/test_editorial_merger.py -v
```

Expected: PASS, including line-budget and constructor tests.

- [ ] **Step 6: Quality gate + graphify**

```bash
.venv/bin/ruff check wyrdcraeft/models/dictionary.py wyrdcraeft/models/__init__.py wyrdcraeft/services/dictionary/editorial_ops.py wyrdcraeft/services/dictionary/editorial_merger.py wyrdcraeft/services/dictionary/__init__.py wyrdcraeft/services/dictionary/sinks.py tests/dictionary/test_editorial_merger.py tests/dictionary/test_editorial_op_modules.py
.venv/bin/mypy wyrdcraeft/models/dictionary.py wyrdcraeft/models/__init__.py wyrdcraeft/services/dictionary/editorial_ops.py wyrdcraeft/services/dictionary/editorial_merger.py wyrdcraeft/services/dictionary/__init__.py wyrdcraeft/services/dictionary/sinks.py tests/dictionary/test_editorial_merger.py tests/dictionary/test_editorial_op_modules.py
make napoleon-gate
graphify update .
```

Expected: clean ruff/mypy; napoleon-gate no new violations; graphify AST update succeeds. If ruff reports `PLR0912`/`PLR0915` on a new method, split that method — do not noqa.

- [ ] **Step 7: Mark ADR 0021 accepted**

In `docs/adr/0021-editorial-merger-ops-and-edit-record.md` set:

```yaml
---
status: accepted
---
```

Replace `**Status:** proposed. Implementation has not started.` with `**Status:** accepted.`

In `CONTEXT.md` ADR 0021 bullet, drop “proposed; not implemented”.

---

## Self-review (spec coverage)

| ADR decision | Task |
|---|---|
| 1 `BTEditRecord` in `models.dictionary` + models export | 2 |
| 2 No services re-export; three callers | 1–2 |
| 3 Merger facade `merge` / warnings | 3 (untouched entry points) |
| 4 Private ops, not injected | 1 constructor test + 3 `__init__` |
| 5 Three classes in one file, not Add | 3 |
| 6 Methods ≤ 60, no new noqa | 3 line-budget test + ruff |
| 7 Substitute + `all_blocks` | 3 `BTSubstituteOp.apply` |
| 8 `append_senses` module fn; `_extend_senses` on merger | 3 |
| 9 `_merge_block` split, still on merger | 3 |
| 10 Cross-refs out of scope | 3 leave in place |
| 11 No new packages; characterization tests | Global + Task 3 pytest |

No placeholders. Names used later match Task 3 interfaces (`BTSubstituteOp.apply`, `append_senses`, `_pick_seed`, `_new_entry`, `_absorb_main_follow_ons`).
