---
status: proposed
---

# Ambiguity is judged on marks, and ambiguous tokens are resolved by a policy

Follows [ADR 0015](0015-mark-diacritics-is-additive-transfer.md). The goal of
`source mark-diacritics` is to take unmarked text, make it student friendly and
leave as little manual work as possible. Today any token whose key is in the
index's `ambiguous` list is left completely unchanged and reported, and 889 of
the 967 ambiguous keys are still undecided. This ADR records how to shrink that
list without new data. Nothing here is implemented yet.

## Facts (measured on the packaged index and its git history)

- 889 ambiguous keys are not marked completed. 142 of them (16%) have options
  that differ only by hyphens, eth/thorn, case or BT diphthong style.
- The other 747 differ in marks: 607 are one marked and one unmarked option
  (`æ`/`ǣ`), 130 are nested (one option has strictly more marks), 10 put marks
  on different letters.
- The user's past decisions, recovered from git history: of 86 keys resolved to
  one word whose options have the same letters, the chosen form was the union of
  the options' marks 69 times; the shared marks only 14 times. 77 keys were kept
  as two genuine words (`ac`/`āc`, `an`/`ān`, `are`/`āre`).
- Marks alone cannot tell a homograph from an entry BT printed without a macron.
  BT part of speech and gloss overlap did not separate the two groups either.
  What does correlate: true homographs are mostly short and unhyphenated (47 of
  73 kept keys are 4 letters or fewer with no hyphen in any BT option; only 11
  of 66 same-word keys fit that), while BT writes a hyphen where it analyses a
  word as prefix + stem or compound.
- A first rule "auto-union if some BT option is hyphenated or the key has 8+
  letters" covered 34 of 66 same-word keys and wrongly covered 9 of 73
  homographs (79% precision) on the labeled decisions. The adopted rule adds the
  non-standard-prefix guard; on a re-measure over the keys where the user chose
  the union (50) it marks 16 of them and wrongly marks 9 of 73 homographs
  (64% precision), because the guard drops 7 correct marks (`an-`/`ān-`,
  `bi-`/`bī-`, `cīst-`). The two measures use different key sets, so they are not
  directly comparable. The 8-letter threshold was picked on this same small
  sample, which skews to the start of the alphabet, so it is likely optimistic.
- `a-` and `ā-` as a prefix mean the same; the difference is an editorial or
  scribal choice. The user resolved such keys inconsistently (10 to `ā-`, 6 to
  `a-`) and prefers plain `a-` because it is the more common form in full
  texts. Only two undecided keys remain that differ solely in that prefix
  (`abregan`, `acuman`), so this rule mostly guards future imports. `for-`/`fōr-`
  is the same kind of pair (the user: an editorial choice; grammar texts name
  `for-`) and, with the hyphen evidence in every differing option, clears 31
  undecided keys (`for-beran`/`fōr-beran`, `for-boda`/`fōr-boda`). `ge-`/`gē-`
  is the same (the user: `ge-` is always spelled `ge-`; `gē` as in `gēon` is
  deliberate) and clears 1 (`ge-bindan`/`gē-bindan`); the hyphen evidence is
  what keeps `ge-an` / `gēan` apart. (An earlier, looser count gave 28 and 5.)
- `fore-`/`fōre-` is the same kind of pair as `for-`/`fōr-` (the user, citing a
  newer article: there is no evidence either pair differs in meaning), so both
  are editorial and written plain (`fore-`, `for-`). 49 undecided keys differ only
  in the `fore-` prefix (`fore-beran`/`fōre-beran`). In total 166 undecided keys
  differ only in marks before a BT hyphen: 83 are editorial pairs (`fore-` 49,
  `for-` 31, `a-` 2, `ge-` 1) and 83 are not, namely other prefixes and compound
  first elements (`oþ-`, `gebed-`, `hired-`, `sweor-`, `beacen-`, `bonde-`).
  The user has since standardized `hīrēd-`, `bēacen-`, `ōþ-` and `bonde`, which
  settle part of those 83; `gebed-`/`ge-bēd-` was deliberately left separate. The
  user's own past decisions on that kind of key (14) were mixed: the union 8
  times, a single option 6 times (`an-weald`, `blæc-ern`, `bonde-land`).
- Standardizing is not only about ambiguous keys. Replacing a reference form's
  element marks with the standard ones changes unique entries too: 823 unique
  forms starting `ā-` would lose that mark (`ā-bacan` → `a-bacan`), as would 47
  with `fōr-` and 66 with `fōre-`; 3 `hīred-` and 4 `oþ-` forms would gain marks.
  No completed (curated) key is affected. The user confirmed this scale is
  acceptable.
- A test of "prefix + a stem that is an index key" is unsafe: short keys such as
  `c`, `n` and `rod` exist, so it would call `ac`/`āc`, `an`/`ān` and
  `arod`/`ārod` prefix pairs, and those are genuine homographs.
- The runtime model `MacronIndex` does not carry `ambiguous_completed`, so the
  applicator cannot tell curated keys from undecided ones.

## Decisions

1. **Order of operations (proposed).** For each token: look up the key with
   `normalize_old_english` → reduce each reference form to a diphthong-canonical
   mark pattern (ADR 0020) → apply standard element forms (decision 3) → collapse
   options that now agree → apply the ambiguity policy (decision 4) → additive
   transfer onto the source.
2. **Ambiguity is judged on marks.** At match time, options are compared
   by letters and diphthong-canonical marks only (ADR 0020), ignoring hyphens,
   case and eth/thorn. If all options collapse to one mark pattern the key is
   not ambiguous: the marks are applied and no ambiguity row is written. This is
   a runtime rule; the `ambiguous` list in the index file is not rewritten.
3. **Standard element forms.** Some prefixes and compound elements have one
   standard spelling, because BT's mark variants are an editorial or scribal choice
   and not a difference in meaning. A data file under `wyrdcraeft/etc/diacritic/`
   maps each element, unmarked, to its standard spelling, and the user can extend
   it. Initial entries:
   - plain (no marks): `a-`, `for-`, `fore-`, `ge-`, `bonde` (as a prefix or a
     suffix). So `ā-`, `fōr-`, `fōre-`, `gē-` and `bōnde` are never written.
   - marked: `hīrēd-`, `bēacen-`, `ōþ-`.
   - not standardized, on purpose: `gebed-` and `ge-bēd-` stay separate. The
     index has 12 keys with 15 forms: 5 marked (`ge-bēd-man`, `ge-bēd-dagas`, …)
     and 10 unmarked (`gebed-bygen`, `gebed-giht`, `gebed-tīd`, …); it is not
     certain the unmarked ones all contain `bēd`, so they stay as BT has them
     for safety.

   Rules:
   - **Hyphen evidence.** An element counts only where BT writes a hyphen
     directly after it (`for-beran`, `hīrēd-mann`), or around it for a suffix
     (`hūs-bonde`), in every option that differs: `ge-an` has the hyphen but
     `gēan` does not, so that pair never collapses. The hyphen is evidence from the BT entries only: the source
     text need not be hyphenated. BT forms with no such hyphen (`for`/`fōr`,
     `forþ`/`fōrþ`, `gēon`) never qualify, a `gē` in an unhyphenated word is a
     different word on purpose, and `foran-` is not `for-`. This also keeps
     `ge-an` / `gēan` apart.
   - **Standardization.** The marks of a matching element in a reference form are
     replaced by the standard marks before the transfer. Options that then differ
     only in that element collapse to one reading, so they are not ambiguous
     (`hīred-mann`/`hīrēd-mann` → `hīrēd-mann`). Marks elsewhere in the word are
     unaffected. The scope is every reference form, unique or ambiguous, so a
     unique `oþ-feolan` becomes `ōþ-feolan` (confirmed by the user).
   - **Source keeps its own.** A source that already writes `ā-`, `fōr-`, `gē-`
     or `oþ-` keeps it (additive, ADR 0015); nothing is removed or replaced.
   - **Allowlist.** Only listed elements are standardized. A hyphen alone is
     necessary evidence, not sufficient.
