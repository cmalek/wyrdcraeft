#!/usr/bin/env python3
"""
Build a precomputed Bosworth-Toller macron lookup index.
"""

from __future__ import annotations

from pathlib import Path

from wyrdcraeft.services.dictionary.resources import default_bt_source_path
from wyrdcraeft.services.markup import MacronApplicator


def main() -> None:
    """
    Build the packaged macron index from the bundled Bosworth-Toller source.
    """
    project_root = Path(__file__).resolve().parents[1]
    source_path = default_bt_source_path()
    output_path = (
        project_root / "wyrdcraeft" / "etc" / "diacritic" / "oe_bt_macron_index.json"
    )
    index = MacronApplicator.build_index_from_bt(source_path, output_path)
    print(
        "Wrote "
        f"{output_path} (unique={len(index.unique)}, "
        f"ambiguous={len(index.ambiguous)})"
    )


if __name__ == "__main__":
    main()
