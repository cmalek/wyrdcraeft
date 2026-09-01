# Graph Report - wyrdcraeft  (2026-08-31)

## Corpus Check
- 345 files · ~5,287,104 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5514 nodes · 11045 edges · 286 communities (239 shown, 38 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 702 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8a49d058`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BTLineParser
- models/dictionary.py
- build_pipeline.py
- run_dictionary_browse
- query
- ParadigmClassMapper
- BTEditorialMerger
- MorphologyGenerateProgressCoordinator
- form_decode.py
- OENormalizer
- DictionaryBuildPipeline
- Word
- browse_tui.py
- ._rebuild_dictionary
- test_build_pipeline.py
- _RecordingSink
- BTAttestationStripper
- Settings
- WeakVerbGenerator
- reference_snapshots.py
- test_browse_tui.py
- DictionaryBrowseQueryService
- ensure_parts_of_speech
- GenerationRunState
- test_markup.py
- tests/conftest.py
- diacritic_disambiguate.py
- cli/dictionary.py
- cli.py
- morphology/test_query_service.py
- File Structure
- models/__init__.py
- RawBlock
- NounFormGenerator
- MorphologyCatalogLoader
- build_session
- sound_changes.py
- etymology_display.py
- noun.py
- SenseMetadataClassifier
- format_wright_audit_text
- .ensure_ready
- ingest/pipeline.py
- OldEnglishText
- test_morph_class_browse.py
- MorphologyGenerationFacade
- NormalizedTitleJoinIndex
- wright_audit.py
- wright-morphology-fixture.schema.json
- test_cli_diacritic_disambiguate.py
- wyrdcraeft/settings.py
- diacritics.py
- test_form_decode.py
- print_info
- Session: Morphology Wright Catalog — Phase 2 complete
- test_index_pipeline.py
- properties
- properties
- create_engine
- form_fk_resolver.py
- cli
- test_loaders.py
- Path
- check_napoleon_gate.py
- Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅
- write_backup_state
- test_attach_morphology_db.py
- .load_from_tei
- LegacyDatabaseResetRequired
- browse_query.py
- OEFilter
- markup.py
- setter
- split_prose_and_verse_runs
- test_corpus_sample.py
- catalog_db
- enum
- MorphologyDictionaryCleaner
- test_form_fk_resolver.py
- test_dictionary_build_relinks_forms_after_dictionary_rebuild
- print_error
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
- lexicon_source_db
- sqlalchemy.py
- .parse
- test_cli_commands.py
- required
- features
- FormRow
- test_lemma_morph_assignment.py
- Configuration: Command Line Tool guide
- DatabaseStartupRuntime
- ensure_inflection_codes
- TestCLIVersion
- OESyllableBreaker
- DictionaryBrowseApp
- wyrdcraeft dictionary browse
- TestCLIGlobalOptions
- properties
- ADR 0009: Collapse morphology generation callback-soup into PoS generator classes
- Lexicon shrink: drop lexicon_entries/lexicon_forms, keep search_keys
- _format_entry_text
- DictionaryBuildStage
- _collect_widget_ids
- _insert_inflection_code
- morphology_row_matches_pos
- Implementation Slices
- fixture_prose.txt (Mark gospel OE prose fixture)
- GeneratorSession.load_all
- wyrdcraeft 1.1.0 release (2026-03-02)
- _table_text
- .__init__
- Batched SQLite sink (25K rows) + bulk PRAGMAs fix for morphology build perf
- Phase 2 — Lemma Morph Class Assignment
- DictionaryBrowseStartupStage
- Morphology Wright catalog — Phase 1 session (2026-07-04)
- .apply
- File map
- DictionaryPosInferer
- Execution order
- TestCLISettings
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
- test_paths.py
- 20260704_01_morph_catalog_tables.py
- Dictionary build/browse flow (concept)
- Wyrdcraeft Canonical DB Migration Implementation Plan
- Architecture review — 2026-08-01
- test_prompt_regression.py
- 20260704_02_lemma_morph_classes.py
- .run
- BackupStateStore
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
- .__init__
- enum
- 20260706_04_drop_forms_legacy_strings.py
- wyrdcraeft Context
- 20260630_01_initial_canonical_schema.py
- test_schema.py
- generation/query.py
- 20260707_01_drop_search_keys.py
- 20260707_03_bt_source_blocks_and_rich_senses.py
- _adjective_row_sort_key
- File Structure
- 20260707_02_bt_senses_entry_order_index.py
- dictionary/pipeline.py
- runtime.py
- Phase A — Reference Tables and Dictionary POS FKs
- MorphologyCatalogQueryService
- Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns
- create_dict31.pl (legacy Perl morphology generator)
- BTQueryService
- Python coding standards
- WrightAuditResult
- BT Structural Visibility Review
- wyrdcraeft
- ._no_mixed_prose_and_verse
- Phase D — Drop Legacy Form String Columns
- LemmaMorphClassAssigner
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
- BT Usage-vs-Sense Cleanup Handoff
- Global Constraints
- Lexicon Browser BT V2 Adaptation Skeleton
- Orchestration: Wyrdcraeft Canonical DB Migration
- Morph Class Browse And Audit Design
- Phase B — Forms Foreign Keys (Legacy Strings Remain)
- 0002-normalized-canonical-schema.md
- Phase 2 — Wright § Text Ingest Report
- OCR pipeline moves to bochord
- Two-gate subagent workflow: Gate A spec review, Gate B code review
- File map
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
- session.py
- Orchestrator Checkpoint
- test_cli_convert.py
- .__init__
- BTSenseSegmenter
- Domain Docs
- normalized_title + lexicon browse — checkpoint 2026-07-03T12:15
- Mission: Machine Assistance For Old English Work
- Mission: Historical Linguistics for Old English Study
- Lemma-level morph class assignment (normalized_title, pos) -> morph_classes
- Issue tracker: Trello
- Subagent task breakdown
- Subagent task breakdown
- Subagent task breakdown
- normalized_title — checkpoint 2026-07-03T12:10
- BT Dictionary Structuring Workflow runbook
- Historical Linguistics for Old English Study Resources
- Old English c/g Palatalization Rule System
- filter_display_variants
- infer_bt_pos_from_wordclasses
- release.sh
- 0002-canonical-morphology-db-uses-startup-alembic-migrations.md
- triage-labels.md
- scripts/__init__.py
- quality/__init__.py
- GeneratorSession
- machine-assistance/NOTES.md
- 0001-starting-point.md
- oe-grammar/NOTES.md
- teaching/README.md
- ipa-play.js
- THIRD_PARTY_NOTICES.md
- wyrdcraeft
- .get_details
- DictionaryBrowseDataError
- .write_json
- WordPool
- progress.md
- test_generation_package_imports.py
- task-8-report.md
- TestCLIErrorHandling
- TestConsoleQuietMode
- _mock_bt_lookup

## God Nodes (most connected - your core abstractions)
1. `Word` - 149 edges
2. `GeneratorSession` - 126 edges
3. `cli()` - 108 edges
4. `BTSenseSegmenter` - 80 edges
5. `WeakVerbGenerator` - 71 edges
6. `BTLineParser` - 64 edges
7. `OENormalizer` - 63 edges
8. `create_engine()` - 58 edges
9. `MorphologyCatalogLoader` - 55 edges
10. `upgrade_canonical_db()` - 53 edges

## Surprising Connections (you probably didn't know these)
- `Solomon and Saturn dialogue test fixture` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_dialogue.txt → doc/source/overview/format.rst
- `Beowulf opening lines test fixture (poetry)` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_poetry.txt → doc/source/overview/format.rst
- `test_convert_rejects_use_llm_flag()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_convert.py → wyrdcraeft/cli/cli.py
- `test_convert_rejects_http_source()` --indirect_call--> `cli()`  [INFERRED]
  tests/test_cli_convert.py → wyrdcraeft/cli/cli.py
- `main()` --uses--> `MacronApplicator`  [INFERRED]
  bin/build_macron_index.py → wyrdcraeft/services/markup.py

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

## Communities (286 total, 38 thin omitted)

### Community 0 - "BTLineParser"
Cohesion: 0.04
Nodes (64): _entry_to_dict(), main(), _parse_and_segment(), Parse and segment one raw BT line., Convert a BTConsolidatedEntry to a serialisable dict., _entry_to_comparable(), _load_golden(), merger() (+56 more)

### Community 1 - "models/dictionary.py"
Cohesion: 0.03
Nodes (82): extractor(), fixture, parametrize, Tests for BTPosGenderExtractor using real oe_bt.txt prefix fragments., Shared extractor instance., Real BT prefix fragments resolve to expected POS and genders., Verb paradigm detection wins when both verb endings and adj appear., Abbad line with m: and m. returns masculine noun once. (+74 more)

### Community 2 - "build_pipeline.py"
Cohesion: 0.20
Nodes (14): DictionaryBuildEvent, DictionaryBuildFinished, DictionaryBuildLog, DictionaryBuildSnapshot, DictionaryBuildStageProgress, DictionaryBuildStageStarted, Typed stage and event models for unified dictionary builds., Successful terminal event for one completed dictionary build. (+6 more)

### Community 3 - "run_dictionary_browse"
Cohesion: 0.09
Nodes (18): ComposeResult, Pressed, Static, test_shell_run_entrypoint_uses_textual_app(), _format_browse_connect_message(), Path, Build the initial browse details placeholder. Args: db_path: Path to the…, Launch the dictionary browse Textual shell for one canonical database. Args:… (+10 more)

### Community 4 - "query"
Cohesion: 0.20
Nodes (19): audit_wright(), browse(), build(), clean_headwords(), ingest_wright_text(), lookup(), argument, command (+11 more)

### Community 5 - "ParadigmClassMapper"
Cohesion: 0.08
Nodes (29): mapper(), fixture, Tests for Wright catalog paradigm exemplar mapping., test_adj_paradigm_blind_maps_to_strong_a_o_stem(), test_noun_paradigm_guma_maps_to_weak_n_stem(), test_noun_paradigm_stan_maps_to_masculine_a_stem(), test_past_participle_title_maps_to_past_participle_class(), test_present_participle_title_maps_to_present_participle_class() (+21 more)

### Community 6 - "BTEditorialMerger"
Cohesion: 0.04
Nodes (57): Unit tests for BTTargetResolver., TestBTTargetResolver, test_normalize_morphology_title_preserves_macrons_and_dots(), BTEditorialMerger, BTEditRecord, _edit_note_detail(), _edit_note_reason(), _plain() (+49 more)

### Community 7 - "MorphologyGenerateProgressCoordinator"
Cohesion: 0.03
Nodes (97): test_build_profiler_disabled_emits_nothing(), test_build_profiler_emits_stage_and_sqlite_sections(), test_progress_coordinator_omits_empty_wright_and_throttles_lemma(), test_progress_coordinator_stage_totals(), MorphologyBuildProfiler, TextIO, Wall-clock profiling helpers for morphology build runs., Finish wall-clock timing for one generation stage. Args: stage: Stage being… (+89 more)

### Community 8 - "form_decode.py"
Cohesion: 0.09
Nodes (39): _append_surface(), _build_adjective_degree_section(), _build_adverb_sidebar(), _build_noun_sidebar(), _build_pronoun_sidebar(), _build_verb_sidebar(), _collect_noun_sidebar_cells(), _decode_adjective() (+31 more)

### Community 9 - "OENormalizer"
Cohesion: 0.10
Nodes (29): Match, parametrize, Tests for BT display spelling normalization., Normalize representative real BT headword spellings from ``oe_bt.txt``., Normalizing an already-normalized spelling is a no-op., test_bt_spelling_normalizer_matches_oe_normalizer(), test_normalize_is_idempotent(), test_normalize_real_bt_diphthong_cases() (+21 more)

### Community 10 - "DictionaryBuildPipeline"
Cohesion: 0.16
Nodes (14): AnyDictionaryBuildEvent, DictionaryBuildLogLevel, DictionaryBuildPipeline, Orchestrate canonical dictionary rebuild, form relink, and follow-on refreshes.…, Infer missing dictionary POS values from stored morphology forms. Args:…, Return the number of dictionary rows currently carrying unknown POS. Args:…, Mark one stage active across progress and typed event surfaces. Args: stage:…, Advance optional build progress for one stage update. Args: stage: Stage being… (+6 more)

### Community 11 - "Word"
Cohesion: 0.05
Nodes (82): _base_formhash(), _make_part(), _make_variant(), _make_verb_paradigm(), _make_word(), MonkeyPatch, test_add_participle_to_adjectives_helper_appends_past_participle(), test_add_participle_to_adjectives_helper_appends_present_participle() (+74 more)

### Community 12 - "browse_tui.py"
Cohesion: 0.06
Nodes (46): _group_morphology_rows(), MorphologyGroup, MorphologyRow, Sidebar grouping of morphology rows by wordclass and function. Attributes:…, Group raw morphology rows by ``wordclass`` and ``function``. Args: rows:…, One raw projected morphology row for sidebar rendering. Note: ``wordclass`` and…, _dedupe_morphology_rows(), _EntryDetailsLike (+38 more)

### Community 13 - "._rebuild_dictionary"
Cohesion: 0.15
Nodes (11): DictionaryBuildEventSink, Event, DictionaryBuildCounters, Monotonic counters accumulated while one build runs., Path, Forward pipeline morphology options to the shared build runner. Keyword Args:…, Initialize the build pipeline for one canonical database. Args: db_path: Path…, Clear stale form links and rebuild the canonical dictionary slice. Args:… (+3 more)

### Community 14 - "test_build_pipeline.py"
Cohesion: 0.18
Nodes (23): build_pipeline_db(), _fetch_entry_id(), _fetch_entry_pos(), _fetch_form_entry_id(), _insert_form(), _pos_id(), Connection, fixture (+15 more)

### Community 15 - "_RecordingSink"
Cohesion: 0.23
Nodes (16): Capture emitted ``form_data`` payloads without TSV geminate expansion., Record one emitted row payload., _RecordingSink, _strong_generator(), _strong_inf_context(), _strong_principal_context(), test_dispatch_strong_derived_from_principal_part_papt_only(), test_dispatch_strong_derived_from_principal_part_routes_painpl() (+8 more)

### Community 16 - "BTAttestationStripper"
Cohesion: 0.04
Nodes (50): fixture, parametrize, Tests for Phase 03 BTAttestationStripper., ``_is_citation_span`` returns True for grammar/editorial markers and citations., ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes., ``_strip_editorial_directive`` removes leading supplement editorial verbs., Unit tests for BTAttestationStripper.strip., ``:--`` is the canonical attestation separator. (+42 more)

### Community 17 - "Settings"
Cohesion: 0.06
Nodes (30): BaseSettings, Exception, PydanticBaseSettingsSource, patch, Unit tests for configuration settings. Tests the new OpenAI and summary…, Test that settings fields have proper descriptions., Test that model_config is properly configured., Test output format validation. (+22 more)

### Community 18 - "WeakVerbGenerator"
Cohesion: 0.04
Nodes (61): Replace the three weak derived-branch entry points with recorders., _record_weak_branches(), test_dispatch_weak_derived_forms_selects_inf_branch(), test_dispatch_weak_derived_forms_selects_painsg1_branch(), test_dispatch_weak_derived_forms_selects_psinsg2_branch(), test_dispatch_weak_derived_forms_skips_item_shape_mode(), test_dispatch_weak_derived_forms_unknown_para_id(), test_dispatch_weak_principal_part_derivations_emits_papt_only() (+53 more)

### Community 19 - "reference_snapshots.py"
Cohesion: 0.14
Nodes (24): build_session(), canonical_sort_rows(), canonicalize_form_rows(), form_rows_for_stage(), full_flow_metadata(), full_flow_rows(), generate_reference_snapshots(), paradigm_snapshot_rows() (+16 more)

### Community 20 - "test_browse_tui.py"
Cohesion: 0.14
Nodes (45): anyio, _bt_entry_id(), _details_text(), _insert_entry(), _pos_id(), Path, Shell-level tests for the dictionary Textual browse scaffold., Insert linked morphology rows for the ``abbad`` noun entry. (+37 more)

### Community 21 - "DictionaryBrowseQueryService"
Cohesion: 0.13
Nodes (30): _bt_entry_id(), _insert_bt_sense(), _insert_entry(), _insert_inflection_code(), lexicon_source_db(), _next_entry_order(), _pos_id(), Connection (+22 more)

### Community 22 - "ensure_parts_of_speech"
Cohesion: 0.09
Nodes (42): parametrize, Tests for morphology catalog POS normalization helpers., test_catalog_pos_from_bt_pos_cli_aliases(), test_catalog_pos_from_bt_pos_join_values(), test_catalog_pos_from_bt_pos_raises_for_unmapped(), test_catalog_pos_from_wordclass(), test_catalog_pos_from_wordclass_unknown_returns_none(), test_pos_id_from_bt_pos() (+34 more)

### Community 23 - "GenerationRunState"
Cohesion: 0.03
Nodes (93): NamedTuple, _adj_print(), AdjectiveFormGenerator, _build_adjective_formhash(), _build_comparative_title_array(), _build_superlative_title_array(), _build_weak_title_array(), _dedupe_preserve_first() (+85 more)

### Community 24 - "test_markup.py"
Cohesion: 0.05
Nodes (46): Path, test_build_index_from_bt_extracts_and_dedupes(), Path, C before i/ī in any position palatalizes (Rule C)., Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)., gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar., Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc., Cyning (c + y from u) remains non-palatalized; blocklist and only-back. (+38 more)

