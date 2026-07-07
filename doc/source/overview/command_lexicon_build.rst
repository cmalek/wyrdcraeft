``wyrdcraeft lexicon build`` (removed)
========================================

.. warning::
   The ``lexicon`` CLI group and ``lexicon build`` command were removed in Phase B
   of the unified dictionary workflow. There is no separate search-index rebuild
   step.

Browse search now queries ``bt_entries`` and ``bt_variants`` directly at runtime.
Rebuild dictionary and morphology source data with the unified build instead:

.. code-block:: bash

    wyrdcraeft dictionary build --source data/oe_bt.txt --with-morphology

See :doc:`command_dictionary_index_bt` for the unified dictionary build command
and :doc:`command_dictionary_browse` for the browse shell.
