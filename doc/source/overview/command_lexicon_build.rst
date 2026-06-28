``wyrdcraeft lexicon build``
==============================

This command rebuilds the lexicon browse read-model inside
``morphology.sqlite3``. It replaces only ``lexicon_*`` tables derived from
existing morphology ``forms`` rows and existing Bosworth-Toller ``bt_*`` tables.

It does **not** regenerate morphology or dictionary source data.

Prerequisites
-------------

Before running ``lexicon build``, the target morphology database must already
contain:

- ``forms`` rows from :doc:`command_morphology_generate`
- ``bt_*`` tables from :doc:`command_dictionary_index_bt` (default attach to
  ``morphology.sqlite3``) or an equivalent in-database dictionary index

When ``bt_entries``, ``bt_senses``, or ``bt_variants`` are missing, the command
fails with a clear error listing the absent source tables.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft lexicon build [OPTIONS]

Options
-------

- ``--index-db PATH``: explicit SQLite index file path.
- ``--index-dir PATH``: directory where ``morphology.sqlite3`` is stored.

Default database location
-------------------------

When neither ``--index-db`` nor ``--index-dir`` is supplied, wyrdcraeft writes
to the OS application-data ``morphology.sqlite3`` path documented in
:ref:`morphology-sqlite-index-database`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/morphology.sqlite3

What gets rebuilt
-----------------

Each run replaces these read-model tables only:

- ``lexicon_entries`` — one row per real dictionary entry
- ``lexicon_forms`` — morphology rows joined to entries when possible
- ``lexicon_search_keys`` — normalized lookup keys for unified search
- ``lexicon_build_meta`` — rebuild timestamp and source row counts

The command never modifies ``forms`` or ``bt_*`` source tables.

Build metadata and staleness
----------------------------

After a successful rebuild, ``lexicon_build_meta`` stores:

- schema version
- ``built_at`` UTC timestamp
- source ``forms`` row count at rebuild time
- source ``bt_entries`` row count at rebuild time

Re-run ``lexicon build`` after you regenerate morphology or re-index dictionary
tables so browse search stays aligned with the current database contents.

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

    # Rebuild against an explicit morphology SQLite file
    wyrdcraeft lexicon build \
      --index-db "$HOME/Library/Application Support/wyrdcraeft/morphology.sqlite3"

    # Rebuild using a custom index directory
    wyrdcraeft lexicon build --index-dir /tmp/wyrdcraeft-index

Typical bootstrap sequence
--------------------------

.. code-block:: bash

    wyrdcraeft morphology generate
    wyrdcraeft dictionary index-bt --source data/oe_bt.txt
    wyrdcraeft lexicon build

See also
--------

- :doc:`command_lexicon_browse`
- :doc:`command_morphology_generate`
- :doc:`command_dictionary_index_bt`
