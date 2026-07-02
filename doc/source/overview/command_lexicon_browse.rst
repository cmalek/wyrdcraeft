``wyrdcraeft lexicon browse``
===============================

This command opens a read-only Textual browse shell for unified lexicon search
over the ``lexicon_*`` read-model inside the canonical ``wyrdcraeft.sqlite3``
database.

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

On macOS with the ``ABC Extended`` keyboard layout, ``wyrdcraeft lexicon browse``
supports direct entry of those characters in the search box, including the
dead-key compose paths for macrons and dotted letters.

Other terminals and keyboard layouts may also pass these characters through,
but terminal support varies. If direct typing does not work in your terminal,
use the fallback character buttons shown below the search field.

.. figure:: /_images/lexicon-browse-macos-abc-extended-keys.jpg
   :alt: textual keys output showing macOS ABC Extended option-key events for Old English character entry
   :width: 100%

   ``textual keys`` on macOS ``ABC Extended`` shows the option-key events used
   for direct Old English character entry in ``wyrdcraeft lexicon browse``.

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

    # Open browse against the default app-data database
    wyrdcraeft lexicon browse

See also
--------

- :doc:`command_lexicon_build`
- :doc:`command_morphology_query`
- :doc:`command_dictionary_lookup`
