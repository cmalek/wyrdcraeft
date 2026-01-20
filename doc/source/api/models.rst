.. _api_models:

Models
======

JSON Schema for Old English Texts
---------------------------------

.. _schema_models:

The JSON schema for Old English texts is defined in the `models.py` file.

.. autodoc_pydantic:: oe_json_extractor.models.schema
    :members:
    :undoc-members:
    :show-inheritance:

Parsing related models
----------------------

The parsing related models are defined in the `parsing.py` file.

.. autodoc_pydantic:: oe_json_extractor.models.parsing
    :members:
    :undoc-members:
    :show-inheritance:

LLM related models
-------------------

The LLM related models are defined in the `llm.py` file.

.. autodoc_pydantic:: oe_json_extractor.models.llm
    :members:
    :undoc-members:
    :show-inheritance:
