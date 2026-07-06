Dictionary Architecture
=======================

What This Flow Does
-------------------

The dictionary flow parses Bosworth-Toller source lines, segments English
glosses into senses, merges editorial instructions, and writes a structured
SQLite index into ``bt_*`` tables.

For Scholars and Translators
----------------------------

This flow is not a new dictionary. It is a structured index over the
Bosworth-Toller source text that makes headwords, senses, variants, and some
editorial interventions easier to query and reuse.

The important scholarly point is that browseable entries are shaped by three
deterministic transformations:

- line parsing
- sense segmentation
- editorial merge

That means the resulting entry boundaries and sense lists are implementation
decisions over source text, not a facsimile edition.

Sources, Provenance, and Limits
-------------------------------

Current code paths use ``data/oe_bt.txt`` as the default dictionary source for
``wyrdcraeft dictionary build``.

Repository evidence supports these current-behavior claims:

- the CLI defaults to ``data/oe_bt.txt``
- the build path writes into the canonical ``wyrdcraeft.sqlite3`` database
- the command requires an existing canonical database with ``forms`` rows
- the optional LLM repair pass is warning-scoped, not the primary parsing path

Repository evidence is less certain about upstream file history. Current docs
suggest ``data/oe_bt.txt`` likely derives from an upstream
``oe_bosworthtoller.txt.bz2`` source, but that upstream artifact is not checked
into this repository.

Process Flow
------------

1. ``wyrdcraeft dictionary build`` resolves the canonical SQLite target and
   checks that ``forms`` already exist.
2. ``BTIndexPipeline.run()`` reads the source file line by line.
3. ``BTLineParser`` classifies and parses accepted Bosworth-Toller lines.
4. ``BTSenseSegmenter`` extracts structured senses from accepted entry bodies.
5. Parse warnings are written to ``parse_warnings.jsonl`` on each CLI build
   run, using either the explicit ``--warnings-file`` path or the default file
   beside the canonical database.
6. ``BTLLMFixPass`` may re-parse warning lines only when ``--llm-fix-pass`` is
   enabled.
7. ``BTEditorialMerger`` consolidates parsed lines into entry-level records.
8. ``BTSqliteSink.write_entries()`` reloads the ``bt_*`` tables.

For Engineers
-------------

Primary entrypoints:

- command: ``wyrdcraeft dictionary build``
- command: ``wyrdcraeft dictionary lookup``
- orchestrator: ``wyrdcraeft.services.dictionary.pipeline.BTIndexPipeline``
- read side: ``wyrdcraeft.services.dictionary.query.BTQueryService``

Key collaborators named directly in the pipeline constructor are:

- ``BTLineParser``
- ``BTSenseSegmenter``
- ``BTEditorialMerger``

The writer is ``BTSqliteSink``, which creates or reuses the ``bt_*`` schema and
truncates prior dictionary rows before reloading them.

Data Read and Data Written
--------------------------

Read:

- ``data/oe_bt.txt`` by default
- optional warning-repair configuration for local Ollama use

Written:

- ``bt_entries``
- ``bt_senses``
- ``bt_variants``
- ``bt_edit_log``
- default ``parse_warnings.jsonl`` with an overridable path
- optional JSON report from ``IndexReport.write_json()``

Lookup reads the same canonical database through ``BTQueryService`` and resolves
entries by normalized key or normalized title.

Sharp Edges and Non-Goals
-------------------------

- This flow depends on an existing canonical database path and currently
  expects morphology to have created the database first.
- The optional LLM repair pass does not replace deterministic parsing; it only
  retries warning lines.
- The flow documents current Bosworth-Toller indexing behavior. It does not
  promise a diplomatic transcription or a full editorial history of every
  source intervention.

Parsing and Editorial Merge
---------------------------

The business logic hinge is the merge step.

``BTIndexPipeline`` does not write one SQLite row per source line. Instead it
parses many line-level fragments and then asks ``BTEditorialMerger`` to
consolidate them into dictionary entries. That is why the sink writes entry,
sense, variant, and edit-log tables rather than a line-for-line source shadow.

This is also where the repository keeps an explicit boundary between:

- source text interpretation
- editorial instruction application
- persisted browse/query structure
