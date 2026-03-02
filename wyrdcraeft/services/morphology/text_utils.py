import re
import unicodedata
from typing import Final


class OENormalizer:
    """
    A robust utility class for Old English text normalization and linguistic
    analysis.  This is used in the generation of Old English morphology forms.

    :func:`~wyrdcraeft.services.syllable.normalize_old_english` is useful for
    normalizing Old English text for stable matching, for instance when doing
    searches for matching Old English text.

    This class is far more robust than that and can be used for linguistic
    analysis of Old English text.

    - Provides robust normalization functions for output text
    - Normalizes Old English text to a canonical form
    - Provides linguistic analysis tools for Old English text
    - Includes robust regex patterns for vowels, diphthongs, and consonants
    - Handles diacritic restoration and accent movement in Bosworth-Toller Old
      English Dictionary data
    - Supports syllable counting and stem length determination

    """

    #: The regex for the vowels (includes macron long vowels: ā ē ī ō ū ȳ ǣ).
    VOWEL: Final[str] = (
        r"[\u00E6aeiyou\u0153\u00C6AEIYOU\u0152\u01E3\u0101\u0113\u012B\u0233\u014D\u016B\u01E2\u0100\u0112\u012A\u0232\u014C\u016A]"
    )
    #: The regex for the long vowels (macrons).
    LVOWEL: Final[str] = (
        r"[\u01E3\u0101\u0113\u012B\u0233\u014D\u016B\u01E2\u0100\u0112\u012A\u0232\u014C\u016A]"
    )
    #: The regex for the diphthongs.
    DIPHTHONG: Final[str] = r"([Ee][AaOo])|([Ii][Ee])"
    #: The regex for the long diphthongs (macrons: ēa ēo īe).
    LDIPHTHONG: Final[str] = r"([\u0112\u0113][AaOo])|([\u012A\u012B][Ee])"
    #: The regex for the consonants.
    CONSONANT: Final[str] = (
        r"[^\u00E6aeiyou\u00C6AEIYOU\u01E3\u0101\u0113\u012B\u0233\u014D\u016B\u01E2\u0100\u0112\u012A\u0232\u014C\u016A]"
    )

    #: The compiled regex for the vowels.
    VOWEL_REGEX: Final[re.Pattern[str]] = re.compile(VOWEL)
    #: The compiled regex for the long vowels.
    LVOWEL_REGEX: Final[re.Pattern[str]] = re.compile(LVOWEL)
    #: The compiled regex for the diphthongs.
    DIPHTHONG_REGEX: Final[re.Pattern[str]] = re.compile(DIPHTHONG)
    #: The compiled regex for the long diphthongs.
    LDIPHTHONG_REGEX: Final[re.Pattern[str]] = re.compile(LDIPHTHONG)
    #: The compiled regex for the consonants.
    CONSONANT_REGEX: Final[re.Pattern[str]] = re.compile(CONSONANT)

    @classmethod
    def eth2thorn(cls, text: str) -> str:
        """
        Replace the eth character with the thorn character.

        Args:
            text: The text to process.

        Returns:
            The text with eth replaced by thorn.

        """
        if not text:
            return ""
        text = text.replace("\u00f0", "þ")  # ð -> þ
        text = text.replace("\u00d0", "Þ")  # Ð -> Þ
        return re.sub("k", "c", text, flags=re.IGNORECASE)

    @classmethod
    def remove_dia_perl(cls, text: str) -> str:
        r"""
        Remove macrons (long-vowel diacritics) from text.

        Strips macron to base vowel (e.g. ā→a, ǣ→æ). Matches Perl ``remove_dia``
        semantics but for macron input.

        Args:
            text: The text to process.

        Returns:
            The text with macrons replaced by base vowels.

        """
        if not text:
            return ""
        replacements = {
            "\u01e3": "æ",  # ǣ -> æ
            "\u01e2": "Æ",  # Ǣ -> Æ
            "\u0101": "a",  # ā -> a
            "\u0100": "A",  # Ā -> A
            "\u0113": "e",  # ē -> e
            "\u0112": "E",  # Ē -> E
            "\u012b": "i",  # ī -> i
            "\u012a": "I",  # Ī -> I
            "\u0233": "y",  # ȳ -> y
            "\u0232": "Y",  # Ȳ -> Y
            "\u014d": "o",  # ō -> o
            "\u014c": "O",  # Ō -> O
            "\u016b": "u",  # ū -> u
            "\u016a": "U",  # Ū -> U
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @classmethod
    def remove_diacritics(cls, text: str) -> str:
        """
        Remove macrons (long-vowel diacritics) from the text.

        Args:
            text: The text to process.

        Returns:
            The text with macrons replaced by base vowels.

        """
        if not text:
            return ""
        replacements = {
            "\u01e3": "æ",  # ǣ -> æ
            "\u01e2": "Æ",  # Ǣ -> Æ
            "\u0101": "a",  # ā -> a
            "\u0100": "A",  # Ā -> A
            "\u0113": "e",  # ē -> e
            "\u0112": "E",  # Ē -> E
            "\u012b": "i",  # ī -> i
            "\u012a": "I",  # Ī -> I
            "\u0233": "y",  # ȳ -> y
            "\u0232": "Y",  # Ȳ -> Y
            "\u014d": "o",  # ō -> o
            "\u014c": "O",  # Ō -> O
            "\u016b": "u",  # ū -> u
            "\u016a": "U",  # Ū -> U
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @classmethod
    def move_accents(cls, text: str) -> str:
        """
        Convert raw BT-style acute diphthongs to macron diphthongs.

        Bosworth-Toller data may have the long-vowel mark on the wrong vowel
        (e.g. eó, eá, ié). This function accepts that acute input and outputs
        macron diphthongs (ēo, ēa, īe) so the rest of the pipeline is macron-only.
        We're doing it this way so we don't have to modify the BT source data.

        Args:
            text: The text to process (may contain acute diphthongs).

        Returns:
            The text with acute diphthongs replaced by macron diphthongs.

        """
        if not text:
            return ""
        # Acute input -> macron output (ē U+0113, ī U+012B)
        text = text.replace("e\u00f3", "\u0113o")  # eó -> ēo
        text = text.replace("e\u00e1", "\u0113a")  # eá -> ēa
        return text.replace("i\u00e9", "\u012be")  # ié -> īe

    @classmethod
    def iumlaut(cls, vowels: list[str]) -> list[str]:  # noqa: PLR0912
        r"""
        Perform i-mutation (umlaut) on the vowels.

        Args:
            vowels: A list of vowels to process.

        Note:
            This is a simplification, but often used in stem comparison.

            Original Perl code:

            .. code-block:: perl

                my @myvowels = @_;
                $myvowels[1] = $myvowels[0];
                $myvowels[0] =~ s/^e$/i/;
                $myvowels[0] =~ s/^o$/e/;
                $myvowels[0] =~ s/^u$/y/;
                $myvowels[0] =~ s/^\x{00E6}$/e/;
                if ($myvowels[0] =~ s/^a$/\x{00E6}/) { $myvowels[2] = "e"; }
                $myvowels[0] =~ s/^\x{00E1}$/\x{001FD}/;
                $myvowels[0] =~ s/^\x{00F3}$/\x{00E9}/;
                $myvowels[0] =~ s/^\x{00FA}$/\x{00FD}/;
                if ($myvowels[1] =~ s/^ea$/ie/) { $myvowels[2] = "i"; }
                $myvowels[0] =~ s/^eo$/ie/;
                if ($myvowels[0] =~ s/^io$/ie/) { $myvowels[2] = "i"; }
                if ($myvowels[0] =~ s/^\x{00E9}a$/\x{00ED}e/) { $myvowels[2] = "\x{00ED}"; }
                $myvowels[0] =~ s/^\x{00E9}o$/\x{00ED}e/;
                if ($myvowels[0] =~ s/^[\x{00ED}]o$/\x{00ED}e/) { $myvowels[2] = "\x{00ED}"; }
                return @myvowels;

        Returns:
            A list of vowels: [mutated, unmutated, (optional third)]

        """  # noqa: E501
        v0 = vowels[0]
        v1 = v0
        v2 = None

        if v0 == "e":
            v0 = "i"
        elif v0 == "o":
            v0 = "e"
        elif v0 == "u":
            v0 = "y"
        elif v0 == "æ":
            v0 = "e"
        elif v0 == "a":
            v0 = "æ"
            v2 = "e"
        elif v0 == "ā":
            v0 = "ǣ"
        elif v0 == "ō":
            v0 = "ē"
        elif v0 == "ū":
            v0 = "ȳ"
        if v1 == "ea":
            v1 = "ie"
            v2 = "i"
        if v0 == "eo":
            v0 = "ie"
        if v0 == "io":
            v0 = "ie"
            v2 = "i"
        if v0 == "ēa":
            v0 = "īe"
            v2 = "ī"
        if v0 == "ēo":
            v0 = "īe"
        if v0 == "īo":
            v0 = "īe"
            v2 = "ī"

        res = [v0, v1]
        if v2 is not None:
            res.append(v2)
        return res

    @classmethod
    def stem_length(cls, stem: str) -> int:
        """
        Get the length of the stem to determine if it is a long stem word.

        Args:
            stem: The stem to evaluate.

        Returns:
            1 if it is a long stem, 0 otherwise.

        """
        pattern = f"^.*?({cls.VOWEL}{cls.VOWEL}?)({cls.CONSONANT}*)(.*)"
        match = re.search(pattern, stem)
        if not match:
            return 0

        vowel_part = match.group(1)
        consonants_part = match.group(2) or ""
        rest = match.group(3) or ""

        mod_consonants = consonants_part.replace("sc", "s").replace("cg", "c")

        length = 0
        # long stem vowel = long stem
        if cls.LVOWEL_REGEX.search(vowel_part):
            length = 1
        # two or more consonants = stem ends in a consonant = long stem
        if len(mod_consonants) > 1:
            length = 1
        # monosyllabic stem ending in a consonant = long stem
        if rest == "" and len(mod_consonants) > 0:
            length = 1

        return length

    @classmethod
    def syllable_count(cls, text: str) -> int:
        """
        Count the syllables in the text.

        Note:
            Matches Perl's syllab exactly: (V+C count) + (final vowel count).

            Original Perl code:

            .. code-block:: perl

                $counter = ($word =~ s/($vowel_regex$consonant_regex)/$1/g);
                $counter += ($word =~ s/($vowel_regex)$/$1/g);

        Args:
            text: The text to evaluate.

        Returns:
            The number of syllables.

        """
        if not text:
            return 0
        vc_count = len(re.findall(f"{cls.VOWEL}{cls.CONSONANT}", text))
        final_vowel_count = len(re.findall(f"{cls.VOWEL}$", text))
        return vc_count + final_vowel_count

    @classmethod
    def normalize_output(cls, text: str) -> str:
        r"""
        Normalize the output text by replacing y/ie with i and stripping macrons.

        Replaces ȳ and īe with ī, then NFKD normalizes and removes combining
        marks (so long vowels become base vowels).

        Args:
            text: The text to normalize.

        Returns:
            The normalized text (macrons stripped to base vowels).

        """
        if not text:
            return ""
        text = re.sub(r"y|ie?", "i", text)
        text = re.sub(r"\u0233|\u012Be", "\u012b", text)  # ȳ|īe -> ī
        text = unicodedata.normalize("NFKD", text)
        return "".join(c for c in text if not unicodedata.combining(c))
