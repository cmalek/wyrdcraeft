---
status: accepted
---

# `source mark-diacritics` is additive transfer, not replacement

`source mark-diacritics` exists to add helpful diacritics while preserving the
source text as closely as possible. It previously replaced each token with the
macron index display form (Bosworth-Toller spelling, keyed on `ð`→`þ`
normalization), which silently swapped eth/thorn and added hyphens. It now
transfers marks only: the index form is aligned to the source token (case,
ð≡þ, and hyphens ignored) and the index's combining marks (almost all
macrons; a handful of breves and diaereses) are copied onto the matching
source letters. No source character is ever removed, replaced, or re-cased.

Rules:

- Tokenization keeps combining marks with their base letter, so decomposed
  (NFD) input is not shredded; untouched letters are emitted byte-for-byte.
- En and em dashes count as hyphens for alignment and are never converted.
- Source ð/þ, casing, and hyphen presence or absence are kept as written.
- Marks already in the source, even ones that disagree with the index, are kept.
- If the index form cannot be aligned, the token is left unchanged and written
  to a new `--unaligned` report, separate from `.anomalies` (ambiguous) and
  `.unknown` (not in index). Lookup is by normalized key, so spelling variants
  such as `ae`/`æ` or `w`/`ƿ` miss the key and are `.unknown`, not unaligned.
  Unaligned means the index entry itself is inconsistent: its display form
  does not normalize to its own key (e.g. `acmuman` → `ā-cuman`). The builder
  and packaged index no longer produce such entries except hand-curated ones.
- `ġ`/`ċ` palatalizers insert a dot at the matched position only (never
  lowercasing the token). `ġ` is not dotted before a back vowel (`stīgan`,
  `wiga` stay velar), and the `g` exception lists compare with ð≡þ folded.
- The macron index builder and the packaged index were also changed so wrong
  variant→headword entries are gone; see
  [ADR 0016](0016-macron-index-variants-are-own-entries-and-index-is-repaired-not-regenerated.md),
  which amends this ADR. The alignment check remains as a backstop and feeds
  `.unaligned`.

## Considered options

- **Keep replacing with the index form.** Rejected: it violates the
  preserve-the-source goal.
- **Transfer whatever aligns, skip the rest, on partial mismatch.** Rejected:
  guessing risks corrupting the source; unchanged-and-reported is safer.
- **Fold unaligned rows into `.unknown`.** Rejected: "not in index" and "in
  index but unalignable" are different problems to fix.
- **Store diacritic positions instead of display forms in the macron index.**
  Rejected: needless migration; the index stays human-readable and
  `diacritic add`/`diacritic-disambiguate` are unaffected.

## Consequences

- Output of `mark-diacritics` may differ from previous runs for any token whose
  index display form used a different eth/thorn or hyphenation; tests and
  snapshots change with this decision.
- Tokens that previously got a (possibly spelling-altering) replacement may now
  appear in `.unaligned` instead. For corrupt index entries this fixes a latent
  bug: the old code replaced the source with an unrelated word.
- `.unaligned` should be rare and flags remaining index problems (ADR 0016).
- The palatalizers currently lowercase and re-case whole tokens; making them
  position-based is a behavior change beyond the `sc` rule.
- "Immediately preceded by `s`" is evaluated within the token; a hyphen between
  `s` and `c` (e.g. a prefix boundary) means the `c` is not preceded by `s`.

## Related changes made in the same work

These go beyond the user's three original rules (no eth/thorn swap, no added
hyphen, no dot on the `c` of `sc`). They came from an end-to-end review of the
command and are deliberate; do not revert them as scope creep.

- **`GPalatalizer` rule rewrite.** The old trailing "first `g` after a front
  vowel" block dotted `g` regardless of what followed, so `stigan` → `stīġan`
  and `wiga` → `wiġa` (velar before a back vowel) and the "front vowel on both
  sides" rule was dead code. Now a non-initial `g` is dotted when preceded by a
  front vowel and not followed by a back vowel (`hiġe`, `þeġn`, `weġ`); initial
  `g` before a front vowel is unchanged. Consequence: `wegas` stays `wegas`
  (previously `weġas`), and the test that asserted `weġas` was updated.
