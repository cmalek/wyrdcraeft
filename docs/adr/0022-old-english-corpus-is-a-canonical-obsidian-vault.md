---
status: accepted
---

# The Old English corpus is a canonical Obsidian vault

## Context

The Dictionary of Old English (DOE) corpus is close to a complete inventory
of surviving Old English, but it is not available as a generally downloadable
corpus.  Its Cameron A--F catalogues still provide a useful baseline: 3,115
entries covering verse, prose, glosses and glossaries, runic inscriptions,
and non-runic inscriptions.  The Cameron identifiers are DOE-local catalogue
identifiers, however, and the catalogue entry is not always the same thing as
a work, manuscript witness, physical fragment, transcription, or downloadable
artifact.

The project needs a locally held corpus for computational linguistic research.
It must preserve provenance, retain every available witness and independent
transcription, distinguish manuscript readings from editorial reconstruction,
and remain browsable by a human.  It must also accommodate lost witnesses
known only through later copies or editions, such as *The Battle of Maldon*.

**Status:** accepted.

## Decision

1. **The canonical corpus is an Obsidian vault.**  Its root is configurable;
   the maintainer's current default is the sibling repository
   `/Users/cmalek/src/personal/old-english-corpus`.  The path is not part of
   the corpus data model.  Markdown notes and their Obsidian Properties are
   the metadata source of truth.  JSONL, CSV, reports, and snapshot manifests
   are derived exports, not competing canonical stores.

2. **The vault contains the corpus data as well as its metadata.**  The
   top-level layout is:

   ```text
   00 Indexes/
   Catalog Entries/
   Works/
   Witnesses/
   Physical Artifacts/
   Transcriptions/
   Source Artifacts/
   Acquisition Events/
   Curation Decisions/
   Snapshots/
   Corpus Files/
     Originals/
     Text/
     Quarantine/
   ```

   Folder location aids browsing but does not carry domain meaning.
   Properties and wikilinks carry identity and relationships.

3. **The vault is a Git repository and large artifacts use Git LFS.**
   `Corpus Files/Originals/` and `Corpus Files/Quarantine/` are LFS-managed.
   Markdown, Obsidian Bases, manifests, and ordinary UTF-8 transcription text
   remain in normal Git so their changes are reviewable.  Exceptionally large
   derived text may be moved to LFS through an explicit pattern.

4. **Each domain entity has its own note.**  The initial entity types are
   `catalog_entry`, `work`, `witness`, `physical_artifact`, `transcription`,
   `source_artifact`, `acquisition_event`, `curation_decision`, and
   `corpus_snapshot`.  Notes use filenames of the form
   `<stable-id> - <human-readable title>.md`.  The filename is immutable after
   creation so links remain stable; later title corrections change the
   `title` and `aliases` Properties rather than the path.  The stable ID is
   authoritative identity, while the readable suffix supports filesystem
   navigation.

5. **Corpus identifiers are independent of Cameron numbers.**  A baseline
   catalogue note retains its Cameron number as `doe_cameron_id`, used only as
   an internal cross-reference.  Works, witnesses, artifacts, and
   transcriptions receive separate corpus identifiers.  External shelfmarks,
   Ker and Gneuss--Lapidge numbers, Sawyer numbers, edition sigla, inscription
   catalogue numbers, repository identifiers, and similar identifiers are
   stored as typed identifiers with their issuing authority.

6. **Properties are authoritative metadata.**  Relationships are expressed
   as quoted Obsidian wikilinks in Properties.  Every entity note carries a
   schema version, stable ID, entity type, title, created date, and updated
   date.  Type-specific schemas add provenance, identifiers, relationships,
   quality, rights, coverage, and review state.  Note bodies contain the
   transcription, readable provenance, source quotations, and curatorial
   discussion; they do not restate Properties as another metadata authority.

   Unknown values are recorded explicitly; required applicable fields are not
   silently omitted.  The minimum provenance contract records:

   - the Cameron identifier, Cameron category, source text name, raw catalogue
     description, and raw citation for each imported catalogue entry;
   - work identity and whether a transcription is `witness_specific`,
     `edition_level`, or `composite`;
   - witness, physical object, shelfmark or object identifier, holding
     institution, and repository catalogue link when applicable;
   - transcription creator or editor and full bibliographic citation;
   - source URL, retrieval date, rights state, license or reuse statement,
     original format, checksum, acquisition method, and extraction method;
   - folio, page, line, face, or comparable locators supplied by the source;
     and
   - known representational loss, editorial intervention, uncertainty, and
     unresolved provenance.

   The source text name is a required primary discovery field even when no
   public transcription can be acquired.