### Community 25 - "tests/conftest.py"
Cohesion: 0.09
Nodes (32): Popen, cli_context(), ensure_llama_server(), _is_llama_server_healthy(), isolated_morphology_app_data(), isolated_morphology_index_db(), lexicon_source_db(), mock_console() (+24 more)

### Community 26 - "diacritic_disambiguate.py"
Cohesion: 0.07
Nodes (47): Layout, test_fetch_bt_search_entries_uses_search_endpoint(), test_filter_bt_entries_by_normalized_form_empty_list_returns_empty(), test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others(), test_filter_bt_entries_by_normalized_form_no_matches_returns_empty(), test_filter_bt_entries_by_normalized_form_preserves_order(), test_merge_bt_entries_deduplicates_and_reindexes(), test_normalize_bt_spelling_converts_acute_to_macron() (+39 more)

### Community 27 - "cli/dictionary.py"
Cohesion: 0.13
Nodes (23): _count_table_rows(), _default_morphology_data_dir(), _default_source_path(), dictionary_group(), generate_reference_snapshots_command(), _missing_canonical_index_message(), group, Path (+15 more)

### Community 28 - "cli.py"
Cohesion: 0.08
Nodes (32): _configure_logging(), _prompt_backup_cleanup(), command, Context, Run the canonical DB startup gate once for DB-using command trees. Args: ctx:…, Print the some version info of this package,, Click group that preserves the raw argv for help-aware gate decisions. Side…, Persist the raw argv before delegating to Click's normal parser. Args: ctx:… (+24 more)

