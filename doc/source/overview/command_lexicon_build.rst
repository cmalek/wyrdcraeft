``wyrdcraeft lexicon build``
==============================

This command rebuilds the lexicon browse read-model inside
``wyrdcraeft.sqlite3``. It replaces only ``lexicon_*`` tables derived from
existing morphology ``forms`` rows and existing Bosworth-Toller ``bt_*`` tables.

It does **not** regenerate morphology or dictionary source data.

Prerequisites
-------------

Before running ``lexicon build``, the target morphology database must already
contain:

- ``forms`` rows from :doc:`command_morphology_generate` (``wyrdcraeft morphology build``)
- ``bt_*`` tables from :doc:`command_dictionary_index_bt` (``wyrdcraeft dictionary build``,
  default attach to ``wyrdcraeft.sqlite3``)

When ``bt_entries``, ``bt_senses``, or ``bt_variants`` are missing, the command
fails with a clear error listing the absent source tables.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft lexicon build [OPTIONS]

Options
-------

- ``--no-tui``: force the plain stderr/stdout renderer.
- ``--quiet``: suppress live progress output while keeping the final summary.

Default database location
-------------------------

The command always writes to the OS application-data ``wyrdcraeft.sqlite3``
path documented in :ref:`morphology-sqlite-index-database`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3

What gets rebuilt
-----------------

Each run replaces these read-model tables only:

- ``lexicon_entries`` — one row per real dictionary entry
- ``lexicon_forms`` — morphology rows joined to entries when possible
- ``lexicon_search_keys`` — normalized lookup keys for unified search
- ``lexicon_build_meta`` — rebuild timestamp and source row counts

The command never modifies ``forms`` or ``bt_*`` source tables.

Monitor behavior
----------------

By default, ``wyrdcraeft lexicon build`` launches a full-screen Textual build
monitor when the terminal is interactive. The monitor shows live stage
progress, structured log output, and the final build summary.

Use ``--no-tui`` to force the plain renderer instead. Use ``--quiet`` when you
want the final summary without the live progress stream.

Build metadata and staleness
----------------------------

After a successful rebuild, ``lexicon_build_meta`` stores:

- schema version
- ``built_at`` UTC timestamp
- source ``forms`` row count at rebuild time
- source ``bt_entries`` row count at rebuild time

Re-run ``lexicon build`` after you rebuild morphology or dictionary tables so
browse search stays aligned with the current database contents.

Completion output
-----------------

On success the command prints:

- resolved ``index_db`` path
- ``built_at`` timestamp
- source row counts observed during rebuild
- counts of ``lexicon_*`` rows written

Examples
--------

.. code-block:: bash

    # Rebuild lexicon tables in the default app-data morphology database
    wyrdcraeft lexicon build

Typical bootstrap sequence
--------------------------

.. code-block:: bash

    wyrdcraeft morphology build
    wyrdcraeft dictionary build --source data/oe_bt.txt
    wyrdcraeft lexicon build

See also
--------

- :doc:`command_lexicon_browse`
- :doc:`command_morphology_generate`
- :doc:`command_dictionary_index_bt`
