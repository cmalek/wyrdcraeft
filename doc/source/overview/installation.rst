Installation
============

This guide covers how to install the ``wyrdcraeft`` package and its dependencies.

Prerequisites
-------------

Before installing ``wyrdcraeft``, ensure you have:

- Python 3.9 - 3.13 (we're waiting for a dependency to be updated to 3.14)
- `uv <https://docs.astral.sh/uv/>`_, `pip <https://pip.pypa.io/en/stable/>`_, or `pipx <https://pipx.pypa.io/stable/>`_

Installation Methods
--------------------

From PyPI with ``pip``
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install wyrdcraeft
    wyrdcraeft --help


From PyPI with ``uv``
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    uv tool install wyrdcraeft
    # Ensure you have ./local/bin in your PATH, since that's where uv puts the
    # executable
    wyrdcraeft --help

From PyPI with ``pipx``
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pipx install wyrdcraeft
    wyrdcraeft --help


From Source
^^^^^^^^^^^

If you want to install from the latest development version:

.. code-block:: bash

    git clone https://github.com/cmalek/wyrdcraeft.git
    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    cd wyrdcraeft
    uv tool install .

Verification
------------

After installation, verify that ``directory-api-client`` is properly installed:

If you've installed the package globally, you should be able to run the CLI:

.. code-block:: bash

    wyrdcraeft --help

If you've installed the package locally, you should be able to run the CLI like this:

.. code-block:: bash

    source .venv/bin/activate
    wyrdcraeft --help

Dependencies
------------

``directory-api-client`` has the following key dependencies:

- **httpx**: Modern HTTP client for Python
- **pydantic**: Data validation using Python type annotations
- **pydantic-settings**: Settings management for Python applications
- **click**: Command line interface creation kit
- **rich**: Rich text and beautiful formatting in the terminal
- **unstructured**: Unstructured data extraction
- **any-llm-sdk**: Any LLM SDK, enabling both cloud and local models
- **delb**: Delimiter-based tokenization for TEI XML parsing
- **acdh-tei-pyutils**: ACDH TEI Python utilities for TEI XML parsing
- **pdfminer-six**: PDFMiner for PDF parsing

These dependencies are automatically installed when you install ``wyrdcraeft``.

Development Installation
------------------------

If you plan to contribute to ``wyrdcraeft`` or need the latest development features:

.. code-block:: bash

    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    git clone https://github.com/cmalek/wyrdcraeft.git
    cd wyrdcraeft
    uv sync --dev

Configuration
-------------

After installation, you may want to configure ``wyrdcraeft`` for your specific
PVS6 device.  See :doc:`configuration_cli` for detailed configuration options.

Getting Help
------------

If you encounter issues during installation:

1. Check the help documentation.
2. Review the troubleshooting section above
3. Ensure your Python environment meets the prerequisites
4. Try installing in a virtual environment to isolate dependencies