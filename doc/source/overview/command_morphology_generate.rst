``wyrdcraeft morphology generate``
==================================

This command generates Old English morphology forms using the migrated Python
implementation from Ondřej Tichý's original Perl-based generator workflow.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft morphology generate [OPTIONS]

Options
-------

- ``--data-dir PATH``: default directory for morphology data files.
- ``--dictionary PATH``: dictionary file to process.
- ``--manual-forms PATH``: manual forms input file.
- ``--verbal-paradigms PATH``: verbal paradigms file.
- ``--prefixes PATH``: prefix list file.
- ``--output PATH``: output TSV path.
- ``--limit INTEGER``: process only the first N words (ignored in full mode).
- ``--enable-r-stem-nouns``: enable opt-in non-parity r-stem noun generation.
- ``--full / --no-full``: full dictionary generation mode.

Defaults
--------

You should not need to provide any of the ``--data-dir``, ``--dictionary``, ``--manual-forms``, ``--verbal-paradigms``, or ``--prefixes`` paths explicitly, as the generator will load the data from the packaged files under ``wyrdcraeft/etc/morphology/``.

Only provide these paths if you need to override the default paths.


Examples
--------

.. code-block:: bash

    # Generate subset output with limit
    wyrdcraeft morphology generate --limit 250 --output output.tsv

    # Generate full output
    wyrdcraeft morphology generate --full --output morphology_full.tsv

Background
----------

The morphology generator is based on the work of Ondřej Tichý, whose thesis and
2017 paper describe a semi-automatic morphological analyser for Old English
(roughly 700–1100). The goal is to support corpus research—lemmatization and
morphological tagging—where diachronic corpora are sparsely annotated and
manual tagging is impractical.

The approach has three phases. First, a base dictionary is built with
morphological metadata for each lemma. Second, a **forms generator** produces
all inflected forms from those lemmas using morphological rules and assigns
grammatical categories to each form, yielding a dictionary of forms. Third, an
analyzer matches text tokens to this form dictionary to produce lemmatization
and morphological analysis. The design is deliberately lemma-based (rather than
root- or stem-based) so that building the base lexicon is feasible; the
generator must be able to derive every inflected form from any lemma using the
rules.

Old English morphology in this tool is described in a pragmatic,
machine-oriented way. For example, the implementation uses many verb classes
(e.g. 132 in the original design) instead of the traditional “seven strong,
three weak” summary, while following traditional grammars (such as Wright &
Wright, Campbell) where possible and collapsing distinctions that are below
the noise of scribal, dialectal, and diachronic variation in the texts.

The base lexicon comes from **Bosworth–Toller** (*An Anglo-Saxon Dictionary*,
1921), enriched with morphological information from **Wright & Wright**, *Old
English Grammar* (1914). Paradigm example words are taken from the Wright
grammar index; manual paradigm data for verbs (including infixation) are held
in a separate table. On test samples of Old English text (around 2,500 words
across ten excerpts), the original tool achieved about 95% recall; with
variation filters enabled, recall rose to about 97.3%. Performance is best on
West Saxon prose from around the year 1000; dialect and verse pose greater
difficulty.

Implementation overview
-----------------------

The generator pipeline (based on Tichý’s paper) works as follows:

1. **Load and standardize data** — Load the dictionary (BT-derived), manual
   forms, verbal paradigms file, and prefix list. Normalize script (e.g.
   unify thorn and edh) and compute derived fields (syllable count, stem
   length).

2. **Assign paradigms** — Match lexicon entries to Wright paradigm example lemmas
   (with word-class and prefix handling). Propagate paradigm from grammar
   references to further lemmas and composites. Use morphophonological
   analysis for unassigned items (e.g. adjectives). Remaining items get
   defaults: e.g. strong verbs → *helpan* type, weak → *déman*; nouns by
   gender and stem length → *stán*, *ār*, *word*, *hof*.

3. **Generate forms** — By word class: manual forms first, then verbs,
   adjectives, adverbs, numerals, nouns. Reuse inflection patterns across
   classes (e.g. participles generated with verbs then declined with
   adjectives). For verbs: analyze stem, replace root vowel (ablaut/umlaut),
   add endings. Emit one TSV line per form (and sometimes a second line with
   incremented probability when a spelling variant is produced).

4. **Output** — TSV with fixed columns (see below).

How to use the output
---------------------

