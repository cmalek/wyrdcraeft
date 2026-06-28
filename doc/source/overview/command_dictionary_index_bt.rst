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
- ``--index-dir PATH``: directory where ``morphology.sqlite3`` is stored by
  default, or ``dictionary.sqlite3`` with ``--standalone``.
- ``--standalone``: write a fresh ``dictionary.sqlite3`` instead of attaching
  ``bt_*`` tables to ``morphology.sqlite3``.
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

By default, ``wyrdcraeft dictionary index-bt`` attaches ``bt_*`` tables to the
same ``morphology.sqlite3`` database used by morphology and lexicon workflows.
The ``forms`` table and its rows are never dropped or altered. If the target
``morphology.sqlite3`` does not exist, the command exits with an error that
points you to ``wyrdcraeft morphology generate`` or to ``--index-db`` /
``--index-dir``.

Use ``--standalone`` when you want a separate ``dictionary.sqlite3`` containing
only Bosworth-Toller lookup tables.

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
     - ``%USERPROFILE%\\AppData\\Local\\wyrdcraeft\\morphology.sqlite3``
   * - macOS
     - ``~/Library/Application Support/wyrdcraeft``
     - ``~/Library/Application Support/wyrdcraeft/morphology.sqlite3``
   * - Linux
     - ``~/.config/wyrdcraeft``
     - ``~/.config/wyrdcraeft/morphology.sqlite3``

Override precedence
~~~~~~~~~~~~~~~~~~~

When resolving where to attach ``bt_*`` tables, wyrdcraeft applies the first
matching option below:

#. ``--index-db PATH`` — explicit SQLite file path
#. ``--index-dir PATH`` — directory; file name is always ``morphology.sqlite3``
#. ``WYRDCRAEFT_APP_DATA_DIR`` environment variable or ``app_data_dir`` in
   ``.wyrdcraeft.toml`` — replaces the OS default **directory** (file name
   stays ``morphology.sqlite3``)
#. OS default (table above)

When the command completes, it prints ``index_db=...`` with the resolved
absolute path so you can confirm the database location without guessing.

Re-run behavior
~~~~~~~~~~~~~~~

Each default ``index-bt`` pass truncates and reloads ``bt_*`` contents so the
dictionary index stays idempotent. The completion line includes
``attach_mode=yes`` when attach mode is active.

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

    # Attach bt_* tables to default app-data morphology.sqlite3
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --report /tmp/bt_report.json

    # Custom morphology index directory (for example CI artifacts)
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --index-dir /tmp/wyrdcraeft-index

    # Explicit morphology.sqlite3 path
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt \
        --index-db ~/Library/Application\ Support/wyrdcraeft/morphology.sqlite3

    # Standalone dictionary.sqlite3 (no morphology database required)
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --standalone \
        --index-db /var/lib/wyrdcraeft/dictionary.sqlite3

    # Optional local LLM repair pass for parse warnings only
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt --llm-fix-pass \
        --llm-model qwen2.5:14b-instruct \
        --warnings-file /tmp/parse_warnings.jsonl

See also
--------

- :doc:`command_morphology_generate` — morphology SQLite index in the same app-data directory