### Community 29 - "morphology/test_query_service.py"
Cohesion: 0.10
Nodes (46): Namespace, _build_output_sink(), main(), _parse_args(), Run cProfile against the morphology adjective generation stage., Profile ``MorphologyGenerationFacade.generate_adjectives`` and print…, Build the output sink used while profiling adjective generation. Keyword Args:…, Run manual and verb stages needed before adjective generation. Args: session:… (+38 more)

### Community 30 - "File Structure"
Cohesion: 0.11
Nodes (18): Addendum: Tasks 11-14 (added after final whole-branch review), File Structure, Global Constraints, Morphology Generation Class Refactor Implementation Plan, Task 10: Delete the now-empty `generators/` directory, Task 11: Build paradigm-dispatch tables for `NounFormGenerator` and `AdjectiveFormGenerator`, Task 12: Collapse `StrongVerbGenerator`'s callback threading into direct method calls, Task 13: Collapse `WeakVerbGenerator`'s callback threading into direct method calls (+10 more)

### Community 31 - "models/__init__.py"
Cohesion: 0.14
Nodes (24): fixture, sample_doc(), Test importing Beowulf from TEI XML., test_tei_import_beowulf(), test_tei_roundtrip_minimal_prose(), test_tei_roundtrip_minimal_verse_dialogue(), Parse a <div> into a Section model. Args: section_node: The node to parse the…, Fill paragraphs, lines, and subsections for a section. Args: sec: The section… (+16 more)

### Community 32 - "RawBlock"
Cohesion: 0.08
Nodes (29): dialogue_text(), prose_text(), fixture, patch, Unmarked verse gets 1-based line numbers within the section., _t(), test_canonical_converter_prose(), test_canonical_converter_verse() (+21 more)

### Community 33 - "NounFormGenerator"
Cohesion: 0.04
Nodes (57): _build_stem_ar_pl(), _build_stem_ar_sg_ge_da(), _build_stem_ar_sg_no_ac(), _build_stem_daeg_pl(), _build_stem_geminate(), _build_stem_hof_ge_da(), _build_stem_pl_ge_da(), _build_stem_pl_no_ac() (+49 more)

### Community 34 - "MorphologyCatalogLoader"
Cohesion: 0.06
Nodes (45): Path, Build a small morphology slice and verify normalized FK columns on forms., test_catalog_loader_ensure_seeded_refresh(), test_catalog_loader_ensure_seeded_skips_when_populated(), test_catalog_loader_is_idempotent(), test_catalog_loader_populates_recognition_hints_json(), test_catalog_loader_refresh_replaces_stale_rows(), test_catalog_loader_rejects_missing_morph_class_fields() (+37 more)

### Community 35 - "build_session"
Cohesion: 0.15
Nodes (19): FixtureRequest, main(), _mypy_baseline(), _runtime_baseline_ms(), _sha256_rows(), _stage_rows(), build_session(), _command_invokes_perl() (+11 more)

### Community 36 - "sound_changes.py"
Cohesion: 0.08
Nodes (35): SoundChangeSequenceEmitter, SoundManualContextEmitter, SoundManualEmitter, SoundSourceContextEmitter, SoundSourceFormEmitter, test_derive_sound_changed_forms_psinsg2_gst_chain(), test_derive_sound_changed_forms_psinsg2_ngst_chain(), test_derive_sound_changed_forms_psinsg3_td_th_chain() (+27 more)

### Community 37 - "etymology_display.py"
Cohesion: 0.06
Nodes (53): Tests for etymology parsing and browse table formatting., test_format_etymology_display_renders_table_headers(), test_misplaced_attestation_is_flagged(), test_mixed_attestation_and_cognates_split(), test_parse_cognate_chain_with_citation(), test_parse_colon_separated_lang_chain(), test_parse_multiple_german_cognates(), test_parse_norse_words_with_latin_tail() (+45 more)

### Community 38 - "noun.py"
Cohesion: 0.06
Nodes (47): _append_short_syllable_front_vowel_heuristic(), _append_suffix_heuristics(), _append_terminal_a_heuristic(), _append_terminal_e_heuristic(), _apply_final_fallback(), _apply_noun_heuristics(), _assign_by_wright(), _assign_from_advanced_stem() (+39 more)

### Community 39 - "SenseMetadataClassifier"
Cohesion: 0.06
Nodes (27): Unit tests for sense-prefix metadata classification., TestSenseMetadataClassifier, _has_substantive_gloss(), _looks_like_gloss_start(), _normalize_case(), _normalize_gender(), _normalize_modifier(), Normalize one modifier abbreviation token. Args: token: Raw modifier token… (+19 more)

### Community 40 - "format_wright_audit_text"
Cohesion: 0.50
Nodes (4): _append_sample_block(), format_wright_audit_text(), Render a human-readable summary of one Wright audit run. Note: The report stays…, Append one capped sample block to the human-readable audit report. Keyword…

### Community 41 - ".ensure_ready"
Cohesion: 0.10
Nodes (16): _format_backup_prompt_text(), Path, Store the backup path and explicit rebuild recipe for CLI reporting. Keyword…, Delete one file when it exists. Args: path: Filesystem path that may need…, Run the startup database decision tree once. Raises: DatabaseMigrationError:…, Replace any existing canonical DB with a fresh Alembic-managed file. Side…, Create one retained backup and update the canonical sidecar state. Args:…, Apply Alembic migrations and emit the locked success narration. Side Effects:… (+8 more)

### Community 42 - "ingest/pipeline.py"
Cohesion: 0.08
Nodes (33): ProgressCallback, parametrize, Test that deterministic ingestion of text files matches the golden JSON…, test_deterministic_ingestion_regression(), BaseDocumentIngestor, DocumentIngestor, HeuristicDocumentIngestor, ingest_auto() (+25 more)

