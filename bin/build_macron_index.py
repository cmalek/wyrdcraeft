#!/usr/bin/env python3
"""
Build a precomputed Bosworth-Toller macron lookup index.
"""

from __future__ import annotations

from pathlib import Path

from wyrdcraeft.services.markup import MacronApplicator


def main() -> None:
    """
    Build ``wyrdcraeft/etc/diacritic/oe_bt_macron_index.json`` from ``data/oe_bt.txt``.
    """
    project_root = Path(__file__).resolve().parents[2]
    source_path = project_root / "data" / "oe_bt.txt"
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
