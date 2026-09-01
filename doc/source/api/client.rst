.. _api_client:

Client API
==========

Converting documents to JSON
----------------------------

:class:`wyrdcraeft.DocumentIngestor` is the primary entrypoint for converting documents into the :class:`~wyrdcraeft.models.OldEnglishText` model, specifically in its :meth:`~wyrdcraeft.DocumentIngestor.ingest` method.  This is a factory class that will choose the appropriate converter based on the source type.

.. autoclass:: wyrdcraeft.DocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

Heuristic Ingestor
^^^^^^^^^^^^^^^^^^

:class:`wyrdcraeft.ingest.pipeline.HeuristicDocumentIngestor` is a converter that uses deterministic heuristics to convert local ``.txt`` documents into the :class:`~wyrdcraeft.models.OldEnglishText` model, specifically in its :meth:`~wyrdcraeft.HeuristicDocumentIngestor.ingest` method.

.. autoclass:: wyrdcraeft.ingest.pipeline.HeuristicDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

TEI Ingestor
^^^^^^^^^^^^

:class:`wyrdcraeft.ingest.pipeline.TEIDocumentIngestor` is an ingestor that will use the `TEI <https://tei-c.org/>`_ XML format to ingest documents.   It will load the document from the source path and then use the TEI XML parser to parse the document, with minimal or no additional processing.

.. autoclass:: wyrdcraeft.ingest.pipeline.TEIDocumentIngestor
    :members:
    :undoc-members:
    :show-inheritance:

Diacritical Marking
-------------------

These classes are used to mark diacritical marks in Old English text that lack them, based on a pre-built index of attested forms from the Bosworth-Toller Old English Dictionary and ``g`` and ``c`` palatalization rules. ``c`` palatalization follows historically informed rules (e.g. ``c`` before /i, iː/ or word-initial before other front vowels; ``c`` after /i/, /iː/ unless a back vowel follows), a pre‑i‑mutation “only back” heuristic, and a blocklist for i‑mutation exceptions; ``sc`` → ``sċ`` is planned as a separate follow‑up.

.. autoclass:: wyrdcraeft.services.markup.MacronApplicator
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: wyrdcraeft.services.markup.GPalatalizer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: wyrdcraeft.services.markup.CPalatalizer
    :members:
    :undoc-members:
    :show-inheritance:

Morphology Generation
---------------------

:class:`wyrdcraeft.services.morphology.GeneratorSession` is a service that will generate morphology forms with an input of the words in the Bosworth-Toller Old English Dictionary, and an output of all inflected forms of those words.

.. important::
    Not all the forms that will be generated are attested in extant Old English corpora.

.. autoclass:: wyrdcraeft.services.morphology.GeneratorSession
    :members:
    :undoc-members:
    :show-inheritance:


Utilities
---------

.. autoclass:: wyrdcraeft.services.syllable.OESyllableBreaker
    :members:
    :undoc-members:
    :show-inheritance:

.. autofunction:: wyrdcraeft.services.markup.normalize_old_english

.. autoclass:: wyrdcraeft.services.morphology.text_utils.OENormalizer
    :members:
    :undoc-members:
    :show-inheritance: