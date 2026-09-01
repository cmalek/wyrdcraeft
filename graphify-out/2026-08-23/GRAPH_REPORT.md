# Graph Report - wyrdcraeft  (2026-08-03)

## Corpus Check
- 367 files · ~5,540,329 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5788 nodes · 12089 edges · 298 communities (258 shown, 40 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 864 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `33d143d0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .write_json
- BTSenseSegmenter
- models/__init__.py
- PartOfSpeech
- morphology/test_query_service.py
- ParadigmClassMapper
- ParsedBTLine
- WordPool
- form_decode.py
- GenerationRunState
- strong_principal_flow.py
- common.py
- browse_tui.py
- processors.py
- VerbFormGenerator
- test_generation_branches.py
- attestation_stripper.py
- Settings
- weak_inflections.py
- generate_vbforms
- test_browse_tui.py
- DictionaryBrowseQueryService
- strong_inflections.py
- generate_and_print_form
- test_markup.py
- tests/conftest.py
- weak_derivation_flow.py
- cli/dictionary.py
- cli.py
- test_bosworthtoller.py
- ensure_parts_of_speech
- OldEnglishText
- ingest/pipeline.py
- Word
- MorphologyCatalogLoader
- adj_forms.py
- strong_derivation_flow.py
- etymology_display.py
- weak_principal_flow.py
- SenseMetadataClassifier
- test_cli_morphology.py
- .ensure_ready
- TextMetadata
- SenseTreeNormalizer
- MorphologyRow
- read_jsonl_gz
- NormalizedTitleJoinIndex
- normalize_morphology_title
- wright-morphology-fixture.schema.json
- test_cli_diacritic_disambiguate.py
- test_pipeline_classes.py
- markup.py
- morphology/loaders.py
- create_progress
- Session: Morphology Wright Catalog — Phase 2 complete
- test_morph_class_browse.py
- properties
- properties
- create_engine
- test_morph_catalog_pos.py
- cli
- SourceLoader
- AnyLLMConfig
- check_napoleon_gate.py
- Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅
- write_backup_state
- BTSqliteSink
- test_line_parser.py
- PHONOLOGY
- browse_query.py
- LLMDocumentIngestor
- BrowseSearchHit
- GeneratorSession
- test_text_utils_reference.py
- test_wright_audit.py
- BTPos
- enum
- MorphologyDictionaryCleaner
- test_form_fk_resolver.py
- .palatalize
- source.py
- BT V2 Parser And Schema Migration
- properties
- BTSourceHeadwordCleaner
- Phase 3 — Forms Link, Query, and Lexicon Surfacing
- Orchestration Guide
- Execution order
- Orchestration Guide
- type
- Orchestration Guide
- Lexicon Architecture Docs Design
- .load_from_tei
- test_wright_section_text.py
- .parse
- required
- features
- BTAttestationStripper
- test_generation_package_imports.py
- Configuration: Command Line Tool guide
- DatabaseStartupRuntime
- 20260706_01_parts_of_speech_and_dictionary_pos.py
- TestCLIVersion
- OESyllableBreaker
- DictionaryBrowseApp
- wyrdcraeft dictionary browse
- TestCLIGlobalOptions
- properties
- session.py
- Lexicon shrink: drop lexicon_entries/lexicon_forms, keep search_keys
- sound_dispatch_flow.py
- catalog_db
- normalize_old_english
- _run_database_readiness_gate
- clean_dictionary
- Implementation Slices
- fixture_prose.txt (Mark gospel OE prose fixture)
- GeneratorSession.load_all
- wyrdcraeft 1.1.0 release (2026-03-02)
- default_bt_source_path
- build_runner.py
- Batched SQLite sink (25K rows) + bulk PRAGMAs fix for morphology build perf
- Phase 2 — Lemma Morph Class Assignment
- main
- Morphology Wright catalog — Phase 1 session (2026-07-04)
- .apply
- TestCLIErrorHandling
- .infer_missing_pos
- TestConsoleQuietMode
- TestCLISettings
- DocumentIngestor
- OldEnglishSearchInput
- enum
- BTIndexPipeline
- examples
- enum
- enum
- Morphology Generation Package Import-Cycle Fix Implementation Plan
- .settings_customise_sources
- Pipeline Changes
- enum
- enum
- test_paths.py
- test_sense_segmenter.py
- Dictionary build/browse flow (concept)
- Wyrdcraeft Canonical DB Migration Implementation Plan
- Architecture review — 2026-08-01
- test_prompt_regression.py
- wyrdcraeft/settings.py
- test_corpus_sample.py
- DatabaseMigrationError
- source_keys
- .__init__
- enum
- enum
- enum
- parent_id
- FormEmitter
- Task 1: Define Build Event Models
- wright_sections
- TestConsole
- Session State: Lexicon SQLAlchemy Slice 1 Complete
- BT Dictionary Structuring Workflow runbook
- enum
- .generate_all_forms
- sense_metadata.py
- wyrdcraeft Context
- sqlalchemy.py
- test_schema.py
- generation/query.py
- test_lemma_morph_assignment.py
- query
- BTSense
- decode_function_dimensions
- File Structure
- 20260707_02_bt_senses_entry_order_index.py
- test_normalized_title_join.py
- runtime.py
- seeded_lexicon_db
- .resolve_sense_path
- Phase A — Reference Tables and Dictionary POS FKs
- MorphologyCatalogQueryService
- Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns
- create_dict31.pl (legacy Perl morphology generator)
- BTQueryService
- Python coding standards
- OENormalizer
- BT Structural Visibility Review
- wyrdcraeft
- ._no_mixed_prose_and_verse
- Phase D — Drop Legacy Form String Columns
- ._resolve_class_key
- Phase A — Unified Dictionary Build
- Napoleon documentation quality gate
- OESyllableBreaker
- tests/dictionary/__init__.py
- lexicon/__init__.py
- tests/morphology/__init__.py
- alembic/__init__.py
- versions/__init__.py
- Morphology Context
- Phase 3 — Browse Wright § text pane
- Target Data Model
- CPalatalizer
- OENormalizer
- wyrdcraeft.models.llm
- wyrdcraeft.models.parsing
- SqliteIndexSink
- .__init__
- .segment_with_warnings
- Global Constraints
- Lexicon Browser BT V2 Adaptation Skeleton
- Orchestration: Wyrdcraeft Canonical DB Migration
- Morph Class Browse And Audit Design
- generation/num_forms.py
- Phase B — Forms Foreign Keys (Legacy Strings Remain)
- 0002-normalized-canonical-schema.md
- Phase 2 — Wright § Text Ingest Report
- 0007-ocr-pipeline-moves-to-bochord.md
- Two-gate subagent workflow: Gate A spec review, Gate B code review
- TestPrintError
- AGENTS.md
- Contributor Covenant 3.0
- isolated_morphology_app_data pytest fixture (no writes to real app-data DB)
- refactor_baseline.json Perl-parity guardrail for morphology generation
- Phase 1 — Reference Catalog Tables
- Unified dictionary build pipeline replacing morphology/dictionary/lexicon build triangle
- Morph Class Browse Surfacing + Wright Audit — Implementation Plan
- test_dict.txt (BT morphology dictionary test fixture)
- create_settings
- base.py
- PHONOLOGY
- CONTEXT.md
- Diacritic Context
- Dictionary Context
- Ingest Context
- Settings Context
- Orchestrator Checkpoint
- Phase 1 — Browse morph-class detail block
- Phase 2 — Wright § text ingest
- Phase 4 — Legacy Wright audit command
- test_session_composition.py
- Orchestrator Checkpoint
- test_cli_convert.py
- .__init__
- TestPrintSuccess
- TestPrintInfo
- Domain Docs
- normalized_title + lexicon browse — checkpoint 2026-07-03T12:15
- Mission: Machine Assistance For Old English Work
- Mission: Historical Linguistics for Old English Study
- CHAPTER IV: THE OLD ENGLISH DEVELOPMENT OF THE PRIM. GERMANIC VOWELS OF ACCENTED SYLLABLES {#chapter-4}
- A. The Short Vowels of Accented Syllables
- Wright & Wright (1908), "Old English Grammar", Oxford University Press
- Lemma-level morph class assignment (normalized_title, pos) -> morph_classes
- Issue tracker: Trello
- Subagent task breakdown
- Subagent task breakdown
- Subagent task breakdown
- normalized_title — checkpoint 2026-07-03T12:10
- Machine Assistance For Old English Work Resources
- Historical Linguistics for Old English Study Resources
- CHAPTER V: THE PRIM. GERMANIC EQUIVALENTS OF THE OE. VOWELS OF ACCENTED SYLLABLES {#chapter-5}
- B. THE LONG VOWELS OF ACCENTED SYLLABLES
- Old English c/g Palatalization Rule System
- filter_display_variants
- CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}
- CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}
- infer_bt_pos_from_wordclasses
- .emit_form_data
- release.sh
- 0002-canonical-morphology-db-uses-startup-alembic-migrations.md
- _format_entry_text
- triage-labels.md
- scripts/__init__.py
- quality/__init__.py
- 0002-ocr-learning-goal.md
- machine-assistance/NOTES.md
- 0001-starting-point.md
- oe-grammar/NOTES.md
- teaching/README.md
- ipa-play.js
- THIRD_PARTY_NOTICES.md
- version
- wyrdcraeft
- .__init__
- .resolve_morph_class_id
- .resolve_wordclass_id

## God Nodes (most connected - your core abstractions)
1. `Word` - 168 edges
2. `cli()` - 107 edges
3. `GeneratorSession` - 100 edges
4. `BTSenseSegmenter` - 86 edges
5. `GenerationRunState` - 81 edges
6. `Settings` - 74 edges
7. `VerbFormGenerator` - 69 edges
8. `ParsedBTLine` - 67 edges
9. `BTLineParser` - 65 edges
10. `create_engine()` - 58 edges

## Surprising Connections (you probably didn't know these)
- `Solomon and Saturn dialogue test fixture` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_dialogue.txt → doc/source/overview/format.rst
- `Beowulf opening lines test fixture (poetry)` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_poetry.txt → doc/source/overview/format.rst
- `test_morphology_group_help()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_morphology.py → wyrdcraeft/cli/cli.py
- `test_morphology_wright_commands_moved_to_dictionary()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_morphology.py → wyrdcraeft/cli/cli.py
- `test_morphology_build_command_moved_to_dictionary()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_morphology.py → wyrdcraeft/cli/cli.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Subagent task reports implementing Wright catalog browse/ingest/audit phases** — doc_sessions_task_phase1_morph_class_browse_report, doc_sessions_task_phase2_wright_text_ingest_report, doc_sessions_task_phase3_wright_text_pane_report, doc_sessions_task_phase4_wright_audit_report [INFERRED 0.85]
- **Dictionary build pipeline stage sequence** — doc_source_architecture_dictionary_btlineparser, doc_source_architecture_dictionary_btsensesegmenter, doc_source_architecture_dictionary_bteditorialmerger, doc_source_architecture_dictionary_btsqlitesink, doc_source_architecture_dictionary_formsentryrelinker [EXTRACTED 1.00]
- **Morphology build stage-ordering (catalog seed, class assign, form emission)** — doc_source_architecture_morphology_generatorsession, doc_source_architecture_morphology_morphologycatalogloader, doc_source_architecture_morphology_lemmamorphclassassigner, doc_source_architecture_morphology_sqliteindexsink [EXTRACTED 1.00]
- **wyrdcraeft CLI configuration documentation cluster** — doc_source_overview_configuration_cli_configuration_guide, doc_source_overview_using_cli_cli_usage_guide, doc_source_overview_command_settings_settings_command [INFERRED 0.75]
- **Bosworth-Toller dictionary processing pipeline (source, runbooks, fixture)** — doc_source_runbook_bt_dictionary_structuring_workflow_bt_structuring_workflow, doc_source_runbook_macron_list_generation_macron_list_generation, tests_fixtures_dictionary_corpus_sample_bt_corpus_sample_fixture [INFERRED 0.75]
- **Morphological Paradigm Generation Data Set** — wyrdcraeft_etc_morphology_dict_adj_vb_part_num_adv_noun, wyrdcraeft_etc_morphology_manual_forms, wyrdcraeft_etc_morphology_para_vb [INFERRED 0.75]
- **Prose Prompt Layering (general -> base mode -> model override)** — wyrdcraeft_prompts_general, wyrdcraeft_prompts_prose, wyrdcraeft_prompts_models_gemini_prose [INFERRED 0.85]
- **c/g Palatalization Exception Lists** — wyrdcraeft_etc_diacritic_c_palatalization_force_non_palatalize, wyrdcraeft_etc_diacritic_c_palatalization_force_palatalize, wyrdcraeft_etc_diacritic_g_frontal [INFERRED 0.85]

## Communities (298 total, 40 thin omitted)

### Community 0 - ".write_json"
Cohesion: 0.40
Nodes (3): Path, Write the report as formatted JSON to disk. Args: report_path: Destination JSON…, Serialize the report to a JSON-friendly mapping. Returns: Dictionary suitable…

### Community 1 - "BTSenseSegmenter"
Cohesion: 0.07
Nodes (21): Unit tests for specific segmenter behaviours., Body with no sense labels produces a single unlabelled sense., Bold <B>I.</B>/<B>II.</B> labels produce two ordered senses., <B>I</B>. (period outside bold tag) is recognised as a sense label., Plain (unbolded) Roman-numeral labels followed by an italic span are split…, Three bold sense labels I., II., III. all produce senses in order., <B>II a.</B> sub-letter label is captured and stripped of period., <B>A.</B> / <B>B.</B> capital-letter labels are supported. (+13 more)

### Community 2 - "models/__init__.py"
Cohesion: 0.05
Nodes (82): AnyDictionaryBuildEvent, DictionaryBuildEventSink, DictionaryBuildLogLevel, DictionaryBuildStatus, Event, build_pipeline_db(), _fetch_entry_id(), _fetch_entry_pos() (+74 more)

### Community 3 - "PartOfSpeech"
Cohesion: 0.06
Nodes (70): DeclarativeBase, _make_word(), query_service(), Tests for read-only Wright catalog lemma class lookup., test_format_morph_class_display_label_falls_back_to_canonical_name(), test_format_morph_class_display_label_prefers_compact_modern_label(), test_lookup_missing_lemma_returns_none(), test_lookup_normalizes_title_before_query() (+62 more)

### Community 4 - "morphology/test_query_service.py"
Cohesion: 0.04
Nodes (81): Write minimal ``forms`` rows into a morphology SQLite database. Args: db_path:…, seed_forms(), _form_row(), _index_dictionary(), _insert_bt_entry(), _insert_bt_variant(), Connection, Path (+73 more)

### Community 5 - "ParadigmClassMapper"
Cohesion: 0.07
Nodes (31): mapper(), fixture, Tests for Wright catalog paradigm exemplar mapping., test_adj_paradigm_blind_maps_to_strong_a_o_stem(), test_noun_paradigm_guma_maps_to_weak_n_stem(), test_noun_paradigm_stan_maps_to_masculine_a_stem(), test_past_participle_title_maps_to_past_participle_class(), test_present_participle_title_maps_to_present_participle_class() (+23 more)

### Community 6 - "ParsedBTLine"
Cohesion: 0.03
Nodes (91): _entry_to_dict(), main(), _parse_and_segment(), Parse and segment one raw BT line., Convert a BTConsolidatedEntry to a serialisable dict., _entry_to_comparable(), _load_golden(), merger() (+83 more)

### Community 7 - "WordPool"
Cohesion: 0.03
Nodes (69): test_build_profiler_disabled_emits_nothing(), test_build_profiler_emits_stage_and_sqlite_sections(), test_progress_coordinator_omits_empty_wright_and_throttles_lemma(), test_progress_coordinator_stage_totals(), MorphologyBuildProfiler, TextIO, Wall-clock profiling helpers for morphology build runs., Finish wall-clock timing for one generation stage. Args: stage: Stage being… (+61 more)

### Community 8 - "form_decode.py"
Cohesion: 0.06
Nodes (69): MorphologyTableInputRow, Tests for morphology function-code decoding., test_build_adjective_sidebar_uses_payload_inflection(), test_build_adverb_sidebar_decodes_superlative_su_code(), test_build_morphology_table_fills_inflection_from_morph_class_label(), test_build_morphology_table_includes_surface_form_column(), test_build_morphology_table_sorts_adjectives_by_degree_inflection_and_case(), test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms() (+61 more)

### Community 9 - "GenerationRunState"
Cohesion: 0.06
Nodes (78): _build_stem_ar_pl(), _build_stem_ar_sg_ge_da(), _build_stem_ar_sg_no_ac(), _build_stem_daeg_pl(), _build_stem_geminate(), _build_stem_hof_ge_da(), _build_stem_pl_ge_da(), _build_stem_pl_no_ac() (+70 more)

### Community 10 - "strong_principal_flow.py"
Cohesion: 0.07
Nodes (35): StrongInfDerivationEmitter, StrongPrincipalFormAction, StrongPrincipalInfDerivationAction, StrongPrincipalParticipleAction, Immutable context for strong principal-part callback bindings. Args: formhash:…, _StrongPrincipalPartContext, Emit one strong principal-part row for a selected active vowel. Side Effects:…, Attach a past participle emitted from a strong principal-part row. Side… (+27 more)

### Community 11 - "common.py"
Cohesion: 0.06
Nodes (60): PartDispatcher, PartProcessor, PartStemSegmentDeriver, StrongPartGenerator, VariantDispatcher, VariantProcessor, WeakPartGenerator, GeneratedForm (+52 more)

### Community 12 - "browse_tui.py"
Cohesion: 0.07
Nodes (46): test_format_entry_details_omits_plain_wright_line_for_selectable_sections(), test_format_entry_details_shows_unclassified_for_missing_assignment(), test_format_entry_details_shows_unclassified_for_unmappable_pos(), DictionaryBrowseStartupStage, StrEnum, Browse startup progress helpers for dictionary browse workflow., Stable stage labels for dictionary browse startup progress., Run browse startup work while showing stable stderr progress stages. Args:… (+38 more)

### Community 13 - "processors.py"
Cohesion: 0.14
Nodes (21): Morphology paradigm assigners., _assign_verb_by_advanced_diacritics(), _assign_verb_by_advanced_stem(), _assign_verb_by_diacritics(), _assign_verb_by_example(), _assign_verb_by_stem(), _assign_verb_by_wright(), _assign_verb_fallback() (+13 more)

### Community 14 - "VerbFormGenerator"
Cohesion: 0.03
Nodes (37): Emit one manual row from a pre-bound weak ``PaInSg1`` context. Side Effects:…, Emit one weak ``PsInSg2``-branch form row with simplified post-vowel. Side…, Emit one weak ``PsInSg2`` sound-change branch with simplified post-vowel. Side…, Generator for Old English verb forms. Args: word_pool: Categorized word pool…, Matches Perl's generate_strong_verb_parts. Notes: Matches Perl implementation…, Generate strong verbs derived from inf. Notes: Matches Perl implementation of…, Matches Perl's generate_and_print_form_with_sound_changes. Notes: Matches Perl…, Matches Perl's generate_and_print_manual. Args: formhash: The form hash. form:… (+29 more)

### Community 15 - "test_generation_branches.py"
Cohesion: 0.07
Nodes (53): SoundManualEmitter, SoundSourceFormEmitter, _base_formhash(), _make_part(), _make_variant(), _make_verb_paradigm(), _make_word(), test_add_participle_to_adjectives_helper_appends_past_participle() (+45 more)

### Community 16 - "attestation_stripper.py"
Cohesion: 0.08
Nodes (30): fixture, parametrize, Tests for Phase 03 BTAttestationStripper., ``_is_citation_span`` returns True for grammar/editorial markers and citations., ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes., ``_strip_editorial_directive`` removes leading supplement editorial verbs., Unit tests for module-level helper functions., ``_is_grammatical_abbrev`` distinguishes grammar markers from glosses. (+22 more)

### Community 17 - "Settings"
Cohesion: 0.07
Nodes (25): Exception, patch, Test that model_config is properly configured., Test output format validation., Test valid output format validation., Test settings loading from environment variables. This test is a placeholder…, Test that environment variables override defaults., Test cases for configuration settings. (+17 more)

### Community 18 - "weak_inflections.py"
Cohesion: 0.04
Nodes (65): test_dispatch_weak_derived_forms_selects_psinsg2_branch(), test_dispatch_weak_derived_forms_skips_item_shape_mode(), test_dispatch_weak_principal_part_derivations_emits_papt_only(), test_emit_weak_derived_from_inf_by_class2_general_branch(), test_emit_weak_derived_from_inf_by_class2_two_uses_general_path(), test_emit_weak_derived_from_inf_sequence_normalizes_none_probability(), test_emit_weak_derived_from_painsg1_sequence_uses_preterite_order(), test_emit_weak_derived_from_painsg1_variant_sequence() (+57 more)

### Community 19 - "generate_vbforms"
Cohesion: 0.12
Nodes (53): _runtime_baseline_ms(), _stage_rows(), full_flow_rows(), Generate canonicalized full-flow rows for parity assertions. Args: session:…, canonicalize_form_rows(), parse_form_output(), Canonicalize form rows for stable snapshot storage., Parse generator TSV output into normalized records. The unstable ``counter``… (+45 more)

### Community 20 - "test_browse_tui.py"
Cohesion: 0.09
Nodes (65): anyio, _bt_entry_id(), _collect_widget_ids(), _details_text(), empty_browse_db(), _insert_entry(), _insert_inflection_code(), _pos_id() (+57 more)

### Community 21 - "DictionaryBrowseQueryService"
Cohesion: 0.13
Nodes (29): _bt_entry_id(), _insert_bt_sense(), _insert_entry(), _insert_inflection_code(), _next_entry_order(), _pos_id(), Connection, Path (+21 more)

### Community 22 - "strong_inflections.py"
Cohesion: 0.08
Nodes (33): StrongBranchAction, StrongDerivedEmitter, StrongFormEmitter, StrongParticipleSink, StrongSoundEmitter, test_dispatch_strong_derived_from_principal_part_routes_painsg1(), test_dispatch_strong_verb_part_branches_painpl(), test_dispatch_strong_verb_part_branches_papt_only() (+25 more)

### Community 23 - "generate_and_print_form"
Cohesion: 0.10
Nodes (23): assemble_form_parts(), materialize_form(), perl_interpolate(), Form assembly helpers for parity-preserving morphology generation., Assemble a raw ``formParts`` payload using legacy Perl field ordering. Side…, Coerce a scalar to a Perl-like interpolation string. Side Effects: None. Args:…, Normalize assembled form parts into the emitted ``form`` and ``formParts``.…, emit_form_for_context() (+15 more)

### Community 24 - "test_markup.py"
Cohesion: 0.07
Nodes (41): Path, test_build_index_from_bt_extracts_and_dedupes(), Path, C before i/ī in any position palatalizes (Rule C)., Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)., gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar., Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc., Cyning (c + y from u) remains non-palatalized; blocklist and only-back. (+33 more)

