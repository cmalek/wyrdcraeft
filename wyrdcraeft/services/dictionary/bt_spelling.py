"""Bosworth-Toller display spelling normalization for dictionary parsing."""

from __future__ import annotations

import re
import unicodedata
from typing import Final

from ..bosworthtoller import normalize_bt_spelling
from ..morphology.text_utils import OENormalizer

#: Regex for BT ``eō``/``eó``-style long-mark-on-second-vowel diphthongs.
_EO_WRONG_LONG_RE: Final[re.Pattern[str]] = re.compile(r"([eE])([ōóŌÓ])")
#: Regex for BT ``eā``/``eá``-style long-mark-on-second-vowel diphthongs.
_EA_WRONG_LONG_RE: Final[re.Pattern[str]] = re.compile(r"([eE])([āáĀÁ])")
#: Regex for BT ``iē``/``ié``-style long-mark-on-second-vowel diphthongs.
_IE_WRONG_LONG_RE: Final[re.Pattern[str]] = re.compile(r"([iI])([ēéĒÉ])")


class BTSpellingNormalizer:
    """
    Normalize Bosworth-Toller spellings to Wright-style macron display forms.

    The normalizer is intentionally display-only for dictionary headwords and
    variant forms. It does not change lookup-key generation (`norm_key`).

    Note:
        Linguistic scope is cross-PoS (verb, noun, adjective, adverb, numeral,
        and indeclinable entries) because BT diphthong long-mark placement is a
        spelling convention issue independent of inflectional category.
        We keep the first-vowel long-mark convention used by project morphology
        output (for example ``beōdan`` -> ``bēodan``), aligned with the grammar
        references in `data/OldEnglishGrammar.pdf` and
        `data/Ondej_Tich_40-54-1.pdf`.

    """

    def normalize(self, spelling: str) -> str:
        """
        Convert one BT spelling to macronized Wright-style display spelling.

        Pipeline order is fixed and idempotent:
        1) NFC normalize
        2) Move acute diphthong accent marks (``eó`` -> ``ēo``)
        3) Convert remaining acute vowels to macrons
        4) Swap wrong-vowel long-mark diphthongs (``eō`` -> ``ēo``)

        Args:
            spelling: Raw BT spelling string.

        Returns:
            Normalized display spelling.

        """
        normalized = unicodedata.normalize("NFC", spelling)
        moved = OENormalizer.move_accents(normalized)
        macronized = normalize_bt_spelling(moved)
        return self._swap_bt_diphthong_long_marks(macronized)

    def _swap_bt_diphthong_long_marks(self, spelling: str) -> str:
        """
        Rewrite BT second-vowel long-mark diphthongs to first-vowel long marks.

        Args:
            spelling: NFC-normalized string with acute/macron vowels.

        Returns:
            Display spelling with Wright-style diphthong long-mark placement.

        """
        swapped = _EO_WRONG_LONG_RE.sub(self._eo_replacement, spelling)
        swapped = _EA_WRONG_LONG_RE.sub(self._ea_replacement, swapped)
        return _IE_WRONG_LONG_RE.sub(self._ie_replacement, swapped)

    def _eo_replacement(self, match: re.Match[str]) -> str:
        """
        Build replacement text for ``eo`` diphthong long-mark correction.

        Args:
            match: Regex match for ``e`` + long-marked ``o``.

        Returns:
            Corrected ``ēo`` sequence with case preserved.

        """
        return self._replace_with_first_long(
            first=match.group(1),
            second=match.group(2),
            corrected_pair="ēo",
        )

    def _ea_replacement(self, match: re.Match[str]) -> str:
        """
        Build replacement text for ``ea`` diphthong long-mark correction.

        Args:
            match: Regex match for ``e`` + long-marked ``a``.

        Returns:
            Corrected ``ēa`` sequence with case preserved.

        """
        return self._replace_with_first_long(
            first=match.group(1),
            second=match.group(2),
            corrected_pair="ēa",
        )

    def _ie_replacement(self, match: re.Match[str]) -> str:
        """
        Build replacement text for ``ie`` diphthong long-mark correction.

        Args:
            match: Regex match for ``i`` + long-marked ``e``.

        Returns:
            Corrected ``īe`` sequence with case preserved.

        """
        return self._replace_with_first_long(
            first=match.group(1),
            second=match.group(2),
            corrected_pair="īe",
        )

    def _replace_with_first_long(
        self,
        *,
        first: str,
        second: str,
        corrected_pair: str,
    ) -> str:
        """
        Compose one corrected diphthong while preserving source case pattern.

        Keyword Args:
            first: First letter from matched diphthong.
            second: Second letter from matched diphthong.
            corrected_pair: Lowercase corrected diphthong (for example ``ēo``).

        Returns:
            Corrected two-character diphthong string.

        """
        first_replacement = (
            corrected_pair[0].upper() if first.isupper() else corrected_pair[0]
        )
        second_replacement = (
            corrected_pair[1].upper() if second.isupper() else corrected_pair[1]
        )
        return f"{first_replacement}{second_replacement}"
