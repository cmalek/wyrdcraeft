``wyrdcraeft diacritic disambiguate``
======================================

The ``wyrdcraeft diacritic disambiguate`` command is a maintainer-facing
interactive tool for curating ambiguous entries in the macron index JSON.

Command syntax
--------------

.. code-block:: bash

    # Iterate all ambiguous normalized forms
    wyrdcraeft diacritic disambiguate

    # Edit a single normalized form
    wyrdcraeft diacritic disambiguate <normalized_form>

    # Use a custom index path
    wyrdcraeft diacritic disambiguate --index-path /path/to/oe_bt_macron_index.json

Behavior overview
-----------------

The command reads the macron index payload and iterates entries in
``ambiguous``.

On each iteration, the interactive console layout shows:

- top section:
  - current normalized form
- running counts for ``unique`` and ``ambiguous``
- progress counter for the current session
- candidate forms section:
  - attested forms table
  - Bosworth-Toller assist table nested inside the candidate forms area
  - any existing POS code and meaning annotations per form
- available actions, including close

.. code-block:: text

    ╭──────────────────────────────────────────── Disambiguating normalized form: con ─────────────────────────────────────────────╮
    │ Progress                                                                                           4/976                     │
    │ Unique entries                                                                                     39207                     │
    │ Ambiguous entries                                                                                  1049                      │
    │ Completed ambiguous                                                                                76                        │
    ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
    ╭────────────────────────────────────────────────────── Candidate Forms ───────────────────────────────────────────────────────╮
    │ ╭────────────────────── Attested Forms ──────────────────────╮╭───────────── Bosworth-Toller Assist (Page 1) ──────────────╮ │
    │ │ ┏━━━┳━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━┓                      ││ ┏━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓ │ │
    │ │ ┃ # ┃ Attested Form ┃ POS ┃ Meaning ┃                      ││ ┃ Attested ┃ BT Spelling ┃ POS  ┃ Meanings               ┃ │ │
    │ │ ┡━━━╇━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━┩                      ││ ┡━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩ │ │
    │ │ │ 1 │ con           │ —   │ —       │                      ││ │ con      │ con         │ —    │ I know, he knows; I,   │ │ │
    │ │ │ 2 │ cōn           │ —   │ —       │                      ││ │          │             │      │ he can                 │ │ │
    │ │ └───┴───────────────┴─────┴─────────┘                      ││ │ cōn      │ cōn         │ adj. │ bold                   │ │ │
    │ │                                                            ││ └──────────┴─────────────┴──────┴────────────────────────┘ │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ │                                                            ││                                                            │ │
    │ ╰────────────────────────────────────────────────────────────╯╰────────────────────────────────────────────────────────────╯ │
    ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
    ╭────────────────────────────────────────────── Actions (Close button: press q) ───────────────────────────────────────────────╮
    │ c  Choose one form and commit                                                                                                │
    │ r  Replace with an explicit unique form                                                                                      │
    │ d  Define POS code + modern meaning for each form                                                                            │
    │ m  Mark ambiguous entry as completed                                                                                         │
    │ a  Add a new entry, then annotate all forms                                                                                  │
    │ x  Delete one entry (requires 2+ forms)                                                                                      │
    ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
    Action [c/r/d/m/a/x/s/q] (s):


Actions
-------

At each entry, choose one action:

- ``c``: choose a single attested form to keep
- ``r``: replace with an explicit unique form and commit
- ``d``: define linguistic metadata for each attested form
- ``m``: mark ambiguous entry as completed (hide from default iteration)
- ``a``: add one attested form, then annotate all forms
- ``x``: delete one attested form (requires at least two forms)
- ``s``: skip with no changes
- ``q``: close immediately

Choose flow
~~~~~~~~~~~

When you choose ``c``:

1. Select the attested form index.
2. Confirm commit (``y``/``n``/``q``).
3. On ``y``:
   - remove the normalized key from ``ambiguous``
   - set ``unique[normalized_key] = selected_form``
   - remove any stale ``ambiguous_metadata`` for that key
   - write the file to disk immediately