### Community 25 - "tests/conftest.py"
Cohesion: 0.09
Nodes (32): Popen, cli_context(), ensure_llama_server(), _is_llama_server_healthy(), isolated_morphology_app_data(), isolated_morphology_index_db(), lexicon_source_db(), mock_console() (+24 more)

### Community 26 - "weak_derivation_flow.py"
Cohesion: 0.05
Nodes (49): WeakInfFormEmitter, WeakPainsg1ContextFormEmitter, WeakPsinsg2DerivationFormContextEmitter, WeakPsinsg2DerivationSoundContextEmitter, Immutable context for weak infinitive-derived emitter callbacks. Args:…, Immutable context for weak ``PaInSg1``-derived emitter callbacks. Args:…, Immutable context for weak ``PsInSg2``-derived emitter callbacks. Args:…, _WeakInfDerivationContext (+41 more)

### Community 27 - "cli/dictionary.py"
Cohesion: 0.12
Nodes (25): clean_headwords(), _count_table_rows(), _default_morphology_data_dir(), _default_source_path(), dictionary_group(), generate_reference_snapshots_command(), _missing_canonical_index_message(), group (+17 more)

### Community 28 - "cli.py"
Cohesion: 0.06
Nodes (52): Layout, Tests for CLI commands with low coverage., Test that Settings has no ocr_ fields., test_settings_has_no_ocr_fields(), Tests for CLI utilities., diacritic_add(), diacritic_delete(), diacritic_group() (+44 more)

