Frequently Asked Questions
==========================

This section answers common questions about tfmate and provides solutions to frequently encountered issues.

General Questions
-----------------

What is wyrdcraeft?
^^^^^^^^^^^^^^^^^^^^^^^^^^

wyrdcraeft is a Python command-line tool designed to convert Old English (Anglo-Saxon) texts into a standard JSON format. It provides capabilities for:

- Ingesting Old English texts from local text files and TEI XML files.
- Converting the text into a standard JSON format using deterministic heuristics or TEI XML parsing.
- Properly handling both prose and verse.

Installation Issues
-------------------

How do I install wyrdcraeft?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See the :doc:`installation` guide for detailed installation instructions. The recommended methods are:

- Using ``uv tool``: ``uv tool install wyrdcraeft``
- Using ``pipx``: ``pipx install wyrdcraeft``
- Using ``pip``: ``pip install wyrdcraeft``
- From source: Clone the repository and run ``uv sync``

I get a "command not found" error after installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This usually means the installation directory is not in your PATH. Try:

1. Restart your terminal session
2. Check if the installation directory is in your PATH
3. For ``pipx`` installations, ensure ``pipx`` is in your PATH
4. For ``uv tool`` installations, ensure ``uv`` is properly configured

Usage Questions
---------------

How do I convert a document to JSON?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Convert a text file to JSON
    wyrdcraeft source convert --title="My Title" input.txt output.json

    # Convert a TEI XML file to JSON
    wyrdcraeft source convert --title="My Title" input.xml output.json

How do I suppress output except errors?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``--quiet`` option:

.. code-block:: bash

    # Suppress all output except errors
    wyrdcraeft --quiet group1 feature1

This is useful in scripts where you only want to see error messages.

Configuration Issues
--------------------

How do I use a custom configuration file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``--config-file`` option:

.. code-block:: bash

    # Use custom configuration file
    wyrdcraeft --config-file /path/to/config.toml source convert --title="My Title" input.txt output.json

The configuration file should be in TOML format. See the :doc:`configuration_cli` guide for details.

What configuration options are available?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``wyrdcraeft`` supports configuration for log level, output format, quiet mode,
and the application data directory. See the :doc:`configuration_cli` guide.

Performance and Limitations
---------------------------

What are the performance characteristics?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Deterministic conversion**: Fast. May still mis-parse complex documents.

Where can I get more help?
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Documentation**: Check the other sections of this documentation
2. **Command help**: Use ``wyrdcraeft --help`` or ``wyrdcraeft <command> --help``
3. **Verbose mode**: Use ``--verbose`` for detailed error information
4. **GitHub issues**: Report bugs or request features on the project repository

How do I report a bug?
^^^^^^^^^^^^^^^^^^^^^^

When reporting a bug, please include:

1. **Command used**: The exact command that failed
2. **Error message**: The complete error output
3. **Environment**: OS, Python version, tfmate version
4. **Verbose output**: Use ``--verbose`` and include the output

Example bug report:

.. code-block:: text

    Command: wyrdcraeft group1 feature1 --arg "foo" --arg "bar"
    Error: Feature 1 error
    OS: macOS 14.0
    Python: 3.11.9
    wyrdcraeft: 0.1.0

    Verbose output:
    [Include verbose output here]