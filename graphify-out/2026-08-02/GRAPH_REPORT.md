# Graph Report - remove-ocr-pipeline  (2026-08-01)

## Corpus Check
- 361 files · ~5,528,084 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6505 nodes · 13589 edges · 295 communities (261 shown, 34 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 985 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `120c22b3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- services/dictionary/__init__.py
- BTSenseSegmenter
- DictionaryBuildPipeline
- PartOfSpeech
- morphology/test_query_service.py
- ParadigmClassMapper
- ParsedBTLine
- MorphologyGenerateProgressCoordinator
- form_decode.py
- noun_forms.py
- BTSqliteSink
- common.py
- browse_tui.py
- test_bt_witness_prep_quality.py
- VerbFormGenerator
- test_generation_branches.py
- BTAttestationStripper
- Settings
- weak_inflections.py
- session.py
- test_browse_tui.py
- DictionaryBrowseQueryService
- test_bt_witness_prep_validation.py
- form_rows.py
- test_markup.py
- tests/conftest.py
- weak_derivation_flow.py
- cli/dictionary.py
- server.py
- diacritic_disambiguate.py
- ensure_parts_of_speech
- OldEnglishText
- RawBlock
- Word
- MorphologyCatalogLoader
- adj_forms.py
- strong_derivation_flow.py
- etymology_display.py
- weak_principal_flow.py
- SenseMetadataClassifier
- BTTile
- test_cli_ocr_bosworth_toller.py
- TextMetadata
- BTSourceBlockBuilder
- bt_witness_prep/pipeline.py
- old_english_pipeline.py
- NormalizedTitleJoinIndex
- WrightAuditService
- wright-morphology-fixture.schema.json
- cli
- strong_principal_flow.py
- models/__init__.py
- BTPreprocessedPage
- utils.py
- morphology-wright-catalog/README.md
- test_morph_class_browse.py
- properties
- properties
- FormsEntryRelinker
- test_morph_catalog_pos.py
- test_cli_dictionary.py
- test_loaders.py
- LLMExtractor
- check_napoleon_gate.py
- Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅
- BackupStateStore
- test_index_pipeline.py
- test_line_parser.py
- PHONOLOGY
- browse_query.py
- AnyLLMConfig
- test_bt_tile_ocr.py
- GeneratorSession
- test_text_utils_reference.py
- db/runtime.py
- BTPosGenderExtractor
- enum
- MorphologyDictionaryCleaner
- create_engine
- TEIExporter
- print_info
- BT V2 Parser And Schema Migration
- properties
- BTSourceHeadwordCleaner
- ocr_proxy/runtime.py
- Orchestration Guide
- Execution order
- Orchestration Guide
- type
- Orchestration Guide
- Lexicon Architecture Docs Design
- OCR pipeline test-fixture corpus (Wright's Grammar pages)
- test_wright_section_text.py
- .parse
- required
- features
- test_schema.py
- test_paths.py
- Configuration: Command Line Tool guide
- DatabaseStartupRuntime
- 20260706_01_parts_of_speech_and_dictionary_pos.py
- test_lemma_morph_assignment.py
- OESyllableBreaker
- i-umlaut (sound change)
- wyrdcraeft dictionary browse
- test_cli_commands.py
- properties
- full_session
- normalized-canonical-schema/README.md
- sound_dispatch_flow.py
- lexicon/conftest.py
- BTQueryService
- cli.py
- cli/morphology.py
- Wright, An Old English Grammar (source text)
- Bosworth-Toller Anglo-Saxon Dictionary (source text)
- GeneratorSession.load_all
- wyrdcraeft 1.1.0 release (2026-03-02)
- default_bt_source_path
- normalize_old_english
- Morphology build performance session (2026-07-03)
- Phase 2 — Lemma Morph Class Assignment
- main
- Morphology Wright catalog — Phase 1 session (2026-07-04)
- QueryFormRow
- BT OCR witness preparation slice (bt_witness_prep)
- pos_inference.py
- .focus_search
- TestCLISettings
- DocumentIngestor
- .on_key
- enum
- BTIndexPipeline
- examples
- enum
- enum
- print_error
- cli/settings.py
- query
- enum
- enum
- test_attach_morphology_db.py
- wright_phonology8.md (Grimm's Law / Verner's Law OCR fixture)
- BTTileQualityScorer
- Wyrdcraeft Canonical DB Migration Implementation Plan
- format_wright_audit_text
- test_prompt_regression.py
- wright_phonology7.md (ablaut / vowel gradation OCR fixture)
- test_corpus_sample.py
- DatabaseMigrationError
- source_keys
- resolve_dictionary_db_path
- enum
- enum
- enum
- parent_id
- build_runner.py
- Task 1: Define Build Event Models
- wright_sections
- Morphology Wright Catalog — Design Decisions
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
- .write_json
- normalize_morphology_title
- .resolve_sense_path
- Phase A — Reference Tables and Dictionary POS FKs
- Phase B — Dictionary Browse, Search, and CLI Consolidation
- Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns
- .on_input_changed
- create_dict31.pl (legacy Perl morphology generator)
- BTQueryService
- Python coding standards
- .normalize_bt_display_spelling
- BT Structural Visibility Review
- wyrdcraeft
- ._no_mixed_prose_and_verse
- Phase D — Drop Legacy Form String Columns
- LemmaMorphClassAssigner
- Phase A — Unified Dictionary Build
- quality/README.md
- OESyllableBreaker
- tests/dictionary/__init__.py
- lexicon/__init__.py
- tests/morphology/__init__.py
- alembic/__init__.py
- versions/__init__.py
- Morphology Context
- Phase 3 — Browse Wright § text pane
- ocr_proxy/__init__.py
- CPalatalizer
- OENormalizer
- wyrdcraeft.models.llm
- wyrdcraeft.models.parsing
- SqliteIndexSink
- wright_phonology9.pdf (scanned page image, no md pair)
- Global Constraints
- Lexicon Browser BT V2 Adaptation Skeleton
- Orchestration: Wyrdcraeft Canonical DB Migration
- Morph Class Browse And Audit Design
- test_build_pipeline.py
- Phase B — Forms Foreign Keys (Legacy Strings Remain)
- Phase C — Lexicon Shrink (Search Index Only)
- Phase 2 — Wright § Text Ingest Report
- 0007-ocr-pipeline-moves-to-bochord.md
- source_db.py
- .build_index_from_bt
- AGENTS.md
- Contributor Covenant 3.0
- Morphology Wright Catalog — Phased Implementation Plan
- Normalized Canonical Schema — Phased Implementation Plan
- Phase 1 — Reference Catalog Tables
- Phase 4 — Wright Section Text Ingest
- Morph Class Browse Surfacing + Wright Audit — Implementation Plan
- BT Usage-vs-Sense Cleanup Handoff
- TestEntryGenderPromotion
- ._load_entry
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
- Session: Morphology Wright Catalog — Phase 2 complete
- Orchestrator Checkpoint
- FormSink
- .__init__
- generate_golden_merged.py
- Wright OE Grammar §§70-92 (i-umlaut, breaking, palatalization of vowels)
- Domain Docs
- normalized_title + lexicon browse — checkpoint 2026-07-03T12:15
- Mission: Machine Assistance For Old English Work
- Mission: Historical Linguistics for Old English Study
- CHAPTER IV: THE OLD ENGLISH DEVELOPMENT OF THE PRIM. GERMANIC VOWELS OF ACCENTED SYLLABLES {#chapter-4}
- A. The Short Vowels of Accented Syllables
- Wright & Wright (1908), "Old English Grammar", Oxford University Press
- Phase 1 Morph-Class Browse Report
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
- _format_entry_text
- CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}
- CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}
- ._on_paste
- .__init__
- release.sh
- 0002-canonical-morphology-db-uses-startup-alembic-migrations.md
- 0003-bt-entry-identity-follows-source-blocks.md
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
- .max_line_no
- wyrdcraeft

## God Nodes (most connected - your core abstractions)
1. `GeneratorSession` - 176 edges
2. `Word` - 164 edges
3. `cli()` - 126 edges
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
- 3-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/form_rows.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 3-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/common.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/adj_forms.py -> wyrdcraeft/services/morphology/generation/form_rows.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/adv_forms.py -> wyrdcraeft/services/morphology/generation/form_rows.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/common.py -> wyrdcraeft/services/morphology/generation/form_rows.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/noun_forms.py -> wyrdcraeft/services/morphology/generation/form_rows.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/num_forms.py -> wyrdcraeft/services/morphology/generation/form_rows.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/common.py -> wyrdcraeft/services/morphology/generation/strong_principal_flow.py -> wyrdcraeft/services/morphology/generation/__init__.py`
- 4-file cycle: `wyrdcraeft/services/morphology/generation/__init__.py -> wyrdcraeft/services/morphology/generation/facade.py -> wyrdcraeft/services/morphology/generation/common.py -> wyrdcraeft/services/morphology/generation/weak_principal_flow.py -> wyrdcraeft/services/morphology/generation/__init__.py`

## Hyperedges (group relationships)
- **Wright morph catalog: four-phase implementation (reference catalog -> lemma assignment -> forms link -> Wright text ingest)** — doc_plans_morphology_wright_catalog_phase_1_reference_catalog, doc_plans_morphology_wright_catalog_phase_2_lemma_assignment, doc_plans_morphology_wright_catalog_phase_3_forms_link_and_query, doc_plans_morphology_wright_catalog_phase_4_wright_section_text_ingest [EXTRACTED 1.00]
- **Normalized canonical schema: four sequential phases A-D (reference/dictionary FKs -> forms FKs -> lexicon shrink -> legacy column drop)** — doc_plans_normalized_canonical_schema_phase_a_reference_and_dictionary, doc_plans_normalized_canonical_schema_phase_b_forms_foreign_keys, doc_plans_normalized_canonical_schema_phase_c_lexicon_shrink, doc_plans_normalized_canonical_schema_phase_d_legacy_column_drop [EXTRACTED 1.00]
- **Subagent task reports implementing Wright catalog browse/ingest/audit phases** — doc_sessions_task_phase1_morph_class_browse_report, doc_sessions_task_phase2_wright_text_ingest_report, doc_sessions_task_phase3_wright_text_pane_report, doc_sessions_task_phase4_wright_audit_report [INFERRED 0.85]
- **Dictionary build pipeline stage sequence** — doc_source_architecture_dictionary_btlineparser, doc_source_architecture_dictionary_btsensesegmenter, doc_source_architecture_dictionary_bteditorialmerger, doc_source_architecture_dictionary_btsqlitesink, doc_source_architecture_dictionary_formsentryrelinker [EXTRACTED 1.00]
- **BT witness prep pipeline collaborator chain** — doc_source_overview_bt_ocr_witness_preparation_method_enumerator, doc_source_overview_bt_ocr_witness_preparation_method_preprocessor, doc_source_overview_bt_ocr_witness_preparation_method_tiler, doc_source_overview_bt_ocr_witness_preparation_method_qualityscorer, doc_source_overview_bt_ocr_witness_preparation_method_manifestwriter, doc_source_overview_bt_ocr_witness_preparation_method_anchorseedbuilder [EXTRACTED 1.00]
- **Morphology build stage-ordering (catalog seed, class assign, form emission)** — doc_source_architecture_morphology_generatorsession, doc_source_architecture_morphology_morphologycatalogloader, doc_source_architecture_morphology_lemmamorphclassassigner, doc_source_architecture_morphology_sqliteindexsink [EXTRACTED 1.00]
- **wyrdcraeft CLI configuration documentation cluster** — doc_source_overview_configuration_cli_configuration_guide, doc_source_overview_using_cli_cli_usage_guide, doc_source_overview_command_settings_settings_command [INFERRED 0.75]
- **Bosworth-Toller dictionary processing pipeline (source, runbooks, fixture)** — doc_source_runbook_bt_dictionary_structuring_workflow_bt_structuring_workflow, doc_source_runbook_macron_list_generation_macron_list_generation, tests_fixtures_dictionary_corpus_sample_bt_corpus_sample_fixture [INFERRED 0.75]
- **BT witness-prep test fixture corpus (readme + notes + transcriptions)** — tests_fixtures_ocr_bt_witness_prep_readme_md, tests_fixtures_ocr_bt_witness_prep_notes_txt, tests_fixtures_ocr_bt_witness_prep_transcriptions_bt_0002_standard_dense_txt, tests_fixtures_ocr_bt_witness_prep_transcriptions_bt_0007_standard_dense_txt, tests_fixtures_ocr_bt_witness_prep_transcriptions_bt_0010_standard_dense_txt [EXTRACTED 1.00]
- **Wright grammar chapters covering umlaut and vowel sound-change (Ch. IV/V material)** — tests_fixtures_ocr_wright2_md, tests_fixtures_ocr_wright5_md, tests_fixtures_ocr_wright_germanic_vowels_md, tests_fixtures_ocr_wright_markup_md [INFERRED 0.85]
- **Wright's Grammar noun-declension OCR test series (nouns.md/pdf through nouns10.md/pdf)** — tests_fixtures_ocr_wright_nouns_md, tests_fixtures_ocr_wright_nouns2_md, tests_fixtures_ocr_wright_nouns9_md, tests_fixtures_ocr_wright_nouns10_md [INFERRED 0.75]
- **Umlaut phenomena described together (i-umlaut, u/o-a-umlaut, breaking) across Wright fixtures** — concept_i_umlaut, concept_u_o_a_umlaut, concept_breaking [EXTRACTED 1.00]
- **Germanic consonant-shift laws treated as a set (Grimm's Law, Verner's Law, ablaut context)** — concept_grimms_law, concept_verners_law, concept_ablaut [INFERRED 0.75]
- **Wright grammar authored by Joseph & Elizabeth Wright, drawing on Bosworth-Toller as a cited dictionary source** — concept_wright_old_english_grammar, concept_joseph_wright, concept_bosworth_toller_dictionary [EXTRACTED 1.00]
- **Morphological Paradigm Generation Data Set** — wyrdcraeft_etc_morphology_dict_adj_vb_part_num_adv_noun, wyrdcraeft_etc_morphology_manual_forms, wyrdcraeft_etc_morphology_para_vb [INFERRED 0.75]
- **Prose Prompt Layering (general -> base mode -> model override)** — wyrdcraeft_prompts_general, wyrdcraeft_prompts_prose, wyrdcraeft_prompts_models_gemini_prose [INFERRED 0.85]
- **c/g Palatalization Exception Lists** — wyrdcraeft_etc_diacritic_c_palatalization_force_non_palatalize, wyrdcraeft_etc_diacritic_c_palatalization_force_palatalize, wyrdcraeft_etc_diacritic_g_frontal [INFERRED 0.85]

## Communities (295 total, 34 thin omitted)

### Community 0 - "services/dictionary/__init__.py"
Cohesion: 0.06
Nodes (50): Client, _parsed_line(), BTSense, Path, Tests for optional Bosworth-Toller LLM parse repair., test_apply_fixes_keeps_deterministic_line_on_validation_failure(), test_apply_fixes_patches_only_warning_lines(), test_extract_json_object_from_fenced_response() (+42 more)

### Community 1 - "BTSenseSegmenter"
Cohesion: 0.03
Nodes (78): _golden_sense_matches(), _load_golden(), fixture, Tests for Phase 03 BTSenseSegmenter., Arabic display labels for canonical sense paths., Unit tests for specific segmenter behaviours., Body with no sense labels produces a single unlabelled sense., Bold <B>I.</B>/<B>II.</B> labels produce two ordered senses. (+70 more)

### Community 2 - "DictionaryBuildPipeline"
Cohesion: 0.05
Nodes (71): AnyDictionaryBuildEvent, DictionaryBuildEventSink, DictionaryBuildLogLevel, DictionaryBuildStatus, Event, MonkeyPatch, Path, test_dictionary_build_pipeline_ensures_schema_and_rebuilds_dictionary_on_empty_db() (+63 more)

### Community 3 - "PartOfSpeech"
Cohesion: 0.06
Nodes (76): DeclarativeBase, test_format_morph_class_display_label_falls_back_to_canonical_name(), test_format_morph_class_display_label_prefers_compact_modern_label(), Alembic environment for the canonical wyrdcraeft SQLite database., Run Alembic migrations without a live database connection. Side Effects:…, Run Alembic migrations with a live SQLAlchemy connection. Side Effects: Opens a…, run_migrations_offline(), run_migrations_online() (+68 more)

### Community 4 - "morphology/test_query_service.py"
Cohesion: 0.08
Nodes (50): _build_output_sink(), Build the output sink used while profiling adjective generation. Keyword Args:…, TemporaryDirectory, _form_row(), _index_dictionary(), _insert_bt_entry(), _insert_bt_variant(), Connection (+42 more)

### Community 5 - "ParadigmClassMapper"
Cohesion: 0.05
Nodes (42): mapper(), fixture, Tests for Wright catalog paradigm exemplar mapping., test_adj_paradigm_blind_maps_to_strong_a_o_stem(), test_noun_paradigm_guma_maps_to_weak_n_stem(), test_noun_paradigm_stan_maps_to_masculine_a_stem(), test_past_participle_title_maps_to_past_participle_class(), test_present_participle_title_maps_to_present_participle_class() (+34 more)

### Community 6 - "ParsedBTLine"
Cohesion: 0.04
Nodes (87): _entry_to_comparable(), _load_golden(), merger(), _parse_lines(), parser(), fixture, parametrize, Tests for Phase 04 BTEditorialMerger and BTTargetResolver. (+79 more)

### Community 7 - "MorphologyGenerateProgressCoordinator"
Cohesion: 0.04
Nodes (55): test_build_profiler_disabled_emits_nothing(), test_build_profiler_emits_stage_and_sqlite_sections(), test_progress_coordinator_omits_empty_wright_and_throttles_lemma(), test_progress_coordinator_stage_totals(), MorphologyBuildProfiler, TextIO, Wall-clock profiling helpers for morphology build runs., Finish wall-clock timing for one generation stage. Args: stage: Stage being… (+47 more)

### Community 8 - "form_decode.py"
Cohesion: 0.04
Nodes (95): MorphologyTableInputRow, Tests for morphology function-code decoding., test_build_adjective_sidebar_uses_payload_inflection(), test_build_adverb_sidebar_decodes_superlative_su_code(), test_build_morphology_table_fills_inflection_from_morph_class_label(), test_build_morphology_table_includes_surface_form_column(), test_build_morphology_table_sorts_adjectives_by_degree_inflection_and_case(), test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms() (+87 more)

### Community 9 - "noun_forms.py"
Cohesion: 0.05
Nodes (75): _build_stem_ar_pl(), _build_stem_ar_sg_ge_da(), _build_stem_ar_sg_no_ac(), _build_stem_daeg_pl(), _build_stem_geminate(), _build_stem_hof_ge_da(), _build_stem_pl_ge_da(), _build_stem_pl_no_ac() (+67 more)

### Community 10 - "BTSqliteSink"
Cohesion: 0.09
Nodes (25): test_pipeline_without_llm_fix_pass_unchanged(), Path, Focused tests for the normalized Bosworth-Toller SQLite sink., _run_index(), _seed_forms_table(), test_bt_entries_allow_duplicate_norm_key_pos(), test_sink_persists_headword_with_normalized_pos_fk(), test_sink_rerun_reuses_seeded_parts_of_speech_rows() (+17 more)

### Community 11 - "common.py"
Cohesion: 0.04
Nodes (82): PartDispatcher, PartProcessor, PartStemSegmentDeriver, StrongPartGenerator, VariantDispatcher, VariantProcessor, WeakPartGenerator, GeneratedForm (+74 more)

### Community 12 - "browse_tui.py"
Cohesion: 0.03
Nodes (95): ComposeResult, Input, ListItem, Selected, Static, test_format_entry_details_omits_plain_wright_line_for_selectable_sections(), test_format_entry_details_shows_unclassified_for_missing_assignment(), test_format_entry_details_shows_unclassified_for_unmappable_pos() (+87 more)

### Community 13 - "test_bt_witness_prep_quality.py"
Cohesion: 0.09
Nodes (59): _draw_horizontal_bars(), _draw_small_dots(), _gray_array(), _image_from_array(), Prove composite cap fires when other metrics would otherwise mask loss., _score_context(), _scorer(), test_bt_tile_quality_to_dict_includes_metric_fields() (+51 more)

### Community 14 - "VerbFormGenerator"
Cohesion: 0.03
Nodes (36): Emit one weak ``PsInSg2``-branch form row with simplified post-vowel. Side…, Emit one weak ``PsInSg2`` sound-change branch with simplified post-vowel. Side…, Matches Perl's generate_strong_verb_parts. Notes: Matches Perl implementation…, Generate strong verbs derived from inf. Notes: Matches Perl implementation of…, Generator for Old English verb forms. Args: session: The session. output_file:…, Matches Perl's generate_and_print_form_with_sound_changes. Notes: Matches Perl…, Matches Perl's generate_and_print_manual. Args: formhash: The form hash. form:…, Attach a present participle emitted from a weak principal-part row. Side… (+28 more)

### Community 15 - "test_generation_branches.py"
Cohesion: 0.05
Nodes (80): SoundManualEmitter, SoundSourceFormEmitter, StrongBranchAction, StrongDerivedEmitter, StrongFormEmitter, StrongParticipleSink, StrongSoundEmitter, _base_formhash() (+72 more)

### Community 16 - "BTAttestationStripper"
Cohesion: 0.04
Nodes (50): fixture, parametrize, Tests for Phase 03 BTAttestationStripper., ``_is_citation_span`` returns True for grammar/editorial markers and citations., ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes., ``_strip_editorial_directive`` removes leading supplement editorial verbs., Unit tests for BTAttestationStripper.strip., ``:--`` is the canonical attestation separator. (+42 more)

### Community 17 - "Settings"
Cohesion: 0.04
Nodes (44): BaseSettings, Exception, PydanticBaseSettingsSource, patch, Unit tests for configuration settings. Tests the new OpenAI and summary…, Test that model_config is properly configured., Test output format validation., Test valid output format validation. (+36 more)

### Community 18 - "weak_inflections.py"
Cohesion: 0.04
Nodes (71): test_dispatch_weak_derived_forms_selects_psinsg2_branch(), test_dispatch_weak_derived_forms_skips_item_shape_mode(), test_dispatch_weak_principal_part_derivations_emits_papt_only(), test_emit_weak_derived_from_inf_by_class2_general_branch(), test_emit_weak_derived_from_inf_by_class2_two_uses_general_path(), test_emit_weak_derived_from_inf_sequence_normalizes_none_probability(), test_emit_weak_derived_from_painsg1_sequence_uses_preterite_order(), test_emit_weak_derived_from_painsg1_variant_sequence() (+63 more)

### Community 19 - "session.py"
Cohesion: 0.07
Nodes (82): morphology, morphology_full, Namespace, main(), _mypy_baseline(), _runtime_baseline_ms(), _sha256_rows(), _stage_rows() (+74 more)

### Community 20 - "test_browse_tui.py"
Cohesion: 0.08
Nodes (67): anyio, _bt_entry_id(), _collect_widget_ids(), _details_text(), empty_browse_db(), _insert_entry(), _insert_inflection_code(), lexicon_source_db() (+59 more)

### Community 21 - "DictionaryBrowseQueryService"
Cohesion: 0.13
Nodes (30): _bt_entry_id(), _insert_bt_sense(), _insert_entry(), _insert_inflection_code(), lexicon_source_db(), _next_entry_order(), _pos_id(), Connection (+22 more)

### Community 22 - "test_bt_witness_prep_validation.py"
Cohesion: 0.07
Nodes (56): test_discover_candidate_tile_images_falls_back_to_whole_page(), test_discover_candidate_tile_images_uses_reading_order(), test_materialize_baseline_pages_uses_manifest_source_filename(), test_run_benchmark_live_arms_use_distinct_image_inputs(), _write_png(), manifest(), test_diacritic_sensitive_cer_is_zero_for_identical_text(), test_diacritic_sensitive_cer_penalizes_diacritic_substitutions() (+48 more)

### Community 23 - "form_rows.py"
Cohesion: 0.06
Nodes (47): generate_vbforms(), output_manual_forms(), FormOutput, Initialize the verb-form generator context. Args: session: Active generation…, Wrapper for VerbFormGenerator. Args: session: The session. output_file: The…, Output manual forms to the output file. Perl load_forms prints each form to…, Human-centric external facade for morphology generation entrypoints., assemble_form_parts() (+39 more)

### Community 24 - "test_markup.py"
Cohesion: 0.06
Nodes (43): Path, C before i/ī in any position palatalizes (Rule C)., Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)., gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar., Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc., Cyning (c + y from u) remains non-palatalized; blocklist and only-back., Medial c before e/æ/y (non-i) does not palatalize (Rule B)., C after i/ī does not palatalize when a back vowel follows (Rule D). (+35 more)