### Community 29 - "test_bosworthtoller.py"
Cohesion: 0.15
Nodes (24): test_fetch_bt_search_entries_uses_search_endpoint(), test_filter_bt_entries_by_normalized_form_empty_list_returns_empty(), test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others(), test_filter_bt_entries_by_normalized_form_no_matches_returns_empty(), test_filter_bt_entries_by_normalized_form_preserves_order(), test_merge_bt_entries_deduplicates_and_reindexes(), test_normalize_bt_spelling_converts_acute_to_macron(), test_parse_bt_search_entries_extracts_fields() (+16 more)

### Community 30 - "ensure_parts_of_speech"
Cohesion: 0.11
Nodes (30): _load_fixture_rows(), Connection, Path, Tests for normalized POS and inflection-code seed fixtures., Read one JSON fixture file used by the POS seed tests., Return the current row count for one reference table., _row_count(), test_inflection_seed_covers_observed_snapshot_function_codes() (+22 more)

### Community 31 - "OldEnglishText"
Cohesion: 0.08
Nodes (43): fixture, sample_doc(), test_tei_export_attributes(), test_tei_export_basic(), test_tei_export_structure(), test_tei_exporter_interface(), Test importing Beowulf from TEI XML., test_tei_import_beowulf() (+35 more)

### Community 32 - "ingest/pipeline.py"
Cohesion: 0.06
Nodes (41): object, test_canonical_converter_prose(), test_canonical_converter_verse(), test_structure_parser_prose(), test_structure_parser_verse(), patch, TestLLMDocumentIngestor, test_mixed_mode_splitting() (+33 more)

### Community 33 - "Word"
Cohesion: 0.07
Nodes (48): Lexical entry schema carrying POS flags and paradigm state for one lemma., Word, _append_short_syllable_front_vowel_heuristic(), _append_suffix_heuristics(), _append_terminal_a_heuristic(), _append_terminal_e_heuristic(), _apply_final_fallback(), _apply_noun_heuristics() (+40 more)

### Community 34 - "MorphologyCatalogLoader"
Cohesion: 0.07
Nodes (33): Path, Build a small morphology slice and verify normalized FK columns on forms., test_catalog_loader_ensure_seeded_refresh(), test_catalog_loader_ensure_seeded_skips_when_populated(), test_catalog_loader_is_idempotent(), test_catalog_loader_populates_recognition_hints_json(), test_catalog_loader_refresh_replaces_stale_rows(), test_catalog_loader_rejects_missing_morph_class_fields() (+25 more)

### Community 35 - "adj_forms.py"
Cohesion: 0.08
Nodes (52): _adj_print(), _build_adjective_formhash(), _build_comparative_title_array(), _build_superlative_title_array(), _build_weak_title_array(), _dedupe_preserve_first(), _emit_superlative_strong_forms(), _emit_weak_degree_forms() (+44 more)

### Community 36 - "strong_derivation_flow.py"
Cohesion: 0.06
Nodes (42): StrongDerivedInfFormAction, StrongDerivedInfImsgAction, StrongDerivedInfParticipleAction, StrongDerivedInfSoundAction, StrongInfDerivationRouter, Immutable context for strong infinitive-derived emitter callbacks. Args:…, _StrongInfDerivationContext, Emit one strong infinitive-derived row for a selected active vowel. Side… (+34 more)

### Community 37 - "etymology_display.py"
Cohesion: 0.07
Nodes (51): Tests for etymology parsing and browse table formatting., test_format_etymology_display_renders_table_headers(), test_misplaced_attestation_is_flagged(), test_mixed_attestation_and_cognates_split(), test_parse_cognate_chain_with_citation(), test_parse_colon_separated_lang_chain(), test_parse_multiple_german_cognates(), test_parse_norse_words_with_latin_tail() (+43 more)

### Community 38 - "weak_principal_flow.py"
Cohesion: 0.06
Nodes (57): WeakInfBranchGenerator, WeakPainsg1BranchGenerator, WeakPrincipalContextAction, WeakPrincipalFormEmitter, WeakPrincipalParticipleAction, WeakPsinsg2BranchGenerator, Immutable context for weak principal-part callback bindings. Args: formhash:…, _WeakPrincipalPartContext (+49 more)

### Community 39 - "SenseMetadataClassifier"
Cohesion: 0.10
Nodes (12): Unit tests for sense-prefix metadata classification., TestSenseMetadataClassifier, Classify sense-level prefix debris into structured metadata. Extracts…, Classify prefix metadata for one sense-body fragment. Args: text: Raw HTML…, Remove leading hyphenated variant spellings before sense prefix spans. Args:…, Remove leading paradigm inflection markers such as ``an;`` or ``es;``. Args:…, Remove leading weak-noun paradigm fragments such as ``-færes;``. Args: text:…, Remove phrase-example tails that follow an ``in the phrase`` usage note. Args:… (+4 more)

### Community 40 - "test_cli_morphology.py"
Cohesion: 0.20
Nodes (9): CLI tests for remaining morphology commands after build moved to dictionary., test_morphology_build_command_moved_to_dictionary(), test_morphology_clean_dictionary_help(), test_morphology_generate_command_is_gone(), test_morphology_group_help(), test_morphology_query_help(), test_morphology_query_requires_exactly_one_lookup_mode(), test_morphology_wright_commands_moved_to_dictionary() (+1 more)

### Community 41 - ".ensure_ready"
Cohesion: 0.11
Nodes (12): ensure_database_ready(), _format_backup_prompt_text(), Ensure the canonical SQLite database is ready for one CLI invocation. Keyword…, Run the startup database decision tree once. Raises: DatabaseMigrationError:…, Create one retained backup and update the canonical sidecar state. Args:…, Apply Alembic migrations and emit the locked success narration. Side Effects:…, Run the Alembic bootstrap and upgrade path. Side Effects: Creates the SQLite…, Read the current Alembic revision from the canonical database. Returns: Current… (+4 more)

### Community 42 - "TextMetadata"
Cohesion: 0.11
Nodes (26): ProgressCallback, parametrize, Test that deterministic ingestion of text files matches the golden JSON…, test_deterministic_ingestion_regression(), patch, BaseDocumentIngestor, HeuristicDocumentIngestor, ingest_auto() (+18 more)

### Community 43 - "SenseTreeNormalizer"
Cohesion: 0.09
Nodes (26): Unit tests for canonical sense-path normalization., TestSenseTreeNormalizer, BTSegmentResult, _normalise_label(), Phase 03 sense segmenter for Bosworth-Toller line bodies., Find all sense-boundary positions in *body*, returning ``(label, pos)`` pairs.…, Split a body field into ordered raw sense fragments. Args: body: Raw HTML body…, Segmented senses plus diagnostics emitted during one body parse. Attributes:… (+18 more)

### Community 44 - "MorphologyRow"
Cohesion: 0.06
Nodes (35): test_morphology_row_matches_entry_pos_filters_participle_for_noun(), _dominant_paradigm(), filter_display_variants(), _group_morphology_rows(), _json_string_list(), MorphologyRow, Any, RowMapping (+27 more)

### Community 45 - "read_jsonl_gz"
Cohesion: 0.12
Nodes (26): morphology, morphology_full, assert_snapshot_parity(), Path, Assert full-flow parity against a canonical snapshot file. Args: session:…, canonical_sort_rows(), Any, Path (+18 more)

### Community 46 - "NormalizedTitleJoinIndex"
Cohesion: 0.08
Nodes (23): _fetch_rows(), load_normalized_title_join_index(), Connection, Fetch three-column join rows from SQLAlchemy or SQLite connections. Args:…, Build a dictionary join index from canonical ``bt_entries`` and variants. Args:…, NormalizedTitleJoinIndex, Return distinct entry ids in stable ascending order. Args: entry_ids: Candidate…, In-memory resolver for macron-preserving ``normalized_title`` dictionary joins.… (+15 more)

### Community 47 - "normalize_morphology_title"
Cohesion: 0.05
Nodes (50): normalize_morphology_title(), Normalize a morphology lemma title while preserving macrons and dot letters.…, _append_sample_block(), _catalog_pos_from_word(), ContradictionIssue, _display_legacy_wright(), _format_blank_but_classified_issue(), _format_contradiction_issue() (+42 more)

### Community 48 - "wright-morphology-fixture.schema.json"
Cohesion: 0.05
Nodes (39): 1.0, morph_classes, Old English, schema_version, sources, wright-modern-morphology, additionalProperties, description (+31 more)

### Community 49 - "test_cli_diacritic_disambiguate.py"
Cohesion: 0.10
Nodes (39): _minimal_index_payload(), _mock_bt_lookup(), fixture, Path, Minimal macron index payload for diacritic add/delete tests., test_diacritic_add_fails_when_exists_without_force(), test_diacritic_add_fails_when_key_in_ambiguous_even_with_force(), test_diacritic_add_force_overwrites() (+31 more)

### Community 50 - "test_pipeline_classes.py"
Cohesion: 0.16
Nodes (14): dialogue_text(), prose_text(), fixture, patch, _t(), test_document_ingestor_dispatch(), test_llm_document_ingestor(), test_oe_filter() (+6 more)

### Community 51 - "markup.py"
Cohesion: 0.10
Nodes (30): patch, With only input given, paths default to stem + infix + extension., test_source_mark_diacritics_default_paths(), test_source_mark_diacritics_writes_text_and_ambiguities(), test_source_mark_diacritics_writes_unknowns_file(), AmbiguityOption, DiacriticRestorationResult, MacronAmbiguity (+22 more)

### Community 52 - "morphology/loaders.py"
Cohesion: 0.15
Nodes (14): ManualForm, Manual form model for ``manual_forms.txt`` ingest rows. Legacy string fields…, load_dictionary(), load_forms(), load_paradigms(), load_prefixes(), Load the paradigms from a file. Args: path: The path to the paradigms file.…, Load the dictionary from a file. Args: path: The path to the dictionary file.… (+6 more)

### Community 53 - "create_progress"
Cohesion: 0.13
Nodes (13): Progress, Test progress creation., Test progress creation returns a Progress object., Test progress has spinner column., Test progress has text column., TestCreateProgress, create_progress(), create_stderr_console() (+5 more)

### Community 54 - "Session: Morphology Wright Catalog — Phase 2 complete"
Cohesion: 0.15
Nodes (7): Architecture, Deliverables, Known limitations (deferred), Next, Session: Morphology Wright Catalog — Phase 2 complete, Summary, Validation

### Community 55 - "test_morph_class_browse.py"
Cohesion: 0.35
Nodes (10): _bt_entry_id(), _insert_bt_entry(), Path, Tests for catalog-backed morph-class metadata in lexicon browse details., Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions., Seed one catalog assignment row into a temporary lexicon test database., Insert one minimal ``bt_entries`` row into a temporary lexicon test database.…, _seed_catalog_assignment() (+2 more)

### Community 56 - "properties"
Cohesion: 0.06
Nodes (34): type, type, type, properties, type, type, type, type (+26 more)

### Community 57 - "properties"
Cohesion: 0.06
Nodes (34): description, minLength, type, $ref, default, description, enum, type (+26 more)

### Community 58 - "create_engine"
Cohesion: 0.15
Nodes (27): _fetch_form_entry_id(), _insert_bt_entry(), _insert_bt_variant(), _insert_form(), _pos_id(), Connection, fixture, Path (+19 more)

### Community 59 - "test_morph_catalog_pos.py"
Cohesion: 0.12
Nodes (30): parametrize, Tests for morphology catalog POS normalization helpers., test_catalog_pos_from_bt_pos_cli_aliases(), test_catalog_pos_from_bt_pos_join_values(), test_catalog_pos_from_bt_pos_raises_for_unmapped(), test_catalog_pos_from_wordclass(), test_catalog_pos_from_wordclass_unknown_returns_none(), test_pos_id_from_bt_pos() (+22 more)

### Community 60 - "cli"
Cohesion: 0.12
Nodes (38): Test that the OCR command group has been removed from the CLI., test_ocr_command_group_removed(), _build_unified_source_db(), _fetch_entry_id(), _fetch_form_entry_id(), _insert_form(), _morphology_data_dir(), _pos_id() (+30 more)

### Community 61 - "SourceLoader"
Cohesion: 0.10
Nodes (22): Element, fixture, source_loader(), test_load_from_file_text(), test_load_from_file_unsupported(), test_tei_source_loader_load_tei(), BaseSourceLoader, FileSourceLoader (+14 more)

### Community 62 - "AnyLLMConfig"
Cohesion: 0.08
Nodes (19): llm, TestLLMExtractor, _j(), parametrize, Test that the live Qwen regression matches the golden regression. Args:…, _t(), test_goldens_are_schema_valid(), test_live_qwen_matches_golden() (+11 more)