- **Exception lists are folded, not normalized.** The frontal exceptions (read from
  `g/frontal.txt`) and `ENDING_G_EXCEPTIONS` compare with NFC, lowercase and ð≡þ. Full
  normalization (`normalize_old_english`) was rejected because it strips
  macrons and would conflate `gēar` with `ġear`. The `c` lists already used
  normalization and are unchanged.
- **Palatalizers never lowercase.** Both compute on a lowercase copy and graft
  a combining dot onto the matching source cluster (`_graft_dots`), so case,
  eth/thorn and every other character stay as written.
- **API changes.** `MacronApplicator.apply` returns a 4-tuple (new last item:
  the unaligned index form or `None`). `DiacriticRestorationResult` gains
  `unaligned: list[UnalignedToken]`. `restore_text` was split into
  `restore_text` + `_restore_line` to stay within the 60-line method limit.
- **CLI.** New `--unaligned-output` (default `stem.unaligned.ext`); help text
  and success message now say "add"/"marked" rather than "restore".
- **Docs/tests.** Command docs, `docs/context/diacritic.md`, `CONTEXT.md`
  (glossary terms: diacritic marking, diacritic transfer, unaligned token, sc
  exception; ADR list) and the changelog were updated. New tests cover
  alignment, NFD input, dashes, `sc`, case preservation, velar `g`, and the
  unaligned report.

## Not changed / known gaps

- `hē—and`-style tokens (word, dash, word) are one token and are looked up as
  one unknown word; they are left unchanged, which is safe but means no marks.
- Quality gates: `make napoleon-gate` already fails on the clean tree
  (93 reported vs 95 baseline keys); `mypy` has one pre-existing error at
  `wyrdcraeft/cli/cli.py:107`. Neither was caused by this work except one new
  `model_config` `#:` comment gap on `UnalignedToken`, matching the other models.

## Follow-up (implemented): `GPalatalizer` reads `g/frontal.txt`

`g/frontal.txt` is a hand-maintained list of `g` exceptions, like the two `c`
lists, but nothing reads it: `GPalatalizer` uses the hardcoded
`FRONTAL_G_EXCEPTIONS`, so the user's edits to the file have no effect.

Decision: `GPalatalizer` loads its frontal exceptions from this file instead of
the hardcoded list, the way `CPalatalizer` loads its lists, and the hardcoded
list is removed. The file stays the single hand-edited source of truth.

Facts to respect when implementing:

- The two lists barely overlap. The file has 22 entries and the hardcoded list
  44; only `gēs` is in both. Switching without migrating would drop protection
  for 43 words (for example `gēar`, `gēat`, `gǣt`, `gēn`, `gǣl`), so `g` would
  start getting a dot in them; an existing test expects `gēar` to stay velar. The
  file also has 21 entries the code does not (`gigant`, `genesis`, `gylden`,
  `girwan`, `Gildas`, `gegnum`, …) that would start to apply.
- So the migration should first add the 43 missing entries to the file (a union),
  so no existing protection is lost, and the user can then prune it. Some of the
  43 are redundant because `g` before a back vowel is never dotted (`gaf`,
  `gār`, `gangan`).
- The file has no comment lines today; the loader should skip blank and `#`
  lines like the `c` loader, fold entries with `_fold` (NFC, lowercase, ð≡þ, so
  `Gildas` matches), and drop a trailing hyphen (`gǣst-` becomes `gǣst`), because
  the palatalizer compares one dash-free segment at a time.
- `ENDING_G_EXCEPTIONS` (`plǣg`, `sweg`, `tǣghrēg`) has no file and is out of
  scope of this change.

## Refined by

[ADR 0020](0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md)
(proposed) makes the transfer treat a diphthong as one unit and fixes source
capitalization; it is implemented in `DiacriticTransfer`, so a source already
marked in BT's diphthong style is no longer double-marked.
