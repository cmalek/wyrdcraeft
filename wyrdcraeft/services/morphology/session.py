import re
from typing import TYPE_CHECKING

from .loaders import load_dictionary, load_forms, load_paradigms, load_prefixes
from .text_utils import OENormalizer

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import ManualForm, VerbParadigm, Word


class GeneratorSession:
    """
    The primary entry point for the morphology generation service.  This is used
    to store the session data for the generator as the generator is run.
    """

    def __init__(self) -> None:
        #: The words: the words to be processed.
        self.words: list[Word] = []
        #: The manual forms
        self.manual_forms: list[ManualForm] = []
        #: The verb paradigms
        self.verb_paradigms: dict[str, VerbParadigm] = {}
        #: The prefixes
        self.prefixes: list[str] = []
        #: The output counter: the number of words output.
        self.output_counter: int = 0
        #: The adjectives: for discovered participles
        self.adjectives: list[Word] = []
        #: The nouns
        self.nouns: list[Word] = []
        #: The verbs
        self.verbs: list[Word] = []
        #: Perl-style shared probability scalar used across generator phases.
        self.perl_probability: int = 0
        #: Whether numeral generation should carry probability across prints.
        #: Enabled by adjective generation in full-flow parity mode.
        self.enable_num_probability_carry: bool = False
        #: Opt-in non-parity extension gate for r-stem noun support.
        #: Default is False to preserve Perl-compatible behavior.
        self.enable_r_stem_nouns: bool = False

    @property
    def prefix_regex(self) -> str:
        """
        Get the prefix regex, used to match the prefixes of the words.

        Prefixes are loaded from the prefixes file

        Returns:
            The prefix regex.

        """
        if not self.prefixes:
            return "0"
        # Perl: foreach (@prefix_input) { $prefix_regex = "$prefix_regex|$_"; }
        return "|".join(self.prefixes)

    def load_all(
        self, dict_path: str, forms_path: str, para_path: str, prefix_path: str
    ) -> None:
        """
        Load all the data from the supporting files into the session.

        - Loads the dictionary
        - Loads the manual forms
        - Loads the paradigms
        - Loads the prefixes
        - Categorizes the words initially into verbs (:attr:`verbs`), adjectives
          (:attr:`adjectives`), and nouns (:attr:`nouns`)

        Args:
            dict_path: The path to the dictionary file.
            forms_path: The path to the forms file.
            para_path: The path to the paradigms file.
            prefix_path: The path to the prefixes file.

        """
        self.words = load_dictionary(dict_path)
        self.manual_forms = load_forms(forms_path)
        self.verb_paradigms = load_paradigms(para_path)
        self.prefixes = load_prefixes(prefix_path)

        # Initial categorization
        self.verbs = [
            w for w in self.words if w.verb == 1 and (w.pspart + w.papart == 0)
        ]
        self.adjectives = [
            w
            for w in self.words
            if w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)
        ]
        self.nouns = [w for w in self.words if w.noun == 1]

    def remove_prefixes(self) -> None:
        """
        Remove the prefixes from the words.
        """
        for word in self.words:
            word.prefix = "0"
            stem = word.stem
            match = re.match(r"^(.*)[\- ](.*)$", stem)
            if match:
                word.prefix = match.group(1)
                word.stem = match.group(2)
            else:
                word.stem = stem

    def remove_hyphens(self) -> None:
        """
        Remove the hyphens from the words.
        """
        for word in self.words:
            word.prefix = word.prefix.replace("-", "")
            word.stem = word.stem.replace("-", "")

    def count_syllables(self) -> None:
        """
        Count the syllables in the words.
        """
        for word in self.words:
            word.syllables = OENormalizer.syllable_count(word.stem)