### Community 63 - "check_napoleon_gate.py"
Cohesion: 0.08
Nodes (44): AST, AsyncFunctionDef, ClassDef, FunctionDef, Module, cyclomatic(), report(), _check_file() (+36 more)

### Community 64 - "Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅"
Cohesion: 0.07
Nodes (29): Background, Explicit non-goals, File Map, Lexicon rebuild (Slice 1), Lexicon SQLAlchemy Rebuild + Normalized Title Join Index Implementation Plan, Locked Decisions, Normalized title join index (Slice 2), References (+21 more)

### Community 65 - "write_backup_state"
Cohesion: 0.09
Nodes (32): Path, test_backup_state_round_trip_uses_sidecar_beside_canonical_db(), test_create_backup_copies_database_and_keeps_latest_by_default(), test_restore_backup_overwrites_database_contents(), create_backup(), list_backups(), _prune_old_backups(), datetime (+24 more)

### Community 66 - "BTSqliteSink"
Cohesion: 0.06
Nodes (55): Row, slow, lexicon_source_db(), fixture, Dictionary-only canonical DB fixture for browse-query tests., lexicon_source_db(), Dictionary-backed canonical DB fixture for browse TUI tests., _fetch_entry() (+47 more)

### Community 67 - "test_line_parser.py"
Cohesion: 0.08
Nodes (24): parametrize, Tests for Phase 02 Bosworth-Toller line parser., Skipped lines return explicit reasons needed by downstream reporting., Substitute target extraction captures ``for X in Dict`` phrases., Variant and noun-gender extraction uses pre-POS prefix conventions., Parser emits display headwords with Wright-style diphthong long marks., Trailing bracket blocks are preserved for later etymology handling., Deletion references are parsed from text after the ``Dele`` marker. (+16 more)

### Community 68 - "PHONOLOGY"
Cohesion: 0.07
Nodes (28): 1. UMLAUT, 2. Breaking, 3. Influence of Nasals, 4. Influence of Initial Palatal Consonants, 5. Influence of w, a, A. The Short Vowels of Accented Syllables, A. THE VOWELS. (+20 more)

### Community 69 - "browse_query.py"
Cohesion: 0.09
Nodes (29): _append_unique(), _best_hit(), _browse_hit_sort_key(), EntrySense, _extract_gender_person_number(), _hit_lexical_distance(), lexical_distance(), _normalize_query() (+21 more)

### Community 70 - "LLMDocumentIngestor"
Cohesion: 0.09
Nodes (16): Unmarked verse gets 1-based line numbers within the section., test_canonical_converter_verse_number_fallback(), fixture, CanonicalConverter, LLMDocumentIngestor, Converts pre-parsed documents into canonical OldEnglishText models., Extract a structural number marker from the start of a string. Args: text: The…, Split a paragraph of text into sentences, handling terminal punctuation inside… (+8 more)

### Community 71 - "BrowseSearchHit"
Cohesion: 0.08
Nodes (23): ComposeResult, ListItem, Pressed, Static, BrowseSearchHit, One deduplicated dictionary-entry search result row. Attributes: entry_id:…, _format_main_result_label(), _MainResultItem (+15 more)

### Community 72 - "GeneratorSession"
Cohesion: 0.05
Nodes (55): setter, _make_verb_paradigm(), _make_word(), test_set_adj_paradigm_stem_propagation(), test_set_adj_paradigm_wright_rule_425(), test_set_noun_paradigm_advanced_stem_propagation(), test_set_noun_paradigm_final_fallback_neuter_long_stem(), test_set_noun_paradigm_final_fallback_neuter_short_stem() (+47 more)

### Community 73 - "test_text_utils_reference.py"
Cohesion: 0.28
Nodes (12): parametrize, test_canonicalize_inflection_code_reference(), test_eth2thorn_reference(), test_iumlaut_reference(), test_move_accents_reference(), test_normalize_bt_display_spelling_is_idempotent(), test_normalize_bt_display_spelling_reference(), test_normalize_output_reference() (+4 more)

### Community 74 - "test_wright_audit.py"
Cohesion: 0.16
Nodes (24): _dictionary_line(), _make_audit_source_dir(), _manual_form_line(), _para_vb_line(), Path, Tests for legacy Wright source auditing. Phase D source contract: The audit…, Build one ``manual_forms.txt`` fixture line with the expected 16 columns., Build one ``para_vb.txt`` fixture line for malformed-token scanning. (+16 more)

### Community 75 - "BTPos"
Cohesion: 0.03
Nodes (111): Client, parametrize, Tests for BT display spelling normalization., Normalize representative real BT headword spellings from ``oe_bt.txt``., Normalizing an already-normalized spelling is a no-op., test_bt_spelling_normalizer_matches_oe_normalizer(), test_normalize_is_idempotent(), test_normalize_real_bt_diphthong_cases() (+103 more)

### Community 76 - "enum"
Cohesion: 0.08
Nodes (26): common, comparative, dual, feminine, first, masculine, neuter, plural (+18 more)

### Community 77 - "MorphologyDictionaryCleaner"
Cohesion: 0.10
Nodes (20): parametrize, Tests for morphology dictionary TSV cleanup., test_clean_dictionary_fixes_bt_diphthongs_in_col2(), test_clean_dictionary_lowercases_col2_dedupes_and_backups(), test_clean_dictionary_raises_when_source_missing(), test_should_lowercase_col2_only_all_upper_letters(), morphology_group(), group (+12 more)

### Community 78 - "test_form_fk_resolver.py"
Cohesion: 0.20
Nodes (23): _insert_bt_entry(), _insert_bt_variant(), _insert_lemma_assignment(), Connection, fixture, Path, Tests for morphology form foreign-key resolution., resolver_db() (+15 more)

### Community 79 - ".palatalize"
Cohesion: 0.17
Nodes (7): _possible_pre_iumlaut_sources(), Palatalize ``g`` in a lexical token. Args: word: Token to palatalize. Returns:…, Return possible pre-i-mutation (reconstructed) sources for an OE vowel. Used to…, Test if ``text[index:]`` starts with a front-vowel context. Args: text:…, Return whether the character before position i is i/ī or i/ī + n. Used for Rule…, Return True if the vowel unambiguously derives only from back vowels. Used to…, Palatalize ``c`` in a lexical token per rules A-D and i-mutation caveat. Rule…

### Community 80 - "source.py"
Cohesion: 0.19
Nodes (15): _mark_diacritics_derived_path(), argument, command, Context, group, option, pass_context, Path (+7 more)

### Community 81 - "BT V2 Parser And Schema Migration"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT V2 Parser And Schema Migration, CLI Output Contract, Context, Dependencies, Follow-on Work, Locked Decisions, Problem Classes BT V2 Must Fix (+4 more)

### Community 82 - "properties"
Cohesion: 0.08
Nodes (25): oldenglish_info, stella, wright_1914, description, minLength, type, default, description (+17 more)

### Community 83 - "BTSourceHeadwordCleaner"
Cohesion: 0.12
Nodes (18): parametrize, Tests for Bosworth-Toller oe_bt.txt headword cleanup., test_clean_headwords_leaves_later_bold_tags_unchanged(), test_clean_headwords_lowercases_first_bold_and_backups(), test_clean_headwords_raises_when_source_missing(), test_should_lowercase_headword_only_all_upper_letters(), BTSourceHeadwordCleaner, BTSourceHeadwordCleanupResult (+10 more)

### Community 84 - "Phase 3 — Forms Link, Query, and Lexicon Surfacing"
Cohesion: 0.20
Nodes (10): Future (post Phase 3), Phase 3 — Forms Link, Query, and Lexicon Surfacing, Phase 3 — Gate A: Spec review, Phase 3 — Gate B: Code review, Phase 3 validation, Task 1: Schema migration, Task 2: Sink propagation, Task 3: Query service (+2 more)

### Community 85 - "Orchestration Guide"
Cohesion: 0.07
Nodes (26): 10. Failure handling, 11. Phase briefs, 12. Definition of done, 1. Architecture, 2. Locked decisions, 3. Files, 4. Phase order, 5. Orchestrator workflow (+18 more)

### Community 86 - "Execution order"
Cohesion: 0.05
Nodes (34): BT entry identity follows source blocks, BT Dictionary Parser Rebuild Implementation Plan, Commit strategy, Domain/runtime models, Execution handoff, Execution order, File map, Live corpus findings to design against (+26 more)

### Community 87 - "Orchestration Guide"
Cohesion: 0.08
Nodes (25): 10. Failure handling, 11. Subagent dispatch prompt, 12. Definition of done, 13. New session kickoff, 1. Architecture, 2. Files, 3. Phase order, 4. Orchestrator workflow (+17 more)

### Community 88 - "type"
Cohesion: 0.10
Nodes (23): default, description, items, type, items, items, items, minLength (+15 more)

### Community 89 - "Orchestration Guide"
Cohesion: 0.08
Nodes (25): 10. Failure handling, 11. Phase briefs, 12. Definition of done, 1. Architecture, 2. Locked decisions, 3. Files, 4. Phase order, 5. Orchestrator workflow (+17 more)

### Community 90 - "Lexicon Architecture Docs Design"
Cohesion: 0.08
Nodes (25): 1. As built in `wyrdcraeft`, 1. Orient the reader, 2. Show shared system flow, 2. Upstream provenance, 3. Optional or non-critical behavior, 3. Show provenance matrix, 4. Show sink matrix, Acceptance Criteria (+17 more)

### Community 91 - ".load_from_tei"
Cohesion: 0.24
Nodes (6): Document, TeiReader, Load a TEI XML document. Args: source: The source to load the document from.…, Import TEI XML using delb and acdh-tei-pyutils. Args: tei_xml: The TEI XML to…, Extract metadata from TEI header. Args: tei_reader: The TEI reader to extract…, Parse the TEI body. Args: doc: The document to parse the body from. ns: The…

### Community 92 - "test_wright_section_text.py"
Cohesion: 0.08
Nodes (33): catalog_db(), fixture, Path, Tests for Wright section markdown parsing and catalog text ingest., test_ingest_result_counts_and_warnings(), test_ingester_force_overwrites_existing_text(), test_ingester_is_idempotent_without_force(), test_ingester_updates_null_sections() (+25 more)

### Community 93 - ".parse"
Cohesion: 0.11
Nodes (12): Parse one source line into ``RawBTLine`` plus phase-02 metadata. Args:…, Extract the POS prefix fragment immediately after the first headword. Args:…, Extract alternate headword spellings from the pre-POS plain-text prefix. Args:…, Apply display spelling normalization to variants with de-duplication. Args:…, Extract substitute target text from ``for X in Dict`` patterns. Args: body:…, Extract reference fragments listed after ``Dele`` markers. Args: body: Main…, Extract trailing bracket etymology blocks from the line body. Args: body: Main…, Build a skipped parse result with the provided reason. Args: reason: Human-… (+4 more)

### Community 95 - "required"
Cohesion: 0.11
Nodes (19): aliases, canonical_name, features, id, is_assignable, mapping_rationale, modern_class, paradigmatic_words (+11 more)

### Community 96 - "features"
Cohesion: 0.11
Nodes (19): citation_apa, retrieved_date, source_key, url, $defs, features, recognitionHints, source (+11 more)

### Community 97 - "BTAttestationStripper"
Cohesion: 0.09
Nodes (18): Unit tests for BTAttestationStripper.strip., ``:--`` is the canonical attestation separator., Combined gender-gloss italic spans like ``<I>f. An oak:</I>`` yield clean…, ``</I>--`` (colon inside italic) is handled as the attestation separator., Grammar markers like ``<I>p.</I>`` and ``<I>pp.</I>`` are removed from the…, ``[…]`` bracket blocks are stripped before gloss extraction., An ``<I>Add:</I>`` span with no following gloss produces an empty string., ``Substitute:`` editorial prefix is removed from the kept gloss span. (+10 more)

### Community 98 - "test_generation_package_imports.py"
Cohesion: 0.25
Nodes (7): Regression test for the generation-package import-cycle fix.…, The package must not carry a facade re-export that recreates the cycle., The only import path any real caller uses must keep working., dispatch.py is the actual production entrypoint into the facade., test_dispatch_still_importable(), test_facade_still_importable_directly(), test_generation_package_does_not_reexport_facade()