### Community 43 - "OldEnglishText"
Cohesion: 0.12
Nodes (20): test_tei_export_attributes(), test_tei_export_basic(), test_tei_export_structure(), test_tei_exporter_interface(), Any, Create the publication statement. Args: doc: The document to export. parent:…, Create the source description. Args: doc: The document to export. parent: The…, Emit a section and its content recursively. Args: sec: The section to export.… (+12 more)

### Community 44 - "test_morph_class_browse.py"
Cohesion: 0.14
Nodes (22): _bt_entry_id(), _insert_bt_entry(), Path, Tests for catalog-backed morph-class metadata in lexicon browse details., Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions., Seed one catalog assignment row into a temporary lexicon test database., Insert one minimal ``bt_entries`` row into a temporary lexicon test database.…, _seed_catalog_assignment() (+14 more)

### Community 45 - "MorphologyGenerationFacade"
Cohesion: 0.07
Nodes (46): morphology, morphology_full, assert_snapshot_parity(), full_flow_rows(), Path, Generate canonicalized full-flow rows for parity assertions. Args: session:…, Assert full-flow parity against a canonical snapshot file. Args: session:…, canonical_sort_rows() (+38 more)

### Community 46 - "NormalizedTitleJoinIndex"
Cohesion: 0.09
Nodes (24): _index(), Unit tests for NormalizedTitleJoinIndex., test_resolve_all_exactly_one_title_across_pos(), test_resolve_all_no_match(), test_resolve_all_pos_direct_multiple_matches(), test_resolve_all_pos_direct_single_match(), test_resolve_all_variant_with_pos_filter(), test_resolve_all_variant_without_pos_filter() (+16 more)

### Community 47 - "wright_audit.py"
Cohesion: 0.04
Nodes (76): Seed one catalog assignment row into a temporary lexicon test database., _seed_catalog_assignment(), _dictionary_line(), _make_audit_source_dir(), _manual_form_line(), _para_vb_line(), Path, Tests for legacy Wright source auditing. Phase D source contract: The audit… (+68 more)

### Community 48 - "wright-morphology-fixture.schema.json"
Cohesion: 0.05
Nodes (39): 1.0, morph_classes, Old English, schema_version, sources, wright-modern-morphology, additionalProperties, description (+31 more)

### Community 49 - "test_cli_diacritic_disambiguate.py"
Cohesion: 0.11
Nodes (37): _minimal_index_payload(), Path, Minimal macron index payload for diacritic add/delete tests., test_diacritic_add_fails_when_exists_without_force(), test_diacritic_add_fails_when_key_in_ambiguous_even_with_force(), test_diacritic_add_force_overwrites(), test_diacritic_add_inserts_pair(), test_diacritic_add_normalizes_key() (+29 more)

### Community 50 - "wyrdcraeft/settings.py"
Cohesion: 0.24
Nodes (8): ConfigurationError, FileError, OejsonextractorError, Raised when file I/O operations fail., Base exception for all wyrdcraeft errors., Raised when settings or configuration fails., Settings management for wyrdcraeft., Validate settings and ensure required directories exist. Raises:…

### Community 51 - "diacritics.py"
Cohesion: 0.10
Nodes (29): patch, With only input given, paths default to stem + infix + extension., test_source_mark_diacritics_default_paths(), test_source_mark_diacritics_writes_text_and_ambiguities(), test_source_mark_diacritics_writes_unknowns_file(), _prompt_form_annotation(), _prompt_pos_code(), Prompt for a controlled POS code for one attested form. Args: attested_form:… (+21 more)

### Community 52 - "test_form_decode.py"
Cohesion: 0.09
Nodes (40): MorphologyTableInputRow, Tests for morphology function-code decoding., test_build_adjective_sidebar_uses_payload_inflection(), test_build_adverb_sidebar_decodes_superlative_su_code(), test_build_morphology_table_fills_inflection_from_morph_class_label(), test_build_morphology_table_includes_surface_form_column(), test_build_morphology_table_sorts_adjectives_by_degree_inflection_and_case(), test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms() (+32 more)

### Community 53 - "print_info"
Cohesion: 0.07
Nodes (33): Tests for CLI utilities., Test success panel has correct styling., Test info printing functions., Test basic info printing., Test info panel has correct styling., Test console objects., Test that console objects are properly initialized., Test progress creation. (+25 more)

### Community 54 - "Session: Morphology Wright Catalog — Phase 2 complete"
Cohesion: 0.15
Nodes (7): Architecture, Deliverables, Known limitations (deferred), Next, Session: Morphology Wright Catalog — Phase 2 complete, Summary, Validation

### Community 55 - "test_index_pipeline.py"
Cohesion: 0.07
Nodes (53): CorpusSampleResult, DictionaryCorpusSampler, main(), Path, Index source lines by lookup key while preserving source line order. Returns:…, Sample keys by deterministic every-Nth stratification. Args: ordered_keys: Keys…, Result of one corpus-sample build run. Attributes: keys: Selected lookup keys…, Collect all editorial siblings for sampled keys in corpus order. Args:… (+45 more)

### Community 56 - "properties"
Cohesion: 0.06
Nodes (34): type, type, type, properties, type, type, type, type (+26 more)

### Community 57 - "properties"
Cohesion: 0.06
Nodes (34): description, minLength, type, $ref, default, description, enum, type (+26 more)

### Community 58 - "create_engine"
Cohesion: 0.15
Nodes (27): _fetch_form_entry_id(), _insert_bt_entry(), _insert_bt_variant(), _insert_form(), _pos_id(), Connection, fixture, Path (+19 more)

### Community 59 - "form_fk_resolver.py"
Cohesion: 0.18
Nodes (13): _fetch_rows(), load_normalized_title_join_index(), Connection, Fetch three-column join rows from SQLAlchemy or SQLite connections. Args:…, Build a dictionary join index from canonical ``bt_entries`` and variants. Args:…, _load_morph_class_ids(), _load_morph_class_ids_by_key(), Connection (+5 more)

### Community 60 - "cli"
Cohesion: 0.09
Nodes (33): Test that the OCR command group has been removed from the CLI., test_ocr_command_group_removed(), Test the convert command without LLM (heuristic mode)., test_convert_command_no_llm(), CLI smoke tests for Bosworth-Toller dictionary commands., test_dictionary_audit_wright_help(), test_dictionary_browse_help(), test_dictionary_build_help() (+25 more)

### Community 61 - "test_loaders.py"
Cohesion: 0.13
Nodes (19): fixture, source_loader(), test_load_from_file_rejects_pdf(), test_load_from_file_text(), test_load_from_file_unsupported(), test_source_loader_load_file(), test_source_loader_rejects_http_url(), test_tei_source_loader_load_tei() (+11 more)

### Community 62 - "Path"
Cohesion: 0.35
Nodes (12): _build_unified_source_db(), _morphology_data_dir(), Path, Bootstrap canonical DB with dictionary + limited morphology generation., _subset_dictionary(), test_dictionary_build_bootstraps_empty_app_data_dir(), test_dictionary_build_runs_morphology_when_forms_table_is_empty(), test_dictionary_build_skips_morphology_when_forms_exist_unless_requested() (+4 more)

### Community 63 - "check_napoleon_gate.py"
Cohesion: 0.08
Nodes (44): AST, AsyncFunctionDef, ClassDef, FunctionDef, Module, cyclomatic(), report(), _check_file() (+36 more)

### Community 64 - "Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅"
Cohesion: 0.07
Nodes (29): Background, Explicit non-goals, File Map, Lexicon rebuild (Slice 1), Lexicon SQLAlchemy Rebuild + Normalized Title Join Index Implementation Plan, Locked Decisions, Normalized title join index (Slice 2), References (+21 more)

### Community 65 - "write_backup_state"
Cohesion: 0.13
Nodes (26): Path, test_backup_state_round_trip_uses_sidecar_beside_canonical_db(), test_create_backup_copies_database_and_keeps_latest_by_default(), test_restore_backup_overwrites_database_contents(), create_backup(), list_backups(), _prune_old_backups(), datetime (+18 more)

### Community 66 - "test_attach_morphology_db.py"
Cohesion: 0.47
Nodes (8): _index_with_attach(), Path, Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite., Seed the canonical ``forms`` table via the real SQLAlchemy sink., _seed_forms_table(), test_attach_missing_db_fails_for_canonical_only_mode(), test_attach_preserves_forms_and_writes_bt_entries(), test_attach_rerun_is_idempotent_and_preserves_forms()

### Community 67 - ".load_from_tei"
Cohesion: 0.24
Nodes (6): Document, TeiReader, Extract metadata from TEI header. Args: tei_reader: The TEI reader to extract…, Parse the TEI body. Args: doc: The document to parse the body from. ns: The…, Load a TEI XML document. Args: source: The source to load the document from.…, Import TEI XML using delb and acdh-tei-pyutils. Args: tei_xml: The TEI XML to…

### Community 68 - "LegacyDatabaseResetRequired"
Cohesion: 0.33
Nodes (8): Path, test_legacy_bootstrap_failure_restores_cleanly_and_raises_typed_error(), test_legacy_morphology_db_is_backed_up_then_requires_rebuild(), DatabaseMigrationError, LegacyDatabaseResetRequired, RuntimeError, Legacy database reset stop signal with rebuild guidance. Args: backup_path:…, Startup migration failure with traceback and rebuild guidance. Args: message:…

### Community 69 - "browse_query.py"
Cohesion: 0.07
Nodes (38): Build a sort key that orders senses by hierarchical path. ``4`` sorts before…, sense_path_sort_key(), _append_unique(), _best_hit(), _browse_hit_sort_key(), BrowseSearchHit, EntrySense, _extract_gender_person_number() (+30 more)

### Community 70 - "OEFilter"
Cohesion: 0.25
Nodes (6): test_oe_filter(), OEFilter, Logic for filtering Old English text from raw blocks., Initialize Old English detection state., Test if a block of text looks like Old English. Args: text: The text to test.…, Filter out blocks that do not look like Old English. A block is kept if at…

### Community 71 - "markup.py"
Cohesion: 0.04
Nodes (79): corpus_index_db(), _index_fixture(), fixture, Path, Unit and integration tests for BTQueryService., sample_index_db(), _seed_forms_table(), test_bt_senses_round_trip_rich_fields() (+71 more)

### Community 72 - "setter"
Cohesion: 0.06
Nodes (23): setter, The words: the words to be processed. Returns: The current word list from…, Forward an updated word list onto :attr:`word_pool`. Args: value: The new word…, The manual forms. Returns: The manual forms list from :attr:`word_pool`., Forward an updated manual forms list onto :attr:`word_pool`. Args: value: The…, The verb paradigms. Returns: The verb paradigms mapping from :attr:`word_pool`., Forward an updated verb paradigms mapping onto :attr:`word_pool`. Args: value:…, The prefixes. Returns: The prefixes list from :attr:`word_pool`. (+15 more)

### Community 73 - "split_prose_and_verse_runs"
Cohesion: 0.33
Nodes (8): _is_heading_line(), _is_number_line(), _is_verse_line(), Test if a line looks like a heading., Heuristic: short, line-broken, non-empty lines typical of OE verse editions., Test if a line is just a numbering marker (e.g. "[12]" or "5")., Split text into ordered prose / verse chunks. - Preserves original text exactly…, split_prose_and_verse_runs()

### Community 74 - "test_corpus_sample.py"
Cohesion: 0.33
Nodes (6): _load_manifest(), Smoke tests for the stratified Bosworth-Toller corpus sample fixture., Ensure corpus fixture is present and within phase-02b size constraints., Parse every corpus line and require deterministic parse or explicit skip., test_corpus_sample_lines_parse_without_raising(), test_corpus_sample_manifest_and_line_count_bounds()

### Community 75 - "catalog_db"
Cohesion: 0.29
Nodes (6): catalog_db(), fixture, Path, test_from_db_path_uses_isolated_database(), Path, Build a query service from one canonical SQLite database path. Args: db_path:…

### Community 76 - "enum"
Cohesion: 0.08
Nodes (26): common, comparative, dual, feminine, first, masculine, neuter, plural (+18 more)

### Community 77 - "MorphologyDictionaryCleaner"
Cohesion: 0.06
Nodes (38): parametrize, Tests for morphology dictionary TSV cleanup., test_clean_dictionary_fixes_bt_diphthongs_in_col2(), test_clean_dictionary_lowercases_col2_dedupes_and_backups(), test_clean_dictionary_raises_when_source_missing(), test_should_lowercase_col2_only_all_upper_letters(), patch, Tests for the main module. (+30 more)

### Community 78 - "test_form_fk_resolver.py"
Cohesion: 0.17
Nodes (24): _insert_bt_entry(), _insert_bt_variant(), _insert_lemma_assignment(), Connection, fixture, Path, Tests for morphology form foreign-key resolution., resolver_db() (+16 more)

### Community 79 - "test_dictionary_build_relinks_forms_after_dictionary_rebuild"
Cohesion: 0.53
Nodes (6): _fetch_entry_id(), _fetch_form_entry_id(), _insert_form(), _pos_id(), Connection, test_dictionary_build_relinks_forms_after_dictionary_rebuild()

### Community 80 - "print_error"
Cohesion: 0.10
Nodes (25): Test error printing functions., Test basic error printing., Test error printing with suggestions., Test error printing without suggestions., Test error panel has correct styling., TestPrintError, _mark_diacritics_derived_path(), argument (+17 more)

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

### Community 86 - "BT Dictionary Parser Rebuild Implementation Plan"
Cohesion: 0.18
Nodes (8): BT entry identity follows source blocks, BT Dictionary Parser Rebuild Implementation Plan, Commit strategy, Execution handoff, Live corpus findings to design against, Locked decisions (do not re-litigate), Review loop, Spec anchors

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

### Community 91 - "lexicon_source_db"
Cohesion: 0.40
Nodes (5): empty_browse_db(), lexicon_source_db(), fixture, Dictionary-backed canonical DB fixture for browse TUI tests., Canonical schema with no dictionary rows for browse readiness tests.

### Community 92 - "sqlalchemy.py"
Cohesion: 0.05
Nodes (54): DeclarativeBase, Path, Tests for Wright section markdown parsing and catalog text ingest., test_ingest_result_counts_and_warnings(), test_ingester_force_overwrites_existing_text(), test_ingester_is_idempotent_without_force(), test_ingester_updates_null_sections(), test_lookup_wright_section_text_returns_stored_value() (+46 more)

### Community 93 - ".parse"
Cohesion: 0.05
Nodes (24): MacronIndex, In-memory macron index model for diacritic restoration., In-memory lookup maps for macron restoration., Initialize parser collaborators for split and POS extraction. Args: splitter:…, Parse one source line into ``RawBTLine`` plus phase-02 metadata. Args:…, Classify one line into ``BTLineKind``. Args: body: Main ``@`` field body…, Detect whether a line is primarily a cross-reference. Args: body: Main ``@``…, Extract the POS prefix fragment immediately after the first headword. Args:… (+16 more)

### Community 94 - "test_cli_commands.py"
Cohesion: 0.50
Nodes (3): Tests for CLI commands with low coverage., Test that Settings has no ocr_ fields., test_settings_has_no_ocr_fields()

### Community 95 - "required"
Cohesion: 0.11
Nodes (19): aliases, canonical_name, features, id, is_assignable, mapping_rationale, modern_class, paradigmatic_words (+11 more)

### Community 96 - "features"
Cohesion: 0.11
Nodes (19): citation_apa, retrieved_date, source_key, url, $defs, features, recognitionHints, source (+11 more)

### Community 97 - "FormRow"
Cohesion: 0.07
Nodes (23): FormRow, Canonical emitted morphology row used by sinks and query services. Legacy…, _build_form_rows_from_form_data(), FormSink, Connection, Protocol, Materialize one finalized output row from legacy ``form_data`` fields. Note:…, Emit parity rows from legacy ``form_data`` and update the run's output counter.… (+15 more)

### Community 98 - "test_lemma_morph_assignment.py"
Cohesion: 0.29
Nodes (14): assigner(), _assignment(), _class_key(), _make_verb_paradigm(), _make_word(), fixture, Tests for lemma-to-morph-class assignment during morphology build., Unmatched inflectable lemmas produce no ``lemma_morph_classes`` row. When no… (+6 more)

