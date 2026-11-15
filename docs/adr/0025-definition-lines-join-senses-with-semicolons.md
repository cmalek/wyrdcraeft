---
status: accepted
---

# Definition lines join senses with semicolons

A definition line is the single line copied from one dictionary entry into an Ænglisc Toolkit annotation's "Definition of root word" field. The stored gloss is left unchanged. The line is a reading of it. The glosses come from the unclean Bosworth-Toller import. Gender, usage notes, and other apparatus stay off the line. The clean reading of `oe_bt.txt` belongs to `boslexicon`. When that reading replaces a gloss, this same reading still applies. Trello https://trello.com/c/K6lah6MZ.

## Reading

Senses stay in stored order. Inside one sense, in this order:

1. Judge each semicolon before any other rewrite. It becomes ` or ` when the trimmed right-hand piece is one word, a space, and then a complement (`to`, `of`, `for`, `in`, and the other prepositions), and that complement is not already a word in the left-hand piece. Words split on whitespace. A comma before that complement keeps the boundary a list. `can; ought to be done` becomes `can or ought to be done`. `The state; dignity of an abbot` becomes `The state or dignity of an abbot`. A right-hand piece that starts with `to `, `a `, `an `, or `the `, or whose first word is a grammatical abbreviation (`pp`, `pl`, `fut`, `t`, `p`), stays a list. Every other internal semicolon becomes a comma. Pieces are trimmed and empty pieces are dropped. `time; time; date` is `time, time, date` at this step.
2. On a verb, remove a leading `to ` or `To ` from each sense part, including each comma-separated alternative. `to ward off; to guard; to save` becomes `ward off, guard, save`. A complement such as `ought to be done` keeps its `to`.
3. Drop a repeated comma-separated item, word or phrase, case-insensitively, keeping the first. The repeat need not be adjacent. `time, time, date` becomes `time, date`. `ward off, guard, ward off` becomes `ward off, guard`. The same item in a later sense stays.

Join the finished senses with `; `.

## Copying

Dictionary browse keeps a title row pinned above the scrolling entry text: `Details: {headword}` on the left and a `Copy` button on the right. The headword leaves the scrolling body. Part of speech, variants, senses, and etymology stay in the scroll. With no entry selected the row reads `Details` and the button is disabled. The button and the platform copy keys (`ctrl+c`, `super+c`: Ctrl-C on Linux and Windows, Cmd-C on Mac) stay disabled when the selected entry has no definition line. Otherwise they copy that entry. Two parts of speech for one headword are two entries, and the title shows the headword only. The toolkit field stays a paste target.

## Considered Options

- **Number the senses** (`1. … 2. …`). A few hand-edited toolkit annotations use that shape. Old English readers separate senses with semicolons.
- **Leave an internal semicolon as a semicolon.** It would look like a sense break.
- **Write every internal semicolon as ` or `.** Tried first. A gloss list such as `to ward off; to guard; to save` is not one shared complement.
- **Write every internal semicolon as a comma.** That matches the gloss list and misses `can; ought to be done`.
- **Leave `to ` on verb glosses.** Bosworth-Toller prints the infinitive marker. Modern Old English grammars give the bare infinitive, and the marker repeats on every alternative.
- **Keep a repeated comma-separated item inside a sense.** `time, time, date` and `ward off, guard, ward off` would paste the duplicate.
- **Repair the gloss, or append gender and usage notes, while copying.** Those fields are part of the unclean import. `boslexicon` owns the clean reading.
- **Write the line into the toolkit database.** Dictionary browse copies to the clipboard. The annotation stays a paste.
- **A results-list `y` binding.** The controls are the pinned `Copy` button and the platform copy keys.

## Consequences

- A broken clause that is not the same comma-separated item is copied through until the gloss text is replaced.
- The toolkit glossary splits this field on `;` and `,`. Each sense becomes its own glossary meaning, and so does each comma inside a sense. ` or ` stays inside one meaning.
- While one entry with a definition line is selected, `ctrl+c` / `super+c` copy that line, and Textual's Ctrl-C quit hint does not appear. A mouse selection still wins: Textual's screen binding copies the selection before the app binding runs. With no entry selected, or with an entry that has no gloss, the copy action skips and the quit hint remains. Quit stays Ctrl-Q.
- The clipboard write is Textual's OSC 52 sequence. Apple's Terminal.app ignores that sequence, and many terminals consume Cmd-C before the TUI sees `super+c`. The button uses the same clipboard write.
