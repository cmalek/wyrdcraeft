---
status: proposed
---

# `DiacriticTransfer` treats a diphthong as one unit; `BTSpellingNormalizer` is not used

Split out of [ADR 0015](0015-mark-diacritics-is-additive-transfer.md), which it
refines. Implemented in `DiacriticTransfer` (`mark_pattern`, diphthong-aware
`transfer`); see ADR 0019 for how the applicator uses it.

## Context

Two different jobs are easy to confuse:

- **Finding the BT word for a source word** is a key lookup, and
  `normalize_old_english` already does it: it lowercases, maps `ð` to `þ`, strips
  every mark and removes hyphens, so `leāst`, `lēast` and `LEAST` all resolve to
  `least`. It never needs to know where a mark sits.
- **Deciding which marks to add** is the job of `DiacriticTransfer`
  (`wyrdcraeft.services.markup`), which aligns the source with the reference form
  letter by letter and copies missing marks onto the source.

There is a real bug at the second job. BT writes some diphthongs with the mark on
the second vowel (`eā`, `eō`, `iē`), the index's normal style puts it on the first
(`ēa`, `ēo`, `īe`). A source that already marks a diphthong in one style is
double-marked against a reference in the other: today
`DiacriticTransfer.transfer("leāst", "lēast")` returns `lēāst`.

## Decisions

1. **Lookup stays `normalize_old_english`.** `BTSpellingNormalizer` is not used
   for matching or for the transfer. It rewrites whole strings, it is blind to
   hyphens, and it belongs to the dictionary-parsing pipeline; the transfer
   already works letter by letter and is the right place to handle diphthongs.
2. **`DiacriticTransfer` treats a diphthong as one unit.** A diphthong is an
   adjacent pair `ea`, `eo`, `ie` or `io` in the reference, with no hyphen
   between the vowels and no mark other than a macron on either of them. For it:
   - if the source already marks either vowel of the pair, nothing is added to it;
   - if the source marks neither, the reference's macron for the pair is added to
     the **first** vowel (the normal style), whichever vowel the reference marked;
   - a macron on both reference vowels merges onto the first.

   A pair carrying any other mark is not a diphthong: in the index, `ēliŏtrŏpus`
   (a Latin loan where `io` is a hiatus) has a breve on the second vowel, and that
   breve stays on its own letter. (Found when the implementation plan was checked
   against the index: of 41,630 forms only `ēliŏtrŏpus` would have been wrongly
   changed by a rule that moved every kind of mark.)
3. **Hyphens in the reference are honored.** Vowels separated by a hyphen in the
   reference are never one diphthong, so `be-ōdrian` is not `bēodrian`. The
   source's own hyphens are irrelevant, as before.
4. **Mark patterns are diphthong-canonical.** Wherever ADR 0019 compares or
   collapses reference forms by marks, it uses the same canonical pattern (the
   diphthong mark on the first vowel), so BT-style and normal-style references
   count as the same.
5. **The source itself is never rewritten**, and marks are added in situ without
   changing base characters or adding hyphens (ADR 0015).
6. **Source capitalization always wins.** The index is lowercase; BT
   capitalization is never kept (it usually comes from a page-initial headword).
   A mark is added to whatever case the source letter already has.

## Considered options

- **Run `BTSpellingNormalizer` over both words (the earlier draft of this ADR).**
  Rejected: it solves the double-marking only by rewriting strings, and key lookup
  never needed it, since `normalize_old_english` already ignores marks.
- **Normalize diphthong style in the index data only.** Rejected: references
  imported later (ADR 0017) would reintroduce BT's style, and the source can be in
  either style anyway.

## Risk to design around

An unhyphenated reference cannot show a prefix boundary, so a reference such as
`beōdrian` would be read as the diphthong `eō`. BT usually hyphenates prefixes
(`be-ōdrian`), which decision 3 relies on; unhyphenated prefixed forms such as
`be-`/`ge-` words should be reviewed.

## Consequences

- Fixes the double-marking above (implemented in `DiacriticTransfer`, with
  `DiacriticTransfer.mark_pattern` as the shared helper ADR 0019 reuses). Of
  41,630 index forms only two (`īē-scēada`, `fēōnd-sēocnes`, a macron on both
  vowels) change under the merge, so existing output is otherwise unaffected.
- BT-style references no longer damage output, so the importer in
  [ADR 0017](0017-diacritic-cli-imports-bt-variants.md) can store variants as BT
  prints them without reintroducing the problem that produced the 28 outliers in
  ADR 0016. The index data may still hold both styles.
- The ambiguity report shows reference forms as stored, in whichever style.
