.. _api_client:

Client API
==========

Entrypoint for ingesting documents
----------------------------------

:class:`wyrdcraeft.DocumentIngestor` is the primary entrypoint for converting documents into the :class:`~wyrdcraeft.models.OldEnglishText` model, specifically in its :meth:`~wyrdcraeft.DocumentIngestor.ingest` method.  This is a factory class that will choose the appropriate converter based on the source type.

.. autoclass:: wyrdcraeft.DocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

Heuristic Ingestor
^^^^^^^^^^^^^^^^^^

:class:`wyrdcraeft.HeuristicDocumentIngestor` is a simple converter that will use deterministic heuristics to convert documents into the :class:`~wyrdcraeft.models.OldEnglishText` model, specifically in its :meth:`~wyrdcraeft.HeuristicDocumentIngestor.ingest` method.  This is a good choice for documents that are not well-structured or that are not well-suited for LLM-based ingestion.

.. autoclass:: wyrdcraeft.HeuristicDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

TEI Ingestor
^^^^^^^^^^^^

:class:`wyrdcraeft.TEIDocumentIngestor` is an ingestor that will use the `TEI <https://tei-c.org/>`_ XML format to ingest documents.  This is a good choice for documents that are in the TEI XML format.  It will load the document from the source path and then use the TEI XML parser to parse the document, with minimal or no additional processing.

.. autoclass:: wyrdcraeft.TEIDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

LLM Ingestor
^^^^^^^^^^^^

:class:`wyrdcraeft.LLMDocumentIngestor` is an ingestor that will use an LLM to ingest documents.  This is a a work in progress and is generally not a good choice for ingesting documents, because it still gets a lot of things wrong, especially verse.
This is why it is not the default ingestor.

.. autoclass:: wyrdcraeft.LLMDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance: