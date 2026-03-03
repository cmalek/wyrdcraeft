from __future__ import annotations

import hashlib
import io
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from tests.morphology.conftest import SUBSET_DICTIONARY, build_session
from tests.morphology.snapshot_io import (
    canonicalize_form_rows,
    parse_form_output,
    stable_json_lines_digest,
)
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
)
from wyrdcraeft.services.morphology.generators.common import output_manual_forms


def _sha256_rows(rows: list[dict[str, str]]) -> str:
    digest_input = stable_json_lines_digest(rows).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


def _stage_rows(stage: str) -> list[dict[str, str]]:
    session = build_session(dictionary_path=SUBSET_DICTIONARY)
    output = io.StringIO()
    if stage == "manual":
        output_manual_forms(session, output)
    elif stage == "verb":
        generate_vbforms(session, output)
    elif stage == "adj":
        generate_adjforms(session, output)
    elif stage == "adv":
        generate_advforms(session, output)
    elif stage == "num":
        generate_numforms(session, output)
    elif stage == "noun":
        generate_nounforms(session, output)
    elif stage == "full_flow":
        output_manual_forms(session, output)
        generate_vbforms(session, output)
        generate_adjforms(session, output)
        generate_advforms(session, output)
        generate_numforms(session, output)
        generate_nounforms(session, output)
    else:
        msg = f"unknown stage: {stage}"
        raise ValueError(msg)

    return canonicalize_form_rows(parse_form_output(output.getvalue()))


def _runtime_baseline_ms() -> float:
    session = build_session(dictionary_path=SUBSET_DICTIONARY)
    output = io.StringIO()
    start = time.perf_counter()
    output_manual_forms(session, output)
    generate_vbforms(session, output)
    generate_adjforms(session, output)
    generate_advforms(session, output)
    generate_numforms(session, output)
    generate_nounforms(session, output)
    elapsed = (time.perf_counter() - start) * 1000
    return round(elapsed, 3)


def _mypy_baseline() -> dict[str, object]:
    cmd = [".venv/bin/mypy", "wyrdcraeft", "tests"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "errors": lines,
    }


def main() -> None:
    stage_order = ["manual", "verb", "adj", "adv", "num", "noun", "full_flow"]
    stage_hashes: dict[str, str] = {}
    stage_counts: dict[str, int] = {}

    for stage in stage_order:
        rows = _stage_rows(stage)
        stage_hashes[stage] = _sha256_rows(rows)
        stage_counts[stage] = len(rows)

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "subset_dictionary": str(SUBSET_DICTIONARY),
        "stage_hashes": stage_hashes,
        "stage_row_counts": stage_counts,
        "runtime_subset_full_flow_ms": _runtime_baseline_ms(),
        "mypy_baseline": _mypy_baseline(),
    }

    out_path = Path("tests/morphology/data/refactor_baseline.json")
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
