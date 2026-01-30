# wyrdcraeft

A pipeline to convert Old English source texts into a canonical JSON structure.

## Quick start (tests)
```bash
python -m pip install -e .
pytest
```

## Next steps
- Implement `load_elements()` and `normalize_elements_to_blocks()` using `unstructured`.
- Add langextract integration tests that produce JSON from prompts.


## LangExtract (live) smoke test
Set an API key and run:
```bash
export LANGEXTRACT_API_KEY="..."
pytest -k langextract
```

## Using langextract in code
```python
from pathlib import Path
from oe_ingest.schema.models import TextMetadata
from oe_ingest.ingest.pipeline import ingest_with_langextract

doc = ingest_with_langextract(
    Path("some_oe_source.pdf"),
    TextMetadata(title="Some OE Text", source="..."),
    model_id="gemini-2.5-flash",
)

print(doc.model_dump(mode="json", exclude_none=True))
```


## Per-section prompt selection
When using `ingest_with_langextract()`, the pipeline chooses prompts based on provisional section kind:
- `oe_extract_prose_v1.1.md` for prose sections
- `oe_extract_verse_v1.1.md` for verse sections

## Confidence propagation
The pipeline propagates confidence upward:
- Section confidence becomes the minimum confidence observed in its subtree (ignoring nulls).

## TEI bridge
A minimal TEI import/export bridge exists at:
- `oe_ingest.ingest.exporters.tei.to_tei(doc) -> str`
- `oe_ingest.ingest.exporters.tei.from_tei(xml: str) -> OldEnglishText`


## Auto ingestion
```python
from pathlib import Path
from oe_ingest.schema.models import TextMetadata
from oe_ingest.ingest.pipeline import ingest_auto

doc = ingest_auto(
    Path("text.tei"),
    TextMetadata(title="...", source="..."),
)
```

- If the file suffix is `.tei` or `.xml` and `prefer_tei=True`, TEI override mode is used (no unstructured/LLM).
- Otherwise, it uses `ingest_with_langextract()` by default (chunked + mixed-aware + speaker-aware).


## Prompt preambles (speaker hints)
When using langextract, the pipeline may pass a **prompt preamble** to the LLM.
This is used for soft guidance (e.g. speaker hints) without polluting metadata
or altering the source text.

The preamble is prepended to the prompt and never stored in the output JSON.