### Community 99 - "Configuration: Command Line Tool guide"
Cohesion: 0.15
Nodes (18): wyrdcraeft settings CLI command doc, wyrdcraeft source convert CLI command doc, Configuration: Command Line Tool guide, wyrdcraeft FAQ, Standard JSON Representation for Old English Texts (schema spec), Installation guide, Quickstart guide, Using the Command Line Interface guide (+10 more)

### Community 100 - "DatabaseStartupRuntime"
Cohesion: 0.33
Nodes (17): _create_pre_alembic_forms_db(), _make_settings(), parametrize, Path, test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(), test_fresh_missing_db_bootstraps_with_alembic_path(), test_interactive_blank_prompt_keeps_backup_without_retry(), test_interactive_prompt_matches_locked_wording_and_deletes_backup() (+9 more)

### Community 101 - "ensure_inflection_codes"
Cohesion: 0.08
Nodes (41): _assert_no_null_pos_ids(), _assert_no_null_text_pos(), downgrade(), _downgrade_bt_entries(), _downgrade_lemma_morph_classes(), _downgrade_morph_classes(), Connection, Replace legacy BT text POS and headword columns with normalized fields. Args:… (+33 more)

### Community 102 - "TestCLIVersion"
Cohesion: 0.25
Nodes (5): Test the version command., Test the version command displays version information., Test the version command with verbose flag., Test the version command with quiet flag., TestCLIVersion

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
Cohesion: 0.29
Nodes (6): ADR 0009: Collapse morphology generation callback-soup into PoS generator classes, Alternatives Considered, Consequences, Context, Decision, Status

### Community 110 - "_format_entry_text"
Cohesion: 0.50
Nodes (4): _format_entry_text(), _format_sense_label(), Render one sense label with trailing punctuation for text output. Args: label:…, Render one consolidated dictionary entry as human-readable text. Args: entry:…

### Community 111 - "DictionaryBuildStage"
Cohesion: 0.21
Nodes (9): DictionaryBuildStage, StrEnum, Stable stage labels emitted during one unified dictionary build., DictionaryBuildProgress, Protocol, Progress callback surface used during unified dictionary builds., Mark one build stage active. Args: stage: Stage being entered. Keyword Args:…, Advance one build stage. Args: stage: Stage being advanced. Keyword Args:… (+1 more)

### Community 112 - "_collect_widget_ids"
Cohesion: 0.67
Nodes (3): _collect_widget_ids(), Collect all widget ids reachable from one widget tree root. Args: widget: Root…, Widget

### Community 113 - "_insert_inflection_code"
Cohesion: 0.67
Nodes (3): _insert_inflection_code(), Connection, Insert one ad-hoc ``inflection_codes`` row and return its id.

### Community 114 - "morphology_row_matches_pos"
Cohesion: 0.40
Nodes (5): test_morphology_row_matches_entry_pos_filters_participle_for_noun(), morphology_row_matches_pos(), Return morphology wordclass labels that match one dictionary POS label. Args:…, Return whether one morphology row belongs to the dictionary entry POS. Keyword…, wordclasses_for_entry_pos()

### Community 115 - "Implementation Slices"
Cohesion: 0.33
Nodes (6): Implementation Slices, Slice 1: consume visibility review, Slice 2: models and schema, Slice 3: parser and merge, Slice 4: query and CLI, Slice 5: rebuild and verify

### Community 117 - "GeneratorSession.load_all"
Cohesion: 0.17
Nodes (12): GeneratorSession (services.morphology), wyrdcraeft.models.morphology, GeneratorSession, LemmaMorphClassAssigner, MorphologyCatalogLoader, Morphology generation flow (concept), GeneratorSession.load_all(), LemmaMorphClassAssigner.assign_all() (+4 more)

### Community 118 - "wyrdcraeft 1.1.0 release (2026-03-02)"
Cohesion: 0.22
Nodes (13): GPalatalizer, MacronApplicator, wyrdcraeft.models.macron_index, wyrdcraeft 1.0.0 initial release (2026-03-01), wyrdcraeft 1.1.0 release (2026-03-02), wyrdcraeft source mark-diacritics, Diacritic restoration runtime processing flow, wyrdcraeft diacritic add (+5 more)

### Community 119 - "_table_text"
Cohesion: 0.67
Nodes (3): DataTable, Flatten a DataTable into plain text for assertions. Args: table: DataTable…, _table_text()

### Community 122 - "Phase 2 — Lemma Morph Class Assignment"
Cohesion: 0.20
Nodes (10): Cleanup (optional same PR or follow-up), Phase 2 — Gate A: Spec review, Phase 2 — Gate B: Code review, Phase 2 — Lemma Morph Class Assignment, Phase 2 validation, Task 1: Schema + migration, Task 2: POS normalization helper, Task 3: Paradigm exemplar registry (+2 more)

### Community 123 - "DictionaryBrowseStartupStage"
Cohesion: 0.15
Nodes (12): Progress, create_stderr_console(), Console, Create one Rich console bound to current stderr stream. Returns: Console…, DictionaryBrowseStartupStage, StrEnum, Browse startup progress helpers for dictionary browse workflow., Stable stage labels for dictionary browse startup progress. (+4 more)

### Community 124 - "Morphology Wright catalog — Phase 1 session (2026-07-04)"
Cohesion: 0.12
Nodes (17): 1. Circular import on full morphology test collection, 2. Untracked plan directory, 3. Package data, Branch and commits, Build integration, Commits this session (Phase 1 Tasks 1–4), Goal (locked design), Key files (+9 more)

### Community 125 - ".apply"
Cohesion: 0.33
Nodes (5): TContext_contra, TWord_contra, Ordered classification rule for paradigm assignment., Return matched paradigm labels for ``word`` in ``context``. Note: Paradigm…, Rule

### Community 126 - "File map"
Cohesion: 0.17
Nodes (12): File map, Global Constraints, LLM and unstructured leave `source convert` Implementation Plan, Self-review (spec coverage), Task 1: Local `.txt` loader returns `RawBlock`s, Task 2: Strip LLM from convert CLI and `DocumentIngestor`, Task 3: Delete LLM ingest types, extractors, prompts, Task 4: Delete dictionary LLM repair (+4 more)

### Community 127 - "DictionaryPosInferer"
Cohesion: 0.20
Nodes (12): PosInferenceCancelCheck, PosInferenceProgress, PosInferenceWarningSink, DictionaryPosInferer, Connection, Attempt one inferred POS update, skipping duplicate and homograph rows. Args:…, Unwrap one SQLAlchemy connection to the underlying SQLite driver. Args:…, Resolve the seeded ``unknown`` part-of-speech identifier. Args: connection:… (+4 more)

### Community 128 - "Execution order"
Cohesion: 0.18
Nodes (11): Execution order, Task 10: Full validation and handoff, Task 1: Move dictionary assets into packaged resources, Task 2: Add schema support for source-block entry identity and rich senses, Task 3: Build deterministic sense-tree normalization, Task 4: Add sense prefix classifier for modifiers, grammatical context, and usage notes, Task 5: Refactor editorial merge around source blocks and canonical sense paths, Task 6: Expand warning and audit plumbing (+3 more)

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

### Community 142 - "test_paths.py"
Cohesion: 0.16
Nodes (21): parametrize, Path, test_get_app_data_path_platform_defaults(), test_get_app_data_path_settings_override(), test_get_app_data_path_unsupported_platform(), test_get_canonical_db_path_creates_parent(), test_isolated_morphology_index_db_uses_canonical_filename(), test_resolve_db_path_explicit_dir_mkdirs_target() (+13 more)

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
Cohesion: 0.32
Nodes (7): _canonicalize(), parametrize, Prompt regression and schema validation tests. These tests are designed to be…, Deterministic ordering for stable snapshot comparisons., Placeholder regression test. Today: just ensures the expected snapshot is…, test_expected_json_is_schema_valid(), test_snapshot_regression_contract()

### Community 148 - "20260704_02_lemma_morph_classes.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add recognition hints to morph classes and create lemma assignment table. Side…, Drop lemma assignment table and recognition hints column. Side Effects: Removes…, upgrade()

