from typing import Final

from ..models.syllable import Syllable


class OESyllableBreaker:
    """
    Break an Old English word into syllables.
    """

    # Longest-first diphthongs
    DIPHTHONGS: Final[list[str]] = [
        "ēa",
        "ēo",
        "īo",
        "ea",
        "eo",
        "io",
    ]

    VOWELS: Final[set[str]] = set("aāæǣeēiīoōuūyȳ")

    # OE onset clusters we are willing to treat as legal
    LEGAL_ONSETS: Final[set[str]] = {
        "pl",
        "pr",
        "bl",
        "br",
        "tr",
        "dr",
        "cl",
        "cr",
        "gl",
        "gr",
        "fl",
        "fr",
        "sl",
        "sm",
        "sn",
        "sp",
        "st",
        "sw",
        "sc",
        "þr",
        "hw",
        "hl",
        "hn",
        "hr",
        "wr",
    }

    # Absolute internal palatalization blocker
    BLOCKING_CLUSTERS: Final[set[str]] = {"ng"}

    # Optional: suffixes where a syllable boundary should be forced
    KNOWN_SUFFIXES: Final[list[str]] = [
        "lic",
        "līc",
        "licc",
        "līcc",
        "nes",
        "nis",
        "nys",
        "nesse",
        "nissedom",
        "dōm",
        "ung",
        "ing",
        "ere",
        "en",
        "an",
        "full",
        "leas",
        "lēas"
    ]

    def is_vowel(self, char: str) -> bool:
        return char in self.VOWELS

    def find_vowel_nuclei(self, word: str):
        """Return list of (start, end, nucleus) for vowel nuclei."""
        nuclei = []
        i = 0
        while i < len(word):
            # Try diphthongs first
            matched = False
            for d in self.DIPHTHONGS:
                if word.startswith(d, i):
                    nuclei.append((i, i + len(d), d))
                    i += len(d)
                    matched = True
                    break
            if matched:
                continue

            if self.is_vowel(word[i]):
                nuclei.append((i, i + 1, word[i]))
            i += 1
        return nuclei

    def split_consonants(self, cluster: str):
        """
        Split consonant cluster between syllables using a conservative
        max-onset principle.
        """
        if not cluster:
            return "", ""

        # Absolute blockers
        for blk in self.BLOCKING_CLUSTERS:
            if blk in cluster:
                return cluster, ""

        # Try to maximize legal onset
        for i in range(len(cluster)):
            onset_candidate = cluster[i:]
            if onset_candidate in self.LEGAL_ONSETS:
                return cluster[:i], onset_candidate

        # Default: single consonant to next syllable
        if len(cluster) == 1:
            return "", cluster

        # Otherwise split conservatively
        return cluster[:-1], cluster[-1]

    def force_suffix_boundaries(self, word: str):
        """Insert dots before known suffixes to guide syllabification."""
        for suffix in self.KNOWN_SUFFIXES:
            if word.endswith(suffix):
                return word[: -len(suffix)] + "." + word[-len(suffix) :]
        return word

    def split(self, word: str) -> list[Syllable]:
        """
        Syllabify an Old English word conservatively.
        """
        # Optional morphological hinting
        word = self.force_suffix_boundaries(word)

        # Split on forced boundaries
        parts = word.split(".")

        syllables: list[Syllable] = []

        for part in parts:
            nuclei = self.find_vowel_nuclei(part)
            if not nuclei:
                continue

            for idx, (start, end, nucleus) in enumerate(nuclei):
                prev_end = nuclei[idx - 1][1] if idx > 0 else 0
                next_start = nuclei[idx + 1][0] if idx + 1 < len(nuclei) else len(part)

                inter_consonants = part[end:next_start]

                coda, onset_next = self.split_consonants(inter_consonants)

                onset = part[prev_end:start]
                syllables.append(Syllable(onset=onset, nucleus=nucleus, coda=coda))

                # carry onset_next to next syllable
                if idx + 1 < len(nuclei):
                    nuclei[idx + 1] = (
                        nuclei[idx + 1][0] - len(onset_next),
                        nuclei[idx + 1][1],
                        nuclei[idx + 1][2],
                    )

        return syllables