### Community 25 - "tests/conftest.py"
Cohesion: 0.08
Nodes (37): Popen, cli_context(), ensure_llama_server(), _is_llama_server_healthy(), isolated_morphology_app_data(), isolated_morphology_index_db(), lexicon_source_db(), mock_console() (+29 more)

### Community 26 - "weak_derivation_flow.py"
Cohesion: 0.04
Nodes (50): WeakInfFormEmitter, WeakPainsg1ContextFormEmitter, WeakPsinsg2DerivationFormContextEmitter, WeakPsinsg2DerivationSoundContextEmitter, Immutable context for weak infinitive-derived emitter callbacks. Args:…, Immutable context for weak ``PaInSg1``-derived emitter callbacks. Args:…, Immutable context for weak ``PsInSg2``-derived emitter callbacks. Args:…, _WeakInfDerivationContext (+42 more)

### Community 27 - "cli/dictionary.py"
Cohesion: 0.12
Nodes (25): clean_headwords(), _count_table_rows(), _default_morphology_data_dir(), _default_source_path(), dictionary_group(), generate_reference_snapshots_command(), _missing_canonical_index_message(), group (+17 more)

### Community 28 - "server.py"
Cohesion: 0.07
Nodes (47): _proxy_config(), test_clamps_max_tokens_to_default_cap(), test_does_not_rewrite_when_finish_reason_is_stop(), test_does_not_rewrite_when_yaml_is_invalid(), test_rewrites_length_to_stop_for_valid_yaml_and_body(), load_proxy_config(), _parse_bool_env(), _parse_float_env() (+39 more)