### Community 149 - ".run"
Cohesion: 0.17
Nodes (10): DictionaryBuildStatus, DictionaryBuildReport, Connection, Summary of one unified dictionary build run., Run the unified dictionary build pipeline against one source file. Keyword…, Relink every stored form row against the rebuilt dictionary tables. Args:…, Return the current ``forms`` row count. Args: connection: Open SQLAlchemy…, Return the number of forms carrying a linked dictionary entry. Args:… (+2 more)

### Community 150 - "BackupStateStore"
Cohesion: 0.13
Nodes (9): datetime, Capture one startup runtime configuration and its collaborators. Keyword Args:…, Store the startup migration failure details for CLI reporting. Args: message:…, BackupStateStore, Persist backup prompt state beside one canonical SQLite database. Args:…, Store one canonical database path for later sidecar operations. Args: db_path:…, Load the current backup sidecar contents. Returns: Parsed sidecar state, or…, Save one backup sidecar payload. Args: state: JSON-serializable backup metadata. (+1 more)

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
Cohesion: 0.06
Nodes (34): Immutable context shared by the strong principal-part emission methods. Args:…, Immutable context shared by the strong infinitive-derived emission methods.…, _StrongInfDerivationContext, _StrongPrincipalPartContext, FormOutput, Emit one normalized form record to ``output``. Note: Form realization follows…, Entry point: route one strong-paradigm part into principal-part generation.…, Generator for Old English strong-verb form derivation. Handles the strong-… (+26 more)

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

### Community 163 - "enum"
Cohesion: 0.40
Nodes (5): past, present, enum, type, participle

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

### Community 169 - "generation/query.py"
Cohesion: 0.06
Nodes (48): test_format_morph_class_display_label_falls_back_to_canonical_name(), test_format_morph_class_display_label_prefers_compact_modern_label(), test_infer_bt_pos_filter_maps_unambiguous_noun(), test_infer_bt_pos_filter_returns_none_for_mixed_wordclasses(), test_resolve_dictionary_db_path_prefers_explicit_override(), test_resolve_dictionary_db_path_uses_sibling_dictionary(), MorphClassQueryMetadata, QueryFormRow (+40 more)

### Community 170 - "20260707_01_drop_search_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop legacy lexicon search-index tables from the canonical schema. Side…, Recreate empty legacy lexicon search-index tables. Side Effects: Restores empty…, upgrade()

### Community 171 - "20260707_03_bt_source_blocks_and_rich_senses.py"
Cohesion: 0.40
Nodes (4): downgrade(), Restore homograph uniqueness and remove rich sense metadata columns. Side…, Drop homograph uniqueness and add source-block sense metadata columns. Side…, upgrade()

### Community 173 - "_adjective_row_sort_key"
Cohesion: 0.50
Nodes (4): _adjective_row_sort_key(), morphology_table_columns(), Build the browse sort key for one adjective morphology table row. Args: row:…, Return browse-table column headers for one morphology wordclass. Args:…

### Community 174 - "File Structure"
Cohesion: 0.15
Nodes (12): File Structure, GeneratorSession → WordPool + GenerationRunState Split Implementation Plan, Global Constraints, Task 1: Introduce `WordPool` + `GenerationRunState`, compose `GeneratorSession` from them, Task 2: Migrate the assigners (`noun.py`, `verb.py`, `adj.py`) onto `WordPool`, Task 3: Migrate the shared sink + row-emission leaf layer onto `GenerationRunState`/`WordPool`, Task 4: Migrate `generation/adv_forms.py` (smallest generator — proves the pattern end to end), Task 5: Migrate `generation/num_forms.py` (+4 more)

### Community 175 - "20260707_02_bt_senses_entry_order_index.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add index supporting ordered sense lookup by dictionary entry. Side Effects:…, Remove ordered lookup index for dictionary sense reads. Side Effects: Drops the…, upgrade()

### Community 177 - "dictionary/pipeline.py"
Cohesion: 0.07
Nodes (46): Client, _parsed_line(), BTSense, Path, Tests for optional Bosworth-Toller LLM parse repair., test_apply_fixes_keeps_deterministic_line_on_validation_failure(), test_apply_fixes_patches_only_warning_lines(), test_extract_json_object_from_fenced_response() (+38 more)

### Community 178 - "runtime.py"
Cohesion: 0.07
Nodes (41): Config, Path, Focused tests for the normalized Bosworth-Toller SQLite sink., _run_index(), _seed_forms_table(), test_bt_entries_allow_duplicate_norm_key_pos(), test_sink_persists_headword_with_normalized_pos_fk(), test_sink_rerun_reuses_seeded_parts_of_speech_rows() (+33 more)

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

### Community 187 - "WrightAuditResult"
Cohesion: 0.33
Nodes (4): Structured Phase 4 audit output for human and JSON reporting. Note: The audit…, Return the total number of scanned source rows. Returns: Sum of all per-source…, Convert the full audit result into a JSON-friendly payload. Returns: Nested…, WrightAuditResult

### Community 188 - "BT Structural Visibility Review"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT Structural Visibility Review, Candidate Types To Include, Deliverables, Dependencies, Downstream Use, Locked Decisions, Non-Goals (+4 more)

### Community 189 - "wyrdcraeft"
Cohesion: 0.15
Nodes (12): All other code, Bosworth-Toller Old English Dictionary, Canonical database, Contributing, Contributing, Licensing and Provenance, Documentation, Features, Installation (+4 more)

### Community 191 - "Phase D — Drop Legacy Form String Columns"
Cohesion: 0.15
Nodes (12): Phase D — Commit, Phase D — Drop Legacy Form String Columns, Phase D — Gate A: Spec review checklist, Phase D — Gate B: Code review checklist, Phase D validation, Post-phase checklist (coordinator), Task 1: Alembic migration `20260706_04`, Task 2: Sink + query path cleanup (+4 more)

### Community 192 - "LemmaMorphClassAssigner"
Cohesion: 0.05
Nodes (40): _make_word(), query_service(), Tests for read-only Wright catalog lemma class lookup., test_lookup_missing_lemma_returns_none(), test_lookup_normalizes_title_before_query(), test_lookup_stan_noun_returns_masculine_a_stem(), AssignmentResult, _AssignmentWrite (+32 more)

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

### Community 213 - "source_db.py"
Cohesion: 0.33
Nodes (8): make_lexicon_source_db(), Path, Helpers for building morphology SQLite databases used in lexicon tests., Build a morphology database seeded with ``forms`` and ``bt_*`` tables. Args:…, Write minimal ``forms`` rows into a morphology SQLite database. Args: db_path:…, Attach minimal Bosworth-Toller ``bt_*`` tables to a morphology database. Args:…, seed_bt_tables(), seed_forms()

### Community 215 - "BT Usage-vs-Sense Cleanup Handoff"
Cohesion: 0.25
Nodes (8): BT Usage-vs-Sense Cleanup Handoff, Current understanding, Key files, Proposed implementation, Suggested review artifact shape, Suggested skills, Useful corpus findings already gathered, Validation required after edits

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

### Community 221 - "Phase B — Forms Foreign Keys (Legacy Strings Remain)"
Cohesion: 0.18
Nodes (11): Phase B — Commit, Phase B — Forms Foreign Keys (Legacy Strings Remain), Phase B — Gate A: Spec review checklist, Phase B — Gate B: Code review checklist, Phase B validation, Task 1: Alembic migration `20260706_02`, Task 2: Form FK resolver service, Task 3: Sink propagation (+3 more)

### Community 223 - "Phase 2 — Wright § Text Ingest Report"
Cohesion: 0.14
Nodes (13): Wright § markdown text ingest into wright_sections.section_text, Files changed, Implementation notes, Manual spot-check, Phase 2 — Wright § Text Ingest Report, Self-review, Summary, Task 2.1 — Markdown § parser (+5 more)

### Community 224 - "OCR pipeline moves to bochord"
Cohesion: 0.50
Nodes (4): Consequence, Not removed, OCR pipeline moves to bochord, Removed from wyrdcraeft

### Community 226 - "File map"
Cohesion: 0.29
Nodes (7): Domain/runtime models, File map, Package/runtime assets, Pipeline/editorial logic, Query/read surfaces, Schema, Tests/docs