### Community 99 - "Configuration: Command Line Tool guide"
Cohesion: 0.15
Nodes (18): wyrdcraeft settings CLI command doc, wyrdcraeft source convert CLI command doc, Configuration: Command Line Tool guide, wyrdcraeft FAQ, Standard JSON Representation for Old English Texts (schema spec), Installation guide, Quickstart guide, Using the Command Line Interface guide (+10 more)

### Community 100 - "DatabaseStartupRuntime"
Cohesion: 0.24
Nodes (21): _create_pre_alembic_forms_db(), _make_settings(), MonkeyPatch, parametrize, Path, test_child_help_skips_database_gate(), test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(), test_fresh_missing_db_bootstraps_with_alembic_path() (+13 more)

### Community 101 - "20260706_01_parts_of_speech_and_dictionary_pos.py"
Cohesion: 0.16
Nodes (23): _assert_no_null_pos_ids(), _assert_no_null_text_pos(), downgrade(), _downgrade_bt_entries(), _downgrade_lemma_morph_classes(), _downgrade_morph_classes(), Connection, Replace legacy BT text POS and headword columns with normalized fields. Args:… (+15 more)

### Community 102 - "TestCLIVersion"
Cohesion: 0.25
Nodes (5): Test the version command., Test the version command displays version information., Test the version command with verbose flag., Test the version command with quiet flag., TestCLIVersion

### Community 103 - "OESyllableBreaker"
Cohesion: 0.16
Nodes (9): Syllable model for Old English syllable breaking., A syllable is a unit of speech that consists of an onset, nucleus, and coda., Syllable, OESyllableBreaker, Split consonant cluster between syllables using a conservative max-onset…, Insert dots before known suffixes to guide syllabification., Syllabify an Old English word conservatively., Break an Old English word into syllables. (+1 more)

### Community 104 - "DictionaryBrowseApp"
Cohesion: 0.10
Nodes (17): Changed, Selected, Submitted, DictionaryBrowseApp, Normalize search input text so dead-key combining marks become OE glyphs. Args:…, Run browse search when the user submits the search box. Args: event: Textual…, Show details for a selected search result or Wright section. Args: event:…, Execute search and refresh browse panes from query results. Args: query: Raw… (+9 more)

### Community 105 - "wyrdcraeft dictionary browse"
Cohesion: 0.23
Nodes (13): normalize_old_english(), BTSpellingNormalizer, DictionaryBrowseApp (Textual TUI), DictionaryBrowseQueryService, 12-tier headword/variant search ranking ladder, wyrdcraeft dictionary browse, wyrdcraeft dictionary build, parse_warnings.jsonl (+5 more)

### Community 106 - "TestCLIGlobalOptions"
Cohesion: 0.12
Nodes (9): Test JSON output format., Test text output format., Test invalid output format., Test global CLI options., Test verbose flag is properly set., Test quiet flag is properly set., Quiet mode should reset on next non-quiet CLI invocation., Test default output format is table. (+1 more)

### Community 107 - "properties"
Cohesion: 0.12
Nodes (16): type, uniqueItems, type, uniqueItems, type, uniqueItems, type, closed_class_examples (+8 more)

### Community 108 - "session.py"
Cohesion: 0.08
Nodes (29): FixtureRequest, Namespace, main(), _mypy_baseline(), _sha256_rows(), _build_output_sink(), main(), _parse_args() (+21 more)

### Community 110 - "sound_dispatch_flow.py"
Cohesion: 0.20
Nodes (14): SoundChangeSequenceEmitter, SoundManualContextEmitter, SoundSourceContextEmitter, Immutable context for sound-change callback dispatch. Args: formhash: Shared…, _SoundChangeDispatchContext, emit_manual_sound_changed_context(), emit_sound_changed_form_for_context(), emit_source_form_with_sound_context() (+6 more)

### Community 111 - "catalog_db"
Cohesion: 0.29
Nodes (6): catalog_db(), fixture, Path, test_from_db_path_uses_isolated_database(), Path, Build a query service from one canonical SQLite database path. Args: db_path:…

### Community 112 - "normalize_old_english"
Cohesion: 0.06
Nodes (53): corpus_index_db(), _index_fixture(), fixture, Path, Unit and integration tests for BTQueryService., sample_index_db(), _seed_forms_table(), test_bt_senses_round_trip_rich_fields() (+45 more)

### Community 113 - "_run_database_readiness_gate"
Cohesion: 0.22
Nodes (8): _prompt_backup_cleanup(), Context, Run the canonical DB startup gate once for DB-using command trees. Args: ctx:…, Click group that preserves the raw argv for help-aware gate decisions. Side…, Persist the raw argv before delegating to Click's normal parser. Args: ctx:…, Read one backup-cleanup confirmation without forcing a re-prompt. Args: text:…, _RootCLIGroup, _run_database_readiness_gate()

### Community 114 - "clean_dictionary"
Cohesion: 0.24
Nodes (11): clean_dictionary(), _default_morphology_data_dir(), _format_dictionary_join_text(), command, option, Path, query(), Query morphology rows by lemma or surface form. Note: Query keys are normalized… (+3 more)

### Community 115 - "Implementation Slices"
Cohesion: 0.33
Nodes (6): Implementation Slices, Slice 1: consume visibility review, Slice 2: models and schema, Slice 3: parser and merge, Slice 4: query and CLI, Slice 5: rebuild and verify

### Community 117 - "GeneratorSession.load_all"
Cohesion: 0.17
Nodes (12): GeneratorSession (services.morphology), wyrdcraeft.models.morphology, GeneratorSession, LemmaMorphClassAssigner, MorphologyCatalogLoader, Morphology generation flow (concept), GeneratorSession.load_all(), LemmaMorphClassAssigner.assign_all() (+4 more)

### Community 118 - "wyrdcraeft 1.1.0 release (2026-03-02)"
Cohesion: 0.22
Nodes (13): GPalatalizer, MacronApplicator, wyrdcraeft.models.macron_index, wyrdcraeft 1.0.0 initial release (2026-03-01), wyrdcraeft 1.1.0 release (2026-03-02), wyrdcraeft source mark-diacritics, Diacritic restoration runtime processing flow, wyrdcraeft diacritic add (+5 more)

### Community 119 - "default_bt_source_path"
Cohesion: 0.09
Nodes (26): CorpusSampleResult, DictionaryCorpusSampler, main(), Path, Index source lines by lookup key while preserving source line order. Returns:…, Sample keys by deterministic every-Nth stratification. Args: ordered_keys: Keys…, Result of one corpus-sample build run. Attributes: keys: Selected lookup keys…, Collect all editorial siblings for sampled keys in corpus order. Args:… (+18 more)

### Community 120 - "build_runner.py"
Cohesion: 0.12
Nodes (26): _apply_limit(), _current_stage_total(), _default_morphology_data_dir(), MorphologyBuildRunnerError, Connection, Path, RuntimeError, Service entrypoint for morphology generation builds. (+18 more)

### Community 122 - "Phase 2 — Lemma Morph Class Assignment"
Cohesion: 0.20
Nodes (10): Cleanup (optional same PR or follow-up), Phase 2 — Gate A: Spec review, Phase 2 — Gate B: Code review, Phase 2 — Lemma Morph Class Assignment, Phase 2 validation, Task 1: Schema + migration, Task 2: POS normalization helper, Task 3: Paradigm exemplar registry (+2 more)

### Community 123 - "main"
Cohesion: 0.23
Nodes (8): patch, Tests for the main module., Test the main function., Test that main function calls the CLI., Test that main function can be imported and called., Test that main function exists and is callable., TestMain, main()

### Community 124 - "Morphology Wright catalog — Phase 1 session (2026-07-04)"
Cohesion: 0.12
Nodes (17): 1. Circular import on full morphology test collection, 2. Untracked plan directory, 3. Package data, Branch and commits, Build integration, Commits this session (Phase 1 Tasks 1–4), Goal (locked design), Key files (+9 more)

### Community 125 - ".apply"
Cohesion: 0.50
Nodes (3): TContext_contra, TWord_contra, Return matched paradigm labels for ``word`` in ``context``. Note: Paradigm…

### Community 126 - "TestCLIErrorHandling"
Cohesion: 0.33
Nodes (4): Test CLI error handling., Test CLI without arguments shows help., Test invalid command shows error., TestCLIErrorHandling

### Community 127 - ".infer_missing_pos"
Cohesion: 0.23
Nodes (10): PosInferenceCancelCheck, PosInferenceProgress, PosInferenceWarningSink, Connection, Attempt one inferred POS update, skipping duplicate and homograph rows. Args:…, Unwrap one SQLAlchemy connection to the underlying SQLite driver. Args:…, Resolve the seeded ``unknown`` part-of-speech identifier. Args: connection:…, Update unknown dictionary POS rows from morphology forms when unambiguous.… (+2 more)

### Community 128 - "TestConsoleQuietMode"
Cohesion: 0.33
Nodes (4): Test console quiet mode functionality., Test that console can be set to quiet mode., Test that stderr console can be set to quiet mode., TestConsoleQuietMode

### Community 129 - "TestCLISettings"
Cohesion: 0.17
Nodes (7): Test the settings command., Test the settings command with table output., Test the settings command with JSON output., Test the settings command with text output., Test the settings command with verbose flag., Test the settings command with custom config file., TestCLISettings

### Community 130 - "DocumentIngestor"
Cohesion: 0.22
Nodes (9): DocumentIngestor, HeuristicDocumentIngestor, LLMDocumentIngestor, TEIDocumentIngestor, wyrdcraeft.models.source_text (OldEnglishText JSON schema), Germanic Lexicon Project (Bosworth-Toller OCR source), github:madeleineth/tichy_oe_generator, Tichý, Morphological analyser of old english (2017) (+1 more)

### Community 131 - "OldEnglishSearchInput"
Cohesion: 0.18
Nodes (8): Input, Key, Paste, OldEnglishSearchInput, Accept Old English keyboard characters at app level as a terminal fallback.…, Search input that accepts OE key aliases and paste-driven compose paths., Accept OE key aliases before Textual's default printable-key handling. Args:…, Normalize pasted text so terminal compose/paste paths keep OE glyphs. Args:…

### Community 132 - "enum"
Cohesion: 0.18
Nodes (11): ablaut, adjectival_declension, adverbial_formation, declension, dental_suffix, lexeme_specific, preterite_present, pronominal_declension (+3 more)

### Community 133 - "BTIndexPipeline"
Cohesion: 0.20
Nodes (10): BTEditorialMerger, BTIndexPipeline, BTLineParser, BTLLMFixPass, BTSenseSegmenter, BTSourceBlockBuilder, BTSqliteSink, DictionaryBuildPipeline (+2 more)

### Community 134 - "examples"
Cohesion: 0.20
Nodes (10): adj.strong.a_o_stem, adv.deadjectival_e, noun.masculine.a_stem, pron.personal.first_person, verb.strong_3.nasal_cluster, description, examples, pattern (+2 more)

### Community 135 - "enum"
Cohesion: 0.20
Nodes (10): case_form, deadjectival_e, deadjectival_lice, lexical, linga_lunga, prepositional_phrase, unga_inga, enum (+2 more)

### Community 136 - "enum"
Cohesion: 0.20
Nodes (10): demonstrative, indefinite, interrogative, personal, possessive, reflexive, relative, enum (+2 more)

### Community 137 - "Morphology Generation Package Import-Cycle Fix Implementation Plan"
Cohesion: 0.40
Nodes (4): File Structure, Global Constraints, Morphology Generation Package Import-Cycle Fix Implementation Plan, Task 1: Remove the dead facade re-export from `generation/__init__.py`

### Community 138 - ".settings_customise_sources"
Cohesion: 0.18
Nodes (7): BaseSettings, PydanticBaseSettingsSource, Path, Return the default local settings file path used by the CLI. Returns: The…, Load settings from file with cascading configuration. Args: config_file:…, Get list of configuration file paths that were loaded. Use this for debugging.…, Resolve the canonical SQLite database path for these settings. Returns:…

### Community 139 - "Pipeline Changes"
Cohesion: 0.40
Nodes (5): 1. Parsing and segmentation, 2. Attestation stripping, 3. Editorial merge, 4. Lowercased display spellings, Pipeline Changes

### Community 140 - "enum"
Cohesion: 0.22
Nodes (9): adjective, adverb, noun, pronoun, verb, description, enum, type (+1 more)

