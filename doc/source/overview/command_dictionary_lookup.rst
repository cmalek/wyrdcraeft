``wyrdcraeft dictionary lookup``
=================================

This command looks up consolidated Bosworth-Toller dictionary entries from the
SQLite index produced by :doc:`command_dictionary_index_bt`.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft dictionary lookup LEMMA [OPTIONS]

Arguments
---------

- ``LEMMA``: headword or alternate variant spelling to resolve.

Options
-------

- ``--pos TEXT``: optional POS filter (for example ``noun``, ``adv``, ``verb``).
- ``--index-db PATH``: explicit SQLite index file path.
- ``--index-dir PATH``: directory where ``dictionary.sqlite3`` is stored.
- ``--json-output / --no-json-output``: render output as JSON instead of text.

Default database location
-------------------------

When neither ``--index-db`` nor ``--index-dir`` is supplied, wyrdcraeft reads
``dictionary.sqlite3`` from the OS application-data directory documented in
:doc:`command_dictionary_index_bt`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/dictionary.sqlite3

Text output format
------------------

Human-readable output includes lemma, POS, optional gender, ordered English
gloss senses, etymology when present, and variant spellings. Attestations and
editorial line references are not shown.

Examples
--------

.. code-block:: bash

    wyrdcraeft dictionary lookup abbod

    wyrdcraeft dictionary lookup a --pos adv

    wyrdcraeft dictionary lookup abbod \
      --index-dir /tmp/wyrdcraeft-index \
      --json-output

See also
--------

- :doc:`command_dictionary_index_bt`
- :doc:`command_morphology_query`
