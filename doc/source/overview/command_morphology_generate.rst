``wyrdcraeft morphology build`` (removed)
===========================================

.. warning::
   The ``wyrdcraeft morphology build`` command was removed in Phase B of the
   unified dictionary workflow. Morphology generation now runs through the
   dictionary build pipeline.

Use the unified build instead:

.. code-block:: bash

    wyrdcraeft dictionary build --source data/oe_bt.txt --with-morphology

Morphology is regenerated automatically when the ``forms`` table is empty.
Pass ``--with-morphology`` to force regeneration when forms already exist.

See :doc:`command_dictionary_index_bt` for the unified dictionary build command
and :doc:`command_morphology_query` for morphology row lookup.
