# Graph Report - wyrdcraeft  (2026-08-02)

## Corpus Check
- 365 files · ~5,529,722 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5728 nodes · 11984 edges · 286 communities (248 shown, 38 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 849 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4aa382d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BTSqliteSink
- BTSenseSegmenter
- DictionaryBuildPipeline
- runtime.py
- morphology/test_query_service.py
- ParadigmClassMapper
- ParsedBTLine
- MorphologyGenerateProgressCoordinator
- form_decode.py
- noun_forms.py
- .__init__
- common.py
- browse_tui.py
- processors.py
- VerbFormGenerator
- test_generation_branches.py
- BTAttestationStripper
- Settings
- weak_inflections.py
- session.py
- test_browse_tui.py
- upgrade_canonical_db
- strong_inflections.py
- form_rows.py
- test_markup.py
- tests/conftest.py
- weak_derivation_flow.py
- cli/dictionary.py
- diacritic_disambiguate
- diacritic_disambiguate.py
- ensure_parts_of_speech
- OldEnglishText
- ingest/pipeline.py
- Word
- .load_fixture
- adj_forms.py
- strong_derivation_flow.py
- etymology_display.py
- weak_principal_flow.py
- SenseMetadataClassifier
- cli
- .ensure_ready
- TextMetadata
- MorphologyCatalogLoader
- build_pipeline.py
- read_jsonl_gz
- NormalizedTitleJoinIndex
- wright_audit.py
- wright-morphology-fixture.schema.json
- test_cli_diacritic_disambiguate.py
- test_pipeline_classes.py
- models/__init__.py
- morphology/loaders.py
- cli.py
- Session: Morphology Wright Catalog — Phase 2 complete
- _seed_catalog_assignment
- properties
- properties
- create_engine
- test_morph_catalog_pos.py
- test_cli_dictionary.py
- SourceLoader
- AnyLLMConfig
- check_napoleon_gate.py
- Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅
- BackupStateStore
- test_index_pipeline.py
- test_line_parser.py
- PHONOLOGY
- markup.py
- LLMDocumentIngestor
- .run
- GeneratorSession
- test_text_utils_reference.py
- test_wright_audit.py
- BTPos
- enum
- MorphologyDictionaryCleaner
- test_form_fk_resolver.py
- .palatalize
- reading_convert
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
- .ingest
- .parse
- required
- features
- DictionaryBuildStage
- test_generation_package_imports.py
- Configuration: Command Line Tool guide
- DatabaseStartupRuntime
- 20260706_01_parts_of_speech_and_dictionary_pos.py
- TestCLIVersion
- OESyllableBreaker
- ._begin_connection
- wyrdcraeft dictionary browse
- TestCLIGlobalOptions
- properties
- full_session
- Lexicon shrink: drop lexicon_entries/lexicon_forms, keep search_keys
- models/morphology.py
- catalog_db
- BTQueryService
- _run_database_readiness_gate
- cli/morphology.py
- Implementation Slices
- fixture_prose.txt (Mark gospel OE prose fixture)
- GeneratorSession.load_all
- wyrdcraeft 1.1.0 release (2026-03-02)
- DictionaryCorpusSampler
- diacritic.py
- Batched SQLite sink (25K rows) + bulk PRAGMAs fix for morphology build perf
- Phase 2 — Lemma Morph Class Assignment
- main
- Morphology Wright catalog — Phase 1 session (2026-07-04)
- Rule
- TestCLIErrorHandling
- DictionaryPosInferer
- TestConsoleQuietMode
- TestCLISettings
- DocumentIngestor
- .on_key
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
- MorphologySetupStep
- .__init__
- Dictionary build/browse flow (concept)
- Wyrdcraeft Canonical DB Migration Implementation Plan
- Architecture review — 2026-08-01
- test_prompt_regression.py
- catalog_db
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
- generate_reference_snapshots
- wyrdcraeft Context
- 20260630_01_initial_canonical_schema.py
- 20260703_01_add_normalized_title_columns.py
- 20260704_01_morph_catalog_tables.py
- 20260704_02_lemma_morph_classes.py
- 20260706_02_forms_foreign_keys.py
- 20260706_03_lexicon_shrink_search_keys.py
- 20260706_04_drop_forms_legacy_strings.py
- 20260707_01_drop_search_keys.py
- 20260707_02_bt_senses_entry_order_index.py
- 20260707_03_bt_source_blocks_and_rich_senses.py
- create_session_factory
- _entry_to_dict
- .resolve_sense_path
- Phase A — Reference Tables and Dictionary POS FKs
- MorphologyCatalogQueryService
- Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns
- create_dict31.pl (legacy Perl morphology generator)
- BTQueryService
- Python coding standards
- .swap_bt_diphthong_long_marks
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
- .__init__
- Global Constraints
- Lexicon Browser BT V2 Adaptation Skeleton
- Orchestration: Wyrdcraeft Canonical DB Migration
- Morph Class Browse And Audit Design
- MorphBuildOptions
- Phase B — Forms Foreign Keys (Legacy Strings Remain)
- 0002-normalized-canonical-schema.md
- Phase 2 — Wright § Text Ingest Report
- 0007-ocr-pipeline-moves-to-bochord.md
- Two-gate subagent workflow: Gate A spec review, Gate B code review
- default_bt_source_path
- AGENTS.md
- Contributor Covenant 3.0
- isolated_morphology_app_data pytest fixture (no writes to real app-data DB)
- refactor_baseline.json Perl-parity guardrail for morphology generation
- Phase 1 — Reference Catalog Tables
- Unified dictionary build pipeline replacing morphology/dictionary/lexicon build triangle
- Morph Class Browse Surfacing + Wright Audit — Implementation Plan
- test_dict.txt (BT morphology dictionary test fixture)
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
- Orchestrator Checkpoint
- FormSink
- .__init__
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
- CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}
- CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}
- FormWriter
- release.sh
- 0002-canonical-morphology-db-uses-startup-alembic-migrations.md
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
- wyrdcraeft

## God Nodes (most connected - your core abstractions)
1. `GeneratorSession` - 176 edges
2. `Word` - 164 edges
3. `cli()` - 107 edges
4. `BTSenseSegmenter` - 86 edges
5. `Settings` - 74 edges
6. `VerbFormGenerator` - 68 edges
7. `ParsedBTLine` - 67 edges
8. `BTLineParser` - 65 edges
9. `create_engine()` - 58 edges
10. `MorphologyCatalogLoader` - 56 edges

## Surprising Connections (you probably didn't know these)
- `Solomon and Saturn dialogue test fixture` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_dialogue.txt → doc/source/overview/format.rst
- `Beowulf opening lines test fixture (poetry)` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_poetry.txt → doc/source/overview/format.rst
- `test_dictionary_group_help()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_dictionary.py → wyrdcraeft/cli/cli.py
- `test_dictionary_clean_headwords_help()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_dictionary.py → wyrdcraeft/cli/cli.py
- `test_dictionary_generate_reference_snapshots_help()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_dictionary.py → wyrdcraeft/cli/cli.py

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

## Communities (286 total, 38 thin omitted)

### Community 0 - "BTSqliteSink"
Cohesion: 0.04
Nodes (69): Client, lexicon_source_db(), Dictionary-backed canonical DB fixture for browse TUI tests., _parsed_line(), BTSense, Path, Tests for optional Bosworth-Toller LLM parse repair., test_apply_fixes_keeps_deterministic_line_on_validation_failure() (+61 more)

### Community 1 - "BTSenseSegmenter"
Cohesion: 0.03
Nodes (84): _golden_sense_matches(), _load_golden(), BTSense, fixture, Tests for Phase 03 BTSenseSegmenter., Arabic display labels for canonical sense paths., Unit tests for specific segmenter behaviours., Body with no sense labels produces a single unlabelled sense. (+76 more)

### Community 2 - "DictionaryBuildPipeline"
Cohesion: 0.12
Nodes (19): AnyDictionaryBuildEvent, DictionaryBuildLogLevel, DictionaryBuildPipeline, Connection, Orchestrate canonical dictionary rebuild, form relink, and follow-on refreshes.…, Relink every stored form row against the rebuilt dictionary tables. Args:…, Infer missing dictionary POS values from stored morphology forms. Args:…, Return the current ``forms`` row count. Args: connection: Open SQLAlchemy… (+11 more)

### Community 3 - "runtime.py"
Cohesion: 0.04
Nodes (115): DeclarativeBase, Tests for catalog-backed morph-class metadata in lexicon browse details., _make_word(), query_service(), Tests for read-only Wright catalog lemma class lookup., test_format_morph_class_display_label_falls_back_to_canonical_name(), test_format_morph_class_display_label_prefers_compact_modern_label(), test_lookup_missing_lemma_returns_none() (+107 more)

### Community 4 - "morphology/test_query_service.py"
Cohesion: 0.04
Nodes (82): _build_output_sink(), Build the output sink used while profiling adjective generation. Keyword Args:…, TemporaryDirectory, make_lexicon_source_db(), Path, Helpers for building morphology SQLite databases used in lexicon tests., Build a morphology database seeded with ``forms`` and ``bt_*`` tables. Args:…, Write minimal ``forms`` rows into a morphology SQLite database. Args: db_path:… (+74 more)

### Community 5 - "ParadigmClassMapper"
Cohesion: 0.06
Nodes (44): assigner(), _assignment(), catalog_db(), _class_key(), _make_verb_paradigm(), _make_word(), fixture, Path (+36 more)

### Community 6 - "ParsedBTLine"
Cohesion: 0.04
Nodes (80): _entry_to_comparable(), _load_golden(), merger(), _parse_lines(), parser(), fixture, parametrize, Tests for Phase 04 BTEditorialMerger and BTTargetResolver. (+72 more)

### Community 7 - "MorphologyGenerateProgressCoordinator"
Cohesion: 0.04
Nodes (66): test_build_profiler_disabled_emits_nothing(), test_build_profiler_emits_stage_and_sqlite_sections(), test_progress_coordinator_omits_empty_wright_and_throttles_lemma(), test_progress_coordinator_stage_totals(), MorphologyBuildProfiler, TextIO, Wall-clock profiling helpers for morphology build runs., Finish wall-clock timing for one generation stage. Args: stage: Stage being… (+58 more)

### Community 8 - "form_decode.py"
Cohesion: 0.04
Nodes (101): MorphologyTableInputRow, Tests for morphology function-code decoding., test_build_adjective_sidebar_uses_payload_inflection(), test_build_adverb_sidebar_decodes_superlative_su_code(), test_build_morphology_table_fills_inflection_from_morph_class_label(), test_build_morphology_table_includes_surface_form_column(), test_build_morphology_table_sorts_adjectives_by_degree_inflection_and_case(), test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms() (+93 more)

### Community 9 - "noun_forms.py"
Cohesion: 0.05
Nodes (76): generate_nounforms(), Delegate noun form generation to the extracted module. Args: session: Active…, _build_stem_ar_pl(), _build_stem_ar_sg_ge_da(), _build_stem_ar_sg_no_ac(), _build_stem_daeg_pl(), _build_stem_geminate(), _build_stem_hof_ge_da() (+68 more)

### Community 10 - ".__init__"
Cohesion: 0.40
Nodes (3): Path, Initialize the dictionary sink for canonical or direct pipeline usage. Args:…, Ensure ``bt_*`` tables exist and clear prior dictionary rows.

### Community 11 - "common.py"
Cohesion: 0.05
Nodes (74): PartDispatcher, PartProcessor, PartStemSegmentDeriver, StrongInfDerivationEmitter, StrongPartGenerator, StrongPrincipalFormAction, StrongPrincipalInfDerivationAction, StrongPrincipalParticipleAction (+66 more)

### Community 12 - "browse_tui.py"
Cohesion: 0.03
Nodes (119): Changed, ComposeResult, Input, ListItem, Paste, Pressed, Selected, Static (+111 more)

### Community 13 - "processors.py"
Cohesion: 0.12
Nodes (25): Morphology paradigm assigners., _get_r_stem_paradigm(), Resolve opt-in r-stem paradigm for a word. Classification uses: - exact Wright…, Check whether ``wright`` contains the exact semicolon-delimited token. Args:…, _wright_has_token(), _assign_verb_by_advanced_diacritics(), _assign_verb_by_advanced_stem(), _assign_verb_by_diacritics() (+17 more)

### Community 14 - "VerbFormGenerator"
Cohesion: 0.03
Nodes (44): ParadigmVariant, BaseModel, Paradigm variant model., VerbParadigm, generate_vbforms(), Emit one weak ``PsInSg2``-branch form row with simplified post-vowel. Side…, Emit one weak ``PsInSg2`` sound-change branch with simplified post-vowel. Side…, Emit one strong principal-part row for a selected active vowel. Side Effects:… (+36 more)

### Community 15 - "test_generation_branches.py"
Cohesion: 0.08
Nodes (48): StrongFormEmitter, _base_formhash(), _make_part(), _make_variant(), _make_verb_paradigm(), _make_word(), test_add_participle_to_adjectives_helper_appends_past_participle(), test_add_participle_to_adjectives_helper_appends_present_participle() (+40 more)

### Community 16 - "BTAttestationStripper"
Cohesion: 0.04
Nodes (47): fixture, parametrize, Tests for Phase 03 BTAttestationStripper., ``_is_citation_span`` returns True for grammar/editorial markers and citations., ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes., ``_strip_editorial_directive`` removes leading supplement editorial verbs., Unit tests for BTAttestationStripper.strip., ``:--`` is the canonical attestation separator. (+39 more)

### Community 17 - "Settings"
Cohesion: 0.05
Nodes (36): Exception, patch, Unit tests for configuration settings. Tests the new OpenAI and summary…, Test that model_config is properly configured., Test output format validation., Test valid output format validation., Test settings loading from environment variables. This test is a placeholder…, Test that environment variables override defaults. (+28 more)

### Community 18 - "weak_inflections.py"
Cohesion: 0.04
Nodes (64): test_dispatch_weak_derived_forms_selects_psinsg2_branch(), test_dispatch_weak_derived_forms_skips_item_shape_mode(), test_dispatch_weak_principal_part_derivations_emits_papt_only(), test_emit_weak_derived_from_inf_by_class2_general_branch(), test_emit_weak_derived_from_inf_by_class2_two_uses_general_path(), test_emit_weak_derived_from_inf_sequence_normalizes_none_probability(), test_emit_weak_derived_from_painsg1_sequence_uses_preterite_order(), test_emit_weak_derived_from_painsg1_variant_sequence() (+56 more)

### Community 19 - "session.py"
Cohesion: 0.09
Nodes (61): morphology, morphology_full, Namespace, main(), _mypy_baseline(), _runtime_baseline_ms(), _sha256_rows(), _stage_rows() (+53 more)

### Community 20 - "test_browse_tui.py"
Cohesion: 0.10
Nodes (60): anyio, _bt_entry_id(), _collect_widget_ids(), _details_text(), empty_browse_db(), _insert_entry(), _insert_inflection_code(), _pos_id() (+52 more)

### Community 21 - "upgrade_canonical_db"
Cohesion: 0.05
Nodes (75): _index_with_attach(), Path, Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite., Seed the canonical ``forms`` table via the real SQLAlchemy sink., _seed_forms_table(), test_attach_missing_db_fails_for_canonical_only_mode(), test_attach_preserves_forms_and_writes_bt_entries(), test_attach_rerun_is_idempotent_and_preserves_forms() (+67 more)

### Community 22 - "strong_inflections.py"
Cohesion: 0.10
Nodes (26): StrongBranchAction, StrongDerivedEmitter, StrongParticipleSink, StrongSoundEmitter, test_dispatch_strong_derived_from_principal_part_routes_painsg1(), test_dispatch_strong_verb_part_branches_painpl(), test_dispatch_strong_verb_part_branches_papt_only(), test_emit_strong_derived_from_inf_sequence_event_ordering() (+18 more)

### Community 23 - "form_rows.py"
Cohesion: 0.06
Nodes (49): generate_advforms(), FormOutput, Adverb form generation helpers., Generate adverb forms and comparative/superlative derivatives. Args: session:…, generate_advforms(), generate_numforms(), Delegate adverb form generation to the extracted module. Args: session: Active…, Delegate numeral form generation to the extracted module. Args: session: Active… (+41 more)

### Community 24 - "test_markup.py"
Cohesion: 0.07
Nodes (40): Path, test_build_index_from_bt_extracts_and_dedupes(), Path, C before i/ī in any position palatalizes (Rule C)., Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)., gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar., Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc., Cyning (c + y from u) remains non-palatalized; blocklist and only-back. (+32 more)

### Community 25 - "tests/conftest.py"
Cohesion: 0.06
Nodes (53): Popen, cli_context(), ensure_llama_server(), _is_llama_server_healthy(), isolated_morphology_app_data(), isolated_morphology_index_db(), lexicon_source_db(), mock_console() (+45 more)

### Community 26 - "weak_derivation_flow.py"
Cohesion: 0.05
Nodes (49): WeakInfFormEmitter, WeakPainsg1ContextFormEmitter, WeakPsinsg2DerivationFormContextEmitter, WeakPsinsg2DerivationSoundContextEmitter, Immutable context for weak infinitive-derived emitter callbacks. Args:…, Immutable context for weak ``PaInSg1``-derived emitter callbacks. Args:…, Immutable context for weak ``PsInSg2``-derived emitter callbacks. Args:…, _WeakInfDerivationContext (+41 more)

### Community 27 - "cli/dictionary.py"
Cohesion: 0.09
Nodes (43): audit_wright(), browse(), build(), clean_headwords(), _count_table_rows(), _default_morphology_data_dir(), _default_source_path(), _format_entry_text() (+35 more)

### Community 28 - "diacritic_disambiguate"
Cohesion: 0.08
Nodes (27): Layout, _can_mark_completed(), diacritic_disambiguate(), _normalize_option_key_sequences(), _prompt_attested_form(), _prompt_form_annotation(), _prompt_modern_meaning(), _prompt_pos_code() (+19 more)

### Community 29 - "diacritic_disambiguate.py"
Cohesion: 0.16
Nodes (24): test_fetch_bt_search_entries_uses_search_endpoint(), test_filter_bt_entries_by_normalized_form_empty_list_returns_empty(), test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others(), test_filter_bt_entries_by_normalized_form_no_matches_returns_empty(), test_filter_bt_entries_by_normalized_form_preserves_order(), test_merge_bt_entries_deduplicates_and_reindexes(), test_normalize_bt_spelling_converts_acute_to_macron(), test_parse_bt_search_entries_extracts_fields() (+16 more)

### Community 30 - "ensure_parts_of_speech"
Cohesion: 0.08
Nodes (40): fixture, resolver_db(), _load_fixture_rows(), Connection, Path, Tests for normalized POS and inflection-code seed fixtures., Read one JSON fixture file used by the POS seed tests., Return the current row count for one reference table. (+32 more)

### Community 31 - "OldEnglishText"
Cohesion: 0.08
Nodes (43): fixture, sample_doc(), test_tei_export_attributes(), test_tei_export_basic(), test_tei_export_structure(), test_tei_exporter_interface(), Test importing Beowulf from TEI XML., test_tei_import_beowulf() (+35 more)

### Community 32 - "ingest/pipeline.py"
Cohesion: 0.06
Nodes (41): object, test_canonical_converter_prose(), test_canonical_converter_verse(), test_structure_parser_prose(), test_structure_parser_verse(), patch, TestLLMDocumentIngestor, test_mixed_mode_splitting() (+33 more)

### Community 33 - "Word"
Cohesion: 0.05
Nodes (55): Lexical entry schema carrying POS flags and paradigm state for one lemma., Word, _append_short_syllable_front_vowel_heuristic(), _append_suffix_heuristics(), _append_terminal_a_heuristic(), _append_terminal_e_heuristic(), _apply_final_fallback(), _apply_noun_heuristics() (+47 more)

### Community 34 - ".load_fixture"
Cohesion: 0.09
Nodes (17): Any, Path, Session, Upsert catalog rows from one packaged Wright fixture JSON file. Args: path:…, Load the fixture when the catalog is empty or refresh is requested. Args: path:…, Read and parse one Wright catalog fixture file. Args: path: Path to the JSON…, Validate required fixture structure before writing catalog rows. Args: payload:…, Collect unique Wright section numbers referenced by morph classes. Args:… (+9 more)

### Community 35 - "adj_forms.py"
Cohesion: 0.07
Nodes (53): _adj_print(), _build_adjective_formhash(), _build_comparative_title_array(), _build_superlative_title_array(), _build_weak_title_array(), _dedupe_preserve_first(), _emit_superlative_strong_forms(), _emit_weak_degree_forms() (+45 more)

### Community 36 - "strong_derivation_flow.py"
Cohesion: 0.05
Nodes (45): StrongDerivedInfFormAction, StrongDerivedInfImsgAction, StrongDerivedInfParticipleAction, StrongDerivedInfSoundAction, StrongInfDerivationRouter, Immutable context for strong infinitive-derived emitter callbacks. Args:…, _StrongInfDerivationContext, Emit one strong infinitive-derived row for a selected active vowel. Side… (+37 more)

### Community 37 - "etymology_display.py"
Cohesion: 0.07
Nodes (51): Tests for etymology parsing and browse table formatting., test_format_etymology_display_renders_table_headers(), test_misplaced_attestation_is_flagged(), test_mixed_attestation_and_cognates_split(), test_parse_cognate_chain_with_citation(), test_parse_colon_separated_lang_chain(), test_parse_multiple_german_cognates(), test_parse_norse_words_with_latin_tail() (+43 more)

### Community 38 - "weak_principal_flow.py"
Cohesion: 0.07
Nodes (56): WeakInfBranchGenerator, WeakPainsg1BranchGenerator, WeakPrincipalContextAction, WeakPrincipalFormEmitter, WeakPrincipalParticipleAction, WeakPsinsg2BranchGenerator, Immutable context for weak principal-part callback bindings. Args: formhash:…, _WeakPrincipalPartContext (+48 more)

### Community 39 - "SenseMetadataClassifier"
Cohesion: 0.07
Nodes (25): Unit tests for sense-prefix metadata classification., TestSenseMetadataClassifier, _has_substantive_gloss(), _looks_like_gloss_start(), _normalize_case(), _normalize_gender(), _normalize_modifier(), Normalize one modifier abbreviation token. Args: token: Raw modifier token… (+17 more)

### Community 40 - "cli"
Cohesion: 0.10
Nodes (25): Test that the OCR command group has been removed from the CLI., test_ocr_command_group_removed(), patch, Test the convert command without LLM (heuristic mode)., Test that LLM flags are correctly passed to the pipeline., Test the convert command with a missing source file., test_convert_command_llm_flags(), test_convert_command_missing_source() (+17 more)

### Community 41 - ".ensure_ready"
Cohesion: 0.10
Nodes (17): Config, build_alembic_config(), _format_backup_prompt_text(), Path, Store the backup path and explicit rebuild recipe for CLI reporting. Keyword…, Build the Alembic configuration for one canonical SQLite database. Args:…, Delete one file when it exists. Args: path: Filesystem path that may need…, Run the startup database decision tree once. Raises: DatabaseMigrationError:… (+9 more)

### Community 42 - "TextMetadata"
Cohesion: 0.11
Nodes (26): ProgressCallback, parametrize, Test that deterministic ingestion of text files matches the golden JSON…, test_deterministic_ingestion_regression(), patch, BaseDocumentIngestor, HeuristicDocumentIngestor, ingest_auto() (+18 more)

### Community 43 - "MorphologyCatalogLoader"
Cohesion: 0.14
Nodes (18): catalog_db(), fixture, Path, Build a small morphology slice and verify normalized FK columns on forms., test_catalog_loader_ensure_seeded_refresh(), test_catalog_loader_ensure_seeded_skips_when_populated(), test_catalog_loader_is_idempotent(), test_catalog_loader_populates_recognition_hints_json() (+10 more)

### Community 44 - "build_pipeline.py"
Cohesion: 0.17
Nodes (21): DictionaryBuildCounters, DictionaryBuildEvent, DictionaryBuildFinished, DictionaryBuildLog, DictionaryBuildSnapshot, DictionaryBuildStageProgress, DictionaryBuildStageStarted, Typed stage and event models for unified dictionary builds. (+13 more)

### Community 45 - "read_jsonl_gz"
Cohesion: 0.17
Nodes (18): assert_snapshot_parity(), Path, Assert full-flow parity against a canonical snapshot file. Args: session:…, canonical_sort_rows(), Any, Path, Read compressed JSON lines snapshot records. Args: path: Snapshot path.…, Write compressed JSON lines deterministically. Args: path: Snapshot destination… (+10 more)

### Community 46 - "NormalizedTitleJoinIndex"
Cohesion: 0.11
Nodes (21): _index(), Unit tests for NormalizedTitleJoinIndex., test_resolve_all_exactly_one_title_across_pos(), test_resolve_all_no_match(), test_resolve_all_pos_direct_multiple_matches(), test_resolve_all_pos_direct_single_match(), test_resolve_all_variant_with_pos_filter(), test_resolve_all_variant_without_pos_filter() (+13 more)

### Community 47 - "wright_audit.py"
Cohesion: 0.05
Nodes (47): Lowercase all-uppercase Bosworth-Toller headwords in oe_bt.txt., _append_sample_block(), _catalog_pos_from_word(), _display_legacy_wright(), _format_blank_but_classified_issue(), _format_contradiction_issue(), _format_malformed_issue(), _format_row_prefix() (+39 more)

### Community 48 - "wright-morphology-fixture.schema.json"
Cohesion: 0.05
Nodes (39): 1.0, morph_classes, Old English, schema_version, sources, wright-modern-morphology, additionalProperties, description (+31 more)

### Community 49 - "test_cli_diacritic_disambiguate.py"
Cohesion: 0.10
Nodes (39): _minimal_index_payload(), _mock_bt_lookup(), fixture, Path, Minimal macron index payload for diacritic add/delete tests., test_diacritic_add_fails_when_exists_without_force(), test_diacritic_add_fails_when_key_in_ambiguous_even_with_force(), test_diacritic_add_force_overwrites() (+31 more)

### Community 50 - "test_pipeline_classes.py"
Cohesion: 0.16
Nodes (14): dialogue_text(), prose_text(), fixture, patch, _t(), test_document_ingestor_dispatch(), test_llm_document_ingestor(), test_oe_filter() (+6 more)

### Community 51 - "models/__init__.py"
Cohesion: 0.11
Nodes (28): patch, With only input given, paths default to stem + infix + extension., test_source_mark_diacritics_default_paths(), test_source_mark_diacritics_writes_text_and_ambiguities(), test_source_mark_diacritics_writes_unknowns_file(), AmbiguityOption, DiacriticRestorationResult, MacronAmbiguity (+20 more)

### Community 52 - "morphology/loaders.py"
Cohesion: 0.17
Nodes (13): ManualForm, Manual form model for ``manual_forms.txt`` ingest rows. Legacy string fields…, load_dictionary(), load_forms(), load_paradigms(), load_prefixes(), Load the paradigms from a file. Args: path: The path to the paradigms file.…, Load the dictionary from a file. Args: path: The path to the dictionary file.… (+5 more)

### Community 53 - "cli.py"
Cohesion: 0.05
Nodes (47): Tests for CLI commands with low coverage., Test that Settings has no ocr_ fields., test_settings_has_no_ocr_fields(), Tests for CLI utilities., Test success panel has correct styling., Test info printing functions., Test basic info printing., Test info panel has correct styling. (+39 more)

### Community 54 - "Session: Morphology Wright Catalog — Phase 2 complete"
Cohesion: 0.15
Nodes (7): Architecture, Deliverables, Known limitations (deferred), Next, Session: Morphology Wright Catalog — Phase 2 complete, Summary, Validation

### Community 55 - "_seed_catalog_assignment"
Cohesion: 0.36
Nodes (9): _bt_entry_id(), _insert_bt_entry(), Path, Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions., Seed one catalog assignment row into a temporary lexicon test database., Insert one minimal ``bt_entries`` row into a temporary lexicon test database.…, _seed_catalog_assignment(), test_get_details_includes_catalog_morph_class_and_unclassified() (+1 more)

### Community 56 - "properties"
Cohesion: 0.06
Nodes (34): type, type, type, properties, type, type, type, type (+26 more)

### Community 57 - "properties"
Cohesion: 0.06
Nodes (34): description, minLength, type, $ref, default, description, enum, type (+26 more)

### Community 58 - "create_engine"
Cohesion: 0.22
Nodes (22): _fetch_form_entry_id(), _insert_bt_entry(), _insert_bt_variant(), _insert_form(), _pos_id(), Connection, fixture, Path (+14 more)

### Community 59 - "test_morph_catalog_pos.py"
Cohesion: 0.11
Nodes (29): parametrize, Tests for morphology catalog POS normalization helpers., test_catalog_pos_from_bt_pos_cli_aliases(), test_catalog_pos_from_bt_pos_join_values(), test_catalog_pos_from_bt_pos_raises_for_unmapped(), test_catalog_pos_from_wordclass(), test_catalog_pos_from_wordclass_unknown_returns_none(), test_pos_id_from_bt_pos() (+21 more)

### Community 60 - "test_cli_dictionary.py"
Cohesion: 0.12
Nodes (32): _build_unified_source_db(), _fetch_entry_id(), _fetch_form_entry_id(), _insert_form(), _morphology_data_dir(), _pos_id(), Connection, Path (+24 more)

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

### Community 65 - "BackupStateStore"
Cohesion: 0.09
Nodes (29): Path, test_backup_state_round_trip_uses_sidecar_beside_canonical_db(), test_create_backup_copies_database_and_keeps_latest_by_default(), test_restore_backup_overwrites_database_contents(), create_backup(), list_backups(), _prune_old_backups(), datetime (+21 more)

### Community 66 - "test_index_pipeline.py"
Cohesion: 0.19
Nodes (27): Row, slow, _fetch_entry(), _index_fixture(), _load_warnings(), Connection, Path, Integration tests for the Bosworth-Toller dictionary index pipeline. (+19 more)

### Community 67 - "test_line_parser.py"
Cohesion: 0.08
Nodes (26): parametrize, Tests for Phase 02 Bosworth-Toller line parser., Skipped lines return explicit reasons needed by downstream reporting., Substitute target extraction captures ``for X in Dict`` phrases., Variant and noun-gender extraction uses pre-POS prefix conventions., Parser emits display headwords with Wright-style diphthong long marks., Trailing bracket blocks are preserved for later etymology handling., Deletion references are parsed from text after the ``Dele`` marker. (+18 more)

### Community 68 - "PHONOLOGY"
Cohesion: 0.07
Nodes (28): 1. UMLAUT, 2. Breaking, 3. Influence of Nasals, 4. Influence of Initial Palatal Consonants, 5. Influence of w, a, A. The Short Vowels of Accented Syllables, A. THE VOWELS. (+20 more)

### Community 69 - "markup.py"
Cohesion: 0.03
Nodes (92): parametrize, Tests for BT display spelling normalization., Normalize representative real BT headword spellings from ``oe_bt.txt``., Normalizing an already-normalized spelling is a no-op., test_bt_spelling_normalizer_matches_oe_normalizer(), test_normalize_is_idempotent(), test_normalize_real_bt_diphthong_cases(), test_normalize_morphology_title_preserves_macrons_and_dots() (+84 more)

### Community 70 - "LLMDocumentIngestor"
Cohesion: 0.09
Nodes (16): Unmarked verse gets 1-based line numbers within the section., test_canonical_converter_verse_number_fallback(), fixture, CanonicalConverter, LLMDocumentIngestor, Converts pre-parsed documents into canonical OldEnglishText models., Extract a structural number marker from the start of a string. Args: text: The…, Split a paragraph of text into sentences, handling terminal punctuation inside… (+8 more)

### Community 71 - ".run"
Cohesion: 0.19
Nodes (9): DictionaryBuildStatus, Path, Forward pipeline morphology options to the shared build runner. Keyword Args:…, Run the unified dictionary build pipeline against one source file. Keyword…, Clear stale form links and rebuild the canonical dictionary slice. Args:…, Run the optional morphology regeneration stage. Args: options: Morphology…, Run one single-step stage with begin and finish hooks. Args: stage: Top-level…, Return the current build snapshot payload. Keyword Args: status: Lifecycle… (+1 more)

### Community 72 - "GeneratorSession"
Cohesion: 0.08
Nodes (37): _make_verb_paradigm(), _make_word(), test_set_adj_paradigm_stem_propagation(), test_set_adj_paradigm_wright_rule_425(), test_set_noun_paradigm_advanced_stem_propagation(), test_set_noun_paradigm_final_fallback_neuter_long_stem(), test_set_noun_paradigm_final_fallback_neuter_short_stem(), test_set_noun_paradigm_heuristic_incel_suffix() (+29 more)

### Community 73 - "test_text_utils_reference.py"
Cohesion: 0.17
Nodes (15): parametrize, test_canonicalize_inflection_code_reference(), test_eth2thorn_reference(), test_iumlaut_reference(), test_move_accents_reference(), test_normalize_bt_display_spelling_is_idempotent(), test_normalize_bt_display_spelling_reference(), test_normalize_output_reference() (+7 more)

### Community 74 - "test_wright_audit.py"
Cohesion: 0.16
Nodes (24): _dictionary_line(), _make_audit_source_dir(), _manual_form_line(), _para_vb_line(), Path, Tests for legacy Wright source auditing. Phase D source contract: The audit…, Build one ``manual_forms.txt`` fixture line with the expected 16 columns., Build one ``para_vb.txt`` fixture line for malformed-token scanning. (+16 more)

### Community 75 - "BTPos"
Cohesion: 0.05
Nodes (56): _entry_to_dict(), main(), _parse_and_segment(), Parse and segment one raw BT line., Convert a BTConsolidatedEntry to a serialisable dict., extractor(), fixture, parametrize (+48 more)

### Community 76 - "enum"
Cohesion: 0.08
Nodes (26): common, comparative, dual, feminine, first, masculine, neuter, plural (+18 more)

### Community 77 - "MorphologyDictionaryCleaner"
Cohesion: 0.12
Nodes (17): parametrize, Tests for morphology dictionary TSV cleanup., test_clean_dictionary_fixes_bt_diphthongs_in_col2(), test_clean_dictionary_lowercases_col2_dedupes_and_backups(), test_clean_dictionary_raises_when_source_missing(), test_should_lowercase_col2_only_all_upper_letters(), MorphologyDictionaryCleaner, MorphologyDictionaryCleanupResult (+9 more)

### Community 78 - "test_form_fk_resolver.py"
Cohesion: 0.22
Nodes (21): _insert_bt_entry(), _insert_bt_variant(), _insert_lemma_assignment(), Connection, Path, Tests for morphology form foreign-key resolution., test_catalog_loader_assignment_visible_via_sqlalchemy(), test_preloaded_maps_without_connection() (+13 more)

### Community 79 - ".palatalize"
Cohesion: 0.15
Nodes (9): _apply_case_pattern(), _possible_pre_iumlaut_sources(), Apply source casing pattern to target text. Args: source: Original text to…, Palatalize ``g`` in a lexical token. Args: word: Token to palatalize. Returns:…, Return possible pre-i-mutation (reconstructed) sources for an OE vowel. Used to…, Test if ``text[index:]`` starts with a front-vowel context. Args: text:…, Return whether the character before position i is i/ī or i/ī + n. Used for Rule…, Return True if the vowel unambiguously derives only from back vowels. Used to… (+1 more)

### Community 80 - "reading_convert"
Cohesion: 0.11
Nodes (21): Progress, _mark_diacritics_derived_path(), argument, command, Context, group, option, pass_context (+13 more)

### Community 81 - "BT V2 Parser And Schema Migration"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT V2 Parser And Schema Migration, CLI Output Contract, Context, Dependencies, Follow-on Work, Locked Decisions, Problem Classes BT V2 Must Fix (+4 more)

### Community 82 - "properties"
Cohesion: 0.08
Nodes (25): oldenglish_info, stella, wright_1914, description, minLength, type, default, description (+17 more)

### Community 83 - "BTSourceHeadwordCleaner"
Cohesion: 0.12
Nodes (17): parametrize, Tests for Bosworth-Toller oe_bt.txt headword cleanup., test_clean_headwords_leaves_later_bold_tags_unchanged(), test_clean_headwords_lowercases_first_bold_and_backups(), test_clean_headwords_raises_when_source_missing(), test_should_lowercase_headword_only_all_upper_letters(), BTSourceHeadwordCleaner, BTSourceHeadwordCleanupResult (+9 more)

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

### Community 92 - ".ingest"
Cohesion: 0.15
Nodes (12): test_packaged_wright_source_path_is_readable(), parse_wright_sections_from_path(), Engine, Path, Session, sessionmaker, Parse Wright markdown from one filesystem path. Args: path: Markdown file…, Upsert Wright section text parsed from one markdown source file. Keyword Args:… (+4 more)

### Community 93 - ".parse"
Cohesion: 0.09
Nodes (14): Parse one source line into ``RawBTLine`` plus phase-02 metadata. Args:…, Classify one line into ``BTLineKind``. Args: body: Main ``@`` field body…, Detect whether a line is primarily a cross-reference. Args: body: Main ``@``…, Extract the POS prefix fragment immediately after the first headword. Args:…, Extract alternate headword spellings from the pre-POS plain-text prefix. Args:…, Apply display spelling normalization to variants with de-duplication. Args:…, Extract substitute target text from ``for X in Dict`` patterns. Args: body:…, Extract reference fragments listed after ``Dele`` markers. Args: body: Main… (+6 more)

### Community 95 - "required"
Cohesion: 0.11
Nodes (19): aliases, canonical_name, features, id, is_assignable, mapping_rationale, modern_class, paradigmatic_words (+11 more)

### Community 96 - "features"
Cohesion: 0.11
Nodes (19): citation_apa, retrieved_date, source_key, url, $defs, features, recognitionHints, source (+11 more)

### Community 97 - "DictionaryBuildStage"
Cohesion: 0.22
Nodes (6): DictionaryBuildStage, StrEnum, Stable stage labels emitted during one unified dictionary build., Mark one build stage active. Args: stage: Stage being entered. Keyword Args:…, Advance one build stage. Args: stage: Stage being advanced. Keyword Args:…, Mark one build stage complete. Args: stage: Stage that has completed.

### Community 98 - "test_generation_package_imports.py"
Cohesion: 0.25
Nodes (7): Regression test for the generation-package import-cycle fix.…, The package must not carry a facade re-export that recreates the cycle., The only import path any real caller uses must keep working., dispatch.py is the actual production entrypoint into the facade., test_dispatch_still_importable(), test_facade_still_importable_directly(), test_generation_package_does_not_reexport_facade()

### Community 99 - "Configuration: Command Line Tool guide"
Cohesion: 0.15
Nodes (18): wyrdcraeft settings CLI command doc, wyrdcraeft source convert CLI command doc, Configuration: Command Line Tool guide, wyrdcraeft FAQ, Standard JSON Representation for Old English Texts (schema spec), Installation guide, Quickstart guide, Using the Command Line Interface guide (+10 more)

### Community 100 - "DatabaseStartupRuntime"
Cohesion: 0.23
Nodes (20): _create_pre_alembic_forms_db(), _make_settings(), Path, test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(), test_fresh_missing_db_bootstraps_with_alembic_path(), test_interactive_blank_prompt_keeps_backup_without_retry(), test_interactive_prompt_matches_locked_wording_and_deletes_backup(), test_legacy_morphology_db_creates_fresh_canonical_db_with_real_migration() (+12 more)

### Community 101 - "20260706_01_parts_of_speech_and_dictionary_pos.py"
Cohesion: 0.16
Nodes (23): _assert_no_null_pos_ids(), _assert_no_null_text_pos(), downgrade(), _downgrade_bt_entries(), _downgrade_lemma_morph_classes(), _downgrade_morph_classes(), Connection, Replace legacy BT text POS and headword columns with normalized fields. Args:… (+15 more)

### Community 102 - "TestCLIVersion"
Cohesion: 0.25
Nodes (5): Test the version command., Test the version command displays version information., Test the version command with verbose flag., Test the version command with quiet flag., TestCLIVersion

### Community 103 - "OESyllableBreaker"
Cohesion: 0.16
Nodes (9): Syllable model for Old English syllable breaking., A syllable is a unit of speech that consists of an onset, nucleus, and coda., Syllable, OESyllableBreaker, Split consonant cluster between syllables using a conservative max-onset…, Insert dots before known suffixes to guide syllabification., Syllabify an Old English word conservatively., Break an Old English word into syllables. (+1 more)

### Community 104 - "._begin_connection"
Cohesion: 0.29
Nodes (5): Connection, Engine, Initialize the relinker from an existing SQLAlchemy bind. Args: connection:…, Yield an active SQLAlchemy connection for one relink operation. Returns:…, Clear every populated ``forms.entry_id`` before dictionary replacement.…

### Community 105 - "wyrdcraeft dictionary browse"
Cohesion: 0.23
Nodes (13): normalize_old_english(), BTSpellingNormalizer, DictionaryBrowseApp (Textual TUI), DictionaryBrowseQueryService, 12-tier headword/variant search ranking ladder, wyrdcraeft dictionary browse, wyrdcraeft dictionary build, parse_warnings.jsonl (+5 more)

### Community 106 - "TestCLIGlobalOptions"
Cohesion: 0.12
Nodes (9): Test JSON output format., Test text output format., Test invalid output format., Test global CLI options., Test verbose flag is properly set., Test quiet flag is properly set., Quiet mode should reset on next non-quiet CLI invocation., Test default output format is table. (+1 more)

### Community 107 - "properties"
Cohesion: 0.12
Nodes (16): type, uniqueItems, type, uniqueItems, type, uniqueItems, type, closed_class_examples (+8 more)

### Community 108 - "full_session"
Cohesion: 0.22
Nodes (9): FixtureRequest, fail_if_perl_subprocess_invoked(), full_session(), fixture, MonkeyPatch, Prepared session using the subset dictionary for default reference tests., Prepared session using the full dictionary for optional smoke checks., Fail fast if morphology tests attempt to execute Perl. (+1 more)

### Community 110 - "models/morphology.py"
Cohesion: 0.07
Nodes (38): SoundChangeSequenceEmitter, SoundManualContextEmitter, SoundManualEmitter, SoundSourceContextEmitter, SoundSourceFormEmitter, test_derive_sound_changed_forms_psinsg2_gst_chain(), test_derive_sound_changed_forms_psinsg2_ngst_chain(), test_derive_sound_changed_forms_psinsg3_td_th_chain() (+30 more)

### Community 111 - "catalog_db"
Cohesion: 0.29
Nodes (6): catalog_db(), fixture, Path, test_from_db_path_uses_isolated_database(), Path, Build a query service from one canonical SQLite database path. Args: db_path:…

### Community 112 - "BTQueryService"
Cohesion: 0.08
Nodes (37): corpus_index_db(), _index_fixture(), fixture, Path, Unit and integration tests for BTQueryService., sample_index_db(), _seed_forms_table(), test_bt_senses_round_trip_rich_fields() (+29 more)

### Community 113 - "_run_database_readiness_gate"
Cohesion: 0.13
Nodes (14): parametrize, test_should_run_database_readiness_gate(), _prompt_backup_cleanup(), Context, Run the canonical DB startup gate once for DB-using command trees. Args: ctx:…, Click group that preserves the raw argv for help-aware gate decisions. Side…, Persist the raw argv before delegating to Click's normal parser. Args: ctx:…, Return whether one top-level CLI command should trigger DB readiness. Args:… (+6 more)

### Community 114 - "cli/morphology.py"
Cohesion: 0.19
Nodes (14): clean_dictionary(), _default_morphology_data_dir(), _format_dictionary_join_text(), morphology_group(), command, group, option, Path (+6 more)

### Community 115 - "Implementation Slices"
Cohesion: 0.33
Nodes (6): Implementation Slices, Slice 1: consume visibility review, Slice 2: models and schema, Slice 3: parser and merge, Slice 4: query and CLI, Slice 5: rebuild and verify

### Community 117 - "GeneratorSession.load_all"
Cohesion: 0.17
Nodes (12): GeneratorSession (services.morphology), wyrdcraeft.models.morphology, GeneratorSession, LemmaMorphClassAssigner, MorphologyCatalogLoader, Morphology generation flow (concept), GeneratorSession.load_all(), LemmaMorphClassAssigner.assign_all() (+4 more)

### Community 118 - "wyrdcraeft 1.1.0 release (2026-03-02)"
Cohesion: 0.22
Nodes (13): GPalatalizer, MacronApplicator, wyrdcraeft.models.macron_index, wyrdcraeft 1.0.0 initial release (2026-03-01), wyrdcraeft 1.1.0 release (2026-03-02), wyrdcraeft source mark-diacritics, Diacritic restoration runtime processing flow, wyrdcraeft diacritic add (+5 more)

### Community 119 - "DictionaryCorpusSampler"
Cohesion: 0.14
Nodes (13): CorpusSampleResult, DictionaryCorpusSampler, main(), Path, Index source lines by lookup key while preserving source line order. Returns:…, Sample keys by deterministic every-Nth stratification. Args: ordered_keys: Keys…, Result of one corpus-sample build run. Attributes: keys: Selected lookup keys…, Collect all editorial siblings for sampled keys in corpus order. Args:… (+5 more)

### Community 120 - "diacritic.py"
Cohesion: 0.21
Nodes (15): diacritic_add(), diacritic_delete(), diacritic_group(), _load_macron_index_payload(), argument, command, group, option (+7 more)

### Community 122 - "Phase 2 — Lemma Morph Class Assignment"
Cohesion: 0.20
Nodes (10): Cleanup (optional same PR or follow-up), Phase 2 — Gate A: Spec review, Phase 2 — Gate B: Code review, Phase 2 — Lemma Morph Class Assignment, Phase 2 validation, Task 1: Schema + migration, Task 2: POS normalization helper, Task 3: Paradigm exemplar registry (+2 more)

### Community 123 - "main"
Cohesion: 0.23
Nodes (8): patch, Tests for the main module., Test the main function., Test that main function calls the CLI., Test that main function can be imported and called., Test that main function exists and is callable., TestMain, main()

### Community 124 - "Morphology Wright catalog — Phase 1 session (2026-07-04)"
Cohesion: 0.12
Nodes (17): 1. Circular import on full morphology test collection, 2. Untracked plan directory, 3. Package data, Branch and commits, Build integration, Commits this session (Phase 1 Tasks 1–4), Goal (locked design), Key files (+9 more)

### Community 125 - "Rule"
Cohesion: 0.33
Nodes (5): TContext_contra, TWord_contra, Ordered classification rule for paradigm assignment., Return matched paradigm labels for ``word`` in ``context``. Note: Paradigm…, Rule

### Community 126 - "TestCLIErrorHandling"
Cohesion: 0.33
Nodes (4): Test CLI error handling., Test CLI without arguments shows help., Test invalid command shows error., TestCLIErrorHandling

### Community 127 - "DictionaryPosInferer"
Cohesion: 0.20
Nodes (12): PosInferenceCancelCheck, PosInferenceProgress, PosInferenceWarningSink, DictionaryPosInferer, Connection, Attempt one inferred POS update, skipping duplicate and homograph rows. Args:…, Unwrap one SQLAlchemy connection to the underlying SQLite driver. Args:…, Resolve the seeded ``unknown`` part-of-speech identifier. Args: connection:… (+4 more)

### Community 128 - "TestConsoleQuietMode"
Cohesion: 0.33
Nodes (4): Test console quiet mode functionality., Test that console can be set to quiet mode., Test that stderr console can be set to quiet mode., TestConsoleQuietMode

### Community 129 - "TestCLISettings"
Cohesion: 0.17
Nodes (7): Test the settings command., Test the settings command with table output., Test the settings command with JSON output., Test the settings command with text output., Test the settings command with verbose flag., Test the settings command with custom config file., TestCLISettings

### Community 130 - "DocumentIngestor"
Cohesion: 0.22
Nodes (9): DocumentIngestor, HeuristicDocumentIngestor, LLMDocumentIngestor, TEIDocumentIngestor, wyrdcraeft.models.source_text (OldEnglishText JSON schema), Germanic Lexicon Project (Bosworth-Toller OCR source), github:madeleineth/tichy_oe_generator, Tichý, Morphological analyser of old english (2017) (+1 more)

### Community 131 - ".on_key"
Cohesion: 0.40
Nodes (3): Key, Accept Old English keyboard characters at app level as a terminal fallback.…, Accept OE key aliases before Textual's default printable-key handling. Args:…

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

### Community 142 - "MorphologySetupStep"
Cohesion: 0.40
Nodes (4): MorphologySetupStep, StrEnum, Stable setup-step labels for pre-generation morphology work. Note: Cross-PoS…, Advance setup progress for one completed startup step. Args: step: Setup step…

### Community 143 - ".__init__"
Cohesion: 0.50
Nodes (3): DictionaryBuildEventSink, Event, Initialize the build pipeline for one canonical database. Args: db_path: Path…

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

### Community 148 - "catalog_db"
Cohesion: 0.50
Nodes (4): catalog_db(), fixture, Path, test_parse_wright_sections_from_path()

### Community 149 - "test_corpus_sample.py"
Cohesion: 0.33
Nodes (6): _load_manifest(), Smoke tests for the stratified Bosworth-Toller corpus sample fixture., Ensure corpus fixture is present and within phase-02b size constraints., Parse every corpus line and require deterministic parse or explicit skip., test_corpus_sample_lines_parse_without_raising(), test_corpus_sample_manifest_and_line_count_bounds()

### Community 150 - "DatabaseMigrationError"
Cohesion: 0.16
Nodes (11): Path, test_legacy_bootstrap_failure_restores_cleanly_and_raises_typed_error(), test_legacy_morphology_db_is_backed_up_then_requires_rebuild(), DatabaseMigrationError, LegacyDatabaseResetRequired, datetime, RuntimeError, Legacy database reset stop signal with rebuild guidance. Args: backup_path:… (+3 more)

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
Cohesion: 0.25
Nodes (7): FormEmitter, ParadigmAssigner, FormOutput, Protocol, Session-level assigner contract., Form emission contract., Emit one normalized form record to ``output``. Note: Form realization follows…

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

### Community 165 - "generate_reference_snapshots"
Cohesion: 0.17
Nodes (16): build_session(), canonical_sort_rows(), canonicalize_form_rows(), generate_reference_snapshots(), paradigm_snapshot_rows(), preprocess_snapshot_rows(), Any, Path (+8 more)

### Community 166 - "wyrdcraeft Context"
Cohesion: 0.15
Nodes (13): ADRs, Boundary, Canonical Terms, Capability Map, Context Docs, Current Migration Progress, Dictionary browse, Dictionary indexing (+5 more)

### Community 167 - "20260630_01_initial_canonical_schema.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop the initial canonical schema. Side Effects: Removes the initial product…, Create the canonical morphology, dictionary, and lexicon tables. Side Effects:…, upgrade()

### Community 168 - "20260703_01_add_normalized_title_columns.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add normalized_title columns to morphology and dictionary source tables. Side…, Remove normalized_title columns and lookup indexes. Side Effects: Drops…, upgrade()

### Community 169 - "20260704_01_morph_catalog_tables.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop morphology catalog reference and junction tables. Side Effects: Removes…, Create morphology catalog reference and junction tables. Side Effects: Adds…, upgrade()

### Community 170 - "20260704_02_lemma_morph_classes.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add recognition hints to morph classes and create lemma assignment table. Side…, Drop lemma assignment table and recognition hints column. Side Effects: Removes…, upgrade()

### Community 171 - "20260706_02_forms_foreign_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add nullable foreign-key columns to ``forms``. Side Effects: Adds…, Remove nullable foreign-key columns from ``forms``. Side Effects: Drops…, upgrade()

### Community 172 - "20260706_03_lexicon_shrink_search_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Restore lexicon projection tables and legacy search table names. Side Effects:…, Rename search tables and drop lexicon projection tables. Side Effects: Renames…, upgrade()

### Community 173 - "20260706_04_drop_forms_legacy_strings.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop legacy denormalized string columns from ``forms``. Side Effects: Removes…, Restore legacy denormalized string columns on ``forms``. Side Effects: Re-adds…, upgrade()

### Community 174 - "20260707_01_drop_search_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop legacy lexicon search-index tables from the canonical schema. Side…, Recreate empty legacy lexicon search-index tables. Side Effects: Restores empty…, upgrade()

### Community 175 - "20260707_02_bt_senses_entry_order_index.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add index supporting ordered sense lookup by dictionary entry. Side Effects:…, Remove ordered lookup index for dictionary sense reads. Side Effects: Drops the…, upgrade()

### Community 176 - "20260707_03_bt_source_blocks_and_rich_senses.py"
Cohesion: 0.40
Nodes (4): downgrade(), Restore homograph uniqueness and remove rich sense metadata columns. Side…, Drop homograph uniqueness and add source-block sense metadata columns. Side…, upgrade()

### Community 177 - "create_session_factory"
Cohesion: 0.50
Nodes (4): create_session_factory(), Session, sessionmaker, Build one SQLAlchemy session factory for the canonical SQLite database. Args:…

### Community 178 - "_entry_to_dict"
Cohesion: 0.67
Nodes (3): _entry_to_dict(), Serialize one consolidated entry for JSON CLI output. Args: entry: Consolidated…, Serialize one consolidated entry for JSON CLI output. Args: entry: Consolidated…

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

### Community 187 - ".swap_bt_diphthong_long_marks"
Cohesion: 0.40
Nodes (3): Match, Rewrite BT second-vowel long-mark diphthongs to first-vowel long marks. Note:…, Compose one corrected diphthong while preserving source case pattern. Args:…

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

### Community 220 - "MorphBuildOptions"
Cohesion: 0.23
Nodes (20): build_pipeline_db(), _fetch_entry_id(), _fetch_entry_pos(), _fetch_form_entry_id(), _insert_form(), _pos_id(), Connection, fixture (+12 more)

### Community 221 - "Phase B — Forms Foreign Keys (Legacy Strings Remain)"
Cohesion: 0.18
Nodes (11): Phase B — Commit, Phase B — Forms Foreign Keys (Legacy Strings Remain), Phase B — Gate A: Spec review checklist, Phase B — Gate B: Code review checklist, Phase B validation, Task 1: Alembic migration `20260706_02`, Task 2: Form FK resolver service, Task 3: Sink propagation (+3 more)

### Community 223 - "Phase 2 — Wright § Text Ingest Report"
Cohesion: 0.14
Nodes (13): Wright § markdown text ingest into wright_sections.section_text, Files changed, Implementation notes, Manual spot-check, Phase 2 — Wright § Text Ingest Report, Self-review, Summary, Task 2.1 — Markdown § parser (+5 more)

### Community 224 - "0007-ocr-pipeline-moves-to-bochord.md"
Cohesion: 0.18
Nodes (7): BT OCR parsing starts with lossless source-grounded AST, BT source acquisition uses a multi-witness download set, BT JP2 witness preparation is library-first, Consequence, Not removed, OCR pipeline moves to bochord, Removed from wyrdcraeft

### Community 226 - "default_bt_source_path"
Cohesion: 0.22
Nodes (12): main(), Build the packaged macron index from the bundled Bosworth-Toller source., default_bt_abbreviations_path(), default_bt_source_path(), default_wright_source_path(), _packaged_dictionary_path(), Path, Resolve packaged Bosworth-Toller dictionary source file paths. (+4 more)

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

### Community 248 - "Orchestrator Checkpoint"
Cohesion: 0.29
Nodes (6): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase status, Resume here

### Community 249 - "FormSink"
Cohesion: 0.40
Nodes (4): FormSink, Protocol, Sink contract for finalized emitted form rows., Consume finalized form rows in emitted order. Note: Emitted row semantics…

### Community 250 - ".__init__"
Cohesion: 0.29
Nodes (4): Path, Initialize a SQLAlchemy sink for emitted morphology rows. Note: Index schema…, Ensure the canonical ``forms`` table and its indexes exist., Tune SQLite for bulk morphology index writes. Side Effects: Sets WAL mode and…

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

### Community 272 - "CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}"
Cohesion: 0.50
Nodes (4): A. THE VOWELS, B. THE CONSONANTS, CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}, STRESS (ACCENT)

### Community 273 - "CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}"
Cohesion: 0.50
Nodes (4): CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}, The Liquids, The Nasals, The Semivowels

### Community 275 - "FormWriter"
Cohesion: 0.20
Nodes (7): FormWriter, Any, Minimal writer protocol used by morphology emitters., Write text to the underlying output stream., Emit one legacy form payload using parity row semantics. Note: Linguistic…, TextIO, Initialize a parity TSV sink. Note: TSV row layout is aligned with outputs…

## Ambiguous Edges - Review These
- `task-phase1-morph-class-browse-report.md` → `task-phase2-wright-text-ingest-report.md`  [AMBIGUOUS]
  doc/sessions/task-phase2-wright-text-ingest-report.md · relation: references
- `The Seafarer (Old English poem, test fixture)` → `Old English Bosworth-Toller Dictionary Text`  [AMBIGUOUS]
  tests/fixtures/seafarer.txt · relation: conceptually_related_to

## Knowledge Gaps
- **876 isolated node(s):** `release.sh script`, `wyrdcraeft`, `IPA_AUDIO`, `$schema`, `$id` (+871 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `task-phase1-morph-class-browse-report.md` and `task-phase2-wright-text-ingest-report.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `The Seafarer (Old English poem, test fixture)` and `Old English Bosworth-Toller Dictionary Text`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Word` connect `Word` to `._resolve_class_key`, `runtime.py`, `adj_forms.py`, `ParadigmClassMapper`, `strong_derivation_flow.py`, `weak_principal_flow.py`, `GeneratorSession`, `noun_forms.py`, `common.py`, `processors.py`, `models/morphology.py`, `test_generation_branches.py`, `VerbFormGenerator`, `wright_audit.py`, `models/__init__.py`, `morphology/loaders.py`, `session.py`, `weak_derivation_flow.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `GeneratorSession` connect `GeneratorSession` to `morphology/test_query_service.py`, `MorphologyGenerateProgressCoordinator`, `noun_forms.py`, `common.py`, `processors.py`, `VerbFormGenerator`, `test_generation_branches.py`, `MorphologySetupStep`, `session.py`, `FormWriter`, `form_rows.py`, `FormEmitter`, `Word`, `adj_forms.py`, `generate_reference_snapshots`, `read_jsonl_gz`, `morphology/loaders.py`, `markup.py`, `.__init__`, `full_session`, `Rule`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `TestCLISettings`, `runtime.py`, `MorphologyGenerateProgressCoordinator`, `.settings_customise_sources`, `upgrade_canonical_db`, `DatabaseMigrationError`, `tests/conftest.py`, `cli/dictionary.py`, `ingest/pipeline.py`, `cli`, `test_pipeline_classes.py`, `cli.py`, `AnyLLMConfig`, `LLMDocumentIngestor`, `DatabaseStartupRuntime`, `TestCLIVersion`, `TestCLIGlobalOptions`, `_run_database_readiness_gate`, `TestCLIErrorHandling`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GeneratorSession` (e.g. with `MorphologyBuildRunnerError` and `FormEmitter`) actually correct?**
  _`GeneratorSession` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `Word` (e.g. with `_NounAssignedIndex` and `AssignmentResult`) actually correct?**
  _`Word` has 22 INFERRED edges - model-reasoned connections that need verification._