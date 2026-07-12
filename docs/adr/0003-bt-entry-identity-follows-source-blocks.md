# BT entry identity follows source blocks

Bosworth-Toller entry identity is the source headword block, not the tuple `(norm_key, pos)`. We chose this because same-spelling same-POS homographs such as `mǣgþ` must survive as separate `bt_entries` rows, and editorial `Add` / `Substitute` / `Dele` lines must target one specific source block or remain unapplied with a warning instead of being guessed across ambiguous homographs.