### Community 29 - "diacritic_disambiguate.py"
Cohesion: 0.07
Nodes (51): Layout, test_fetch_bt_search_entries_uses_search_endpoint(), test_filter_bt_entries_by_normalized_form_empty_list_returns_empty(), test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others(), test_filter_bt_entries_by_normalized_form_no_matches_returns_empty(), test_filter_bt_entries_by_normalized_form_preserves_order(), test_merge_bt_entries_deduplicates_and_reindexes(), test_normalize_bt_spelling_converts_acute_to_macron() (+43 more)

### Community 30 - "ensure_parts_of_speech"
Cohesion: 0.08
Nodes (40): _load_fixture_rows(), Connection, Path, Tests for normalized POS and inflection-code seed fixtures., Read one JSON fixture file used by the POS seed tests., Return the current row count for one reference table., _row_count(), test_inflection_seed_covers_observed_snapshot_function_codes() (+32 more)

### Community 31 - "OldEnglishText"
Cohesion: 0.09
Nodes (36): Document, TeiReader, fixture, sample_doc(), test_tei_export_attributes(), test_tei_export_basic(), test_tei_export_structure(), Test importing Beowulf from TEI XML. (+28 more)

### Community 32 - "RawBlock"
Cohesion: 0.05
Nodes (52): dialogue_text(), prose_text(), fixture, patch, Unmarked verse gets 1-based line numbers within the section., _t(), test_canonical_converter_prose(), test_canonical_converter_verse() (+44 more)

### Community 33 - "Word"
Cohesion: 0.07
Nodes (49): Lexical entry schema carrying POS flags and paradigm state for one lemma., Word, _append_short_syllable_front_vowel_heuristic(), _append_suffix_heuristics(), _append_terminal_a_heuristic(), _append_terminal_e_heuristic(), _apply_final_fallback(), _apply_noun_heuristics() (+41 more)

### Community 34 - "MorphologyCatalogLoader"
Cohesion: 0.06
Nodes (35): catalog_db(), fixture, Path, Build a small morphology slice and verify normalized FK columns on forms., test_catalog_loader_ensure_seeded_refresh(), test_catalog_loader_ensure_seeded_skips_when_populated(), test_catalog_loader_is_idempotent(), test_catalog_loader_populates_recognition_hints_json() (+27 more)

### Community 35 - "adj_forms.py"
Cohesion: 0.07
Nodes (53): _adj_print(), _build_adjective_formhash(), _build_comparative_title_array(), _build_superlative_title_array(), _build_weak_title_array(), _dedupe_preserve_first(), _emit_superlative_strong_forms(), _emit_weak_degree_forms() (+45 more)

### Community 36 - "strong_derivation_flow.py"
Cohesion: 0.06
Nodes (42): StrongDerivedInfFormAction, StrongDerivedInfImsgAction, StrongDerivedInfParticipleAction, StrongDerivedInfSoundAction, StrongInfDerivationRouter, Immutable context for strong infinitive-derived emitter callbacks. Args:…, _StrongInfDerivationContext, Emit one strong infinitive-derived row for a selected active vowel. Side… (+34 more)

### Community 37 - "etymology_display.py"
Cohesion: 0.07
Nodes (51): Tests for etymology parsing and browse table formatting., test_format_etymology_display_renders_table_headers(), test_misplaced_attestation_is_flagged(), test_mixed_attestation_and_cognates_split(), test_parse_cognate_chain_with_citation(), test_parse_colon_separated_lang_chain(), test_parse_multiple_german_cognates(), test_parse_norse_words_with_latin_tail() (+43 more)

### Community 38 - "weak_principal_flow.py"
Cohesion: 0.07
Nodes (56): WeakInfBranchGenerator, WeakPainsg1BranchGenerator, WeakPrincipalContextAction, WeakPrincipalFormEmitter, WeakPrincipalParticipleAction, WeakPsinsg2BranchGenerator, Immutable context for weak principal-part callback bindings. Args: formhash:…, _WeakPrincipalPartContext (+48 more)

### Community 39 - "SenseMetadataClassifier"
Cohesion: 0.07
Nodes (25): Unit tests for sense-prefix metadata classification., TestSenseMetadataClassifier, _has_substantive_gloss(), _looks_like_gloss_start(), _normalize_case(), _normalize_gender(), _normalize_modifier(), Normalize one modifier abbreviation token. Args: token: Raw modifier token… (+17 more)

### Community 40 - "BTTile"
Cohesion: 0.07
Nodes (38): _sample_preprocessed_page(), _sample_tile(), test_anchor_seeds_jsonl_contains_page_region_hierarchy(), test_manifest_serialization_order_is_deterministic(), test_page_and_tile_records_require_provenance_fields(), test_pages_jsonl_contains_source_and_recipe_provenance(), test_tile_id_is_stable_from_page_and_split_geometry(), test_tiles_jsonl_contains_crop_overlap_and_quality_metadata() (+30 more)

### Community 41 - "test_cli_ocr_bosworth_toller.py"
Cohesion: 0.05
Nodes (61): test_full_validation_fixture_supports_live_five_page_pairing(), test_prepare_pages_filters_page_ids_in_memory(), test_prepare_pages_honors_overlap_px_override(), test_prepare_pages_runs_end_to_end_pipeline(), test_prepare_pages_zero_page_filter_raises(), _seed_prep_workspace(), test_bosworth_toller_default_prep(), test_bosworth_toller_help_shows_flags() (+53 more)

### Community 42 - "TextMetadata"
Cohesion: 0.08
Nodes (38): ProgressCallback, parametrize, Test that deterministic ingestion of text files matches the golden JSON…, test_deterministic_ingestion_regression(), Factory class for creating and using the correct source loader., SourceLoader, BaseDocumentIngestor, DocumentIngestor (+30 more)

### Community 43 - "BTSourceBlockBuilder"
Cohesion: 0.21
Nodes (7): BTSourceBlockBuilder, Build ordered source blocks from parsed BT lines. Skipped lines are ignored.…, Create one new source block seeded by *line*. Args: blocks: Blocks built so…, Return the normalised lookup key for one parsed line. Args: line: Parsed BT…, Return ``True`` when an orphan editorial line may seed a block. Args: line:…, Group parsed Bosworth-Toller lines into source-order dictionary blocks.…, Initialise the builder with an optional target resolver. Args: resolver:…

