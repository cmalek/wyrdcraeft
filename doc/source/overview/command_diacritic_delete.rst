``wyrdcraeft diacritic delete``
===============================

This page documents the ``wyrdcraeft diacritic delete`` command, which removes
a normalized/macron pair from the **unique** list of the macron index.

Purpose
-------

The command deletes a single mapping from the macron index. It prompts for
confirmation (showing both normalized and macron forms) unless ``--yes`` is
passed. The **normalized** argument is normalized (lowercase, ð→þ, strip
diacritics, internal hyphens) before lookup.

Command syntax
--------------

.. code-block:: bash

    wyrdcraeft diacritic delete NORMALIZED [OPTIONS]

Arguments
---------

- **NORMALIZED**: Key to remove; normalized before lookup.

Options
-------

- ``--index-path PATH``: Path to the macron index JSON file. Default: packaged
  default path.
- ``--yes`` / ``-y``: Skip confirmation prompt.

Examples
--------

.. code-block:: bash

    wyrdcraeft diacritic delete cyning
    wyrdcraeft diacritic delete word --yes
    wyrdcraeft diacritic delete "some key" --index-path /path/to/oe_bt_macron_index.json