7. **Transcription text normally lives in its transcription note.**  This
   makes it searchable, linkable, and readable in Obsidian without a plugin.
   Stable `<!-- corpus-text:start -->` and `<!-- corpus-text:end -->` comments
   delimit the exact computational payload in a note; its UTF-8 bytes are
   recorded in `payload_sha256`.  When the payload is a linked `.txt` or `.xml`
   file because the text is exceptionally large or structurally unsuitable for
   Markdown, that file and checksum are identified instead.  The untouched
   HTML, XML, PDF, ZIP, or other downloaded object is retained separately as
   the authoritative source artifact.

   Acquisition performs no normalization, tokenization, lemmatization, or
   analysis-specific transformation.  It preserves source characters,
   editorial notation, uncertainty, and intervention to the extent the
   transcription representation permits, and records any representational
   loss.  When extracting from a scholarly edition, the corpus payload contains
   the primary Old English text, supplied manuscript locators, and textual
   apparatus needed to interpret variants.  It excludes modern introductions,
   translations, indexes, and commentary unrelated to establishing the text.

8. **The source and the extraction are both retained.**  A source artifact is
   immutable, content-addressed evidence.  Its note records checksum, original
   format, local path, bibliographic citation, relationships to works and
   witnesses, and the Git LFS object identity when applicable.  Each retrieval
   has a separate acquisition-event note recording exact URL, retrieval date,
   rights state, license or reuse statement, access and acquisition methods,
   and observed checksum.  A derived transcription links its source artifact
   and records the extraction method.  A changed download becomes a new source
   artifact.  Byte-identical downloads share one stored artifact while
   retaining every acquisition event.

9. **The corpus distinguishes textual evidence levels.**  A transcription is
   classified as witness-specific scholarly transcription, scholarly
   edition-level text, repository transcription, traceable community
   transcription, unverified transcription, or suspect third-party OCR.
   Edition-level texts are useful corpus material but do not satisfy
   witness-level coverage.  Editorial emendations and reconstructions are
   preserved as presented and are never silently promoted to manuscript
   readings.

10. **Every distinct witness and independent transcription is retained.**
    Multiple transcriptions of one witness remain separate.  Lost witnesses,
    early modern transcripts, and printed copies are modeled as secondary
    witnesses when they preserve otherwise lost text.  Dispersed fragments
    receive separate physical-artifact notes and may be grouped under a
    reconstructed witness when scholarship supports that relationship.  A
    title match alone is never enough to merge entities.

    Witness enumeration is an independent research track rather than a
    by-product of finding downloadable text.  It consults public manuscript
    catalogues, repository descriptions, edition introductions, Ker and
    Gneuss--Lapidge references, inscription catalogues, and other scholarly
    witness inventories.  Each catalogue entry records whether its witness
    inventory is `unknown`, `provisional`, or `reviewed_complete`, together
    with the evidence and review date supporting that claim.

11. **Mixed-language context is preserved.**  When a source supplies the
    complete transcription, Latin context, lemma--gloss relationships, and
    layout or editorial markers are retained.  Modern translations are
    ancillary and do not count as corpus coverage.  For runic material, every
    supplied diplomatic rune sequence, normalized rune sequence,
    transliteration, transcription, word division, and uncertain reading is
    retained as a distinct representation.

12. **Acquisition is limited to publicly available material.**  Automated
    acquisition requires access without authentication, individual approval,
    paywall bypass, or protection bypass.  Account-gated, request-only,
    institution-only, and otherwise unavailable sources are recorded as
    research leads.  A manual-import workflow accepts files later obtained
    legitimately and applies the same provenance, rights, checksum,
    deduplication, and review rules.  The full corpus is private by default;
    only a rights-cleared subset may be exported for redistribution.

    A lead is still actionable metadata.  It records the likely edition or
    transcription, repository, shelfmark or object identifier, catalogue
    links, bibliographic citation, and plausible access route.  Availability
    states distinguish at least `image_only`, `scan_only`, `account_gated`,
    `request_only`, `institution_only`, and `no_public_text`.

13. **Discovery is broader than promotion.**  Automated discovery may place
    candidates in `Corpus Files/Quarantine/`, but a candidate does not count
    toward coverage until its identity, provenance, evidence level, and
    work/witness mapping are reviewed.  Manual merges, splits, mappings,
    rejections, and reversals are auditable curation decisions with evidence,
    author, date, and rationale.

14. **No OCR or HTR is performed by this corpus workflow.**  Image-only and
    scan-only discoveries are catalogued as leads without bulk image download.
    Existing third-party OCR may be downloaded, but it is marked
    `suspect_unverified_ocr` and cannot improve human-transcription coverage.
    OCR is outside this corpus workflow, which has no runtime dependency on an
    OCR pipeline.

15. **Obsidian Bases provide operational views.**  Built-in `.base` files,
    without a Dataview dependency, expose baseline coverage, parse anomalies,
    multi-witness entries, quarantine, suspect OCR, missing public text,
    witnesses without transcriptions, rights-cleared artifacts, checksum
    conflicts, and unresolved curation decisions.  Index notes embed these
    views.

