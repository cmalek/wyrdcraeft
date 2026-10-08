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
3. **The importer never overwrites an existing key.** Conflicts are reported,
   not resolved.
4. **Junk is filtered, real short words are kept.** Citation sigla and
   fragments the parser extracts as "variants" (`Ps`, `Rdr`, `v`, `B`) are
   junk. `aa` is a real word (a variant of `ā`) and must be kept, so a minimum
   length rule is not acceptable. The filter rules are still open.
5. **Hand-adding a variant uses plain `diacritic add`.** There is no
   `--variant-of` flag: the index has no headword link, so the flag would only
   validate that a headword exists and then store an ordinary entry.

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

- Ordering: the importer must not ship before ADR 0020, or
  must normalize diphthong style on import (see facts).
- The junk filter (which parser variants are real words).
- Collision policy: ignore eth/thorn-only differences; decide whether a variant
  carrying marks the existing unique entry lacks becomes a second option
  (making the key ambiguous) or is only reported.

## Consequences

- The importer makes the repair in ADR 0016 repeatable and reviewable.
- The first real run will mostly produce a review report, not a large automatic
  change.
