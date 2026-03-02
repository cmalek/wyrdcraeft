"""Syllable model for Old English syllable breaking."""

from dataclasses import dataclass


@dataclass
class Syllable:
    """
    A syllable is a unit of speech that consists of an onset, nucleus, and coda.
    """

    #: The onset is the consonant cluster before the nucleus.
    onset: str
    #: The nucleus is the vowel sound.
    nucleus: str
    #: The coda is the consonant cluster after the nucleus.
    coda: str

    def __str__(self) -> str:
        return f"{self.onset}{self.nucleus}{self.coda}"
