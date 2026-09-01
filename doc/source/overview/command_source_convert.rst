``wyrdcraeft source convert``
=============================

This page documents the main ingestion workflow invoked as
``wyrdcraeft source convert``.

Purpose
-------

The command converts a source document (plain text or TEI XML) into the
project's standard JSON format. See :doc:`/overview/format` for the format
specification. Conversion is performed by
:class:`~wyrdcraeft.ingest.pipeline.DocumentIngestor`, which selects:

- **Heuristic path** (default): deterministic parsing and chunking for local
  ``.txt``.
- **TEI path**: direct TEI XML parsing when the source is ``.xml`` / ``.tei``.

Command syntax
--------------

.. code-block:: bash

    wyrdcraeft source convert SOURCE OUTPUT [OPTIONS]

Arguments
---------

- **SOURCE**: Path to a local ``.txt`` or TEI XML file. The file must exist.
- **OUTPUT**: Path to the output JSON file.

Options
-------

- ``--title``: Title for the document metadata. Default: derived from the
  source filename.

Examples
--------

.. code-block:: bash

    # Heuristic conversion
    wyrdcraeft source convert input.txt output.json

    # With explicit title
    wyrdcraeft source convert input.txt output.json --title "Beowulf"

    # TEI XML
    wyrdcraeft source convert edition.xml output.json
