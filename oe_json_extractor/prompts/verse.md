MODE: VERSE

Interpret the input as verse (poetry), not prose.

Structural rules:
- Represent content using `lines`, not `paragraphs`.
- Set `paragraphs = null`.
- Set `lines` to an array of Line objects.
- Preserve the original line order exactly.

Line handling:
- Each explicit line break in the source text should normally produce one `Line.text`.
- Do NOT merge lines.
- Do NOT split lines unless the source clearly contains multiple lines on one physical line (rare).
- Preserve all original spelling, punctuation, and capitalization exactly.

Numbering:
- If explicit line numbers appear in the source (e.g. `1`, `[1]`, `1.`), set `Line.number`.
- Otherwise, set `Line.number = null`.
- Do NOT invent or infer numbering.

Speakers:
- Only set `Line.speaker` if the source text explicitly indicates a speaker
  (e.g. `X cwæð:`, `X:`).
- Speaker labels must NOT be included in `Line.text`.

Ambiguity:
- If it is unclear whether something is a heading or a line of verse,
  prefer treating it as a line of verse.
- If the text alternates between verse and prose, extract ONLY the verse
  content in this mode.

Confidence:
- Assign confidence per line.
- Use lower confidence if verse boundaries or speaker attribution are uncertain.