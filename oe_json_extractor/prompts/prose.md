MODE: PROSE

Interpret the input as prose, not verse.

Structural rules:
- Represent content using `paragraphs`, not `lines`.
- Set `lines = null`.
- Set `paragraphs` to an array of Paragraph objects.

Paragraph handling:
- Preserve paragraph boundaries if they are explicit or strongly implied.
- If paragraph boundaries are unclear, inconsistent, or editorially uncertain,
  treat the entire input as a single paragraph.
- Do NOT invent paragraph breaks.

Sentence handling:
- Within each paragraph, represent content as sentences.
- Split sentences conservatively.
- Prefer fewer, longer sentences if boundaries are unclear.
- Do NOT split sentences based solely on capitalization, conjunctions,
  or clause boundaries.
- Do NOT invent sentence numbering.

Dialogue:
- If the prose contains dialogue, continue to use Paragraph → Sentence structure.
- Do NOT switch to line-based representation in prose mode.
- Assign `speaker` only if explicitly indicated in the text.

Ambiguity:
- If prose structure is ambiguous at any level, choose the most conservative option
  and lower the confidence value accordingly.