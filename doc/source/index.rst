=================
wyrdcraeft
=================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   overview/installation
   overview/quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   overview/configuration_cli
   overview/using_client
   overview/using_cli
   overview/faq

.. toctree::
   :maxdepth: 2
   :caption: Development
   :hidden:

   runbook/contributing
   runbook/coding_standards

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   changelog
   overview/format
   overview/wright_paradigms
   runbook/macron_list_generation
   verview/morphology_perl_quirks_ledger

.. toctree::
   :maxdepth: 2
   :caption: API
   :hidden:

   api/client
   api/models

Current version is |release|.

``wyrdcraeft`` is a Python command-line tool for converting Old English
texts into a standard JSON format that can be used for programmatic analysis and
manipulation.

Core Features
-------------

wyrdcraeft provides the following key features:

- Ingesting Old English texts from text files and TEI XML files; extraction from other formats is a work in progress.
- Converting the text into a standard JSON format using a variety of methods: deterministic heuristics, TEI XML parsing, and LLM-based parsing.
- Properly handling both prose and verse.
- Generating Old English morphology forms using the migrated Python implementation from Ondřej Tichý's original Perl-based generator workflow.

Getting Started
---------------

To get started with wyrdcraeft:

1. **Installation**: Follow the :doc:`/overview/installation` guide
2. **Quick Start**: See the :doc:`/overview/quickstart` guide for basic usage
3. **Usage Guide**: Learn about commands and options in :doc:`/overview/using_cli` and :doc:`/overview/using_client`
4. **Configuration**: Learn about CLI configuration options in :doc:`/overview/configuration_cli`.
5. **FAQ**: Check the :doc:`/overview/faq` section for common questions and troubleshooting

For developers, see the :doc:`/runbook/contributing` and :doc:`/runbook/coding_standards` guides.

Requirements
------------

- Python 3.10 - 3.13 (we're waiting for a dependency to be updated to 3.14)

Licensing and provenance
------------------------

Bosworth-Toller Old English Dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The OCR extracted text of the Bosworth-Toller Old English Dictionary used in this project is from the `Germanic Lexicon Project <https://www.germanic-lexicon-project.org/>`_.  The scanning was done by Jason Burton, B. Dan Fairchild, Margaret Hoyt, Grace Mrowicki, Michael O'Keefe, Sarah Hartman, Finlay Logan, Sean Crist, Thomas McFadden, David Harrison, and Sean Crist; that data is in the public domain.

Morphological Analyser of Old English
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The Old English morphology generator in ``wyrdcraeft`` is based on the work of Ondřej Tichý's thesis, `Morphological Analyser of Old English <https://www.researchgate.net/publication/318926182_Morphological_analyser_of_old_english>`_ (2017).
- The upstream morphological generator Perl code and data is (c) Ondřej Tichý, is released under the CC BY 4.0 license.  The modified Perl code itself, with Madeleine Thompson's changes, can be found at `github:madeleineth/tichy_oe_generator <https://github.com/madeleineth/tichy_oe_generator>`_.
- Changes made to the morphology generator in this repository by the maintainers of ``wyrdcraeft`` are released under the MIT license.

All other code
~~~~~~~~~~~~~~

- All other code implemented directly by Christopher Malek, also released under the MIT license.