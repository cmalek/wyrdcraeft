"""
Recover the user's ambiguity decisions from the macron index's git history.

Usage: python scripts/diacritic/extract_ambiguity_labels.py OUTPUT.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wyrdcraeft.services.markup import DiacriticTransfer

INDEX = "wyrdcraeft/etc/diacritic/oe_bt_macron_index.json"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout


def load(sha: str) -> dict:
    return json.loads(git("show", f"{sha}:{INDEX}"))


def main(output: Path) -> None:
    shas = git("log", "--follow", "--format=%H", "--reverse", "--", INDEX).split()
    labels: dict[str, dict] = {}
    prev = load(shas[0])
    for sha in shas[1:]:
        cur = load(sha)
        done_prev = set(prev.get("ambiguous_completed", []))
        done_cur = set(cur.get("ambiguous_completed", []))
        for key, options in prev["ambiguous"].items():
            if key in done_prev or key in labels:
                continue
            chosen = cur["unique"].get(key)
            if key in done_cur and key in cur["ambiguous"]:
                labels[key] = {"options": options, "label": "homograph"}
            elif (
                chosen is not None
                and key not in cur["ambiguous"]
                and len(DiacriticTransfer.mark_pattern(chosen))
                == len(DiacriticTransfer.mark_pattern(options[0]))
            ):
                labels[key] = {"options": options, "label": "same_word"}
        prev = cur
    counts = {
        name: sum(v["label"] == name for v in labels.values())
        for name in ("same_word", "homograph")
    }
    meta = {"source": INDEX, "revisions": len(shas), **counts}
    payload = {"meta": meta, "labels": labels}
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    print(payload["meta"])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