Quick reference
---------------

The final output is a TSV (Tab-Separated Values) file.  Use the **form** column
for the surface spelling of each generated word form.  Use **function** for the
morphosyntactic tag (e.g. case, number, tense).  Use **wright** for the
inflectional paradigm name (the example word from Wright’s grammar that the
generator follows). For a list of Wright paradigm names and which ones the
generator implements, see :doc:`wright_paradigms`.

.. warning::
    The ouput file is **huge**.  There will be on the order of 15 million lines
    in the full output file.

Generator output format
-----------------------

Output is **TSV** (tab-separated), UTF-8, one row per generated form. Some
forms produce an extra line when a spelling variant is generated (e.g. when
double consonants are reduced).

Column order and meaning:

.. list-table::
   :header-rows: 1
   :widths: 15 50

   * - Column
     - Meaning
   * - ``counter``
     - Running index of the form line (1-based).
   * - ``formi``
     - Normalized form used for matching (e.g. doubled consonants reduced).
   * - ``BT``
     - Bosworth–Toller dictionary identifier for the headword.
   * - ``title``
     - Lemma / dictionary headword (e.g. with prefix: *æt-swymman*).
   * - ``stem``
     - Stem used for this form (may differ from lemma after prefix stripping).
   * - ``form``
     - Surface form as generated (spelling with endings).
   * - ``formParts``
     - Decomposition (e.g. stem + ending, or hyphenated segments).
   * - ``var``
     - Variant index or flag (e.g. 0/1 for alternants).
   * - ``probability``
     - Rank or preference when multiple analyses exist (e.g. 0, 1, 2).
   * - ``function``
     - Morphosyntactic function tag (e.g. SgMaNo, PoPlMaGe, PaInSg1, Inf).
   * - ``wright``
     - Wright paradigm name (e.g. *bindan*, *blinda*, *stán*).
   * - ``paradigm``
     - Internal paradigm label (may match wright or be a subclass).
   * - ``paraID``
     - Paradigm or verb-class ID (numeric where applicable).
   * - ``wordclass``
     - Part of speech: verb, adjective, noun, adverb, numeral, pronoun, participle, etc.
   * - ``class1``
     - First classification (e.g. strong/weak for verbs).
   * - ``class2``
     - Second classification (e.g. tense or subclass).
   * - ``class3``
     - Third classification (e.g. verb subclass).
   * - ``comment``
     - Optional comment or note.

The same field set is used in the Python reference snapshots (JSONL), with
``counter`` omitted in stored records.

Function codes (glossary)
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``function`` column contains morphosyntactic tags. Codes are built from
abbreviations for number (``Sg`` = singular, ``Pl`` = plural), gender (``Ma`` = masculine,
``Fe`` = feminine, ``Ne`` = neuter), and case (``No`` = nominative, ``Ac`` = accusative,
``Ge`` = genitive, ``Da`` = dative, ``Is`` = instrumental). Adjective codes add a degree
prefix: ``Po`` = positive, ``Co`` = comparative, ``Sp`` = superlative. Verb codes use
a variety of different abbreviations (see below).

Nouns
^^^^^

.. list-table::
   :header-rows: 1
   :widths: 12 50

   * - Code
     - Meaning
   * - ``SgMaNo``
     - Masculine singular nominative
   * - ``SgMaAc``
     - Masculine singular accusative
   * - ``SgMaGe``
     - Masculine singular genitive
   * - ``SgMaDa``
     - Masculine singular dative
   * - ``PlMaNo``
     - Masculine plural nominative
   * - ``PlMaAc``
     - Masculine plural accusative
   * - ``PlMaGe``
     - Masculine plural genitive
   * - ``PlMaDa``
     - Masculine plural dative
   * - ``SgFeNo``
     - Feminine singular nominative
   * - ``SgFeAc``
     - Feminine singular accusative
   * - ``SgFeGe``
     - Feminine singular genitive
   * - ``SgFeDa``
     - Feminine singular dative
   * - ``PlFeNo``
     - Feminine plural nominative
   * - ``PlFeAc``
     - Feminine plural accusative
   * - ``PlFeGe``
     - Feminine plural genitive
   * - ``PlFeDa``
     - Feminine plural dative
   * - ``SgNeNo``
     - Neuter singular nominative
   * - ``SgNeAc``
     - Neuter singular accusative
   * - ``SgNeGe``
     - Neuter singular genitive
   * - ``SgNeDa``
     - Neuter singular dative
   * - ``PlNeNo``
     - Neuter plural nominative
   * - ``PlNeAc``
     - Neuter plural accusative
   * - ``PlNeGe``
     - Neuter plural genitive
   * - ``PlNeDa``
     - Neuter plural dative

