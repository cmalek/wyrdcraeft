Using the Command Line Interface
================================

The ``wyrdcraeft`` command-line interface provides access to ingestion,
conversion, and diacritic-maintenance workflows from the terminal.

Getting Help
------------

Basic Help
~~~~~~~~~~

.. code-block:: bash

    # Show main help
    wyrdcraeft --help

    # Show help for specific command groups
    wyrdcraeft version --help
    wyrdcraeft convert --help
    wyrdcraeft diacritic --help
    wyrdcraeft diacritic disambiguate --help
    wyrdcraeft settings --help
    wyrdcraeft settings show --help
    wyrdcraeft settings create --help
    wyrdcraeft source convert --help
    wyrdcraeft morphology --help
    wyrdcraeft morphology generate --help
    wyrdcraeft morphology generate-reference-snapshots --help

Command Structure
-----------------

The CLI follows a hierarchical command structure:

.. code-block:: bash

    wyrdcraeft [global-options] <command-group> <subcommand> [options]

Global Options
--------------

Common options available for all commands:

.. code-block:: bash

    # Enable verbose output
    wyrdcraeft --verbose convert input.txt output.json

    # Enable quiet mode
    wyrdcraeft --quiet convert input.txt output.json

    # Use a custom configuration file
    wyrdcraeft --config-file /path/to/config.toml convert input.txt output.json

    # Choose output format
    wyrdcraeft --output table settings show

    # Use environment variables to change configuration
    export WYRDCRAEFT_LLM_MODEL_ID="gpt-4o"
    $ wyrdcraeft convert input.txt output.json

Configuration
-------------

See :doc:`/overview/configuration_cli` for details on how to configure ``wyrdcraeft`` for your specific use case.

Best Practices
--------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

Use configuration files when necessary.  The default configuration shipped with
``wyrdcraeft`` is is typically fine (though you still must supply the LLM
API keys as environment variables or in the configuration file if you are using
a cloud model) for development, testing, and troubleshooting, but you can
override it with a configuration file.  See :doc:`/overview/configuration_cli`
for more details.

Command Guides
--------------

The following pages document the diacritic command workflows in detail:

.. toctree::
   :maxdepth: 1

   command_source_mark_diacritics
   command_diacritic_disambiguate
   command_morphology_generate
   command_morphology_generate_reference_snapshots