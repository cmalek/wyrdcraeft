# Graph Report - wyrdcraeft  (2026-10-02)

## Corpus Check
- 354 files · ~5,284,109 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5513 nodes · 11035 edges · 307 communities (259 shown, 39 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 707 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4140c0b8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BTSenseSegmenter
- test_sense_segmenter.py
- cli/settings.py
- create_engine
- test_form_decode.py
- ParadigmClassMapper
- normalize_old_english
- MorphologyGenerateProgressCoordinator
- form_decode.py
- OENormalizer
- DictionaryBuildPipeline
- test_generation_branches.py
- QueryFormRow
- test_line_parser.py
- test_attestation_stripper.py
- _WeakInfDerivationContext
- cli/dictionary.py
- Settings
- WeakVerbGenerator
- reference_snapshots.py
- test_browse_tui.py
- DictionaryBrowseQueryService
- test_morph_catalog_pos.py
- GenerationRunState
- test_markup.py
- tests/conftest.py
- diacritic_disambiguate.py
- dictionary_group
- models/morphology.py
- morphology/test_query_service.py
- File Structure
- models/__init__.py
- RawBlock
- NounFormGenerator
- MorphologyCatalogLoader
- models/dictionary.py
- derive_sound_changed_forms
- etymology_display.py
- noun.py
- SenseMetadataClassifier
- ensure_parts_of_speech
- .ensure_ready
- ingest/pipeline.py
- TEIExporter
- NormalizedTitleJoinIndex
- BTAttestationStripper
- load_normalized_title_join_index
- .load_fixture
- properties
- test_cli_diacritic_disambiguate.py
- ConfigurationError
- markup.py
- browse_tui.py
- build_runner.py
- Session: Morphology Wright Catalog — Phase 2 complete
- BTTargetResolver
- properties
- properties
- test_forms_entry_relinker.py
- resolve_dictionary_db_path
- test_cli_convert.py
- test_loaders.py
- cli
- check_napoleon_gate.py
- Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅
- write_backup_state
- BTSqliteSink
- upgrade_canonical_db
- WrightAuditService
- _row_to_morphology
- OEFilter
- dictionary/test_query_service.py
- GeneratorSession
- 20260706_01_parts_of_speech_and_dictionary_pos.py
- test_build_pipeline.py
- _WeakPainsg1DerivationContext
- enum
- MorphologyDictionaryCleaner
- test_form_fk_resolver.py
- test_corpus_sample.py
- print_info
- BT V2 Parser And Schema Migration
- properties
- BTSourceHeadwordCleaner
- Phase 3 — Forms Link, Query, and Lexicon Surfacing
- Orchestration Guide
- BT Dictionary Parser Rebuild Implementation Plan
- Orchestration Guide
- type
- Orchestration Guide
- Lexicon Architecture Docs Design
- Word
- test_wright_section_text.py
- .parse
- diacritic.py
- required
- recognitionHints
- format_wright_audit_text
- DictionaryBrowseStartupStage
- Configuration: Command Line Tool guide
- DatabaseStartupRuntime
- .__init__
- test_cli_commands.py
- OESyllableBreaker
- DictionaryBrowseApp
- wyrdcraeft dictionary browse
- TestCLIGlobalOptions
- properties
- ADR 0009: Collapse morphology generation callback-soup into PoS generator classes
- Lexicon shrink: drop lexicon_entries/lexicon_forms, keep search_keys
- _WeakPsinsg2DerivationContext
- _NounAssignedIndex
- _label
- read_jsonl_gz
- session.py
- Implementation Slices
- fixture_prose.txt (Mark gospel OE prose fixture)
- GeneratorSession.load_all
- wyrdcraeft 1.1.0 release (2026-03-02)
- .load_from_tei
- browse_query.py
- Batched SQLite sink (25K rows) + bulk PRAGMAs fix for morphology build perf
- Phase 2 — Lemma Morph Class Assignment
- contracts.py
- Morphology Wright catalog — Phase 1 session (2026-07-04)
- .apply
- File map
- infer_bt_pos_from_wordclasses
- Execution order
- pos_inference.py
- DocumentIngestor
- OldEnglishSearchInput
- enum
- BTIndexPipeline
- examples
- enum
- enum
- Morphology Generation Package Import-Cycle Fix Implementation Plan
- 20260703_01_add_normalized_title_columns.py
- Pipeline Changes
- enum
- enum
- wyrdcraeft/settings.py
- 20260704_01_morph_catalog_tables.py
- Dictionary build/browse flow (concept)
- Wyrdcraeft Canonical DB Migration Implementation Plan
- Architecture review — 2026-08-01
- test_prompt_regression.py
- 20260704_02_lemma_morph_classes.py
- 20260707_03_bt_source_blocks_and_rich_senses.py
- LegacyDatabaseResetRequired
- source_keys
- 20260706_02_forms_foreign_keys.py
- enum
- enum
- enum
- parent_id
- StrongVerbGenerator
- Task 1: Define Build Event Models
- wright_sections
- 20260706_03_lexicon_shrink_search_keys.py
- Session State: Lexicon SQLAlchemy Slice 1 Complete
- DictionaryBuildCounters
- enum
- default_bt_source_path
- 20260706_04_drop_forms_legacy_strings.py
- wyrdcraeft Context
- 20260630_01_initial_canonical_schema.py
- test_schema.py
- FormSink
- 20260707_01_drop_search_keys.py
- run_dictionary_browse
- build_session
- test_lemma_morph_assignment.py
- File Structure
- 20260707_02_bt_senses_entry_order_index.py
- .run
- print_error
- lexicon/conftest.py
- .generate_all_forms
- Phase A — Reference Tables and Dictionary POS FKs
- MorphologyCatalogQueryService
- Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns
- create_dict31.pl (legacy Perl morphology generator)
- BTQueryService
- Python coding standards
- build_pipeline.py
- BT Structural Visibility Review
- wyrdcraeft
- set_verb_paradigm
- Phase D — Drop Legacy Form String Columns
- runtime.py
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
- source_db.py
- Dictionary CLI index gate and morph paths Implementation Plan
- BT Usage-vs-Sense Cleanup Handoff
- Global Constraints
- Lexicon Browser BT V2 Adaptation Skeleton
- Orchestration: Wyrdcraeft Canonical DB Migration
- Morph Class Browse And Audit Design
- .palatalize
- Phase B — Forms Foreign Keys (Legacy Strings Remain)
- 0002-normalized-canonical-schema.md
- Phase 2 — Wright § Text Ingest Report
- OCR pipeline moves to bochord
- Two-gate subagent workflow: Gate A spec review, Gate B code review
- LLM and unstructured leave `source convert`
- AGENTS.md
- Contributor Covenant 3.0
- isolated_morphology_app_data pytest fixture (no writes to real app-data DB)
- refactor_baseline.json Perl-parity guardrail for morphology generation
- Phase 1 — Reference Catalog Tables
- Unified dictionary build pipeline replacing morphology/dictionary/lexicon build triangle
- Morph Class Browse Surfacing + Wright Audit — Implementation Plan
- test_dict.txt (BT morphology dictionary test fixture)
- wright-morphology-fixture.schema.json
- split_prose_and_verse_runs
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
- test_assigner_branches.py
- Orchestrator Checkpoint
- DictionaryBuildStage
- source_key
- test_generation_package_imports.py
- TestCLIVersion
- Domain Docs
- normalized_title + lexicon browse — checkpoint 2026-07-03T12:15
- Mission: Machine Assistance For Old English Work
- Mission: Historical Linguistics for Old English Study
- .__init__
- .__init__
- cli.py
- Lemma-level morph class assignment (normalized_title, pos) -> morph_classes
- Issue tracker: Trello
- Subagent task breakdown
- Subagent task breakdown
- Subagent task breakdown
- normalized_title — checkpoint 2026-07-03T12:10
- BT Dictionary Structuring Workflow runbook
- Historical Linguistics for Old English Study Resources
- language
- TestConsoleQuietMode
- Old English c/g Palatalization Rule System
- WrightAuditResult
- source_set
- morphology_row_matches_pos
- features
- .write_json
- release.sh
- 0002-canonical-morphology-db-uses-startup-alembic-migrations.md
- morphClass
- triage-labels.md
- scripts/__init__.py
- quality/__init__.py
- ._no_mixed_prose_and_verse
- machine-assistance/NOTES.md
- 0001-starting-point.md
- oe-grammar/NOTES.md
- teaching/README.md
- ipa-play.js
- THIRD_PARTY_NOTICES.md
- .__init__
- wyrdcraeft
- .__init__
- format_noun_declension
- Verb generators leave `common.py`
- lexicon_source_db
- filter_display_variants
- DictionaryBrowseDataError
- progress.md
- sound_dispatch_flow.py
- Task 8 Report
- _collect_widget_ids
- _insert_inflection_code
- _table_text

## God Nodes (most connected - your core abstractions)
1. `Word` - 150 edges
2. `GeneratorSession` - 126 edges
3. `cli()` - 110 edges
4. `BTSenseSegmenter` - 80 edges
5. `WeakVerbGenerator` - 75 edges
6. `OENormalizer` - 65 edges
7. `BTLineParser` - 64 edges
8. `create_engine()` - 59 edges
9. `upgrade_canonical_db()` - 57 edges
10. `MorphologyCatalogLoader` - 55 edges

## Surprising Connections (you probably didn't know these)
- `Solomon and Saturn dialogue test fixture` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_dialogue.txt → doc/source/overview/format.rst
- `Beowulf opening lines test fixture (poetry)` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_poetry.txt → doc/source/overview/format.rst
- `test_verb_form_generator_imports_from_verb_forms()` --uses--> `VerbFormGenerator`  [INFERRED]
  tests/morphology/test_verb_generator_modules.py → wyrdcraeft/services/morphology/generation/verb_forms.py
- `test_weak_verb_generator_imports_from_weak_verb_forms()` --uses--> `WeakVerbGenerator`  [INFERRED]
  tests/morphology/test_verb_generator_modules.py → wyrdcraeft/services/morphology/generation/weak_verb_forms.py
- `test_dictionary_build_has_no_llm_flags()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_commands.py → wyrdcraeft/cli/cli.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Dictionary build pipeline stage sequence** — doc_source_architecture_dictionary_btlineparser, doc_source_architecture_dictionary_btsensesegmenter, doc_source_architecture_dictionary_bteditorialmerger, doc_source_architecture_dictionary_btsqlitesink, doc_source_architecture_dictionary_formsentryrelinker [EXTRACTED 1.00]
- **Morphology build stage-ordering (catalog seed, class assign, form emission)** — doc_source_architecture_morphology_generatorsession, doc_source_architecture_morphology_morphologycatalogloader, doc_source_architecture_morphology_lemmamorphclassassigner, doc_source_architecture_morphology_sqliteindexsink [EXTRACTED 1.00]
- **Bosworth-Toller dictionary processing pipeline (source, runbooks, fixture)** — doc_source_runbook_bt_dictionary_structuring_workflow_bt_structuring_workflow, doc_source_runbook_macron_list_generation_macron_list_generation, tests_fixtures_dictionary_corpus_sample_bt_corpus_sample_fixture [INFERRED 0.75]
- **wyrdcraeft CLI configuration documentation cluster** — doc_source_overview_configuration_cli_configuration_guide, doc_source_overview_using_cli_cli_usage_guide, doc_source_overview_command_settings_settings_command [INFERRED 0.75]
- **Morphological Paradigm Generation Data Set** — wyrdcraeft_etc_morphology_dict_adj_vb_part_num_adv_noun, wyrdcraeft_etc_morphology_manual_forms, wyrdcraeft_etc_morphology_para_vb [INFERRED 0.75]
- **c/g Palatalization Exception Lists** — wyrdcraeft_etc_diacritic_c_palatalization_force_non_palatalize, wyrdcraeft_etc_diacritic_c_palatalization_force_palatalize, wyrdcraeft_etc_diacritic_g_frontal [INFERRED 0.85]
- **Subagent task reports implementing Wright catalog browse/ingest/audit phases** — doc_sessions_task_phase1_morph_class_browse_report, doc_sessions_task_phase2_wright_text_ingest_report, doc_sessions_task_phase3_wright_text_pane_report, doc_sessions_task_phase4_wright_audit_report [INFERRED 0.85]

## Communities (307 total, 39 thin omitted)

### Community 0 - "BTSenseSegmenter"
Cohesion: 0.04
Nodes (57): _entry_to_comparable(), _load_golden(), merger(), _parse_lines(), parser(), fixture, parametrize, Tests for Phase 04 BTEditorialMerger and BTTargetResolver. (+49 more)

### Community 1 - "test_sense_segmenter.py"
Cohesion: 0.04
Nodes (54): _golden_sense_matches(), _load_golden(), BTSense, fixture, Tests for Phase 03 BTSenseSegmenter., Unit tests for sense-level gender promotion (Task 5 deferral hook)., Unit tests for canonical sense-path normalization., Golden-file acceptance tests: ≥95% exact gloss match required. (+46 more)

### Community 2 - "cli/settings.py"
Cohesion: 0.29
Nodes (10): create_settings(), command, Context, group, pass_context, Settings-related commands., Settings-related commands., Create a new settings file. (+2 more)

### Community 3 - "create_engine"
Cohesion: 0.07
Nodes (38): Config, _bt_entry_id(), _insert_bt_entry(), Path, Tests for catalog-backed morph-class metadata in lexicon browse details., Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions., Seed one catalog assignment row into a temporary lexicon test database., Insert one minimal ``bt_entries`` row into a temporary lexicon test database.… (+30 more)

### Community 4 - "test_form_decode.py"
Cohesion: 0.10
Nodes (28): MorphologyTableInputRow, Tests for morphology function-code decoding., test_build_morphology_table_fills_inflection_from_morph_class_label(), test_build_morphology_table_includes_surface_form_column(), test_build_morphology_table_sorts_adjectives_by_degree_inflection_and_case(), test_decode_noun_plural_neuter_accusative(), test_decode_verb_imperative_plural(), test_decode_verb_inflected_infinitive() (+20 more)

### Community 5 - "ParadigmClassMapper"
Cohesion: 0.08
Nodes (29): mapper(), fixture, Tests for Wright catalog paradigm exemplar mapping., test_adj_paradigm_blind_maps_to_strong_a_o_stem(), test_noun_paradigm_guma_maps_to_weak_n_stem(), test_noun_paradigm_stan_maps_to_masculine_a_stem(), test_past_participle_title_maps_to_past_participle_class(), test_present_participle_title_maps_to_present_participle_class() (+21 more)

### Community 6 - "normalize_old_english"
Cohesion: 0.05
Nodes (52): _entry_to_dict(), main(), _parse_and_segment(), Parse and segment one raw BT line., Convert a BTConsolidatedEntry to a serialisable dict., BTConsolidatedEntry, Canonical dictionary record after editorial merge for one ``(norm_key, pos)``.…, BTEditRecord (+44 more)

### Community 7 - "MorphologyGenerateProgressCoordinator"
Cohesion: 0.03
Nodes (78): test_build_profiler_disabled_emits_nothing(), test_build_profiler_emits_stage_and_sqlite_sections(), CLI tests for remaining morphology commands after build moved to dictionary., test_morphology_build_command_moved_to_dictionary(), test_morphology_clean_dictionary_help(), test_morphology_generate_command_is_gone(), test_morphology_group_help(), test_morphology_query_help() (+70 more)

### Community 8 - "form_decode.py"
Cohesion: 0.10
Nodes (43): test_build_adjective_sidebar_uses_payload_inflection(), test_build_adverb_sidebar_decodes_superlative_su_code(), test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms(), test_build_noun_paradigm_grid_groups_case_and_number(), test_build_noun_paradigm_grid_includes_instrumental_case(), test_build_noun_paradigm_grid_uses_fk_joined_codes_without_legacy_classes(), test_build_verb_sidebar_accepts_lowercase_function_codes(), test_build_verb_sidebar_places_ps_su_sg_on_subjunctive_sing_row() (+35 more)

### Community 9 - "OENormalizer"
Cohesion: 0.06
Nodes (51): Match, parametrize, test_canonicalize_inflection_code_reference(), test_eth2thorn_reference(), test_iumlaut_reference(), test_move_accents_reference(), test_normalize_bt_display_spelling_is_idempotent(), test_normalize_bt_display_spelling_reference() (+43 more)

### Community 10 - "DictionaryBuildPipeline"
Cohesion: 0.16
Nodes (14): AnyDictionaryBuildEvent, DictionaryBuildLogLevel, DictionaryBuildPipeline, Orchestrate canonical dictionary rebuild, form relink, and follow-on refreshes.…, Infer missing dictionary POS values from stored morphology forms. Args:…, Return the number of dictionary rows currently carrying unknown POS. Args:…, Mark one stage active across progress and typed event surfaces. Args: stage:…, Advance optional build progress for one stage update. Args: stage: Stage being… (+6 more)

### Community 11 - "test_generation_branches.py"
Cohesion: 0.11
Nodes (43): _base_formhash(), _make_word(), MonkeyPatch, Capture emitted ``form_data`` payloads without TSV geminate expansion., Record one emitted row payload., _RecordingSink, _strong_generator(), _strong_inf_context() (+35 more)

### Community 12 - "QueryFormRow"
Cohesion: 0.10
Nodes (22): test_infer_bt_pos_filter_maps_unambiguous_noun(), test_infer_bt_pos_filter_returns_none_for_mixed_wordclasses(), QueryFormRow, Indexed morphology row enriched with normalized query keys., dictionary_join_entry_to_dict(), _form_lookup_sql(), _infer_bt_pos_filter(), _lemma_lookup_sql() (+14 more)

### Community 13 - "test_line_parser.py"
Cohesion: 0.08
Nodes (26): parametrize, Tests for Phase 02 Bosworth-Toller line parser., Skipped lines return explicit reasons needed by downstream reporting., Substitute target extraction captures ``for X in Dict`` phrases., Variant and noun-gender extraction uses pre-POS prefix conventions., Parser emits display headwords with Wright-style diphthong long marks., Trailing bracket blocks are preserved for later etymology handling., Deletion references are parsed from text after the ``Dele`` marker. (+18 more)

### Community 14 - "test_attestation_stripper.py"
Cohesion: 0.07
Nodes (28): fixture, parametrize, Tests for Phase 03 BTAttestationStripper., ``_is_citation_span`` returns True for grammar/editorial markers and citations., ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes., ``_strip_editorial_directive`` removes leading supplement editorial verbs., Unit tests for module-level helper functions., ``_is_grammatical_abbrev`` distinguishes grammar markers from glosses. (+20 more)

### Community 15 - "_WeakInfDerivationContext"
Cohesion: 0.14
Nodes (10): Immutable context for weak infinitive-derived emitter callbacks. Args:…, _WeakInfDerivationContext, Attach a present participle emitted from infinitive-derived weak rows. Side…, Emit weak infinitive-derived branches for one principal-part context. Side…, Check whether a form-parts base ends in a Perl-style vowel segment. Side…, Check whether a form-parts base ends with the normalized vowel regex. Side…, Emit weak-verb forms derived from infinitives for the general class2 branch.…, Emit weak-verb forms for one variant of the class2-special infinitive branch.… (+2 more)

### Community 16 - "cli/dictionary.py"
Cohesion: 0.11
Nodes (35): audit_wright(), browse(), build(), clean_headwords(), _default_morphology_data_dir(), _default_source_path(), _format_entry_text(), _format_sense_label() (+27 more)

### Community 17 - "Settings"
Cohesion: 0.06
Nodes (30): BaseSettings, Exception, PydanticBaseSettingsSource, patch, Unit tests for configuration settings. Tests the new OpenAI and summary…, Test that settings fields have proper descriptions., Test that model_config is properly configured., Test output format validation. (+22 more)

### Community 18 - "WeakVerbGenerator"
Cohesion: 0.07
Nodes (32): Replace the three weak derived-branch entry points with recorders., _record_weak_branches(), test_dispatch_weak_derived_forms_selects_inf_branch(), test_dispatch_weak_derived_forms_selects_painsg1_branch(), test_dispatch_weak_derived_forms_selects_psinsg2_branch(), test_dispatch_weak_derived_forms_skips_item_shape_mode(), test_dispatch_weak_derived_forms_unknown_para_id(), test_dispatch_weak_principal_part_derivations_emits_papt_only() (+24 more)

### Community 19 - "reference_snapshots.py"
Cohesion: 0.14
Nodes (24): build_session(), canonical_sort_rows(), canonicalize_form_rows(), form_rows_for_stage(), full_flow_metadata(), full_flow_rows(), generate_reference_snapshots(), paradigm_snapshot_rows() (+16 more)

### Community 20 - "test_browse_tui.py"
Cohesion: 0.14
Nodes (45): anyio, _bt_entry_id(), _details_text(), _insert_entry(), _pos_id(), Path, Shell-level tests for the dictionary Textual browse scaffold., Insert linked morphology rows for the ``abbad`` noun entry. (+37 more)

### Community 21 - "DictionaryBrowseQueryService"
Cohesion: 0.13
Nodes (30): _bt_entry_id(), _insert_bt_sense(), _insert_entry(), _insert_inflection_code(), lexicon_source_db(), _next_entry_order(), _pos_id(), Connection (+22 more)

### Community 22 - "test_morph_catalog_pos.py"
Cohesion: 0.11
Nodes (31): parametrize, Tests for morphology catalog POS normalization helpers., test_catalog_pos_from_bt_pos_cli_aliases(), test_catalog_pos_from_bt_pos_join_values(), test_catalog_pos_from_bt_pos_raises_for_unmapped(), test_catalog_pos_from_wordclass(), test_catalog_pos_from_wordclass_unknown_returns_none(), test_pos_id_from_bt_pos() (+23 more)

### Community 23 - "GenerationRunState"
Cohesion: 0.05
Nodes (71): NamedTuple, _adj_print(), _build_superlative_title_array(), _build_weak_title_array(), _dedupe_preserve_first(), _emit_superlative_strong_forms(), _emit_weak_degree_forms(), _finalize_degree_titles() (+63 more)

### Community 24 - "test_markup.py"
Cohesion: 0.06
Nodes (43): Path, test_build_index_from_bt_extracts_and_dedupes(), Path, C before i/ī in any position palatalizes (Rule C)., Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)., gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar., Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc., Cyning (c + y from u) remains non-palatalized; blocklist and only-back. (+35 more)

### Community 25 - "tests/conftest.py"
Cohesion: 0.15
Nodes (19): cli_context(), isolated_morphology_app_data(), isolated_morphology_index_db(), lexicon_source_db(), mock_console(), mock_settings(), fixture, Path (+11 more)

### Community 26 - "diacritic_disambiguate.py"
Cohesion: 0.07
Nodes (51): Layout, test_fetch_bt_search_entries_uses_search_endpoint(), test_filter_bt_entries_by_normalized_form_empty_list_returns_empty(), test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others(), test_filter_bt_entries_by_normalized_form_no_matches_returns_empty(), test_filter_bt_entries_by_normalized_form_preserves_order(), test_merge_bt_entries_deduplicates_and_reindexes(), test_normalize_bt_spelling_converts_acute_to_macron() (+43 more)

### Community 27 - "dictionary_group"
Cohesion: 0.67
Nodes (3): dictionary_group(), group, Dictionary command group.

### Community 28 - "models/morphology.py"
Cohesion: 0.08
Nodes (39): _make_part(), _make_variant(), _make_verb_paradigm(), test_process_paradigm_routes_variant_payload_from_flow(), test_process_part_routes_strong_generation_from_flow(), test_process_part_routes_weak_generation_from_flow(), GeneratedForm, MorphClassQueryMetadata (+31 more)

### Community 29 - "morphology/test_query_service.py"
Cohesion: 0.06
Nodes (61): Namespace, _build_output_sink(), main(), _parse_args(), Run cProfile against the morphology adjective generation stage., Profile ``MorphologyGenerationFacade.generate_adjectives`` and print…, Build the output sink used while profiling adjective generation. Keyword Args:…, Run manual and verb stages needed before adjective generation. Args: session:… (+53 more)

### Community 30 - "File Structure"
Cohesion: 0.11
Nodes (18): Addendum: Tasks 11-14 (added after final whole-branch review), File Structure, Global Constraints, Morphology Generation Class Refactor Implementation Plan, Task 10: Delete the now-empty `generators/` directory, Task 11: Build paradigm-dispatch tables for `NounFormGenerator` and `AdjectiveFormGenerator`, Task 12: Collapse `StrongVerbGenerator`'s callback threading into direct method calls, Task 13: Collapse `WeakVerbGenerator`'s callback threading into direct method calls (+10 more)

### Community 31 - "models/__init__.py"
Cohesion: 0.12
Nodes (30): fixture, sample_doc(), test_tei_export_attributes(), test_tei_export_basic(), test_tei_export_structure(), Test importing Beowulf from TEI XML., test_tei_import_beowulf(), test_tei_roundtrip_minimal_prose() (+22 more)

### Community 32 - "RawBlock"
Cohesion: 0.08
Nodes (30): dialogue_text(), prose_text(), fixture, patch, Unmarked verse gets 1-based line numbers within the section., _t(), test_canonical_converter_prose(), test_canonical_converter_verse() (+22 more)

### Community 33 - "NounFormGenerator"
Cohesion: 0.05
Nodes (35): _build_stem_daeg_pl(), _form_from_parts(), _is_ge_collective(), _noun_print(), NounFormGenerator, FormOutput, ``strengu`` paradigm (feminine u-stems). Args: word: The word to process.…, ``hand``/``feld`` paradigm (feminine/masculine consonant stems). Args: word:… (+27 more)

### Community 34 - "MorphologyCatalogLoader"
Cohesion: 0.07
Nodes (59): DeclarativeBase, Seed one catalog assignment row into a temporary lexicon test database., _seed_catalog_assignment(), Path, Build a small morphology slice and verify normalized FK columns on forms., test_catalog_loader_ensure_seeded_refresh(), test_catalog_loader_ensure_seeded_skips_when_populated(), test_catalog_loader_is_idempotent() (+51 more)

### Community 35 - "models/dictionary.py"
Cohesion: 0.03
Nodes (82): parametrize, Tests for BT display spelling normalization., Normalize representative real BT headword spellings from ``oe_bt.txt``., Normalizing an already-normalized spelling is a no-op., test_bt_spelling_normalizer_matches_oe_normalizer(), test_normalize_is_idempotent(), test_normalize_real_bt_diphthong_cases(), test_relocate_moves_attestation_tail_to_last_sense() (+74 more)

### Community 36 - "derive_sound_changed_forms"
Cohesion: 0.12
Nodes (18): SoundManualEmitter, SoundSourceFormEmitter, test_derive_sound_changed_forms_psinsg2_gst_chain(), test_derive_sound_changed_forms_psinsg2_ngst_chain(), test_derive_sound_changed_forms_psinsg3_td_th_chain(), test_emit_sound_changed_forms_psinsg2_probability_delta(), test_emit_sound_changed_forms_psinsg3_zero_delta(), test_emit_sound_changed_from_source_keeps_source_ordering() (+10 more)

### Community 37 - "etymology_display.py"
Cohesion: 0.07
Nodes (48): Tests for etymology parsing and browse table formatting., test_format_etymology_display_renders_table_headers(), test_misplaced_attestation_is_flagged(), test_mixed_attestation_and_cognates_split(), test_parse_cognate_chain_with_citation(), test_parse_colon_separated_lang_chain(), test_parse_multiple_german_cognates(), test_parse_norse_words_with_latin_tail() (+40 more)

### Community 38 - "noun.py"
Cohesion: 0.10
Nodes (28): _append_short_syllable_front_vowel_heuristic(), _append_suffix_heuristics(), _append_terminal_a_heuristic(), _append_terminal_e_heuristic(), _apply_final_fallback(), _apply_noun_heuristics(), _assign_by_wright(), _extract_heuristic_vowel() (+20 more)

### Community 39 - "SenseMetadataClassifier"
Cohesion: 0.06
Nodes (27): Unit tests for sense-prefix metadata classification., TestSenseMetadataClassifier, _has_substantive_gloss(), _looks_like_gloss_start(), _normalize_case(), _normalize_gender(), _normalize_modifier(), Normalize one modifier abbreviation token. Args: token: Raw modifier token… (+19 more)

### Community 40 - "ensure_parts_of_speech"
Cohesion: 0.11
Nodes (31): _load_fixture_rows(), Connection, Path, Tests for normalized POS and inflection-code seed fixtures., Read one JSON fixture file used by the POS seed tests., Return the current row count for one reference table., _row_count(), test_inflection_seed_covers_observed_snapshot_function_codes() (+23 more)

### Community 41 - ".ensure_ready"
Cohesion: 0.11
Nodes (12): _format_backup_prompt_text(), Run the startup database decision tree once. Raises: DatabaseMigrationError:…, Replace any existing canonical DB with a fresh Alembic-managed file. Side…, Create one retained backup and update the canonical sidecar state. Args:…, Apply Alembic migrations and emit the locked success narration. Side Effects:…, Run one narrated migration attempt with shared failure recovery. Keyword Args:…, Run the Alembic bootstrap and upgrade path. Side Effects: Creates the SQLite…, Read the current Alembic revision from the canonical database. Returns: Current… (+4 more)

### Community 42 - "ingest/pipeline.py"
Cohesion: 0.08
Nodes (33): ProgressCallback, parametrize, Test that deterministic ingestion of text files matches the golden JSON…, test_deterministic_ingestion_regression(), BaseDocumentIngestor, DocumentIngestor, HeuristicDocumentIngestor, ingest_auto() (+25 more)

### Community 43 - "TEIExporter"
Cohesion: 0.19
Nodes (13): test_tei_exporter_interface(), Any, Create the publication statement. Args: doc: The document to export. parent:…, Create the source description. Args: doc: The document to export. parent: The…, Emit a section and its content recursively. Args: sec: The section to export.…, Apply common metadata attributes to a node. Args: node: The node to apply the…, Emit prose paragraphs, handling speakers. Args: paragraphs: The paragraphs to…, Exporter for TEI XML format using delb for XML manipulation. (+5 more)

### Community 44 - "NormalizedTitleJoinIndex"
Cohesion: 0.11
Nodes (21): _index(), Unit tests for NormalizedTitleJoinIndex., test_resolve_all_exactly_one_title_across_pos(), test_resolve_all_no_match(), test_resolve_all_pos_direct_multiple_matches(), test_resolve_all_pos_direct_single_match(), test_resolve_all_variant_with_pos_filter(), test_resolve_all_variant_without_pos_filter() (+13 more)

### Community 45 - "BTAttestationStripper"
Cohesion: 0.08
Nodes (19): Unit tests for BTAttestationStripper.strip., ``:--`` is the canonical attestation separator., Combined gender-gloss italic spans like ``<I>f. An oak:</I>`` yield clean…, ``</I>--`` (colon inside italic) is handled as the attestation separator., Grammar markers like ``<I>p.</I>`` and ``<I>pp.</I>`` are removed from the…, ``[…]`` bracket blocks are stripped before gloss extraction., An ``<I>Add:</I>`` span with no following gloss produces an empty string., ``Substitute:`` editorial prefix is removed from the kept gloss span. (+11 more)

### Community 46 - "load_normalized_title_join_index"
Cohesion: 0.13
Nodes (17): _fetch_rows(), load_normalized_title_join_index(), Connection, Shared loader for normalized-title dictionary join indexes., Fetch three-column join rows from SQLAlchemy or SQLite connections. Args:…, Build a dictionary join index from canonical ``bt_entries`` and variants. Args:…, _bt_pos_from_code(), Convert a canonical POS code back to the BT enum used by CLI payloads. Args:… (+9 more)

### Community 47 - ".load_fixture"
Cohesion: 0.09
Nodes (18): LoadResult, Any, Path, Session, Upsert catalog rows from one packaged Wright fixture JSON file. Args: path:…, Load the fixture when the catalog is empty or refresh is requested. Args: path:…, Read and parse one Wright catalog fixture file. Args: path: Path to the JSON…, Validate required fixture structure before writing catalog rows. Args: payload:… (+10 more)

### Community 48 - "properties"
Cohesion: 0.12
Nodes (18): 1.0, $ref, description, items, minItems, type, properties, morph_classes (+10 more)

### Community 49 - "test_cli_diacritic_disambiguate.py"
Cohesion: 0.10
Nodes (39): _minimal_index_payload(), _mock_bt_lookup(), fixture, Path, Minimal macron index payload for diacritic add/delete tests., test_diacritic_add_fails_when_exists_without_force(), test_diacritic_add_fails_when_key_in_ambiguous_even_with_force(), test_diacritic_add_force_overwrites() (+31 more)

### Community 50 - "ConfigurationError"
Cohesion: 0.28
Nodes (7): ConfigurationError, FileError, OejsonextractorError, Raised when file I/O operations fail., Base exception for all wyrdcraeft errors., Raised when settings or configuration fails., Validate settings and ensure required directories exist. Raises:…

### Community 51 - "markup.py"
Cohesion: 0.10
Nodes (30): patch, With only input given, paths default to stem + infix + extension., test_source_mark_diacritics_default_paths(), test_source_mark_diacritics_writes_text_and_ambiguities(), test_source_mark_diacritics_writes_unknowns_file(), AmbiguityOption, DiacriticRestorationResult, MacronAmbiguity (+22 more)

### Community 52 - "browse_tui.py"
Cohesion: 0.06
Nodes (50): _dominant_paradigm(), _group_morphology_rows(), MorphologyGroup, MorphologyRow, Sidebar grouping of morphology rows by wordclass and function. Attributes:…, Pick the most common non-empty morphology paradigm label for one entry. Args:…, Group raw morphology rows by ``wordclass`` and ``function``. Args: rows:…, One raw projected morphology row for sidebar rendering. Note: ``wordclass`` and… (+42 more)

### Community 53 - "build_runner.py"
Cohesion: 0.13
Nodes (26): Path, Morphology input path defaults live on the generation runner., test_packaged_default_morphology_data_dir_exists(), test_resolve_morphology_input_paths_keeps_overrides(), test_resolve_morphology_input_paths_uses_data_dir_defaults(), test_validate_morphology_input_paths_raises_for_missing_file(), _apply_limit(), default_morphology_data_dir() (+18 more)

### Community 54 - "Session: Morphology Wright Catalog — Phase 2 complete"
Cohesion: 0.15
Nodes (7): Architecture, Deliverables, Known limitations (deferred), Next, Session: Morphology Wright Catalog — Phase 2 complete, Summary, Validation

### Community 55 - "BTTargetResolver"
Cohesion: 0.11
Nodes (13): Unit tests for BTTargetResolver., TestBTTargetResolver, legacy_bt_sense(), Build a minimal ``BTSense`` from legacy label and gloss fields. Args:…, Initialise the builder with an optional target resolver. Args: resolver:…, BTTargetResolver, BTSense, Convert a slug field (third ``@``-separated field) to a normalised lookup key.… (+5 more)

### Community 56 - "properties"
Cohesion: 0.06
Nodes (34): type, type, type, properties, type, type, type, type (+26 more)

### Community 57 - "properties"
Cohesion: 0.06
Nodes (34): description, minLength, type, $ref, default, description, enum, type (+26 more)

### Community 58 - "test_forms_entry_relinker.py"
Cohesion: 0.16
Nodes (24): _fetch_form_entry_id(), _insert_bt_entry(), _insert_bt_variant(), _insert_form(), _pos_id(), Connection, fixture, Path (+16 more)

### Community 59 - "resolve_dictionary_db_path"
Cohesion: 0.15
Nodes (14): test_resolve_dictionary_db_path_prefers_explicit_override(), test_resolve_dictionary_db_path_uses_attach_mode_tables(), test_resolve_dictionary_db_path_uses_sibling_dictionary(), _db_has_table(), _forms_has_morph_class_id(), _morphology_db_has_bt_entries(), Connection, Path (+6 more)

### Community 60 - "test_cli_convert.py"
Cohesion: 0.29
Nodes (6): Test the convert command with a missing source file., Test the convert command without LLM (heuristic mode)., test_convert_command_missing_source(), test_convert_command_no_llm(), test_convert_rejects_http_source(), test_convert_rejects_use_llm_flag()

### Community 61 - "test_loaders.py"
Cohesion: 0.13
Nodes (19): fixture, source_loader(), test_load_from_file_rejects_pdf(), test_load_from_file_text(), test_load_from_file_unsupported(), test_source_loader_load_file(), test_source_loader_rejects_http_url(), test_tei_source_loader_load_tei() (+11 more)

### Community 62 - "cli"
Cohesion: 0.13
Nodes (37): _build_unified_source_db(), _fetch_entry_id(), _fetch_form_entry_id(), _insert_form(), _morphology_data_dir(), _pos_id(), Connection, Path (+29 more)

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
Cohesion: 0.07
Nodes (52): Row, slow, _index_with_attach(), Path, Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite., Seed the canonical ``forms`` table via the real SQLAlchemy sink., _seed_forms_table(), test_attach_missing_db_fails_for_canonical_only_mode() (+44 more)

### Community 67 - "upgrade_canonical_db"
Cohesion: 0.11
Nodes (32): catalog_db(), fixture, Path, test_from_db_path_uses_isolated_database(), _dictionary_line(), _make_audit_source_dir(), _manual_form_line(), _para_vb_line() (+24 more)

### Community 68 - "WrightAuditService"
Cohesion: 0.09
Nodes (23): _AssignedMorphClass, _catalog_pos_from_word(), LegacyWrightRow, _parse_encoded_wright_sections(), Engine, Path, Session, In-memory deterministic assignment payload keyed by lemma title and POS. (+15 more)

### Community 69 - "_row_to_morphology"
Cohesion: 0.33
Nodes (6): Any, RowMapping, Project one SQLite row into a ``MorphologyRow`` dataclass. Args: row: Mapping…, _row_to_morphology(), inflection_strength_from_morph_class(), Derive strong/weak inflection labels from catalog morph-class metadata. Keyword…

### Community 70 - "OEFilter"
Cohesion: 0.25
Nodes (6): test_oe_filter(), OEFilter, Logic for filtering Old English text from raw blocks., Initialize Old English detection state., Test if a block of text looks like Old English. Args: text: The text to test.…, Filter out blocks that do not look like Old English. A block is kept if at…

### Community 71 - "dictionary/test_query_service.py"
Cohesion: 0.07
Nodes (51): corpus_index_db(), _index_fixture(), fixture, Path, Unit and integration tests for BTQueryService., sample_index_db(), _seed_forms_table(), test_bt_query_service_constructs_on_empty_migrated_db() (+43 more)

### Community 72 - "GeneratorSession"
Cohesion: 0.04
Nodes (44): setter, canonical_sort_rows(), Build a stable digest string for richer assertion diffs. Args: rows: Rows to…, Return deterministically sorted shallow-copied records. Args: rows: Input row…, stable_json_lines_digest(), test_is_weak_item_shape_window_bounds(), test_should_use_weak_item_shape_for_irregular_paradigm_types(), _paradigm_rows() (+36 more)

### Community 73 - "20260706_01_parts_of_speech_and_dictionary_pos.py"
Cohesion: 0.16
Nodes (23): _assert_no_null_pos_ids(), _assert_no_null_text_pos(), downgrade(), _downgrade_bt_entries(), _downgrade_lemma_morph_classes(), _downgrade_morph_classes(), Connection, Replace legacy BT text POS and headword columns with normalized fields. Args:… (+15 more)

### Community 74 - "test_build_pipeline.py"
Cohesion: 0.18
Nodes (23): build_pipeline_db(), _fetch_entry_id(), _fetch_entry_pos(), _fetch_form_entry_id(), _insert_form(), _pos_id(), Connection, fixture (+15 more)

### Community 75 - "_WeakPainsg1DerivationContext"
Cohesion: 0.12
Nodes (11): Immutable context for weak ``PaInSg1``-derived emitter callbacks. Args:…, _WeakPainsg1DerivationContext, Emit one weak ``PaInSg1`` row for a selected vowel variant. Side Effects:…, Emit one manual row from a pre-bound weak ``PaInSg1`` context. Side Effects:…, Attach a past participle emitted from a weak ``PaInSg1`` branch. Side Effects:…, Emit one weak ``PsInSg2`` form row from a pre-bound derivation context. Side…, Emit weak ``PaInSg1``-derived branches for one principal-part context. Side…, Generate and print a form. Note: Kept as a method (not a bare call into… (+3 more)

### Community 76 - "enum"
Cohesion: 0.08
Nodes (26): common, comparative, dual, feminine, first, masculine, neuter, plural (+18 more)

### Community 77 - "MorphologyDictionaryCleaner"
Cohesion: 0.06
Nodes (38): parametrize, Tests for morphology dictionary TSV cleanup., test_clean_dictionary_fixes_bt_diphthongs_in_col2(), test_clean_dictionary_lowercases_col2_dedupes_and_backups(), test_clean_dictionary_raises_when_source_missing(), test_should_lowercase_col2_only_all_upper_letters(), patch, Tests for the main module. (+30 more)

### Community 78 - "test_form_fk_resolver.py"
Cohesion: 0.18
Nodes (24): _insert_bt_entry(), _insert_bt_variant(), _insert_lemma_assignment(), Connection, fixture, Path, Tests for morphology form foreign-key resolution., resolver_db() (+16 more)

### Community 79 - "test_corpus_sample.py"
Cohesion: 0.33
Nodes (6): _load_manifest(), Smoke tests for the stratified Bosworth-Toller corpus sample fixture., Ensure corpus fixture is present and within phase-02b size constraints., Parse every corpus line and require deterministic parse or explicit skip., test_corpus_sample_lines_parse_without_raising(), test_corpus_sample_manifest_and_line_count_bounds()

### Community 80 - "print_info"
Cohesion: 0.12
Nodes (21): Test info printing functions., Test basic info printing., Test info panel has correct styling., TestPrintInfo, _mark_diacritics_derived_path(), argument, command, Context (+13 more)

### Community 81 - "BT V2 Parser And Schema Migration"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT V2 Parser And Schema Migration, CLI Output Contract, Context, Dependencies, Follow-on Work, Locked Decisions, Problem Classes BT V2 Must Fix (+4 more)

### Community 82 - "properties"
Cohesion: 0.12
Nodes (17): description, minLength, type, default, description, type, citation_apa, notes (+9 more)

### Community 83 - "BTSourceHeadwordCleaner"
Cohesion: 0.12
Nodes (18): parametrize, Tests for Bosworth-Toller oe_bt.txt headword cleanup., test_clean_headwords_leaves_later_bold_tags_unchanged(), test_clean_headwords_lowercases_first_bold_and_backups(), test_clean_headwords_raises_when_source_missing(), test_should_lowercase_headword_only_all_upper_letters(), BTSourceHeadwordCleaner, BTSourceHeadwordCleanupResult (+10 more)

### Community 84 - "Phase 3 — Forms Link, Query, and Lexicon Surfacing"
Cohesion: 0.20
Nodes (10): Future (post Phase 3), Phase 3 — Forms Link, Query, and Lexicon Surfacing, Phase 3 — Gate A: Spec review, Phase 3 — Gate B: Code review, Phase 3 validation, Task 1: Schema migration, Task 2: Sink propagation, Task 3: Query service (+2 more)

### Community 85 - "Orchestration Guide"
Cohesion: 0.07
Nodes (26): 10. Failure handling, 11. Phase briefs, 12. Definition of done, 1. Architecture, 2. Locked decisions, 3. Files, 4. Phase order, 5. Orchestrator workflow (+18 more)

### Community 86 - "BT Dictionary Parser Rebuild Implementation Plan"
Cohesion: 0.14
Nodes (14): BT Dictionary Parser Rebuild Implementation Plan, Commit strategy, Domain/runtime models, Execution handoff, File map, Live corpus findings to design against, Locked decisions (do not re-litigate), Package/runtime assets (+6 more)

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

### Community 91 - "Word"
Cohesion: 0.04
Nodes (62): _make_word(), Regression tests for the GeneratorSession -> WordPool/GenerationRunState split.…, test_session_composes_word_pool_and_run_state(), test_word_pool_append_participle(), test_word_pool_categorize_matches_load_all_categorization(), Lexical entry schema carrying POS flags and paradigm state for one lemma., Word, _assign_verb_by_advanced_diacritics() (+54 more)

### Community 92 - "test_wright_section_text.py"
Cohesion: 0.09
Nodes (32): catalog_db(), fixture, Path, Tests for Wright section markdown parsing and catalog text ingest., test_ingest_result_counts_and_warnings(), test_ingester_force_overwrites_existing_text(), test_ingester_is_idempotent_without_force(), test_ingester_updates_null_sections() (+24 more)

### Community 93 - ".parse"
Cohesion: 0.09
Nodes (12): Parse one source line into ``RawBTLine`` plus phase-02 metadata. Args:…, Classify one line into ``BTLineKind``. Args: body: Main ``@`` field body…, Detect whether a line is primarily a cross-reference. Args: body: Main ``@``…, Extract the POS prefix fragment immediately after the first headword. Args:…, Extract alternate headword spellings from the pre-POS plain-text prefix. Args:…, Apply display spelling normalization to variants with de-duplication. Args:…, Extract substitute target text from ``for X in Dict`` patterns. Args: body:…, Extract reference fragments listed after ``Dele`` markers. Args: body: Main… (+4 more)

### Community 94 - "diacritic.py"
Cohesion: 0.21
Nodes (15): diacritic_add(), diacritic_delete(), diacritic_group(), _load_macron_index_payload(), argument, command, group, option (+7 more)

### Community 95 - "required"
Cohesion: 0.13
Nodes (15): aliases, canonical_name, features, id, is_assignable, mapping_rationale, modern_class, paradigmatic_words (+7 more)

### Community 96 - "recognitionHints"
Cohesion: 0.14
Nodes (14): citation_apa, retrieved_date, source_key, url, $defs, recognitionHints, source, additionalProperties (+6 more)

### Community 97 - "format_wright_audit_text"
Cohesion: 0.10
Nodes (24): _append_sample_block(), BlankLegacyButClassifiedIssue, ContradictionIssue, _display_legacy_wright(), _format_blank_but_classified_issue(), _format_contradiction_issue(), _format_malformed_issue(), _format_row_prefix() (+16 more)

### Community 98 - "DictionaryBrowseStartupStage"
Cohesion: 0.15
Nodes (12): Progress, create_stderr_console(), Console, Create one Rich console bound to current stderr stream. Returns: Console…, DictionaryBrowseStartupStage, StrEnum, Browse startup progress helpers for dictionary browse workflow., Stable stage labels for dictionary browse startup progress. (+4 more)

### Community 99 - "Configuration: Command Line Tool guide"
Cohesion: 0.15
Nodes (18): wyrdcraeft settings CLI command doc, wyrdcraeft source convert CLI command doc, Configuration: Command Line Tool guide, wyrdcraeft FAQ, Standard JSON Representation for Old English Texts (schema spec), Installation guide, Quickstart guide, Using the Command Line Interface guide (+10 more)

### Community 100 - "DatabaseStartupRuntime"
Cohesion: 0.27
Nodes (19): _create_pre_alembic_forms_db(), _make_settings(), MonkeyPatch, parametrize, Path, test_child_help_skips_database_gate(), test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(), test_fresh_missing_db_bootstraps_with_alembic_path() (+11 more)

### Community 101 - ".__init__"
Cohesion: 0.29
Nodes (4): Path, Initialize a SQLAlchemy sink for emitted morphology rows. Note: Index schema…, Ensure the canonical ``forms`` table and its indexes exist., Tune SQLite for bulk morphology index writes. Side Effects: Sets WAL mode and…

### Community 102 - "test_cli_commands.py"
Cohesion: 0.08
Nodes (17): Tests for CLI commands with low coverage., Test CLI error handling., Test CLI without arguments shows help., Test invalid command shows error., Test that the OCR command group has been removed from the CLI., Test that Settings has no ocr_ fields., Test the settings command., Test the settings command with table output. (+9 more)

### Community 103 - "OESyllableBreaker"
Cohesion: 0.16
Nodes (9): Syllable model for Old English syllable breaking., A syllable is a unit of speech that consists of an onset, nucleus, and coda., Syllable, OESyllableBreaker, Split consonant cluster between syllables using a conservative max-onset…, Insert dots before known suffixes to guide syllabification., Syllabify an Old English word conservatively., Break an Old English word into syllables. (+1 more)

### Community 104 - "DictionaryBrowseApp"
Cohesion: 0.08
Nodes (20): Changed, ListItem, Selected, Submitted, DictionaryBrowseApp, Normalize search input text so dead-key combining marks become OE glyphs. Args:…, Run browse search when the user submits the search box. Args: event: Textual…, Show details for a selected search result or Wright section. Args: event:… (+12 more)

### Community 105 - "wyrdcraeft dictionary browse"
Cohesion: 0.23
Nodes (13): normalize_old_english(), BTSpellingNormalizer, DictionaryBrowseApp (Textual TUI), DictionaryBrowseQueryService, 12-tier headword/variant search ranking ladder, wyrdcraeft dictionary browse, wyrdcraeft dictionary build, parse_warnings.jsonl (+5 more)

### Community 106 - "TestCLIGlobalOptions"
Cohesion: 0.12
Nodes (9): Test text output format., Test invalid output format., Test global CLI options., Test verbose flag is properly set., Test quiet flag is properly set., Quiet mode should reset on next non-quiet CLI invocation., Test default output format is table., Test JSON output format. (+1 more)

### Community 107 - "properties"
Cohesion: 0.12
Nodes (16): type, uniqueItems, type, uniqueItems, type, uniqueItems, type, closed_class_examples (+8 more)

### Community 108 - "ADR 0009: Collapse morphology generation callback-soup into PoS generator classes"
Cohesion: 0.18
Nodes (9): ADR 0009: Collapse morphology generation callback-soup into PoS generator classes, Alternatives Considered, Consequences, Context, Decision, Status, Consequences, Considered options (+1 more)

### Community 110 - "_WeakPsinsg2DerivationContext"
Cohesion: 0.40
Nodes (4): Immutable context for weak ``PsInSg2``-derived emitter callbacks. Args:…, _WeakPsinsg2DerivationContext, Emit weak-verb forms derived from the ``PsInSg2`` principal part. Side Effects:…, Emit weak ``PsInSg2``-derived forms for one principal-part stem context. Side…

### Community 111 - "_NounAssignedIndex"
Cohesion: 0.12
Nodes (18): _assign_from_advanced_stem(), _assign_from_simple_stem(), _normalized_stem_variants(), _NounAssignedIndex, Assign paradigm using normalized stem variants against assigned nouns. Args:…, Track assigned noun paradigms with O(1) exact-stem and ordered advanced lookup.…, Initialize empty assigned-noun tracking state., Register one assigned noun and its first-seen stem paradigm mapping. Args:… (+10 more)

### Community 112 - "_label"
Cohesion: 0.22
Nodes (10): _decode_adjective(), _decode_noun_like(), _decode_verb(), _label(), _pick_inflection(), Map one morphology code fragment to a human-readable label. Args: mapping:…, Derive adjective inflection metadata from morphology class columns. Args:…, Decode noun-like case/gender/number function codes. Args: code: Morphology… (+2 more)

### Community 113 - "read_jsonl_gz"
Cohesion: 0.12
Nodes (32): morphology, morphology_full, main(), _mypy_baseline(), _runtime_baseline_ms(), _sha256_rows(), _stage_rows(), assert_snapshot_parity() (+24 more)

### Community 114 - "session.py"
Cohesion: 0.19
Nodes (13): ManualForm, Manual form model for ``manual_forms.txt`` ingest rows. Legacy string fields…, load_dictionary(), load_forms(), load_paradigms(), load_prefixes(), Load the paradigms from a file. Args: path: The path to the paradigms file.…, Load the dictionary from a file. Args: path: The path to the dictionary file.… (+5 more)

### Community 115 - "Implementation Slices"
Cohesion: 0.33
Nodes (6): Implementation Slices, Slice 1: consume visibility review, Slice 2: models and schema, Slice 3: parser and merge, Slice 4: query and CLI, Slice 5: rebuild and verify

### Community 117 - "GeneratorSession.load_all"
Cohesion: 0.17
Nodes (12): GeneratorSession (services.morphology), wyrdcraeft.models.morphology, GeneratorSession, LemmaMorphClassAssigner, MorphologyCatalogLoader, Morphology generation flow (concept), GeneratorSession.load_all(), LemmaMorphClassAssigner.assign_all() (+4 more)

### Community 118 - "wyrdcraeft 1.1.0 release (2026-03-02)"
Cohesion: 0.22
Nodes (13): GPalatalizer, MacronApplicator, wyrdcraeft.models.macron_index, wyrdcraeft 1.0.0 initial release (2026-03-01), wyrdcraeft 1.1.0 release (2026-03-02), wyrdcraeft source mark-diacritics, Diacritic restoration runtime processing flow, wyrdcraeft diacritic add (+5 more)

### Community 119 - ".load_from_tei"
Cohesion: 0.24
Nodes (6): Document, TeiReader, Extract metadata from TEI header. Args: tei_reader: The TEI reader to extract…, Parse the TEI body. Args: doc: The document to parse the body from. ns: The…, Load a TEI XML document. Args: source: The source to load the document from.…, Import TEI XML using delb and acdh-tei-pyutils. Args: tei_xml: The TEI XML to…

### Community 120 - "browse_query.py"
Cohesion: 0.05
Nodes (43): Arabic display labels for canonical sense paths., TestSenseDisplayLabels, format_sense_display_label(), Build a sort key that orders senses by hierarchical path. ``4`` sorts before…, User-facing sense label derived from ``sense_path``. Roman source labels are…, Convert canonical ``sense_path`` to Arabic display text. Top-level paths stay…, sense_path_sort_key(), _append_unique() (+35 more)

### Community 122 - "Phase 2 — Lemma Morph Class Assignment"
Cohesion: 0.20
Nodes (10): Cleanup (optional same PR or follow-up), Phase 2 — Gate A: Spec review, Phase 2 — Gate B: Code review, Phase 2 — Lemma Morph Class Assignment, Phase 2 validation, Task 1: Schema + migration, Task 2: POS normalization helper, Task 3: Paradigm exemplar registry (+2 more)

### Community 123 - "contracts.py"
Cohesion: 0.14
Nodes (14): FormEmitter, FormWriter, ParadigmAssigner, ParityFormOutput, Any, Protocol, Shared protocols for morphology refactor boundaries., Minimal writer protocol used by morphology emitters. (+6 more)

### Community 124 - "Morphology Wright catalog — Phase 1 session (2026-07-04)"
Cohesion: 0.12
Nodes (17): 1. Circular import on full morphology test collection, 2. Untracked plan directory, 3. Package data, Branch and commits, Build integration, Commits this session (Phase 1 Tasks 1–4), Goal (locked design), Key files (+9 more)

### Community 125 - ".apply"
Cohesion: 0.33
Nodes (5): TContext_contra, TWord_contra, Ordered classification rule for paradigm assignment., Return matched paradigm labels for ``word`` in ``context``. Note: Paradigm…, Rule

### Community 126 - "File map"
Cohesion: 0.22
Nodes (9): File map, Task 1: Local `.txt` loader returns `RawBlock`s, Task 2: Strip LLM from convert CLI and `DocumentIngestor`, Task 3: Delete LLM ingest types, extractors, prompts, Task 4: Delete dictionary LLM repair, Task 5: Strip Settings LLM fields and tests, Task 6: Pytest marker, live-LLM fixtures, package deps, Task 7: Napoleon baseline + leftover references (+1 more)

### Community 127 - "infer_bt_pos_from_wordclasses"
Cohesion: 0.40
Nodes (4): test_infer_bt_pos_from_wordclasses_requires_single_mapping(), infer_bt_pos_from_wordclasses(), Shared morphology wordclass to dictionary POS mapping helpers., Map distinct morphology wordclasses to one dictionary POS when unambiguous.…

### Community 128 - "Execution order"
Cohesion: 0.18
Nodes (11): Execution order, Task 10: Full validation and handoff, Task 1: Move dictionary assets into packaged resources, Task 2: Add schema support for source-block entry identity and rich senses, Task 3: Build deterministic sense-tree normalization, Task 4: Add sense prefix classifier for modifiers, grammatical context, and usage notes, Task 5: Refactor editorial merge around source blocks and canonical sense paths, Task 6: Expand warning and audit plumbing (+3 more)

### Community 129 - "pos_inference.py"
Cohesion: 0.18
Nodes (13): PosInferenceCancelCheck, PosInferenceProgress, PosInferenceWarningSink, DictionaryPosInferer, Connection, Shared dictionary POS inference from morphology forms., Attempt one inferred POS update, skipping duplicate and homograph rows. Args:…, Unwrap one SQLAlchemy connection to the underlying SQLite driver. Args:… (+5 more)

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

### Community 138 - "20260703_01_add_normalized_title_columns.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add normalized_title columns to morphology and dictionary source tables. Side…, Remove normalized_title columns and lookup indexes. Side Effects: Drops…, upgrade()

### Community 139 - "Pipeline Changes"
Cohesion: 0.40
Nodes (5): 1. Parsing and segmentation, 2. Attestation stripping, 3. Editorial merge, 4. Lowercased display spellings, Pipeline Changes

### Community 140 - "enum"
Cohesion: 0.22
Nodes (9): adjective, adverb, noun, pronoun, verb, description, enum, type (+1 more)

### Community 141 - "enum"
Cohesion: 0.22
Nodes (9): adverbial_or_prepositional_origin, irregular_or_suppletive, irregular_or_umlauted, regular, suppletive, umlauted, enum, type (+1 more)

### Community 142 - "wyrdcraeft/settings.py"
Cohesion: 0.15
Nodes (22): parametrize, Path, test_get_app_data_path_platform_defaults(), test_get_app_data_path_settings_override(), test_get_app_data_path_unsupported_platform(), test_get_canonical_db_path_creates_parent(), test_isolated_morphology_index_db_uses_canonical_filename(), test_resolve_db_path_explicit_dir_mkdirs_target() (+14 more)

### Community 143 - "20260704_01_morph_catalog_tables.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop morphology catalog reference and junction tables. Side Effects: Removes…, Create morphology catalog reference and junction tables. Side Effects: Adds…, upgrade()

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
Cohesion: 0.50
Nodes (3): parametrize, Prompt regression and schema validation tests. These tests stay runnable…, test_expected_json_is_schema_valid()

### Community 148 - "20260704_02_lemma_morph_classes.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add recognition hints to morph classes and create lemma assignment table. Side…, Drop lemma assignment table and recognition hints column. Side Effects: Removes…, upgrade()

### Community 149 - "20260707_03_bt_source_blocks_and_rich_senses.py"
Cohesion: 0.40
Nodes (4): downgrade(), Restore homograph uniqueness and remove rich sense metadata columns. Side…, Drop homograph uniqueness and add source-block sense metadata columns. Side…, upgrade()

### Community 150 - "LegacyDatabaseResetRequired"
Cohesion: 0.17
Nodes (12): Path, test_legacy_bootstrap_failure_restores_cleanly_and_raises_typed_error(), test_legacy_morphology_db_is_backed_up_then_requires_rebuild(), DatabaseMigrationError, LegacyDatabaseResetRequired, datetime, RuntimeError, Legacy database reset stop signal with rebuild guidance. Args: backup_path:… (+4 more)

### Community 151 - "source_keys"
Cohesion: 0.29
Nodes (7): pattern, source_keys, description, items, minItems, type, uniqueItems

### Community 152 - "20260706_02_forms_foreign_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add nullable foreign-key columns to ``forms``. Side Effects: Adds…, Remove nullable foreign-key columns from ``forms``. Side Effects: Drops…, upgrade()

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

### Community 157 - "StrongVerbGenerator"
Cohesion: 0.05
Nodes (41): ADR 0011: verb engines live in per-class modules; ``common.py`` is gone., test_strong_verb_generator_imports_from_strong_verb_forms(), test_verb_form_generator_imports_from_verb_forms(), test_weak_verb_generator_imports_from_weak_verb_forms(), Immutable context shared by the strong principal-part emission methods. Args:…, Immutable context shared by the strong infinitive-derived emission methods.…, _StrongInfDerivationContext, _StrongPrincipalPartContext (+33 more)

### Community 158 - "Task 1: Define Build Event Models"
Cohesion: 0.13
Nodes (14): Execution Handoff, File Map, Lexicon Build Monitor Implementation Plan, Locked Decisions, Notes for Implementer, Task 1: Define Build Event Models, Task 2: Build Shared Runtime Controller, Task 3: Expand `rebuild_lexicon(...)` Contract for Events and Cancel (+6 more)

### Community 159 - "wright_sections"
Cohesion: 0.33
Nodes (6): minimum, wright_sections, default, description, items, type

### Community 160 - "20260706_03_lexicon_shrink_search_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Restore lexicon projection tables and legacy search table names. Side Effects:…, Rename search tables and drop lexicon projection tables. Side Effects: Renames…, upgrade()

### Community 161 - "Session State: Lexicon SQLAlchemy Slice 1 Complete"
Cohesion: 0.14
Nodes (13): Alembic owns lexicon DDL, Code review notes (Slice 1, not blocking commit), Files changed in Slice 1 commit, Locked decisions (human, this session), Rebuild semantics, References, Session State: Lexicon SQLAlchemy Slice 1 Complete, Slice 1 deliverables (shipped) (+5 more)

### Community 162 - "DictionaryBuildCounters"
Cohesion: 0.15
Nodes (11): DictionaryBuildEventSink, Event, DictionaryBuildCounters, Monotonic counters accumulated while one build runs., Path, Forward pipeline morphology options to the shared build runner. Keyword Args:…, Initialize the build pipeline for one canonical database. Args: db_path: Path…, Clear stale form links and rebuild the canonical dictionary slice. Args:… (+3 more)

### Community 163 - "enum"
Cohesion: 0.40
Nodes (5): past, present, enum, type, participle

### Community 164 - "default_bt_source_path"
Cohesion: 0.09
Nodes (27): CorpusSampleResult, DictionaryCorpusSampler, main(), Path, Index source lines by lookup key while preserving source line order. Returns:…, Sample keys by deterministic every-Nth stratification. Args: ordered_keys: Keys…, Result of one corpus-sample build run. Attributes: keys: Selected lookup keys…, Collect all editorial siblings for sampled keys in corpus order. Args:… (+19 more)

### Community 165 - "20260706_04_drop_forms_legacy_strings.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop legacy denormalized string columns from ``forms``. Side Effects: Removes…, Restore legacy denormalized string columns on ``forms``. Side Effects: Re-adds…, upgrade()

### Community 166 - "wyrdcraeft Context"
Cohesion: 0.15
Nodes (13): ADRs, Boundary, Canonical Terms, Capability Map, Context Docs, Current Migration Progress, Dictionary browse, Dictionary indexing (+5 more)

### Community 167 - "20260630_01_initial_canonical_schema.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop the initial canonical schema. Side Effects: Removes the initial product…, Create the canonical morphology, dictionary, and lexicon tables. Side Effects:…, upgrade()

### Community 168 - "test_schema.py"
Cohesion: 0.22
Nodes (18): _forms_column_names(), _fresh_canonical_db(), _index_names(), Connection, parametrize, Path, Tests for lexicon read-model schema helpers., Return the seeded ``unknown`` part-of-speech row id. (+10 more)

### Community 169 - "FormSink"
Cohesion: 0.40
Nodes (4): FormSink, Protocol, Sink contract for finalized emitted form rows., Consume finalized form rows in emitted order. Note: Emitted row semantics…

### Community 170 - "20260707_01_drop_search_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop legacy lexicon search-index tables from the canonical schema. Side…, Recreate empty legacy lexicon search-index tables. Side Effects: Restores empty…, upgrade()

### Community 171 - "run_dictionary_browse"
Cohesion: 0.09
Nodes (18): ComposeResult, Pressed, Static, test_shell_run_entrypoint_uses_textual_app(), _format_browse_connect_message(), Path, Build the initial browse details placeholder. Args: db_path: Path to the…, Launch the dictionary browse Textual shell for one canonical database. Args:… (+10 more)

### Community 172 - "build_session"
Cohesion: 0.18
Nodes (14): FixtureRequest, build_session(), _command_invokes_perl(), fail_if_perl_subprocess_invoked(), full_session(), Any, fixture, MonkeyPatch (+6 more)

### Community 173 - "test_lemma_morph_assignment.py"
Cohesion: 0.24
Nodes (16): assigner(), _assignment(), catalog_db(), _class_key(), _make_verb_paradigm(), _make_word(), fixture, Path (+8 more)

### Community 174 - "File Structure"
Cohesion: 0.15
Nodes (12): File Structure, GeneratorSession → WordPool + GenerationRunState Split Implementation Plan, Global Constraints, Task 1: Introduce `WordPool` + `GenerationRunState`, compose `GeneratorSession` from them, Task 2: Migrate the assigners (`noun.py`, `verb.py`, `adj.py`) onto `WordPool`, Task 3: Migrate the shared sink + row-emission leaf layer onto `GenerationRunState`/`WordPool`, Task 4: Migrate `generation/adv_forms.py` (smallest generator — proves the pattern end to end), Task 5: Migrate `generation/num_forms.py` (+4 more)

### Community 175 - "20260707_02_bt_senses_entry_order_index.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add index supporting ordered sense lookup by dictionary entry. Side Effects:…, Remove ordered lookup index for dictionary sense reads. Side Effects: Drops the…, upgrade()

### Community 176 - ".run"
Cohesion: 0.17
Nodes (10): DictionaryBuildStatus, DictionaryBuildReport, Connection, Summary of one unified dictionary build run., Run the unified dictionary build pipeline against one source file. Keyword…, Relink every stored form row against the rebuilt dictionary tables. Args:…, Return the current ``forms`` row count. Args: connection: Open SQLAlchemy…, Return the number of forms carrying a linked dictionary entry. Args:… (+2 more)

### Community 177 - "print_error"
Cohesion: 0.07
Nodes (25): Tests for CLI utilities., Test success panel has correct styling., Test console objects., Test that console objects are properly initialized., Test progress creation., Test progress creation returns a Progress object., Test progress has spinner column., Test progress has text column. (+17 more)

### Community 178 - "lexicon/conftest.py"
Cohesion: 0.21
Nodes (14): _inflection_code_id(), lexicon_db_connection(), lexicon_db_path(), _noun_pos_id(), Connection, fixture, Path, Shared fixtures for lexicon schema and service tests. (+6 more)

### Community 179 - ".generate_all_forms"
Cohesion: 0.14
Nodes (7): Emit all generated adverb rows for the bound session. Side Effects: Writes rows…, Emit all generated numeral rows for the bound session. Side Effects: Writes…, Emit all generated noun rows for the bound session. Side Effects: Writes rows…, Emit the default full morphology generation flow in stable order. Side Effects:…, Emit curated manual rows before paradigm-driven generation. Side Effects:…, Emit all generated verb rows for the bound session. Side Effects: Writes rows…, Emit all generated adjective rows for the bound session. Side Effects: Writes…

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

### Community 187 - "build_pipeline.py"
Cohesion: 0.20
Nodes (14): DictionaryBuildEvent, DictionaryBuildFinished, DictionaryBuildLog, DictionaryBuildSnapshot, DictionaryBuildStageProgress, DictionaryBuildStageStarted, Typed stage and event models for unified dictionary builds., Successful terminal event for one completed dictionary build. (+6 more)

### Community 188 - "BT Structural Visibility Review"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT Structural Visibility Review, Candidate Types To Include, Deliverables, Dependencies, Downstream Use, Locked Decisions, Non-Goals (+4 more)

### Community 189 - "wyrdcraeft"
Cohesion: 0.15
Nodes (12): All other code, Bosworth-Toller Old English Dictionary, Canonical database, Contributing, Contributing, Licensing and Provenance, Documentation, Features, Installation (+4 more)

### Community 190 - "set_verb_paradigm"
Cohesion: 0.21
Nodes (12): _make_verb_paradigm(), test_set_verb_paradigm_fallback_for_weak_verbs(), test_set_verb_paradigm_strong_heuristic_assignment(), _assign_verb_by_advanced_stem(), _assign_verb_by_diacritics(), _assign_verb_by_stem(), Step 6.5: Assign verbs by stem comparison disregarding diacritics. Args: words:…, Set the verb paradigm. Note: This function matches Perl's set_verb_paradigm… (+4 more)

### Community 191 - "Phase D — Drop Legacy Form String Columns"
Cohesion: 0.15
Nodes (12): Phase D — Commit, Phase D — Drop Legacy Form String Columns, Phase D — Gate A: Spec review checklist, Phase D — Gate B: Code review checklist, Phase D validation, Post-phase checklist (coordinator), Task 1: Alembic migration `20260706_04`, Task 2: Sink + query path cleanup (+4 more)

### Community 192 - "runtime.py"
Cohesion: 0.04
Nodes (64): _make_word(), query_service(), Tests for read-only Wright catalog lemma class lookup., test_format_morph_class_display_label_falls_back_to_canonical_name(), test_format_morph_class_display_label_prefers_compact_modern_label(), test_lookup_missing_lemma_returns_none(), test_lookup_normalizes_title_before_query(), test_lookup_stan_noun_returns_masculine_a_stem() (+56 more)

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

### Community 211 - "source_db.py"
Cohesion: 0.33
Nodes (8): make_lexicon_source_db(), Path, Helpers for building morphology SQLite databases used in lexicon tests., Build a morphology database seeded with ``forms`` and ``bt_*`` tables. Args:…, Write minimal ``forms`` rows into a morphology SQLite database. Args: db_path:…, Attach minimal Bosworth-Toller ``bt_*`` tables to a morphology database. Args:…, seed_bt_tables(), seed_forms()

### Community 213 - "Dictionary CLI index gate and morph paths Implementation Plan"
Cohesion: 0.17
Nodes (10): Considered Options, Index population gate is a query-module check, not startup runtime, Dictionary CLI index gate and morph paths Implementation Plan, File map, Global Constraints, Self-review, Spec coverage, Task 1: Index population gate (+2 more)

### Community 215 - "BT Usage-vs-Sense Cleanup Handoff"
Cohesion: 0.17
Nodes (9): BT entry identity follows source blocks, BT Usage-vs-Sense Cleanup Handoff, Current understanding, Key files, Proposed implementation, Suggested review artifact shape, Suggested skills, Useful corpus findings already gathered (+1 more)

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

### Community 220 - ".palatalize"
Cohesion: 0.17
Nodes (7): _possible_pre_iumlaut_sources(), Palatalize ``g`` in a lexical token. Args: word: Token to palatalize. Returns:…, Return possible pre-i-mutation (reconstructed) sources for an OE vowel. Used to…, Test if ``text[index:]`` starts with a front-vowel context. Args: text:…, Return whether the character before position i is i/ī or i/ī + n. Used for Rule…, Return True if the vowel unambiguously derives only from back vowels. Used to…, Palatalize ``c`` in a lexical token per rules A-D and i-mutation caveat. Rule…

### Community 221 - "Phase B — Forms Foreign Keys (Legacy Strings Remain)"
Cohesion: 0.18
Nodes (11): Phase B — Commit, Phase B — Forms Foreign Keys (Legacy Strings Remain), Phase B — Gate A: Spec review checklist, Phase B — Gate B: Code review checklist, Phase B validation, Task 1: Alembic migration `20260706_02`, Task 2: Form FK resolver service, Task 3: Sink propagation (+3 more)

### Community 223 - "Phase 2 — Wright § Text Ingest Report"
Cohesion: 0.14
Nodes (13): Wright § markdown text ingest into wright_sections.section_text, Files changed, Implementation notes, Manual spot-check, Phase 2 — Wright § Text Ingest Report, Self-review, Summary, Task 2.1 — Markdown § parser (+5 more)

### Community 224 - "OCR pipeline moves to bochord"
Cohesion: 0.50
Nodes (4): Consequence, Not removed, OCR pipeline moves to bochord, Removed from wyrdcraeft

### Community 226 - "LLM and unstructured leave `source convert`"
Cohesion: 0.18
Nodes (8): LLM and unstructured leave `source convert`, Not this decision, Removed, Sibling name, `.txt` load (not a heuristic rewrite), Global Constraints, LLM and unstructured leave `source convert` Implementation Plan, Self-review (spec coverage)

### Community 227 - "AGENTS.md"
Cohesion: 0.22
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

### Community 235 - "wright-morphology-fixture.schema.json"
Cohesion: 0.18
Nodes (10): morph_classes, schema_version, sources, additionalProperties, description, $id, required, $schema (+2 more)

### Community 236 - "split_prose_and_verse_runs"
Cohesion: 0.33
Nodes (8): _is_heading_line(), _is_number_line(), _is_verse_line(), Test if a line looks like a heading., Heuristic: short, line-broken, non-empty lines typical of OE verse editions., Test if a line is just a numbering marker (e.g. "[12]" or "5")., Split text into ordered prose / verse chunks. - Preserves original text exactly…, split_prose_and_verse_runs()

### Community 237 - "PHONOLOGY"
Cohesion: 0.04
Nodes (47): The Seafarer (Old English poem, test fixture), Old English Bosworth-Toller Dictionary Text, 1. UMLAUT, 2. Breaking, 3. Influence of Nasals, 4. Influence of Initial Palatal Consonants, 5. Influence of w, a (+39 more)

### Community 238 - "CONTEXT.md"
Cohesion: 0.21
Nodes (4): Lexicon data lives in morphology.sqlite3, BT OCR parsing starts with lossless source-grounded AST, BT source acquisition uses a multi-witness download set, BT JP2 witness preparation is library-first

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

### Community 247 - "test_assigner_branches.py"
Cohesion: 0.18
Nodes (21): _make_word(), test_set_adj_paradigm_stem_propagation(), test_set_adj_paradigm_wright_rule_425(), test_set_noun_paradigm_advanced_stem_propagation(), test_set_noun_paradigm_final_fallback_neuter_long_stem(), test_set_noun_paradigm_final_fallback_neuter_short_stem(), test_set_noun_paradigm_heuristic_incel_suffix(), test_set_noun_paradigm_heuristic_nd_stem_masculine() (+13 more)

### Community 248 - "Orchestrator Checkpoint"
Cohesion: 0.29
Nodes (6): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase status, Resume here

### Community 249 - "DictionaryBuildStage"
Cohesion: 0.21
Nodes (9): DictionaryBuildStage, StrEnum, Stable stage labels emitted during one unified dictionary build., DictionaryBuildProgress, Protocol, Progress callback surface used during unified dictionary builds., Mark one build stage active. Args: stage: Stage being entered. Keyword Args:…, Advance one build stage. Args: stage: Stage being advanced. Keyword Args:… (+1 more)

### Community 250 - "source_key"
Cohesion: 0.25
Nodes (8): oldenglish_info, stella, wright_1914, source_key, description, examples, pattern, type

### Community 251 - "test_generation_package_imports.py"
Cohesion: 0.25
Nodes (7): Regression test for the generation-package import-cycle fix.…, The package must not carry a facade re-export that recreates the cycle., The only import path any real caller uses must keep working., The facade's verb-generation method is the production entrypoint., test_facade_still_importable_directly(), test_facade_verb_method_still_importable(), test_generation_package_does_not_reexport_facade()

### Community 252 - "TestCLIVersion"
Cohesion: 0.25
Nodes (5): Test the version command., Test the version command displays version information., Test the version command with verbose flag., Test the version command with quiet flag., TestCLIVersion

### Community 253 - "Domain Docs"
Cohesion: 0.33
Nodes (5): Before exploring, read these, Domain Docs, File structure, Flag ADR conflicts, Use the glossary's vocabulary

### Community 254 - "normalized_title + lexicon browse — checkpoint 2026-07-03T12:15"
Cohesion: 0.33
Nodes (5): Done this session, Gates, normalized_title + lexicon browse — checkpoint 2026-07-03T12:15, Ready to commit, User requirement (confirmed)

### Community 255 - "Mission: Machine Assistance For Old English Work"
Cohesion: 0.25
Nodes (6): New applied learning goal: difficult Old English OCR to structured data, Constraints, Mission: Machine Assistance For Old English Work, Out of scope, Success looks like, Why

### Community 256 - "Mission: Historical Linguistics for Old English Study"
Cohesion: 0.33
Nodes (5): Constraints, Mission: Historical Linguistics for Old English Study, Out of scope, Success looks like, Why

### Community 257 - ".__init__"
Cohesion: 0.25
Nodes (6): _CatalogClass, Engine, Session, Build catalog indexes used by the assignment pipeline. Note: Linguistic…, Load assignable morph classes and Wright section links from the DB. Args:…, In-memory morph-class row used during assignment.

### Community 259 - "cli.py"
Cohesion: 0.12
Nodes (17): _configure_logging(), _prompt_backup_cleanup(), command, Context, Run the canonical DB startup gate once for DB-using command trees. Args: ctx:…, Print the some version info of this package,, Click group that preserves the raw argv for help-aware gate decisions. Side…, Persist the raw argv before delegating to Click's normal parser. Args: ctx:… (+9 more)

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

### Community 266 - "BT Dictionary Structuring Workflow runbook"
Cohesion: 0.28
Nodes (8): data/oe_bt.txt Bosworth-Toller OCR source file, BT Dictionary Structuring Workflow runbook, Generating the canonical macron list runbook, Gaps, Knowledge, Machine Assistance For Old English Work Resources, Wisdom (Communities), Bosworth-Toller dictionary corpus sample test fixture

### Community 267 - "Historical Linguistics for Old English Study Resources"
Cohesion: 0.40
Nodes (4): Gaps, Historical Linguistics for Old English Study Resources, Knowledge, Wisdom (Communities)

### Community 268 - "language"
Cohesion: 0.33
Nodes (6): Old English, default, description, examples, type, language

### Community 269 - "TestConsoleQuietMode"
Cohesion: 0.33
Nodes (4): Test console quiet mode functionality., Test that console can be set to quiet mode., Test that stderr console can be set to quiet mode., TestConsoleQuietMode

### Community 270 - "Old English c/g Palatalization Rule System"
Cohesion: 0.83
Nodes (4): Old English c/g Palatalization Rule System, c-Palatalization Force-Non-Palatalize Exception List, c-Palatalization Force-Palatalize Exception List, g Frontal-Vowel Palatalization Exception List

### Community 271 - "WrightAuditResult"
Cohesion: 0.33
Nodes (4): Structured Phase 4 audit output for human and JSON reporting. Note: The audit…, Return the total number of scanned source rows. Returns: Sum of all per-source…, Convert the full audit result into a JSON-friendly payload. Returns: Nested…, WrightAuditResult

### Community 272 - "source_set"
Cohesion: 0.40
Nodes (5): wright-modern-morphology, source_set, description, examples, type

### Community 273 - "morphology_row_matches_pos"
Cohesion: 0.40
Nodes (5): test_morphology_row_matches_entry_pos_filters_participle_for_noun(), morphology_row_matches_pos(), Return morphology wordclass labels that match one dictionary POS label. Args:…, Return whether one morphology row belongs to the dictionary entry POS. Keyword…, wordclasses_for_entry_pos()

### Community 274 - "features"
Cohesion: 0.40
Nodes (5): features, additionalProperties, default, description, type

### Community 275 - ".write_json"
Cohesion: 0.40
Nodes (3): Path, Write the report as formatted JSON to disk. Args: report_path: Destination JSON…, Serialize the report to a JSON-friendly mapping. Returns: Dictionary suitable…

### Community 278 - "morphClass"
Cohesion: 0.50
Nodes (4): morphClass, additionalProperties, allOf, type

### Community 297 - "Verb generators leave `common.py`"
Cohesion: 0.14
Nodes (12): Consequences, Considered options, Engines, not OE conjugation classes, Module map, Verb generators leave `common.py`, File map, Global Constraints, Out of scope (+4 more)

### Community 298 - "lexicon_source_db"
Cohesion: 0.40
Nodes (5): empty_browse_db(), lexicon_source_db(), fixture, Dictionary-backed canonical DB fixture for browse TUI tests., Canonical schema with no dictionary rows for browse readiness tests.

### Community 299 - "filter_display_variants"
Cohesion: 0.40
Nodes (5): test_filter_display_variants_drops_genitive_endings(), filter_display_variants(), is_genitive_variant_token(), Return whether one variant token is a weak-noun genitive ending. Args: token:…, Drop genitive-ending tokens from dictionary variant spellings. Args: variants:…

### Community 300 - "DictionaryBrowseDataError"
Cohesion: 0.40
Nodes (5): DictionaryBrowseDataError, _ensure_browse_ready(), RuntimeError, Validate that browse tables exist and contain searchable rows. Args:…, Raised when dictionary browse data is unavailable for the TUI shell.

### Community 302 - "progress.md"
Cohesion: 0.50
Nodes (3): Phase A SDD Progress, Prior ledger (Phase A — do not treat as ADR 0010), SDD Progress — ADR 0010 LLM/unstructured leave source convert

### Community 309 - "sound_dispatch_flow.py"
Cohesion: 0.20
Nodes (14): SoundChangeSequenceEmitter, SoundManualContextEmitter, SoundSourceContextEmitter, Immutable context for sound-change callback dispatch. Args: formhash: Shared…, _SoundChangeDispatchContext, emit_manual_sound_changed_context(), emit_sound_changed_form_for_context(), emit_source_form_with_sound_context() (+6 more)

### Community 311 - "_collect_widget_ids"
Cohesion: 0.67
Nodes (3): _collect_widget_ids(), Collect all widget ids reachable from one widget tree root. Args: widget: Root…, Widget

### Community 312 - "_insert_inflection_code"
Cohesion: 0.67
Nodes (3): _insert_inflection_code(), Connection, Insert one ad-hoc ``inflection_codes`` row and return its id.

### Community 313 - "_table_text"
Cohesion: 0.67
Nodes (3): DataTable, Flatten a DataTable into plain text for assertions. Args: table: DataTable…, _table_text()

## Ambiguous Edges - Review These
- `task-phase1-morph-class-browse-report.md` → `task-phase2-wright-text-ingest-report.md`  [AMBIGUOUS]
  doc/sessions/task-phase2-wright-text-ingest-report.md · relation: references
- `The Seafarer (Old English poem, test fixture)` → `Old English Bosworth-Toller Dictionary Text`  [AMBIGUOUS]
  tests/fixtures/seafarer.txt · relation: conceptually_related_to

## Knowledge Gaps
- **921 isolated node(s):** `release.sh script`, `wyrdcraeft`, `IPA_AUDIO`, `$schema`, `$id` (+916 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2724 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `task-phase1-morph-class-browse-report.md` and `task-phase2-wright-text-ingest-report.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `The Seafarer (Old English poem, test fixture)` and `Old English Bosworth-Toller Dictionary Text`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `GeneratorSession` connect `GeneratorSession` to `MorphologyGenerateProgressCoordinator`, `OENormalizer`, `test_generation_branches.py`, `build_session`, `read_jsonl_gz`, `WeakVerbGenerator`, `source_db.py`, `reference_snapshots.py`, `build_runner.py`, `session.py`, `test_assigner_branches.py`, `Word`, `models/morphology.py`, `morphology/test_query_service.py`, `set_verb_paradigm`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Word` connect `Word` to `MorphologyGenerateProgressCoordinator`, `OENormalizer`, `test_generation_branches.py`, `_WeakInfDerivationContext`, `WeakVerbGenerator`, `GenerationRunState`, `models/morphology.py`, `StrongVerbGenerator`, `models/__init__.py`, `NounFormGenerator`, `MorphologyCatalogLoader`, `noun.py`, `test_lemma_morph_assignment.py`, `set_verb_paradigm`, `runtime.py`, `WrightAuditService`, `_WeakPainsg1DerivationContext`, `_NounAssignedIndex`, `session.py`, `test_assigner_branches.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `OENormalizer` connect `OENormalizer` to `runtime.py`, `MorphologyCatalogLoader`, `models/dictionary.py`, `WrightAuditService`, `ParadigmClassMapper`, `noun.py`, `GeneratorSession`, `MorphologyDictionaryCleaner`, `WeakVerbGenerator`, `markup.py`, `GenerationRunState`, `session.py`, `StrongVerbGenerator`, `test_assigner_branches.py`, `Word`, `models/morphology.py`, `morphology/test_query_service.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `Word` (e.g. with `test_generate_verb_parts_routes_direct_derivation_stack()` and `test_generate_verb_parts_routes_direct_weak_painsg1_stack()`) actually correct?**
  _`Word` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `GeneratorSession` (e.g. with `_run_prerequisite_stages()` and `full_session()`) actually correct?**
  _`GeneratorSession` has 25 INFERRED edges - model-reasoned connections that need verification._