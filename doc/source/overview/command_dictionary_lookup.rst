``wyrdcraeft dictionary lookup``
=================================

This command looks up consolidated Bosworth-Toller dictionary entries from the
``bt_*`` tables in ``morphology.sqlite3`` by default, or from a standalone
``dictionary.sqlite3`` with ``--standalone``.

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
- ``--index-dir PATH``: directory where ``morphology.sqlite3`` is stored by
  default, or ``dictionary.sqlite3`` with ``--standalone``.
- ``--standalone``: read from ``dictionary.sqlite3`` instead of
  ``morphology.sqlite3``.
- ``--json-output / --no-json-output``: render output as JSON instead of text.

Default database location
-------------------------

When neither ``--index-db`` nor ``--index-dir`` is supplied, wyrdcraeft reads
``bt_*`` tables from the OS application-data ``morphology.sqlite3`` path
documented in :doc:`command_morphology_generate`. If that database does not
exist, the command exits with an error pointing you to
``wyrdcraeft morphology generate`` or to an explicit ``--index-db`` /
``--index-dir`` override.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/morphology.sqlite3

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

    wyrdcraeft dictionary lookup abbod --standalone \
      --index-db /var/lib/wyrdcraeft/dictionary.sqlite3

See also
--------

- :doc:`command_dictionary_index_bt`
- :doc:`command_morphology_query`
