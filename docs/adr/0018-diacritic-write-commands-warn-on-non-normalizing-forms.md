---
status: proposed
---

# `diacritic` write commands warn on forms that do not match their key

Follows [ADR 0016](0016-macron-index-variants-are-own-entries-and-index-is-repaired-not-regenerated.md)
and sits beside [ADR 0017](0017-diacritic-cli-imports-bt-variants.md). The
packaged macron index is curated through `diacritic add`, `diacritic delete`
and `diacritic-disambiguate`. Nothing checks that a stored form actually
belongs to its key. Entries such as `acmuman` → `ā-cuman` came from the index
builder's variant mapping (ADR 0016), not from these commands, but the commands
can store the same kind of inconsistent entry, so the same guard belongs here. The
user confirmed this must be fixed. Nothing
here is implemented yet.

## Decisions

1. **Warn and confirm.** When the form stored by `diacritic add`, or by the
   disambiguate prompts "replace unique" and "add attested form", does not
   normalize to its own key, the command warns and asks for confirmation:
   the entry cannot be applied to text and will only appear in the `.unaligned`
   report. `--yes` skips the prompt.
2. **Not a hard reject.** Curated variants whose letters differ from their
   headword are legitimate. `blac` is a variant of `blæc` and is stored with
   the forms `blæc`/`blǣc`; rejecting that would block valid curation.
3. **Comparison uses the key lookup rule**, `normalize_old_english`, applied to the
   stored form (ADR 0020 keeps lookup unchanged), so a form that differs from its
   key only by hyphens, eth/thorn, case or marks does not trigger the warning.
4. **`add` and `delete` get tests.** `tests/test_cli_diacritic.py` covers both
   commands; before this change they had none (only `disambiguate` was
   tested).

## Considered options

- **Reject non-matching forms (optionally with `--force`).** Rejected: blocks
  legitimate variant entries such as `blac`.
- **No check.** Rejected: the commands could store the same kind of inconsistent
  entry the builder produced.
- **Check only in a separate audit command.** Not rejected, only deferred: an
  audit listing existing non-matching entries (including the curated ones) is
  useful but is a separate change.

## Consequences

- Interactive commands gain one confirmation in the rare mismatch case.
- Scripts must pass `--yes`.
