"""Seed normalized POS and inflection-code reference tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import sqlite3

#: Repo-relative directory containing packaged morphology seed fixtures.
_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "etc" / "morphology"
#: Packaged POS seed fixture path.
_PARTS_OF_SPEECH_FIXTURE = _FIXTURE_DIR / "parts_of_speech_seed.json"
#: Packaged inflection-code seed fixture path.
_INFLECTION_CODES_FIXTURE = _FIXTURE_DIR / "inflection_codes_seed.json"
#: POS codes that must always exist in the packaged seed fixture.
_REQUIRED_POS_CODES: tuple[str, ...] = (
    "noun",
    "verb",
    "adjective",
    "adverb",
    "pronoun",
    "numeral",
    "unknown",
    "participle",
    "preposition",
    "conjunction",
    "interjection",
    "indeclinable",
)


def ensure_parts_of_speech(connection: sqlite3.Connection) -> dict[str, int]:
    """
    Create and upsert seeded part-of-speech reference rows.

    Note:
        The seed vocabulary follows the Old English Parts-of-Speech categories
        used by ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this creates the
        canonical POS lookup rows that later normalized-schema tasks reference.
        Part-of-speech scope: ``cross-PoS``.

    Args:
        connection: Open ``sqlite3.Connection`` bound to the canonical SQLite
            database. The caller owns transaction boundaries.

    Returns:
        Mapping from seeded POS ``code`` to surrogate ``parts_of_speech.id``.

    Raises:
        ValueError: The packaged seed fixture is malformed or missing required
            POS codes.

    Side Effects:
        Creates ``parts_of_speech`` and ``inflection_codes`` when missing, then
        upserts seeded rows into ``parts_of_speech``.

    """
    _ensure_reference_tables(connection)
    rows = _read_seed_rows(_PARTS_OF_SPEECH_FIXTURE)
    _validate_parts_of_speech_rows(rows)
    connection.executemany(
        """
        INSERT INTO parts_of_speech (code, display_label, is_inflectable)
        VALUES (:code, :display_label, :is_inflectable)
        ON CONFLICT(code) DO UPDATE SET
            display_label = excluded.display_label,
            is_inflectable = excluded.is_inflectable
        """,
        [
            {
                "code": str(row["code"]),
                "display_label": str(row["display_label"]),
                "is_inflectable": int(row["is_inflectable"]),
            }
            for row in rows
        ],
    )
    return _fetch_code_id_map(connection, table_name="parts_of_speech")


def ensure_inflection_codes(
    connection: sqlite3.Connection,
    pos_map: dict[str, int],
) -> dict[str, int]:
    """
    Create and upsert seeded morphology function-code reference rows.

    Note:
        The seeded function codes mirror current Old English morphology output
        from ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf`` plus legacy/manual rows still emitted by
        the generator. In plain terms, this creates one lookup row per compact
        morphology ``function`` code, even when several Parts of Speech share
        the same code family. Part-of-speech scope: ``cross-PoS``.

    Args:
        connection: Open ``sqlite3.Connection`` bound to the canonical SQLite
            database. The caller owns transaction boundaries.
        pos_map: Previously seeded mapping from POS ``code`` to
            ``parts_of_speech.id``.

    Returns:
        Mapping from seeded inflection ``code`` to surrogate
        ``inflection_codes.id``.

    Raises:
        ValueError: The packaged seed fixture is malformed or references an
            unknown POS code.

    Side Effects:
        Creates ``parts_of_speech`` and ``inflection_codes`` when missing, then
        upserts seeded rows into ``inflection_codes``.

    """
    _ensure_reference_tables(connection)
    rows = _read_seed_rows(_INFLECTION_CODES_FIXTURE)
    _validate_inflection_code_rows(rows, pos_map=pos_map)
    connection.executemany(
        """
        INSERT INTO inflection_codes (code, pos_id, display_json)
        VALUES (:code, :pos_id, :display_json)
        ON CONFLICT(code) DO UPDATE SET
            pos_id = excluded.pos_id,
            display_json = excluded.display_json
        """,
        [
            {
                "code": str(row["code"]),
                "pos_id": int(pos_map[str(row["pos_code"])]),
                "display_json": json.dumps(
                    row.get("display_json", {}),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
            for row in rows
        ],
    )
    return _fetch_code_id_map(connection, table_name="inflection_codes")


def _ensure_reference_tables(connection: sqlite3.Connection) -> None:
    """
    Create reference lookup tables and indexes when missing.

    Args:
        connection: Open SQLite connection receiving DDL statements.

    Side Effects:
        Creates ``parts_of_speech`` / ``inflection_codes`` and their indexes.

    """
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS parts_of_speech (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            display_label TEXT NOT NULL,
            is_inflectable INTEGER NOT NULL DEFAULT 1
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_parts_of_speech_code
            ON parts_of_speech(code);

        CREATE TABLE IF NOT EXISTS inflection_codes (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            pos_id INTEGER NOT NULL REFERENCES parts_of_speech(id),
            display_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_inflection_codes_code
            ON inflection_codes(code);

        CREATE INDEX IF NOT EXISTS idx_inflection_codes_pos_id
            ON inflection_codes(pos_id);
        """,
    )