### Community 44 - "bt_witness_prep/pipeline.py"
Cohesion: 0.06
Nodes (56): test_source_page_id_is_stable_from_filename_stem(), _source_page(), test_clamp_crop_box_falls_back_to_full_frame_when_geometry_collapses(), test_preprocess_clamps_pathological_over_crop_to_max_margin(), test_preprocess_crop_box_is_deterministic_for_fixture_page(), test_preprocess_function_matches_preprocessor_entrypoint(), test_preprocess_preserves_output_dimensions_and_contracts(), test_preprocess_records_recipe_id_on_result() (+48 more)

### Community 45 - "old_english_pipeline.py"
Cohesion: 0.04
Nodes (79): _align_characters(), compute_ocr_metrics(), _levenshtein_distance(), _precision(), preprocess_ocr_text(), _recall(), test_normalize_ocr_input_to_pdf_accepts_pdf(), test_old_english_accepts_pdf() (+71 more)

### Community 46 - "NormalizedTitleJoinIndex"
Cohesion: 0.07
Nodes (32): _index(), Unit tests for NormalizedTitleJoinIndex., test_resolve_all_exactly_one_title_across_pos(), test_resolve_all_no_match(), test_resolve_all_pos_direct_multiple_matches(), test_resolve_all_pos_direct_single_match(), test_resolve_all_variant_with_pos_filter(), test_resolve_all_variant_without_pos_filter() (+24 more)

### Community 47 - "WrightAuditService"
Cohesion: 0.10
Nodes (21): _catalog_pos_from_word(), LegacyWrightRow, _parse_encoded_wright_sections(), Engine, Path, Session, Audit legacy Wright source annotations against deterministic catalog rows.…, Build a read-only audit service bound to one canonical database. Args: engine:… (+13 more)

### Community 48 - "wright-morphology-fixture.schema.json"
Cohesion: 0.05
Nodes (39): 1.0, morph_classes, Old English, schema_version, sources, wright-modern-morphology, additionalProperties, description (+31 more)

### Community 49 - "cli"
Cohesion: 0.07
Nodes (64): _minimal_index_payload(), _mock_bt_lookup(), fixture, Path, Minimal macron index payload for diacritic add/delete tests., test_diacritic_add_fails_when_exists_without_force(), test_diacritic_add_fails_when_key_in_ambiguous_even_with_force(), test_diacritic_add_force_overwrites() (+56 more)

### Community 50 - "strong_principal_flow.py"
Cohesion: 0.07
Nodes (34): StrongInfDerivationEmitter, StrongPrincipalFormAction, StrongPrincipalInfDerivationAction, StrongPrincipalParticipleAction, Immutable context for strong principal-part callback bindings. Args: formhash:…, _StrongPrincipalPartContext, Emit one strong principal-part row for a selected active vowel. Side Effects:…, Attach a past participle emitted from a strong principal-part row. Side… (+26 more)

### Community 51 - "models/__init__.py"
Cohesion: 0.11
Nodes (30): patch, With only input given, paths default to stem + infix + extension., test_source_mark_diacritics_default_paths(), test_source_mark_diacritics_writes_text_and_ambiguities(), test_source_mark_diacritics_writes_unknowns_file(), AmbiguityOption, DiacriticRestorationResult, MacronAmbiguity (+22 more)

### Community 52 - "BTPreprocessedPage"
Cohesion: 0.09
Nodes (38): _preprocessed_page(), _source_page(), test_column_crop_boxes_respect_midline_gutter_guardrails(), test_explicit_non_ready_page_status_skips_forced_four_tile_split(), test_standard_page_splits_into_exactly_four_tiles(), test_tile_function_matches_tiler_entrypoint(), test_tile_order_is_stable_col_part_sequence(), test_tile_records_match_image_dimensions() (+30 more)

### Community 53 - "utils.py"
Cohesion: 0.06
Nodes (27): Progress, Tests for CLI utilities., Test success panel has correct styling., Test console quiet mode functionality., Test that console can be set to quiet mode., Test that stderr console can be set to quiet mode., Test console objects., Test that console objects are properly initialized. (+19 more)

### Community 54 - "morphology-wright-catalog/README.md"
Cohesion: 0.16
Nodes (8): forms.morph_class_id denormalized propagation, isolated_morphology_app_data pytest fixture (no writes to real app-data DB), Lemma-level morph class assignment (normalized_title, pos) -> morph_classes, Wright morph catalog reference schema (morph_classes, wright_sections, morph_sources), parts_of_speech as single POS source of truth (FK-only product tables), refactor_baseline.json Perl-parity guardrail for morphology generation, Wright § markdown text ingest into wright_sections.section_text, Screenshot: macOS Alt+key Textual Key() events for lexicon browse

### Community 55 - "test_morph_class_browse.py"
Cohesion: 0.35
Nodes (10): _bt_entry_id(), _insert_bt_entry(), Path, Tests for catalog-backed morph-class metadata in lexicon browse details., Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions., Seed one catalog assignment row into a temporary lexicon test database., Insert one minimal ``bt_entries`` row into a temporary lexicon test database.…, _seed_catalog_assignment() (+2 more)

### Community 56 - "properties"
Cohesion: 0.06
Nodes (34): type, type, type, properties, type, type, type, type (+26 more)

### Community 57 - "properties"
Cohesion: 0.06
Nodes (34): description, minLength, type, $ref, default, description, enum, type (+26 more)

### Community 58 - "FormsEntryRelinker"
Cohesion: 0.16
Nodes (24): _fetch_form_entry_id(), _insert_bt_entry(), _insert_bt_variant(), _insert_form(), _pos_id(), Connection, fixture, Path (+16 more)

### Community 59 - "test_morph_catalog_pos.py"
Cohesion: 0.11
Nodes (31): parametrize, Tests for morphology catalog POS normalization helpers., test_catalog_pos_from_bt_pos_cli_aliases(), test_catalog_pos_from_bt_pos_join_values(), test_catalog_pos_from_bt_pos_raises_for_unmapped(), test_catalog_pos_from_wordclass(), test_catalog_pos_from_wordclass_unknown_returns_none(), test_pos_id_from_bt_pos() (+23 more)

### Community 60 - "test_cli_dictionary.py"
Cohesion: 0.12
Nodes (31): _build_unified_source_db(), _fetch_entry_id(), _fetch_form_entry_id(), _insert_form(), _morphology_data_dir(), _pos_id(), Connection, Path (+23 more)

### Community 61 - "test_loaders.py"
Cohesion: 0.10
Nodes (20): Element, fixture, source_loader(), test_load_from_file_text(), test_load_from_file_unsupported(), test_tei_source_loader_load_tei(), BaseSourceLoader, FileSourceLoader (+12 more)

### Community 62 - "LLMExtractor"
Cohesion: 0.10
Nodes (16): llm, patch, TestLLMExtractor, _j(), parametrize, Test that the live Qwen regression matches the golden regression. Args:…, _t(), test_goldens_are_schema_valid() (+8 more)

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

### Community 69 - "browse_query.py"
Cohesion: 0.05
Nodes (53): parametrize, Tests for BT display spelling normalization., Normalize representative real BT headword spellings from ``oe_bt.txt``., Normalizing an already-normalized spelling is a no-op., test_bt_spelling_normalizer_matches_oe_normalizer(), test_normalize_is_idempotent(), test_normalize_real_bt_diphthong_cases(), _append_unique() (+45 more)

### Community 70 - "AnyLLMConfig"
Cohesion: 0.13
Nodes (12): object, TestAnyLLMConfig, fixture, patch, TestLLMDocumentIngestor, AnyLLMConfig, Configuration for Python any-llm., Get the model ID. Raises: ValueError: If we can't determine the model. Returns:… (+4 more)

### Community 71 - "test_bt_tile_ocr.py"
Cohesion: 0.18
Nodes (21): test_concatenate_tile_texts_joins_with_blank_lines(), test_discover_tile_images_falls_back_to_whole_page(), test_discover_tile_images_uses_reading_order(), test_run_page_witness_ocr_concatenates_tile_outputs(), test_run_tile_ocr_calls_old_english_pipeline(), test_run_tile_ocr_skip_ocr_raises_when_cache_missing(), test_run_tile_ocr_skip_ocr_reads_cached_normalized_text(), test_run_tile_ocr_uses_injected_runner() (+13 more)

### Community 72 - "GeneratorSession"
Cohesion: 0.07
Nodes (50): _make_verb_paradigm(), _make_word(), test_set_adj_paradigm_stem_propagation(), test_set_adj_paradigm_wright_rule_425(), test_set_noun_paradigm_advanced_stem_propagation(), test_set_noun_paradigm_final_fallback_neuter_long_stem(), test_set_noun_paradigm_final_fallback_neuter_short_stem(), test_set_noun_paradigm_heuristic_incel_suffix() (+42 more)

### Community 73 - "test_text_utils_reference.py"
Cohesion: 0.19
Nodes (14): parametrize, test_canonicalize_inflection_code_reference(), test_eth2thorn_reference(), test_iumlaut_reference(), test_move_accents_reference(), test_normalize_bt_display_spelling_is_idempotent(), test_normalize_bt_display_spelling_reference(), test_normalize_output_reference() (+6 more)

### Community 74 - "db/runtime.py"
Cohesion: 0.08
Nodes (41): Config, _dictionary_line(), _make_audit_source_dir(), _manual_form_line(), _para_vb_line(), Path, Tests for legacy Wright source auditing. Phase D source contract: The audit…, Build one ``manual_forms.txt`` fixture line with the expected 16 columns. (+33 more)

### Community 75 - "BTPosGenderExtractor"
Cohesion: 0.10
Nodes (22): extractor(), fixture, parametrize, Tests for BTPosGenderExtractor using real oe_bt.txt prefix fragments., Shared extractor instance., Real BT prefix fragments resolve to expected POS and genders., Verb paradigm detection wins when both verb endings and adj appear., Abbad line with m: and m. returns masculine noun once. (+14 more)

### Community 76 - "enum"
Cohesion: 0.08
Nodes (26): common, comparative, dual, feminine, first, masculine, neuter, plural (+18 more)

### Community 77 - "MorphologyDictionaryCleaner"
Cohesion: 0.12
Nodes (17): parametrize, Tests for morphology dictionary TSV cleanup., test_clean_dictionary_fixes_bt_diphthongs_in_col2(), test_clean_dictionary_lowercases_col2_dedupes_and_backups(), test_clean_dictionary_raises_when_source_missing(), test_should_lowercase_col2_only_all_upper_letters(), MorphologyDictionaryCleaner, MorphologyDictionaryCleanupResult (+9 more)

### Community 78 - "create_engine"
Cohesion: 0.18
Nodes (26): _insert_bt_entry(), _insert_bt_variant(), _insert_lemma_assignment(), Connection, fixture, Path, Tests for morphology form foreign-key resolution., resolver_db() (+18 more)

### Community 79 - "TEIExporter"
Cohesion: 0.14
Nodes (17): ABC, test_tei_exporter_interface(), BaseExporter, Any, Create the publication statement. Args: doc: The document to export. parent:…, Create the source description. Args: doc: The document to export. parent: The…, Emit a section and its content recursively. Args: sec: The section to export.…, Apply common metadata attributes to a node. Args: node: The node to apply the… (+9 more)

