Generating the canonical macron list
====================================

The canonical macron list used by the following commands is generated from a Bosworth-Toller OCR source file
(``data/oe_bt.txt``) using the builder script. The source of this file is [github:madeleineth/btc_anglo_saxon](https://github.com/madeleineth/btc_anglo_saxon/blob/master/db/oe_bosworthtoller.txt.bz2):

.. code-block:: bash

    wyrdcraeft source mark-diacritics source.txt
    wyrdcraeft diacritic disambiguate
    wyrdcraeft diacritic add <normalized_form> <macron_form>
    wyrdcraeft diacritic delete <normalized_form>

Our internal macron index was originally built from this source file using the
builder script:

.. code-block:: bash

    python data/tools/build_macron_index.py

.. important::
    This tool is specifically **not** included in the command line interface because it really only ever needs to be built once and then must be manually updated to deal with ambiguities.  It is only here for developers.

Build pipeline summary
----------------------

1. Read each source line from ``data/oe_bt.txt`` and split with ``@``.
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

The normalization rules are:

- lowercase input
- replace ``ð`` with ``þ``
- decompose Unicode and remove combining marks
- remove internal hyphen/dash characters
- preserve core Old English letters such as ``æ`` and ``þ``