def _read_seed_rows(path: Path) -> list[dict[str, Any]]:
    """
    Read one packaged seed fixture into a list of dictionaries.

    Args:
        path: Absolute path to one JSON fixture file.

    Returns:
        Parsed fixture rows.

    Raises:
        TypeError: The JSON payload is not a list of objects.

    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        msg = f"Seed fixture must be a JSON array: {path}"
        raise TypeError(msg)
    if not all(isinstance(row, dict) for row in payload):
        msg = f"Seed fixture rows must be JSON objects: {path}"
        raise TypeError(msg)
    return payload


def _validate_parts_of_speech_rows(rows: list[dict[str, Any]]) -> None:
    """
    Validate the packaged POS fixture structure and required rows.

    Args:
        rows: Parsed POS seed rows.

    Raises:
        ValueError: Required keys or required POS codes are missing.

    """
    codes: list[str] = []
    for row in rows:
        _require_keys(
            row,
            required_keys=("code", "display_label", "is_inflectable"),
            row_label="parts_of_speech row",
        )
        codes.append(str(row["code"]))

    missing_codes = sorted(set(_REQUIRED_POS_CODES) - set(codes))
    if missing_codes:
        msg = f"parts_of_speech seed missing required codes: {missing_codes}"
        raise ValueError(msg)


def _validate_inflection_code_rows(
    rows: list[dict[str, Any]],
    *,
    pos_map: dict[str, int],
) -> None:
    """
    Validate the packaged inflection-code fixture structure.

    Args:
        rows: Parsed inflection-code seed rows.

    Keyword Args:
        pos_map: Seeded POS code-to-id mapping used for FK resolution.

    Raises:
        ValueError: Required keys are missing or a row references unknown POS.

    """
    for row in rows:
        _require_keys(
            row,
            required_keys=("code", "pos_code", "display_json"),
            row_label="inflection_codes row",
        )
        pos_code = str(row["pos_code"])
        if pos_code not in pos_map:
            msg = (
                f"inflection_codes seed references unknown parts_of_speech "
                f"code {pos_code!r}"
            )
            raise ValueError(msg)


def _require_keys(
    row: dict[str, Any],
    *,
    required_keys: tuple[str, ...],
    row_label: str,
) -> None:
    """
    Ensure one seed row contains all required keys.

    Args:
        row: Parsed JSON object for one seed row.

    Keyword Args:
        required_keys: Required keys for this row type.
        row_label: Human-readable row type for error messages.

    Raises:
        ValueError: One or more required keys are missing.

    """
    missing = [key for key in required_keys if key not in row]
    if missing:
        msg = f"{row_label} missing required keys: {missing}"
        raise ValueError(msg)


def _fetch_code_id_map(
    connection: sqlite3.Connection,
    *,
    table_name: str,
) -> dict[str, int]:
    """
    Fetch one reference table's ``code`` to ``id`` mapping.

    Args:
        connection: Open SQLite connection receiving the select query.

    Keyword Args:
        table_name: Reference table name to query.

    Returns:
        Mapping from ``code`` to integer primary key.

    """
    rows = connection.execute(
        f"SELECT code, id FROM {table_name} ORDER BY id",  # noqa: S608
    ).fetchall()
    return {str(code): int(row_id) for code, row_id in rows}