### Community 80 - "print_info"
Cohesion: 0.12
Nodes (21): Test info printing functions., Test basic info printing., Test info panel has correct styling., TestPrintInfo, _mark_diacritics_derived_path(), argument, command, Context (+13 more)

### Community 81 - "BT V2 Parser And Schema Migration"
Cohesion: 0.07
Nodes (26): 1. Parsing and segmentation, 2. Attestation stripping, 3. Editorial merge, 4. Lowercased display spellings, Acceptance Criteria, BT V2 Parser And Schema Migration, CLI Output Contract, Context (+18 more)

### Community 82 - "properties"
Cohesion: 0.08
Nodes (25): oldenglish_info, stella, wright_1914, description, minLength, type, default, description (+17 more)

### Community 83 - "BTSourceHeadwordCleaner"
Cohesion: 0.12
Nodes (18): parametrize, Tests for Bosworth-Toller oe_bt.txt headword cleanup., test_clean_headwords_leaves_later_bold_tags_unchanged(), test_clean_headwords_lowercases_first_bold_and_backups(), test_clean_headwords_raises_when_source_missing(), test_should_lowercase_headword_only_all_upper_letters(), BTSourceHeadwordCleaner, BTSourceHeadwordCleanupResult (+10 more)

### Community 84 - "ocr_proxy/runtime.py"
Cohesion: 0.17
Nodes (19): test_managed_ocr_proxy_launches_and_stops(), test_overrides_existing_server_equals_arg(), test_overrides_existing_server_split_arg(), _bool_env_value(), _build_proxy_env(), managed_ocr_proxy(), _pick_unused_local_port(), ProxyLaunchConfig (+11 more)

### Community 85 - "Orchestration Guide"
Cohesion: 0.07
Nodes (26): 10. Failure handling, 11. Phase briefs, 12. Definition of done, 1. Architecture, 2. Locked decisions, 3. Files, 4. Phase order, 5. Orchestrator workflow (+18 more)

### Community 86 - "Execution order"
Cohesion: 0.08
Nodes (25): BT Dictionary Parser Rebuild Implementation Plan, Commit strategy, Domain/runtime models, Execution handoff, Execution order, File map, Live corpus findings to design against, Locked decisions (do not re-litigate) (+17 more)

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

