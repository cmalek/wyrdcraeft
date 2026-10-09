---
status: proposed
---

# `diacritic` CLI imports BT variants as their own index entries

Follows [ADR 0015](0015-mark-diacritics-is-additive-transfer.md) and
[ADR 0016](0016-macron-index-variants-are-own-entries-and-index-is-repaired-not-regenerated.md).
After ADR 0016 nothing repeatable adds BT variants to the packaged macron index;
the 462 variants added so far came from a throwaway script that read only the
third `@` field of `oe_bt.txt`. This ADR records the importer the user wants.
Nothing here is implemented yet. Hand-editing commands are in
[ADR 0018](0018-diacritic-write-commands-warn-on-non-normalizing-forms.md).

## Decisions

1. **A repeatable importer replaces the one-off script.** A new command
   (working name `diacritic import-variants`) reads `oe_bt.txt`, extracts
   variants with the existing dictionary parser (`BTLineParser`; it already
   handles compound headings such as `mægþ, mægeþ;` and pre-POS variants) and
   adds each as its own top-level entry keyed by its own normalized spelling.
   Dry run by default; an explicit flag applies the change through the existing
   atomic index writer.
2. **A variant's spelling is what BT prints, lowercased.** If BT prints `barr`
   with no macron, `barr` is correct and is stored without one. Marks are never
   copied from the headword onto a variant. BT capitalization is never kept: it
   usually comes from a headword that starts a page. (Source capitalization
   always wins when marks are applied to text; see ADR 0015.)
3. **The importer never changes an existing key.** Conflicts are reported, not
   resolved (see decision 6).
4. **Junk is filtered, real short words are kept.** Citation sigla and
   fragments the parser extracts as "variants" (`Ps`, `Rdr`, `v`, `B`) are
   junk. `aa` is a real word (a variant of `ā`) and must be kept, so a minimum
   length rule is not acceptable. The filter has two layers (decided by the
   user):
   - **Hard rejects**, never imported and only counted: a key that appears as a
     variant under 3 or more different headwords across the BT source (`v`,
     `ii`, `cf`, `the`, `wrt`, …: 147 keys, and 4,027 of the 9,932 candidate
     rows are `v` alone); a token in a hand-edited stoplist,
     `wyrdcraeft/etc/diacritic/bt_variant_stoplist.txt` (citation sigla and Roman
     numerals that the frequency rule misses; extend it as review reports show
     more); an ALL-CAPS token of 2 or more letters (`UNCERTAIN`,
     `APPLE-SHREDS`); a hyphenated token whose last segment is one letter, a
     truncated fragment (`on-g`, `ge-ǣ`, `ofer-f`). The checks use BT's
     spelling before lowercasing.
   - **Similarity gate.** Only a variant that is a spelling of its own headword
     is imported automatically: the edit distance between the two normalized
     keys is at most `max(2, len(headword key) // 3)`. This keeps `aa`,
     `tiolung`/`tilung`, `senu`/`seonu` and drops `The`, `with`, `classes`.
     Variants that pass the hard rejects but not the gate (real inflected forms
     such as `bacest` for `bacan`, and English words from BT's notes) go to the
     review report, not the index, because the two cannot be told apart without
     an English word list.
5. **Hand-adding a variant uses plain `diacritic add`.** There is no
   `--variant-of` flag: the index has no headword link, so the flag would only
   validate that a headword exists and then store an ordinary entry.

6. **Collision policy: report only** (decided by the user). For a variant that
   passes decision 4 and whose key already exists, or whose key another variant
   in the same run also proposes with different marks, the comparison uses
   `DiacriticTransfer.mark_pattern` after standard elements (ADR 0019), so
   hyphens, case and eth/thorn never count:
   - same marks, or the variant has fewer marks: skipped, counted only (existing
     entries win; the index only ever gains marks);
   - the variant has marks the existing unique entry lacks (`bide` against
     `bīde`), conflicting marks, or a mark pattern that is new for an
     undecided ambiguous key: listed in the review report with both forms and the
     BT headword. The importer does not make the key ambiguous and does not
     upgrade the existing form; the user settles each case with
     `diacritic add`;
   - a key in `ambiguous_completed` is never touched or proposed;
   - two new variants for the same key with different mark patterns: neither is
     added; both are listed for review.

   Measured (BT source with the current index, gated variants, distinct
   spelling per key): 4,301 collide with a unique entry, of which 4,084 have the
   same marks, 138 have fewer, 75 have more and 4 conflict; 236 collide with an
   ambiguous key, of which 202 match an existing option, 33 are completed keys
   and 1 is a new pattern; 10 of 2,449 importable new keys have conflicting
   variants. About 90 cases need review, against about 2,440 keys added.

## Facts the implementation must respect

- `BTLineParser.parse` already passes variants through `BTSpellingNormalizer`
  (acute→macron, diphthong marks moved). The importer needs the raw variants
  (`_split_headword_forms` and `_extract_variants`, currently private), not
  `ParsedBTLine.variants`, or decision 2 is silently violated. Because the
  transfer treats a diphthong as one unit (ADR 0020), BT-style diphthong marks in
  a stored variant do not corrupt output, so the importer does not need to flag
  them. See the risk in ADR 0020 about unhyphenated prefix forms.
- On the bundled source the parser yields 19,480 variants: 9,931 with keys not
  in the index (including the junk above), 7,141 equal to an existing unique
  entry, 1,745 colliding with a unique entry whose spelling differs, and 663
  colliding with an ambiguous key. Many of the 1,745 are only eth/thorn
  differences (`ðū` against `þū`) and are not real conflicts; others carry marks
  BT prints that the index lacks (`un-ābīgendlīc` against `un-ābigendlīc`).
- Index forms are stored lowercase; parser variants keep BT capitalization.
- The bundled source writes BT's diphthong style (`eā`, `eō`); the original
  index had none of it. All 28 such forms later found in the index came from the
  throwaway import, so importing "as BT prints" reintroduces them (ADR 0016).
  Decision 2 is therefore only safe once ADR 0020 (the transfer treats a
  diphthong as one unit) is implemented, or if the importer normalizes diphthong
  style itself, never across a hyphen.
- The counts above were measured after the 462 throwaway additions, so the
  "equal to an existing entry" figure includes them.

## Considered options

- **Transfer the headword's macrons onto a variant (`barr` → `bārr`).**
  Rejected by the user: BT's spelling of the variant is authoritative.
- **Best-effort mapping of marks onto differing vowels (`blǣc` → `blāc`).**
  Rejected: some results would be wrong and undetectable.
- **Run stored variants through `BTSpellingNormalizer`.** Rejected: store what BT
  prints; the transfer handles either diphthong style (ADR 0020).
- **Regenerate the index from `oe_bt.txt`.** Rejected in ADR 0016.
- **A `--variant-of` flag on `add`.** Rejected: no headword link to record.

## Open questions

- Ordering is resolved: ADR 0020 is implemented, so the importer may store BT's
  diphthong style as printed.
- The review report's file name and format, and the command name
  (`diacritic import-variants` is a working name).

## Consequences

- The importer makes the repair in ADR 0016 repeatable and reviewable.
- The first real run adds roughly 2,450 keys and lists about 90 collisions plus
  the rejected-by-gate variants (roughly 1,900 keys) for review, so it produces
  both a real change and a review report.
