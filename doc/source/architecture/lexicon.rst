Lexicon Architecture
====================

What This Flow Does
-------------------

The lexicon flow rebuilds a derived browse/search read model from existing
dictionary and morphology data. It does not regenerate either source layer.

For Scholars and Translators
----------------------------

This is the layer that turns previously built data into a usable browse
surface.

The lexicon is therefore best understood as a combined reading model over:

- dictionary entries and senses
- generated forms
- normalized search keys

For scholarly users, the important point is that lexicon browse reflects prior
dictionary and morphology build choices. It is downstream of them, not an
independent philological source.

Sources, Provenance, and Limits
-------------------------------

Current code paths require the target canonical SQLite database to already
contain:

- ``forms``
- ``bt_entries``
- ``bt_senses``
- ``bt_variants``

Current repository evidence supports these current-behavior claims:

- ``wyrdcraeft lexicon build`` replaces ``lexicon_*`` rows only
- ``rebuild_lexicon()`` is a thin wrapper around ``LexiconBuilder.rebuild()``
- browse search is served through ``LexiconQueryService``
- Wright section prose is not required for lexicon build

Process Flow
------------

1. ``wyrdcraeft lexicon build`` resolves the canonical database path.
2. ``rebuild_lexicon()`` constructs ``LexiconBuilder`` and calls ``rebuild()``.
3. ``LexiconBuilder`` verifies that required source and target tables exist.
4. The builder clears prior ``lexicon_*`` rows.
5. It loads source rows, infers POS alignment where needed, and projects
   dictionary-backed entry rows.
6. It projects morphology rows into ``lexicon_forms``, linking to entries when
   possible and preserving orphans when not.
7. It generates normalized search keys for headwords, variants, stems, and
   forms.
8. It writes build metadata into ``lexicon_build_meta``.

For Engineers
-------------

Primary entrypoints:

- command: ``wyrdcraeft lexicon build``
- command: ``wyrdcraeft lexicon browse``
- rebuild wrapper: ``wyrdcraeft.services.lexicon.build.rebuild_lexicon()``
- orchestrator: ``wyrdcraeft.services.lexicon.build.LexiconBuilder``
- read side: ``wyrdcraeft.services.lexicon.query.LexiconQueryService``

Important implementation boundaries:

- lexicon build is a rebuild of read-model tables, not a live query join
- lexicon query uses ``lexicon_search_keys`` first, then resolves details from
  ``lexicon_entries`` and ``lexicon_forms``
- browse-facing morph-class and Wright-section lookups are delegated to
  ``MorphologyCatalogQueryService``

Data Read and Data Written
--------------------------

Read:

- ``forms``
- ``bt_entries``
- ``bt_senses``
- ``bt_variants``
- ``lemma_morph_classes`` and catalog tables indirectly during browse details

Written:

- ``lexicon_entries``
- ``lexicon_forms``
- ``lexicon_search_keys``
- ``lexicon_build_meta``

Browse reads:

- search hits from ``lexicon_search_keys``
- entry details from ``lexicon_entries`` and ``lexicon_forms``
- optional class and Wright citation metadata from catalog tables

Sharp Edges and Non-Goals
-------------------------

- ``lexicon build`` fails when required source tables are missing.
- Rebuilding lexicon does not refresh stale dictionary or morphology data.
- The browse model preserves orphans, so not every morphology form resolves to
  a dictionary-backed entry.
- This flow is a read-model build, not a ranking experiment or corpus analysis
  engine.

Morphology Classification
-------------------------

Lexicon browse can surface morph-class information for a selected entry, but
that information is not computed by ``LexiconBuilder`` itself.

Instead, ``LexiconQueryService._lookup_entry_morph_class()``:

- normalizes the selected headword
- maps dictionary POS to catalog POS
- asks ``MorphologyCatalogQueryService.lookup_lemma_class()``

That lookup depends on:

- ``lemma_morph_classes``
- ``morph_classes``
- Wright section junction rows

So morphology classification in browse is a downstream read of the catalog
layer seeded by ``morphology build``.

Optional Wright Excerpt Lookup
------------------------------

Stored Wright prose is a separate browse enhancement.

``LexiconQueryService.lookup_wright_section_text()`` simply delegates to
``MorphologyCatalogQueryService.lookup_wright_section_text()``, which returns
the value currently stored in ``wright_sections.section_text``.

That value exists only if someone has already run
``wyrdcraeft morphology ingest-wright-text``.

So:

- lexicon build does not require section prose
- ordinary browse search does not require section prose
- opening a Wright excerpt is the part that depends on prior prose ingest
