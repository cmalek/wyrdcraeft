Configuration: Command Line Tool
================================

This guide covers all configuration options for the ``oe_json_extractor``
command line tool, including configuration files, environment variables, and
command-line options.

We offer configuration files and command-line options to make it easier for us
language nerds to convert documents into the
:class:`~oe_json_extractor.models.OldEnglishText` model without having to write
any code.

Configuration Methods
---------------------

The ``oe_json_extractor`` command line tool supports multiple configuration methods,
loaded in order of priority:

1. **Command-line options** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Default values** (lowest priority)

Configuration Files
-------------------

File Locations
~~~~~~~~~~~~~~

In macOS and Linux, configuration files are searched in this order:

1. ``/etc/oe_json_extractor.conf`` (system-wide)
2. ``~/.oe_json_extractor.conf`` (user-specific)
3. ``./oe_json_extractor.conf`` (current directory)

In Windows, the configuration files are searched in this order:

1. ``C:\ProgramData\oe_json_extractor\config.toml`` (system-wide)
2. ``%USERPROFILE%\.config\oe_json_extractor.toml`` (user-specific)
3. ``%USERPROFILE%\.oe_json_extractor.toml`` (current directory)

File Format
~~~~~~~~~~~

Configuration files use INI format:

.. code-block:: toml

    [oe_json_extractor]
    llm_model_id = "qwen2.5:14b-instruct"
    llm_temperature = 0.0
    llm_max_tokens = 4096
    llm_timeout_s = 120
    openai_api_key = "sk-proj-1234567890"
    gemini_api_key = "gcp-api-key-1234567890"
    log_level = "INFO"
    log_file = "/var/log/oe_json_extractor.log"
    default_output_format = "json"
    enable_colors = true
    quiet_mode = false

.. note::
    The configuration file is a TOML file.  In all honesty, the LLM settings are unimportant since the LLM extraction is a work in progress and is generally not a good choice for converting documents, because it still gets a lot of things wrong, especially verse.

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

**llm_model_id**
    The ID of the LLM model to use when using
    :class:`~oe_json_extractor.LLMDocumentIngestor`.  We support the following
    models:

    - qwen2.5:14b-instruct
    - gemini-3-flash-preview
    - gpt-4o
    - o1-mini
    - o3-preview

    Default: ``qwen2.5:14b-instruct``

    Example:
    .. code-block:: toml

        llm_model_id = "qwen2.5:14b-instruct"

**llm_temperature**
    The temperature to use for the LLM when using
    :class:`~oe_json_extractor.LLMDocumentIngestor`.  This is a value between 0
    and 1 that controls the randomness of the LLM's output.   We recommend setting
    this to 0.0 for deterministic output.

    Default: ``0.0``

    Example:

    .. code-block:: toml

        llm_temperature = 0.0

**llm_max_tokens**
    The maximum number of tokens to use for the LLM when using
    :class:`~oe_json_extractor.LLMDocumentIngestor`.  This is the maximum number
    of tokens that we will allow the LLM to return.  Note that the maximum for this is
    is dependent on the model you are using.

    Default: ``4096``

    Example:

    .. code-block:: toml

        llm_max_tokens = 8192

**llm_timeout_s**
    The timeout in seconds to use for the LLM when using
    :class:`~oe_json_extractor.LLMDocumentIngestor`.  This is the maximum amount
    of time we will wait for the LLM to return a response.

    Default: ``120``

    Example:

    .. code-block:: toml

        llm_timeout_s = 60

**openai_api_key**
    If you want to use an OpenAI model when using
    :class:`~oe_json_extractor.LLMDocumentIngestor`, you need to set the API key
    here.

    Example:

    .. code-block:: ini

        openai_api_key = "sk-proj-1234567890"

**gemini_api_key**
    If you want to use a Gemini model when using
    :class:`~oe_json_extractor.LLMDocumentIngestor`, you need to set the API key
    here.

    Example:

    .. code-block:: toml

        gemini_api_key = "gcp-api-key-1234567890"

**log_level**
    The log level to use for the application.  This is the level of logging to use.
    We support the following levels: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.
    The hierarchy is: DEBUG < INFO < WARNING < ERROR, and setting a lower level will
    include all messages at higher levels.

    Default: ``INFO``

    Example:

    .. code-block:: toml

        log_level = "INFO"

