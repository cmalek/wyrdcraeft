Morphology Architecture
=======================

What This Flow Does
-------------------

The morphology flow loads bundled Old English lemma and paradigm files, assigns
paradigms and classes, generates inflected forms, seeds Wright-backed catalog
tables, and writes the results into the canonical SQLite database.

For Scholars and Translators
----------------------------

This flow is a generator, not just a lookup table loader.

Its job is to start from lemma-oriented source data and emit a large form
inventory that can later support analysis and browse. In the current
implementation, the build also seeds a separate Wright-backed catalog and
assigns many lemmas to reusable morph classes.

For scholarly readers, the key distinction is:

- the direct build path produces forms and class assignments
- Wright section prose is optional enrichment, not a prerequisite for build

Sources, Provenance, and Limits
-------------------------------

Current build code reads four bundled morphology inputs directly:

- ``dict_adj-vb-part-num-adv-noun.txt``
- ``manual_forms.txt``
- ``para_vb.txt``
- ``prefixes.txt``

It also reads ``wright_paradigms.json`` to seed the catalog and support lemma
classification.

Current repository evidence supports these present-tense claims:

- ``GeneratorSession.load_all()`` loads the four bundled text inputs
- ``MorphologyCatalogLoader.ensure_seeded()`` loads the Wright catalog fixture
- ``LemmaMorphClassAssigner.assign_all()`` writes ``lemma_morph_classes`` during
  build
- ``wyrdcraeft morphology ingest-wright-text`` is a separate command

Current repository evidence does not prove the full off-repo authorship history
of every bundled file, so provenance beyond their checked-in use should be read
carefully.

Process Flow
------------

1. ``wyrdcraeft morphology build`` resolves default or overridden input paths.
2. ``GeneratorSession.load_all()`` loads lemmas, manual forms, verb paradigms,
   and prefixes.
3. The build normalizes prefixes and hyphens and computes syllable counts.
4. The assigner layer applies verb, adjective, and noun paradigm assignment.
5. ``MorphologyCatalogLoader.ensure_seeded()`` seeds the Wright-backed catalog
   when needed or when ``--refresh-catalog`` is passed.
6. ``LemmaMorphClassAssigner.assign_all()`` assigns inflectable lemmas to
   catalog classes keyed by ``(normalized_title, pos)``.
7. Generation dispatch runs staged output in this order: manual, verbs,
   adjectives, adverbs, numerals, nouns.
8. ``SqliteIndexSink`` writes ``forms`` into the canonical database.

For Engineers
-------------

Primary entrypoints:

- command: ``wyrdcraeft morphology build``
- command: ``wyrdcraeft morphology query``
- command: ``wyrdcraeft morphology ingest-wright-text``
- session root: ``wyrdcraeft.services.morphology.session.GeneratorSession``
- read side: ``wyrdcraeft.services.morphology.generation.query.MorphologyQueryService``

Main build-time collaborators visible in the CLI wiring are:

- paradigm assignment helpers: ``set_verb_paradigm()``,
  ``set_adj_paradigm()``, ``set_noun_paradigm()``
- generation dispatch: ``output_manual_forms()``, ``generate_vbforms()``,
  ``generate_adjforms()``, ``generate_advforms()``, ``generate_numforms()``,
  ``generate_nounforms()``
- catalog loader: ``MorphologyCatalogLoader``
- lemma classifier: ``LemmaMorphClassAssigner``
- paradigm-to-class resolver: ``ParadigmClassMapper``

The build command owns the critical ordering: class seeding and lemma-class
assignment happen before form emission, but Wright prose ingest does not.

Data Read and Data Written
--------------------------

Read:

- ``wyrdcraeft/etc/morphology/dict_adj-vb-part-num-adv-noun.txt``
- ``wyrdcraeft/etc/morphology/manual_forms.txt``
- ``wyrdcraeft/etc/morphology/para_vb.txt``
- ``wyrdcraeft/etc/morphology/prefixes.txt``
- ``wyrdcraeft/etc/morphology/wright_paradigms.json``

Written during ``morphology build``:

- ``forms``
- ``morph_sources``
- ``morph_classes``
- ``wright_sections`` with section rows seeded and ``section_text`` still null
- junction tables linking classes to sources and Wright sections
- ``lemma_morph_classes``

Read during query:

- ``forms``
- optional dictionary joins through ``BTQueryService``

Sharp Edges and Non-Goals
-------------------------

- ``wyrdcraeft morphology build`` writes the real canonical app-data database
  by default.
- The direct build path is parity-oriented and stage-ordered; it is not a loose
  collection of independent generators.
- Wright section prose is not loaded automatically during build.
- This page documents the current generator architecture. It does not claim a
  full survey of Old English morphological analyzers.

Optional Wright Section Ingest
------------------------------

``wyrdcraeft morphology ingest-wright-text`` is a separate ingest path.

It reads a markdown source such as ``data/sources/wright.md`` and uses
``WrightSectionTextIngester`` to populate ``wright_sections.section_text`` for
section numbers that were already seeded into the catalog.

That means:

- build can succeed without stored section prose
- class assignment can succeed without stored section prose
- dictionary browse can still work without stored section prose
- only Wright excerpt display is degraded when prose has not been ingested

Related Work and Alternatives
-----------------------------

The current repository explicitly builds on Tichý-derived morphology inputs and
on Wright-backed class metadata.

Code and checked-in docs support these narrow claims:

- the generator is organized around bundled Tichý-derived input files
- the catalog layer adds a Wright-oriented class system and citation surface
- the repository does not currently integrate an alternative Old English
  generation engine alongside this one

So this architecture should be read as one practical implementation, not as a
comparative survey.
