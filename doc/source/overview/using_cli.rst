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
    wyrdcraeft --help

    # Show help for specific command groups
    wyrdcraeft convert --help
    wyrdcraeft settings --help

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
