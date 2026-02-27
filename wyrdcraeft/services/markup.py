from typing import Final


class GPalatalizer:
    """
    Palatalize g in the given text.
    """

    #: Words that seem like they should have a palatalized g, but don't
    #: mainly for historical linguistics reasons.
    #:
    #: Note that we will have to deal with these exceptions in compound
    #: words also, by splitting on - and seeing if the first part is in the
    #: list.
    FRONTAL_G_EXCEPTIONS: Final[list[str]] = [
        "gǣl",
        "gǣf",
        "gǣfon",
        "gǣlscipe",
        "gǣng",
        "gǣnge",
        "gǣr",
        "gǣrlicgǣst",
        "gǣstas",
        "gǣsthus",
        "gǣstlic",
        "gǣstlīce",
        "gǣt",
        "gǣten",
        "gaf",
        "gafol",
        "gafolrǣden",
        "gafolgyld",
        "galan",
        "gangan",
        "gār",
        "gāt",
        "gēar",
        "gēara",
        "gēoguð",
        "geōguþ",
        "gēn",
        "gēna",
        "gēola",
        "gēol",
        "gēomor",
        "gēong",
        "gēongra",
        "gēs",
        "gēsne",
        "gēsnian",
        "gēsting",
        "gēstlīc",
        "gēsthus",
        "gēat",
        "gēatlic",
        "gēard",
        "Gēatas",
        "Gēatland",
    ]

    #: Ending palatalized g exceptions, where the g seems like
    #: it should be palatalized, but is not.
    ENDING_G_EXCEPTIONS: Final[list[str]] = ["plǣg", "sweg", "tǣghrēg"]

    #: Front vowels
    FRONT_VOWELS: Final[list[str]] = [
        "ī",
        "i",
        "ē",
        "e",
        "ǣ",
        "æ",
        "ȳ",
        "y",
        "ēa",
        "ea",
        "īo",
        "io",
        "ēo",
        "eo",
        "īe",
        "ie",
    ]

    MIN_INTERNAL_G_LENGTH: Final[int] = 3

    def palatalize(self, word: str) -> str:
        """
        Palatalize g in the given text.

        First, a front vowel is identified as any of the following (because the
        vowels are made at the **front** of the mouth):

        - ī, i, ē, e, ǣ, æ, y, ȳ
        - ēa, ea, īo, io, ēo, eo, īe, ie

        A back vowel is identified as any of the following (because the vowels are
        made at the **back** of the mouth):

        - ū, u, ō, o, ā, a

        Rules for palatalizing "g" to "ġ":

        - If a "g" appears before a front vowel or a dipthong (when the first
        element is a front vowel), as in ġeond, ġepinnan, ġiefu, it becomes "ġ"
        - If a "g" appears as the final sound after a front vowel, as in weġ, wīġ,
        and dæġ
        - If it is the final vowel of a syllable after a front vowel, as in bræġden,
        hræġl-weard
        - If it is between front vowels as in hīġan, dæġes, stiġel

        There are exceptions to these rules; see :attr:`FRONTAL_G_EXCEPTIONS` and
        :attr:`ENDING_G_EXCEPTIONS`.

        Args:
            word: The word to palatalize.

        Returns:
            The palatalized text.

        """
        # Deal with compound words
        if "-" in word:
            parts = word.split("-")
            for part in parts:
                word = self.palatalize(part)
            return "-".join(parts)

        # Deal with the frontal g
        if (
            word.startswith("g")
            and word[1] in self.FRONT_VOWELS
            and word not in self.FRONTAL_G_EXCEPTIONS
        ):
            word = "ġ" + word[1:]

        # Deal with the ending g
        if (
            word.endswith("g")
            and word[-2] in self.FRONT_VOWELS
            and word not in self.ENDING_G_EXCEPTIONS
        ):
            return word[:-1] + "ġ"

        # Deal with g surrounded by front vowels
        if len(word) >= self.MIN_INTERNAL_G_LENGTH:
            g_positions = [i for i, c in enumerate(word) if c == "g"]
            for g_position in g_positions:
                if g_position == 0:
                    continue
                if g_position == len(word) - 1:
                    continue
                if (
                    word[g_position - 1] in self.FRONT_VOWELS
                    and word[g_position + 1] in self.FRONT_VOWELS
                ):
                    word = word[:g_position] + "ġ" + word[g_position + 1 :]

        # Now the hard part -- g that ends a syllable following
        # a front vowel.
        if "g" in word and word[word.index("g") - 1] in self.FRONT_VOWELS:
            return word[: word.index("g")] + "ġ" + word[word.index("g") + 1 :]

        return word
