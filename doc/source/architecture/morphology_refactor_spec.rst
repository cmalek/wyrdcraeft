Morphology Refactor Specification
=================================

Summary
-------

This document defines module boundaries for the morphology refactor while
preserving strict output parity with current snapshot contracts.

Invariants
----------

1. Output parity for stages ``manual``, ``verb``, ``adj``, ``adv``, ``num``, and
   ``noun`` is required unless an explicit behavior-change PR is approved.
2. Full-flow subset snapshot hash must remain stable.
3. Existing compatibility import paths in
   ``wyrdcraeft.services.morphology.processors`` and
   ``wyrdcraeft.services.morphology.generators.common`` remain valid.
4. Known parity quirks are contractual and are not silently normalized.

Contracts
---------

Contracts are defined in ``wyrdcraeft/services/morphology/contracts.py``.

- ``Rule``: ``apply(word, context) -> list[str]``
- ``RuleSet``: ordered list of ``Rule`` instances
- ``ParadigmAssigner``: ``assign(session) -> None``
- ``FormEmitter``: ``emit(form_record, output) -> None``
- ``FormWriter``: protocol with ``write(str)``

Module Map
----------

Assigners
~~~~~~~~~

- ``wyrdcraeft/services/morphology/assigners/verb.py``
- ``wyrdcraeft/services/morphology/assigners/adj.py``
- ``wyrdcraeft/services/morphology/assigners/noun.py``

Generation
~~~~~~~~~~

- ``wyrdcraeft/services/morphology/generation/verb_engine.py``
- ``wyrdcraeft/services/morphology/generation/shared.py``
- ``wyrdcraeft/services/morphology/generation/dispatch.py``

Compatibility Layers
--------------------

- ``wyrdcraeft/services/morphology/processors.py`` re-exports assigner entrypoints.
- ``wyrdcraeft/services/morphology/generators/common.py`` retains wrapper
  entrypoints and delegates verb orchestration to the generation package.

Guardrail Reports
-----------------

Warning-mode guardrail scripts for maintainers:

- ``scripts/morphology/report_quality_guardrails.py``
- ``scripts/morphology/generate_refactor_baseline.py``