16. **Validation gates snapshots and exports.**  Validation rejects duplicate
    corpus IDs, invalid controlled values, malformed dates, missing required
    provenance, broken required relationships, invalid Properties, source
    checksum drift, and transcription-payload checksum drift.  Schema
    migrations are explicit and preserve human edits.  A named corpus snapshot
    records the full Git commit ID plus a manifest of transcription IDs and
    payload checksums, source-artifact checksums, and Git LFS object identities
    used by an analysis.  A snapshot is valid only when every manifest entry is
    retrievable from that commit and the required LFS objects are available.

17. **`wyrdcraeft` manages the vault through a CLI-first workflow.**  Models
    live in semantically named modules under `wyrdcraeft.models`; acquisition,
    vault validation, source adapters, exports, and curation workflows live in
    cohesive services under `wyrdcraeft.services`; commands and human display
    live under `wyrdcraeft.cli`.  Importers may create notes and propose
    changes, but must not silently overwrite human-curated Properties.

18. **The first implementation milestone is inventory-only.**  It initializes
    the vault repository and Git LFS, installs the note schemas, templates,
    validation, indexes, and Bases, then parses the six Cameron A--F source
    documents into exactly 3,115 `catalog_entry` notes: 202 A, 2,370 B, 286 C,
    150 D, 46 E, and 61 F.  Every raw entry is preserved verbatim; text name
    and cited source are extracted conservatively; multi-witness,
    multi-object, fragment, and parsing ambiguities are flagged.  The milestone
    performs no corpus downloads and no OCR, and stops for human review.

    Before parsing, the importer copies the exact six user-supplied Cameron
    A--F documents into `Corpus Files/Originals/DOE Cameron Catalogue/` and
    writes a checked-in input manifest mapping A through F to local filename,
    original supplied path, byte count, and SHA-256 checksum.  Parsing uses the
    retained copies in deterministic A--F order.  It fails on a missing,
    ambiguous, or checksum-mismatched input unless the maintainer explicitly
    updates the input manifest.

19. **Acquisition after the inventory is breadth-first, then witness-deep.**
    The first source feasibility and acquisition targets are the downloadable
    *Anglo-Saxon Poetic Records* and York--Toronto--Helsinki Parsed Corpus of
    Old English Prose as edition-level bootstrap corpora.  Witness-oriented
    refinement follows through Old English Poetry in Facsimile, RuneS,
    Electronic Sawyer, Early English Laws, the Oxford Text Archive, public
    repository projects, and public-domain editions.  Source-specific access,
    formats, rights, and mapping behavior are verified before an adapter is
    implemented.

20. **Completeness remains multidimensional.**  Reports distinguish baseline
    entries with any local text, human text, suspect OCR only, or leads only;
    known witnesses; witnesses with local transcriptions; edition-only
    coverage; coverage by A--F category and evidence level; and extended
    material outside the DOE baseline.  There is no single percentage that
    conflates edition coverage with witness completeness.

    DOE baseline membership is preserved exactly as imported.  Extended-corpus
    material may be admitted when a credible scholarly source identifies it as
    wholly or partly Old English, including disputed linguistic boundaries,
    early Middle English or Old Saxon overlap, and uncertain runic readings.
    Such records preserve the proposed classification, source, evidence, and
    uncertainty rather than forcing a false binary decision.

## Considered options

- **Keep JSON or a database canonical and generate an Obsidian view.**
  Rejected: it gives curators two representations and makes edits in the
  browsable vault disposable or subject to overwrite.
- **Keep large artifacts outside the vault.**  Rejected: the corpus should be
  browsable as one collection.  Git LFS provides the agreed storage boundary.
- **Use one note per Cameron entry and nest all other metadata inside it.**
  Rejected: Properties do not provide a good nested relational model, and one
  catalogue entry may map to many works, witnesses, fragments,
  transcriptions, and source artifacts.
- **Use Cameron numbers as universal IDs.**  Rejected: they are internal DOE
  catalogue identifiers and do not cover extended material or distinguish
  the corpus entities.
- **Treat a normalized or critical edition as witness-complete.**  Rejected:
  edition-level text is valuable, but it cannot stand in for each physical or
  lost witness.
- **Run OCR when only a scan is available.**  Rejected: tested Old English OCR
  output is not sufficiently accurate for automatic corpus admission.  Existing
  third-party OCR may still be retained as explicitly suspect evidence.
- **Require a graphical curator before inventory work.**  Rejected: a CLI,
  Properties, Markdown, and Obsidian Bases are sufficient for the first
  workflow and keep the initial surface small.

## Consequences

The corpus becomes a second repository with a stable, human-readable domain
graph and a potentially large Git LFS footprint.  Vault changes are real data
changes and require validation and review.  `wyrdcraeft` gains a configurable
corpus-vault boundary and services for note generation, validation,
acquisition, curation, and export, but it does not gain OCR dependencies.

The inventory can deliver a measurable first checkpoint without pretending
that catalogue coverage is manuscript coverage.  Later source adapters can
add broad edition-level text quickly while witness research proceeds
independently.  Computational analyses must cite a named snapshot rather than
an evolving working tree.