### Community 227 - "AGENTS.md"
Cohesion: 0.12
Nodes (14): AGENTS.md, Architecture (Required), AWS Interaction, Documentation Contract (Required), graphify, Implementation Priority (Required), Post-Implementation Quality Gate (Required), Project Structure (Mandatory) (+6 more)

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

### Community 247 - "session.py"
Cohesion: 0.06
Nodes (39): ManualForm, Manual form model for ``manual_forms.txt`` ingest rows. Legacy string fields…, _assign_by_wright(), Resolve the Wright 425 adjective paradigm using vowel-sensitive matching., Apply ordered Wright-token rules and return the first matching paradigm., _wright_rule_425(), Morphology paradigm assigners., _assign_verb_by_advanced_diacritics() (+31 more)

### Community 248 - "Orchestrator Checkpoint"
Cohesion: 0.29
Nodes (6): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase status, Resume here

### Community 249 - "test_cli_convert.py"
Cohesion: 0.40
Nodes (4): Test the convert command with a missing source file., test_convert_command_missing_source(), test_convert_rejects_http_source(), test_convert_rejects_use_llm_flag()

### Community 250 - ".__init__"
Cohesion: 0.29
Nodes (4): Path, Initialize a SQLAlchemy sink for emitted morphology rows. Note: Index schema…, Ensure the canonical ``forms`` table and its indexes exist., Tune SQLite for bulk morphology index writes. Side Effects: Sets WAL mode and…

### Community 252 - "BTSenseSegmenter"
Cohesion: 0.04
Nodes (34): _load_golden(), fixture, Arabic display labels for canonical sense paths., Unit tests for specific segmenter behaviours., Body with no sense labels produces a single unlabelled sense., Bold <B>I.</B>/<B>II.</B> labels produce two ordered senses., <B>I</B>. (period outside bold tag) is recognised as a sense label., Plain (unbolded) Roman-numeral labels followed by an italic span are split… (+26 more)

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

### Community 270 - "Old English c/g Palatalization Rule System"
Cohesion: 0.83
Nodes (4): Old English c/g Palatalization Rule System, c-Palatalization Force-Non-Palatalize Exception List, c-Palatalization Force-Palatalize Exception List, g Frontal-Vowel Palatalization Exception List

### Community 271 - "filter_display_variants"
Cohesion: 0.40
Nodes (5): test_filter_display_variants_drops_genitive_endings(), filter_display_variants(), is_genitive_variant_token(), Return whether one variant token is a weak-noun genitive ending. Args: token:…, Drop genitive-ending tokens from dictionary variant spellings. Args: variants:…

### Community 274 - "infer_bt_pos_from_wordclasses"
Cohesion: 0.40
Nodes (4): test_infer_bt_pos_from_wordclasses_requires_single_mapping(), infer_bt_pos_from_wordclasses(), Shared morphology wordclass to dictionary POS mapping helpers., Map distinct morphology wordclasses to one dictionary POS when unambiguous.…

### Community 282 - "GeneratorSession"
Cohesion: 0.14
Nodes (27): _make_verb_paradigm(), _make_word(), test_set_adj_paradigm_stem_propagation(), test_set_adj_paradigm_wright_rule_425(), test_set_noun_paradigm_advanced_stem_propagation(), test_set_noun_paradigm_final_fallback_neuter_long_stem(), test_set_noun_paradigm_final_fallback_neuter_short_stem(), test_set_noun_paradigm_heuristic_incel_suffix() (+19 more)

### Community 295 - ".get_details"
Cohesion: 0.14
Nodes (13): _dominant_paradigm(), filter_display_variants(), _json_string_list(), Any, RowMapping, Deserialize a JSON string array stored in SQLite text columns. Args: payload:…, Drop genitive-ending tokens from dictionary variant spellings. Args: variants:…, Project one SQLite row into a ``MorphologyRow`` dataclass. Args: row: Mapping… (+5 more)

### Community 299 - "DictionaryBrowseDataError"
Cohesion: 0.40
Nodes (5): DictionaryBrowseDataError, _ensure_browse_ready(), RuntimeError, Validate that browse tables exist and contain searchable rows. Args:…, Raised when dictionary browse data is unavailable for the TUI shell.

### Community 300 - ".write_json"
Cohesion: 0.40
Nodes (3): Path, Write the report as formatted JSON to disk. Args: report_path: Destination JSON…, Serialize the report to a JSON-friendly mapping. Returns: Dictionary suitable…

### Community 301 - "WordPool"
Cohesion: 0.07
Nodes (21): _make_word(), Regression tests for the GeneratorSession -> WordPool/GenerationRunState split.…, test_session_composes_word_pool_and_run_state(), test_word_pool_append_participle(), test_word_pool_categorize_matches_load_all_categorization(), Assign paradigms in-place for session words. Note: Paradigm assignment reflects…, FormOutput, Bind an adverb form generator to one word pool, run state, and output sink.… (+13 more)

### Community 302 - "progress.md"
Cohesion: 0.50
Nodes (3): Phase A SDD Progress, Prior ledger (Phase A — do not treat as ADR 0010), SDD Progress — ADR 0010 LLM/unstructured leave source convert

### Community 307 - "test_generation_package_imports.py"
Cohesion: 0.25
Nodes (7): Regression test for the generation-package import-cycle fix.…, The package must not carry a facade re-export that recreates the cycle., The only import path any real caller uses must keep working., The facade's verb-generation method is the production entrypoint., test_facade_still_importable_directly(), test_facade_verb_method_still_importable(), test_generation_package_does_not_reexport_facade()

### Community 312 - "TestCLIErrorHandling"
Cohesion: 0.33
Nodes (4): Test CLI error handling., Test CLI without arguments shows help., Test invalid command shows error., TestCLIErrorHandling

### Community 314 - "TestConsoleQuietMode"
Cohesion: 0.33
Nodes (4): Test console quiet mode functionality., Test that console can be set to quiet mode., Test that stderr console can be set to quiet mode., TestConsoleQuietMode

## Ambiguous Edges - Review These
- `task-phase1-morph-class-browse-report.md` → `task-phase2-wright-text-ingest-report.md`  [AMBIGUOUS]
  doc/sessions/task-phase2-wright-text-ingest-report.md · relation: references
- `The Seafarer (Old English poem, test fixture)` → `Old English Bosworth-Toller Dictionary Text`  [AMBIGUOUS]
  tests/fixtures/seafarer.txt · relation: conceptually_related_to

## Knowledge Gaps
- **904 isolated node(s):** `release.sh script`, `wyrdcraeft`, `IPA_AUDIO`, `$schema`, `$id` (+899 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2724 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `task-phase1-morph-class-browse-report.md` and `task-phase2-wright-text-ingest-report.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `The Seafarer (Old English poem, test fixture)` and `Old English Bosworth-Toller Dictionary Text`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `GeneratorSession` connect `GeneratorSession` to `build_session`, `MorphologyGenerateProgressCoordinator`, `setter`, `OENormalizer`, `Word`, `MorphologyGenerationFacade`, `WordPool`, `_RecordingSink`, `WeakVerbGenerator`, `reference_snapshots.py`, `source_db.py`, `session.py`, `morphology/test_query_service.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `Word` connect `Word` to `LemmaMorphClassAssigner`, `NounFormGenerator`, `test_lemma_morph_assignment.py`, `noun.py`, `MorphologyGenerateProgressCoordinator`, `WordPool`, `wright_audit.py`, `WeakVerbGenerator`, `GenerationRunState`, `session.py`, `GeneratorSession`, `sqlalchemy.py`, `StrongVerbGenerator`, `models/__init__.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `OENormalizer` connect `OENormalizer` to `NounFormGenerator`, `FormRow`, `ParadigmClassMapper`, `noun.py`, `markup.py`, `generation/query.py`, `Word`, `MorphologyDictionaryCleaner`, `wright_audit.py`, `WeakVerbGenerator`, `morphology/test_query_service.py`, `GenerationRunState`, `session.py`, `GeneratorSession`, `StrongVerbGenerator`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `Word` (e.g. with `test_generate_verb_parts_routes_direct_derivation_stack()` and `test_generate_verb_parts_routes_direct_weak_painsg1_stack()`) actually correct?**
  _`Word` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `GeneratorSession` (e.g. with `_run_prerequisite_stages()` and `full_session()`) actually correct?**
  _`GeneratorSession` has 25 INFERRED edges - model-reasoned connections that need verification._