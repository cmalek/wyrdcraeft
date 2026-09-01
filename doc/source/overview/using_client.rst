Configuration: Python Client
============================

This guide covers how to use the ``wyrdcraeft`` Python client.

Direct Configuration
~~~~~~~~~~~~~~~~~~~~

Configure the client directly in Python using the :class:`~wyrdcraeft.DocumentIngestor` class:

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

TEI Ingestor
^^^^^^^^^^^^

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

Convert accepts a local ``.txt`` or TEI/XML path only. HTML, PDF, HTTP fetch,
and LLM extraction are not part of this package.
