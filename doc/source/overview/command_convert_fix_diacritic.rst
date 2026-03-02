``wyrdcraeft convert fix-diacritic``
====================================

This page documents the diacritic-restoration workflow requested as
``wyrdcraeft convert fix-diacritic``.

Compatibility note
------------------

In this codebase, the currently shipped command path is:

.. code-block:: bash

    wyrdcraeft source mark-diacritics INPUT OUTPUT --ambiguities-output FILE

The workflow and data pipeline described below are the same ones used by that
command path.

Purpose
-------

The command applies attested Old English diacritics in unmarked text by applying:

- macrons from a Bosworth-Toller-derived canonical index
- palatalization marks for ``g`` (``ġ``) and ``c`` (``ċ``)

It also emits an ambiguity report when a token has multiple valid macron
candidates.

Canonical list construction
---------------------------

The canonical macron list is generated from a Bosworth-Toller OCR source file
(``data/oe_bt.txt``) using the builder script. The source of this file is [github:madeleineth/btc_anglo_saxon](https://github.com/madeleineth/btc_anglo_saxon/blob/master/db/oe_bosworthtoller.txt.bz2):

Our internal macron index was originally built from this source file using the
builder script:

.. code-block:: bash

    python data/tools/build_macron_index.py

Build pipeline summary:

1. Read each source line and split with ``@``.
2. Extract the first bold headword from ``<B>...</B>``.
3. Normalize the candidate keys (see normalization rules below).
4. Aggregate attested marked forms per normalized key.
5. Partition results:
   - one attested form -> ``unique``
   - multiple attested forms -> ``ambiguous``
6. Write payload to:
   ``wyrdcraeft/etc/diacritic/oe_bt_macron_index.json``.

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

- marked output text file
- JSON ambiguity report with line number, word number, original token, options

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
