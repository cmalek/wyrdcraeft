from __future__ import annotations

import gzip
import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

FORM_FIELDS = [
    "counter",
    "formi",
    "BT",
    "title",
    "stem",
    "form",
    "formParts",
    "var",
    "probability",
    "function",
    "wright",
    "paradigm",
    "paraID",
    "wordclass",
    "class1",
    "class2",
    "class3",
    "comment",
]

FORM_FIELDS_NO_COUNTER = [field for field in FORM_FIELDS if field != "counter"]

DEFAULT_FORM_SORT_FIELDS = [
    "BT",
    "wordclass",
    "function",
    "form",
    "formParts",
    "var",
    "title",
    "stem",
    "wright",
    "paradigm",
    "paraID",
    "class1",
    "class2",
    "class3",
    "comment",
    "probability",
    "formi",
]


def parse_form_output(output: str) -> list[dict[str, str]]:
    """
    Parse generator TSV output into normalized records.

    The unstable ``counter`` field is dropped from records.

    Args:
        output: Raw TSV output from generator functions.

    Returns:
        Parsed rows containing all stable output columns.

    """
    records: list[dict[str, str]] = []
    for raw_line in output.splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("\t")
        if len(parts) < len(FORM_FIELDS):
            parts += [""] * (len(FORM_FIELDS) - len(parts))

        row_full = dict(zip(FORM_FIELDS, parts[: len(FORM_FIELDS)], strict=False))
        row = {field: str(row_full[field]) for field in FORM_FIELDS_NO_COUNTER}
        records.append(row)

    return records


def canonical_sort_rows(
    rows: Sequence[dict[str, Any]],
    *,
    sort_fields: Sequence[str],
) -> list[dict[str, str]]:
    """
    Return deterministically sorted shallow-copied records.

    Args:
        rows: Input row dictionaries.
        sort_fields: Ordered field list used as sort key.

    Returns:
        Sorted rows with values coerced to strings.

    """

    def _coerce_record(row: dict[str, Any]) -> dict[str, str]:
        return {key: str(value) for key, value in row.items()}

    normalized = [_coerce_record(row) for row in rows]
    return sorted(
        normalized,
        key=lambda row: tuple(row.get(field, "") for field in sort_fields),
    )


def canonicalize_form_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    """Canonicalize form rows for stable snapshot storage."""
    return canonical_sort_rows(rows, sort_fields=DEFAULT_FORM_SORT_FIELDS)


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    """
    Read compressed JSON lines snapshot records.

    Args:
        path: Snapshot path.

    Returns:
        Parsed JSON dictionaries in file order.

    """
    rows: list[dict[str, Any]] = []
    with gzip.open(path, mode="rt", encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def write_jsonl_gz(
    path: Path,
    rows: Iterable[dict[str, Any]],
    *,
    update: bool,
) -> None:
    """
    Write compressed JSON lines deterministically.

    Args:
        path: Snapshot destination path.
        rows: Rows to write.
        update: Whether to allow overwriting existing file.

    Raises:
        FileExistsError: If path exists and update is false.

    """
    if path.exists() and not update:
        msg = f"Snapshot already exists: {path}. Re-run with --update to overwrite."
        raise FileExistsError(msg)

    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, mode="wt", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            serialized = json.dumps(row, ensure_ascii=False, sort_keys=True)
            handle.write(f"{serialized}\n")


def stable_json_lines_digest(rows: Sequence[dict[str, Any]]) -> str:
    """
    Build a stable digest string for richer assertion diffs.

    Args:
        rows: Rows to serialize.

    Returns:
        Newline-joined stable JSON serialization.

    """
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows
    )


def stable_json_sha256(rows: Sequence[dict[str, Any]]) -> str:
    """
    Build a stable SHA-256 hash from canonicalized JSON-line rows.

    Args:
        rows: Rows to serialize and hash.

    Returns:
        Hex SHA-256 digest.

    """
    payload = stable_json_lines_digest(rows).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
