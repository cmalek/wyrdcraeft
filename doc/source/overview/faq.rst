Frequently Asked Questions
==========================

This section answers common questions about tfmate and provides solutions to frequently encountered issues.

General Questions
-----------------

What is wyrdcraeft?
^^^^^^^^^^^^^^^^^^^^^^^^^^

wyrdcraeft is a Python command-line tool designed to convert Old English (Anglo-Saxon) texts into a standard JSON format. It provides capabilities for:

- Ingesting Old English texts from a variety of sources: text files, PDF files, and TEI XML files.
- Converting the text into a standard JSON format using a variety of methods: deterministic heuristics, TEI XML parsing, and LLM-based parsing.
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

    # Convert a PDF file to JSON
    wyrdcraeft source convert --title="My Title" input.pdf output.json

    # Convert a TEI XML file to JSON
    wyrdcraeft source convert --title="My Title" input.xml output.json

How do I convert a document to JSON using the LLM method?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Convert a text file to JSON using the gpt-4o model
    $ export OPENAI_API_KEY=your-openai-api-key
    $ wyrdcraeft source convert --title="My Title" input.txt output.json --use-llm --llm-model="gpt-4o"

    # Convert a PDF file to JSON using the gemini-3-flash-preview model
    $ export GEMINI_API_KEY=your-gemini-api-key
    $ wyrdcraeft source convert --title="My Title" input.pdf output.json --use-llm --llm-model="gemini-3-flash-preview"

    # Convert a TEI XML file to JSON using the qwen2.5:14b-instruct model
    $ export OLLAMA_API_KEY=your-ollama-api-key
    $ wyrdcraeft source convert --title="My Title" input.xml output.json --use-llm --llm-model="qwen2.5:14b-instruct"

    # Convert a text file to JSON using the qwen2.5:14b-instruct model
    # First run ollama, and pull the model like this:
    $ ollama pull qwen2.5:14b-instruct
    $ wyrdcraeft source convert --title="My Title" input.txt output.json --use-llm

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

``wyrdcraeft`` supports configuration for:

- LLM model ID
- LLM temperature
- LLM max tokens
- LLM timeout
- OpenAI API key
- Gemini API key

See the :doc:`configuration_cli` guide for a complete list of options.

Performance and Limitations
---------------------------

What are the performance characteristics?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **LLM conversion**: This can be very slow, especially when using a local model.  It also is not very accurate, especially for verse.
- **Deterministic conversion**: This is the fastest and most accurate method, but may make mistakes, especially for complex documents.

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