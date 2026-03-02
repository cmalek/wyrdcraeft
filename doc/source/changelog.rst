CHANGELOG
=========

1.1.0 (2026-03-02)
------------------

Breaking changes
^^^^^^^^^^^^^^^^

- Removed the top-level ``convert`` command. Use ``wyrdcraeft source convert`` instead.

Enhancements
^^^^^^^^^^^^

- ``wyrdcraeft diacritic disambiguate`` command now shows more candidate forms and more rows in the Bosworth-Toller assist table.
- ``wyrdcraeft diacritic add``: allow adding or overwriting a unique entry in the macron index.
- ``wyrdcraeft diacritic delete``: allow deleting a unique entry from the macron index.
- ``wyrdcraeft source mark-diacritics`` now outputs a new ``.unknown.txt`` file listing words that were not found in the macron index.
- ``wyrdcraeft source mark-diacritics`` now uses filename defaults based on the input filename instead of requiring explicit output paths to be provided.
- Updated the Tichý morphological generator code to use macrons instead of acutes, to match how the rest of the project handles diacritics.

Refactorings
^^^^^^^^^^^^

- Refactored the CLI code to be more organized and easier to maintain.
- Moved all ``@dataclass`` and ``pydantic`` models to the ``wyrdcraeft.models`` module.

Data changes
^^^^^^^^^^^^

- Disambiguated some more ambiguous entries in the macron index.

1.0.0 (2026-03-01)
------------------

Enhancements
^^^^^^^^^^^^

- Initial release.
