from __future__ import annotations

import gzip
import hashlib
import io
import json
import tempfile
from pathlib import Path
from typing import Any, cast

from wyrdcraeft.services.morphology.generators.common import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.processors import (
    set_adj_paradigm,
    set_noun_paradigm,
    set_verb_paradigm,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

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
    """Parse generator TSV output into normalized records."""
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
    rows: list[dict[str, Any]],
    *,
    sort_fields: list[str],
) -> list[dict[str, str]]:
    """Return deterministically sorted shallow-copied records."""
    normalized = [{key: str(value) for key, value in row.items()} for row in rows]
    return sorted(
        normalized,
        key=lambda row: tuple(row.get(field, "") for field in sort_fields),
    )


def canonicalize_form_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Canonicalize form rows for stable snapshot storage."""
    return canonical_sort_rows(rows, sort_fields=DEFAULT_FORM_SORT_FIELDS)


def write_jsonl_gz(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    update: bool,
) -> None:
    """Write compressed JSON lines deterministically."""
    if path.exists() and not update:
        msg = f"Snapshot already exists: {path}. Re-run with --update to overwrite."
        raise FileExistsError(msg)

    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, mode="wt", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            serialized = json.dumps(row, ensure_ascii=False, sort_keys=True)
            handle.write(f"{serialized}\n")


def build_session(
    *,
    dictionary_path: Path,
    manual_forms: Path,
    verbal_paradigms: Path,
    prefixes: Path,
) -> GeneratorSession:
    """Create a fully prepared session for a dictionary file."""
    session = GeneratorSession()
    session.load_all(
        str(dictionary_path),
        str(manual_forms),
        str(verbal_paradigms),
        str(prefixes),
    )
    session.remove_prefixes()
    session.remove_hyphens()
    session.count_syllables()
    set_verb_paradigm(session)
    set_adj_paradigm(session)
    set_noun_paradigm(session)
    return session


def preprocess_snapshot_rows(session: GeneratorSession) -> list[dict[str, str]]:
    """Build canonical preprocess rows from session words."""
    rows = [
        {
            "nid": str(word.nid),
            "title": word.title,
            "prefix": word.prefix,
            "stem": word.stem,
            "syllables": str(word.syllables),
        }
        for word in session.words
    ]
    return canonical_sort_rows(rows, sort_fields=["nid", "title", "stem", "prefix"])


def paradigm_snapshot_rows(session: GeneratorSession) -> list[dict[str, str]]:
    """Build canonical paradigm assignment rows from session words."""
    rows = [
        {
            "nid": str(word.nid),
            "title": word.title,
            "verb": str(word.verb),
            "adjective": str(word.adjective),
            "noun": str(word.noun),
            "numeral": str(word.numeral),
            "pspart": str(word.pspart),
            "papart": str(word.papart),
            "vb_paradigm": ";".join(vp.ID for vp in word.vb_paradigm),
            "adj_paradigm": ";".join(word.adj_paradigm),
            "noun_paradigm": ";".join(word.noun_paradigm),
        }
        for word in session.words
    ]
    return canonical_sort_rows(rows, sort_fields=["nid", "title"])


def form_rows_for_stage(
    session: GeneratorSession,
    *,
    stage_name: str,
) -> list[dict[str, str]]:
    """Run one generation stage and return canonicalized form rows."""
    output = io.StringIO()

    if stage_name == "manual":
        output_manual_forms(session, output)
    elif stage_name == "verb":
        generate_vbforms(session, output)
    elif stage_name == "adj":
        generate_adjforms(session, output)
    elif stage_name == "adv":
        generate_advforms(session, output)
    elif stage_name == "num":
        generate_numforms(session, output)
    elif stage_name == "noun":
        generate_nounforms(session, output)
    else:
        msg = f"Unknown stage: {stage_name}"
        raise ValueError(msg)

    return canonicalize_form_rows(parse_form_output(output.getvalue()))


def full_flow_rows(session: GeneratorSession) -> list[dict[str, str]]:
    """Run full generator flow and return canonicalized output rows."""
    output = io.StringIO()
    output_manual_forms(session, output)
    generate_vbforms(session, output)
    generate_adjforms(session, output)
    generate_advforms(session, output)
    generate_numforms(session, output)
    generate_nounforms(session, output)
    return canonicalize_form_rows(parse_form_output(output.getvalue()))


def full_flow_metadata(session: GeneratorSession) -> dict[str, str]:
    """Compute stable metadata for optional full-dataset smoke checking."""
    hasher = hashlib.sha256()
    line_count = 0
    byte_count = 0

    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as handle:
        output = cast("io.StringIO", handle)
        output_manual_forms(session, output)
        generate_vbforms(session, output)
        generate_adjforms(session, output)
        generate_advforms(session, output)
        generate_numforms(session, output)
        generate_nounforms(session, output)
        handle.flush()
        handle.seek(0)

        for line in handle:
            encoded = line.encode("utf-8")
            hasher.update(encoded)
            line_count += 1
            byte_count += len(encoded)

    return {
        "line_count": str(line_count),
        "byte_count": str(byte_count),
        "sha256": hasher.hexdigest(),
    }


def generate_reference_snapshots(
    *,
    output_dir: Path,
    update: bool,
    include_full: bool,
    subset_dictionary: Path,
    full_dictionary: Path,
    manual_forms: Path,
    verbal_paradigms: Path,
    prefixes: Path,
) -> dict[str, object]:
    """Generate morphology reference snapshots for test fixtures."""
    subset_session = build_session(
        dictionary_path=subset_dictionary,
        manual_forms=manual_forms,
        verbal_paradigms=verbal_paradigms,
        prefixes=prefixes,
    )
    preprocess_rows = preprocess_snapshot_rows(subset_session)
    write_jsonl_gz(
        output_dir / "preprocess_subset.jsonl.gz",
        preprocess_rows,
        update=update,
    )

    paradigms_rows = paradigm_snapshot_rows(subset_session)
    write_jsonl_gz(
        output_dir / "paradigms_subset.jsonl.gz",
        paradigms_rows,
        update=update,
    )

    for stage_name in ("manual", "verb", "adj", "adv", "num", "noun"):
        stage_session = build_session(
            dictionary_path=subset_dictionary,
            manual_forms=manual_forms,
            verbal_paradigms=verbal_paradigms,
            prefixes=prefixes,
        )
        rows = form_rows_for_stage(stage_session, stage_name=stage_name)
        write_jsonl_gz(
            output_dir / f"forms_{stage_name}_subset.jsonl.gz",
            rows,
            update=update,
        )

    full_session_subset = build_session(
        dictionary_path=subset_dictionary,
        manual_forms=manual_forms,
        verbal_paradigms=verbal_paradigms,
        prefixes=prefixes,
    )
    full_rows = full_flow_rows(full_session_subset)
    write_jsonl_gz(
        output_dir / "full_flow_subset.jsonl.gz",
        full_rows,
        update=update,
    )

    if include_full:
        full_session_dataset = build_session(
            dictionary_path=full_dictionary,
            manual_forms=manual_forms,
            verbal_paradigms=verbal_paradigms,
            prefixes=prefixes,
        )
        full_meta = full_flow_metadata(full_session_dataset)
        write_jsonl_gz(
            output_dir / "full_flow_full_smoke.jsonl.gz",
            [full_meta],
            update=update,
        )

    return {
        "output_dir": str(output_dir),
        "include_full": include_full,
    }


def format_reference_snapshot_result(result: dict[str, object]) -> str:
    """Format snapshot command result payload for CLI output."""
    return json.dumps(result)
