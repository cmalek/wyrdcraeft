import re
import unicodedata
from typing import Final


class OENormalizer:
    """
    A utility class for Old English text normalization and linguistic analysis.
    """

    #: The regex for the vowels.
    VOWEL: Final[str] = (
        r"[\u00E6aeiyou\u0153\u00C6AEIYOU\u0152\u01FD\u00E1\u00E9\u00ED\u00FD\u00F3\u00FA\u01FC\u00C1\u00C9\u00CD\u00DD\u00D3\u00DA]"
    )
    #: The regex for the long vowels.
    LVOWEL: Final[str] = (
        r"[\u01FD\u00E1\u00E9\u00ED\u00FD\u00F3\u00FA\u01FC\u00C1\u00C9\u00CD\u00DD\u00D3\u00DA]"
    )
    #: The regex for the diphthongs.
    DIPHTHONG: Final[str] = r"([Ee][AaOo])|([Ii][Ee])"
    #: The regex for the long diphthongs.
    LDIPHTHONG: Final[str] = r"([\u00C9\u00E9][AaOo])|([\u00CD\u00ED][Ee])"
    #: The regex for the consonants.
    CONSONANT: Final[str] = (
        r"[^\u00E6aeiyou\u00C6AEIYOU\u01FD\u00E1\u00E9\u00ED\u00FD\u00F3\u00FA\u01FC\u00C1\u00C9\u00CD\u00DD\u00D3\u00DA]"
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
        Remove diacritics from text, matching ``create_dict31.pl`` ``remove_dia``.

        Note:
            Original Perl code:

            .. code-block:: perl

                $mywords =~ s/\x{01FD}/\x{00E6}/g;
                $mywords =~ s/\x{00E1}/a/g;
                $mywords =~ s/\x{00E9}/e/g;
                $mywords =~ s/\x{00ED}/i/g;
                $mywords =~ s/\x{00FD}/y/g;
                $mywords =~ s/\x{00F3}/o/g;
                $mywords =~ s/\x{00FA}/u/g;

        Args:
            text: The text to process.

        Returns:
            The text with diacritics replaced.

        """  # noqa: E501
        if not text:
            return ""
        replacements = {
            "\u01fd": "æ",  # ǽ -> æ
            "\u00e1": "a",  # á -> a
            "\u00e9": "e",  # é -> e
            "\u00ed": "i",  # í -> i
            "\u00fd": "y",  # ý -> y
            "\u00f3": "o",  # ó -> o
            "\u00fa": "u",  # ú -> u
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @classmethod
    def remove_diacritics(cls, text: str) -> str:
        """
        Remove the diacritics from the text.

        Args:
            text: The text to process.

        Returns:
            The text with diacritics removed.

        """
        if not text:
            return ""
        replacements = {
            "\u01fd": "æ",  # ǽ -> æ
            "\u00e1": "a",  # á -> a
            "\u00e9": "e",  # é -> e
            "\u00ed": "i",  # í -> i
            "\u00fd": "y",  # ý -> y
            "\u00f3": "o",  # ó -> o
            "\u00fa": "u",  # ú -> u
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @classmethod
    def move_accents(cls, text: str) -> str:
        """
        Move the accents from the accents to the vowels.

        Args:
            text: The text to process.

        Returns:
            The text with accents moved to the vowels.

        """
        if not text:
            return ""
        text = text.replace("e\u00f3", "éo")  # eó -> éo
        text = text.replace("e\u00e1", "éa")  # eá -> éa
        return text.replace("i\u00e9", "íe")  # ié -> íe

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
        elif v0 == "á":
            v0 = "ǽ"
        elif v0 == "ó":
            v0 = "é"
        elif v0 == "ú":
            v0 = "ý"
        if v1 == "ea":
            v1 = "ie"
            v2 = "i"
        if v0 == "eo":
            v0 = "ie"
        if v0 == "io":
            v0 = "ie"
            v2 = "i"
        if v0 == "éa":
            v0 = "íe"
            v2 = "í"
        if v0 == "éo":
            v0 = "íe"
        if v0 == "ío":
            v0 = "íe"
            v2 = "í"

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
        Normalize the output text by replacing y/ie with i and removing diacritics.
        Matches Perl's print_one_form normalization exactly.

        Args:
            text: The text to normalize.

        Note:
            Matches Perl's ``print_one_form`` normalization exactly.

            Original Perl code:

            .. code-block:: perl

                $formi =~ s/(y)|(ie?)/i/g;
                $formi =~ s/\x{00FD}|\x{00ED}e/\x{00ED}/g;
                $formi = Unicode::Normalize::NFKD($formi);

        Returns:
            The normalized text.

        """
        if not text:
            return ""
        text = re.sub(r"y|ie?", "i", text)
        text = re.sub(r"\u00FD|\u00EDe", "\u00ed", text)
        text = unicodedata.normalize("NFKD", text)
        return "".join(c for c in text if not unicodedata.combining(c))
