---
status: accepted
---

# Verb generators leave `common.py`

ADR 0009 collapsed Perl callback soup into `VerbFormGenerator`,
`StrongVerbGenerator`, and `WeakVerbGenerator`, but left all three in
`generation/common.py`. That file is still a god module. Adjectives and nouns
already live as one class per file (`adj_forms.py`, `noun_forms.py`). We split
verbs the same way and **delete** `common.py` — no stub, no compatibility
re-exports.

`facade.generate_verbs()` still constructs `VerbFormGenerator`. That orchestrator
still constructs Strong/Weak in `__init__` from the same `word_pool` /
`run_state` / `output_file`; those collaborators are not facade constructor
arguments. `AGENTS.md` now says public boundaries are injected and private
collaborators may be built inside the orchestrator.

**Status:** accepted. Implementation is Trello
https://trello.com/c/vzj24HRg (one landing). Wright class-II `-ig-`/`-ige-`
spellings are a separate behavior card (https://trello.com/c/s0IpN3s9), not
this split.

## Module map

- `verb_forms.py` — `VerbFormGenerator`
- `strong_verb_forms.py` — `StrongVerbGenerator`
- `weak_verb_forms.py` — `WeakVerbGenerator`

`verb_forms.py` imports the strong/weak modules; those two must not import
`verb_forms.py`. Each generator file binds `form_rows` / `participles` helpers
as module-level names so tests patch that module, not `form_rows` globally.
`nz` / `perl_numify` come from `scalar_utils`; `print_one_form` callers import
`form_rows`. Drop unused `VerbFormGenerator.S2_CHANGES` / `S3_CHANGES` and the
orchestrator's leftover `_add_participle_to_adjectives` forward. Do not copy
`common.py`'s blanket ruff `noqa`.

This split is a file move: keep generation order (manual, verb, adjective,
adverb, numeral, noun). The unreachable `elif class2 == "2"` loop still moves
verbatim so the Wright-correctness change stays on its own card
(https://trello.com/c/s0IpN3s9). Perl is not an oracle; see ADR 0012.

## Considered options

- **Leave `VerbFormGenerator` in `common.py` after extracting Strong/Weak.**
  Rejected: `common.py` would remain a misnamed hub.
- **Inject Strong/Weak through the facade.** Rejected: no product need; other
  PoS generators do not expose sub-collaborators on the facade; tests already
  construct Strong/Weak directly.
- **Keep a `common.py` re-export for tests.** Rejected: another redirect layer
  ADR 0009 existed to remove.
- **Enable the class-II spelling loop in this change.** Rejected: it is a
  real behavior change and must not hide inside a 3k-line move (Wright card
  s0IpN3s9; allowed in principle by ADR 0012).
- **Patch `form_rows` in tests.** Rejected: that would fake emission for every
  PoS generator, not just the verb module under test.

## Consequences

Callers of `generation.common` (`facade`, `test_generation_branches`,
`print_one_form` imports in `test_query_service` and `tests/lexicon/source_db`)
must retarget. Historical plans/ADRs that name `common.py` stay as history.

### Engines, not OE conjugation classes

The three Python classes are generation engines. They are **not** Wright’s
conjugation taxonomy (Weak I–II, Weak III, Strong I–VII, preterite-present,
anomalous). Do not add a generator class per linguistic group as part of this
split. Keeping `pp` and `a` in `WeakVerbGenerator` is Tichý packaging: those
paradigms are fully specified tables, not dental weak derivation. ADR 0012
allows a later move of that routing; this ADR does not require it.

Generation order still runs **manual forms** as a prior stage (curated rows,
including some irregulars). That is not a fourth verb-class generator.

| Linguistic group | `VerbParadigm.type` / flags | Engine / path |
|---|---|---|
| Strong I–VII | `s` (`vb_strong`) | `StrongVerbGenerator` (ablaut) |
| Weak I / II | `w` | `WeakVerbGenerator` derived-from-infinitive |
| Weak III (four oddballs) | `w`, paradigm IDs 89–92 | `WeakVerbGenerator` item-shape (`para_vb` parts) |
| Preterite-present | `pp` (`vb_pretpres`) | `WeakVerbGenerator` item-shape |
| Anomalous | `a` (`vb_anomalous`) | `WeakVerbGenerator` item-shape, plus extra manual-form rows where curated |
| Manual / exception rows | (not a paradigm type) | `output_manual_forms` before verb generation |

`VerbFormGenerator` only special-cases `type == "s"` onto Strong; `w`, `pp`,
and `a` all go to Weak. The catalog may still label seven preterite-present
Wright classes; they share one emitter, not seven Python classes.