### Community 141 - "enum"
Cohesion: 0.22
Nodes (9): adverbial_or_prepositional_origin, irregular_or_suppletive, irregular_or_umlauted, regular, suppletive, umlauted, enum, type (+1 more)

### Community 142 - "test_paths.py"
Cohesion: 0.16
Nodes (21): parametrize, Path, test_get_app_data_path_platform_defaults(), test_get_app_data_path_settings_override(), test_get_app_data_path_unsupported_platform(), test_get_canonical_db_path_creates_parent(), test_isolated_morphology_index_db_uses_canonical_filename(), test_resolve_db_path_explicit_dir_mkdirs_target() (+13 more)

### Community 143 - "test_sense_segmenter.py"
Cohesion: 0.12
Nodes (16): _golden_sense_matches(), _load_golden(), BTSense, fixture, Tests for Phase 03 BTSenseSegmenter., Unit tests for sense-level gender promotion (Task 5 deferral hook)., Golden-file acceptance tests: ≥95% exact gloss match required., At least 95 % of golden entries must match exactly on sense count and gloss… (+8 more)

### Community 144 - "Dictionary build/browse flow (concept)"
Cohesion: 0.50
Nodes (4): Dictionary build/browse flow (concept), Alembic head 20260707_01 (normalized-schema Phases A-D), Canonical Database ER Diagram (wyrdcraeft.sqlite3), Lexicon architecture (superseded, search_keys removed)

### Community 145 - "Wyrdcraeft Canonical DB Migration Implementation Plan"
Cohesion: 0.12
Nodes (15): Completion Checklist, File Map, Locked Decisions, Native Codex Execution Notes, Orchestrator Strategy, Phase 1: Persistence Skeleton and Canonical Path, Phase 2: Alembic Scaffold, Startup Runtime, Backup Sidecar, Phase 3: Initial Declarative Schema and First Migration (+7 more)

### Community 146 - "Architecture review — 2026-08-01"
Cohesion: 0.50
Nodes (3): Architecture review — 2026-08-01, Decision, Status

### Community 147 - "test_prompt_regression.py"
Cohesion: 0.32
Nodes (7): _canonicalize(), parametrize, Prompt regression and schema validation tests. These tests are designed to be…, Deterministic ordering for stable snapshot comparisons., Placeholder regression test. Today: just ensures the expected snapshot is…, test_expected_json_is_schema_valid(), test_snapshot_regression_contract()

### Community 148 - "wyrdcraeft/settings.py"
Cohesion: 0.13
Nodes (11): Unit tests for configuration settings. Tests the new OpenAI and summary…, ConfigurationError, FileError, OejsonextractorError, Raised when file I/O operations fail., Base exception for all wyrdcraeft errors., Raised when settings or configuration fails., Get the API key for the LLM provider. (+3 more)

### Community 149 - "test_corpus_sample.py"
Cohesion: 0.33
Nodes (6): _load_manifest(), Smoke tests for the stratified Bosworth-Toller corpus sample fixture., Ensure corpus fixture is present and within phase-02b size constraints., Parse every corpus line and require deterministic parse or explicit skip., test_corpus_sample_lines_parse_without_raising(), test_corpus_sample_manifest_and_line_count_bounds()

### Community 150 - "DatabaseMigrationError"
Cohesion: 0.15
Nodes (12): Path, test_legacy_bootstrap_failure_restores_cleanly_and_raises_typed_error(), test_legacy_morphology_db_is_backed_up_then_requires_rebuild(), DatabaseMigrationError, LegacyDatabaseResetRequired, datetime, RuntimeError, Legacy database reset stop signal with rebuild guidance. Args: backup_path:… (+4 more)

### Community 151 - "source_keys"
Cohesion: 0.29
Nodes (7): pattern, source_keys, description, items, minItems, type, uniqueItems

### Community 152 - ".__init__"
Cohesion: 0.33
Nodes (6): _db_has_table(), _forms_has_morph_class_id(), Connection, Return whether one SQLite table exists in the active database. Args:…, Return whether the ``forms`` table exposes ``morph_class_id``. Args:…, Initialize a SQLAlchemy query service for a generated morphology index. Note:…

### Community 153 - "enum"
Cohesion: 0.33
Nodes (6): cardinal, ordinal, other, enum, type, numeral_type

### Community 154 - "enum"
Cohesion: 0.33
Nodes (6): distal, proximal, simple, enum, type, deixis

### Community 155 - "enum"
Cohesion: 0.33
Nodes (6): minor, strong, weak, strength, enum, type

### Community 156 - "parent_id"
Cohesion: 0.33
Nodes (6): null, string, description, pattern, type, parent_id

### Community 157 - "FormEmitter"
Cohesion: 0.20
Nodes (8): FormEmitter, ParadigmAssigner, FormOutput, Protocol, Session-level assigner contract., Assign paradigms in-place for session words. Note: Paradigm assignment reflects…, Form emission contract., Emit one normalized form record to ``output``. Note: Form realization follows…

### Community 158 - "Task 1: Define Build Event Models"
Cohesion: 0.13
Nodes (14): Execution Handoff, File Map, Lexicon Build Monitor Implementation Plan, Locked Decisions, Notes for Implementer, Task 1: Define Build Event Models, Task 2: Build Shared Runtime Controller, Task 3: Expand `rebuild_lexicon(...)` Contract for Events and Cancel (+6 more)

### Community 159 - "wright_sections"
Cohesion: 0.33
Nodes (6): minimum, wright_sections, default, description, items, type

### Community 160 - "TestConsole"
Cohesion: 0.50
Nodes (3): Test console objects., Test that console objects are properly initialized., TestConsole

### Community 161 - "Session State: Lexicon SQLAlchemy Slice 1 Complete"
Cohesion: 0.14
Nodes (13): Alembic owns lexicon DDL, Code review notes (Slice 1, not blocking commit), Files changed in Slice 1 commit, Locked decisions (human, this session), Rebuild semantics, References, Session State: Lexicon SQLAlchemy Slice 1 Complete, Slice 1 deliverables (shipped) (+5 more)

### Community 162 - "BT Dictionary Structuring Workflow runbook"
Cohesion: 0.83
Nodes (4): data/oe_bt.txt Bosworth-Toller OCR source file, BT Dictionary Structuring Workflow runbook, Generating the canonical macron list runbook, Bosworth-Toller dictionary corpus sample test fixture

### Community 163 - "enum"
Cohesion: 0.40
Nodes (5): past, present, enum, type, participle

### Community 164 - ".generate_all_forms"
Cohesion: 0.14
Nodes (7): Emit all generated adverb rows for the bound session. Side Effects: Writes rows…, Emit all generated numeral rows for the bound session. Side Effects: Writes…, Emit all generated noun rows for the bound session. Side Effects: Writes rows…, Emit the default full morphology generation flow in stable order. Side Effects:…, Emit curated manual rows before paradigm-driven generation. Side Effects:…, Emit all generated verb rows for the bound session. Side Effects: Writes rows…, Emit all generated adjective rows for the bound session. Side Effects: Writes…

### Community 165 - "sense_metadata.py"
Cohesion: 0.15
Nodes (16): _has_substantive_gloss(), _looks_like_gloss_start(), _normalize_case(), _normalize_gender(), _normalize_modifier(), Sense-level prefix metadata classification for Bosworth-Toller sense bodies., Normalize one modifier abbreviation token. Args: token: Raw modifier token…, Normalize one case abbreviation token. Args: token: Raw case token text.… (+8 more)

### Community 166 - "wyrdcraeft Context"
Cohesion: 0.15
Nodes (13): ADRs, Boundary, Canonical Terms, Capability Map, Context Docs, Current Migration Progress, Dictionary browse, Dictionary indexing (+5 more)

### Community 167 - "sqlalchemy.py"
Cohesion: 0.04
Nodes (46): downgrade(), Drop the initial canonical schema. Side Effects: Removes the initial product…, Create the canonical morphology, dictionary, and lexicon tables. Side Effects:…, upgrade(), downgrade(), Add normalized_title columns to morphology and dictionary source tables. Side…, Remove normalized_title columns and lookup indexes. Side Effects: Drops…, upgrade() (+38 more)

### Community 168 - "test_schema.py"
Cohesion: 0.22
Nodes (18): _forms_column_names(), _fresh_canonical_db(), _index_names(), Connection, parametrize, Path, Tests for lexicon read-model schema helpers., Return the seeded ``unknown`` part-of-speech row id. (+10 more)

### Community 169 - "generation/query.py"
Cohesion: 0.13
Nodes (16): MorphClassQueryMetadata, FK-backed morph-class metadata joined from catalog tables. Note: Linguistic…, Resolve morphology form rows to normalized-schema foreign keys., _build_morph_class_metadata(), dictionary_join_entry_to_dict(), _form_lookup_sql(), _lemma_lookup_sql(), _parse_wright_sections() (+8 more)

### Community 170 - "test_lemma_morph_assignment.py"
Cohesion: 0.24
Nodes (16): assigner(), _assignment(), catalog_db(), _class_key(), _make_verb_paradigm(), _make_word(), fixture, Path (+8 more)

### Community 171 - "query"
Cohesion: 0.24
Nodes (17): audit_wright(), browse(), build(), ingest_wright_text(), lookup(), argument, command, Context (+9 more)

### Community 172 - "BTSense"
Cohesion: 0.15
Nodes (8): Arabic display labels for canonical sense paths., TestSenseDisplayLabels, BTSense, format_sense_display_label(), One English gloss sense for a consolidated dictionary entry. Attributes:…, Backward-compatible sense label derived from ``source_label_raw``. Returns:…, User-facing sense label derived from ``sense_path``. Roman source labels are…, Convert canonical ``sense_path`` to Arabic display text. Top-level paths stay…

### Community 173 - "decode_function_dimensions"
Cohesion: 0.19
Nodes (14): test_decode_noun_plural_neuter_accusative(), test_decode_verb_imperative_plural(), test_decode_verb_inflected_infinitive(), test_decode_verb_pa_in_sg2(), _decode_adjective(), decode_function_dimensions(), _decode_noun_like(), _decode_verb() (+6 more)

### Community 174 - "File Structure"
Cohesion: 0.15
Nodes (12): File Structure, GeneratorSession → WordPool + GenerationRunState Split Implementation Plan, Global Constraints, Task 1: Introduce `WordPool` + `GenerationRunState`, compose `GeneratorSession` from them, Task 2: Migrate the assigners (`noun.py`, `verb.py`, `adj.py`) onto `WordPool`, Task 3: Migrate the shared sink + row-emission leaf layer onto `GenerationRunState`/`WordPool`, Task 4: Migrate `generation/adv_forms.py` (smallest generator — proves the pattern end to end), Task 5: Migrate `generation/num_forms.py` (+4 more)

### Community 175 - "20260707_02_bt_senses_entry_order_index.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add index supporting ordered sense lookup by dictionary entry. Side Effects:…, Remove ordered lookup index for dictionary sense reads. Side Effects: Drops the…, upgrade()

### Community 176 - "test_normalized_title_join.py"
Cohesion: 0.28
Nodes (12): _index(), Unit tests for NormalizedTitleJoinIndex., test_resolve_all_exactly_one_title_across_pos(), test_resolve_all_no_match(), test_resolve_all_pos_direct_multiple_matches(), test_resolve_all_pos_direct_single_match(), test_resolve_all_variant_with_pos_filter(), test_resolve_all_variant_without_pos_filter() (+4 more)

### Community 177 - "runtime.py"
Cohesion: 0.08
Nodes (37): Config, _index_with_attach(), Path, Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite., Seed the canonical ``forms`` table via the real SQLAlchemy sink., _seed_forms_table(), test_attach_missing_db_fails_for_canonical_only_mode(), test_attach_preserves_forms_and_writes_bt_entries() (+29 more)

### Community 178 - "seeded_lexicon_db"
Cohesion: 0.21
Nodes (13): _inflection_code_id(), lexicon_db_connection(), lexicon_db_path(), _noun_pos_id(), Connection, fixture, Path, Temporary SQLite database with canonical source and search-index tables.… (+5 more)

### Community 179 - ".resolve_sense_path"
Cohesion: 0.50
Nodes (3): BTSense, Map one Roman sense label to a canonical ``sense_path``. When the label matches…, Resolve deletion/substitution references to canonical sense paths. Args: refs:…

