from __future__ import annotations

import re
import unicodedata
from typing import Final

from ..models import (
    Example,
    ExpressionComponent,
    ExpressionType,
    LexicalExpression,
    Sense,
)


class BosworthTollerParser:
    """
    Stateful, testable parser for a *single* Bosworth-Toller CSV line.
    """

    #: Regular expressions for extracting the display form and examples
    BOLD_RE: Final[re.Pattern[str]] = re.compile(r"<B>(.*?)</B>", re.DOTALL)
    #: Regular expressions for extracting the italic text
    ITALIC_RE: Final[re.Pattern[str]] = re.compile(r"<I>(.*?)</I>", re.DOTALL)
    #: Regular expressions for extracting the tag text
    TAG_RE = re.compile(r"</?[^>]+>")
    #: Regular expressions for splitting the senses
    SENSE_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"<B>([IVX]+)</B>\.")

    #: Canonical characters for Old English text
    #: (ð -> þ, ƿ -> w, Ƿ -> W)
    CANONICAL_CHARS: Final[dict[str, str]] = {
        "ð": "þ",
        "Ð": "Þ",
        "ƿ": "w",
        "Ƿ": "W",
    }
    #: Allowed characters for Old English text
    #: (æ, þ)
    ALLOWED_CHARS: Final[str] = "æþ"

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def parse(self, csv_line: str) -> LexicalExpression:
        """
        Main entry point.  Takes a *single* Bosworth-Toller CSV line
        (definitions column) and returns a fully-populated LexicalExpression
        with all fields populated.

        Args:
            csv_line: A single Bosworth-Toller CSV line (definitions column)

        Returns:
            A fully-populated LexicalExpression

        Raises:
            ValueError: If no <B>...</B> display form is found

        """
        display = self._extract_display_form(csv_line)
        if not display:
            msg = "No <B>...</B> display form found"
            raise ValueError(msg)

        normalized = self._normalize(display)
        expr_type = ExpressionType.IDIOM if " " in normalized else ExpressionType.WORD

        expr = LexicalExpression(
            display_form=display,
            normalized=normalized,
            expression_type=expr_type,
        )

        # deletion stub
        if self._is_deletion(csv_line):
            return expr

        # idiom components
        if expr.expression_type == ExpressionType.IDIOM:
            expr.components = self._build_components(display)

        # senses
        expr.senses = self._parse_senses(csv_line)

        return expr

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _normalize(self, text: str) -> str:
        """
        Normalizes Old English text to a strict, normalized form.

        - Removes diacritics
        - Replaces special characters with their canonical forms (ð -> þ, ƿ ->
          w, Ƿ -> w)
        - Removes non-word characters other than hyphens and spaces
        - Normalizes whitespace (collapses multiple spaces into one)

        """
        if not text:
            return ""

        text = text.strip().lower()
        text = unicodedata.normalize("nfd", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))

        for src, tgt in self.CANONICAL_CHARS.items():
            text = text.replace(src.lower(), tgt)

        text = re.sub(rf"[^\w\s{self.ALLOWED_CHARS}]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def _extract_display_form(self, text: str) -> str | None:
        """
        Extracts the display form from the text.  This is the true
        surface form of the lexical expression.

        Args:
            text: The text to extract the display form from.

        Returns:
            The display form, or None if not found.

        """
        m = self.BOLD_RE.search(text)
        return m.group(1).strip() if m else None

    def _strip_markup(self, text: str) -> str:
        """
        Strips markup from the text.

        Args:
            text: The text to strip markup from.

        Returns:
            The text with markup stripped.

        """
        return self.TAG_RE.sub("", text).strip()

    def _is_deletion(self, text: str) -> bool:
        """
        Checks if the text is a deletion.

        Args:
            text: The text to check if it is a deletion.

        Returns:
            True if the text is a deletion, False otherwise.

        """
        cleaned = self._strip_markup(text).lower()
        return cleaned in {"dele", "delete", "dele."}

    def _split_senses(self, text: str) -> list[str]:
        """
        Splits the text into senses.

        Args:
            text: The text to split into senses.

        Returns:
            A list of sense blocks.

        """
        parts = self.SENSE_SPLIT_RE.split(text)
        if len(parts) == 1:
            return [text]
        return [parts[i + 1] for i in range(1, len(parts), 2)]

    def _parse_senses(self, text: str) -> list[Sense]:
        """
        Parses the senses from the text.

        Args:
            text: The text to parse the senses from.

        Returns:
            A list of senses.

        """
        sense_blocks = self._split_senses(text)
        senses: list[Sense] = []

        for idx, block in enumerate(sense_blocks, start=1):
            definition = self._extract_definition(block)
            examples = self._extract_examples(block)

            senses.append(
                Sense(
                    sense_order=idx,
                    definition=definition,
                    examples=examples,
                )
            )

        return senses

    def _extract_definition(self, block: str) -> str:
        """
        Extracts the definition from the sense block.

        Note:
            Definition is everything before the first example marker.

        Args:
            block: The sense block to extract the definition from.

        Returns:
            The definition.

        """
        if ":--" in block:
            block = block.split(":--", 1)[0]
        return self._strip_markup(block)

    def _extract_examples(self, block: str) -> list[Example]:
        """
        Extracts the examples from the sense block.

        Args:
            block: The sense block to extract the examples from.

        Returns:
            A list of examples.

        """
        examples: list[Example] = []

        if ":--" not in block:
            return examples

        _, example_block = block.split(":--", 1)
        chunks = example_block.split(". ")

        for ch in chunks:
            m = self.ITALIC_RE.search(ch)
            if not m:
                continue

            oe = self._strip_markup(ch[: m.start()])
            me = m.group(1).strip()
            src = self._strip_markup(ch[m.end() :])

            examples.append(
                Example(
                    old_english=oe,
                    modern_english=me,
                    source=src or None,
                )
            )

        return examples

    def _build_components(self, display: str) -> list[ExpressionComponent]:
        """
        Builds the components of the lexical expression.

        - Splits the display form into tokens
        - Creates an ExpressionComponent for each token
        - Returns the list of components

        Args:
            display: The display form of the lexical expression.

        Returns:
            A list of components.

        """
        tokens = display.split()
        components: list[ExpressionComponent] = []

        for i, tok in enumerate(tokens, start=1):
            components.append(
                ExpressionComponent(
                    position=i,
                    surface_form=tok,
                )
            )

        return components
