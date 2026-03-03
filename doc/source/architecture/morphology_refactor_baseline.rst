Morphology Refactor Baseline
============================

This page records the parity and quality baseline captured for the morphology
refactor rollout.

Artifact
--------

The canonical machine-readable baseline is stored at:

- ``tests/morphology/data/refactor_baseline.json``

Recorded Snapshot Hashes
------------------------

- ``manual``: ``ec602888b0a6bf76cf5aa2c21d81d7e41848073d8bf5847fcb6bec9111a32048``
- ``verb``: ``011ec15f4b0780aa14eb2c71fcd4be109c632b85e3c3c2e579d5398423663c63``
- ``adj``: ``66fec967b8986e28bc08dd374e542dac15e0051c55f94a869403309a38ed284e``
- ``adv``: ``38a509d6c81c8701529b9f0cab747512f10e54c2682c4d1ba0b5ad9665bad039``
- ``num``: ``bae1aa4edd9e5bc1e07652fa5fbeac7d3794c497a54eaa39c07a359b5e849a08``
- ``noun``: ``6c344a9c2dcd26fb815ad2566cabbcee3b3585fb6deaaecc9bc8c6b867b01fbb``
- ``full_flow``: ``89fbea5164d269f87b17af3c9fef55ff2ba07fce34ded245e48929e39f3623f8``

Runtime Baseline
----------------

- Subset full-flow runtime: ``176.564 ms``

Mypy Baseline
-------------

The baseline JSON records the current output of
``.venv/bin/mypy wyrdcraeft tests`` and currently reports success.
