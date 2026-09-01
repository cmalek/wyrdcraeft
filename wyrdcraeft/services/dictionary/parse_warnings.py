"""JSONL I/O for Bosworth-Toller parse warning records."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.models.dictionary import BTParseWarning


def write_parse_warnings(path: Path, warnings: list[BTParseWarning]) -> None:
    """
    Write parse warnings as JSONL.

    Args:
        path: Destination ``parse_warnings.jsonl`` path.
        warnings: Warning records collected during indexing.

    Side Effects:
        Creates parent directories and writes UTF-8 JSONL.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(warning.to_json(), ensure_ascii=False) for warning in warnings]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def append_parse_warnings(path: Path, warnings: list[BTParseWarning]) -> None:
    """
    Append parse warnings to an existing JSONL file.

    Args:
        path: Destination ``parse_warnings.jsonl`` path.
        warnings: Additional warning records to append.

    Side Effects:
        Creates parent directories when needed and appends UTF-8 JSONL rows.

    """
    if not warnings:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(warning.to_json(), ensure_ascii=False) for warning in warnings]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
