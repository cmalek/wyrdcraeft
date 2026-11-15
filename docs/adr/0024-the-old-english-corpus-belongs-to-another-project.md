---
status: accepted
---

# The Old English corpus belongs to another project

`wyrdcraeft` prepares a text already in hand for translation. It does not acquire the extant Old English corpus or manage the corpus vault. ADR 0022's corpus design moves with that separate project. An acquired text enters `wyrdcraeft` as an ordinary local TEI/XML or `.txt` source file.

## Consequences

ADR 0022 is superseded for this repository. The catalogue seed and the acquisition skill currently in this tree move to the corpus project. `wyrdcraeft` gains no corpus writer, catalogue database, or vault client.
