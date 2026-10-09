``wyrdcraeft diacritic import-variants``
========================================

This page documents ``wyrdcraeft diacritic import-variants``, which adds the
variant spellings printed in Bosworth-Toller (BT) entries to the **unique** list
of the macron index as entries of their own.

Purpose
-------

A BT entry such as ``tilung, teolung, tiolung`` lists spellings of one headword.
The importer makes each variant a key of its own, so
:doc:`command_convert_mark_diacritics` recognizes it. It is a **dry run unless
``--apply`` is given**: run it, read the report, then apply.

Command syntax
--------------

.. code-block:: bash

    wyrdcraeft diacritic import-variants [OPTIONS]

Options
-------

- ``--source-path PATH``: BT ``oe_bt.txt``. Default: the packaged source.
- ``--index-path PATH``: Macron index JSON. Default: the packaged index.
- ``--apply``: Write the new entries to the index. Without it nothing in the
  index changes.
- ``--report-output PATH``: Where to write the review report. Default:
  ``bt-variant-import-report.json`` in the current directory. The report is
  written on every run, dry or not.

What is added
-------------

A variant is stored as BT prints it, lowercased. No mark is copied from the
headword. A variant is added only when its key is in neither the unique nor the
ambiguous list.

What is never touched
---------------------

Existing keys. A variant of a key that is already in the index never changes
it, and a key completed with ``diacritic-disambiguate`` is left alone. When the
variant adds nothing (same marks, or fewer marks than the existing form) it is
only counted. When it has more marks, conflicting marks, or a new mark pattern
for an undecided ambiguous key, it is listed in the report for you to decide.

What is skipped as junk
-----------------------

- Words in ALL CAPS (two or more letters).
- A hyphenated token that ends in a single letter (a truncated fragment).
- Citation sigla and Roman numerals in the stoplist
  (``wyrdcraeft/etc/diacritic/bt_variant_stoplist.txt``, hand-edited).
- A key listed as a variant under three or more headwords.

A variant that survives is added only when it is a spelling of its own headword:
its edit distance from the headword must be at most ``max(2, len(headword) // 3)``.
Variants beyond that (inflected forms, English words) are listed under
``below_gate`` when their key is not in the index.

The report
----------

The JSON report has ``additions`` (new key to stored form), ``collisions``
(each with the existing forms and a reason: ``more_marks``, ``conflicting_marks``
or ``new_pattern``), ``conflicting_new`` (new keys whose variants disagree on
marks; none is added), ``below_gate`` and ``counts``. To settle a collision,
edit the entry by hand with ``wyrdcraeft diacritic add --force``.

Recommended workflow
--------------------

1. Run without ``--apply`` and read the report.
2. Run with ``--apply``.
3. Review ``git diff`` of the index. Running it again adds nothing.
