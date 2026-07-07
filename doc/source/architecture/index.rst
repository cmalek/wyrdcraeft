Architecture
============

This section documents the current lexicon-building architecture as it exists
in the repository today.

The same concept stack is presented at two reading depths:

- plain-language sections for scholars and translators
- implementation-facing sections for engineers and computational linguists

The three main flows are:

- dictionary
- morphology
- lexicon

.. toctree::
   :maxdepth: 2

   dictionary
   morphology
   lexicon

How the Three Flows Fit Together
--------------------------------

``wyrdcraeft`` builds its lexicon (the browse/search layer for the dictionary) in layers:

- ``wyrdcraeft dictionary build`` parses Bosworth-Toller source text into canonical dictionary entries in a SQL database.
- ``wyrdcraeft morphology build`` uses Ondrej Tichy's Old English Morphology generator to generate inflected forms and Wright & Wright-backed class metadata.
- ``wyrdcraeft lexicon build`` builds the browse/search layer helper tables from the already-built dictionary and morphology data.  It is this layer that is used by ``wyrdcraeft lexicon browse`` to run the browse/search layer.

.. note::
  ``wyrdcraeft morphology ingest-wright-text`` can be used to ingest Wright
  section text as markdown into the database, so that it can be displayed on
  demand in the browse/search layer.

Critical build paths
--------------------

Bosworth-Toller dictionary parsing pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- command: ``wyrdcraeft dictionary build``
- input: ``data/oe_bt.txt``
- orchestrator: ``wyrdcraeft.services.dictionary.pipeline.BTIndexPipeline``
- writes: ``bt_entries``, ``bt_senses``, ``bt_variants``, ``bt_edit_log``

Ondrej Tichy's Old English Morphology generator pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- command: ``wyrdcraeft morphology build``
- inputs:

  - ``wyrdcraeft/etc/morphology/dict_adj-vb-part-num-adv-noun.txt``
  - ``wyrdcraeft/etc/morphology/manual_forms.txt``
  - ``wyrdcraeft/etc/morphology/para_vb.txt``
  - ``wyrdcraeft/etc/morphology/prefixes.txt``
  - ``wyrdcraeft/etc/morphology/wright_paradigms.json``

- session root: :class:`~wyrdcraeft.services.morphology.session.GeneratorSession`
- writes: ``forms``, ``morph_sources``, ``morph_classes``, ``wright_sections``,
  ``morph_class_*``, ``lemma_morph_classes``

Derived lexicon browse/search pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- command: ``wyrdcraeft lexicon build``
- rebuild entrypoint: ``wyrdcraeft.services.lexicon.build.rebuild_lexicon()``
- orchestrator: ``wyrdcraeft.services.lexicon.build.LexiconBuilder``
- reads: ``forms`` plus ``bt_*`` tables
- writes: ``search_keys``, ``search_build_meta``

Optional Wright & Wright-backed section texts
---------------------------------------------

Wright & Wright-backed section text ingestion pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- command: ``wyrdcraeft morphology ingest-wright-text``
- ingester:
  ``wyrdcraeft.services.morphology.catalog.wright_text.WrightSectionTextIngester``
- input: ``data/sources/wright.md``
- writes: ``wright_sections.section_text``
- consumer: optional Wright excerpt display in ``wyrdcraeft lexicon browse``

Canonical Database ER Diagram
-----------------------------

The canonical app-data database is one ``wyrdcraeft.sqlite3`` file. The
diagram below shows the declared SQL foreign-key relationships from
``wyrdcraeft/models/reference.py``, ``wyrdcraeft/models/sqlalchemy.py``, and
``wyrdcraeft/models/morph_catalog.py`` after normalized-schema Phases A–D
(Alembic head ``20260706_04``). ``forms`` stores foreign keys to reference
and catalog tables only; legacy denormalized string columns
(``wordclass``, ``function``, ``wright``, ``paradigm``, ``paraID``,
``class1``–``class3``) were dropped in Phase D. The lexicon layer is a slim
search index only (``search_keys``, ``search_build_meta``).

