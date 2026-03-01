``wyrdcraeft morphology generate``
=================================

This command generates Old English morphology forms using the migrated Python
implementation from Ondřej Tichý's original Perl-based generator workflow.

Licensing and provenance
------------------------

This morphology generator is based on the work of Ondřej Tichý's thesis,
Morphological Analyser of Old English (2017):
https://www.researchgate.net/publication/318926182_Morphological_analyser_of_old_english

The upstream morphological generator Perl code and data is (c) Ondřej Tichý,
is released under the CC BY 4.0 license.

Changes made to in this repository by Christopher Malek are released under the
MIT license.

All other code implemented directly by Christopher Malek, also released under
the MIT license.

Scope note
----------

``wyrdcraeft`` includes Python runtime morphology generation and Python-reference
snapshot tooling. Perl parity audit tooling remains in the source migration
project and is intentionally not shipped as a ``wyrdcraeft`` command.

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

If paths are not provided explicitly, data is loaded from packaged files under:

.. code-block:: text

    wyrdcraeft/etc/morphology/

Examples
--------

.. code-block:: bash

    # Generate subset output with limit
    wyrdcraeft morphology generate --limit 250 --output output.tsv

    # Generate full output
    wyrdcraeft morphology generate --full --output morphology_full.tsv

Python-reference snapshots
--------------------------

The migrated Python snapshot generator is available as:

.. code-block:: bash

    wyrdcraeft morphology generate-reference-snapshots --help

It writes deterministic compressed JSONL snapshots used by morphology reference
tests.

Perl quirks ledger
------------------

See :doc:`/overview/morphology_perl_quirks_ledger` for retained compatibility
behaviors inherited from the original Perl generator semantics.
