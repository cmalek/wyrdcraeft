``wyrdcraeft dictionary build``
====================================

This command builds a compiled Bosworth-Toller dictionary SQLite index from the
packaged Bosworth-Toller source (``wyrdcraeft/etc/dictionary/oe_bt.txt`` by
default). Editorial Add / Substitute / Dele lines are merged into source-order
dictionary entries; homographs with the same ``(norm_key, pos)`` remain
separate rows distinguished by ``entry_order``.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft dictionary build [OPTIONS]

Options
-------

- ``--source PATH``: Bosworth-Toller source file (default: packaged
  ``wyrdcraeft/etc/dictionary/oe_bt.txt``).
- ``--report PATH``: optional JSON report with parse/merge statistics.
- ``--warnings-file PATH``: optional ``parse_warnings.jsonl`` output path. When
  omitted, the file is written alongside the resolved index database as
  ``parse_warnings.jsonl``.

Parse warnings
--------------

Each ``build`` run writes ``parse_warnings.jsonl`` with one JSON object per
line when deterministic parsing is uncertain. Triggers include low-confidence
attestation stripping, unknown POS on a main headword line, and empty sense
segmentation on a non-empty body. After editorial merge, unapplied edits and
editorial debris are appended to the same file; cross-check ``bt_edit_log`` for
``applied=0`` rows whose ``note`` begins with ``target_missing`` or
``target_ambiguous``. The warnings file is diagnostic only.

SQLite index database
---------------------

By default, ``wyrdcraeft dictionary build`` attaches ``bt_*`` tables to the
same ``wyrdcraeft.sqlite3`` database used by morphology workflows.
The ``forms`` table and its rows are never dropped or altered. If the target
database does not exist, the command exits with an error that points you to
``wyrdcraeft dictionary build --with-morphology``.

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
     - ``%USERPROFILE%\\AppData\\Local\\wyrdcraeft\\wyrdcraeft.sqlite3``
   * - macOS
     - ``~/Library/Application Support/wyrdcraeft``
     - ``~/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3``
   * - Linux
     - ``~/.config/wyrdcraeft``
     - ``~/.config/wyrdcraeft/wyrdcraeft.sqlite3``

Override precedence
~~~~~~~~~~~~~~~~~~~

The command always uses the canonical app-data database path resolved from
``WYRDCRAEFT_APP_DATA_DIR`` or ``app_data_dir`` in ``.wyrdcraeft.toml``.

Re-run behavior
~~~~~~~~~~~~~~~

Each default ``build`` pass truncates and reloads ``bt_*`` contents so the
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

    # Packaged default source; attach bt_* tables to the app-data database
    wyrdcraeft dictionary build --report /tmp/bt_report.json

    # Custom Bosworth-Toller corpus override
    wyrdcraeft dictionary build --source /path/to/oe_bt.txt --report /tmp/bt_report.json

See also
--------

- :doc:`command_morphology_generate` — morphology ``forms`` via ``dictionary build --with-morphology``
