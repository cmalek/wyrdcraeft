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
- **Convert** to a standard JSON format via deterministic heuristics, TEI parsing, or LLM-based extraction.
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

## Quick start

**Command line:** convert a text file to JSON:

```bash
wyrdcraeft convert --title="My Title" input.txt output.json
```

**Python:** use `DocumentIngestor` to get an `OldEnglishText` model:

```python
from wyrdcraeft import DocumentIngestor, TextMetadata

metadata = TextMetadata(
    title="The Anglo-Saxon Chronicle",
    source="https://example.org/source.txt",
)
oe_json = DocumentIngestor().ingest(
    source_path="path/to/source.txt",
    metadata=metadata,
)
```

For TEI XML, pass a `.xml` path; `DocumentIngestor` will use the TEI ingestor. For LLM-based extraction, use `ingest(..., use_llm=True, llm_config=...)`. See the full documentation for configuration and options.

## Documentation

Full documentation (installation, quickstart, CLI, Python client, configuration, FAQ): [https://oe_json_extractor.readthedocs.io](https://oe_json_extractor.readthedocs.io)

## Contributing and license

Contributing and coding standards are described in the documentation (runbook). This project is licensed under the MIT License — see [LICENSE.txt](LICENSE.txt).

---

## Licensing and Provenance

### Bosworth-Toller Old English Dictionary

The OCR extracted text of the Bosworth-Toller Old English Dictionary used in this project is from the [Germanic Lexicon Project](https://www.germanic-lexicon-project.org/). The scanning was done by Jason Burton, B. Dan Fairchild, Margaret Hoyt, Grace Mrowicki, Michael O'Keefe, Sarah Hartman, Finlay Logan, Sean Crist, Thomas McFadden, David Harrison, and Sean Crist; that data is in the public domain.

### Morphological Analyser of Old English

- The Old English morphology generator in `wyrdcraeft` is based on the work of Ondřej Tichý's thesis, [Morphological Analyser of Old English](https://www.researchgate.net/publication/318926182_Morphological_analyser_of_old_english) (2017).
- The upstream morphological generator Perl code and data is (c) Ondřej Tichý, is released under the CC BY 4.0 license. The modified Perl code itself, with Madeleine Thompson's changes, can be found at [github:madeleineth/tichy_oe_generator](https://github.com/madeleineth/tichy_oe_generator).
- Changes made to the morphology generator in this repository by the maintainers of `wyrdcraeft` are released under the MIT license.

### All other code

- All other code implemented directly by Christopher Malek, also released under the MIT license.
