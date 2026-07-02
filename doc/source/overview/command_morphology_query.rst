``wyrdcraeft morphology query``
===============================

This command looks up generated morphology rows from the canonical SQLite
index produced by :doc:`command_morphology_generate`.

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
- ``--with-dictionary``: attach matching Bosworth-Toller dictionary entries.
- ``--dictionary-db PATH``: optional dictionary SQLite index path override.

Provide exactly one of ``--lemma`` or ``--form``.

Dictionary join
-----------------

When ``--with-dictionary`` is set, the command resolves a dictionary SQLite
database in this order:

1. ``--dictionary-db PATH`` when provided.
2. Sibling ``dictionary.sqlite3`` in the same directory as ``--db``.
3. The morphology database itself when it contains ``bt_*`` tables (attach mode).

The lookup uses ``normalize_old_english`` on the lemma token. When all returned
morphology rows share one unambiguous ``wordclass`` (for example ``noun``), the
join filters dictionary entries to the matching POS. Mixed or unmapped
``wordclass`` values return all dictionary homographs for the normalized key.

With ``--json-output``, the payload becomes an object with ``forms`` and
``dictionary`` keys. Without ``--with-dictionary``, output is unchanged.

Default database location
-------------------------

There is no implicit default for ``--db`` today. After running
``wyrdcraeft morphology build``, the index is written to the OS application-
data path documented in :ref:`morphology-sqlite-index-database`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3

Examples
--------

.. code-block:: bash

    wyrdcraeft morphology query \
      --db "$HOME/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3" \
      --lemma helpan \
      --limit 20

    wyrdcraeft morphology query \
      --db /tmp/wyrdcraeft-index/wyrdcraeft.sqlite3 \
      --form helpe \
      --json-output

    wyrdcraeft morphology query \
      --db "$HOME/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3" \
      --lemma abbod \
      --with-dictionary \
      --json-output

See also
--------

- :doc:`command_morphology_generate`
- :doc:`command_dictionary_lookup`
