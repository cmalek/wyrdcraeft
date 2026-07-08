"""Deterministic sense-tree normalization for Bosworth-Toller sense labels."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

#: Roman numeral with optional lowercase sub-letter suffix.
_ROMAN_SUB_LABEL_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<roman>[IVX]+)(?:[\s.](?P<letter>[a-z])|(?P<glued>[a-z]))\.?$",
)

#: Capital letter followed by a Roman sub-label (``B. I.`` style).
_LETTER_ROMAN_LABEL_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<letter>[A-Z])\.\s*(?P<roman>[IVX]+(?:[\s.][a-z]|[a-z])?)\.?$",
)

#: Top-level Roman numeral label.
_ROMAN_TOP_LABEL_RE: Final[re.Pattern[str]] = re.compile(r"^[IVX]+\.?$")

#: Top-level single capital-letter label.
_LETTER_TOP_LABEL_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z]\.?$")


@dataclass(frozen=True)
class RawSenseFragment:
    """
    One raw sense fragment split from a Bosworth-Toller body field.

    Attributes:
        source_label_raw: Raw sense marker text from the source (for example ``IVa.``).
        source_fragment_raw: Raw HTML/text body for this sense fragment.

    """

    #: Raw Roman-numeral or letter label from the source.
    source_label_raw: str
    #: Raw HTML/text fragment for this sense body.
    source_fragment_raw: str


@dataclass(frozen=True)
class CanonicalSenseFragment:
    """
    One sense fragment with a canonical hierarchical path assignment.

    Attributes:
        source_label_raw: Raw sense marker text preserved from the source.
        source_fragment_raw: Raw HTML/text body for this sense fragment.
        sense_path: Canonical hierarchical path (for example ``2.1``).
        parent_path: Parent sense path when nested; ``None`` for top-level senses.
        warnings: Normalization warnings (for example orphan-label fallback).

    """

    #: Raw Roman-numeral or letter label from the source.
    source_label_raw: str
    #: Raw HTML/text fragment for this sense body.
    source_fragment_raw: str
    #: Canonical hierarchical sense path within one entry block.
    sense_path: str
    #: Parent sense path when nested; ``None`` for top-level senses.
    parent_path: str | None
    #: Normalization warnings emitted while assigning ``sense_path``.
    warnings: tuple[str, ...] = ()


class SenseTreeNormalizer:
    """
    Assign canonical ``sense_path`` values to raw Bosworth-Toller sense fragments.

    Responsibilities are limited to label-depth inference, encounter-order path
    assignment, orphan-label nearest-open-ancestor fallback, and warning metadata.
    Attestation stripping and modifier parsing belong elsewhere.
    """

    def normalize(
        self,
        fragments: list[RawSenseFragment],
    ) -> list[CanonicalSenseFragment]:
        """
        Normalize raw sense fragments into canonical path assignments.

        Args:
            fragments: Ordered raw sense fragments from one entry body.

        Returns:
            Ordered canonical fragments with ``sense_path`` and ``parent_path``.

        """
        if not fragments:
            return []

        results: list[CanonicalSenseFragment] = []
        open_nodes: list[tuple[int, str, str]] = []
        top_level_count = 0
        sibling_counters: dict[str, int] = {}

        for fragment in fragments:
            label = fragment.source_label_raw.rstrip(".")
            depth = self._infer_depth(label)

            if depth == 0:
                top_level_count += 1
                sense_path = str(top_level_count)
                parent_path: str | None = None
                warnings: tuple[str, ...] = ()
                open_nodes = [(0, sense_path, label)]
            else:
                parent_path, warnings = self._resolve_parent(label, open_nodes)
                child_index = self._child_index(label, parent_path, sibling_counters)
                sense_path = f"{parent_path}.{child_index}"
                open_nodes = [
                    node for node in open_nodes if node[0] < depth
                ] + [(depth, sense_path, label)]

            results.append(
                CanonicalSenseFragment(
                    source_label_raw=fragment.source_label_raw,
                    source_fragment_raw=fragment.source_fragment_raw,
                    sense_path=sense_path,
                    parent_path=parent_path,
                    warnings=warnings,
                )
            )

        return results

    def _infer_depth(self, label: str) -> int:
        """
        Infer nesting depth from a normalized source label form.

        Args:
            label: Source label with trailing period removed.

        Returns:
            ``0`` for top-level Roman or letter labels; ``1`` for nested forms.

        """
        if _LETTER_ROMAN_LABEL_RE.match(label):
            return 1
        if _ROMAN_SUB_LABEL_RE.match(label):
            return 1
        if _ROMAN_TOP_LABEL_RE.match(label) or _LETTER_TOP_LABEL_RE.match(label):
            return 0
        return 0

    def _resolve_parent(
        self,
        label: str,
        open_nodes: list[tuple[int, str, str]],
    ) -> tuple[str, tuple[str, ...]]:
        """
        Resolve the parent path for a nested label.

        Args:
            label: Normalized nested source label.
            open_nodes: Open ancestor nodes as ``(depth, path, label)`` tuples.

        Returns:
            Parent path and any fallback warnings.

        """
        expected_parent = self._expected_parent_label(label)
        if expected_parent is not None:
            for depth, path, node_label in reversed(open_nodes):
                if depth == 0 and node_label == expected_parent:
                    return path, ()

        for depth, path, _node_label in reversed(open_nodes):
            if depth == 0:
                if expected_parent is not None:
                    return path, (
                        "orphan label "
                        f"{label!r}: attached to nearest open ancestor {path!r}",
                    )
                return path, ()

        return "1", (f"orphan label {label!r}: attached to default root path '1'",)

    def _expected_parent_label(self, label: str) -> str | None:
        """
        Derive the expected top-level parent label for a nested marker.

        Args:
            label: Normalized nested source label.

        Returns:
            Expected parent label text, or ``None`` when not inferable.

        """
        letter_roman = _LETTER_ROMAN_LABEL_RE.match(label)
        if letter_roman is not None:
            return letter_roman.group("letter")

        roman_sub = _ROMAN_SUB_LABEL_RE.match(label)
        if roman_sub is not None:
            return roman_sub.group("roman")

        return None

    def _child_index(
        self,
        label: str,
        parent_path: str,
        sibling_counters: dict[str, int],
    ) -> int:
        """
        Choose the child index for a nested sense path segment.

        Letter-suffixed labels (``IVa.``, ``II a.``) use the letter position;
        otherwise sibling indices are assigned in encounter order.

        Args:
            label: Normalized nested source label.
            parent_path: Resolved parent sense path.
            sibling_counters: Running next-sibling counters keyed by parent path.

        Returns:
            One-based child index for ``sense_path`` construction.

        """
        letter = self._letter_suffix(label)
        if letter is not None:
            return ord(letter) - ord("a") + 1

        sibling_counters[parent_path] = sibling_counters.get(parent_path, 0) + 1
        return sibling_counters[parent_path]

    def _letter_suffix(self, label: str) -> str | None:
        """
        Extract a lowercase sub-sense letter suffix when present.

        Args:
            label: Normalized source label.

        Returns:
            Lowercase letter suffix, or ``None`` when absent.

        """
        letter_roman = _LETTER_ROMAN_LABEL_RE.match(label)
        if letter_roman is not None:
            roman_part = letter_roman.group("roman")
            roman_sub = _ROMAN_SUB_LABEL_RE.match(roman_part)
            if roman_sub is not None:
                return roman_sub.group("letter") or roman_sub.group("glued")

        roman_sub = _ROMAN_SUB_LABEL_RE.match(label)
        if roman_sub is not None:
            return roman_sub.group("letter") or roman_sub.group("glued")

        return None
