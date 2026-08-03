import re
from typing import TYPE_CHECKING

from .loaders import load_dictionary, load_forms, load_paradigms, load_prefixes
from .text_utils import OENormalizer

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import ManualForm, VerbParadigm, Word


class WordPool:
    """
    Categorized word lists and supporting dictionaries for one morphology
    generation run.
    """

    def __init__(self) -> None:
        """Initialize an empty word pool with no words or categorized lists."""
        #: The words: the words to be processed.
        self.words: list[Word] = []
        #: The manual forms
        self.manual_forms: list[ManualForm] = []
        #: The verb paradigms
        self.verb_paradigms: dict[str, VerbParadigm] = {}
        #: The prefixes
        self.prefixes: list[str] = []
        #: The adjectives: for discovered participles
        self.adjectives: list[Word] = []
        #: The nouns
        self.nouns: list[Word] = []
        #: The verbs
        self.verbs: list[Word] = []

    def categorize(self) -> None:
        """
        Recompute the verb/adjective/noun pools from the current word list.

        Side Effects:
            Overwrites :attr:`verbs`, :attr:`adjectives`, and :attr:`nouns` in place.

        """
        self.verbs = [
            w for w in self.words if w.verb == 1 and (w.pspart + w.papart == 0)
        ]
        self.adjectives = [
            w
            for w in self.words
            if w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)
        ]
        self.nouns = [w for w in self.words if w.noun == 1]

    def append_participle(self, word: "Word") -> None:
        """
        Add a verb-discovered participle to the adjective pool.

        Args:
            word: Participle word discovered during verb generation.

        Side Effects:
            Appends ``word`` to :attr:`adjectives`.

        """
        self.adjectives.append(word)

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


class GenerationRunState:
    """
    Cross-stage scalar state shared across one morphology generation run.
    """

    def __init__(self) -> None:
        """Initialize run state with a zeroed counter and parity-safe defaults."""
        #: The output counter: the number of words output.
        self.output_counter: int = 0
        #: Perl-style shared probability scalar used across generator phases.
        self.perl_probability: int = 0
        #: Whether numeral generation should carry probability across prints.
        #: Enabled by adjective generation in full-flow parity mode.
        self.enable_num_probability_carry: bool = False
        #: Opt-in non-parity extension gate for r-stem noun support.
        #: Default is False to preserve Perl-compatible behavior.
        self.enable_r_stem_nouns: bool = False


class GeneratorSession:
    """
    The primary entry point for the morphology generation service.  This is used
    to store the session data for the generator as the generator is run.

    Composes a :class:`WordPool` and a :class:`GenerationRunState`. Every
    attribute below is a forwarding property onto one or the other, kept for
    backward compatibility with existing callers while callers are migrated,
    file by file, onto the narrower ``word_pool``/``run_state`` collaborators
    directly.
    """

    def __init__(self) -> None:
        """Compose a fresh :class:`WordPool` and :class:`GenerationRunState`."""
        #: Categorized word pools and supporting dictionaries for this run.
        self.word_pool = WordPool()
        #: Cross-stage scalar run state for this run.
        self.run_state = GenerationRunState()

    @property
    def words(self) -> list["Word"]:
        """
        The words: the words to be processed.

        Returns:
            The current word list from :attr:`word_pool`.

        """
        return self.word_pool.words

    @words.setter
    def words(self, value: list["Word"]) -> None:
        """
        Forward an updated word list onto :attr:`word_pool`.

        Args:
            value: The new word list.

        """
        self.word_pool.words = value

    @property
    def manual_forms(self) -> list["ManualForm"]:
        """
        The manual forms.

        Returns:
            The manual forms list from :attr:`word_pool`.

        """
        return self.word_pool.manual_forms

    @manual_forms.setter
    def manual_forms(self, value: list["ManualForm"]) -> None:
        """
        Forward an updated manual forms list onto :attr:`word_pool`.

        Args:
            value: The new manual forms list.

        """
        self.word_pool.manual_forms = value

    @property
    def verb_paradigms(self) -> dict[str, "VerbParadigm"]:
        """
        The verb paradigms.

        Returns:
            The verb paradigms mapping from :attr:`word_pool`.

        """
        return self.word_pool.verb_paradigms

    @verb_paradigms.setter
    def verb_paradigms(self, value: dict[str, "VerbParadigm"]) -> None:
        """
        Forward an updated verb paradigms mapping onto :attr:`word_pool`.

        Args:
            value: The new verb paradigms mapping.

        """
        self.word_pool.verb_paradigms = value

    @property
    def prefixes(self) -> list[str]:
        """
        The prefixes.

        Returns:
            The prefixes list from :attr:`word_pool`.

        """
        return self.word_pool.prefixes

    @prefixes.setter
    def prefixes(self, value: list[str]) -> None:
        """
        Forward an updated prefixes list onto :attr:`word_pool`.

        Args:
            value: The new prefixes list.

        """
        self.word_pool.prefixes = value

    @property
    def adjectives(self) -> list["Word"]:
        """
        The adjectives: for discovered participles.

        Returns:
            The adjectives list from :attr:`word_pool`.

        """
        return self.word_pool.adjectives

    @adjectives.setter
    def adjectives(self, value: list["Word"]) -> None:
        """
        Forward an updated adjectives list onto :attr:`word_pool`.

        Args:
            value: The new adjectives list.

        """
        self.word_pool.adjectives = value

    @property
    def nouns(self) -> list["Word"]:
        """
        The nouns.

        Returns:
            The nouns list from :attr:`word_pool`.

        """
        return self.word_pool.nouns

    @nouns.setter
    def nouns(self, value: list["Word"]) -> None:
        """
        Forward an updated nouns list onto :attr:`word_pool`.

        Args:
            value: The new nouns list.

        """
        self.word_pool.nouns = value

    @property
    def verbs(self) -> list["Word"]:
        """
        The verbs.

        Returns:
            The verbs list from :attr:`word_pool`.

        """
        return self.word_pool.verbs

    @verbs.setter
    def verbs(self, value: list["Word"]) -> None:
        """
        Forward an updated verbs list onto :attr:`word_pool`.

        Args:
            value: The new verbs list.

        """
        self.word_pool.verbs = value

    @property
    def output_counter(self) -> int:
        """
        The output counter: the number of words output.

        Returns:
            The output counter from :attr:`run_state`.

        """
        return self.run_state.output_counter

    @output_counter.setter
    def output_counter(self, value: int) -> None:
        """
        Forward an updated output counter onto :attr:`run_state`.

        Args:
            value: The new output counter value.

        """
        self.run_state.output_counter = value

    @property
    def perl_probability(self) -> int:
        """
        Perl-style shared probability scalar used across generator phases.

        Returns:
            The current probability scalar from :attr:`run_state`.

        """
        return self.run_state.perl_probability

    @perl_probability.setter
    def perl_probability(self, value: int) -> None:
        """
        Forward an updated probability scalar onto :attr:`run_state`.

        Args:
            value: The new probability scalar value.

        """
        self.run_state.perl_probability = value

    @property
    def enable_num_probability_carry(self) -> bool:
        """
        Whether numeral generation should carry probability across prints.

        Returns:
            The probability-carry flag from :attr:`run_state`.

        """
        return self.run_state.enable_num_probability_carry

    @enable_num_probability_carry.setter
    def enable_num_probability_carry(self, value: bool) -> None:
        """
        Forward an updated probability-carry flag onto :attr:`run_state`.

        Args:
            value: The new probability-carry flag value.

        """
        self.run_state.enable_num_probability_carry = value

    @property
    def enable_r_stem_nouns(self) -> bool:
        """
        Opt-in non-parity extension gate for r-stem noun support.

        Returns:
            The r-stem noun gate flag from :attr:`run_state`.

        """
        return self.run_state.enable_r_stem_nouns

    @enable_r_stem_nouns.setter
    def enable_r_stem_nouns(self, value: bool) -> None:
        """
        Forward an updated r-stem noun gate flag onto :attr:`run_state`.

        Args:
            value: The new r-stem noun gate flag value.

        """
        self.run_state.enable_r_stem_nouns = value

    @property
    def prefix_regex(self) -> str:
        """
        Get the prefix regex, used to match the prefixes of the words.

        Prefixes are loaded from the prefixes file

        Returns:
            The prefix regex.

        """
        return self.word_pool.prefix_regex

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
        self.word_pool.categorize()

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
