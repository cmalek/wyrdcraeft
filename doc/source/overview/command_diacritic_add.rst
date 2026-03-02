``wyrdcraeft diacritic add``
============================

This page documents the ``wyrdcraeft diacritic add`` command, which adds a
normalized/macron pair to the **unique** list of the macron index.

Purpose
-------

The command inserts a single mapping from a normalized form (key) to a macronized
form (value) in the macron index JSON. It is used to extend or correct the
canonical list used by :doc:`command_convert_mark_diacritics` and related
workflows.

The **normalized** argument is normalized (lowercase, ð→þ, strip diacritics,
internal hyphens) before storage so the key matches index convention. The
**macron_form** is stored as-is.

Command syntax
--------------

.. code-block:: bash

    wyrdcraeft diacritic add NORMALIZED MACRON_FORM [OPTIONS]

Arguments
---------

- **NORMALIZED**: Key form; normalized before lookup/insert.
- **MACRON_FORM**: Display form with macrons; stored as-is in the unique list.

Options
-------

- ``--index-path PATH``: Path to the macron index JSON file. Default: packaged
  default path.
- ``--force``: Overwrite an existing unique entry if the normalized key already
  exists. Does not apply when the key is in the **ambiguous** list; resolve
  those via ``wyrdcraeft diacritic disambiguate`` first.

Examples
--------

.. code-block:: bash

    wyrdcraeft diacritic add cyning cȳning
    wyrdcraeft diacritic add "some key" "sōme fōrm" --force
    wyrdcraeft diacritic add word wōrd --index-path /path/to/oe_bt_macron_index.json
