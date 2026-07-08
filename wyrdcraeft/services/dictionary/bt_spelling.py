"""Bosworth-Toller display spelling normalization for dictionary parsing."""

from __future__ import annotations

from ..morphology.text_utils import OENormalizer


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
        return OENormalizer.normalize_bt_display_spelling(spelling)
