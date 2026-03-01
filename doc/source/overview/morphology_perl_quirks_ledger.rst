Morphology Perl Compatibility Quirks Ledger
===========================================

This document tracks known ``create_dict31.pl`` behaviors that are preserved
intentionally in Python for compatibility.

Policy
------

- Default behavior remains Perl-compatible.
- Do not "fix" these quirks in the default path.
- Any normalized behavior must be opt-in and documented as intentionally
  non-parity.

Q1: Hash-order-driven comparative/superlative probability
----------------------------------------------------------

Perl source
~~~~~~~~~~~

- ``create_dict31.pl:6853-6855`` (comparative)
- ``create_dict31.pl:7160-7162`` (superlative)

Behavior
~~~~~~~~

- Perl deduplicates ``@title_array`` with ``%hash`` and then iterates
  ``keys %hash``.
- Probability is derived from ``$y`` (``$probability = abs($y - 2)``), so
  hash-key order affects emitted ``probability``.

Python compatibility behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- In full-flow mode, prior parity work queried Perl-style key ordering.
- In differential oracle mode, deterministic lexical ordering was used.

Regression lock
~~~~~~~~~~~~~~~

- ``tests/test_perl_quirks.py::test_participle_comparative_probability_uses_perl_order``

Q2: Cross-phase probability carry into numeral ``-ena`` forms
--------------------------------------------------------------

Perl source
~~~~~~~~~~~

- ``create_dict31.pl:7187`` (``$probability = abs($y - 2)`` in adjective generation)
- ``create_dict31.pl:8327``, ``8370``
  (``$formhash{"probability"} = $probability + 1`` in numeral ``PoPl*Ge -ena``)

Behavior
~~~~~~~~

- Numeral ``-ena`` probabilities depend on mutable shared ``$probability`` state
  after adjective generation in full flow.
- Isolated numeral generation behaves differently from full flow.

Python compatibility behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Python keeps explicit compatibility state in ``GeneratorSession`` and applies
  carry only in full-flow mode.
- Differential oracle mode keeps isolated numeral behavior.

Regression lock
~~~~~~~~~~~~~~~

- ``tests/test_perl_quirks.py::test_num_ena_probability_carry_is_full_flow_only``

Q3: ``probability`` undefined vs ``"0"`` output semantics
-----------------------------------------------------------

Perl source
~~~~~~~~~~~

- ``create_dict31.pl:9898-9900`` (prints ``$form{probability}`` as-is)
- ``create_dict31.pl:9903-9907``
  (double-consonant alternate increments ``$form{probability}``)

Behavior
~~~~~~~~

- Undefined probability prints as empty field.
- Literal ``"0"`` prints as ``"0"`` (not empty).
- Reduced-form duplicate uses incremented probability.

Python compatibility behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``print_one_form`` preserves empty-vs-zero distinction and reduced-form
  increment behavior.

Regression lock
~~~~~~~~~~~~~~~

- ``tests/test_perl_quirks.py::test_print_one_form_probability_empty_vs_zero``

Q4: Opt-in r-stem noun extension (non-parity)
----------------------------------------------

Flag
~~~~

- CLI: ``--enable-r-stem-nouns``
- Session: ``GeneratorSession.enable_r_stem_nouns``

Behavior
~~~~~~~~

- When enabled, noun assignment and generation add support for r-stem noun
  paradigms (``fæder``, ``bróþor``, ``módor``, ``dóhtor``, ``sweostor``).
- This extension is intentionally outside Perl parity.

Parity implications
~~~~~~~~~~~~~~~~~~~

- Default behavior keeps ``enable_r_stem_nouns=False``, preserving
  ``create_dict31.pl`` compatibility.
- Differential parity protocol and assertions are unchanged in default mode.
