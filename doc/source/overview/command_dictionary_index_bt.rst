``wyrdcraeft dictionary index-bt``
====================================

This command builds a compiled Bosworth-Toller dictionary SQLite index from
``data/oe_bt.txt``. Editorial Add / Substitute / Dele lines are merged into
canonical lookup entries keyed by ``(norm_key, pos)``.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft dictionary index-bt [OPTIONS]

Options
-------

- ``--source PATH``: Bosworth-Toller source file (default: ``data/oe_bt.txt``).
- ``--index-db PATH``: explicit SQLite index file path.
- ``--index-dir PATH``: directory where ``dictionary.sqlite3`` is written.
- ``--attach-morphology-db PATH``: write ``bt_*`` tables into an existing
  ``morphology.sqlite3`` without modifying ``forms`` (single-file mode).
- ``--report PATH``: optional JSON report with parse/merge statistics.
- ``--warnings-file PATH``: optional ``parse_warnings.jsonl`` output path. When
  omitted, the file is written alongside the resolved index database as
  ``parse_warnings.jsonl``.
- ``--llm-fix-pass``: optional second pass that sends warning lines to a local
  Ollama-compatible LLM for strict JSON repair before editorial merge.
- ``--llm-model MODEL``: Ollama model for ``--llm-fix-pass`` (default:
  ``qwen2.5:14b-instruct``).
- ``--llm-endpoint URL``: Ollama ``/api/generate`` endpoint (default:
  ``http://localhost:11434/api/generate``).

Parse warnings
--------------

Each ``index-bt`` run writes ``parse_warnings.jsonl`` with one JSON object per
line when deterministic parsing is uncertain. Triggers include low-confidence
attestation stripping, unknown POS on a main headword line, and empty sense
segmentation on a non-empty body. Without ``--llm-fix-pass``, the SQLite index
matches the deterministic-only path; the warnings file is diagnostic only.

When ``--llm-fix-pass`` is enabled, only warning records are sent to the LLM.
Invalid JSON or schema validation failures are logged and the deterministic
partial result is preserved for that line.

SQLite index database
---------------------

``wyrdcraeft dictionary index-bt`` writes ``dictionary.sqlite3`` containing
consolidated headwords, ordered English gloss senses, variant spellings, and an
internal editorial audit log.

Default path by operating system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 34 48

   * - OS
     - Default directory
     - Full default database path
   * - Windows
     - ``%USERPROFILE%\\AppData\\Local\\wyrdcraeft``
     - ``%USERPROFILE%\\AppData\\Local\\wyrdcraeft\\dictionary.sqlite3``
   * - macOS
     - ``~/Library/Application Support/wyrdcraeft``
     - ``~/Library/Application Support/wyrdcraeft/dictionary.sqlite3``
   * - Linux
     - ``~/.config/wyrdcraeft``
     - ``~/.config/wyrdcraeft/dictionary.sqlite3``

Override precedence
~~~~~~~~~~~~~~~~~~~

When resolving where to write ``dictionary.sqlite3``, wyrdcraeft applies the
first matching option below:

#. ``--index-db PATH`` — explicit SQLite file path
#. ``--index-dir PATH`` — directory; file name is always ``dictionary.sqlite3``
#. ``WYRDCRAEFT_APP_DATA_DIR`` environment variable or ``app_data_dir`` in
   ``.wyrdcraeft.toml`` — replaces the OS default **directory** (file name
   stays ``dictionary.sqlite3``)
#. OS default (table above)

When the command completes, it prints ``index_db=...`` with the resolved
absolute path so you can confirm the database location without guessing.

Attach mode (single database file)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``--attach-morphology-db PATH`` when you want dictionary lookup tables
stored in the same SQLite file as morphology ``forms`` rows (for example
``morphology.sqlite3`` under app data). This option is **mutually exclusive**
with ``--index-db``, ``--index-dir``, and the default sibling
``dictionary.sqlite3`` path.

Behavior:

- **Existing morphology database:** wyrdcraeft adds or refreshes ``bt_*`` tables
  only. The ``forms`` table and its rows are never dropped or altered.
- **Missing target file:** wyrdcraeft creates a new SQLite file containing
  ``bt_*`` tables only (no ``forms`` schema until you run
  ``wyrdcraeft morphology generate``).
- **Re-run:** each ``index-bt --attach-morphology-db`` pass truncates and
  reloads ``bt_*`` contents so the dictionary index stays idempotent.

The completion line includes ``attach_mode=yes`` when attach mode is active.

Report JSON
-----------

When ``--report PATH`` is supplied, wyrdcraeft writes JSON containing:

- ``parsed``, ``skipped``, ``merged`` counts
- ``pos_counts`` grouped by normalized part of speech
- ``warning_counts`` for parser skips and unapplied editorial operations
- ``skipped_by_reason`` grouped by parser skip reason

Examples
--------

.. code-block:: bash

    # Index the full Bosworth-Toller source with default app-data output
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --report /tmp/bt_report.json

    # Custom index directory (for example CI artifacts or a shared drive)
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --index-dir /tmp/wyrdcraeft-index

    # Explicit index file path
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --index-db /var/lib/wyrdcraeft/dictionary.sqlite3

    # Single-file mode: attach dictionary tables to morphology.sqlite3
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt \
        --attach-morphology-db ~/Library/Application\ Support/wyrdcraeft/morphology.sqlite3

    # Optional local LLM repair pass for parse warnings only
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --llm-fix-pass \
        --llm-model qwen2.5:14b-instruct \
        --warnings-file /tmp/parse_warnings.jsonl

See also
--------

- :doc:`command_morphology_generate` — morphology SQLite index in the same app-data directory
