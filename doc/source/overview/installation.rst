Installation
============

This guide covers how to install the ``oe_json_extractor`` package and its dependencies.

Prerequisites
-------------

Before installing ``oe_json_extractor``, ensure you have:

- Python 3.9 - 3.13 (we're waiting for a dependency to be updated to 3.14)
- `uv <https://docs.astral.sh/uv/>`_, `pip <https://pip.pypa.io/en/stable/>`_, or `pipx <https://pipx.pypa.io/stable/>`_

Installation Methods
--------------------

From PyPI with ``pip``
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install oe_json_extractor
    oe_json_extractor --help


From PyPI with ``uv``
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    uv tool install oe_json_extractor
    # Ensure you have ./local/bin in your PATH, since that's where uv puts the
    # executable
    oe_json_extractor --help

From PyPI with ``pipx``
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pipx install oe_json_extractor
    oe_json_extractor --help


From Source
^^^^^^^^^^^

If you want to install from the latest development version:

.. code-block:: bash

    git clone https://github.com/cmalek/oe_json_extractor.git
    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    cd oe_json_extractor
    uv tool install .

Verification
------------

After installation, verify that ``directory-api-client`` is properly installed:

If you've installed the package globally, you should be able to run the CLI:

.. code-block:: bash

    oe_json_extractor --help

If you've installed the package locally, you should be able to run the CLI like this:

.. code-block:: bash

    source .venv/bin/activate
    oe_json_extractor --help

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

These dependencies are automatically installed when you install ``oe_json_extractor``.

Development Installation
------------------------

If you plan to contribute to ``oe_json_extractor`` or need the latest development features:

.. code-block:: bash

    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    git clone https://github.com/cmalek/oe_json_extractor.git
    cd oe_json_extractor
    uv sync --dev

Configuration
-------------

After installation, you may want to configure ``oe_json_extractor`` for your specific
PVS6 device.  See :doc:`configuration_cli`  and :doc:`configuration_client` for
detailed configuration options.

Getting Help
------------

If you encounter issues during installation:

1. Check the your colleagues for help.
2. Review the troubleshooting section above
3. Ensure your Python environment meets the prerequisites
4. Try installing in a virtual environment to isolate dependencies