---
status: accepted
amends: 0015
---

# Macron index: variants are their own entries; the packaged index is repaired, not regenerated

Amends [ADR 0015](0015-mark-diacritics-is-additive-transfer.md), which makes
`source mark-diacritics` an additive transfer. That change exposed that the
macron index itself contained wrong entries, and fixing them required two
decisions that look wrong in isolation. Do not reverse them without reading
this.

## Decisions

1. **A variant gets its own entry, never the first headword's form.**
   `MacronApplicator.build_index_from_bt` used to map every variant in an
   entry's third `@` field to the entry's first bold headword. That produced
   entries such as `ærþling` → `ǣrst` and `acmuman` → `ā-cuman` (81 unique
   entries and 101 ambiguous options in the packaged index). It now adds a
   variant only with the form(s) the entry's bold heading spells out for that
   key. A variant the heading does not spell out is not indexed (`barr` is
   now unknown, not `bār`). Two heading forms with the same key (`a-bacan`,
   `ā-bacan`) are both kept, which makes the key ambiguous.

2. **The packaged index is repaired in place and is never regenerated from
   `oe_bt.txt`.** `wyrdcraeft/etc/diacritic/oe_bt_macron_index.json` is
   curated data, not a build artifact:
   - It holds hand-made disambiguation state (`ambiguous_completed`,
     `ambiguous_metadata`) and manual additions made through
     `diacritic add` / `diacritic-disambiguate`.
   - A trial rebuild from the bundled `oe_bt.txt` disagreed with 4,071 existing
     entries: 4,066 only in diphthong style (the bundled text uses BT's `eā`/`eō`,
     the index the normal `ēa`/`ēo`; for example `abbod-leāst` against
     `abbod-lēast`) and 5 where the rebuild has fewer marks (`a-bacan` against
     `ā-bacan`). The index's `meta.source_path` points at a different checkout,
     so it was probably built from a differently cleaned copy (an inference).

   The repair therefore (a) pruned entries whose display form does not
   normalize to their own key, leaving hand-curated ambiguous entries
   (`beinnan`, `blac`, `cinn`) as curated, and (b) added variants the index
   lacked from the bundled source, never overwriting an existing key. Net
   effect: 39,207 → 39,208 unique after the prune (1,049 → 964 ambiguous), then
   39,670 unique and 967 ambiguous after the additions.

3. **One-time diphthong fix (28 entries).** The original index contained none of
   these forms: all 28 were introduced by this repair's own import of the bundled
   source, which writes BT's other style of diphthong marking (`eā`, `eō`, `iē`).
   They were moved to the normal first-vowel style
   (`ēa`, `ēo`, `īe`) by an explicit, user-approved list (for example
   `geōmore` → `gēomore`, `ge-seōwan` → `ge-sēowan`). It was a list, not a
   rule, because a hyphen-free form can hide a prefix boundary (`be-ōdrian`
   is not `bēodrian`); a mechanical rewrite must never cross a hyphen and
   needs review for forms starting with a prefix such as `be`/`ge`.

## Considered options

- **Regenerate the index with the fixed builder.** Rejected: destroys curation
  and manual additions and loses a few macrons (see above). The 4,066 diphthong
  style differences alone would not justify this; the curated state does. Anyone tempted to run
  `bin/build_macron_index.py` and commit the result: do not.
- **Keep variant → headword mapping and let alignment reject bad ones.**
  Rejected: the wrong forms stay in the index and in ambiguity reports.
  Alignment (ADR 0015) remains as a backstop and reports leftovers in
  `.unaligned`.
- **Map a variant to the headword when only the spelling differs (`barr` →
  `bār`).** Rejected: the macron pattern belongs to the headword's spelling,
  so under additive transfer it cannot be copied onto a different spelling.

## Consequences

- `bin/build_macron_index.py` produces a fresh index that lacks curation; treat
  its output as input to a merge, not as a replacement for the packaged file.
- Hand-curated entries may still fail alignment and appear in `.unaligned`.
  That is expected; they are left as the user curated them.
- Importing from the bundled source leaks BT's diphthong style into the index
  (the 28 above). With ADR 0020 the transfer handles either style, so a future
  import does not need to normalize it.
- Not refreshed: the 4,071 existing entries that differ from the bundled source.
  4,066 are diphthong style only; the index's normal style is kept.
