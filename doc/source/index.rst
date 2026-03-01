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

   overview/configuration_client
   overview/configuration_cli
   overview/using_client
   overview/using_cli
   overview/command_morphology_generate
   overview/morphology_perl_quirks_ledger
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
   api/client
   api/models

Current version is |release|.

``wyrdcraeft`` is a Python command-line tool for converting Old English
texts into a standard JSON format that can be used for programmatic analysis and
manipulation.

Core Features
-------------

wyrdcraeft provides the following key features:

- Ingesting Old English texts from a variety of sources: text files, PDF files, and TEI XML files.
- Converting the text into a standard JSON format using a variety of methods: deterministic heuristics, TEI XML parsing, and LLM-based parsing.
- Properly handling both prose and verse.

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