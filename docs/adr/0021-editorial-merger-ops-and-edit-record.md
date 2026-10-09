---
status: accepted
---

# Editorial merger stays a facade; edit records live with dictionary models

`BTEditorialMerger` is the right package for consolidating dictionary source
blocks, but `_merge_block` and the Substitute/Dele/Dele-and-add methods are
over the 60-line budget, and `BTEditRecord` is a domain audit type sitting in
a service module. Trello https://trello.com/c/Gwr8hysN. Structure only:
editorial behavior must not change.

This ADR **overrides the card** where they conflict (injection, a models
module of its own, one class per op including Add, a services re-export).
Same pattern as ADR 0014.

**Status:** accepted.

## Decision

1. **Move `BTEditRecord` into `wyrdcraeft.models.dictionary`**, next to
   `BTEditorialOp`, and export it from `wyrdcraeft.models`. Trello’s
   “semantically named models module” is that file, not a new
   `models/editorial.py`.

2. **No services re-export.** Canonical import is
   `wyrdcraeft.models.dictionary.BTEditRecord`. Update the three callers:
   `editorial_merger.py`, `sinks.py` (today imports the service module
   directly), `tests/dictionary/test_editorial_merger.py`, and drop it from
   `services.dictionary.__all__`. A compatibility alias is the redirect
   layer ADR 0011 deleted.

3. **`BTEditorialMerger` stays the public facade.** `merge` and
   `collect_editorial_warnings` remain the entry points.

4. **Private collaborators, not injected ops.** The card asked for injected
   collaborator classes. Rejected: AGENTS.md lets the orchestrator construct
   private collaborators in `__init__` from public boundaries; ADR 0011
   already refused to put Strong/Weak on the facade constructor. Public
   seams stay `resolver` and `block_builder`. Op classes are built inside
   `__init__` from `resolver`.

5. **One collaborator class per over-budget editorial operation**, all in
   `editorial_ops.py`: Substitute, Dele, Dele-and-add. **Not Add** — that
   method is already under 60 lines once `append_senses` is shared. Four
   files for four methods is scaffolding. One `EditorialOpApplicator` with
   every `apply_*` is the same god object.

6. **Moving a method is not shrinking it.** Every public and private method
   on those collaborators must be ≤ 60 lines with no new `PLR0912` noqa.
   Substitute in particular must split internally (target resolution vs
   sense rewrite vs audit emission). A 165-line `SubstituteOp.apply` fails
   this card.

7. **Substitute may mutate a foreign entry.** “May mutate” reflects the
   collaborator signature: current entry, line, current block, and
   `all_blocks`. Cross-entry “for X in Dict” / whole-entry substitute is
   in-scope behavior, not `apply(entry, line)` only. This landing does not
   rewrite the foreign block (`for_X_in_Dict` audit records use
   `applied=False`).

8. **`append_senses` lives in `editorial_ops.py` as a module-level
   function.** Add (still on the merger) and Dele-and-add both call it.
   `_extend_senses` / `_next_top_level_path` stay on the merger: they
   reassign colliding MAIN follow-on `sense_path` values, which is seed
   assembly, not an editorial op.

9. **`_merge_block` is in scope.** Trello’s first code citation
   (`editorial_merger.py:326-435`) is this method, not an `apply_*`. Extract
   seed selection, `BTConsolidatedEntry` construction, and MAIN follow-on
   assembly into private merger helpers so `_merge_block` is dispatch (ops
   + gender promote) and ≤ 60 lines. That is not a fifth op class.

10. **`_apply_cross_refs` is out of scope.** `CROSS_REF` is not a
    `BTEditorialOp`; it fills `see_also` after consolidation. It is already
    under 60 lines. Leave it on the merger.

11. **No new packages.** Characterization stays
    `tests/dictionary/test_editorial_merger.py`. Do not assert collaborator
    internals.

## Considered options

- **New `models/editorial.py`.** Rejected: one dataclass beside
  `BTEditorialOp`.
- **Keep `BTEditRecord` on the services package.** Rejected: two homes;
  `sinks.py` would not even use the alias.
- **Inject each op on the merger constructor.** Rejected: see Decision 4;
  overrides the card.
- **Class-per-op including Add, for uniform dispatch.** Rejected: dispatch
  is four loops; Add is not over budget.
- **Leave `_merge_block` for a follow-up.** Rejected: it is the cited
  range; extracting `apply_*` does not shrink the seed-assembly half.
- **Op registry keyed by `BTEditorialOp`.** Rejected: four known line
  kinds, no third-party ops.
- **Split methods in place, leave the record in the service file.**
  Rejected: the finding is line-budget *and* model home.

## Consequences

Importers of `BTEditRecord` retarget to models in the same landing.
`editorial_ops.py` holds three classes plus `append_senses`, note helpers
`_plain` and `_target_note`, and the Substitute/Dele regexes currently at
the top of `editorial_merger.py`. `_edit_note_reason` and `_edit_note_detail`
stay on the merger beside `collect_editorial_warnings` unless a move is
required to keep a method under 60 lines.
