CHANGELOG
=========

Unreleased
----------

Enhancements
^^^^^^^^^^^^

- ``wyrdcraeft source mark-diacritics`` now only adds diacritics and never alters the source text: ``ð``/``þ``, case and hyphenation are kept as written, existing marks are never removed, the ``c`` of ``sc`` is never dotted, and ``g`` before a back vowel stays velar. Tokens whose macron-index form cannot be aligned to the source are left unchanged and written to a new ``--unaligned-output`` report.
- ``wyrdcraeft source mark-diacritics`` now applies marks to an ambiguous macron-index key whose options agree on their marks, and has a new ``--ambiguity-policy auto|leave|union`` option (default ``auto``) for keys whose options differ. A token written by ``auto`` or ``union`` stays in the ambiguity report with the form that was written (``applied_form``) and the policy, and the command prints how many tokens were guessed. A key completed with ``diacritic-disambiguate`` is never guessed.
- ``wyrdcraeft source mark-diacritics`` spells the prefixes and compound elements listed in ``wyrdcraeft/etc/diacritic/standard_elements.txt`` (``a-``, ``for-``, ``ge-`` and so on) the same way in every index form, so BT's mark variants of them no longer make a key ambiguous. The list is hand-edited.
- ``wyrdcraeft diacritic add`` and ``wyrdcraeft diacritic-disambiguate`` warn and ask before storing a form that does not normalize to its key. ``diacritic-disambiguate`` also skips keys whose options already agree on their marks.
- Added ``wyrdcraeft diacritic import-variants``, which adds the variant spellings in Bosworth-Toller entries to the macron index as entries of their own. It is a dry run unless ``--apply`` is given, never changes an existing key, filters out citation sigla, fragments, all-caps text and over-frequent variants, accepts dialect and scribal spellings close to the headword, and writes a JSON review report of collisions, conflicting keys and variants left out.
- The Bosworth-Toller display normalizer now also moves the macron of ``io`` diphthongs to the first vowel (``fiōnd`` becomes ``fīond``).
- The packaged macron index now includes the Bosworth-Toller variant spellings imported with ``diacritic import-variants``.
- ``wyrdcraeft dictionary browse`` no longer depends on SQLAlchemy, and the dictionary query index checks now live in the service layer instead of the CLI.

Bugfixes
^^^^^^^^

- ``wyrdcraeft diacritic disambiguate`` action ``m`` now marks a truly ambiguous
  key completed without requiring POS/meaning annotations first, so it stays out
  of the default review queue.
- ``wyrdcraeft source mark-diacritics`` now reads the ``g`` exceptions from ``wyrdcraeft/etc/diacritic/g/frontal.txt`` instead of a hardcoded list, so edits to that file take effect.
- ``wyrdcraeft source mark-diacritics`` no longer double-marks a diphthong that the source already marks in Bosworth-Toller's style (``leāst`` stayed ``leāst`` instead of becoming ``lēāst``).
- ``wyrdcraeft source mark-diacritics`` no longer splits decomposed (NFD) text into fragments, no longer replaces a source token with an unrelated word: the macron index builder now gives each variant its own entry instead of mapping it to the first headword, and the packaged macron index was pruned and extended accordingly, and no longer lowercases mixed-case tokens.
- ``wyrdcraeft settings create`` now writes valid TOML (it previously wrote JSON into the ``.toml`` file), and omits the readonly ``app_name`` and ``app_version`` settings.
- Fixed the global settings path on Unix-like systems, which contained unrendered template text instead of ``/etc/wyrdcraeft.toml``.

Refactorings
^^^^^^^^^^^^

- Moved ingest code into ``wyrdcraeft.services``.
- Moved the verb generators out of ``generation/common.py`` into their own modules.

Documentation
^^^^^^^^^^^^^

- Recorded ADRs 0011 (verb generator module split) and 0012 (generation is not bound to Perl parity).

1.2.0 (2026-09-01)
------------------

Breaking changes
^^^^^^^^^^^^^^^^

