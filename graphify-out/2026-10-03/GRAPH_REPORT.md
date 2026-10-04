# Graph Report - wyrdcraeft  (2026-10-03)

## Corpus Check
- 356 files · ~5,286,189 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5523 nodes · 11055 edges · 282 communities (237 shown, 36 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 709 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `277ab757`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BTSenseSegmenter
- models/dictionary.py
- Context
- test_morph_class_browse.py
- reference_snapshots.py
- normalize_morphology_title
- ParsedBTLine
- MorphologyBuildProfiler
- form_decode.py
- OENormalizer
- ._begin_stage
- test_generation_branches.py
- generation/query.py
- BTLineKind
- diacritic_disambiguate
- _WeakPainsg1DerivationContext
- audit_wright
- TestConfiguration
- _WeakPrincipalPartContext
- ._sqlite_connection
- test_browse_tui.py
- DictionaryBrowseQueryService
- test_morph_catalog_pos.py
- MorphologySetupStep
- test_markup.py
- tests/conftest.py
- Dictionary browse TUI must not touch SQLAlchemy Implementation Plan
- source.py
- WordPool
- AdjectiveFormGenerator
- File Structure
- ingest/pipeline.py
- RawBlock
- Word
- MorphologyCatalogLoader
- _WeakInfDerivationContext
- sound_changes.py
- etymology_display.py
- BTSqliteSink
- SenseMetadataClassifier
- ensure_parts_of_speech
- .ensure_ready
- ._get_preparsed_doc
- TEIExporter
- NormalizedTitleJoinIndex
- BTAttestationStripper
- FormRow
- diacritic_disambiguate.py
- wright-morphology-fixture.schema.json
- test_cli_diacritic_disambiguate.py
- TEISourceLoader
- markup.py
- EntryDetails
- build_runner.py
- Session: Morphology Wright Catalog — Phase 2 complete
- .segment_with_warnings
- properties
- properties
- create_engine
- .palatalize
- cli
- test_loaders.py
- test_cli_dictionary.py
- check_napoleon_gate.py
- Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅
- create_backup
- .settings_customise_sources
- test_wright_audit.py
- wright_audit.py
- .get_details
- morphology/test_query_service.py
- upgrade_canonical_db
- GeneratorSession
- 20260706_01_parts_of_speech_and_dictionary_pos.py
- test_build_pipeline.py
- VerbFormGenerator
- enum
- MorphologyDictionaryCleaner
- test_form_fk_resolver.py
- cli/settings.py
- print_error
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
- set_verb_paradigm
- test_wright_section_text.py
- .parse
- diacritic_add
- required
- features
- AdverbFormGenerator
- DictionaryBrowseStartupStage
- Configuration: Command Line Tool guide
- DatabaseStartupRuntime
- form_assembly.py
- test_cli_commands.py
- OESyllableBreaker
- DictionaryBrowseApp
- wyrdcraeft dictionary browse
- TestCLIGlobalOptions
- properties
- ADR 0009: Collapse morphology generation callback-soup into PoS generator classes
- Lexicon shrink: drop lexicon_entries/lexicon_forms, keep search_keys
- _WeakPsinsg2DerivationContext
- test_session_composition.py
- create_stderr_console
- read_jsonl_gz
- ._generate_word
- Implementation Slices
- fixture_prose.txt (Mark gospel OE prose fixture)
- GeneratorSession.load_all
- wyrdcraeft 1.1.0 release (2026-03-02)
- models/__init__.py
- TestSenseDisplayLabels
- Batched SQLite sink (25K rows) + bulk PRAGMAs fix for morphology build perf
- Phase 2 — Lemma Morph Class Assignment
- build_participle_adjective
- Morphology Wright catalog — Phase 1 session (2026-07-04)
- .apply
- File map
- infer_bt_pos_from_wordclasses
- .__init__
- DictionaryPosInferer
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
- 20260707_03_bt_source_blocks_and_rich_senses.py
- runtime.py
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
- generation/sinks.py
- enum
- test_index_pipeline.py
- 20260706_04_drop_forms_legacy_strings.py
- wyrdcraeft Context
- 20260630_01_initial_canonical_schema.py
- test_schema.py
- ._no_mixed_prose_and_verse
- 20260707_01_drop_search_keys.py
- _ParticipleOverride
- TestCLISettings
- test_lemma_morph_assignment.py
- File Structure
- 20260707_02_bt_senses_entry_order_index.py
- DictionaryBuildPipeline
- lexicon/conftest.py
- Phase A — Reference Tables and Dictionary POS FKs
- MorphologyCatalogQueryService
- Morphology Dictionary: Adjectives, Verbs, Participles, Numerals, Adverbs, Nouns
- create_dict31.pl (legacy Perl morphology generator)
- BTQueryService
- Python coding standards
- build_pipeline.py
- BT Structural Visibility Review
- wyrdcraeft
- browse_tui.py
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
- Dictionary CLI index gate and morph paths Implementation Plan
- Global Constraints
- Lexicon Browser BT V2 Adaptation Skeleton
- Orchestration: Wyrdcraeft Canonical DB Migration
- Morph Class Browse And Audit Design
- Phase B — Forms Foreign Keys (Legacy Strings Remain)
- 0002-normalized-canonical-schema.md
- Phase 2 — Wright § Text Ingest Report
- Two-gate subagent workflow: Gate A spec review, Gate B code review
- AGENTS.md
- Contributor Covenant 3.0
- isolated_morphology_app_data pytest fixture (no writes to real app-data DB)
- refactor_baseline.json Perl-parity guardrail for morphology generation
- Phase 1 — Reference Catalog Tables
- Unified dictionary build pipeline replacing morphology/dictionary/lexicon build triangle
- Morph Class Browse Surfacing + Wright Audit — Implementation Plan
- test_dict.txt (BT morphology dictionary test fixture)
- _RecordingSink
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
- split_prose_and_verse_runs
- Orchestrator Checkpoint
- DictionaryBuildStage
- MorphologyGenerationFacade
- Domain Docs
- normalized_title + lexicon browse — checkpoint 2026-07-03T12:15
- Mission: Machine Assistance For Old English Work
- Mission: Historical Linguistics for Old English Study
- resolve_dictionary_db_path
- Lemma-level morph class assignment (normalized_title, pos) -> morph_classes
- Issue tracker: Trello
- Subagent task breakdown
- Subagent task breakdown
- Subagent task breakdown
- normalized_title — checkpoint 2026-07-03T12:10
- BT Dictionary Structuring Workflow runbook
- Historical Linguistics for Old English Study Resources
- Old English c/g Palatalization Rule System
- test_normalized_title_join.py
- release.sh
- 0002-canonical-morphology-db-uses-startup-alembic-migrations.md
- triage-labels.md
- scripts/__init__.py
- quality/__init__.py
- machine-assistance/NOTES.md
- 0001-starting-point.md
- oe-grammar/NOTES.md
- teaching/README.md
- ipa-play.js
- THIRD_PARTY_NOTICES.md
- wyrdcraeft
- Verb generators leave `common.py`
- ParadigmAssigner
- progress.md
- .__init__
- TestConsoleQuietMode
- Task 8 Report
- .emit_form_data
- .__init__

## God Nodes (most connected - your core abstractions)
1. `Word` - 150 edges
2. `GeneratorSession` - 126 edges
3. `cli()` - 110 edges
4. `BTSenseSegmenter` - 80 edges
5. `WeakVerbGenerator` - 75 edges
6. `OENormalizer` - 65 edges
7. `BTLineParser` - 64 edges
8. `create_engine()` - 59 edges
9. `upgrade_canonical_db()` - 59 edges
10. `MorphologyCatalogLoader` - 55 edges

## Surprising Connections (you probably didn't know these)
- `Solomon and Saturn dialogue test fixture` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_dialogue.txt → doc/source/overview/format.rst
- `Beowulf opening lines test fixture (poetry)` --semantically_similar_to--> `Standard JSON Representation for Old English Texts (schema spec)`  [INFERRED] [semantically similar]
  tests/fixtures/fixture_poetry.txt → doc/source/overview/format.rst
- `test_strong_verb_generator_imports_from_strong_verb_forms()` --uses--> `StrongVerbGenerator`  [INFERRED]
  tests/morphology/test_verb_generator_modules.py → wyrdcraeft/services/morphology/generation/strong_verb_forms.py
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

## Communities (282 total, 36 thin omitted)

### Community 0 - "BTSenseSegmenter"
Cohesion: 0.04
Nodes (64): _entry_to_dict(), main(), _parse_and_segment(), Parse and segment one raw BT line., Convert a BTConsolidatedEntry to a serialisable dict., _entry_to_comparable(), _load_golden(), merger() (+56 more)

### Community 1 - "models/dictionary.py"
Cohesion: 0.03
Nodes (76): extractor(), fixture, parametrize, Tests for BTPosGenderExtractor using real oe_bt.txt prefix fragments., Shared extractor instance., Real BT prefix fragments resolve to expected POS and genders., Verb paradigm detection wins when both verb endings and adj appear., Abbad line with m: and m. returns masculine noun once. (+68 more)

### Community 2 - "Context"
Cohesion: 0.40
Nodes (4): Context, Click group that preserves the raw argv for help-aware gate decisions. Side…, Persist the raw argv before delegating to Click's normal parser. Args: ctx:…, _RootCLIGroup

### Community 3 - "test_morph_class_browse.py"
Cohesion: 0.29
Nodes (12): _bt_entry_id(), _insert_bt_entry(), Path, Tests for catalog-backed morph-class metadata in lexicon browse details., Resolve one ``bt_entries.id`` by ``norm_key`` for test assertions., Seed one catalog assignment row into a temporary lexicon test database., Insert one minimal ``bt_entries`` row into a temporary lexicon test database.…, _seed_catalog_assignment() (+4 more)

### Community 4 - "reference_snapshots.py"
Cohesion: 0.13
Nodes (26): build_session(), canonical_sort_rows(), canonicalize_form_rows(), form_rows_for_stage(), format_reference_snapshot_result(), full_flow_metadata(), full_flow_rows(), generate_reference_snapshots() (+18 more)

### Community 5 - "normalize_morphology_title"
Cohesion: 0.07
Nodes (32): mapper(), fixture, Tests for Wright catalog paradigm exemplar mapping., test_adj_paradigm_blind_maps_to_strong_a_o_stem(), test_noun_paradigm_guma_maps_to_weak_n_stem(), test_noun_paradigm_stan_maps_to_masculine_a_stem(), test_past_participle_title_maps_to_past_participle_class(), test_present_participle_title_maps_to_present_participle_class() (+24 more)

### Community 6 - "ParsedBTLine"
Cohesion: 0.04
Nodes (51): Unit tests for BTTargetResolver., TestBTTargetResolver, BTConsolidatedEntry, Canonical dictionary record after editorial merge for one ``(norm_key, pos)``.…, BTEditRecord, _plain(), BTSense, Phase 04 editorial merger for Bosworth-Toller dictionary entries. (+43 more)

### Community 7 - "MorphologyBuildProfiler"
Cohesion: 0.10
Nodes (17): test_build_profiler_disabled_emits_nothing(), test_build_profiler_emits_stage_and_sqlite_sections(), MorphologyBuildProfiler, TextIO, Wall-clock profiling helpers for morphology build runs., Finish wall-clock timing for one generation stage. Args: stage: Stage being…, Accumulate SQLite bulk-flush timing separately from generation stages. Args:…, Return a sink callback for SQLite flush timing, when profiling is enabled.… (+9 more)

### Community 8 - "form_decode.py"
Cohesion: 0.05
Nodes (84): MorphologyTableInputRow, Tests for morphology function-code decoding., test_build_adjective_sidebar_uses_payload_inflection(), test_build_adverb_sidebar_decodes_superlative_su_code(), test_build_morphology_table_fills_inflection_from_morph_class_label(), test_build_morphology_table_includes_surface_form_column(), test_build_morphology_table_sorts_adjectives_by_degree_inflection_and_case(), test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms() (+76 more)

### Community 9 - "OENormalizer"
Cohesion: 0.06
Nodes (51): Match, parametrize, test_canonicalize_inflection_code_reference(), test_eth2thorn_reference(), test_iumlaut_reference(), test_move_accents_reference(), test_normalize_bt_display_spelling_is_idempotent(), test_normalize_bt_display_spelling_reference() (+43 more)

### Community 10 - "._begin_stage"
Cohesion: 0.17
Nodes (11): AnyDictionaryBuildEvent, DictionaryBuildLogLevel, Infer missing dictionary POS values from stored morphology forms. Args:…, Mark one stage active across progress and typed event surfaces. Args: stage:…, Advance optional build progress for one stage update. Args: stage: Stage being…, Mark one stage complete across progress and log surfaces. Args: stage: Stage…, Emit one structured log event. Keyword Args: stage: Stage associated with the…, Send one typed build event to the configured sink. Args: event: Build event… (+3 more)

### Community 11 - "test_generation_branches.py"
Cohesion: 0.10
Nodes (44): _base_formhash(), _make_word(), MonkeyPatch, Replace the three weak derived-branch entry points with recorders., _record_weak_branches(), test_add_participle_to_adjectives_helper_appends_past_participle(), test_add_participle_to_adjectives_helper_appends_present_participle(), test_add_participle_to_adjectives_helper_skips_mismatched_prefix() (+36 more)

### Community 12 - "generation/query.py"
Cohesion: 0.09
Nodes (29): test_infer_bt_pos_filter_maps_unambiguous_noun(), test_infer_bt_pos_filter_returns_none_for_mixed_wordclasses(), MorphClassQueryMetadata, QueryFormRow, FK-backed morph-class metadata joined from catalog tables. Note: Linguistic…, Indexed morphology row enriched with normalized query keys., _build_morph_class_metadata(), dictionary_join_entry_to_dict() (+21 more)

### Community 13 - "BTLineKind"
Cohesion: 0.05
Nodes (39): _load_manifest(), Smoke tests for the stratified Bosworth-Toller corpus sample fixture., Ensure corpus fixture is present and within phase-02b size constraints., Parse every corpus line and require deterministic parse or explicit skip., test_corpus_sample_lines_parse_without_raising(), test_corpus_sample_manifest_and_line_count_bounds(), parametrize, Tests for Phase 02 Bosworth-Toller line parser. (+31 more)

### Community 14 - "diacritic_disambiguate"
Cohesion: 0.09
Nodes (24): _can_mark_completed(), diacritic_disambiguate(), _normalize_option_key_sequences(), _prompt_attested_form(), _prompt_form_annotation(), _prompt_modern_meaning(), _prompt_pos_code(), _prompt_text_input() (+16 more)

### Community 15 - "_WeakPainsg1DerivationContext"
Cohesion: 0.11
Nodes (13): Immutable context for weak ``PaInSg1``-derived emitter callbacks. Args:…, _WeakPainsg1DerivationContext, derive_papt_sound_changed_forms(), Return sequential ``PaPt`` sound-change derivations. Side Effects: None. Args:…, Emit one weak ``PaInSg1`` row for a selected vowel variant. Side Effects:…, Emit one manual row from a pre-bound weak ``PaInSg1`` context. Side Effects:…, Attach a past participle emitted from a weak ``PaInSg1`` branch. Side Effects:…, Emit one weak ``PsInSg2`` form row from a pre-bound derivation context. Side… (+5 more)

### Community 16 - "audit_wright"
Cohesion: 0.16
Nodes (22): audit_wright(), browse(), build(), clean_headwords(), _default_morphology_data_dir(), _default_source_path(), ingest_wright_text(), lookup() (+14 more)

### Community 17 - "TestConfiguration"
Cohesion: 0.08
Nodes (19): Exception, patch, Test that settings fields have proper descriptions., Test that model_config is properly configured., Test output format validation., Test valid output format validation., Test settings loading from environment variables. This test is a placeholder…, Test that environment variables override defaults. (+11 more)

### Community 18 - "_WeakPrincipalPartContext"
Cohesion: 0.07
Nodes (19): WeakStemParts, Immutable context for weak principal-part callback bindings. Args: formhash:…, _WeakPrincipalPartContext, Emit one generated form for a fixed stem context. Side Effects: Writes one row…, Dispatch weak branch derivations and participle side effects per principal…, Attach a present participle emitted from a weak principal-part row. Side…, Attach a past participle emitted from a weak principal-part row. Side Effects:…, Emit weak infinitive-derived rows from a principal-part context. Side Effects:… (+11 more)

### Community 19 - "._sqlite_connection"
Cohesion: 0.50
Nodes (3): Connection, Session, Unwrap SQLAlchemy's DB-API connection to the underlying SQLite driver. Args:…

### Community 20 - "test_browse_tui.py"
Cohesion: 0.08
Nodes (70): anyio, _bt_entry_id(), _collect_widget_ids(), _details_text(), empty_browse_db(), _insert_entry(), _insert_inflection_code(), lexicon_source_db() (+62 more)

### Community 21 - "DictionaryBrowseQueryService"
Cohesion: 0.09
Nodes (40): _bt_entry_id(), _insert_bt_sense(), _insert_entry(), _insert_inflection_code(), lexicon_source_db(), _next_entry_order(), _pos_id(), Connection (+32 more)

### Community 22 - "test_morph_catalog_pos.py"
Cohesion: 0.11
Nodes (31): parametrize, Tests for morphology catalog POS normalization helpers., test_catalog_pos_from_bt_pos_cli_aliases(), test_catalog_pos_from_bt_pos_join_values(), test_catalog_pos_from_bt_pos_raises_for_unmapped(), test_catalog_pos_from_wordclass(), test_catalog_pos_from_wordclass_unknown_returns_none(), test_pos_id_from_bt_pos() (+23 more)

### Community 23 - "MorphologySetupStep"
Cohesion: 0.12
Nodes (13): test_progress_coordinator_omits_empty_wright_and_throttles_lemma(), MorphologySetupStep, MorphologyStageSnapshot, StrEnum, Stable setup-step labels for pre-generation morphology work. Note: Cross-PoS…, Start Rich progress rendering and register stable stage tasks., Advance setup progress for one completed startup step. Args: step: Setup step…, Initialize one stage banner with its current total. Args: stage: Stage being… (+5 more)

### Community 24 - "test_markup.py"
Cohesion: 0.07
Nodes (41): Path, test_build_index_from_bt_extracts_and_dedupes(), Path, C before i/ī in any position palatalizes (Rule C)., Blocklist keeps c velar for i-mutation exceptions (cyning, cemban, cynn)., gēs ('geese') is a g-exception (ē from i-mutation of ō); g stays velar., Force-palatalize list gives final ċ for hwelc/hwilc, swelc, ǣlc, þylc., Cyning (c + y from u) remains non-palatalized; blocklist and only-back. (+33 more)

### Community 25 - "tests/conftest.py"
Cohesion: 0.15
Nodes (19): cli_context(), isolated_morphology_app_data(), isolated_morphology_index_db(), lexicon_source_db(), mock_console(), mock_settings(), fixture, Path (+11 more)

### Community 26 - "Dictionary browse TUI must not touch SQLAlchemy Implementation Plan"
Cohesion: 0.18
Nodes (9): Considered Options, Dictionary browse TUI must not touch SQLAlchemy, Dictionary browse TUI must not touch SQLAlchemy Implementation Plan, File map, Global Constraints, Review Focus, Spec coverage (self-review), Task 1: Browse readiness on the query service (+1 more)

### Community 27 - "source.py"
Cohesion: 0.19
Nodes (15): _mark_diacritics_derived_path(), argument, command, Context, group, option, pass_context, Path (+7 more)

### Community 28 - "WordPool"
Cohesion: 0.04
Nodes (92): test_progress_coordinator_stage_totals(), ManualForm, Morphology-related Pydantic models for the Old English morphology generator., Manual form model for ``manual_forms.txt`` ingest rows. Legacy string fields…, FormWriter, Shared protocols for morphology refactor boundaries., Minimal writer protocol used by morphology emitters., _emit_superlative_strong_forms() (+84 more)

### Community 29 - "AdjectiveFormGenerator"
Cohesion: 0.05
Nodes (39): _adj_print(), AdjectiveFormGenerator, _build_adjective_formhash(), _build_comparative_title_array(), _build_superlative_title_array(), _build_weak_title_array(), _dedupe_preserve_first(), _emit_weak_degree_forms() (+31 more)

### Community 30 - "File Structure"
Cohesion: 0.11
Nodes (18): Addendum: Tasks 11-14 (added after final whole-branch review), File Structure, Global Constraints, Morphology Generation Class Refactor Implementation Plan, Task 10: Delete the now-empty `generators/` directory, Task 11: Build paradigm-dispatch tables for `NounFormGenerator` and `AdjectiveFormGenerator`, Task 12: Collapse `StrongVerbGenerator`'s callback threading into direct method calls, Task 13: Collapse `WeakVerbGenerator`'s callback threading into direct method calls (+10 more)

### Community 31 - "ingest/pipeline.py"
Cohesion: 0.13
Nodes (16): parametrize, Test that deterministic ingestion of text files matches the golden JSON…, test_deterministic_ingestion_regression(), PreParsedDocument, ProvisionalSection, A provisional section is a section that has been parsed from the raw blocks,…, A pre-parsed document is a document that has been parsed from the raw blocks,…, DocumentIngestor (+8 more)

### Community 32 - "RawBlock"
Cohesion: 0.07
Nodes (35): dialogue_text(), prose_text(), fixture, patch, Unmarked verse gets 1-based line numbers within the section., _t(), test_canonical_converter_prose(), test_canonical_converter_verse() (+27 more)

### Community 33 - "Word"
Cohesion: 0.03
Nodes (84): Lexical entry schema carrying POS flags and paradigm state for one lemma., Word, _append_short_syllable_front_vowel_heuristic(), _append_suffix_heuristics(), _append_terminal_a_heuristic(), _append_terminal_e_heuristic(), _apply_final_fallback(), _apply_noun_heuristics() (+76 more)

### Community 34 - "MorphologyCatalogLoader"
Cohesion: 0.04
Nodes (75): DeclarativeBase, catalog_db(), fixture, Path, Build a small morphology slice and verify normalized FK columns on forms., test_catalog_loader_ensure_seeded_refresh(), test_catalog_loader_ensure_seeded_skips_when_populated(), test_catalog_loader_is_idempotent() (+67 more)

### Community 35 - "_WeakInfDerivationContext"
Cohesion: 0.17
Nodes (9): Immutable context for weak infinitive-derived emitter callbacks. Args:…, _WeakInfDerivationContext, Add a participle to adjectives. Side Effects: Adds one adjective-row candidate…, Attach a present participle emitted from infinitive-derived weak rows. Side…, Emit weak infinitive-derived branches for one principal-part context. Side…, Emit weak-verb forms derived from infinitives for the general class2 branch.…, Emit weak-verb forms for one variant of the class2-special infinitive branch.…, Emit weak infinitive-derived branches according to ``class2`` routing. Side… (+1 more)

### Community 36 - "sound_changes.py"
Cohesion: 0.08
Nodes (33): SoundChangeSequenceEmitter, SoundManualContextEmitter, SoundManualEmitter, SoundSourceContextEmitter, SoundSourceFormEmitter, test_derive_sound_changed_forms_psinsg2_gst_chain(), test_derive_sound_changed_forms_psinsg2_ngst_chain(), test_derive_sound_changed_forms_psinsg3_td_th_chain() (+25 more)

### Community 37 - "etymology_display.py"
Cohesion: 0.07
Nodes (48): Tests for etymology parsing and browse table formatting., test_format_etymology_display_renders_table_headers(), test_misplaced_attestation_is_flagged(), test_mixed_attestation_and_cognates_split(), test_parse_cognate_chain_with_citation(), test_parse_colon_separated_lang_chain(), test_parse_multiple_german_cognates(), test_parse_norse_words_with_latin_tail() (+40 more)

### Community 38 - "BTSqliteSink"
Cohesion: 0.04
Nodes (75): _index_with_attach(), Path, Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite., Seed the canonical ``forms`` table via the real SQLAlchemy sink., _seed_forms_table(), test_attach_missing_db_fails_for_canonical_only_mode(), test_attach_preserves_forms_and_writes_bt_entries(), test_attach_rerun_is_idempotent_and_preserves_forms() (+67 more)

### Community 39 - "SenseMetadataClassifier"
Cohesion: 0.06
Nodes (27): Unit tests for sense-prefix metadata classification., TestSenseMetadataClassifier, _has_substantive_gloss(), _looks_like_gloss_start(), _normalize_case(), _normalize_gender(), _normalize_modifier(), Normalize one modifier abbreviation token. Args: token: Raw modifier token… (+19 more)

### Community 40 - "ensure_parts_of_speech"
Cohesion: 0.11
Nodes (31): _load_fixture_rows(), Connection, Path, Tests for normalized POS and inflection-code seed fixtures., Read one JSON fixture file used by the POS seed tests., Return the current row count for one reference table., _row_count(), test_inflection_seed_covers_observed_snapshot_function_codes() (+23 more)

### Community 41 - ".ensure_ready"
Cohesion: 0.08
Nodes (23): Config, build_alembic_config(), create_session_factory(), _format_backup_prompt_text(), Path, Session, sessionmaker, Store the backup path and explicit rebuild recipe for CLI reporting. Keyword… (+15 more)

### Community 42 - "._get_preparsed_doc"
Cohesion: 0.16
Nodes (15): ProgressCallback, BaseDocumentIngestor, HeuristicDocumentIngestor, ingest_from_tei(), Path, Base orchestrator for document ingestion., Abstract ingest method to be overridden by subclasses. Args: source_path: Path…, Load, filter, and pre-parse a local text document. Args: source_path: Path to… (+7 more)

### Community 43 - "TEIExporter"
Cohesion: 0.19
Nodes (13): test_tei_exporter_interface(), Any, Create the publication statement. Args: doc: The document to export. parent:…, Create the source description. Args: doc: The document to export. parent: The…, Emit a section and its content recursively. Args: sec: The section to export.…, Apply common metadata attributes to a node. Args: node: The node to apply the…, Emit prose paragraphs, handling speakers. Args: paragraphs: The paragraphs to…, Exporter for TEI XML format using delb for XML manipulation. (+5 more)

### Community 44 - "NormalizedTitleJoinIndex"
Cohesion: 0.08
Nodes (27): Relink morphology ``forms.entry_id`` values after dictionary rebuilds., _fetch_rows(), load_normalized_title_join_index(), Connection, Shared loader for normalized-title dictionary join indexes., Fetch three-column join rows from SQLAlchemy or SQLite connections. Args:…, Build a dictionary join index from canonical ``bt_entries`` and variants. Args:…, NormalizedTitleJoinIndex (+19 more)

### Community 45 - "BTAttestationStripper"
Cohesion: 0.04
Nodes (47): fixture, parametrize, Tests for Phase 03 BTAttestationStripper., ``_is_citation_span`` returns True for grammar/editorial markers and citations., ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes., ``_strip_editorial_directive`` removes leading supplement editorial verbs., Unit tests for BTAttestationStripper.strip., ``:--`` is the canonical attestation separator. (+39 more)

### Community 46 - "FormRow"
Cohesion: 0.07
Nodes (22): FormRow, Canonical emitted morphology row used by sinks and query services. Legacy…, _build_form_rows_from_form_data(), FormSink, Connection, Protocol, Materialize one finalized output row from legacy ``form_data`` fields. Note:…, Emit parity rows from legacy ``form_data`` and update the run's output counter.… (+14 more)

### Community 47 - "diacritic_disambiguate.py"
Cohesion: 0.14
Nodes (27): Layout, test_fetch_bt_search_entries_uses_search_endpoint(), test_filter_bt_entries_by_normalized_form_empty_list_returns_empty(), test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others(), test_filter_bt_entries_by_normalized_form_no_matches_returns_empty(), test_filter_bt_entries_by_normalized_form_preserves_order(), test_merge_bt_entries_deduplicates_and_reindexes(), test_normalize_bt_spelling_converts_acute_to_macron() (+19 more)

### Community 48 - "wright-morphology-fixture.schema.json"
Cohesion: 0.05
Nodes (39): 1.0, morph_classes, Old English, schema_version, sources, wright-modern-morphology, additionalProperties, description (+31 more)

### Community 49 - "test_cli_diacritic_disambiguate.py"
Cohesion: 0.10
Nodes (39): _minimal_index_payload(), _mock_bt_lookup(), fixture, Path, Minimal macron index payload for diacritic add/delete tests., test_diacritic_add_fails_when_exists_without_force(), test_diacritic_add_fails_when_key_in_ambiguous_even_with_force(), test_diacritic_add_force_overwrites() (+31 more)

### Community 50 - "TEISourceLoader"
Cohesion: 0.13
Nodes (15): Document, TeiReader, Test importing Beowulf from TEI XML., test_tei_import_beowulf(), Extract metadata from TEI header. Args: tei_reader: The TEI reader to extract…, Parse the TEI body. Args: doc: The document to parse the body from. ns: The…, Parse a <div> into a Section model. Args: section_node: The node to parse the…, Fill paragraphs, lines, and subsections for a section. Args: sec: The section… (+7 more)

### Community 51 - "markup.py"
Cohesion: 0.10
Nodes (30): patch, With only input given, paths default to stem + infix + extension., test_source_mark_diacritics_default_paths(), test_source_mark_diacritics_writes_text_and_ambiguities(), test_source_mark_diacritics_writes_unknowns_file(), AmbiguityOption, DiacriticRestorationResult, MacronAmbiguity (+22 more)

### Community 52 - "EntryDetails"
Cohesion: 0.07
Nodes (31): test_format_entry_details_omits_plain_wright_line_for_selectable_sections(), test_format_entry_details_shows_unclassified_for_missing_assignment(), test_format_entry_details_shows_unclassified_for_unmappable_pos(), EntryDetails, Resolve catalog-backed morph-class metadata for one dictionary entry. Keyword…, Full details payload for one dictionary-backed browse entry. Note:…, Build the browse sentinel used when no deterministic assignment exists.…, _unclassified_morph_class_summary() (+23 more)

### Community 53 - "build_runner.py"
Cohesion: 0.10
Nodes (36): Path, Morphology input path defaults live on the generation runner., test_packaged_default_morphology_data_dir_exists(), test_resolve_morphology_input_paths_keeps_overrides(), test_resolve_morphology_input_paths_uses_data_dir_defaults(), test_validate_morphology_input_paths_raises_for_missing_file(), generate_reference_snapshots_command(), Generate Python-reference snapshot fixtures via CLI. Note: Snapshot baselines… (+28 more)

### Community 54 - "Session: Morphology Wright Catalog — Phase 2 complete"
Cohesion: 0.15
Nodes (7): Architecture, Deliverables, Known limitations (deferred), Next, Session: Morphology Wright Catalog — Phase 2 complete, Summary, Validation

### Community 55 - ".segment_with_warnings"
Cohesion: 0.19
Nodes (7): BTSense, Return an ordered list of :class:`~wyrdcraeft.models.dictionary.BTSense` for…, Segment one body and return senses plus segmentation diagnostics. Args: body:…, Segment a body with no explicit sense labels into zero or one senses. Args:…, Build one :class:`~wyrdcraeft.models.dictionary.BTSense` from a fragment. Args:…, Classify prefix metadata and extract one sense gloss from *segment_body*. Args:…, Segment one body for ``ParsedBTLine`` construction. Args: body: Raw HTML body…

### Community 56 - "properties"
Cohesion: 0.06
Nodes (34): type, type, type, properties, type, type, type, type (+26 more)

### Community 57 - "properties"
Cohesion: 0.06
Nodes (34): description, minLength, type, $ref, default, description, enum, type (+26 more)

### Community 58 - "create_engine"
Cohesion: 0.15
Nodes (27): _fetch_form_entry_id(), _insert_bt_entry(), _insert_bt_variant(), _insert_form(), _pos_id(), Connection, fixture, Path (+19 more)

### Community 59 - ".palatalize"
Cohesion: 0.17
Nodes (7): _possible_pre_iumlaut_sources(), Palatalize ``g`` in a lexical token. Args: word: Token to palatalize. Returns:…, Return possible pre-i-mutation (reconstructed) sources for an OE vowel. Used to…, Test if ``text[index:]`` starts with a front-vowel context. Args: text:…, Return whether the character before position i is i/ī or i/ī + n. Used for Rule…, Return True if the vowel unambiguously derives only from back vowels. Used to…, Palatalize ``c`` in a lexical token per rules A-D and i-mutation caveat. Rule…

### Community 60 - "cli"
Cohesion: 0.12
Nodes (22): Test the convert command with a missing source file., Test the convert command without LLM (heuristic mode)., test_convert_command_missing_source(), test_convert_command_no_llm(), test_convert_rejects_http_source(), test_convert_rejects_use_llm_flag(), CLI tests for remaining morphology commands after build moved to dictionary., test_morphology_build_command_moved_to_dictionary() (+14 more)

### Community 61 - "test_loaders.py"
Cohesion: 0.13
Nodes (19): fixture, source_loader(), test_load_from_file_rejects_pdf(), test_load_from_file_text(), test_load_from_file_unsupported(), test_source_loader_load_file(), test_source_loader_rejects_http_url(), test_tei_source_loader_load_tei() (+11 more)

### Community 62 - "test_cli_dictionary.py"
Cohesion: 0.12
Nodes (33): _build_unified_source_db(), _fetch_entry_id(), _fetch_form_entry_id(), _insert_form(), _morphology_data_dir(), _pos_id(), Connection, Path (+25 more)

### Community 63 - "check_napoleon_gate.py"
Cohesion: 0.08
Nodes (44): AST, AsyncFunctionDef, ClassDef, FunctionDef, Module, cyclomatic(), report(), _check_file() (+36 more)

### Community 64 - "Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅"
Cohesion: 0.07
Nodes (29): Background, Explicit non-goals, File Map, Lexicon rebuild (Slice 1), Lexicon SQLAlchemy Rebuild + Normalized Title Join Index Implementation Plan, Locked Decisions, Normalized title join index (Slice 2), References (+21 more)

### Community 65 - "create_backup"
Cohesion: 0.09
Nodes (29): Path, test_backup_state_round_trip_uses_sidecar_beside_canonical_db(), test_create_backup_copies_database_and_keeps_latest_by_default(), test_restore_backup_overwrites_database_contents(), create_backup(), list_backups(), _prune_old_backups(), datetime (+21 more)

### Community 66 - ".settings_customise_sources"
Cohesion: 0.18
Nodes (7): BaseSettings, PydanticBaseSettingsSource, Path, Load settings from file with cascading configuration. Args: config_file:…, Get list of configuration file paths that were loaded. Use this for debugging.…, Resolve the canonical SQLite database path for these settings. Returns:…, Return the default local settings file path used by the CLI. Returns: The…

### Community 67 - "test_wright_audit.py"
Cohesion: 0.16
Nodes (24): _dictionary_line(), _make_audit_source_dir(), _manual_form_line(), _para_vb_line(), Path, Tests for legacy Wright source auditing. Phase D source contract: The audit…, Build one ``manual_forms.txt`` fixture line with the expected 16 columns., Build one ``para_vb.txt`` fixture line for malformed-token scanning. (+16 more)

### Community 68 - "wright_audit.py"
Cohesion: 0.05
Nodes (52): _append_sample_block(), _AssignedMorphClass, BlankLegacyButClassifiedIssue, _catalog_pos_from_word(), ContradictionIssue, _display_legacy_wright(), _format_blank_but_classified_issue(), _format_contradiction_issue() (+44 more)

### Community 69 - ".get_details"
Cohesion: 0.09
Nodes (21): test_filter_display_variants_drops_genitive_endings(), _append_unique(), EntrySense, _extract_gender_person_number(), filter_display_variants(), _json_string_list(), _ordered_distinct(), Any (+13 more)

### Community 70 - "morphology/test_query_service.py"
Cohesion: 0.17
Nodes (28): _form_row(), _index_dictionary(), _insert_bt_entry(), _insert_bt_variant(), Connection, Path, Ambiguous dictionary joins must persist NULL ``entry_id`` on inserted forms., _seed_abbod_noun_form() (+20 more)

### Community 71 - "upgrade_canonical_db"
Cohesion: 0.05
Nodes (72): corpus_index_db(), _index_fixture(), fixture, Path, Unit and integration tests for BTQueryService., sample_index_db(), _seed_forms_table(), test_bt_query_service_constructs_on_empty_migrated_db() (+64 more)

### Community 72 - "GeneratorSession"
Cohesion: 0.05
Nodes (51): setter, _make_verb_paradigm(), _make_word(), test_set_adj_paradigm_stem_propagation(), test_set_adj_paradigm_wright_rule_425(), test_set_noun_paradigm_advanced_stem_propagation(), test_set_noun_paradigm_final_fallback_neuter_long_stem(), test_set_noun_paradigm_final_fallback_neuter_short_stem() (+43 more)

### Community 73 - "20260706_01_parts_of_speech_and_dictionary_pos.py"
Cohesion: 0.16
Nodes (23): _assert_no_null_pos_ids(), _assert_no_null_text_pos(), downgrade(), _downgrade_bt_entries(), _downgrade_lemma_morph_classes(), _downgrade_morph_classes(), Connection, Replace legacy BT text POS and headword columns with normalized fields. Args:… (+15 more)

### Community 74 - "test_build_pipeline.py"
Cohesion: 0.23
Nodes (20): build_pipeline_db(), _fetch_entry_id(), _fetch_entry_pos(), _fetch_form_entry_id(), _insert_form(), _pos_id(), Connection, fixture (+12 more)

### Community 75 - "VerbFormGenerator"
Cohesion: 0.08
Nodes (36): _make_part(), _make_variant(), _make_verb_paradigm(), test_process_paradigm_routes_variant_payload_from_flow(), test_process_part_routes_strong_generation_from_flow(), test_process_part_routes_weak_generation_from_flow(), ADR 0011: verb engines live in per-class modules; ``common.py`` is gone., test_strong_verb_generator_imports_from_strong_verb_forms() (+28 more)

### Community 76 - "enum"
Cohesion: 0.08
Nodes (26): common, comparative, dual, feminine, first, masculine, neuter, plural (+18 more)

### Community 77 - "MorphologyDictionaryCleaner"
Cohesion: 0.06
Nodes (39): parametrize, Tests for morphology dictionary TSV cleanup., test_clean_dictionary_fixes_bt_diphthongs_in_col2(), test_clean_dictionary_lowercases_col2_dedupes_and_backups(), test_clean_dictionary_raises_when_source_missing(), test_should_lowercase_col2_only_all_upper_letters(), patch, Tests for the main module. (+31 more)

### Community 78 - "test_form_fk_resolver.py"
Cohesion: 0.20
Nodes (23): _insert_bt_entry(), _insert_bt_variant(), _insert_lemma_assignment(), Connection, fixture, Path, Tests for morphology form foreign-key resolution., resolver_db() (+15 more)

### Community 79 - "cli/settings.py"
Cohesion: 0.29
Nodes (10): create_settings(), command, Context, group, pass_context, Settings-related commands., Settings-related commands., Create a new settings file. (+2 more)

### Community 80 - "print_error"
Cohesion: 0.05
Nodes (34): Tests for CLI utilities., Test success panel has correct styling., Test info printing functions., Test basic info printing., Test info panel has correct styling., Test console objects., Test that console objects are properly initialized., Test progress creation. (+26 more)

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

### Community 91 - "set_verb_paradigm"
Cohesion: 0.10
Nodes (27): Resolve the Wright 425 adjective paradigm using vowel-sensitive matching., _wright_rule_425(), Morphology paradigm assigners., _get_r_stem_paradigm(), Resolve opt-in r-stem paradigm for a word. Classification uses: - exact Wright…, Check whether ``wright`` contains the exact semicolon-delimited token. Args:…, _wright_has_token(), _assign_verb_by_advanced_diacritics() (+19 more)

### Community 92 - "test_wright_section_text.py"
Cohesion: 0.08
Nodes (33): catalog_db(), fixture, Path, Tests for Wright section markdown parsing and catalog text ingest., test_ingest_result_counts_and_warnings(), test_ingester_force_overwrites_existing_text(), test_ingester_is_idempotent_without_force(), test_ingester_updates_null_sections() (+25 more)

### Community 93 - ".parse"
Cohesion: 0.07
Nodes (19): Initialize parser collaborators for split and POS extraction. Args: splitter:…, Parse one source line into ``RawBTLine`` plus phase-02 metadata. Args:…, Extract the POS prefix fragment immediately after the first headword. Args:…, Extract alternate headword spellings from the pre-POS plain-text prefix. Args:…, Apply display spelling normalization to variants with de-duplication. Args:…, Extract substitute target text from ``for X in Dict`` patterns. Args: body:…, Extract reference fragments listed after ``Dele`` markers. Args: body: Main…, Extract trailing bracket etymology blocks from the line body. Args: body: Main… (+11 more)

### Community 94 - "diacritic_add"
Cohesion: 0.27
Nodes (12): diacritic_add(), diacritic_delete(), _load_macron_index_payload(), argument, command, option, Path, Add a normalized/macron-ed pair to the unique list of the macron index. The… (+4 more)

### Community 95 - "required"
Cohesion: 0.11
Nodes (19): aliases, canonical_name, features, id, is_assignable, mapping_rationale, modern_class, paradigmatic_words (+11 more)

### Community 96 - "features"
Cohesion: 0.11
Nodes (19): citation_apa, retrieved_date, source_key, url, $defs, features, recognitionHints, source (+11 more)

### Community 97 - "AdverbFormGenerator"
Cohesion: 0.25
Nodes (6): AdverbFormGenerator, FormOutput, Generates adverb surface forms (base, comparative, superlative) for one…, Bind an adverb form generator to one word pool, run state, and output sink.…, Generate adverb forms and comparative/superlative derivatives. Side Effects:…, Generate adverb forms and comparative/superlative derivatives for a single…

### Community 98 - "DictionaryBrowseStartupStage"
Cohesion: 0.29
Nodes (7): Progress, DictionaryBrowseStartupStage, StrEnum, Browse startup progress helpers for dictionary browse workflow., Stable stage labels for dictionary browse startup progress., Run browse startup work while showing stable stderr progress stages. Args:…, run_browse_startup_progress()

### Community 99 - "Configuration: Command Line Tool guide"
Cohesion: 0.15
Nodes (18): wyrdcraeft settings CLI command doc, wyrdcraeft source convert CLI command doc, Configuration: Command Line Tool guide, wyrdcraeft FAQ, Standard JSON Representation for Old English Texts (schema spec), Installation guide, Quickstart guide, Using the Command Line Interface guide (+10 more)

### Community 100 - "DatabaseStartupRuntime"
Cohesion: 0.27
Nodes (20): _create_pre_alembic_forms_db(), _make_settings(), parametrize, Path, test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(), test_fresh_missing_db_bootstraps_with_alembic_path(), test_interactive_blank_prompt_keeps_backup_without_retry(), test_interactive_prompt_matches_locked_wording_and_deletes_backup() (+12 more)

### Community 101 - "form_assembly.py"
Cohesion: 0.29
Nodes (7): assemble_form_parts(), materialize_form(), perl_interpolate(), Form assembly helpers for parity-preserving morphology generation., Assemble a raw ``formParts`` payload using legacy Perl field ordering. Side…, Coerce a scalar to a Perl-like interpolation string. Side Effects: None. Args:…, Normalize assembled form parts into the emitted ``form`` and ``formParts``.…

### Community 102 - "test_cli_commands.py"
Cohesion: 0.10
Nodes (15): Tests for CLI commands with low coverage., Test CLI error handling., Test CLI without arguments shows help., Test invalid command shows error., Test that the OCR command group has been removed from the CLI., Test the version command., Test that Settings has no ocr_ fields., Test the version command displays version information. (+7 more)

### Community 103 - "OESyllableBreaker"
Cohesion: 0.16
Nodes (9): Syllable model for Old English syllable breaking., A syllable is a unit of speech that consists of an onset, nucleus, and coda., Syllable, OESyllableBreaker, Split consonant cluster between syllables using a conservative max-onset…, Insert dots before known suffixes to guide syllabification., Syllabify an Old English word conservatively., Break an Old English word into syllables. (+1 more)

### Community 104 - "DictionaryBrowseApp"
Cohesion: 0.05
Nodes (34): Changed, ComposeResult, ListItem, Pressed, Selected, Static, Submitted, DictionaryBrowseApp (+26 more)

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
Cohesion: 0.32
Nodes (5): Immutable context for weak ``PsInSg2``-derived emitter callbacks. Args:…, _WeakPsinsg2DerivationContext, Emit weak ``PsInSg2``-derived branches for one principal-part context. Side…, Emit weak-verb forms derived from the ``PsInSg2`` principal part. Side Effects:…, Emit weak ``PsInSg2``-derived forms for one principal-part stem context. Side…

### Community 111 - "test_session_composition.py"
Cohesion: 0.47
Nodes (5): _make_word(), Regression tests for the GeneratorSession -> WordPool/GenerationRunState split.…, test_session_composes_word_pool_and_run_state(), test_word_pool_append_participle(), test_word_pool_categorize_matches_load_all_categorization()

### Community 112 - "create_stderr_console"
Cohesion: 0.33
Nodes (5): create_stderr_console(), Console, Create one Rich console bound to current stderr stream. Returns: Console…, Console, Initialize one coordinator instance for one generation run. Keyword Args:…

### Community 113 - "read_jsonl_gz"
Cohesion: 0.07
Nodes (54): FixtureRequest, morphology, morphology_full, main(), _mypy_baseline(), _runtime_baseline_ms(), _sha256_rows(), _stage_rows() (+46 more)

### Community 114 - "._generate_word"
Cohesion: 0.33
Nodes (4): Generate numeral forms for every word where ``numeral == 1``. Side Effects:…, Generate numeral forms for a single word. Args: word: The word to generate…, Remove trailing [ea] from stem. Note: This is the same as Perl s/[ea]$//. Args:…, _stem_no_ea()

### Community 115 - "Implementation Slices"
Cohesion: 0.33
Nodes (6): Implementation Slices, Slice 1: consume visibility review, Slice 2: models and schema, Slice 3: parser and merge, Slice 4: query and CLI, Slice 5: rebuild and verify

### Community 117 - "GeneratorSession.load_all"
Cohesion: 0.17
Nodes (12): GeneratorSession (services.morphology), wyrdcraeft.models.morphology, GeneratorSession, LemmaMorphClassAssigner, MorphologyCatalogLoader, Morphology generation flow (concept), GeneratorSession.load_all(), LemmaMorphClassAssigner.assign_all() (+4 more)

### Community 118 - "wyrdcraeft 1.1.0 release (2026-03-02)"
Cohesion: 0.22
Nodes (13): GPalatalizer, MacronApplicator, wyrdcraeft.models.macron_index, wyrdcraeft 1.0.0 initial release (2026-03-01), wyrdcraeft 1.1.0 release (2026-03-02), wyrdcraeft source mark-diacritics, Diacritic restoration runtime processing flow, wyrdcraeft diacritic add (+5 more)

### Community 119 - "models/__init__.py"
Cohesion: 0.17
Nodes (25): fixture, sample_doc(), test_tei_export_attributes(), test_tei_export_basic(), test_tei_export_structure(), test_tei_roundtrip_minimal_prose(), test_tei_roundtrip_minimal_verse_dialogue(), GeneratedForm (+17 more)

### Community 120 - "TestSenseDisplayLabels"
Cohesion: 0.22
Nodes (5): Arabic display labels for canonical sense paths., TestSenseDisplayLabels, format_sense_display_label(), User-facing sense label derived from ``sense_path``. Roman source labels are…, Convert canonical ``sense_path`` to Arabic display text. Top-level paths stay…

### Community 122 - "Phase 2 — Lemma Morph Class Assignment"
Cohesion: 0.20
Nodes (10): Cleanup (optional same PR or follow-up), Phase 2 — Gate A: Spec review, Phase 2 — Gate B: Code review, Phase 2 — Lemma Morph Class Assignment, Phase 2 validation, Task 1: Schema + migration, Task 2: POS normalization helper, Task 3: Paradigm exemplar registry (+2 more)

### Community 123 - "build_participle_adjective"
Cohesion: 0.40
Nodes (6): build_participle_adjective(), derive_participle_stem(), Normalize form fragments by removing legacy separators and null markers. Args:…, Derive participle stem text from ``form_parts`` using legacy prefix logic.…, Build one adjective-form ``Word`` record from a generated participle form.…, _sanitize_form_text()

### Community 124 - "Morphology Wright catalog — Phase 1 session (2026-07-04)"
Cohesion: 0.12
Nodes (17): 1. Circular import on full morphology test collection, 2. Untracked plan directory, 3. Package data, Branch and commits, Build integration, Commits this session (Phase 1 Tasks 1–4), Goal (locked design), Key files (+9 more)

### Community 125 - ".apply"
Cohesion: 0.33
Nodes (5): TContext_contra, TWord_contra, Ordered classification rule for paradigm assignment., Return matched paradigm labels for ``word`` in ``context``. Note: Paradigm…, Rule

### Community 126 - "File map"
Cohesion: 0.17
Nodes (12): File map, Global Constraints, LLM and unstructured leave `source convert` Implementation Plan, Self-review (spec coverage), Task 1: Local `.txt` loader returns `RawBlock`s, Task 2: Strip LLM from convert CLI and `DocumentIngestor`, Task 3: Delete LLM ingest types, extractors, prompts, Task 4: Delete dictionary LLM repair (+4 more)

### Community 127 - "infer_bt_pos_from_wordclasses"
Cohesion: 0.40
Nodes (4): test_infer_bt_pos_from_wordclasses_requires_single_mapping(), infer_bt_pos_from_wordclasses(), Shared morphology wordclass to dictionary POS mapping helpers., Map distinct morphology wordclasses to one dictionary POS when unambiguous.…

### Community 128 - ".__init__"
Cohesion: 0.40
Nodes (3): datetime, Capture one startup runtime configuration and its collaborators. Keyword Args:…, Store the startup migration failure details for CLI reporting. Args: message:…

### Community 129 - "DictionaryPosInferer"
Cohesion: 0.23
Nodes (10): PosInferenceCancelCheck, PosInferenceProgress, PosInferenceWarningSink, DictionaryPosInferer, Connection, Attempt one inferred POS update, skipping duplicate and homograph rows. Args:…, Unwrap one SQLAlchemy connection to the underlying SQLite driver. Args:…, Fill missing dictionary POS values from unambiguous morphology wordclasses.… (+2 more)

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
Cohesion: 0.50
Nodes (3): parametrize, Prompt regression and schema validation tests. These tests stay runnable…, test_expected_json_is_schema_valid()

### Community 148 - "20260704_02_lemma_morph_classes.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add recognition hints to morph classes and create lemma assignment table. Side…, Drop lemma assignment table and recognition hints column. Side Effects: Removes…, upgrade()

### Community 149 - "20260707_03_bt_source_blocks_and_rich_senses.py"
Cohesion: 0.40
Nodes (4): downgrade(), Restore homograph uniqueness and remove rich sense metadata columns. Side…, Drop homograph uniqueness and add source-block sense metadata columns. Side…, upgrade()

### Community 150 - "runtime.py"
Cohesion: 0.06
Nodes (41): Unit tests for configuration settings. Tests the new OpenAI and summary…, test_settings_has_no_llm_fields(), Path, test_legacy_bootstrap_failure_restores_cleanly_and_raises_typed_error(), test_legacy_morphology_db_is_backed_up_then_requires_rebuild(), _configure_logging(), _prompt_backup_cleanup(), command (+33 more)

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
Nodes (35): Immutable context shared by the strong principal-part emission methods. Args:…, Immutable context shared by the strong infinitive-derived emission methods.…, _StrongInfDerivationContext, _StrongPrincipalPartContext, FormOutput, Emit one normalized form record to ``output``. Note: Form realization follows…, FormOutput, Emit one source row and its sound-change derivatives for a stem context. Side… (+27 more)

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

### Community 162 - "generation/sinks.py"
Cohesion: 0.10
Nodes (27): Namespace, _build_output_sink(), main(), _parse_args(), Run cProfile against the morphology adjective generation stage., Profile ``MorphologyGenerationFacade.generate_adjectives`` and print…, Build the output sink used while profiling adjective generation. Keyword Args:…, Run manual and verb stages needed before adjective generation. Args: session:… (+19 more)

### Community 163 - "enum"
Cohesion: 0.40
Nodes (5): past, present, enum, type, participle

### Community 164 - "test_index_pipeline.py"
Cohesion: 0.07
Nodes (53): CorpusSampleResult, DictionaryCorpusSampler, main(), Path, Index source lines by lookup key while preserving source line order. Returns:…, Sample keys by deterministic every-Nth stratification. Args: ordered_keys: Keys…, Result of one corpus-sample build run. Attributes: keys: Selected lookup keys…, Collect all editorial siblings for sampled keys in corpus order. Args:… (+45 more)

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

### Community 170 - "20260707_01_drop_search_keys.py"
Cohesion: 0.40
Nodes (4): downgrade(), Drop legacy lexicon search-index tables from the canonical schema. Side…, Recreate empty legacy lexicon search-index tables. Side Effects: Restores empty…, upgrade()

### Community 171 - "_ParticipleOverride"
Cohesion: 0.67
Nodes (3): NamedTuple, _ParticipleOverride, Participle override applied when a strong-paradigm dispatch matches.

### Community 172 - "TestCLISettings"
Cohesion: 0.17
Nodes (7): Test the settings command., Test the settings command with table output., Test the settings command with JSON output., Test the settings command with text output., Test the settings command with verbose flag., Test the settings command with custom config file., TestCLISettings

### Community 173 - "test_lemma_morph_assignment.py"
Cohesion: 0.24
Nodes (16): assigner(), _assignment(), catalog_db(), _class_key(), _make_verb_paradigm(), _make_word(), fixture, Path (+8 more)

### Community 174 - "File Structure"
Cohesion: 0.15
Nodes (12): File Structure, GeneratorSession → WordPool + GenerationRunState Split Implementation Plan, Global Constraints, Task 1: Introduce `WordPool` + `GenerationRunState`, compose `GeneratorSession` from them, Task 2: Migrate the assigners (`noun.py`, `verb.py`, `adj.py`) onto `WordPool`, Task 3: Migrate the shared sink + row-emission leaf layer onto `GenerationRunState`/`WordPool`, Task 4: Migrate `generation/adv_forms.py` (smallest generator — proves the pattern end to end), Task 5: Migrate `generation/num_forms.py` (+4 more)

### Community 175 - "20260707_02_bt_senses_entry_order_index.py"
Cohesion: 0.40
Nodes (4): downgrade(), Add index supporting ordered sense lookup by dictionary entry. Side Effects:…, Remove ordered lookup index for dictionary sense reads. Side Effects: Drops the…, upgrade()

### Community 176 - "DictionaryBuildPipeline"
Cohesion: 0.10
Nodes (22): DictionaryBuildEventSink, DictionaryBuildStatus, Event, DictionaryBuildCounters, Monotonic counters accumulated while one build runs., DictionaryBuildPipeline, Connection, Path (+14 more)

### Community 178 - "lexicon/conftest.py"
Cohesion: 0.21
Nodes (14): _inflection_code_id(), lexicon_db_connection(), lexicon_db_path(), _noun_pos_id(), Connection, fixture, Path, Shared fixtures for lexicon schema and service tests. (+6 more)

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
Cohesion: 0.17
Nodes (16): DictionaryBuildEvent, DictionaryBuildFinished, DictionaryBuildLog, DictionaryBuildSnapshot, DictionaryBuildStageProgress, DictionaryBuildStageStarted, Typed stage and event models for unified dictionary builds., Successful terminal event for one completed dictionary build. (+8 more)

### Community 188 - "BT Structural Visibility Review"
Cohesion: 0.17
Nodes (12): Acceptance Criteria, BT Structural Visibility Review, Candidate Types To Include, Deliverables, Dependencies, Downstream Use, Locked Decisions, Non-Goals (+4 more)

### Community 189 - "wyrdcraeft"
Cohesion: 0.15
Nodes (12): All other code, Bosworth-Toller Old English Dictionary, Canonical database, Contributing, Contributing, Licensing and Provenance, Documentation, Features, Installation (+4 more)

### Community 190 - "browse_tui.py"
Cohesion: 0.05
Nodes (58): test_lexical_distance_prefers_exact_matches(), test_normalized_query_at_affix_requires_start_or_end(), _best_hit(), _browse_hit_sort_key(), BrowseSearchHit, _dominant_paradigm(), _group_morphology_rows(), _hit_lexical_distance() (+50 more)

### Community 191 - "Phase D — Drop Legacy Form String Columns"
Cohesion: 0.15
Nodes (12): Phase D — Commit, Phase D — Drop Legacy Form String Columns, Phase D — Gate A: Spec review checklist, Phase D — Gate B: Code review checklist, Phase D validation, Post-phase checklist (coordinator), Task 1: Alembic migration `20260706_04`, Task 2: Sink + query path cleanup (+4 more)

### Community 192 - "LemmaMorphClassAssigner"
Cohesion: 0.04
Nodes (52): catalog_db(), _make_word(), fixture, Path, query_service(), Tests for read-only Wright catalog lemma class lookup., test_format_morph_class_display_label_falls_back_to_canonical_name(), test_format_morph_class_display_label_prefers_compact_modern_label() (+44 more)

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

### Community 213 - "Dictionary CLI index gate and morph paths Implementation Plan"
Cohesion: 0.17
Nodes (10): Considered Options, Index population gate is a query-module check, not startup runtime, Dictionary CLI index gate and morph paths Implementation Plan, File map, Global Constraints, Self-review, Spec coverage, Task 1: Index population gate (+2 more)

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

### Community 236 - "_RecordingSink"
Cohesion: 0.23
Nodes (16): Capture emitted ``form_data`` payloads without TSV geminate expansion., Record one emitted row payload., _RecordingSink, _strong_generator(), _strong_inf_context(), _strong_principal_context(), test_dispatch_strong_derived_from_principal_part_papt_only(), test_dispatch_strong_derived_from_principal_part_routes_painpl() (+8 more)

### Community 237 - "PHONOLOGY"
Cohesion: 0.04
Nodes (47): The Seafarer (Old English poem, test fixture), Old English Bosworth-Toller Dictionary Text, 1. UMLAUT, 2. Breaking, 3. Influence of Nasals, 4. Influence of Initial Palatal Consonants, 5. Influence of w, a (+39 more)

### Community 238 - "CONTEXT.md"
Cohesion: 0.15
Nodes (8): Lexicon data lives in morphology.sqlite3, BT OCR parsing starts with lossless source-grounded AST, BT source acquisition uses a multi-witness download set, BT JP2 witness preparation is library-first, Consequence, Not removed, OCR pipeline moves to bochord, Removed from wyrdcraeft

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

### Community 247 - "split_prose_and_verse_runs"
Cohesion: 0.33
Nodes (8): _is_heading_line(), _is_number_line(), _is_verse_line(), Test if a line looks like a heading., Heuristic: short, line-broken, non-empty lines typical of OE verse editions., Test if a line is just a numbering marker (e.g. "[12]" or "5")., Split text into ordered prose / verse chunks. - Preserves original text exactly…, split_prose_and_verse_runs()

### Community 248 - "Orchestrator Checkpoint"
Cohesion: 0.29
Nodes (6): Active blockers, Last 3 log events, Locked decisions, Orchestrator Checkpoint, Phase status, Resume here

### Community 249 - "DictionaryBuildStage"
Cohesion: 0.21
Nodes (9): DictionaryBuildStage, StrEnum, Stable stage labels emitted during one unified dictionary build., DictionaryBuildProgress, Protocol, Progress callback surface used during unified dictionary builds., Mark one build stage active. Args: stage: Stage being entered. Keyword Args:…, Advance one build stage. Args: stage: Stage being advanced. Keyword Args:… (+1 more)

### Community 251 - "MorphologyGenerationFacade"
Cohesion: 0.10
Nodes (18): Regression test for the generation-package import-cycle fix.…, The package must not carry a facade re-export that recreates the cycle., The only import path any real caller uses must keep working., The facade's verb-generation method is the production entrypoint., test_facade_still_importable_directly(), test_facade_verb_method_still_importable(), test_generation_package_does_not_reexport_facade(), MorphologyGenerationFacade (+10 more)

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

### Community 259 - "resolve_dictionary_db_path"
Cohesion: 0.16
Nodes (13): test_resolve_dictionary_db_path_prefers_explicit_override(), test_resolve_dictionary_db_path_uses_sibling_dictionary(), _db_has_table(), _forms_has_morph_class_id(), _morphology_db_has_bt_entries(), Connection, Path, Return whether one SQLite table exists in the active database. Args:… (+5 more)

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

### Community 271 - "test_normalized_title_join.py"
Cohesion: 0.28
Nodes (12): _index(), Unit tests for NormalizedTitleJoinIndex., test_resolve_all_exactly_one_title_across_pos(), test_resolve_all_no_match(), test_resolve_all_pos_direct_multiple_matches(), test_resolve_all_pos_direct_single_match(), test_resolve_all_variant_with_pos_filter(), test_resolve_all_variant_without_pos_filter() (+4 more)

### Community 297 - "Verb generators leave `common.py`"
Cohesion: 0.14
Nodes (12): Consequences, Considered options, Engines, not OE conjugation classes, Module map, Verb generators leave `common.py`, File map, Global Constraints, Out of scope (+4 more)

### Community 301 - "ParadigmAssigner"
Cohesion: 0.29
Nodes (6): FormEmitter, ParadigmAssigner, Protocol, Session-level assigner contract., Assign paradigms in-place for session words. Note: Paradigm assignment reflects…, Form emission contract.

### Community 302 - "progress.md"
Cohesion: 0.50
Nodes (3): Phase A SDD Progress, Prior ledger (Phase A — do not treat as ADR 0010), SDD Progress — ADR 0010 LLM/unstructured leave source convert

### Community 303 - ".__init__"
Cohesion: 0.29
Nodes (4): Path, Initialize a SQLAlchemy sink for emitted morphology rows. Note: Index schema…, Ensure the canonical ``forms`` table and its indexes exist., Tune SQLite for bulk morphology index writes. Side Effects: Sets WAL mode and…

### Community 306 - "TestConsoleQuietMode"
Cohesion: 0.33
Nodes (4): Test console quiet mode functionality., Test that console can be set to quiet mode., Test that stderr console can be set to quiet mode., TestConsoleQuietMode

### Community 312 - ".emit_form_data"
Cohesion: 0.40
Nodes (3): Any, Write text to the underlying output stream., Emit one legacy form payload using parity row semantics. Note: Linguistic…

## Ambiguous Edges - Review These
- `task-phase1-morph-class-browse-report.md` → `task-phase2-wright-text-ingest-report.md`  [AMBIGUOUS]
  doc/sessions/task-phase2-wright-text-ingest-report.md · relation: references
- `The Seafarer (Old English poem, test fixture)` → `Old English Bosworth-Toller Dictionary Text`  [AMBIGUOUS]
  tests/fixtures/seafarer.txt · relation: conceptually_related_to

## Knowledge Gaps
- **927 isolated node(s):** `release.sh script`, `wyrdcraeft`, `IPA_AUDIO`, `$schema`, `$id` (+922 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2727 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **36 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `task-phase1-morph-class-browse-report.md` and `task-phase2-wright-text-ingest-report.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `The Seafarer (Old English poem, test fixture)` and `Old English Bosworth-Toller Dictionary Text`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `GeneratorSession` connect `GeneratorSession` to `generation/sinks.py`, `reference_snapshots.py`, `morphology/test_query_service.py`, `OENormalizer`, `VerbFormGenerator`, `test_generation_branches.py`, `_RecordingSink`, `test_session_composition.py`, `read_jsonl_gz`, `build_runner.py`, `MorphologyGenerationFacade`, `WordPool`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `OENormalizer` connect `OENormalizer` to `Word`, `generation/sinks.py`, `wright_audit.py`, `normalize_morphology_title`, `BTSqliteSink`, `GeneratorSession`, `VerbFormGenerator`, `generation/query.py`, `MorphologyDictionaryCleaner`, `test_generation_branches.py`, `FormRow`, `markup.py`, `StrongVerbGenerator`, `set_verb_paradigm`, `WordPool`, `AdjectiveFormGenerator`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `Word` connect `Word` to `normalize_morphology_title`, `OENormalizer`, `test_generation_branches.py`, `_WeakPainsg1DerivationContext`, `_WeakPrincipalPartContext`, `WordPool`, `StrongVerbGenerator`, `AdjectiveFormGenerator`, `_WeakInfDerivationContext`, `test_lemma_morph_assignment.py`, `LemmaMorphClassAssigner`, `wright_audit.py`, `GeneratorSession`, `VerbFormGenerator`, `set_verb_paradigm`, `AdverbFormGenerator`, `test_session_composition.py`, `._generate_word`, `models/__init__.py`, `build_participle_adjective`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `Word` (e.g. with `test_generate_verb_parts_routes_direct_derivation_stack()` and `test_generate_verb_parts_routes_direct_weak_painsg1_stack()`) actually correct?**
  _`Word` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `GeneratorSession` (e.g. with `_run_prerequisite_stages()` and `full_session()`) actually correct?**
  _`GeneratorSession` has 25 INFERRED edges - model-reasoned connections that need verification._