Adjectives
^^^^^^^^^^

Adjective codes use the same case/gender/number suffixes (e.g. SgMaNo, PlFeDa)
with a degree prefix: **Po** (positive), **Co** (comparative), **Sp** (superlative).
The instrumental case **Is** appears only in the singular (e.g. PoSgMaIs = positive
masculine singular instrumental). Examples:

.. list-table::
   :header-rows: 1
   :widths: 14 50

   * - Code
     - Meaning
   * - ``PoSgMaNo``
     - Positive masculine singular nominative
   * - ``PoSgMaAc``
     - Positive masculine singular accusative
   * - ``PoSgMaGe``
     - Positive masculine singular genitive
   * - ``PoSgMaDa``
     - Positive masculine singular dative
   * - ``PoSgMaIs``
     - Positive masculine singular instrumental
   * - ``PoSgFeNo``, ``PoPlMaNo``, etc.
     - Same pattern for all gender/number/case (Po/Co/Sp + Sg/Pl + Ma/Fe/Ne + No/Ac/Ge/Da/Is)
   * - ``CoSgMaNo`` … ``CoPlFeDa``
     - Comparative (all cases/genders/numbers)
   * - ``SpSgMaNo`` … ``SpPlFeDa``
     - Superlative (all cases/genders/numbers)

Verbs
^^^^^

.. list-table::
   :header-rows: 1
   :widths: 14 50

   * - Code
     - Meaning
   * - ``If``
     - Infinitive (form in paradigm table)
   * - ``IdIf``
     - Infinitive (dependent / identical form)
   * - ``Inf``
     - Infinitive
   * - ``PsInSg1``
     - Present indicative singular 1st person
   * - ``PsInSg2``
     - Present indicative singular 2nd person
   * - ``PsInSg3``
     - Present indicative singular 3rd person
   * - ``PsInPl``
     - Present indicative plural
   * - ``PsSuSg``
     - Present subjunctive singular
   * - ``PsSuPl``
     - Present subjunctive plural
   * - ``PsPa``
     - Present participle (adjective form)
   * - ``PsPt``
     - Present participle
   * - ``PsSug``
     - Present subjunctive (variant)
   * - ``PaInSg1``
     - Preterite (past) indicative singular 1st person
   * - ``PaInSg2``
     - Preterite indicative singular 2nd person
   * - ``PaInSg3``
     - Preterite indicative singular 3rd person
   * - ``PaInPl``
     - Preterite indicative plural
   * - ``PaSuSg``
     - Preterite subjunctive singular
   * - ``PaSuPl``
     - Preterite subjunctive plural
   * - ``PaPt``
     - Past participle
   * - ``ImSg``
     - Imperative singular
   * - ``ImPl``
     - Imperative plural
   * - ``ImpSg``
     - Imperative singular (variant)
   * - ``ImpPl``
     - Imperative plural (variant)
   * - ``Pp``
     - (Present) participle

Numerals and other
^^^^^^^^^^^^^^^^^^

Numerals and pronoun-like forms reuse noun and adjective function codes where
they decline (e.g. ``PlFeNo``, ``PoPlFeNo`` for numeral forms that agree in
gender, number, and case).



Perl quirks ledger
------------------

See :doc:`/overview/morphology_perl_quirks_ledger` for retained compatibility
behaviors inherited from the original Perl generator semantics.

See also
--------

- :doc:`/overview/wright_paradigms` — List of Wright's paradigms and generator coverage.

References
----------

- Tichý, O. (2017). Nástroj na tvaroslovnou analýzu staré angličtiny /
  Morphological analyser of Old English. *Časopis pro moderní filologii*
  99(1), 40–54. `ResearchGate
  <https://www.researchgate.net/publication/318926182_Morphological_analyser_of_old_english>`__
- Wright, J. & Wright, E. M. (1914). *Old English Grammar*. Oxford: Henry
  Frowde. (Original edition 1908.)
- Bosworth, J. & Toller, T. N. (1921). *An Anglo-Saxon Dictionary*. Oxford.
