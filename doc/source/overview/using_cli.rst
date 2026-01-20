Using the Command Line Interface
================================

The ``sungazer`` command-line interface provides easy access to all PVS6 functionality
from the terminal. This guide covers all available commands and options.

Getting Help
------------

Basic Help
~~~~~~~~~~

.. code-block:: bash

    # Show main help
    oe_json_extractor --help

    # Show help for specific command groups
    oe_json_extractor convert --help
    oe_json_extractor settings --help

Command Structure
-----------------

The CLI follows a hierarchical command structure:

.. code-block:: bash

    oe_json_extractor [global-options] <command-group> <subcommand> [options]

Global Options
--------------

Common options available for all commands:

.. code-block:: bash

    # Enable verbose output
    oe_json_extractor --verbose convert input.txt output.json

    # Choose output format
    oe_json_extractor --output table settings show

    # Use environment variables to change configuration
    export OE_JSON_EXTRACTOR_LLM_MODEL_ID="gpt-4o"
    $ oe_json_extractor convert input.txt output.json

Configuration
-------------

See :doc:`/overview/configuration_cli` for details on how to configure ``oe_json_extractor`` for your specific use case.

Best Practices
--------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

Use configuration files when necessary.  The default configuration shipped with
``oe_json_extractor`` is is typically fine (though you still must supply the LLM
API keys as environment variables or in the configuration file if you are using
a cloud model) for development, testing, and troubleshooting, but you can
override it with a configuration file.  See :doc:`/overview/configuration_cli`
for more details.
