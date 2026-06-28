``wyrdcraeft lexicon browse``
===============================

This command opens a read-only Textual browse shell for unified lexicon search
over the ``lexicon_*`` read-model inside ``morphology.sqlite3``.

The TUI is browse-only in v1: there are no edit or provenance-editing flows.

Prerequisites
-------------

Run :doc:`command_lexicon_build` first. The browse shell requires populated
``lexicon_entries`` and ``lexicon_search_keys`` tables.

If those tables are missing or empty, the command fails with guidance to run
``wyrdcraeft lexicon build``.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft lexicon browse [OPTIONS]

Options
-------

- ``--index-db PATH``: explicit SQLite index file path.
- ``--index-dir PATH``: directory where ``morphology.sqlite3`` is stored.

Default database location
-------------------------

When neither ``--index-db`` nor ``--index-dir`` is supplied, wyrdcraeft opens
the OS application-data ``morphology.sqlite3`` path documented in
:ref:`morphology-sqlite-index-database`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/morphology.sqlite3

Browse behavior
---------------

The shell uses a simple two-pane layout:

- top search box (search runs on Enter only)
- left results pane for dictionary entries
- lower orphan section for morphology-only matches
- right details pane with summary sense, full senses, etymology, and grouped
  morphology rows

Search ranking:

1. exact dictionary lemma or variant hits
2. morphology lemma or stem hits joined to a dictionary entry
3. morphology form hits joined to a dictionary entry
4. orphan morphology hits shown separately

When exactly one dictionary entry matches, the details pane opens that entry
immediately.

Staleness hints
---------------

When source ``forms`` or ``bt_*`` row counts no longer match the stored build
metadata, the browse shell shows a note suggesting ``wyrdcraeft lexicon build``.
After a fresh build, the idle details pane shows the last ``built_at`` timestamp.

Examples
--------

.. code-block:: bash

    # Open browse against the default app-data morphology database
    wyrdcraeft lexicon browse

    # Open browse against an explicit morphology SQLite file
    wyrdcraeft lexicon browse \
      --index-db "$HOME/Library/Application Support/wyrdcraeft/morphology.sqlite3"

    # Open browse using a custom index directory
    wyrdcraeft lexicon browse --index-dir /tmp/wyrdcraeft-index

See also
--------

- :doc:`command_lexicon_build`
- :doc:`command_morphology_query`
- :doc:`command_dictionary_lookup`
