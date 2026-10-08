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
- **--unaligned-output**: default ``stem.unaligned.extension`` (e.g. ``poem.unaligned.txt``).

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

The command adds diacritics to Old English text while changing the source as
little as possible. It only ever *adds* combining marks: it never removes or
replaces a character, never converts ``ð`` to ``þ`` (or back), never adds or
removes a hyphen, and never changes case. Marks already in the source are kept
even when they disagree with the index. It adds:

- macrons (and the few other marks) from a Bosworth-Toller-derived canonical
  index, copied onto the matching source letters
- palatalization dots for ``g`` (``ġ``) and ``c`` (``ċ``)

It also emits:

- an **ambiguity report** when a token has multiple valid macron candidates that differ in their marks (with part-of-speech and definitions per option when available in the index);
- an **unknown-words report** listing lexical tokens that were not found in the macron index;
- an **unaligned-words report** listing tokens that are in the index but whose index form cannot be matched letter-for-letter to the source (``ð``/``þ``, case, and hyphens/dashes are ignored when matching). These tokens are left unchanged. The usual cause is an index entry that maps a variant spelling to a different headword.

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

   - if key in ``unique``: align the index form with the source token and
     copy its marks onto the source letters (the index form never replaces the
     source token); if the letters cannot be aligned, keep the source token and
     emit an unaligned row. A diphthong (``ea``, ``eo``, ``ie``, ``io``, not
     separated by a hyphen in the index form) is treated as one unit whose macron
     goes on the first vowel; a source that already marks either vowel gets
     nothing added to it.
   - if key in ``ambiguous`` and every option has the same letters and marks
     (hyphens, case, ``ð``/``þ`` and diphthong style ignored): apply it like a
     unique entry and emit no ambiguity row. A key the user marked completed
     is never treated this way
   - if key in ``ambiguous`` otherwise: keep source token, emit ambiguity row with options

3. Apply ``g`` palatalization rules (a ``g`` before a back vowel stays velar,
   e.g. *stīgan*, *wiga*).
4. Apply ``c`` palatalization rules (historically informed: ``c`` before /i, iː/ or
   word-initial before other front vowels, and ``c`` after /i/, /i:/ unless a back
   vowel follows). A pre-i-mutation “only back” check and a blocklist avoid
   palatalizing ``c`` when the adjacent front vowel derives from i-mutation (e.g.
   *cyning*). The ``c`` of ``sc`` is never dotted.

Tokens keep their combining marks, so text in decomposed (NFD) form is handled
without being split, and en/em dashes between word parts are treated like
hyphens.

The command writes:

- **Marked output text file** (default: ``stem.fixed.extension``).
- **Ambiguity report** (default: ``stem.anomalies.extension``): JSON array of objects with ``line_number``, ``word_number``, ``word``, and ``options``. Each option is an object with ``form`` (the candidate marked form), and when available from the index, ``part_of_speech`` and ``definitions``, so POS and meaning are attached to each choice for context when deciding.
- **Unknown-words report** (default: ``stem.unknown.extension``): JSON array of objects with ``line_number``, ``word_number``, and ``word`` for each token not found in the macron index.
- **Unaligned-words report** (default: ``stem.unaligned.extension``): JSON array of objects with ``line_number``, ``word_number``, ``word``, and ``index_form`` for each token left unchanged because the index form could not be aligned to it.
