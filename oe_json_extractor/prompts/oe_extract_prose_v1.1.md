You are extracting Old English (Anglo-Saxon) source text into a strict JSON schema.

This is version v1.1, stricter than v1.

Non-negotiable rules:
- DO NOT invent, normalize, translate, or paraphrase text.
- Preserve original order exactly.
- Output Old English text only in text fields.
- Remove/ignore footnotes, commentary, apparatus, running headers/footers.
- Do NOT embed structure into text fields (no verse numbers, no speaker labels, no chapter headings).

When structure is ambiguous:
- Prefer ONE section with minimal nesting.
- Prefer prose paragraphs unless hard line breaks indicate verse.
- If speaker labels like “X cwæð:” exist, treat the following content as dialogue by that speaker.

Output must be valid JSON with UTF-8 text.

Schema:
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

Hard constraints:
- A section may contain paragraphs OR lines OR subsections, but not both paragraphs and lines.
- Never drop OE content; if uncertain about a boundary, keep the content and leave metadata null.

Confidence scoring:
- Set confidence on each sentence/line when:
  - You removed obvious editorial noise (lower confidence if uncertain)
  - Speaker assignment is inferred (lower confidence)
  - Verse/prose classification is uncertain (lower confidence on enclosing section)
- Suggested values:
  - 0.95–1.0: exact extraction, obvious structure
  - 0.7–0.9: minor uncertainty
  - 0.4–0.7: significant uncertainty (still must not invent text)


Additional instruction (prose mode):
- Treat the input as PROSE. Prefer paragraphs/sentences. Do not output lines.
