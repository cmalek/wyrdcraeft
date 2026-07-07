``wyrdcraeft dictionary browse``
====================================

This command opens a read-only Textual browse shell for dictionary search over
``bt_entries`` and ``bt_variants`` inside the canonical ``wyrdcraeft.sqlite3``
database. Search runs at query time with a 12-tier headword-and-variant ranking
ladder; morphology sidebar details load from ``forms`` and catalog tables for
the selected entry.

The TUI is browse-only in v1: there are no edit or provenance-editing flows.

Prerequisites
-------------

Run :doc:`command_dictionary_index_bt` first. The browse shell requires
populated ``bt_entries``, ``bt_senses``, and ``bt_variants`` tables.

If those tables are missing or empty, the command fails with guidance to run
``wyrdcraeft dictionary build``.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft dictionary browse [OPTIONS]

Options
-------

Default database location
-------------------------

The browse shell always opens the OS application-data ``wyrdcraeft.sqlite3``
path documented in :ref:`morphology-sqlite-index-database`.

On macOS, that default file is typically:

.. code-block:: text

    ~/Library/Application Support/wyrdcraeft/wyrdcraeft.sqlite3

Browse behavior
---------------

The shell uses a simple two-pane layout:

- top search box (search runs on Enter only)
- left results pane for dictionary entries
- right details pane with summary sense, full senses, etymology, morph-class
  metadata, selectable Wright § citations, and POS-filtered morphology grids

Search ranking (lower tier number = higher priority):

1. exact headword on ``bt_entries.headword``
2. exact variant on ``bt_variants.spelling_macronized``
3. headword ``normalized_title``
4. variant ``normalized_title``
5. headword ``norm_key`` (diacritic-stripped)
6. variant norm key
7.–12. prefix/suffix matches on display headword, variant spelling,
   ``normalized_title``, and norm keys

Within a tier, results sort by lexical distance, then headword. Browse returns
dictionary entries only; there is no orphan morphology section.

When exactly one dictionary entry matches, the details pane opens that entry
immediately.

Old English character input
---------------------------

When the search field has focus, you can type Old English characters directly.
The browse shell accepts these characters:

- ``æ``, ``Æ``
- ``ð``, ``Ð``
- ``þ``, ``Þ``
- ``ā``, ``Ā``
- ``ē``, ``Ē``
- ``ī``, ``Ī``
- ``ō``, ``Ō``
- ``ū``, ``Ū``
- ``ȳ``, ``Ȳ``
- ``ǣ``, ``Ǣ``
- ``ċ``, ``Ċ``
- ``ġ``, ``Ġ``

On macOS with the ``ABC Extended`` keyboard layout, ``wyrdcraeft dictionary browse``
supports direct entry of those characters in the search box, including the
dead-key compose paths for macrons and dotted letters.

Other terminals and keyboard layouts may also pass these characters through,
but terminal support varies. If direct typing does not work in your terminal,
use the fallback character buttons shown below the search field.

.. figure:: /_images/lexicon-browse-macos-abc-extended-keys.jpg
   :alt: textual keys output showing macOS ABC Extended option-key events for Old English character entry
   :width: 100%

   ``textual keys`` on macOS ``ABC Extended`` shows the option-key events used
   for direct Old English character entry in ``wyrdcraeft dictionary browse``.

Wright section text
-------------------

Optional Wright paragraph text is loaded on demand when you select a § citation
in the detail pane. Stored prose comes from
``wyrdcraeft dictionary ingest-wright-text``; until that command has been run,
the modal shows an ingest-needed message.

Examples
--------

.. code-block:: bash

    # Open browse against the default app-data database
    wyrdcraeft dictionary browse

See also
--------

- :doc:`command_dictionary_index_bt`
- :doc:`command_morphology_query`
- :doc:`command_dictionary_lookup`
