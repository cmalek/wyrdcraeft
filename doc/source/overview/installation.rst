Installation
============

This guide covers how to install the ``oe_json_extractor`` package and its dependencies.

Prerequisites
-------------

Before installing ``oe_json_extractor``, ensure you have:

- Python 3.10 or higher
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

After installation, verify that ``oe_json_extractor`` is properly installed:

.. code-block:: shell

    oe_json_extractor --help


Configuration
-------------

After installation, you may want to configure ``oe_json_extractor`` for your specific
environment.  See :doc:`configuration` for detailed configuration options.

Getting Help
------------

If you encounter issues during installation:

1. Check the `GitHub issues <https://github.com/cmalek/oe_json_extractor/issues>`_
2. Review the troubleshooting section above
3. Ensure your Python environment meets the prerequisites
4. Try installing in a virtual environment to isolate dependencies