.. mermaid::

   erDiagram
       PARTS_OF_SPEECH {
           int id PK
           text code
           text display_label
           int is_inflectable
       }

       INFLECTION_CODES {
           int id PK
           text code
           int pos_id FK
           text display_json
       }

       BT_ENTRIES {
           int id PK
           text norm_key
           text headword
           text normalized_title
           int pos_id FK
           text genders_json
           text etymology
           text see_also_json
           text source_line_nos_json
       }

       BT_SENSES {
           int id PK
           int entry_id FK
           text sense_label
           text gloss_en
           int order_index
       }

       BT_VARIANTS {
           int entry_id PK, FK
           text spelling_raw PK
           text spelling_macronized
           text normalized_title
       }

       BT_EDIT_LOG {
           int id PK
           text op
           int source_line_no
           text target_norm_key
           text target_pos
           text scope
           int applied
           text note
       }

       FORMS {
           int id PK
           int counter
           text formi
           text BT
           text title
           text normalized_title
           text stem
           text form
           text formParts
           text var
           text probability
           text comment
           text bt_key
           text title_key
           text stem_key
           text form_key
           text formi_key
           int wordclass_id FK
           int inflection_code_id FK
           int morph_class_id FK
           int entry_id FK
       }

       MORPH_SOURCES {
           int id PK
           text source_key
           text citation_apa
           text url
           text retrieved_date
           text notes
       }

       MORPH_CLASSES {
           int id PK
           text class_key
           int pos_id FK
           text canonical_name
           text modern_class
           text traditional_class
           text wright_label
           text mapping_rationale
           text notes
           int is_assignable
           text paradigmatic_words_json
           text aliases_json
           text features_json
           text recognition_hints_json
       }

       WRIGHT_SECTIONS {
           int section_no PK
           text section_text
           text work
           text notes
       }

       MORPH_CLASS_SOURCES {
           int id PK
           int morph_class_id FK
           int source_id FK
       }

       MORPH_CLASS_WRIGHT_SECTIONS {
           int id PK
           int morph_class_id FK
           int section_no FK
           int sort_order
       }

       LEMMA_MORPH_CLASSES {
           int id PK
           text normalized_title
           int pos_id FK
           int morph_class_id FK
           text assignment_source
           int confidence
           text features_json
           text notes
       }

       SEARCH_KEYS {
           int id PK
           text key_text
           text key_kind
           int rank_tier
           int entry_id FK
           int form_id FK
           text display_text
       }

       SEARCH_BUILD_META {
           text key PK
           text value
       }

       PARTS_OF_SPEECH ||--o{ INFLECTION_CODES : classifies
       PARTS_OF_SPEECH ||--o{ BT_ENTRIES : classifies
       PARTS_OF_SPEECH ||--o{ MORPH_CLASSES : classifies
       PARTS_OF_SPEECH ||--o{ LEMMA_MORPH_CLASSES : classifies
       PARTS_OF_SPEECH ||--o{ FORMS : classifies

       INFLECTION_CODES ||--o{ FORMS : tags

       BT_ENTRIES ||--o{ BT_SENSES : has
       BT_ENTRIES ||--o{ BT_VARIANTS : has
       BT_ENTRIES o|--o{ FORMS : links

       MORPH_CLASSES ||--o{ MORPH_CLASS_SOURCES : cites
       MORPH_SOURCES ||--o{ MORPH_CLASS_SOURCES : sources
       MORPH_CLASSES ||--o{ MORPH_CLASS_WRIGHT_SECTIONS : anchors
       WRIGHT_SECTIONS ||--o{ MORPH_CLASS_WRIGHT_SECTIONS : anchored_by
       MORPH_CLASSES ||--o{ LEMMA_MORPH_CLASSES : assigned_to
       MORPH_CLASSES o|--o{ FORMS : assigned_to

       BT_ENTRIES o|--o{ SEARCH_KEYS : indexed_by
       FORMS o|--o{ SEARCH_KEYS : indexed_by

.. note::

   Important business-key joins are intentionally omitted from the ER diagram
   because they are code-level joins, not declared SQL foreign keys. The main
   ones are:

   - ``forms.normalized_title`` to dictionary normalized-title lookups when
     ``forms.entry_id`` is populated at morphology build
   - ``lemma_morph_classes.(normalized_title, pos_id)`` to browse-time morph-class
     lookup when ``forms.morph_class_id`` is NULL
   - ``bt_edit_log`` targets dictionary entries by stored business fields rather
     than an entry-id foreign key

Provenance Matrix
-----------------

.. list-table::
   :header-rows: 1
   :widths: 18 23 20 13 16 10

   * - Source artifact
     - Upstream provenance
     - Checked-in local file
     - Flows
     - Role
     - Certainty
   * - ``data/oe_bt.txt``
     - This is a file of just the OCR-derived dictionary entries from the Bosworth & Toller (1908),
       for dictionary indexing.
     - ``data/oe_bt.txt``
     - dictionary
     - Default source file for ``wyrdcraeft dictionary build``.
     - medium
   * - ``oe_bosworthtoller.txt.bz2``
     - Repository docs elsewhere suggest ``data/oe_bt.txt`` derives from the
       upstream compressed file, but that upstream artifact is not checked in.
     - not checked in
     - dictionary
     - Probable upstream intermediary behind ``data/oe_bt.txt``.
     - low
   * - Bosworth-Toller bibliographic source
     - Cited in checked-in docs as the dictionary source underlying both the
       dictionary index and parts of the morphology workflow.
     - ``doc/source/index.rst``
     - dictionary, morphology
     - Bibliographic anchor for the lexical source tradition.
     - medium
   * - ``wyrdcraeft/etc/morphology/manual_forms.txt``
     - Bundled morphology input file used directly by the build command.
     - ``wyrdcraeft/etc/morphology/manual_forms.txt``
     - morphology
     - Manual forms emitted before generated stages.
     - high
   * - ``wyrdcraeft/etc/morphology/dict_adj-vb-part-num-adv-noun.txt``
     - Bundled morphology input file used directly by the build command.
     - ``wyrdcraeft/etc/morphology/dict_adj-vb-part-num-adv-noun.txt``
     - morphology
     - Main lemma inventory loaded into ``GeneratorSession.words``.
     - high
   * - ``wyrdcraeft/etc/morphology/para_vb.txt``
     - Bundled morphology input file used directly by the build command.
     - ``wyrdcraeft/etc/morphology/para_vb.txt``
     - morphology
     - Verb paradigm data and catalog assignment support.
     - high
   * - ``wyrdcraeft/etc/morphology/prefixes.txt``
     - Bundled morphology input file used directly by the build command.
     - ``wyrdcraeft/etc/morphology/prefixes.txt``
     - morphology
     - Prefix normalization input for lemma preprocessing.
     - high
   * - ``wyrdcraeft/etc/morphology/wright_paradigms.json``
     - Repository fixture consumed by the catalog loader; the file itself
       carries source rows used by the catalog.
     - ``wyrdcraeft/etc/morphology/wright_paradigms.json``
     - morphology
     - Seeds Wright-backed morph-class reference data.
     - high for in-repo use; lower for off-repo authorship history
   * - ``wyrdcraeft/etc/morphology/wright-morphology-fixture.schema.json``
     - Repository-owned schema for the Wright catalog fixture.
     - ``wyrdcraeft/etc/morphology/wright-morphology-fixture.schema.json``
     - morphology
     - Describes the local fixture shape rather than a runtime input command
       reads directly.
     - high
   * - ``data/sources/wright.md``
     - Checked-in Wright markdown source used only by the explicit ingest
       command.
     - ``data/sources/wright.md``
     - morphology, lexicon
     - Optional source for populating ``wright_sections.section_text``.
     - high for current use; lower for OCR history not re-proven here

Sink Matrix
-----------

.. list-table::
   :header-rows: 1
   :widths: 22 17 18 18 25

   * - Artifact or table family written
     - Producing command
     - Main code writer
     - Consuming command or UI
     - Downstream role
   * - ``bt_entries``, ``bt_senses``, ``bt_variants``, ``bt_edit_log``
     - ``wyrdcraeft dictionary build``
     - ``BTIndexPipeline`` via ``BTSqliteSink``
     - ``wyrdcraeft dictionary lookup``, ``wyrdcraeft lexicon build``
     - Canonical dictionary index plus editorial audit trail.
   * - ``forms``
     - ``wyrdcraeft morphology build``
     - ``SqliteIndexSink``
     - ``wyrdcraeft morphology query``, ``wyrdcraeft lexicon build``
     - Canonical generated morphology form store.
   * - morph catalog tables
     - ``wyrdcraeft morphology build``
     - ``MorphologyCatalogLoader``
     - ``MorphologyCatalogQueryService``, lexicon browse
     - Wright-backed reference catalog for class lookup.
   * - ``lemma_morph_classes``
     - ``wyrdcraeft morphology build``
     - ``LemmaMorphClassAssigner``
     - ``MorphologyCatalogQueryService``, lexicon browse
     - Lemma-to-class assignments keyed by normalized title and POS.
   * - ``wright_sections.section_text``
     - ``wyrdcraeft morphology ingest-wright-text``
     - ``WrightSectionTextIngester``
     - lexicon browse Wright modal
     - Optional stored Wright paragraph text.
   * - ``search_keys``, ``search_build_meta``
     - ``wyrdcraeft lexicon build``
     - ``rebuild_lexicon()`` via ``LexiconBuilder``
     - ``wyrdcraeft lexicon browse``
     - Derived search index over dictionary plus morphology; browse reads
       ``bt_*`` and ``forms`` directly at query time.

Reading Guide
-------------

- Start with :doc:`dictionary` if you want to see how Bosworth-Toller source
  becomes structured lexical data.
- Start with :doc:`morphology` if you want to see how lemma data becomes
  generated inflected forms and Wright-backed class metadata.
- Start with :doc:`lexicon` if you want to see how browse/search is rebuilt
  from the already-built dictionary and morphology layers.
