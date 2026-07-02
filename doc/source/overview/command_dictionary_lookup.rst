``wyrdcraeft dictionary lookup``
=================================

This command looks up consolidated Bosworth-Toller dictionary entries from the
``bt_*`` tables in the canonical ``wyrdcraeft.sqlite3`` database.

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
- ``--json-output / --no-json-output``: render output as JSON instead of text.

Default database location
-------------------------

The command always reads from the canonical app-data database resolved from
``WYRDCRAEFT_APP_DATA_DIR`` or ``app_data_dir`` in ``.wyrdcraeft.toml``. If the
database does not exist, the command exits with an error pointing you to
``wyrdcraeft morphology build`` first, then ``wyrdcraeft dictionary build`` to
populate the dictionary tables.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3

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

    wyrdcraeft dictionary lookup abbod --json-output

See also
--------

- :doc:`command_dictionary_index_bt`
- :doc:`command_morphology_query`
