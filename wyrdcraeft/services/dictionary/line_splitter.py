"""Bosworth-Toller ``@``-field line splitting utilities."""

from __future__ import annotations

from dataclasses import dataclass

from ..markup import BT_SPLIT_PART_COUNT


@dataclass(frozen=True)
class BTSplitLine:
    """
    One Bosworth-Toller source line split into its three ``@`` fields.

    Attributes:
        lookup_field: Raw left field used for lookup aliases.
        body: Main dictionary payload field containing BT HTML.
        slug_field: Right field used by the BT export as normalized slug text.
        lookup_keys: Parsed lookup aliases from ``lookup_field``.

    """

    #: Raw lookup alias field before parsing commas.
    lookup_field: str
    #: Main line body between first and second ``@`` separators.
    body: str
    #: Final source field (typically normalized slug(s)).
    slug_field: str
    #: Parsed lookup keys in source order.
    lookup_keys: tuple[str, ...]


class BTLineSplitter:
    """
    Split Bosworth-Toller source lines into canonical ``@`` fields.
    """

    def split(self, line: str) -> BTSplitLine | None:
        """
        Split one source line into three fields and parse lookup keys.

        Args:
            line: Raw line from ``oe_bt.txt``.

        Returns:
            Parsed split result, or ``None`` when field count is invalid.

        """
        parts = line.split("@", maxsplit=2)
        if len(parts) != BT_SPLIT_PART_COUNT:
            return None
        lookup_field, body, slug_field = parts
        lookup_keys = tuple(
            key.strip() for key in lookup_field.split(",") if key.strip()
        )
        return BTSplitLine(
            lookup_field=lookup_field,
            body=body,
            slug_field=slug_field,
            lookup_keys=lookup_keys,
        )