4. **Ambiguity policy** `--ambiguity-policy` on `source mark-diacritics`:
   - `auto` (default): apply the union of marks when some BT option for the key
     is hyphenated or the key has 8 or more letters, except when the marks
     differ only before a BT hyphen and that prefix or first element is not on
     the standard-element list (`an-`/`ān-`, `bi-`/`bī-`, other compound first
     elements): there the marks may be a real lexical distinction, so the token
     is left unchanged and reported. Everything else is left unchanged
     and reported too.
   - `leave`: today's behavior for every ambiguous token.
   - `union`: apply the union of marks everywhere, except on letters where the
     options put conflicting marks. It is a guess and is opt-in.
5. **Curated keys are protected.** A key in `ambiguous_completed` was decided by
   the user to be genuinely ambiguous; neither `auto` nor `union` applies to it.
6. **Guesses are visible.** A token resolved by `auto` or `union` still appears
   in the ambiguity report, with the form actually written and the policy that
   wrote it, so the user can review exactly the guessed tokens. To veto a key the
   user edits the index file directly (marking it completed through
   `diacritic-disambiguate` needs every form annotated with a sense, which the
   current BT parsing makes hard; improving that parsing is separate work).
7. **Review queue.** Keys that collapse under decisions 2 and 3 are skipped by
   `diacritic-disambiguate`; keys left unresolved by `auto` stay in it.
8. **Acceptance test.** The labeled decisions recovered from the index's git
   history (86 resolved, 77 kept as two words) are a fixture to measure the
   `auto` rule, so it can be re-measured when more keys are curated.

## Considered options

- **`consensus` (apply only marks every option has).** Rejected by the user: a
  partly marked word costs as much review as an unmarked one, and it does nothing
  for a marked/unmarked pair (607 undecided keys).
- **`union` as the default.** Rejected: about half of the keys the user decided
  were genuine homographs, so it would put wrong macrons in student text.
- **Prefix + known stem as evidence of a prefix.** Rejected: see facts.
- **Treat every BT-hyphenated prefix pair as editorial.** Rejected: the user's own
  past decisions on other prefixes (`an-`/`ān-`, `bi-`/`bī-`) and compound first
  elements were mixed, so only elements the user names go on the list.
- **Use BT part of speech or gloss overlap.** Rejected: neither separated the
  groups.
- **Rewrite the `ambiguous` list to drop the collapsible keys.** Rejected: the
  index is curated data (ADR 0016).
- **Per-text decisions and corpus or context resolution.** Not rejected, only out
  of scope; a separate ADR.

## Open questions

- Where the standard-element file lives and its format. Proposed: a hand-edited
  data file under `wyrdcraeft/etc/diacritic/`, like the existing `c` and `g`
  exception lists, with no CLI to edit it.

## Resolved questions

- Undecided keys with other (non-standard) prefix or first-element differences
  are left for review: `auto` leaves the token unchanged and reported, and the
  user decides them with `diacritic-disambiguate`.
- The interactive `diacritic-disambiguate` queue skips keys that collapse under
  decisions 2 and 3, since they need no decision.

## Consequences

- Output for tokens that were ambiguous changes: they may now be marked. This
  still only adds marks (ADR 0015).
- The ambiguity report gains fields for the applied form and policy; consumers
  of `.anomalies` JSON must tolerate new fields.
- `MacronIndex` must carry `ambiguous_completed`.
- Tests need fixtures for each policy, the collapse rule, the standard-element
  rule, and a curated key.