### Community 91 - "OCR pipeline test-fixture corpus (Wright's Grammar pages)"
Cohesion: 0.12
Nodes (23): OCR pipeline test-fixture corpus (Wright's Grammar pages), Old English noun declension system (strong/weak/minor), wright_markup.pdf (OCR fixture), wright_nouns10.md (OCR ground truth, suffixes/derivation), wright_nouns10.pdf (OCR fixture), wright_nouns2.md (OCR ground truth, cyning/engel/heofon declension), wright_nouns2.pdf (OCR fixture), wright_nouns3.md (OCR ground truth) (+15 more)

### Community 92 - "test_wright_section_text.py"
Cohesion: 0.08
Nodes (33): catalog_db(), fixture, Path, Tests for Wright section markdown parsing and catalog text ingest., test_ingest_result_counts_and_warnings(), test_ingester_force_overwrites_existing_text(), test_ingester_is_idempotent_without_force(), test_ingester_updates_null_sections() (+25 more)

### Community 93 - ".parse"
Cohesion: 0.06
Nodes (21): Parsed representation of one ``oe_bt.txt`` line before sense segmentation.…, RawBTLine, Initialize parser collaborators for split and POS extraction. Args: splitter:…, Parse one source line into ``RawBTLine`` plus phase-02 metadata. Args:…, Classify one line into ``BTLineKind``. Args: body: Main ``@`` field body…, Detect whether a line is primarily a cross-reference. Args: body: Main ``@``…, Extract the POS prefix fragment immediately after the first headword. Args:…, Extract alternate headword spellings from the pre-POS plain-text prefix. Args:… (+13 more)

### Community 95 - "required"
Cohesion: 0.11
Nodes (19): aliases, canonical_name, features, id, is_assignable, mapping_rationale, modern_class, paradigmatic_words (+11 more)

### Community 96 - "features"
Cohesion: 0.11
Nodes (19): citation_apa, retrieved_date, source_key, url, $defs, features, recognitionHints, source (+11 more)

### Community 97 - "test_schema.py"
Cohesion: 0.22
Nodes (18): _forms_column_names(), _fresh_canonical_db(), _index_names(), Connection, parametrize, Path, Tests for lexicon read-model schema helpers., Return the seeded ``unknown`` part-of-speech row id. (+10 more)

### Community 98 - "test_paths.py"
Cohesion: 0.16
Nodes (21): parametrize, Path, test_get_app_data_path_platform_defaults(), test_get_app_data_path_settings_override(), test_get_app_data_path_unsupported_platform(), test_get_canonical_db_path_creates_parent(), test_isolated_morphology_index_db_uses_canonical_filename(), test_resolve_db_path_explicit_dir_mkdirs_target() (+13 more)

### Community 99 - "Configuration: Command Line Tool guide"
Cohesion: 0.15
Nodes (18): wyrdcraeft settings CLI command doc, wyrdcraeft source convert CLI command doc, Configuration: Command Line Tool guide, wyrdcraeft FAQ, Standard JSON Representation for Old English Texts (schema spec), Installation guide, Quickstart guide, Using the Command Line Interface guide (+10 more)

### Community 100 - "DatabaseStartupRuntime"
Cohesion: 0.09
Nodes (34): _create_pre_alembic_forms_db(), _make_settings(), MonkeyPatch, Path, test_child_help_skips_database_gate(), test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(), test_fresh_missing_db_bootstraps_with_alembic_path(), test_interactive_blank_prompt_keeps_backup_without_retry() (+26 more)

### Community 101 - "20260706_01_parts_of_speech_and_dictionary_pos.py"
Cohesion: 0.16
Nodes (23): _assert_no_null_pos_ids(), _assert_no_null_text_pos(), downgrade(), _downgrade_bt_entries(), _downgrade_lemma_morph_classes(), _downgrade_morph_classes(), Connection, Replace legacy BT text POS and headword columns with normalized fields. Args:… (+15 more)

### Community 102 - "test_lemma_morph_assignment.py"
Cohesion: 0.24
Nodes (16): assigner(), _assignment(), catalog_db(), _class_key(), _make_verb_paradigm(), _make_word(), fixture, Path (+8 more)

### Community 103 - "OESyllableBreaker"
Cohesion: 0.16
Nodes (9): Syllable model for Old English syllable breaking., A syllable is a unit of speech that consists of an onset, nucleus, and coda., Syllable, OESyllableBreaker, Split consonant cluster between syllables using a conservative max-onset…, Insert dots before known suffixes to guide syllabification., Syllabify an Old English word conservatively., Break an Old English word into syllables. (+1 more)

### Community 104 - "i-umlaut (sound change)"
Cohesion: 0.13
Nodes (20): Breaking (OE vowel sound change), i-umlaut (sound change), u- and o/a-umlaut (guttural umlaut), Wright OE Grammar - Ch. IV/V ToC (vowel development), Wright OE Grammar scan - Ch. IV/V ToC (source PDF), Wright OE Grammar - nasal loss and breaking (§61-64), Wright OE Grammar scan - nasal loss/breaking (source PDF), Wright OE Grammar - Germanic equivalents of OE vowels (§153-164) (+12 more)

### Community 105 - "wyrdcraeft dictionary browse"
Cohesion: 0.17
Nodes (16): normalize_old_english(), BTSpellingNormalizer, DictionaryBrowseApp (Textual TUI), DictionaryBrowseQueryService, MorphologyCatalogQueryService, WrightSectionTextIngester (ref), WrightSectionTextIngester, 12-tier headword/variant search ranking ladder (+8 more)

### Community 106 - "test_cli_commands.py"
Cohesion: 0.06
Nodes (23): Tests for CLI commands with low coverage., Test JSON output format., Test text output format., Test invalid output format., Test CLI error handling., Test CLI without arguments shows help., Test invalid command shows error., Test that the OCR command group has been removed from the CLI. (+15 more)

### Community 107 - "properties"
Cohesion: 0.12
Nodes (16): type, uniqueItems, type, uniqueItems, type, uniqueItems, type, closed_class_examples (+8 more)

### Community 108 - "full_session"
Cohesion: 0.22
Nodes (9): FixtureRequest, fail_if_perl_subprocess_invoked(), full_session(), fixture, MonkeyPatch, Prepared session using the subset dictionary for default reference tests., Prepared session using the full dictionary for optional smoke checks., Fail fast if morphology tests attempt to execute Perl. (+1 more)

### Community 109 - "normalized-canonical-schema/README.md"
Cohesion: 0.11
Nodes (14): Two-gate subagent workflow: Gate A spec review, Gate B code review, Lexicon shrink: drop lexicon_entries/lexicon_forms, keep search_keys, Drop search_keys entirely; query-time 12-tier dictionary browse search, Unified dictionary build pipeline replacing morphology/dictionary/lexicon build triangle, Execution options, Gate A — Spec review (required once per phase), Gate B — Code review (required once per phase), Global validation (+6 more)

### Community 110 - "sound_dispatch_flow.py"
Cohesion: 0.20
Nodes (14): SoundChangeSequenceEmitter, SoundManualContextEmitter, SoundSourceContextEmitter, Immutable context for sound-change callback dispatch. Args: formhash: Shared…, _SoundChangeDispatchContext, emit_manual_sound_changed_context(), emit_sound_changed_form_for_context(), emit_source_form_with_sound_context() (+6 more)

### Community 111 - "lexicon/conftest.py"
Cohesion: 0.21
Nodes (14): _inflection_code_id(), lexicon_db_connection(), lexicon_db_path(), _noun_pos_id(), Connection, fixture, Path, Shared fixtures for lexicon schema and service tests. (+6 more)

### Community 112 - "BTQueryService"
Cohesion: 0.21
Nodes (21): corpus_index_db(), _index_fixture(), fixture, Path, Unit and integration tests for BTQueryService., sample_index_db(), _seed_forms_table(), test_bt_senses_round_trip_rich_fields() (+13 more)

### Community 113 - "cli.py"
Cohesion: 0.07
Nodes (27): patch, Test the convert command without LLM (heuristic mode)., Test that LLM flags are correctly passed to the pipeline., Test the convert command with a missing source file., test_convert_command_llm_flags(), test_convert_command_missing_source(), test_convert_command_no_llm(), parametrize (+19 more)

### Community 114 - "cli/morphology.py"
Cohesion: 0.19
Nodes (14): clean_dictionary(), _default_morphology_data_dir(), _format_dictionary_join_text(), morphology_group(), command, group, option, Path (+6 more)

### Community 115 - "Wright, An Old English Grammar (source text)"
Cohesion: 0.13
Nodes (15): a-declension (OE noun morphology), Elizabeth M. Wright (author), Joseph Wright (author), Old English phonology: vowels, umlaut, ablaut, Wright, An Old English Grammar (source text), Wright OE Grammar - Table of Contents (Ch. I-III), Wright OE Grammar scan - Table of Contents (source PDF), Wright OE Grammar - consonant system (§7-8) (+7 more)

### Community 116 - "Bosworth-Toller Anglo-Saxon Dictionary (source text)"
Cohesion: 0.23
Nodes (12): Bosworth-Toller Anglo-Saxon Dictionary (source text), JP2-only enumerator filter, Conservative margin-crop regression test, Stage B five-page validation manifest, fixture_prose.txt (Mark gospel OE prose fixture), test_dict.txt (BT morphology dictionary test fixture), notes.txt (non-JP2 ignore-behavior fixture), readme.md (BT witness-prep fixtures documentation) (+4 more)

### Community 117 - "GeneratorSession.load_all"
Cohesion: 0.14
Nodes (14): GeneratorSession (services.morphology), wyrdcraeft.models.morphology, GeneratorSession, LemmaMorphClassAssigner, MorphologyCatalogLoader, Morphology generation flow (concept), GeneratorSession.load_all(), LemmaMorphClassAssigner.assign_all() (+6 more)

### Community 118 - "wyrdcraeft 1.1.0 release (2026-03-02)"
Cohesion: 0.20
Nodes (14): GPalatalizer, MacronApplicator, wyrdcraeft.models.macron_index, wyrdcraeft 1.0.0 initial release (2026-03-01), wyrdcraeft 1.1.0 release (2026-03-02), Witness-first structuring principle, wyrdcraeft source mark-diacritics, Diacritic restoration runtime processing flow (+6 more)

### Community 119 - "default_bt_source_path"
Cohesion: 0.10
Nodes (24): CorpusSampleResult, DictionaryCorpusSampler, main(), Path, Index source lines by lookup key while preserving source line order. Returns:…, Sample keys by deterministic every-Nth stratification. Args: ordered_keys: Keys…, Result of one corpus-sample build run. Attributes: keys: Selected lookup keys…, Collect all editorial siblings for sampled keys in corpus order. Args:… (+16 more)

### Community 120 - "normalize_old_english"
Cohesion: 0.14
Nodes (18): test_normalize_old_english_parity_rules(), diacritic_add(), diacritic_delete(), _load_macron_index_payload(), argument, command, option, Path (+10 more)

### Community 121 - "Morphology build performance session (2026-07-03)"
Cohesion: 0.11
Nodes (19): Batched SQLite sink (25K rows) + bulk PRAGMAs fix for morphology build perf, O(n) paradigm assignment replacing O(n^2) stem comparison, 1. Batched SQLite sink + bulk PRAGMAs (kept), 2. Deferred indexes (reverted), 3. Built-in build profiling (`--profile`), 4. O(n) paradigm assignment (kept), 5. Adjective stage cProfile script, Changes implemented (+11 more)

### Community 122 - "Phase 2 — Lemma Morph Class Assignment"
Cohesion: 0.09
Nodes (20): Cleanup (optional same PR or follow-up), Phase 2 — Gate A: Spec review, Phase 2 — Gate B: Code review, Phase 2 — Lemma Morph Class Assignment, Phase 2 validation, Task 1: Schema + migration, Task 2: POS normalization helper, Task 3: Paradigm exemplar registry (+12 more)

### Community 123 - "main"
Cohesion: 0.23
Nodes (8): patch, Tests for the main module., Test the main function., Test that main function calls the CLI., Test that main function can be imported and called., Test that main function exists and is callable., TestMain, main()

### Community 124 - "Morphology Wright catalog — Phase 1 session (2026-07-04)"
Cohesion: 0.12
Nodes (17): 1. Circular import on full morphology test collection, 2. Untracked plan directory, 3. Package data, Branch and commits, Build integration, Commits this session (Phase 1 Tasks 1–4), Goal (locked design), Key files (+9 more)

### Community 125 - "QueryFormRow"
Cohesion: 0.08
Nodes (25): test_infer_bt_pos_filter_maps_unambiguous_noun(), test_infer_bt_pos_filter_returns_none_for_mixed_wordclasses(), QueryFormRow, Indexed morphology row enriched with normalized query keys., dictionary_join_entry_to_dict(), _form_lookup_sql(), _infer_bt_pos_filter(), _lemma_lookup_sql() (+17 more)

### Community 126 - "BT OCR witness preparation slice (bt_witness_prep)"
Cohesion: 0.18
Nodes (12): ADR 0004: BT OCR parsing starts with lossless source-grounded AST, ADR 0005: BT source acquisition uses multi-witness download set, BTWitnessPrepInput, BTWitnessPrepRun, BTSourcePageEnumerator, BTWitnessPrepPipeline, BTPagePreprocessor, prepare_pages() (+4 more)

### Community 127 - "pos_inference.py"
Cohesion: 0.15
Nodes (15): PosInferenceCancelCheck, PosInferenceProgress, PosInferenceWarningSink, test_infer_bt_pos_from_wordclasses_requires_single_mapping(), Connection, Shared dictionary POS inference from morphology forms., Attempt one inferred POS update, skipping duplicate and homograph rows. Args:…, Unwrap one SQLAlchemy connection to the underlying SQLite driver. Args:… (+7 more)

### Community 128 - ".focus_search"
Cohesion: 0.17
Nodes (7): Pressed, Submitted, Run browse search when the user submits the search box. Args: event: Textual…, Close the overlay when the user activates the close button. Args: event:…, Cache browse pane widgets for stable access during event handling. Side…, Return keyboard focus to the search input field., Insert one Old English character at the search input cursor. Args: event:…

### Community 129 - "TestCLISettings"
Cohesion: 0.17
Nodes (7): Test the settings command., Test the settings command with table output., Test the settings command with JSON output., Test the settings command with text output., Test the settings command with verbose flag., Test the settings command with custom config file., TestCLISettings

### Community 130 - "DocumentIngestor"
Cohesion: 0.18
Nodes (11): DocumentIngestor, HeuristicDocumentIngestor, LLMDocumentIngestor, TEIDocumentIngestor, wyrdcraeft.models.source_text (OldEnglishText JSON schema), Dictionary build/browse flow (concept), Alembic head 20260707_01 (normalized-schema Phases A-D), Canonical Database ER Diagram (wyrdcraeft.sqlite3) (+3 more)

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

### Community 137 - "print_error"
Cohesion: 0.21
Nodes (8): Test error printing functions., Test basic error printing., Test error printing with suggestions., Test error printing without suggestions., Test error panel has correct styling., TestPrintError, print_error(), Print error message with optional suggestions. Args: message: Error message…

### Community 138 - "cli/settings.py"
Cohesion: 0.12
Nodes (17): create_settings(), command, Context, group, pass_context, Settings-related commands., Settings-related commands., Create a new settings file. (+9 more)

### Community 139 - "query"
Cohesion: 0.24
Nodes (17): audit_wright(), browse(), build(), ingest_wright_text(), lookup(), argument, command, Context (+9 more)

### Community 140 - "enum"
Cohesion: 0.22
Nodes (9): adjective, adverb, noun, pronoun, verb, description, enum, type (+1 more)

### Community 141 - "enum"
Cohesion: 0.22
Nodes (9): adverbial_or_prepositional_origin, irregular_or_suppletive, irregular_or_umlauted, regular, suppletive, umlauted, enum, type (+1 more)

### Community 142 - "test_attach_morphology_db.py"
Cohesion: 0.47
Nodes (8): _index_with_attach(), Path, Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite., Seed the canonical ``forms`` table via the real SQLAlchemy sink., _seed_forms_table(), test_attach_missing_db_fails_for_canonical_only_mode(), test_attach_preserves_forms_and_writes_bt_entries(), test_attach_rerun_is_idempotent_and_preserves_forms()

### Community 143 - "wright_phonology8.md (Grimm's Law / Verner's Law OCR fixture)"
Cohesion: 0.32
Nodes (8): Grimm's law (first sound-shifting), Verner's law, Wright OE Grammar - Introduction (Indo-Germanic language family), Wright OE Grammar scan - Introduction (source PDF), wright_phonology8.md (Grimm's Law / Verner's Law OCR fixture), wright_phonology8.pdf (scanned page image), wright_skew_table.md (Grimm's Law consonant table, skewed-scan OCR fixture), wright_skew_table.pdf (skewed scanned table image)

### Community 144 - "BTTileQualityScorer"
Cohesion: 0.25
Nodes (8): BTAnchorSeedBuilder, scripts/ocr/benchmark_bt_witness_prep.py, BTWitnessManifestWriter, BTTileQualityScorer, Small-component preservation guardrail, Stage B validation (relative CER improvement pass rule), BTPageTiler, validation.py (diacritic_sensitive_cer, historical_char_exact_match_rate, relative_cer_improvement, recipe_passes_stage_b)

### Community 145 - "Wyrdcraeft Canonical DB Migration Implementation Plan"
Cohesion: 0.12
Nodes (15): Completion Checklist, File Map, Locked Decisions, Native Codex Execution Notes, Orchestrator Strategy, Phase 1: Persistence Skeleton and Canonical Path, Phase 2: Alembic Scaffold, Startup Runtime, Backup Sidecar, Phase 3: Initial Declarative Schema and First Migration (+7 more)

### Community 146 - "format_wright_audit_text"
Cohesion: 0.17
Nodes (16): _append_sample_block(), _display_legacy_wright(), _format_blank_but_classified_issue(), _format_contradiction_issue(), _format_malformed_issue(), _format_row_prefix(), _format_unclassified_issue(), format_wright_audit_text() (+8 more)

### Community 147 - "test_prompt_regression.py"
Cohesion: 0.32
Nodes (7): _canonicalize(), parametrize, Prompt regression and schema validation tests. These tests are designed to be…, Deterministic ordering for stable snapshot comparisons., Placeholder regression test. Today: just ensures the expected snapshot is…, test_expected_json_is_schema_valid(), test_snapshot_regression_contract()

### Community 148 - "wright_phonology7.md (ablaut / vowel gradation OCR fixture)"
Cohesion: 0.29
Nodes (7): Ablaut / vowel gradation (six OE series), wright_phonology5.md (long vowels ā/ǣ OCR fixture), wright_phonology5.pdf (scanned page image), wright_phonology6.md (diphthongs ai/au/eu/iu OCR fixture), wright_phonology6.pdf (scanned page image), wright_phonology7.md (ablaut / vowel gradation OCR fixture), wright_phonology7.pdf (scanned page image)

### Community 149 - "test_corpus_sample.py"
Cohesion: 0.33
Nodes (6): _load_manifest(), Smoke tests for the stratified Bosworth-Toller corpus sample fixture., Ensure corpus fixture is present and within phase-02b size constraints., Parse every corpus line and require deterministic parse or explicit skip., test_corpus_sample_lines_parse_without_raising(), test_corpus_sample_manifest_and_line_count_bounds()

### Community 150 - "DatabaseMigrationError"
Cohesion: 0.18
Nodes (9): DatabaseMigrationError, LegacyDatabaseResetRequired, datetime, RuntimeError, Legacy database reset stop signal with rebuild guidance. Args: backup_path:…, Store the backup path and explicit rebuild recipe for CLI reporting. Keyword…, Capture one startup runtime configuration and its collaborators. Keyword Args:…, Startup migration failure with traceback and rebuild guidance. Args: message:… (+1 more)

### Community 151 - "source_keys"
Cohesion: 0.29
Nodes (7): pattern, source_keys, description, items, minItems, type, uniqueItems

### Community 152 - "resolve_dictionary_db_path"
Cohesion: 0.16
Nodes (13): test_resolve_dictionary_db_path_prefers_explicit_override(), test_resolve_dictionary_db_path_uses_sibling_dictionary(), _db_has_table(), _forms_has_morph_class_id(), _morphology_db_has_bt_entries(), Connection, Path, Return whether one SQLite table exists in the active database. Args:… (+5 more)

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

### Community 157 - "build_runner.py"
Cohesion: 0.06
Nodes (42): TContext_contra, TWord_contra, _apply_limit(), _default_morphology_data_dir(), MorphologyBuildRunnerError, Connection, Path, RuntimeError (+34 more)

### Community 158 - "Task 1: Define Build Event Models"
Cohesion: 0.13
Nodes (14): Execution Handoff, File Map, Lexicon Build Monitor Implementation Plan, Locked Decisions, Notes for Implementer, Task 1: Define Build Event Models, Task 2: Build Shared Runtime Controller, Task 3: Expand `rebuild_lexicon(...)` Contract for Events and Cancel (+6 more)

### Community 159 - "wright_sections"
Cohesion: 0.33
Nodes (6): minimum, wright_sections, default, description, items, type

### Community 160 - "Morphology Wright Catalog — Design Decisions"
Cohesion: 0.14
Nodes (14): Assignment model (Phase 2+), Canonical terms, Catalog load behavior, Dictionary ↔ morphology link, Entity model (reference + dictionary + morphology), Explicit non-goals, Gap-fill priority (Phase 2 assignment), Legacy column meanings (do not conflate) (+6 more)

### Community 161 - "Session State: Lexicon SQLAlchemy Slice 1 Complete"
Cohesion: 0.14
Nodes (13): Alembic owns lexicon DDL, Code review notes (Slice 1, not blocking commit), Files changed in Slice 1 commit, Locked decisions (human, this session), Rebuild semantics, References, Session State: Lexicon SQLAlchemy Slice 1 Complete, Slice 1 deliverables (shipped) (+5 more)

### Community 162 - "BT Dictionary Structuring Workflow runbook"
Cohesion: 0.60
Nodes (5): data/oe_bt.txt Bosworth-Toller OCR source file, BT Dictionary Structuring Workflow runbook, Generating the canonical macron list runbook, Old English OCR Pipeline runbook, Bosworth-Toller dictionary corpus sample test fixture

### Community 163 - "enum"
Cohesion: 0.40
Nodes (5): past, present, enum, type, participle

### Community 164 - ".generate_all_forms"
Cohesion: 0.14
Nodes (7): Emit all generated adverb rows for the bound session. Side Effects: Writes rows…, Emit all generated numeral rows for the bound session. Side Effects: Writes…, Emit all generated noun rows for the bound session. Side Effects: Writes rows…, Emit the default full morphology generation flow in stable order. Side Effects:…, Emit curated manual rows before paradigm-driven generation. Side Effects:…, Emit all generated verb rows for the bound session. Side Effects: Writes rows…, Emit all generated adjective rows for the bound session. Side Effects: Writes…

### Community 165 - "generate_reference_snapshots"
Cohesion: 0.19
Nodes (14): build_session(), canonical_sort_rows(), generate_reference_snapshots(), paradigm_snapshot_rows(), preprocess_snapshot_rows(), Any, Path, Return deterministically sorted shallow-copied records. Args: rows: The rows to… (+6 more)

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

### Community 177 - ".write_json"
Cohesion: 0.40
Nodes (3): Path, Write the report as formatted JSON to disk. Args: report_path: Destination JSON…, Serialize the report to a JSON-friendly mapping. Returns: Dictionary suitable…

### Community 178 - "normalize_morphology_title"
Cohesion: 0.09
Nodes (23): test_normalize_morphology_title_preserves_macrons_and_dots(), Shared morphology-to-dictionary join index keyed by normalized title., _entry_to_dict(), _json_tuple(), _normalize_lookup_key(), _normalize_pos_filter(), _normalize_title_key(), BTSense (+15 more)

### Community 179 - ".resolve_sense_path"
Cohesion: 0.50
Nodes (3): BTSense, Map one Roman sense label to a canonical ``sense_path``. When the label matches…, Resolve deletion/substitution references to canonical sense paths. Args: refs:…

### Community 180 - "Phase A — Reference Tables and Dictionary POS FKs"
Cohesion: 0.15
Nodes (13): Phase A — Commit, Phase A — Gate A: Spec review checklist, Phase A — Gate B: Code review checklist, Phase A — Reference Tables and Dictionary POS FKs, Phase A validation, Task 1: POS + inflection seed fixtures, Task 2: SQLAlchemy reference models, Task 3: Alembic migration `20260706_01` (+5 more)

### Community 181 - "Phase B — Dictionary Browse, Search, and CLI Consolidation"
Cohesion: 0.15
Nodes (13): Acceptance criteria (phase), Browse search rank ladder (locked), Phase B commit message, Phase B — Dictionary Browse, Search, and CLI Consolidation, Phase B — Gate A checklist, Phase B — Gate B checklist, Phase B validation, Task 1: Alembic migration — drop search index tables (+5 more)

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

### Community 187 - ".normalize_bt_display_spelling"
Cohesion: 0.18
Nodes (6): Match, Convert one BT spelling to macronized Wright-style display spelling. Pipeline…, Convert raw BT-style acute diphthongs to macron diphthongs. Bosworth-Toller…, Convert one BT spelling to macronized Wright-style display spelling. Note:…, Rewrite BT second-vowel long-mark diphthongs to first-vowel long marks. Note:…, Compose one corrected diphthong while preserving source case pattern. Args:…

### Community 188 - "BT Structural Visibility Review"
Cohesion: 0.15
Nodes (12): Acceptance Criteria, BT Structural Visibility Review, Candidate Types To Include, Deliverables, Dependencies, Downstream Use, Locked Decisions, Non-Goals (+4 more)

### Community 189 - "wyrdcraeft"
Cohesion: 0.15
Nodes (12): All other code, Bosworth-Toller Old English Dictionary, Canonical database, Contributing, Contributing, Licensing and Provenance, Documentation, Features, Installation (+4 more)

### Community 191 - "Phase D — Drop Legacy Form String Columns"
Cohesion: 0.17
Nodes (12): Phase D — Commit, Phase D — Drop Legacy Form String Columns, Phase D — Gate A: Spec review checklist, Phase D — Gate B: Code review checklist, Phase D validation, Post-phase checklist (coordinator), Task 1: Alembic migration `20260706_04`, Task 2: Sink + query path cleanup (+4 more)

### Community 192 - "LemmaMorphClassAssigner"
Cohesion: 0.06
Nodes (29): catalog_db(), _make_word(), fixture, Path, query_service(), Tests for read-only Wright catalog lemma class lookup., test_from_db_path_uses_isolated_database(), test_lookup_missing_lemma_returns_none() (+21 more)

### Community 193 - "Phase A — Unified Dictionary Build"
Cohesion: 0.17
Nodes (12): Acceptance criteria (phase), Phase A commit message, Phase A — Gate A checklist, Phase A — Gate B checklist, Phase A — Unified Dictionary Build, Phase A validation, Task 1: `FormsEntryRelinker` service, Task 2: `DictionaryBuildPipeline` orchestrator (+4 more)

### Community 201 - "Morphology Context"
Cohesion: 0.17
Nodes (12): Inputs And Outputs, Invariants And Sharp Edges, Key Files, Legacy Wright Audit (report-only v1), Lexicon Browse Integration, Main CLI Entrypoints, Morphology Context, Primary Python Entrypoints (+4 more)

### Community 202 - "Phase 3 — Browse Wright § text pane"
Cohesion: 0.17
Nodes (12): Acceptance criteria, Exact files likely touched, Gate A — Spec review checklist, Gate B — Code review checklist, Objective, Phase 3 — Browse Wright § text pane, Subagent dispatch packet — Phase 3, Subagent task breakdown (+4 more)

### Community 216 - "Global Constraints"
Cohesion: 0.17
Nodes (11): Global Constraints, Remove OCR Pipeline (ADR 0007) Implementation Plan, Task 1: Sever CLI registration of the OCR command group, Task 2: Delete the OCR CLI module and its dedicated tests, Task 3: Delete the OCR proxy service and its tests, Task 4: Delete the OCR pipeline service and its tests, Task 5: Delete `scripts/ocr/` and its `pyproject.toml` entry point, Task 6: Drop OCR-only dependencies and the `ocr_integration` pytest marker (+3 more)

### Community 217 - "Lexicon Browser BT V2 Adaptation Skeleton"
Cohesion: 0.17
Nodes (11): Acceptance Criteria, Browse Changes This Plan Owns, Dependencies, Details-Pane Outcome, Expected BT V2 Inputs, Lexicon Browser BT V2 Adaptation Skeleton, Likely Data-Contract Changes, Locked Decisions (+3 more)

### Community 218 - "Orchestration: Wyrdcraeft Canonical DB Migration"
Cohesion: 0.17
Nodes (11): Completion checklist, Locked decisions (do not re-litigate), Model tiers, Operating modes (mandatory for every subagent), Orchestration: Wyrdcraeft Canonical DB Migration, Per-phase workflow (mandatory), Phase 8 verification commands, Phase order (1 → 8) (+3 more)

### Community 219 - "Morph Class Browse And Audit Design"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, Audit Command, Browse V1, Canonical Model, Current Facts, Locked Decisions, Morph Class Browse And Audit Design, Non-Goals (+4 more)

### Community 220 - "test_build_pipeline.py"
Cohesion: 0.32
Nodes (11): build_pipeline_db(), _fetch_entry_id(), _fetch_entry_pos(), _fetch_form_entry_id(), _insert_form(), _pos_id(), Connection, fixture (+3 more)

### Community 221 - "Phase B — Forms Foreign Keys (Legacy Strings Remain)"
Cohesion: 0.18
Nodes (11): Phase B — Commit, Phase B — Forms Foreign Keys (Legacy Strings Remain), Phase B — Gate A: Spec review checklist, Phase B — Gate B: Code review checklist, Phase B validation, Task 1: Alembic migration `20260706_02`, Task 2: Form FK resolver service, Task 3: Sink propagation (+3 more)

### Community 222 - "Phase C — Lexicon Shrink (Search Index Only)"
Cohesion: 0.18
Nodes (11): Phase C — Commit, Phase C — Gate A: Spec review checklist, Phase C — Gate B: Code review checklist, Phase C — Lexicon Shrink (Search Index Only), Phase C validation, Task 1: Schema constants + migration `20260706_03`, Task 2: Lexicon build — search keys only, Task 3: Lexicon query — source table joins (+3 more)

### Community 223 - "Phase 2 — Wright § Text Ingest Report"
Cohesion: 0.18
Nodes (11): Files changed, Implementation notes, Manual spot-check, Phase 2 — Wright § Text Ingest Report, Self-review, Summary, Task 2.1 — Markdown § parser, Task 2.2 — WrightSectionTextIngester (+3 more)

### Community 224 - "0007-ocr-pipeline-moves-to-bochord.md"
Cohesion: 0.18
Nodes (7): BT OCR parsing starts with lossless source-grounded AST, BT source acquisition uses a multi-witness download set, BT JP2 witness preparation is library-first, Consequence, Not removed, OCR pipeline moves to bochord, Removed from wyrdcraeft

### Community 225 - "source_db.py"
Cohesion: 0.27
Nodes (10): make_lexicon_source_db(), Path, Helpers for building morphology SQLite databases used in lexicon tests., Build a morphology database seeded with ``forms`` and ``bt_*`` tables. Args:…, Write minimal ``forms`` rows into a morphology SQLite database. Args: db_path:…, Attach minimal Bosworth-Toller ``bt_*`` tables to a morphology database. Args:…, seed_bt_tables(), seed_forms() (+2 more)

### Community 226 - ".build_index_from_bt"
Cohesion: 0.20
Nodes (7): main(), Build the packaged macron index from the bundled Bosworth-Toller source., Path, test_build_index_from_bt_extracts_and_dedupes(), _is_oe_wordlike(), Determine whether a form looks like a lexical OE token. Args: form: Candidate…, Build a macron index from Bosworth-Toller source data. Args: source_path: Path…

### Community 227 - "AGENTS.md"
Cohesion: 0.20
Nodes (8): Architecture (Required), AWS Interaction, Documentation Contract (Required), graphify, Implementation Priority (Required), Post-Implementation Quality Gate (Required), Project Structure (Mandatory), Tooling Preflight (Required)

### Community 228 - "Contributor Covenant 3.0"
Cohesion: 0.20
Nodes (9): Addressing and Repairing Harm, Attribution, Contributor Covenant 3.0, Encouraged Behaviors, Other Restrictions, Our Pledge, Reporting an Issue, Restricted Behaviors (+1 more)

### Community 229 - "Morphology Wright Catalog — Phased Implementation Plan"
Cohesion: 0.20
Nodes (10): Design decisions (locked), Execution options, File map (expected end state), Gate A — Spec review (required after each phase), Gate B — Code review (required after each phase), Morphology Wright Catalog — Phased Implementation Plan, Per phase workflow, Phase validation commands (all phases) (+2 more)

### Community 230 - "Normalized Canonical Schema — Phased Implementation Plan"
Cohesion: 0.20
Nodes (10): Execution options, File map (expected end state), Gate A — Spec review (required after each phase), Gate B — Code review (required after each phase), Global validation (all phases), Locked decisions (do not re-litigate), Normalized Canonical Schema — Phased Implementation Plan, Phase commit (required after Gates A and B) (+2 more)

### Community 231 - "Phase 1 — Reference Catalog Tables"
Cohesion: 0.22
Nodes (9): Phase 1 completion checklist, Phase 1 — Gate A: Spec review, Phase 1 — Gate B: Code review, Phase 1 — Reference Catalog Tables, Task 1: Alembic migration, Task 2: SQLAlchemy models, Task 3: Fixture loader, Task 4: Build integration (+1 more)

### Community 232 - "Phase 4 — Wright Section Text Ingest"
Cohesion: 0.22
Nodes (9): Known limitations, Phase 4 — Gate A: Spec review, Phase 4 — Gate B: Code review, Phase 4 validation, Phase 4 — Wright Section Text Ingest, Task 1: Section parser, Task 2: DB upsert, Task 3: CLI hook (+1 more)

### Community 233 - "Morph Class Browse Surfacing + Wright Audit — Implementation Plan"
Cohesion: 0.22
Nodes (9): Coordinator quick reference — phase order summary, Explicitly deferred (not in this plan), Final whole-branch review, Global risks, Locked constraints (do not re-litigate), Morph Class Browse Surfacing + Wright Audit — Implementation Plan, Open questions, Orchestration (subagent-driven) (+1 more)

### Community 234 - "BT Usage-vs-Sense Cleanup Handoff"
Cohesion: 0.22
Nodes (8): BT Usage-vs-Sense Cleanup Handoff, Current understanding, Key files, Proposed implementation, Suggested review artifact shape, Suggested skills, Useful corpus findings already gathered, Validation required after edits

### Community 235 - "TestEntryGenderPromotion"
Cohesion: 0.33
Nodes (6): BTSense, Unit tests for sense-level gender promotion (Task 5 deferral hook)., TestEntryGenderPromotion, promote_entry_gender_from_senses(), BTSense, Promote a single sense-level gender context to entry-level genders. When the…

### Community 236 - "._load_entry"
Cohesion: 0.22
Nodes (6): Build a sort key that orders senses by hierarchical path. ``4`` sorts before…, sense_path_sort_key(), _genders_from_json(), Deserialize stored gender markers into enum values. Args: payload: JSON array…, Look up consolidated entries by macron-preserving normalized title. Matching…, Reconstruct one consolidated entry from persisted dictionary rows. Args:…

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

### Community 247 - "Session: Morphology Wright Catalog — Phase 2 complete"
Cohesion: 0.29
Nodes (7): Architecture, Deliverables, Known limitations (deferred), Next, Session: Morphology Wright Catalog — Phase 2 complete, Summary, Validation

### Community 248 - "Orchestrator Checkpoint"
Cohesion: 0.29
Nodes (6): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase status, Resume here

### Community 249 - "FormSink"
Cohesion: 0.29
Nodes (5): FormSink, Protocol, Sink contract for finalized emitted form rows., Consume finalized form rows in emitted order. Note: Emitted row semantics…, Initialize a fan-out sink for parity and projection outputs. Note: Fan-out…

### Community 250 - ".__init__"
Cohesion: 0.29
Nodes (4): Path, Initialize a SQLAlchemy sink for emitted morphology rows. Note: Index schema…, Ensure the canonical ``forms`` table and its indexes exist., Tune SQLite for bulk morphology index writes. Side Effects: Sets WAL mode and…

### Community 251 - "generate_golden_merged.py"
Cohesion: 0.47
Nodes (5): _entry_to_dict(), main(), _parse_and_segment(), Parse and segment one raw BT line., Convert a BTConsolidatedEntry to a serialisable dict.

### Community 252 - "Wright OE Grammar §§70-92 (i-umlaut, breaking, palatalization of vowels)"
Cohesion: 0.47
Nodes (5): Wright OE Grammar §§70-92 (i-umlaut, breaking, palatalization of vowels), Wright Umlaut Skew OCR Fixture (Markdown, clean transcription), Wright Umlaut Skew OCR Fixture (Skewed scan PDF, §§70-92), The Seafarer (Old English poem, test fixture), Old English Bosworth-Toller Dictionary Text

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
Cohesion: 0.33
Nodes (6): ABBREVIATIONS, CONTENTS, INTRODUCTION, PREFACE, SELECT LIST OF BOOKS USED, Wright & Wright (1908), "Old English Grammar", Oxford University Press

### Community 260 - "Phase 1 Morph-Class Browse Report"
Cohesion: 0.40
Nodes (5): Files changed, Phase 1 Morph-Class Browse Report, Self-review findings, Test commands and output summary, What I implemented

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

### Community 271 - "_format_entry_text"
Cohesion: 0.50
Nodes (4): _format_entry_text(), _format_sense_label(), Render one sense label with trailing punctuation for text output. Args: label:…, Render one consolidated dictionary entry as human-readable text. Args: entry:…

### Community 272 - "CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}"
Cohesion: 0.50
Nodes (4): A. THE VOWELS, B. THE CONSONANTS, CHAPTER I: ORTHOGRAPHY AND PRONUNCIATION {#chapter-1}, STRESS (ACCENT)

### Community 273 - "CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}"
Cohesion: 0.50
Nodes (4): CHAPTER X: THE OE. DEVELOPMENT OF THE GENERAL GERMANIC CONSONANT-SYSTEM {#chapter-10}, The Liquids, The Nasals, The Semivowels

## Ambiguous Edges - Review These
- `task-phase1-morph-class-browse-report.md` → `task-phase2-wright-text-ingest-report.md`  [AMBIGUOUS]
  doc/sessions/task-phase2-wright-text-ingest-report.md · relation: references
- `BT Dictionary Structuring Workflow runbook` → `Old English OCR Pipeline runbook`  [AMBIGUOUS]
  doc/source/runbook/old_english_ocr_pipeline.rst · relation: semantically_similar_to
- `fixture_prose.txt (Mark gospel OE prose fixture)` → `Bosworth-Toller Anglo-Saxon Dictionary (source text)`  [AMBIGUOUS]
  tests/fixtures/fixture_prose.txt · relation: semantically_similar_to
- `wright_nouns2.md (OCR ground truth, cyning/engel/heofon declension)` → `Old English phonology: vowels, umlaut, ablaut`  [AMBIGUOUS]
  tests/fixtures/ocr/wright_nouns2.md · relation: conceptually_related_to
- `wright_phonology2.md (umlaut/breaking OCR fixture)` → `wright_toc.md (Table of Contents + Preface + Select List of Books, OCR fixture)`  [AMBIGUOUS]
  tests/fixtures/ocr/wright_toc.md · relation: references
- `wright_phonology2.md (umlaut/breaking OCR fixture)` → `wright_umlaut.md (umlaut/breaking recap, duplicate-content OCR fixture)`  [AMBIGUOUS]
  tests/fixtures/ocr/wright_umlaut.md · relation: semantically_similar_to
- `The Seafarer (Old English poem, test fixture)` → `Old English Bosworth-Toller Dictionary Text`  [AMBIGUOUS]
  tests/fixtures/seafarer.txt · relation: conceptually_related_to

## Knowledge Gaps
- **1003 isolated node(s):** `release.sh script`, `wyrdcraeft`, `IPA_AUDIO`, `$schema`, `$id` (+998 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `task-phase1-morph-class-browse-report.md` and `task-phase2-wright-text-ingest-report.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `BT Dictionary Structuring Workflow runbook` and `Old English OCR Pipeline runbook`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `fixture_prose.txt (Mark gospel OE prose fixture)` and `Bosworth-Toller Anglo-Saxon Dictionary (source text)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `wright_nouns2.md (OCR ground truth, cyning/engel/heofon declension)` and `Old English phonology: vowels, umlaut, ablaut`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `wright_phonology2.md (umlaut/breaking OCR fixture)` and `wright_toc.md (Table of Contents + Preface + Select List of Books, OCR fixture)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `wright_phonology2.md (umlaut/breaking OCR fixture)` and `wright_umlaut.md (umlaut/breaking recap, duplicate-content OCR fixture)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `The Seafarer (Old English poem, test fixture)` and `Old English Bosworth-Toller Dictionary Text`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._