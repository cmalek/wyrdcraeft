MODE: VERSE

Interpret the input as verse (poetry), not prose.

Structural rules:
- Represent content strictly using `lines`, never `paragraphs`.
- Set `paragraphs = null`.
- Set `lines` to an array of Line objects.
- Preserve the original line order exactly.

Line handling:
- CRITICAL: Each physical line in the source text MUST correspond to exactly one Line object.
- Do NOT merge physical lines into sentences.
- Do NOT split a physical line into multiple objects, even if it contains a period or semicolon in the middle (the caesura).
- DO NOT collapse multiple spaces. If you see "word1      word2", you MUST preserve those exact spaces in the output.
- Preserve all original spelling, punctuation, capitalization, and whitespace exactly as they appear in each line.
- REMAIN BLIND to grammatical punctuation (like periods) when deciding where a line ends. ONLY the physical line break in the input matters.

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