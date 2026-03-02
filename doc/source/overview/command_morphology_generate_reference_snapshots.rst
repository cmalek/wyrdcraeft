``wyrdcraeft morphology generate-reference-snapshots``
=====================================================

This command is a developer-only tool for generating deterministic compressed
JSONL snapshots used by morphology reference tests.  A regular user should not
need to use this command.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft morphology generate-reference-snapshots [OPTIONS]

Options
-------

- ``--output-dir PATH``: directory where compressed snapshot files are written.
- ``--update``: allow overwriting existing snapshot files.
- ``--include-full``: also generate optional full-dataset smoke metadata snapshot.
- ``--data-dir PATH``: directory containing default morphology data files.
- ``--subset-dictionary PATH``: subset dictionary for default reference snapshots.

Defaults
--------

- ``--output-dir tests/python_reference/data``: the default output directory is the ``tests/python_reference/data`` directory.
- ``--update``: the default is to not update the existing snapshots.
- ``--include-full``: the default is to not include the full dataset smoke metadata snapshot.
- ``--data-dir``: the default is to use the data directory from the ``wyrdcraeft`` package.
- ``--subset-dictionary``: the default is to use the subset dictionary from the ``tests/fixtures/morphology/test_dict.txt`` file.

Output
------

The command writes deterministic compressed JSONL snapshots to the output directory.

The snapshots are used by the morphology reference tests to verify the correctness of the morphology generator.

The snapshots are written to the output directory in the following files:

- ``preprocess_subset.jsonl.gz``: the preprocessed subset dictionary
- ``paradigms_subset.jsonl.gz``: the paradigm metadata the paradigm data for the subset dictionary
- ``forms_manual_subset.jsonl.gz``: the manual forms the manual forms for the subset dictionary
- ``forms_verb_subset.jsonl.gz``: the verb forms the verb forms for the subset dictionary
- ``forms_adj_subset.jsonl.gz``: the adjective forms the adjective forms for the subset dictionary
- ``forms_adv_subset.jsonl.gz``: the adverb forms the adverb forms for the subset dictionary
- ``forms_num_subset.jsonl.gz``: the numeral forms the numeral forms for the subset dictionary
- ``forms_noun_subset.jsonl.gz``: the noun forms the noun forms for the subset dictionary