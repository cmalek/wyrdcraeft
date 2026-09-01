.. _configuration cli:

Configuration: Command Line Tool
================================

This guide covers all configuration options for the ``wyrdcraeft``
command line tool, including configuration files, environment variables, and
command-line options.

We offer configuration files and command-line options to make it easier for us
language nerds to convert documents into the
:class:`~wyrdcraeft.models.OldEnglishText` model without having to write
any code.

Configuration Methods
---------------------

The ``wyrdcraeft`` command line tool supports multiple configuration methods,
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

1. ``/etc/wyrdcraeft.toml`` (system-wide)
2. ``~/.wyrdcraeft.toml`` (user-specific)
3. ``./wyrdcraeft.toml`` (current directory)

In Windows, the configuration files are searched in this order:

1. ``C:\ProgramData\wyrdcraeft\config.toml`` (system-wide)
2. ``%USERPROFILE%\.config\wyrdcraeft.toml`` (user-specific)
3. ``%USERPROFILE%\.wyrdcraeft.toml`` (current directory)

File Format
~~~~~~~~~~~

Configuration files use INI format:

.. code-block:: toml

    [wyrdcraeft]
    log_level = "INFO"
    log_file = "/var/log/wyrdcraeft.log"
    default_output_format = "json"
    enable_colors = true
    quiet_mode = false

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

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

        log_file = "/var/log/wyrdcraeft.log"

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

- ``WYRDCRAEFT_LOG_LEVEL`` → ``log_level``
- ``WYRDCRAEFT_LOG_FILE`` → ``log_file``
- ``WYRDCRAEFT_ENABLE_COLORS`` → ``enable_colors``
- ``WYRDCRAEFT_QUIET_MODE`` → ``quiet_mode``
- ``WYRDCRAEFT_DEFAULT_OUTPUT_FORMAT`` → ``default_output_format``

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

        wyrdcraeft --verbose source convert /path/to/source.txt /path/to/output.json


**--quiet**
    Enable quiet mode.

    Example:

    .. code-block:: bash

        wyrdcraeft --quiet source convert /path/to/source.txt /path/to/output.json

**--output**
    Choose output format: ``json`` or ``table``.

    Default: ``json``

    Example:
    .. code-block:: bash

        wyrdcraeft --output json settings show

**--config-file**
    Specify a custom configuration file to use.

    Example:
    .. code-block:: bash

        wyrdcraeft --config-file /path/to/config.toml settings show

Configuration Examples
----------------------

Basic Setup
~~~~~~~~~~~

.. code-block:: toml

    # ~/.wyrdcraeft.conf
    [wyrdcraeft]
    log_level = "INFO"
    log_file = "/var/log/wyrdcraeft.log"
    default_output_format = "json"
    enable_colors = true
    quiet_mode = false

Or use command-line options:

.. code-block:: bash

    $ export WYRDCRAEFT_LOG_LEVEL="INFO"
    $ export WYRDCRAEFT_LOG_FILE="/var/log/wyrdcraeft.log"
    $ wyrdcraeft source convert /path/to/source.txt /path/to/output.json
    $ wyrdcraeft settings show
    $ wyrdcraeft settings create

Security Considerations
-----------------------

Configuration File Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Protect your configuration files:

.. code-block:: bash

    # Set proper permissions
    chmod 600 ~/.wyrdcraeft.conf

    # For system-wide configuration
    chmod 640 /etc/wyrdcraeft.conf
    chown root:root /etc/wyrdcraeft.conf

Environment Variable Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secure environment variable usage:

.. code-block:: bash

    # Set variables for current session only
    export WYRDCRAEFT_APP_DATA_DIR="$HOME/.config/wyrdcraeft"

    # Clear overrides when done
    unset WYRDCRAEFT_APP_DATA_DIR

Troubleshooting Configuration
-----------------------------

Configuration Debugging
~~~~~~~~~~~~~~~~~~~~~~~

Check which configuration is being used:

.. code-block:: bash

    # Display configuration
    wyrdcraeft settings show


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

    - Check variable names (must start with ``WYRDCRAEFT_``)
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

- **log_level**: Must be one of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``
- **log_file**: Must be a valid, writable file path
- **enable_colors**: Must be a boolean
- **quiet_mode**: Must be a boolean
- **default_output_format**: Must be one of ``table``, ``json``, ``text``

Error Messages
~~~~~~~~~~~~~~

Common validation errors:

.. code-block:: bash

    # Invalid output format
    Error: Invalid output format: foobar

Best Practices
--------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use configuration files for defaults**

   - Set common settings in ``~/.wyrdcraeft.conf``
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