### Community 180 - "Phase A — Reference Tables and Dictionary POS FKs"
Cohesion: 0.15
Nodes (13): Phase A — Commit, Phase A — Gate A: Spec review checklist, Phase A — Gate B: Code review checklist, Phase A — Reference Tables and Dictionary POS FKs, Phase A validation, Task 1: POS + inflection seed fixtures, Task 2: SQLAlchemy reference models, Task 3: Alembic migration `20260706_01` (+5 more)

### Community 181 - "MorphologyCatalogQueryService"
Cohesion: 0.67
Nodes (3): MorphologyCatalogQueryService, WrightSectionTextIngester (ref), WrightSectionTextIngester

### Community 182 - "Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns"
Cohesion: 0.50
Nodes (4): Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns, Manual Strong-Verb Inflected Forms Table, Adverb Comparison Paradigm Table, Old English Prefix/Preposition Word List

### Community 184 - "create_dict31.pl (legacy Perl morphology generator)"
Cohesion: 1.00
Nodes (3): create_dict31.pl (legacy Perl morphology generator), Morphology Perl Compatibility Quirks Ledger, Wright's paradigms (Old English Grammar, 1908) doc

### Community 185 - "BTQueryService"
Cohesion: 0.67
Nodes (3): wyrdcraeft.models.bosworth_toller, BTQueryService, MorphologyQueryService

### Community 186 - "Python coding standards"
Cohesion: 0.67
Nodes (3): Python coding standards, Contributing guide, Napoleon docstring quality gate (make napoleon-gate)

### Community 187 - "OENormalizer"
Cohesion: 0.13
Nodes (10): Match, Convert one BT spelling to macronized Wright-style display spelling. Pipeline…, OENormalizer, Remove macrons (long-vowel diacritics) from the text. Args: text: The text to…, Convert one BT spelling to macronized Wright-style display spelling. Note:…, Rewrite BT second-vowel long-mark diphthongs to first-vowel long marks. Note:…, Compose one corrected diphthong while preserving source case pattern. Args:…, r""" Perform i-mutation (umlaut) on the vowels. Args: vowels: A list of vowels… (+2 more)

### Community 188 - "BT Structural Visibility Review"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT Structural Visibility Review, Candidate Types To Include, Deliverables, Dependencies, Downstream Use, Locked Decisions, Non-Goals (+4 more)

### Community 189 - "wyrdcraeft"
Cohesion: 0.15
Nodes (12): All other code, Bosworth-Toller Old English Dictionary, Canonical database, Contributing, Contributing, Licensing and Provenance, Documentation, Features, Installation (+4 more)

### Community 191 - "Phase D — Drop Legacy Form String Columns"
Cohesion: 0.15
Nodes (12): Phase D — Commit, Phase D — Drop Legacy Form String Columns, Phase D — Gate A: Spec review checklist, Phase D — Gate B: Code review checklist, Phase D validation, Post-phase checklist (coordinator), Task 1: Alembic migration `20260706_04`, Task 2: Sink + query path cleanup (+4 more)

### Community 192 - "._resolve_class_key"
Cohesion: 0.17
Nodes (6): Resolve one lemma to ``(class_key, assignment_source, confidence)``. Args:…, Resolve ``class_key`` from generator paradigm labels (priority 1). Args: word:…, Resolve ``class_key`` from POS flags and morph-class features (priority 2).…, Score how well one lemma matches one morph-class feature dict. Args: word:…, Resolve ``class_key`` from Wright section intersection (priority 3). Args:…, Extract inflection Wright section numbers from ``Word.wright``. Args: wright:…

### Community 193 - "Phase A — Unified Dictionary Build"
Cohesion: 0.15
Nodes (12): Acceptance criteria (phase), Phase A commit message, Phase A — Gate A checklist, Phase A — Gate B checklist, Phase A — Unified Dictionary Build, Phase A validation, Task 1: `FormsEntryRelinker` service, Task 2: `DictionaryBuildPipeline` orchestrator (+4 more)

### Community 201 - "Morphology Context"
Cohesion: 0.17
Nodes (12): Inputs And Outputs, Invariants And Sharp Edges, Key Files, Legacy Wright Audit (report-only v1), Lexicon Browse Integration, Main CLI Entrypoints, Morphology Context, Primary Python Entrypoints (+4 more)

### Community 202 - "Phase 3 — Browse Wright § text pane"
Cohesion: 0.17
Nodes (12): Acceptance criteria, Exact files likely touched, Gate A — Spec review checklist, Gate B — Code review checklist, Objective, Phase 3 — Browse Wright § text pane, Subagent dispatch packet — Phase 3, Subagent task breakdown (+4 more)

### Community 203 - "Target Data Model"
Cohesion: 0.67
Nodes (3): Entry-level model, Sense-tree model, Target Data Model

### Community 213 - ".segment_with_warnings"
Cohesion: 0.19
Nodes (7): BTSense, Return an ordered list of :class:`~wyrdcraeft.models.dictionary.BTSense` for…, Segment one body and return senses plus segmentation diagnostics. Args: body:…, Segment a body with no explicit sense labels into zero or one senses. Args:…, Build one :class:`~wyrdcraeft.models.dictionary.BTSense` from a fragment. Args:…, Classify prefix metadata and extract one sense gloss from *segment_body*. Args:…, Segment one body for ``ParsedBTLine`` construction. Args: body: Raw HTML body…

### Community 216 - "Global Constraints"
Cohesion: 0.17
Nodes (11): Global Constraints, Remove OCR Pipeline (ADR 0007) Implementation Plan, Task 1: Sever CLI registration of the OCR command group, Task 2: Delete the OCR CLI module and its dedicated tests, Task 3: Delete the OCR proxy service and its tests, Task 4: Delete the OCR pipeline service and its tests, Task 5: Delete `scripts/ocr/` and its `pyproject.toml` entry point, Task 6: Drop OCR-only dependencies and the `ocr_integration` pytest marker (+3 more)

### Community 217 - "Lexicon Browser BT V2 Adaptation Skeleton"
Cohesion: 0.18
Nodes (11): Acceptance Criteria, Browse Changes This Plan Owns, Dependencies, Details-Pane Outcome, Expected BT V2 Inputs, Lexicon Browser BT V2 Adaptation Skeleton, Likely Data-Contract Changes, Locked Decisions (+3 more)

### Community 218 - "Orchestration: Wyrdcraeft Canonical DB Migration"
Cohesion: 0.17
Nodes (11): Completion checklist, Locked decisions (do not re-litigate), Model tiers, Operating modes (mandatory for every subagent), Orchestration: Wyrdcraeft Canonical DB Migration, Per-phase workflow (mandatory), Phase 8 verification commands, Phase order (1 → 8) (+3 more)

### Community 219 - "Morph Class Browse And Audit Design"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, Audit Command, Browse V1, Canonical Model, Current Facts, Locked Decisions, Morph Class Browse And Audit Design, Non-Goals (+4 more)

### Community 220 - "generation/num_forms.py"
Cohesion: 0.22
Nodes (11): _form_from_parts(), generate_numforms(), _num_print(), FormOutput, Numeral form generation. Port of Perl generate_numforms from create_dict31.pl…, Generate numeral forms. Processes words where numeral==1. For noun numerals:…, r""" Remove [0\\-\\n] from form_parts to get form, matching Perl. Args:…, Helper to set form/formParts/function and call print_one_form. Args: run_state:… (+3 more)

### Community 221 - "Phase B — Forms Foreign Keys (Legacy Strings Remain)"
Cohesion: 0.18
Nodes (11): Phase B — Commit, Phase B — Forms Foreign Keys (Legacy Strings Remain), Phase B — Gate A: Spec review checklist, Phase B — Gate B: Code review checklist, Phase B validation, Task 1: Alembic migration `20260706_02`, Task 2: Form FK resolver service, Task 3: Sink propagation (+3 more)

### Community 223 - "Phase 2 — Wright § Text Ingest Report"
Cohesion: 0.14
Nodes (13): Wright § markdown text ingest into wright_sections.section_text, Files changed, Implementation notes, Manual spot-check, Phase 2 — Wright § Text Ingest Report, Self-review, Summary, Task 2.1 — Markdown § parser (+5 more)

### Community 224 - "0007-ocr-pipeline-moves-to-bochord.md"
Cohesion: 0.18
Nodes (7): BT OCR parsing starts with lossless source-grounded AST, BT source acquisition uses a multi-witness download set, BT JP2 witness preparation is library-first, Consequence, Not removed, OCR pipeline moves to bochord, Removed from wyrdcraeft

### Community 226 - "TestPrintError"
Cohesion: 0.20
Nodes (6): Test error printing functions., Test basic error printing., Test error printing with suggestions., Test error printing without suggestions., Test error panel has correct styling., TestPrintError

### Community 227 - "AGENTS.md"
Cohesion: 0.20
Nodes (9): AGENTS.md, Architecture (Required), AWS Interaction, Documentation Contract (Required), graphify, Implementation Priority (Required), Post-Implementation Quality Gate (Required), Project Structure (Mandatory) (+1 more)

### Community 228 - "Contributor Covenant 3.0"
Cohesion: 0.20
Nodes (9): Addressing and Repairing Harm, Attribution, Contributor Covenant 3.0, Encouraged Behaviors, Other Restrictions, Our Pledge, Reporting an Issue, Restricted Behaviors (+1 more)

### Community 231 - "Phase 1 — Reference Catalog Tables"
Cohesion: 0.22
Nodes (9): Phase 1 completion checklist, Phase 1 — Gate A: Spec review, Phase 1 — Gate B: Code review, Phase 1 — Reference Catalog Tables, Task 1: Alembic migration, Task 2: SQLAlchemy models, Task 3: Fixture loader, Task 4: Build integration (+1 more)

### Community 233 - "Morph Class Browse Surfacing + Wright Audit — Implementation Plan"
Cohesion: 0.22
Nodes (9): Coordinator quick reference — phase order summary, Explicitly deferred (not in this plan), Final whole-branch review, Global risks, Locked constraints (do not re-litigate), Morph Class Browse Surfacing + Wright Audit — Implementation Plan, Open questions, Orchestration (subagent-driven) (+1 more)

### Community 235 - "create_settings"
Cohesion: 0.29
Nodes (10): create_settings(), command, Context, group, pass_context, Settings-related commands., Settings-related commands., Create a new settings file. (+2 more)

### Community 236 - "base.py"
Cohesion: 0.20
Nodes (7): Alembic environment for the canonical wyrdcraeft SQLite database., Run Alembic migrations without a live database connection. Side Effects:…, Run Alembic migrations with a live SQLAlchemy connection. Side Effects: Opens a…, run_migrations_offline(), run_migrations_online(), Declarative database base class for wyrdcraeft., Shared database primitives for wyrdcraeft.

