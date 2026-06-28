# Lexicon data lives in morphology.sqlite3

`wyrdcraeft lexicon` will treat `morphology.sqlite3` as the canonical working lexicon database. Bosworth-Toller tables (`bt_*`) should be attached there and curated in-database, morphology rows (`forms`) remain the live generated data, and `lexicon_*` tables are a derived browse/read-model rebuilt from the current contents of that same database. We chose this over a separate `lexicon.sqlite3` because the product is a living scholarly workspace, full morphology rebuilds are expensive, Bosworth-Toller source text is read-only, and one canonical database removes sync drift between browse data and curated working data.

First version scope stays browse-only in the TUI: `wyrdcraeft lexicon build` refreshes only `lexicon_*` tables from existing `forms` and `bt_*` data, and `wyrdcraeft lexicon browse` reads that database. Manual curation must record required provenance, but editing flows can stay in CLI/admin surfaces until browse UX proves out.