- Removed all LLM support: ``wyrdcraeft source convert`` no longer accepts ``--use-llm`` or other LLM flags, and the LLM fix pass in the dictionary pipeline is gone. The ``unstructured``, ``langextract`` and ``any-llm-sdk`` dependencies were dropped.
- ``wyrdcraeft source convert`` no longer accepts HTTP sources or HTML/PDF input; only local text files are supported.
- Removed the OCR pipeline (the ``ocr`` command group, the ``olmocr`` and ``ocrmypdf`` dependencies, and the unused OCR settings). OCR work now lives in the separate ``bochord`` project.
- Removed the ``lexicon`` command group. Use ``wyrdcraeft dictionary browse`` and ``wyrdcraeft dictionary build`` instead.
- The database-producing commands were renamed to ``build``. Persistence is now a single canonical ``wyrdcraeft.sqlite3`` database whose schema is managed by Alembic migrations; the legacy ``forms`` string columns were replaced by foreign keys to reference tables.

Enhancements
^^^^^^^^^^^^

- Added ``wyrdcraeft dictionary build``, a unified build that indexes the Bosworth-Toller dictionary, relinks ``forms.entry_id`` and optionally regenerates morphology.
- Rebuilt the Bosworth-Toller dictionary parser with source blocks and richer sense parsing, and improved etymology parsing.
- Added ``wyrdcraeft dictionary query`` and ``wyrdcraeft dictionary browse``, with morphology tables for verbs and adjectives, the catalog morphological class, and the Wright section text in the detail pane.
- Added ``wyrdcraeft dictionary clean-headwords`` to lowercase all-uppercase ``oe_bt`` headwords.
- Added ``wyrdcraeft morphology clean-dictionary`` to normalize the bundled TSV dictionary (diphthongs, column casing), with a backup.
- Added ``wyrdcraeft dictionary audit-wright`` and ``wyrdcraeft dictionary ingest-wright-text`` for auditing and ingesting Wright & Wright grammar data.
- Added ``wyrdcraeft dictionary generate-reference-snapshots`` for canonical Python-reference morphology snapshots.
- The morphology build now seeds a Wright morphological class catalog and assigns a class to each lemma.
- Added progress reporting to morphology generation, and sped up the build by batching SQLite writes and trimming adjective hot paths.
- Added a ``normalized_title`` column for joining morphology and dictionary data.
- Added Old English lessons.

Bugfixes
^^^^^^^^

- Made the OE key buttons in the browse TUI readable.
- Fixed the form foreign-key resolver mapping of morphological class IDs.
- Fixed cross-test contamination so the full test suite runs cleanly.

Refactorings
^^^^^^^^^^^^

- Reorganized morphology generation into class-based generators (noun, adjective, adverb, numeral, strong and weak verb) behind a ``MorphologyGenerationFacade``, replacing ``GeneratorSession`` with ``WordPool`` and ``GenerationRunState``, and removing the old dispatch and wrapper modules (ADR 0009).
- Moved persistence for the morphology, dictionary and lexicon data to SQLAlchemy Core.

Data changes
^^^^^^^^^^^^

- Added Wright & Wright section fixtures and a term to the morphology inputs.

1.1.0 (2026-03-02)
------------------

Breaking changes
^^^^^^^^^^^^^^^^

- Removed the top-level ``convert`` command. Use ``wyrdcraeft source convert`` instead.

Enhancements
^^^^^^^^^^^^

- ``wyrdcraeft diacritic disambiguate`` command now shows more candidate forms and more rows in the Bosworth-Toller assist table.
- ``wyrdcraeft diacritic add``: allow adding or overwriting a unique entry in the macron index.
- ``wyrdcraeft diacritic delete``: allow deleting a unique entry from the macron index.
- ``wyrdcraeft source mark-diacritics`` now outputs a new ``.unknown.txt`` file listing words that were not found in the macron index.
- ``wyrdcraeft source mark-diacritics`` now uses filename defaults based on the input filename instead of requiring explicit output paths to be provided.
- Updated the Tichý morphological generator code to use macrons instead of acutes, to match how the rest of the project handles diacritics.

Refactorings
^^^^^^^^^^^^

- Refactored the CLI code to be more organized and easier to maintain.
- Moved all ``@dataclass`` and ``pydantic`` models to the ``wyrdcraeft.models`` module.

Data changes
^^^^^^^^^^^^

- Disambiguated some more ambiguous entries in the macron index.

1.0.0 (2026-03-01)
------------------

Enhancements
^^^^^^^^^^^^

- Initial release.
