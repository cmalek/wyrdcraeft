---
status: accepted
---

# Dictionary browse forms wrap and are never truncated

Today the paradigm table clips long form lists at the right edge and puts the Past column out of sight behind a horizontal scrollbar. A reader who is looking for one variant spelling cannot tell whether it is missing or hidden. This ADR changes how paradigms are painted. The sidebar models in `form_decode` and `paradigm_sidebar` keep their shape (ADR 0014). Layout is ADR 0026.

## Rendering

- Every form for a tense, number, person, case or degree is shown. No cell is cut off, and no `…` or "show all" stands in for omitted forms.
- Paradigms stay in a Textual `DataTable`. The clipping is our own call, not a `DataTable` limit. `add_row` is called with its default `height=1`, which turns wrapping off, and columns size to their longest content. The fix is `height=None` on every row and a fixed width on the forms column, set from the pane width. A cell wraps inside its column and the pane scrolls vertically. There is no horizontal scrollbar. The table cursor stays off (`cursor_type = "none"`).
- All forms use the Old English form colour at regular weight until the model carries a citation marker. A cell's forms are sorted alphabetically, and `forms.probability` is an undocumented generator score (empty on about 30% of rows, tied across variants), so no form can be marked as the citation spelling yet.
- A row with no form is dropped, so a verb's Past table omits Infinitive. A feature column with no value in any row is dropped. A row with no features at all shows its forms as one wrapped list, deduplicated, with no empty column headers.
- A table with no rows, or only empty feature columns and no forms, is not drawn and neither is its section.

## Switching

Only one table of a switch group shows at a time. The footer shows the keys while a switch exists.

| Part of speech | Primary switch (`←` `→`) | Secondary switch (`[` `]`) |
|---|---|---|
| Verb | Present, Past | none |
| Adjective | Strong, Weak | Positive, Comparative, Superlative |
| Noun | none; one table, Singular and Plural columns | none |
| Adverb | none; rows for Positive, Comparative, Superlative | none |
| Pronoun | Singular, Plural (only when the entry has case, gender and number) | none |
| Preposition, conjunction, interjection | no forms | none |

An adjective table keeps columns for Masculine singular, Feminine singular, Neuter singular and Plural. The mockup's Singular/Plural toggle is dropped, because wrapping makes the plural column fit. A pronoun with case, gender and number data gets two tabs, Singular and Plural. Rows are cases (Nom, Acc, Gen, Dat, and Inst when any form has it). The Singular tab has Masc., Fem. and Neut. columns. The Plural tab has one column, since plural forms do not vary by gender. This matches the data the pronoun sidebar already groups by case, gender and number; only the Singular/Plural split is new. Person is not a tab; if the generator later emits it, that is a new decision. `←` and `→` act when the entry pane has focus and are inert in the search input and results list.

## Upstream gap, not fixed here

- Pronoun forms arrive with no case, gender, number or person. The browse table shows those headers over empty cells. Under this ADR such an entry shows a flat wrapped list. Once the generator emits the features, the pronoun tabs below fill in with no further browse change. The generator should emit the features. That is a morphology-generation bug, tracked on its own, and this ADR does not patch it in the TUI.
- Prepositions, conjunctions and interjections are uninflected and have no forms. They show no Forms section, so the empty table in the current screenshots disappears. Case government for a preposition (the dative, accusative or instrumental noted in the senses) would have to be parsed out of the Bosworth-Toller sense text. That is a job for boslexicon, not for this repo's morphology generation or the TUI. Until boslexicon provides it, browse shows no case-government data.

## Considered Options

- **Swap `DataTable` for a Rich `Table` in the scroll column.** Tried first on the false premise that `DataTable` cannot wrap. It can. The swap would cost the existing `DataTable` tests and helpers for no gain.
- **Truncate with `…` and a "show all" key.** Rejected. A hidden form reads as a missing form.
- **Widen the pane or shrink the font.** The longest verb rows are wider than any terminal.
- **Show Present and Past side by side.** Doubles the width of the widest table.
- **A Singular/Plural toggle on adjectives.** One more key for no benefit once the cells wrap. Pronouns keep the split because singular has a gender axis and plural does not.

## Consequences

- Tests that read `DataTable` text (`_table_text`) keep working, with cells wrapped across lines. Expected strings change.
- Row heights now vary, so scroll distances in tests differ.
- The Past tab needs the past-tense rows from the existing sidebar model. The mockup showed only Present.
