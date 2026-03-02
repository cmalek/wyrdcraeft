``wyrdcraeft settings``
=======================

This page documents the ``wyrdcraeft settings`` group and its subcommands
``show`` and ``create``.

Purpose
-------

- **show**: Display the current application settings. Output format is
  controlled by the global ``--output`` option (``json``, ``table``, or
  ``text``).
- **create**: Create a new settings file at the default path with default
  values. If ``--verbose`` is set, also prints a table of the written settings
  (excluding frozen fields such as ``app_name`` and ``app_version``).

Command syntax
--------------

.. code-block:: bash

    # Default: show settings (table format)
    wyrdcraeft settings

    # Show settings in JSON
    wyrdcraeft settings show
    wyrdcraeft --output json settings

    # Show settings in text format
    wyrdcraeft --output text settings show

    # Create default settings file
    wyrdcraeft settings create

Output formats (show)
---------------------

- **table** (default): Rich table with setting name and value.
- **json**: Single JSON object of all settings.
- **text**: One line per setting, ``name: value``.

Default settings path (create)
------------------------------

The ``create`` subcommand writes to the default settings path used by the
application (e.g. under the user config directory). The exact path is defined
by :class:`wyrdcraeft.settings.Settings`.

Examples
--------

.. code-block:: bash

    wyrdcraeft settings
    wyrdcraeft settings show
    wyrdcraeft --output json settings show
    wyrdcraeft settings create
    wyrdcraeft --verbose settings create