Replace flow
~~~~~~~~~~~~

When you choose ``r``:

1. Enter the explicit replacement text to store as the unique value.
2. Confirm commit (``y``/``n``/``q``).
3. On ``y``:
   - remove the normalized key from ``ambiguous``
   - set ``unique[normalized_key] = replacement_text``
   - remove any stale ``ambiguous_metadata`` for that key
   - write the file to disk immediately

Define flow
~~~~~~~~~~~

When you choose ``d``, the command prompts for each attested form:

- POS code + modern English meaning for one sense
- optional additional senses for the same attested form (repeat POS + meaning)

The normalized key remains in ``ambiguous`` and the annotations are written to
``ambiguous_metadata`` immediately.

Mark Completed flow
~~~~~~~~~~~~~~~~~~~

When you choose ``m``:

1. The command verifies every attested form has at least one POS/meaning sense.
2. Confirm completion (``y``/``n``/``q``).
3. On ``y``, the key is added to ``ambiguous_completed`` and written immediately.

Completed entries remain in ``ambiguous`` but are excluded from default
``wyrdcraeft diacritic disambiguate`` iteration.

Add flow
~~~~~~~~

When you choose ``a``:

1. Enter one new attested form for the normalized key.
2. Provide POS code + modern English meaning for the new form.
3. Optionally add additional senses for that form.
4. Continue directly through prompts for the existing forms.
5. The updated ``ambiguous`` list and ``ambiguous_metadata`` row are written
   immediately.

The free-text prompts accept Unicode (for example ``ā``, ``ǣ``, ``æ``).
If your terminal emits Option-key sequences like ``^[aa`` instead of ``ā``,
the prompt normalizes those common macron sequences automatically.

Bosworth-Toller assist pane
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each normalized key, the command requests:

.. code-block:: text

    https://bosworthtoller.com/search?q=<normalized_form>

and also searches each attested form (de-duplicated), for example:

.. code-block:: text

    https://bosworthtoller.com/search?q=<attested_form>

Only page 1 is used for each query. For each attested form, the command chooses the closest
search result using this ranking:

1. exact match against BT spelling after acute-to-macron display normalization
2. exact raw spelling match (case-insensitive)
3. exact normalized match
4. prefix proximity on normalized forms
5. smaller edit distance
6. earlier result order on the page

If BT lookup or parsing fails, disambiguation continues with a warning shown in
the Bosworth-Toller assist area and no BT rows for that key.

Delete flow
~~~~~~~~~~~

When you choose ``x``:

1. If fewer than two forms exist, delete is rejected and no file mutation occurs.
2. Otherwise, select the attested form index to remove.
3. Confirm deletion (``y``/``n``/``q``).
4. On ``y``, the selected form is removed from ``ambiguous[normalized_key]``,
   any matching annotation is removed from ``ambiguous_metadata``, and the file
   is written immediately.

Skip and close
~~~~~~~~~~~~~~

- ``s`` moves to the next entry with no mutation.
- ``q`` exits the session at any prompt where close is offered.

Single-key mode
---------------

When ``<normalized_form>`` is provided, only that key is processed.

If the key is not in ``ambiguous``, the command exits non-zero with a
clear error.

POS code set
------------

The command stores these codes:

- ``N``: noun
- ``V``: verb
- ``PRO``: pronoun
- ``ADJ``: adjective
- ``ADV``: adverb
- ``CONJ``: conjunction
- ``PREP``: preposition
- ``INTJ``: interjection
- ``NUM``: number
- ``DET``: determiner/article

Data model writes
-----------------

The command writes to the macron index payload with these top-level fields:

- ``unique``
- ``ambiguous``
- ``ambiguous_metadata``
- ``meta`` (count fields are refreshed on write)

All writes are immediate and atomic so curation progress is preserved even if
you close mid-session.