**log_file**
    The file to use for logging.  If not set, logging will be written to the console.

    Default: ``None``

    Example:

    .. code-block:: toml

        log_file = "/var/log/oe_json_extractor.log"

**enable_colors**
    Whether to enable colors in the output.

    Default: ``true``

    Example:

    .. code-block:: toml

        enable_colors = true

**quiet_mode**
    Whether to enable quiet mode.  If enabled, no output will be written to the console.

    Default: ``false``

    Example:

    .. code-block:: toml

        quiet_mode = true

**default_output_format**
    The default output format to use for the application.  We support the following
    formats: ``table``, ``json``, ``text``.

    Default: ``table``

    Example:

    .. code-block:: toml

        default_output_format = "json"

Environment Variables
---------------------

You can set configuration using environment variables:

.. code-block:: bash

    # Set base URL
    export DIRECTORY_API_BASE_URL=https://directory.caltech.edu/

    # Set timeout
    export DIRECTORY_API_TIMEOUT=30.0

    # Set authentication token
    export DIRECTORY_API_AUTH_TOKEN=2304983209834059430924380593485432987

    # Set insecure flag
    export DIRECTORY_API_INSECURE=True

Environment Variable Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``OE_JSON_EXTRACTOR_LLM_MODEL_ID`` → ``llm_model_id``
- ``OE_JSON_EXTRACTOR_LLM_TEMPERATURE`` → ``llm_temperature``
- ``OE_JSON_EXTRACTOR_LLM_MAX_TOKENS`` → ``llm_max_tokens``
- ``OE_JSON_EXTRACTOR_LLM_TIMEOUT_S`` → ``llm_timeout_s``
- ``OE_JSON_EXTRACTOR_OPENAI_API_KEY`` → ``openai_api_key``
- ``OE_JSON_EXTRACTOR_GEMINI_API_KEY`` → ``gemini_api_key``
- ``OE_JSON_EXTRACTOR_LOG_LEVEL`` → ``log_level``
- ``OE_JSON_EXTRACTOR_LOG_FILE`` → ``log_file``
- ``OE_JSON_EXTRACTOR_ENABLE_COLORS`` → ``enable_colors``
- ``OE_JSON_EXTRACTOR_QUIET_MODE`` → ``quiet_mode``
- ``OE_JSON_EXTRACTOR_DEFAULT_OUTPUT_FORMAT`` → ``default_output_format``

Command-Line Options
--------------------

Global Options
~~~~~~~~~~~~~~

All commands support these global options:

.. code-block:: bash

    # Specify base URL
    directory-api-client --base-url https://directory.caltech.edu/ buildings list

    # Set timeout
    directory-api-client --timeout 60 buildings list

    # Disable SSL certificate verification
    directory-api-client --insecure buildings list

    # Choose output format
    directory-api-client --output table buildings list

Option Reference for all commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**--verbose**
    Enable verbose output.

    Example:

    .. code-block:: bash

        oe_json_extractor --verbose convert /path/to/source.txt /path/to/output.json


**--quiet**
    Enable quiet mode.

    Example:

    .. code-block:: bash

        oe_json_extractor --quiet convert /path/to/source.txt /path/to/output.json

**--output**
    Choose output format: ``json`` or ``table``.

    Default: ``json``

    Example:
    .. code-block:: bash

        oe_json_extractor --output json settings show

**--config-file**
    Specify a custom configuration file to use.

    Example:
    .. code-block:: bash

        oe_json_extractor --config-file /path/to/config.toml settings show

Configuration Examples
----------------------

Basic Setup
~~~~~~~~~~~

.. code-block:: toml

    # ~/.directory-api-client.conf
    [oe_json_extractor]
    llm_model_id = "qwen2.5:14b-instruct"
    llm_temperature = 0.0
    llm_max_tokens = 4096
    llm_timeout_s = 120
    openai_api_key = "sk-proj-1234567890"
    gemini_api_key = "gcp-api-key-1234567890"
    log_level = "INFO"
    log_file = "/var/log/oe_json_extractor.log"
    default_output_format = "json"
    enable_colors = true
    quiet_mode = false

Or use command-line options:

.. code-block:: bash

    $ export OE_JSON_EXTRACTOR_LLM_MODEL_ID="qwen2.5:14b-instruct"
    $ export OE_JSON_EXTRACTOR_LLM_TEMPERATURE=0.0
    $ export OE_JSON_EXTRACTOR_LLM_MAX_TOKENS=4096
    $ export OE_JSON_EXTRACTOR_LLM_TIMEOUT_S=120
    $ export OE_JSON_EXTRACTOR_OPENAI_API_KEY="sk-proj-1234567890"
    $ export OE_JSON_EXTRACTOR_GEMINI_API_KEY="gcp-api-key-1234567890"
    $ export OE_JSON_EXTRACTOR_LOG_LEVEL="INFO"
    $ export OE_JSON_EXTRACTOR_LOG_FILE="/var/log/oe_json_extractor.log"
    $ directory-api-client convert /path/to/source.txt /path/to/output.json
    $ oe_json_extractor settings show
    $ oe_json_extractor settings create

Security Considerations
-----------------------

Configuration File Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Protect your configuration files:

.. code-block:: bash

    # Set proper permissions
    chmod 600 ~/.oe_json_extractor.conf

    # For system-wide configuration
    chmod 640 /etc/oe_json_extractor.conf
    chown root:root /etc/oe_json_extractor.conf

Environment Variable Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secure environment variable usage:

.. code-block:: bash

    # Set variables for current session only
    export OE_JSON_EXTRACTOR_OPENAI_API_KEY="sk-proj-1234567890"
    export OE_JSON_EXTRACTOR_GEMINI_API_KEY="gcp-api-key-1234567890"

    # Clear sensitive variables when done
    unset OE_JSON_EXTRACTOR_OPENAI_API_KEY
    unset OE_JSON_EXTRACTOR_GEMINI_API_KEY

Troubleshooting Configuration
-----------------------------

Configuration Debugging
~~~~~~~~~~~~~~~~~~~~~~~

Check which configuration is being used:

.. code-block:: bash

    # Display configuration
    oe_json_extractor settings show


Common Issues
~~~~~~~~~~~~~

**Configuration Not Loaded**

    - Check file permissions and ownership
    - Verify file format (INI syntax)
    - Ensure file is in correct location
    - Ensure that the file is readable by the user running the command

**Configuration Not Valid**

    - See :ref:`Configuration Validation CLI` for more details.

**Environment Variables Not Recognized**

    - Check variable names (must start with ``OE_JSON_EXTRACTOR_``)
    - Restart terminal session
    - Verify variable values

**Command-Line Options Override**

    - Command-line options take highest priority
    - Check for conflicting options
    - Use ``--help`` to see current options


.. _Configuration Validation CLI:

Configuration Validation
------------------------

Validation Rules
~~~~~~~~~~~~~~~~

The library validates configuration:

- **llm_model_id**: Must be a valid model ID: one of ``qwen*``, ``gemini*``, ``gpt-*``, ``o1-*``, ``o3-*``
- **llm_temperature**: Must be a float between 0 and 1
- **llm_max_tokens**: Must be a positive integer and less than the maximum number of tokens for the model
- **llm_timeout_s**: Must be a positive integer
- **openai_api_key**: Must be a valid OpenAI API key
- **gemini_api_key**: Must be a valid Gemini API key
- **log_level**: Must be one of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``
- **log_file**: Must be a valid, writable file path
- **enable_colors**: Must be a boolean
- **quiet_mode**: Must be a boolean
- **default_output_format**: Must be one of ``table``, ``json``, ``text``

Error Messages
~~~~~~~~~~~~~~

Common validation errors:

.. code-block:: bash

    # Invalid model ID
    Error: Invalid model ID: foobar2.5

    # Invalid temperature
    Error: Temperature must be between 0 and 1

    # Invalid max tokens
    Error: Max tokens must be greater than 0

    # Invalid timeout
    Error: Timeout must be greater than 0

    # Invalid output format
    Error: Invalid output format: foobar

Best Practices
--------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use configuration files for defaults**

   - Set common settings in ``~/.oe_json_extractor.conf``
   - Use environment variables for overrides
   - Use command-line options for one-time changes

2. **Version control**

   - Don't commit sensitive configuration
   - Use templates for configuration files
   - Document configuration changes

3. **Security**

   - Protect configuration files with proper permissions
   - Clear sensitive environment variables

4. **Testing**

   - Test timeout settings