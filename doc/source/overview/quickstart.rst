Quickstart Guide
================

This guide will get you up and running with ``wyrdcraeft`` quickly,
showing both the Python client and command-line interface.

Prerequisites
-------------

- Python 3.9 - 3.13 (we're waiting for a dependency to be updated to 3.14)
- Follow the :doc:`/overview/installation` instructions to install ``wyrdcraeft``

Optional prerequisites
^^^^^^^^^^^^^^^^^^^^^^

- API keys for Gemini and OpenAI, if you want to use the Cloud LLM method to extract text from your documents
- Ollama installed and running with ``qwen2.5:14b-instruct`` available if you want to use local LLM inference to extract text from your documents

Basic Usage with Python Client
------------------------------

The :class:`~wyrdcraeft.DocumentIngestor` provides a simple interface to
convert documents into the :class:`~wyrdcraeft.models.OldEnglishText`
model.  You can find the full API reference in the :doc:`/api/client` section.
See :doc:`configuration_cli` for configuration options for the
Python client.

Configuration for the Command Line Tool
----------------------------------------

Typically the defaults that ship with ``wyrdcraeft`` will work. If you
need to change those defaults, you can create a configuration file at
``~/.wyrdcraeft.conf``, or on Windows at
``C:\ProgramData\wyrdcraeft\config.toml``

Configuration files should be in TOML format. See the :doc:`configuration_cli` guide for details.

You can create a stub version of the configuration file by running:
.. code-block:: bash

    wyrdcraeft settings create

This will create a stub version of the configuration file at the appropriate location for your OS.

You can then edit the configuration file to your liking.  See the :doc:`configuration_cli` guide for details.

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

- :envvar:`WYRDCRAEFT_LLM_MODEL_ID` - The ID of the LLM model to use.
- :envvar:`WYRDCRAEFT_LLM_TEMPERATURE` - The temperature to use for the LLM.
- :envvar:`WYRDCRAEFT_LLM_MAX_TOKENS` - The maximum number of tokens to use for the LLM.
- :envvar:`WYRDCRAEFT_LLM_TIMEOUT_S` - The timeout in seconds to use for the LLM.
- :envvar:`WYRDCRAEFT_OPENAI_API_KEY` - The OpenAI API key to use for the OpenAI models.
- :envvar:`WYRDCRAEFT_GEMINI_API_KEY` - The Gemini API key to use for the Gemini models.
- :envvar:`WYRDCRAEFT_LOG_LEVEL` - The log level to use for the application.
- :envvar:`WYRDCRAEFT_LOG_FILE` - The file to use for logging.
- :envvar:`WYRDCRAEFT_ENABLE_COLORS` - Whether to enable colors in the output.
- :envvar:`WYRDCRAEFT_QUIET_MODE` - Whether to enable quiet mode.
- :envvar:`WYRDCRAEFT_DEFAULT_OUTPUT_FORMAT` - The default output format to use for the application.

Next Steps
----------

Now that you have the basics working:

1. **Usage**: See :doc:`/overview/using_client` and :doc:`/overview/using_cli` for more advanced features and detailed examples.
2. **Configuration**: See :doc:`configuration_cli` for configuration options.
3. **Troubleshooting**: See the troubleshooting sections in each guide for common issues.

Getting Help
------------

- Check the full documentation for detailed examples
- Review the troubleshooting sections in each guide
- Report issues on the GitHub repository