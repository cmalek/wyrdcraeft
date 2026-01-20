.. _api_client:

Client API
==========

Entrypoint for ingesting documents
----------------------------------

:class:`oe_json_extractor.DocumentIngestor` is the primary entrypoint for converting documents into the :class:`~oe_json_extractor.models.OldEnglishText` model, specifically in its :meth:`~oe_json_extractor.DocumentIngestor.ingest` method.  This is a factory class that will choose the appropriate converter based on the source type.

.. autoclass:: oe_json_extractor.DocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

Heuristic Ingestor
^^^^^^^^^^^^^^^^^^

:class:`oe_json_extractor.HeuristicDocumentIngestor` is a simple converter that will use deterministic heuristics to convert documents into the :class:`~oe_json_extractor.models.OldEnglishText` model, specifically in its :meth:`~oe_json_extractor.HeuristicDocumentIngestor.ingest` method.  This is a good choice for documents that are not well-structured or that are not well-suited for LLM-based ingestion.

.. autoclass:: oe_json_extractor.HeuristicDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

TEI Ingestor
^^^^^^^^^^^^

:class:`oe_json_extractor.TEIDocumentIngestor` is an ingestor that will use the `TEI <https://tei-c.org/>`_ XML format to ingest documents.  This is a good choice for documents that are in the TEI XML format.  It will load the document from the source path and then use the TEI XML parser to parse the document, with minimal or no additional processing.

.. autoclass:: oe_json_extractor.TEIDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

LLM Ingestor
^^^^^^^^^^^^

:class:`oe_json_extractor.LLMDocumentIngestor` is an ingestor that will use an LLM to ingest documents.  This is a a work in progress and is generally not a good choice for ingesting documents, because it still gets a lot of things wrong, especially verse.
This is why it is not the default ingestor.

.. autoclass:: oe_json_extractor.LLMDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance: