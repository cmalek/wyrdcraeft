``wyrdcraeft source mark-diacritics``
=====================================

This page documents the diacritic-restoration workflow requested as
``wyrdcraeft source mark-diacritics``.

Compatibility note
------------------

In this codebase, the currently shipped command path is:

.. code-block:: bash

    wyrdcraeft source mark-diacritics INPUT [OUTPUT] [OPTIONS]

All output paths are optional. When omitted, they default to the input
directory using the input filename stem and extension:

- **OUTPUT** (marked text): default ``stem.fixed.extension`` (e.g. ``poem.txt`` → ``poem.fixed.txt``).
- **--ambiguities-output**: default ``stem.anomalies.extension`` (e.g. ``poem.anomalies.txt``).
- **--unknown-output**: default ``stem.unknown.extension`` (e.g. ``poem.unknown.txt``).

Example with defaults (only input required):

.. code-block:: bash

    wyrdcraeft source mark-diacritics source.txt

Example with explicit paths:

.. code-block:: bash

    wyrdcraeft source mark-diacritics source.txt output.txt --ambiguities-output source.anomalies.json --unknown-output source.unknown.json

The workflow and data pipeline described below are the same ones used by that
command path.

Purpose
-------

The command applies attested Old English diacritics in unmarked text by applying:

- macrons from a Bosworth-Toller-derived canonical index
- palatalization marks for ``g`` (``ġ``) and ``c`` (``ċ``)

It also emits:

- an **ambiguity report** when a token has multiple valid macron candidates (with part-of-speech and definitions per option when available in the index);
- an **unknown-words report** listing lexical tokens that were not found in the macron index.

Normalization rules
-------------------

Normalization is intentionally conservative and stable:

- lowercase input
- replace ``ð`` with ``þ``
- decompose Unicode and remove combining marks
- remove internal hyphen/dash characters
- preserve core Old English letters such as ``æ`` and ``þ``

These rules are used both while building the canonical list and while
normalizing input tokens at runtime for lookup.

Runtime processing flow
-----------------------

For each lexical token:

1. Normalize token with the rules above.
2. Lookup in macron index:
   - if key in ``unique``: apply deterministic marked form
   - if key in ``ambiguous``: keep source token, emit ambiguity row with options
3. Apply ``g`` palatalization rules.
4. Apply ``c`` palatalization rules (historically informed: ``c`` before /i, iː/ or
   word-initial before other front vowels, and ``c`` after /i/, /i:/ unless a back
   vowel follows). A pre-i-mutation “only back” check and a blocklist avoid
   palatalizing ``c`` when the adjacent front vowel derives from i-mutation (e.g.
   *cyning*). ``sc`` → ``sċ`` is handled in a separate follow-up.

The command writes:

- **Marked output text file** (default: ``stem.fixed.extension``).
- **Ambiguity report** (default: ``stem.anomalies.extension``): JSON array of objects with ``line_number``, ``word_number``, ``word``, and ``options``. Each option is an object with ``form`` (the candidate marked form), and when available from the index, ``part_of_speech`` and ``definitions``, so POS and meaning are attached to each choice for context when deciding.
- **Unknown-words report** (default: ``stem.unknown.extension``): JSON array of objects with ``line_number``, ``word_number``, and ``word`` for each token not found in the macron index.

Maintaining the canonical list
------------------------------

The canonical list is curated with:

.. code-block:: bash

    wyrdcraeft diacritic disambiguate

Maintenance loop:

1. Review each normalized key in ``ambiguous``.
2. Either:
   - promote one form into ``unique`` (resolving the ambiguity), or
   - annotate forms in ``ambiguous_metadata`` with POS code and modern meaning.
3. Persist changes immediately after each commit.

This keeps the canonical index maintainable over time while preserving
provenance for unresolved lexical ambiguity.