### Community 237 - "PHONOLOGY"
Cohesion: 0.22
Nodes (9): CHAPTER II: THE PRIMITIVE GERMANIC EQUIVALENTS OF THE INDO-GERMANIC VOWEL-SOUNDS {#chapter-3}, CHAPTER III: THE PRIMITIVE GERMANIC VOWEL-SYSTEM {#chapter-3}, CHAPTER IX: SPECIAL WEST GERMANIC MODIFICATIONS OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-9}, CHAPTER VI: THE OLD ENGLISH DEVELOPMENT OF THE PRIMITIVE GERMANIC VOWELS OF UNACCENTED SYLLABLES {#chapter-6}, CHAPTER VII: ABLAUT (VOWEL GRADATION) {#chapter-7}, CHAPTER VIII: THE FIRST SOUND-SHIFTING, VERNER’S LAW, AND OTHER CONSONANT CHANGES WHICH TOOK PLACE IN THE PRIMITIVE GERMANIC LANGUAGE {#chapter-8}, Other Consonant Changes, PHONOLOGY (+1 more)

### Community 239 - "Diacritic Context"
Cohesion: 0.25
Nodes (8): Diacritic Context, Inputs And Outputs, Invariants And Sharp Edges, Key Files, Main CLI Entrypoints, Primary Python Entrypoints, Related Docs, What This Capability Does

### Community 240 - "Dictionary Context"
Cohesion: 0.25
Nodes (8): Dictionary Context, Inputs And Outputs, Invariants And Sharp Edges, Key Files, Main CLI Entrypoints, Primary Python Entrypoints, Related Docs, What This Capability Does

### Community 241 - "Ingest Context"
Cohesion: 0.25
Nodes (8): Ingest Context, Inputs And Outputs, Invariants And Sharp Edges, Key Files, Main CLI Entrypoints, Primary Python Entrypoints, Related Docs, What This Capability Does

### Community 242 - "Settings Context"
Cohesion: 0.25
Nodes (8): Inputs And Outputs, Invariants And Sharp Edges, Key Files, Main CLI Entrypoints, Primary Python Entrypoints, Related Docs, Settings Context, What This Capability Does

### Community 243 - "Orchestrator Checkpoint"
Cohesion: 0.25
Nodes (7): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase 08 no-op rationale, Phase status, Resume here

### Community 244 - "Phase 1 — Browse morph-class detail block"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Exact files likely touched, Gate A — Spec review checklist, Gate B — Code review checklist, Objective, Phase 1 — Browse morph-class detail block, Subagent dispatch packet — Phase 1, Validation commands

### Community 245 - "Phase 2 — Wright § text ingest"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Exact files likely touched, Gate A — Spec review checklist, Gate B — Code review checklist, Objective, Phase 2 — Wright § text ingest, Subagent dispatch packet — Phase 2, Validation commands

### Community 246 - "Phase 4 — Legacy Wright audit command"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Exact files likely touched, Gate A — Spec review checklist, Gate B — Code review checklist, Objective, Phase 4 — Legacy Wright audit command, Subagent dispatch packet — Phase 4, Validation commands

### Community 247 - "test_session_composition.py"
Cohesion: 0.32
Nodes (7): _make_word(), Regression tests for the GeneratorSession -> WordPool/GenerationRunState split.…, test_run_state_attrs_forward_through_session(), test_session_composes_word_pool_and_run_state(), test_word_pool_append_participle(), test_word_pool_attrs_forward_through_session(), test_word_pool_categorize_matches_load_all_categorization()

### Community 248 - "Orchestrator Checkpoint"
Cohesion: 0.29
Nodes (6): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase status, Resume here

### Community 249 - "test_cli_convert.py"
Cohesion: 0.25
Nodes (7): patch, Test the convert command without LLM (heuristic mode)., Test that LLM flags are correctly passed to the pipeline., Test the convert command with a missing source file., test_convert_command_llm_flags(), test_convert_command_missing_source(), test_convert_command_no_llm()

### Community 250 - ".__init__"
Cohesion: 0.29
Nodes (4): Path, Initialize a SQLAlchemy sink for emitted morphology rows. Note: Index schema…, Ensure the canonical ``forms`` table and its indexes exist., Tune SQLite for bulk morphology index writes. Side Effects: Sets WAL mode and…

### Community 251 - "TestPrintSuccess"
Cohesion: 0.33
Nodes (4): Test success panel has correct styling., Test success printing functions., Test basic success printing., TestPrintSuccess

### Community 252 - "TestPrintInfo"
Cohesion: 0.33
Nodes (4): Test info printing functions., Test basic info printing., Test info panel has correct styling., TestPrintInfo

### Community 253 - "Domain Docs"
Cohesion: 0.33
Nodes (5): Before exploring, read these, Domain Docs, File structure, Flag ADR conflicts, Use the glossary's vocabulary

### Community 254 - "normalized_title + lexicon browse — checkpoint 2026-07-03T12:15"
Cohesion: 0.33
Nodes (5): Done this session, Gates, normalized_title + lexicon browse — checkpoint 2026-07-03T12:15, Ready to commit, User requirement (confirmed)

### Community 255 - "Mission: Machine Assistance For Old English Work"
Cohesion: 0.33
Nodes (5): Constraints, Mission: Machine Assistance For Old English Work, Out of scope, Success looks like, Why

### Community 256 - "Mission: Historical Linguistics for Old English Study"
Cohesion: 0.33
Nodes (5): Constraints, Mission: Historical Linguistics for Old English Study, Out of scope, Success looks like, Why

### Community 257 - "CHAPTER IV: THE OLD ENGLISH DEVELOPMENT OF THE PRIM. GERMANIC VOWELS OF ACCENTED SYLLABLES {#chapter-4}"
Cohesion: 0.33
Nodes (6): 1. UMLAUT, 2. Breaking, 3. Influence of Nasals, 4. Influence of Initial Palatal Consonants, 5. Influence of w, CHAPTER IV: THE OLD ENGLISH DEVELOPMENT OF THE PRIM. GERMANIC VOWELS OF ACCENTED SYLLABLES {#chapter-4}

### Community 258 - "A. The Short Vowels of Accented Syllables"
Cohesion: 0.33
Nodes (6): a, A. The Short Vowels of Accented Syllables, e, i, o, u

### Community 259 - "Wright & Wright (1908), "Old English Grammar", Oxford University Press"
Cohesion: 0.22
Nodes (8): The Seafarer (Old English poem, test fixture), Old English Bosworth-Toller Dictionary Text, ABBREVIATIONS, CONTENTS, INTRODUCTION, PREFACE, SELECT LIST OF BOOKS USED, Wright & Wright (1908), "Old English Grammar", Oxford University Press

### Community 260 - "Lemma-level morph class assignment (normalized_title, pos) -> morph_classes"
Cohesion: 0.18
Nodes (9): forms.morph_class_id denormalized propagation, Lemma-level morph class assignment (normalized_title, pos) -> morph_classes, Wright morph catalog reference schema (morph_classes, wright_sections, morph_sources), parts_of_speech as single POS source of truth (FK-only product tables), Files changed, Phase 1 Morph-Class Browse Report, Self-review findings, Test commands and output summary (+1 more)

### Community 261 - "Issue tracker: Trello"
Cohesion: 0.40
Nodes (4): Conventions, Issue tracker: Trello, When a skill says "fetch the relevant ticket", When a skill says "publish to the issue tracker"

### Community 262 - "Subagent task breakdown"
Cohesion: 0.40
Nodes (5): Subagent task breakdown, Task 1.1 — Extend catalog read DTO, Task 1.2 — Browse-time join in `LexiconQueryService`, Task 1.3 — Details pane rendering, Task 1.4 — Tests

### Community 263 - "Subagent task breakdown"
Cohesion: 0.40
Nodes (5): Subagent task breakdown, Task 2.1 — Markdown § parser, Task 2.2 — `WrightSectionTextIngester`, Task 2.3 — CLI subcommand, Task 2.4 — Query helper (minimal)

### Community 264 - "Subagent task breakdown"
Cohesion: 0.40
Nodes (5): Subagent task breakdown, Task 4.1 — Source file readers (priority 1), Task 4.2 — Audit checks (design spec), Task 4.3 — CLI, Task 4.4 — Tests

### Community 265 - "normalized_title — checkpoint 2026-07-03T12:10"
Cohesion: 0.40
Nodes (4): Done, Gates (2026-07-03 follow-up), normalized_title — checkpoint 2026-07-03T12:10, Remain

### Community 266 - "Machine Assistance For Old English Work Resources"
Cohesion: 0.40
Nodes (4): Gaps, Knowledge, Machine Assistance For Old English Work Resources, Wisdom (Communities)

### Community 267 - "Historical Linguistics for Old English Study Resources"
Cohesion: 0.40
Nodes (4): Gaps, Historical Linguistics for Old English Study Resources, Knowledge, Wisdom (Communities)

### Community 268 - "CHAPTER V: THE PRIM. GERMANIC EQUIVALENTS OF THE OE. VOWELS OF ACCENTED SYLLABLES {#chapter-5}"
Cohesion: 0.40
Nodes (5): A. THE SHORT VOWELS, B. The Long Vowels, C. The Short Diphthongs, CHAPTER V: THE PRIM. GERMANIC EQUIVALENTS OF THE OE. VOWELS OF ACCENTED SYLLABLES {#chapter-5}, The Chief Deviations Of The Other Dialects From West Saxon

### Community 269 - "B. THE LONG VOWELS OF ACCENTED SYLLABLES"
Cohesion: 0.40
Nodes (5): B. THE LONG VOWELS OF ACCENTED SYLLABLES, The Lengthening of Short Vowels, The Shortening Of Long Vowels, ā, ǣ

### Community 270 - "Old English c/g Palatalization Rule System"
Cohesion: 0.83
Nodes (4): Old English c/g Palatalization Rule System, c-Palatalization Force-Non-Palatalize Exception List, c-Palatalization Force-Palatalize Exception List, g Frontal-Vowel Palatalization Exception List

### Community 271 - "filter_display_variants"
Cohesion: 0.40
Nodes (5): test_filter_display_variants_drops_genitive_endings(), filter_display_variants(), is_genitive_variant_token(), Return whether one variant token is a weak-noun genitive ending. Args: token:…, Drop genitive-ending tokens from dictionary variant spellings. Args: variants:…

### Community 272 - "CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}"
Cohesion: 0.50
Nodes (4): A. THE VOWELS, B. THE CONSONANTS, CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}, STRESS (ACCENT)

### Community 273 - "CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}"
Cohesion: 0.50
Nodes (4): CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}, The Liquids, The Nasals, The Semivowels

### Community 274 - "infer_bt_pos_from_wordclasses"
Cohesion: 0.40
Nodes (4): test_infer_bt_pos_from_wordclasses_requires_single_mapping(), infer_bt_pos_from_wordclasses(), Shared morphology wordclass to dictionary POS mapping helpers., Map distinct morphology wordclasses to one dictionary POS when unambiguous.…

### Community 275 - ".emit_form_data"
Cohesion: 0.40
Nodes (3): Any, Write text to the underlying output stream., Emit one legacy form payload using parity row semantics. Note: Linguistic…

### Community 278 - "_format_entry_text"
Cohesion: 0.50
Nodes (4): _format_entry_text(), _format_sense_label(), Render one sense label with trailing punctuation for text output. Args: label:…, Render one consolidated dictionary entry as human-readable text. Args: entry:…

### Community 289 - "version"
Cohesion: 0.67
Nodes (3): command, Print the some version info of this package,, version()

## Ambiguous Edges - Review These
- `task-phase1-morph-class-browse-report.md` → `task-phase2-wright-text-ingest-report.md`  [AMBIGUOUS]
  doc/sessions/task-phase2-wright-text-ingest-report.md · relation: references
- `The Seafarer (Old English poem, test fixture)` → `Old English Bosworth-Toller Dictionary Text`  [AMBIGUOUS]
  tests/fixtures/seafarer.txt · relation: conceptually_related_to

## Knowledge Gaps
- **886 isolated node(s):** `release.sh script`, `wyrdcraeft`, `IPA_AUDIO`, `$schema`, `$id` (+881 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `task-phase1-morph-class-browse-report.md` and `task-phase2-wright-text-ingest-report.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `The Seafarer (Old English poem, test fixture)` and `Old English Bosworth-Toller Dictionary Text`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Word` connect `Word` to `models/__init__.py`, `PartOfSpeech`, `WordPool`, `GenerationRunState`, `strong_principal_flow.py`, `common.py`, `processors.py`, `VerbFormGenerator`, `test_generation_branches.py`, `weak_derivation_flow.py`, `adj_forms.py`, `strong_derivation_flow.py`, `weak_principal_flow.py`, `test_lemma_morph_assignment.py`, `normalize_morphology_title`, `morphology/loaders.py`, `._resolve_class_key`, `GeneratorSession`, `session.py`, `test_session_composition.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `TestCLISettings`, `.settings_customise_sources`, `test_paths.py`, `wyrdcraeft/settings.py`, `DatabaseMigrationError`, `cli/dictionary.py`, `cli.py`, `ingest/pipeline.py`, `test_schema.py`, `.ensure_ready`, `runtime.py`, `test_pipeline_classes.py`, `cli`, `AnyLLMConfig`, `LLMDocumentIngestor`, `source.py`, `DatabaseStartupRuntime`, `TestCLIVersion`, `TestCLIGlobalOptions`, `create_settings`, `build_runner.py`, `TestCLIErrorHandling`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `GeneratorSession` connect `GeneratorSession` to `Word`, `BTSqliteSink`, `morphology/test_query_service.py`, `WordPool`, `GenerationRunState`, `common.py`, `session.py`, `read_jsonl_gz`, `test_generation_branches.py`, `generate_vbforms`, `morphology/loaders.py`, `test_session_composition.py`, `build_runner.py`, `OENormalizer`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Word` (e.g. with `_NounAssignedIndex` and `AssignmentResult`) actually correct?**
  _`Word` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 87 inferred relationships involving `cli()` (e.g. with `test_morphology_build_populates_form_foreign_keys_for_known_lemma()` and `test_morphology_audit_wright_cli_json_does_not_rewrite_source_files()`) actually correct?**
  _`cli()` has 87 INFERRED edges - model-reasoned connections that need verification._