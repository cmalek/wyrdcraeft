``wyrdcraeft morphology query``
===============================

This command looks up generated morphology rows from the SQLite index produced
by :doc:`command_morphology_generate`.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft morphology query [OPTIONS]

Options
-------

- ``--db PATH`` (**required**): path to the morphology SQLite index database.
- ``--lemma TEXT``: lookup rows by lemma or root token.
- ``--form TEXT``: lookup rows by surface form.
- ``--limit INTEGER``: maximum rows to return (default: 200).
- ``--json-output / --no-json-output``: render output as JSON instead of TSV.

Provide exactly one of ``--lemma`` or ``--form``.

Default database location
-------------------------

There is no implicit default for ``--db`` today. After running
``wyrdcraeft morphology generate`` without ``--index-db`` or ``--index-dir``,
the index is written to the OS application-data path documented in
:ref:`morphology-sqlite-index-database`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/morphology.sqlite3

Examples
--------

.. code-block:: bash

    wyrdcraeft morphology query \
      --db "$HOME/Library/Application Support/wyrdcraeft/morphology.sqlite3" \
      --lemma helpan \
      --limit 20

    wyrdcraeft morphology query \
      --db /tmp/wyrdcraeft-index/morphology.sqlite3 \
      --form helpe \
      --json-output

See also
--------

- :doc:`command_morphology_generate`
