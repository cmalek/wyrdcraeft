"""Bosworth-Toller search result model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BTSearchEntry:
    """
    One parsed Bosworth-Toller search result entry.

    Attributes:
        headword_raw: Original BT spelling as shown in the search result.
        headword_macronized: Display spelling with acutes converted to macrons.
        pos: Word class label if present.
        meanings: Parsed meaning snippets from the first description line.
        entry_url: Absolute URL to the BT entry.
        order_index: Zero-based order in the search result list.

    """

    #: Original BT spelling as shown in search.
    headword_raw: str
    #: BT spelling normalized for display with macrons.
    headword_macronized: str
    #: Word class label, if present.
    pos: str
    #: Meaning snippets extracted from summary line.
    meanings: list[str]
    #: Absolute URL to entry.
    entry_url: str
    #: Position in result order.
    order_index: int
