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

- **Heuristic path** (default): deterministic parsing and chunking for plain text
  and TEI XML, without LLM.
- **TEI path**: direct TEI XML parsing when the source is ``.xml`` and recognized
  as TEI.
- **LLM path**: when ``--use-llm`` is set, uses the configured LLM to assist
  extraction (requires API keys in configuration or environment).

Command syntax
--------------

.. code-block:: bash

    wyrdcraeft source convert SOURCE OUTPUT [OPTIONS]

Arguments
---------

- **SOURCE**: Path to the input file (or URL). Local files must exist.
- **OUTPUT**: Path to the output JSON file.

Options
-------

- ``--use-llm`` / ``--no-use-llm``: Use LLM for extraction. Default: ``--no-use-llm``.
- ``--llm-model``: Model ID (e.g. ``gpt-4o``, ``gemini-3-flash-preview``,
  ``qwen2.5:14b-instruct``). Overrides configuration.
- ``--llm-temperature``: LLM temperature. Overrides configuration.
- ``--llm-max-tokens``: LLM max tokens. Overrides configuration.
- ``--llm-timeout``: LLM timeout in seconds. Overrides configuration.
- ``--title``: Title for the document metadata. Default: derived from source
  filename or URL.

Examples
--------

.. code-block:: bash

    # Heuristic conversion (no LLM)
    wyrdcraeft source convert input.txt output.json

    # With explicit title
    wyrdcraeft source convert input.txt output.json --title "Beowulf"

    # LLM-assisted conversion (requires API keys in config or environment)
    wyrdcraeft source convert input.txt output.json --use-llm --llm-model gpt-4o
