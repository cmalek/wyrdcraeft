Configuration: Python Client
============================

This guide covers all configuration options for the ``wyrdcraeft`` Python client.

Direct Configuration
~~~~~~~~~~~~~~~~~~~~

Configure the client directly in Python (this will use the :class:`~wyrdcraeft.HeuristicDocumentIngestor` class):

.. code-block:: python

    from wyrdcraeft import DocumentIngestor

    metadata = TextMetadata(
        title="The Anglo-Saxon Chronicle",
        source="https://www.gutenberg.org/files/173/173-0.txt",
    )
    # Basic configuration
    oe_json = DocumentIngestor().ingest(
        source_path="path/to/source.txt",
        metadata=metadata,
    )

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

Convert a `TEI <https://tei-c.org/>`_ XML document (this will use the :class:`~wyrdcraeft.TEIDocumentIngestor` class):

.. code-block:: python

    from wyrdcraeft import DocumentIngestor

    metadata = TextMetadata(
        title="Aelfric's Lives of Saints",
        source="https://github.com/TFED-NGO/Aelfric/blob/main/edition.xml"
    )
    oe_json = DocumentIngestor().ingest(
        source_path="path/to/edition.xml",
        metadata=metadata,
    )

Use `unstructured <https://unstructured.io/>`_ and `any-llm <https://any-llm.readthedocs.io/>`_ to convert a document (this will use the :class:`~wyrdcraeft.LLMDocumentIngestor` class):

.. code-block:: python

    from wyrdcraeft import DocumentIngestor

    metadata = TextMetadata(
        title="The Anglo-Saxon Chronicle",
        source="https://www.gutenberg.org/files/173/173-0.txt",
    )
    llm_config = AnyLLMConfig(
        model_id="qwen2.5:14b-instruct",
        max_tokens=8192,
    )
    oe_json = DocumentIngestor().ingest(
        source_path="path/to/source.txt",
        metadata=metadata,
        use_llm=True,
        llm_config=llm_config,
    )

Troubleshooting Configuration
-----------------------------

Common Issues
~~~~~~~~~~~~~

**LLM API key not set**
    - Ensure that your LLM API key is set correctly; see :ref:`Configuration CLI` for more details.

**LLM model not supported**
    - Ensure that the LLM model you are using is supported; see :ref:`Configuration CLI` for more details.

**LLM timeout**
    - Ensure that the LLM timeout is set correctly; see :ref:`Configuration CLI` for more details.
    - If you are using a local model, ensure that `Ollama <https://ollama.com/>`_ is running and that the model is available.

**LLM parsing problem**
    If you look at the output of the LLM, you will see a JSON object.  If you don't see what you expect inside the JSON object, it is likely that the LLM did not parse the document correctly.  You can try to parse the document deterministically by not supplying a ``llm_config`` and ``use_llm=True`` to the :class:`~wyrdcraeft.DocumentIngestor`.
