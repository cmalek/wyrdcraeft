Dictionary Architecture
=======================

What This Flow Does
-------------------

The dictionary flow parses Bosworth-Toller source lines, segments English
glosses into senses, merges editorial instructions, and writes a structured
SQLite index into ``bt_*`` tables. The same package also serves query-time
browse search and the Textual browse shell over those tables plus linked
morphology rows.

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

Browse search ranks dictionary headwords and variant spellings at query time.
Morphology sidebar grids and Wright morph-class metadata reflect prior
dictionary build morphology choices; they are downstream of morphology
generation, not an independent philological source.

Sources, Provenance, and Limits
-------------------------------

Current code paths use ``data/oe_bt.txt`` as the default dictionary source for
``wyrdcraeft dictionary build``.

Repository evidence supports these current-behavior claims:

- the CLI defaults to ``data/oe_bt.txt``
- the build path writes into the canonical ``wyrdcraeft.sqlite3`` database
- the unified build can regenerate morphology when ``forms`` is empty or when
  ``--with-morphology`` is requested
- the optional LLM repair pass is warning-scoped, not the primary parsing path
- browse search requires populated ``bt_*`` tables only; there is no separate
  search-index rebuild step

Repository evidence is less certain about upstream file history. Current docs
suggest ``data/oe_bt.txt`` likely derives from an upstream
``oe_bosworthtoller.txt.bz2`` source, but that upstream artifact is not checked
into this repository.

Process Flow
------------

Build:

1. ``wyrdcraeft dictionary build`` resolves the canonical SQLite target.
2. ``DictionaryBuildPipeline`` (or ``BTIndexPipeline`` for dictionary-only paths)
   rebuilds ``bt_*`` tables from source lines.
3. ``BTLineParser`` classifies and parses accepted Bosworth-Toller lines.
4. ``BTSenseSegmenter`` extracts structured senses from accepted entry bodies.
5. Parse warnings are written to ``parse_warnings.jsonl`` on each CLI build
   run, using either the explicit ``--warnings-file`` path or the default file
   beside the canonical database.
6. ``BTLLMFixPass`` may re-parse warning lines only when ``--llm-fix-pass`` is
   enabled.
7. ``BTEditorialMerger`` consolidates parsed lines into entry-level records.
8. ``BTSqliteSink.write_entries()`` reloads the ``bt_*`` tables.
9. ``FormsEntryRelinker`` repopulates ``forms.entry_id`` foreign keys after the
   dictionary rebuild.

Browse:

1. ``wyrdcraeft dictionary browse`` resolves the canonical database path.
2. ``DictionaryBrowseQueryService`` searches ``bt_entries`` and ``bt_variants``
   with the locked 12-tier ranking ladder.
3. ``DictionaryBrowseApp`` (Textual) renders results, entry details, morph-class
   metadata, optional Wright § excerpts, and POS-filtered morphology grids.

For Engineers
-------------

Primary entrypoints:

- command: ``wyrdcraeft dictionary build``
- command: ``wyrdcraeft dictionary query``
- command: ``wyrdcraeft dictionary browse``
- command: ``wyrdcraeft dictionary ingest-wright-text``
- command: ``wyrdcraeft dictionary audit-wright``
- build orchestrator: ``wyrdcraeft.services.dictionary.pipeline.BTIndexPipeline``
  and ``wyrdcraeft.services.dictionary.build_pipeline.DictionaryBuildPipeline``
- dictionary lookup: ``wyrdcraeft.services.dictionary.query.BTQueryService``
- browse search/details: ``wyrdcraeft.services.dictionary.browse_query.DictionaryBrowseQueryService``
- browse TUI: ``wyrdcraeft.services.dictionary.browse_tui.DictionaryBrowseApp``

Key collaborators named directly in the pipeline constructor are:

- ``BTLineParser``
- ``BTSenseSegmenter``
- ``BTEditorialMerger``

The writer is ``BTSqliteSink``, which creates or reuses the ``bt_*`` schema and
truncates prior dictionary rows before reloading them.

Browse-facing morph-class and Wright-section lookups delegate to
``MorphologyCatalogQueryService``.

Data Read and Data Written
--------------------------

Build read:

- ``data/oe_bt.txt`` by default
- optional warning-repair configuration for local Ollama use
- existing ``forms`` rows when relinking ``entry_id``

Build written:

- ``bt_entries``
- ``bt_senses``
- ``bt_variants``
- ``bt_edit_log``
- updated ``forms.entry_id`` values after relink
- default ``parse_warnings.jsonl`` with an overridable path
- optional JSON report from ``IndexReport.write_json()``

Browse read:

- ``bt_entries``, ``bt_senses``, ``bt_variants`` for search hits and entry details
- ``forms`` and reference joins for morphology sidebar grids
- ``lemma_morph_classes`` and catalog tables for morph-class display
- ``wright_sections.section_text`` when a Wright § citation is opened

Query reads the same canonical database through ``BTQueryService`` and resolves
entries by normalized key or normalized title.

Browse Search Ranking
---------------------

``DictionaryBrowseQueryService.search()`` implements the locked 12-tier ladder
over headwords and variant spellings. Lower ``rank_tier`` means higher priority.
Within tier, results sort by lexical distance, then headword.

Query normalization reuses ``BTSpellingNormalizer``, ``normalize_old_english``,
and ``normalize_morphology_title`` consistently with dictionary indexing.
Undiacritized queries such as ``abbod`` can match macronized headwords.

Morphology Classification in Browse
-----------------------------------

Browse can surface morph-class information for a selected entry, but that
information is not computed during dictionary build.

Instead, ``DictionaryBrowseQueryService`` normalizes the selected headword,
maps dictionary POS to catalog POS, and asks
``MorphologyCatalogQueryService.lookup_lemma_class()``. That lookup depends on
``lemma_morph_classes``, ``morph_classes``, and Wright section junction rows
seeded by ``dictionary build --with-morphology``.

Optional Wright Excerpt Lookup
------------------------------

Stored Wright prose is a separate browse enhancement.

``DictionaryBrowseQueryService.lookup_wright_section_text()`` delegates to
``MorphologyCatalogQueryService.lookup_wright_section_text()``, which returns
the value currently stored in ``wright_sections.section_text``.

That value exists only if someone has already run
``wyrdcraeft dictionary ingest-wright-text``.

Sharp Edges and Non-Goals
-------------------------

- Dictionary build depends on an existing canonical database path; morphology
  may need to run first when ``forms`` is empty and ``--with-morphology`` is not
  used.
- The optional LLM repair pass does not replace deterministic parsing; it only
  retries warning lines.
- Browse search returns dictionary entries only; morphology-only matches
  without a dictionary entry are not shown.
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
