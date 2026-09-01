# wyrdcraeft

Process Old English texts into structured JSON and generate morphology.

## Why wyrdcraeft?

If you work with Old English (Anglo-Saxon) texts - editions, corpora, translation tooling, or digital humanities projects - you often need a single pipeline that turns raw or marked-up sources into a consistent, machine-readable form. **wyrdcraeft** provides that.

- It ingests plain text and TEI XML, converts them into a standard JSON schema that is prose, verse and dialogue aware
- Provides diacritic restoration Old English texts that have no diacritic marks.
- Includes an Old English morphology generator based on established lexical and grammatical resources.
- Provides other minor utilities for working with Old English text.

Use it from the command line or from Python, and avoid ad-hoc scripts and format fragmentation.

## Features

- **Ingest** Old English texts from **text files** and **TEI XML**.
- **Convert** to a standard JSON format via deterministic heuristics or TEI parsing.
- **Handle** both prose and verse (paragraphs, verse lines, dialogue, sections).
- **Generate** Old English morphology forms using the migrated Python implementation from Ondřej Tichý's Perl-based generator (based on the Bosworth & Toller, *An Anglo-Saxon Dictionary*, 1898,  and Wright & Wright,  *Old English Grammar*, 1908).
- **Diacritic workflows**: macron restoration and disambiguation tooling for normalized forms.

## Installation

**Prerequisites:** Python 3.11–3.13.

From PyPI with pip:

```bash
pip install wyrdcraeft
wyrdcraeft --help
```

With [uv](https://docs.astral.sh/uv/):

```bash
sh -c "$(curl -fsSL https://astral.sh/uv/install)"
uv tool install wyrdcraeft
wyrdcraeft --help
```

With [pipx](https://pipx.pypa.io/stable/):

```bash
pipx install wyrdcraeft
wyrdcraeft --help
```

From source (development):

```bash
git clone https://github.com/cmalek/wyrdcraeft.git
cd wyrdcraeft
uv sync --dev
```

## Canonical database

Morphology and dictionary data live in one SQLite file:
**`wyrdcraeft.sqlite3`** under the OS application-data directory (override with
`WYRDCRAEFT_APP_DATA_DIR` or `app_data_dir` in `.wyrdcraeft.toml`).

On first run (or after a schema upgrade), wyrdcraeft checks the database,
applies Alembic migrations, and keeps a backup copy. If an older
**`morphology.sqlite3`** is found, it is backed up and replaced with a fresh
canonical database; the CLI then prints a rebuild recipe.

Rebuild from scratch:

```bash
wyrdcraeft dictionary build --with-morphology
```

Use `--source PATH` to index a custom Bosworth-Toller file instead of the
packaged default (`wyrdcraeft/etc/dictionary/oe_bt.txt`).

## Documentation

Full documentation (installation, quickstart, CLI, Python client, configuration, FAQ): [https://wyrdcraeft.readthedocs.io](https://wyrdcraeft.readthedocs.io)

For `wyrdcraeft dictionary browse`, the search field accepts direct Old English
characters including `æ Æ ð Ð þ Þ ā Ā ē Ē ī Ī ō Ō ū Ū ȳ Ȳ ǣ Ǣ ċ Ċ ġ Ġ`. On macOS
with the `ABC Extended` keyboard layout, those keys are supported directly in
the browse input; on other terminals or keyboard layouts, direct typing may
also work, and the on-screen character buttons remain available as a fallback.

## Contributing, Licensing and Provenance

## Contributing

Contributing and coding standards are described in the documentation (runbook).

## Licensing and Provenance

### Bosworth-Toller Old English Dictionary

The OCR extracted text of the Bosworth-Toller Old English Dictionary used in this project is from the [Germanic Lexicon Project](https://www.germanic-lexicon-project.org/). The scanning was done by Jason Burton, B. Dan Fairchild, Margaret Hoyt, Grace Mrowicki, Michael O'Keefe, Sarah Hartman, Finlay Logan, Sean Crist, Thomas McFadden, David Harrison, and Sean Crist; that data is in the public domain.

### Morphological Analyser of Old English

- The Old English morphology generator in `wyrdcraeft` is based on the work of Ondřej Tichý's thesis, [Morphological Analyser of Old English](https://www.researchgate.net/publication/318926182_Morphological_analyser_of_old_english) (2017).
- The upstream morphological generator Perl code and data is (c) Ondřej Tichý, is released under the CC BY 4.0 license. The modified Perl code itself, with Madeleine Thompson's changes, can be found at [github:madeleineth/tichy_oe_generator](https://github.com/madeleineth/tichy_oe_generator).
- Changes made to the morphology generator in this repository by the maintainers of `wyrdcraeft` are released under the MIT license.

### All other code

- All other code implemented directly by this project's maintainers are also released under the MIT license.
