---
status: accepted
---

# Dictionary browse shows an entry as one sectioned column

The browse TUI draws every part of an entry in one font, one foreground, one background and uniform spacing. Entry text sits in a top half-pane and the paradigm in a bottom pane with its own scroll. This ADR replaces that layout. It changes presentation only. Query, ranking, decode and sidebar logic stay where ADR 0014 put them. Forms rendering is ADR 0027. Copy, the results preview and focus are ADR 0028. Design mockup: `doc/source/_images/interface.jpg`.

## Layout

A terminal draws one cell size, so rank comes from weight, colour role, caps, rules and blocks, never from font size.

- Search input, one row of diacritic insert chips, results pane on the left, entry pane on the right, footer that lists only the keys that are live.
- Panes use rounded titled borders. The focused pane takes the accent border **and** an accent title, so focus is never carried by colour alone (unfocused borders are 1.35:1 against the panel on purpose).
- The entry pane is one scrolling column. A banner (tinted block, accent edge, part-of-speech tag, Copy button) stays pinned. Below it scroll a key/value block, then `Senses`, `Etymology` and `Forms`. Each section has a dim caps label with a hairline rule.
- A section with no content is not drawn, label included. A preposition, conjunction or interjection has no `Forms` section.
- Palette (dark): ground `#101319`, panel `#151922`, selected row `#232a38`, border `#2a3140`, text `#dbe0ea`, label `#8c95a8`, accent `#e6b36a`, Old English forms `#8fd0c4`. The lowest text pair, label on the selected row, is 4.78:1; every tag pair is 7:1 or better. Defined once as a Textual `Theme`; widgets use theme variables, not hex.

## Results rows

- One cell of padding above and below the text, so a row is three cells tall without a second line of text. The row holds, left to right: headword, a dim definition line (ADR 0028), the part-of-speech tag.
- A hyphen inside a headword (`for-sceamian`) is drawn dim.
- When the hit matched a variant, the row shows the matched text first, then `→ headword` dim. This replaces the `matched (headword, pos)` text, which repeated the part of speech now carried by the tag.
- Part of speech tags are tinted per part of speech and differ in lightness as well as hue.

## Key/value block

Rows, each drawn only when it has a value: `Variants`, `Class`, `Gender`, `Source`. `Source` is today's `Provenance` label.

**Class** shows the stored morph-class `display_label`, and only for verbs, nouns and adjectives. An entry of any other part of speech has no Class row: adverbs, prepositions, pronouns, conjunctions, interjections, and entries whose part of speech is `unknown` (an interjection stored as `unknown` is one). A verb, noun or adjective with no assigned class shows `unclassified` dimmed, so a data gap stays visible. A leading `verb, ` is removed from the label (`verb, weak class 2` shows as `weak class 2`). The part of speech is already in the banner tag. The stored label is unchanged.

## Senses and etymology

- Sub-senses (`5a`, `10c`) are indented and their number is dim. Main sense numbers are accent and bold.
- The `Summary` block is dropped when its text equals sense 1 after the ADR 0025 reading. Otherwise it shows as the first line of `Senses`.
- Etymology is a table of language, word, meaning and source. A column with no value in any row is dropped, so the usual two-column case shows only language and word. A `Note:` line shows under the table. A Bosworth-Toller source abbreviation such as `Piers P. Chauc.`, `Laym.`, `Orm.` or `Plat.` stands in for Middle English and goes in the language column, and the form that follows it goes in the word column. Labels come from the `spellings` in `wyrdcraeft/etc/dictionary/bosworth_and_toller_abbreviations.json`.

## Considered Options

- **Keep two stacked panes.** Two scroll regions stay and long variant lists still overflow.
- **Different font sizes.** Not available in a terminal cell grid.
- **Keep the Class row for every part of speech and show `Unclassified`.** It reads as a defect on parts of speech that have no classes.
- **Hide the Class row whenever the class is unclassified.** A noun that should have a class and has none is a data gap the user wants to see.
- **Keep `matched (headword, pos)` in the row.** It repeats the tag and hides the headword in a long list.

## Consequences

- The footer key list in the mockup is the starting set. Keys that cannot act in the current focus are not shown.
- Entry formatting in `browse_tui.py` (`_format_entry_details` and the morph-class line) is replaced by section widgets. Tests that assert the old plain-text lines are rewritten.
- The mockup did not show nouns, adverbs, prepositions, pronouns, conjunctions or interjections. They follow these rules and ADR 0027.
