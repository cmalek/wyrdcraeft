Quickstart Guide
================

This guide will get you up and running with ``oe_json_extractor`` quickly, showing both
the Python client and command-line interface.

Prerequisites
-------------

- Python 3.10 or higher
- Follow the :doc:`/overview/installation` instructions to install ``oe_json_extractor``
- Other prerequisites here

Configuration
-------------

Typically the defaults that ship with ``oe_json_extractor``
will work. If you need to change those defaults, you can create a configuration
file at ``~/.oe_json_extractor.conf``:

You can configure ``oe_json_extractor`` using configuration
files or environment variables. See :doc:`/overview/configuration` for more
details.

Basic Usage
-----------

Get Help
^^^^^^^^

.. code-block:: bash

    # Show main help
    oe_json_extractor --help

    # Show help for specific command groups
    oe_json_extractor group1 --help
    oe_json_extractor group2 --help
    oe_json_extractor group3 --help
    oe_json_extractor settings --help

Feature 1 Usage
^^^^^^^^^^^^^^^

.. code-block:: bash

    # List all features
    oe_json_extractor group1 feature1

    # Filter services by pattern
    oe_json_extractor group1 feature1 --arg "foo" --arg "bar"


Feature 2 Usage
^^^^^^^^^^^^^^^

.. code-block:: bash

    # List all features
    oe_json_extractor group2 feature2

    # Filter services by pattern
    oe_json_extractor group2 feature2 --arg "foo" --arg "bar"

Output Formats
^^^^^^^^^^^^^^

.. code-block:: bash

    # Use table format (default) for human reading
    oe_json_extractor group1 feature1 --output table

    # Use JSON format for scripting
    oe_json_extractor group1 feature1 --output json

    # Use text format for simple output
    oe_json_extractor group1 feature1 --output text

    # Use text format for settings
    oe_json_extractor group1 feature1 --output text settings

Next Steps
----------

Now that you have the basics working:

1. **Usage**: See :doc:`/overview/usage` for more advanced features and detailed examples.
2. **Configuration**: See :doc:`/overview/configuration` for configuration options.
3. **Troubleshooting**: See the troubleshooting sections in each guide for common issues.

Getting Help
------------

- Check the full documentation for detailed examples
- Review the troubleshooting sections in each guide
- Report issues on the GitHub repository