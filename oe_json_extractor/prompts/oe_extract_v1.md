You are extracting Old English (Anglo-Saxon) source text into a strict JSON schema.

Non-negotiable rules:
- DO NOT invent, normalize, translate, or paraphrase text.
- Preserve original order exactly.
- Do NOT include commentary, footnotes, apparatus, or Modern English.
- Do NOT embed structure (numbers/headings/speakers) into the text fields.
- If uncertain, choose the minimal valid structure and leave optional fields null.

Output must be valid JSON with UTF-8 text.

Schema (output exactly these keys; omit keys only if value is null):
{
  "sections": [
    {
      "number": "string|int|null",
      "title": "string|null",
      "paragraphs": [
        {
          "speaker": "string|null",
          "sentences": [
            {
              "text": "string",
              "number": "string|int|null",
              "confidence": "number|null"
            }
          ],
          "confidence": "number|null"
        }
      ],
      "lines": [
        {
          "text": "string",
          "number": "int|null",
          "speaker": "string|null",
          "confidence": "number|null"
        }
      ],
      "confidence": "number|null"
    }
  ]
}

Structure mapping:
- Prose => paragraphs => sentences
- Poetry => lines only
- Dialogue => use speaker field on paragraphs or lines

Important constraint:
- Never mix "paragraphs" and "lines" in the same section. If a source interleaves prose and verse, create subsections instead.

Confidence:
- Provide confidence scores only when you have strong reason (0.0–1.0). Otherwise use null.
