from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from ..models.diacritics import (
    POS_CODE_LABELS,
    AmbiguityOption,
    DiacriticRestorationResult,
    MacronAmbiguity,
    MacronIndexPayload,
    UnalignedToken,
    UnknownToken,
)
from ..models.macron_index import MacronIndex

#: Module logger.
LOGGER = logging.getLogger(__name__)

#: Root directory of this repository.
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
#: Default package data directory used by diacritic tools.
DEFAULT_DIACRITIC_DIR: Final[Path] = PROJECT_ROOT / "wyrdcraeft" / "etc" / "diacritic"
#: Default macron index path.
DEFAULT_MACRON_INDEX_PATH: Final[Path] = (
    DEFAULT_DIACRITIC_DIR / "oe_bt_macron_index.json"
)
#: Default force-palatalize list for ``c``.
DEFAULT_C_FORCE_PALATALIZE_PATH: Final[Path] = (
    DEFAULT_DIACRITIC_DIR / "c_palatalization_force_palatalize.txt"
)
#: Default force-non-palatalize list for ``c``.
DEFAULT_C_FORCE_NON_PALATALIZE_PATH: Final[Path] = (
    DEFAULT_DIACRITIC_DIR / "c_palatalization_force_non_palatalize.txt"
)

#: Regex used to split lexical tokens while preserving separators.
LEXICAL_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:[^\W\d_][\u0300-\u036f]*)+"
    r"(?:[-\u2013\u2014](?:[^\W\d_][\u0300-\u036f]*)+)*",
    re.UNICODE,
)
#: Regex splitting text into letter+combining-mark clusters and single others.
CLUSTER_RE: Final[re.Pattern[str]] = re.compile(
    r"[^\W\d_][\u0300-\u036f]*|.", re.UNICODE | re.DOTALL
)
#: Hyphen and dash characters treated as word-internal joiners.
DASH_CHARS: Final[str] = "-\u2013\u2014"
#: Regex splitting a token on joiners while keeping them.
DASH_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"([-\u2013\u2014])")
#: Combining dot above, used for ``ġ``/``ċ``.
DOT_ABOVE: Final[str] = "\u0307"
#: Adjacent vowel pairs (first, second) that count as one diphthong.
DIPHTHONGS: Final[frozenset[tuple[str, str]]] = frozenset(
    {("e", "a"), ("e", "o"), ("i", "e"), ("i", "o")}
)
#: Combining macron, the only mark that is shared between a diphthong's vowels.
MACRON: Final[str] = "\u0304"
#: Regex for extracting first bold headword from Bosworth-Toller lines.
BOLD_HEADWORD_RE: Final[re.Pattern[str]] = re.compile(r"<B>(.*?)</B>")
#: Trailing punctuation to trim from extracted headwords.
TRAILING_HEADWORD_PUNCT_RE: Final[re.Pattern[str]] = re.compile(r"[;,.]+$")
#: Internal dash matcher for normalization.
INTERNAL_DASH_RE: Final[re.Pattern[str]] = re.compile(r"(?<=\S)[-\u2013\u2014](?=\S)")
#: Expected number of fields when splitting Bosworth-Toller lines by ``@``.
BT_SPLIT_PART_COUNT: Final[int] = 3


def normalize_old_english(text: str | None) -> str | None:
    """
    A simple Old English word normalizer for stable matching.

    Rules:
        - Lowercase
        - Replace ``ð`` with ``þ``
        - Remove combining-mark diacritics
        - Remove internal hyphen/dash characters
        - Preserve OE letters like ``æ`` and ``þ``

    Args:
        text: Source text.

    Returns:
        Normalized text, or ``None`` when input is ``None``.

    """
    if text is None:
        return None
    lowered = text.strip().lower().replace("ð", "þ")
    decomposed = unicodedata.normalize("NFD", lowered)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    stripped_internal_hyphen = INTERNAL_DASH_RE.sub("", without_marks)
    return unicodedata.normalize("NFC", stripped_internal_hyphen)


def normalize_morphology_title(text: str | None) -> str:
    """
    Normalize a morphology lemma title while preserving macrons and dot letters.

    Rules:
        - Lowercase
        - Replace ``ð`` with ``þ``
        - Remove internal hyphen/dash characters
        - Correct BT-style long diphthong marks (for example ``beōn`` -> ``bēon``)
        - Preserve macrons, dotted ``c``/``g``, and OE letters like ``æ`` and ``þ``

    Args:
        text: Source lemma title text.

    Returns:
        Normalized title text, or an empty string when input is ``None``/blank.

    """
    if text is None:
        return ""
    lowered = text.strip().lower().replace("ð", "þ")
    if not lowered:
        return ""
    stripped_internal_hyphen = INTERNAL_DASH_RE.sub("", lowered)
    nfc = unicodedata.normalize("NFC", stripped_internal_hyphen)
    from .morphology.text_utils import OENormalizer  # noqa: PLC0415

    return OENormalizer.normalize_bt_display_spelling(nfc)


def _apply_case_pattern(source: str, target: str) -> str:
    """
    Apply source casing pattern to target text.

    Args:
        source: Original text to mirror case from.
        target: Replacement text.

    Returns:
        Cased replacement text.

    """
    if not source:
        return target
    if source.isupper():
        return target.upper()
    if source[0].isupper() and source[1:].islower():
        return target[:1].upper() + target[1:]
    return target


def _is_oe_wordlike(form: str) -> bool:
    """
    Determine whether a form looks like a lexical OE token.

    Args:
        form: Candidate form.

    Returns:
        ``True`` when form is a single lexical token.

    """
    return bool(LEXICAL_TOKEN_RE.fullmatch(form))


def _fold(text: str) -> str:
    """
    Fold text for exception-list comparison: NFC, lowercase, ``ð`` as ``þ``.

    Args:
        text: Text to fold.

    Returns:
        Folded text; macrons are kept.

    """
    return unicodedata.normalize("NFC", text).lower().replace("ð", "þ")


def _graft_dots(clusters: list[str], lows: list[str], after: str) -> str:
    """
    Add a dot above to source clusters whose lowered letter became ``ġ``/``ċ``.

    Only ``g``→``ġ`` and ``c``→``ċ`` changes are applied, and only by appending
    a combining dot to the original cluster, so case and every other character
    of the source token are preserved.

    Args:
        clusters: Source token split into letter+mark clusters.
        lows: NFC-lowercased form of each cluster (parallel to ``clusters``).
        after: Palatalized lowercase token (``"".join(lows)`` with dots added).

    Returns:
        Source token with dots added.

    """
    out: list[str] = []
    offset = 0
    for cluster, low in zip(clusters, lows, strict=True):
        segment = after[offset : offset + len(low)]
        offset += len(low)
        if (low, segment) in (("g", "ġ"), ("c", "ċ")):
            out.append(unicodedata.normalize("NFC", cluster + DOT_ABOVE))
        else:
            out.append(cluster)
    return "".join(out)


@dataclass(frozen=True)
class _Letter:
    """
    One letter of a token together with its combining marks.
    """

    #: Letter plus combining marks, exactly as written.
    cluster: str
    #: Case-folded base letter, with ``ð`` as ``þ``.
    base: str
    #: Combining marks on the letter, as decomposed characters.
    marks: frozenset[str]
    #: Whether no hyphen or dash separates this letter from the previous one.
    joined: bool


class DiacriticTransfer:
    """
    Copy combining marks from a macron-index form onto a source token.

    The index form never replaces the source token: its letters are aligned
    one-to-one with the source letters (case, ``ð``≡``þ`` and hyphens/dashes
    ignored) and only marks missing from the source are added. A diphthong
    (``ea``, ``eo``, ``ie``, ``io``, with no hyphen between the vowels in the
    index form and only macrons on them) is one unit whose macron always sits on
    the first vowel, whichever vowel the index form or the source marked.
    """

    @staticmethod
    def _parse(text: str) -> list[_Letter]:
        """
        Split text into letters, dropping hyphens and dashes.

        Args:
            text: Token text.

        Returns:
            The letters in order, each noting whether it is joined to the
            previous letter without a hyphen or dash between them.

        """
        letters: list[_Letter] = []
        joined = False
        for cluster in CLUSTER_RE.findall(text):
            if cluster in DASH_CHARS:
                joined = False
                continue
            decomposed = unicodedata.normalize("NFD", cluster)
            letters.append(
                _Letter(
                    cluster=cluster,
                    base=decomposed[0].lower().replace("ð", "þ"),
                    marks=frozenset(decomposed[1:]),
                    joined=joined,
                )
            )
            joined = True
        return letters

    @staticmethod
    def _diphthong_starts(letters: list[_Letter]) -> list[int]:
        """
        Find the diphthongs of a form.

        A diphthong is an adjacent pair from :data:`DIPHTHONGS` with no hyphen
        between the vowels and no mark other than a macron on either (a breve in
        a loanword such as ``ēliŏtrŏpus`` marks a hiatus, not a diphthong).
        Pairs do not overlap; the first one wins.

        Args:
            letters: Letters of the form that defines the word, the index form.

        Returns:
            The index of the first vowel of each diphthong, in order.

        """
        starts: list[int] = []
        i = 0
        while i + 1 < len(letters):
            first, second = letters[i], letters[i + 1]
            if (
                second.joined
                and (first.base, second.base) in DIPHTHONGS
                and (first.marks | second.marks) <= {MACRON}
            ):
                starts.append(i)
                i += 2
            else:
                i += 1
        return starts

    @staticmethod
    def _merge_diphthongs(
        letters: list[_Letter], starts: list[int]
    ) -> list[frozenset[str]]:
        """
        Return each letter's marks with diphthong marks moved to the first vowel.

        Args:
            letters: Letters of one form.
            starts: First-vowel indexes of the diphthongs, from the index form.

        Returns:
            One mark set per letter; the second vowel of a diphthong has none.

        """
        marks = [letter.marks for letter in letters]
        for i in starts:
            marks[i] = marks[i] | marks[i + 1]
            marks[i + 1] = frozenset()
        return marks

    @classmethod
    def mark_pattern(cls, form: str) -> tuple[tuple[str, frozenset[str]], ...]:
        """
        Describe a form as its letters and marks, independent of spelling noise.

        Case, hyphens, dashes and ``ð``/``þ`` do not matter, and a diphthong's
        macron is always on its first vowel, so ``leāst`` and ``lēast`` have the
        same pattern.

        Args:
            form: A source word or an index display form.

        Returns:
            One ``(base letter, marks)`` pair per letter.

        """
        letters = cls._parse(form)
        marks = cls._merge_diphthongs(letters, cls._diphthong_starts(letters))
        return tuple(
            (letter.base, mark_set)
            for letter, mark_set in zip(letters, marks, strict=True)
        )

    @classmethod
    def transfer(cls, source: str, marked: str) -> str | None:
        """
        Add the index form's marks to the matching letters of ``source``.

        Args:
            source: Verbatim source token.
            marked: Macron-index display form for the same word.

        Returns:
            The source token with missing marks added, or ``None`` when the
            letters of the two forms cannot be aligned.

        """
        source_letters = cls._parse(source)
        index_letters = cls._parse(marked)
        if len(source_letters) != len(index_letters) or any(
            s.base != i.base for s, i in zip(source_letters, index_letters, strict=True)
        ):
            return None
        starts = cls._diphthong_starts(index_letters)
        source_marks = cls._merge_diphthongs(source_letters, starts)
        index_marks = cls._merge_diphthongs(index_letters, starts)
        additions = {
            n: index_marks[n]
            for n in range(len(source_letters))
            if index_marks[n] and not source_marks[n]
        }
        out: list[str] = []
        letter_index = 0
        for cluster in CLUSTER_RE.findall(source):
            if cluster in DASH_CHARS:
                out.append(cluster)
                continue
            if letter_index in additions:
                marks = "".join(sorted(additions[letter_index]))
                out.append(unicodedata.normalize("NFC", cluster + marks))
            else:
                out.append(cluster)
            letter_index += 1
        return "".join(out)


class MacronApplicator:
    """
    Apply dictionary-backed macrons to lexical tokens.

    Args:
        index_path: Path to macron index JSON.

    """

    def __init__(self, index_path: Path = DEFAULT_MACRON_INDEX_PATH):
        """
        Initialize applicator from a prebuilt index.

        Args:
            index_path: Path to macron index JSON.

        """
        #: Path to the prebuilt macron index.
        self.index_path = index_path
        #: Parsed in-memory index.
        self.index = self.load_index(index_path)

    @classmethod
    def load_index(cls, index_path: Path) -> MacronIndex:
        """
        Load a prebuilt macron index from disk.

        Args:
            index_path: Path to JSON index.

        Raises:
            FileNotFoundError: If the index file does not exist.
            ValueError: If the index file format is invalid.

        Returns:
            Loaded :class:`MacronIndex`.

        """
        if not index_path.exists():
            msg = (
                f"Macron index not found at {index_path}. "
                "Build it with data/tools/build_macron_index.py."
            )
            raise FileNotFoundError(msg)

        try:
            payload = MacronIndexPayload.model_validate(
                json.loads(index_path.read_text(encoding="utf-8"))
            )
        except (TypeError, ValidationError, ValueError) as e:
            msg = (
                "Invalid macron index format; expected object with unique/ambiguous "
                "and optional ambiguous_metadata."
            )
            raise TypeError(msg) from e

        LOGGER.debug(
            "Loaded macron index from %s (unique=%d, ambiguous=%d, metadata=%d)",
            index_path,
            len(payload.unique),
            len(payload.ambiguous),
            len(payload.ambiguous_metadata),
        )
        return MacronIndex(
            unique=payload.unique,
            ambiguous=payload.ambiguous,
            ambiguous_metadata=payload.ambiguous_metadata,
        )

    @staticmethod
    def _headword_forms(bold_text: str) -> dict[str, set[str]]:
        """
        Extract the lexical forms spelled out in a bold heading.

        Args:
            bold_text: Text of the first ``<B>`` heading of an entry.

        Returns:
            Mapping of normalized key to the lowercase marked forms.

        """
        forms: dict[str, set[str]] = {}
        for raw in bold_text.split(","):
            form = TRAILING_HEADWORD_PUNCT_RE.sub("", raw.strip())
            key = normalize_old_english(form)
            if key and _is_oe_wordlike(form):
                forms.setdefault(key, set()).add(form.lower())
        return forms

    @staticmethod
    def _variant_keys(normalized_part: str) -> list[str]:
        """
        Normalize the comma-separated variant list of an entry.

        Args:
            normalized_part: Third ``@`` field of a Bosworth-Toller line.

        Returns:
            Normalized keys of the usable (non-affix, lexical) variants.

        """
        keys: list[str] = []
        for raw in normalized_part.split(","):
            form = raw.strip()
            if (
                not form
                or not _is_oe_wordlike(form)
                or form.startswith("-")
                or form.endswith("-")
            ):
                continue
            key = normalize_old_english(form)
            if key is not None:
                keys.append(key)
        return keys

    @classmethod
    def build_index_from_bt(
        cls, source_path: Path, output_path: Path | None = None
    ) -> MacronIndex:
        """
        Build a macron index from Bosworth-Toller source data.

        Args:
            source_path: Path to ``oe_bt.txt``.
            output_path: Optional destination JSON path.

        Raises:
            FileNotFoundError: If source file is missing.

        Returns:
            Built :class:`MacronIndex`.

        """
        if not source_path.exists():
            msg = f"Bosworth-Toller source not found: {source_path}"
            raise FileNotFoundError(msg)

        candidates: dict[str, set[str]] = {}
        line_count = 0
        parsed_count = 0

        with source_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line_count += 1
                line = raw_line.rstrip("\n")
                parts = line.split("@", maxsplit=2)
                if len(parts) != BT_SPLIT_PART_COUNT:
                    continue

                normalized_part = parts[2]
                headword_match = BOLD_HEADWORD_RE.search(parts[1])
                if headword_match is None:
                    continue
                headword_forms = cls._headword_forms(headword_match.group(1))
                if not headword_forms:
                    continue

                parsed_count += 1
                for key in cls._variant_keys(normalized_part):
                    # A variant gets its own entry only when the heading
                    # spells it out; otherwise there are no marks to record.
                    if key in headword_forms:
                        candidates.setdefault(key, set()).update(headword_forms[key])

        unique: dict[str, str] = {}
        ambiguous: dict[str, list[str]] = {}

        for key, forms in candidates.items():
            sorted_forms = sorted(forms)
            if len(sorted_forms) == 1:
                unique[key] = sorted_forms[0]
            else:
                ambiguous[key] = sorted_forms

        index = MacronIndex(
            unique=unique,
            ambiguous=ambiguous,
            ambiguous_metadata={},
        )

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_payload = {
                "meta": {
                    "source_path": str(source_path),
                    "line_count": line_count,
                    "parsed_entry_count": parsed_count,
                    "unique_count": len(unique),
                    "ambiguous_count": len(ambiguous),
                },
                "unique": unique,
                "ambiguous": ambiguous,
                "ambiguous_metadata": {},
            }
            output_path.write_text(
                json.dumps(output_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            LOGGER.debug(
                "Wrote macron index to %s (unique=%d, ambiguous=%d)",
                output_path,
                len(unique),
                len(ambiguous),
            )

        LOGGER.debug(
            "Built macron index from %s (lines=%d, parsed=%d, unique=%d, ambiguous=%d)",
            source_path,
            line_count,
            parsed_count,
            len(unique),
            len(ambiguous),
        )
        return index

    def apply(
        self, word: str, line_number: int, word_number: int
    ) -> tuple[str, MacronAmbiguity | None, bool, str | None]:
        """
        Add index diacritics to a single lexical token, preserving its letters.

        Args:
            word: Verbatim lexical token.
            line_number: 1-based line number.
            word_number: 1-based lexical token number within line.

        Returns:
            Tuple of (transformed token, optional ambiguity row, is_unknown,
            unaligned index form). is_unknown is True when the token normalized
            but was not in the index. The last item is the index display form
            when it could not be aligned to the source (token returned
            unchanged), else ``None``.

        """
        normalized = normalize_old_english(word)
        LOGGER.debug(
            "Macron lookup token='%s' normalized='%s' line=%d word=%d",
            word,
            normalized,
            line_number,
            word_number,
        )
        if not normalized:
            return word, None, False, None

        if normalized in self.index.ambiguous:
            raw_options = self.index.ambiguous[normalized]
            metadata_by_form = self.index.ambiguous_metadata.get(normalized, {})
            options_list: list[AmbiguityOption] = []
            for opt in raw_options:
                cased_form = _apply_case_pattern(word, opt)
                annotation = metadata_by_form.get(opt)
                if annotation and annotation.senses:
                    pos_labels = sorted(
                        dict.fromkeys(
                            POS_CODE_LABELS.get(
                                s.part_of_speech_code, s.part_of_speech_code
                            )
                            for s in annotation.senses
                        )
                    )
                    part_of_speech = ", ".join(pos_labels) if pos_labels else None
                    definitions = [s.modern_english_meaning for s in annotation.senses]
                    options_list.append(
                        AmbiguityOption(
                            form=cased_form,
                            part_of_speech=part_of_speech,
                            definitions=definitions,
                        )
                    )
                else:
                    options_list.append(
                        AmbiguityOption(
                            form=cased_form,
                            part_of_speech=None,
                            definitions=[],
                        )
                    )
            ambiguity = MacronAmbiguity(
                line_number=line_number,
                word_number=word_number,
                word=word,
                options=options_list,
            )
            LOGGER.debug(
                "Macron ambiguous token='%s' line=%d word=%d options=%s",
                word,
                line_number,
                word_number,
                [o.form for o in options_list],
            )
            return word, ambiguity, False, None

        marked = self.index.unique.get(normalized)
        if marked is None:
            LOGGER.debug(
                "Macron no-match token='%s' line=%d word=%d",
                word,
                line_number,
                word_number,
            )
            return word, None, True, None

        transformed = DiacriticTransfer.transfer(word, marked)
        if transformed is None:
            LOGGER.debug(
                "Macron unaligned token='%s' index_form='%s' line=%d word=%d",
                word,
                marked,
                line_number,
                word_number,
            )
            return word, None, False, marked
        LOGGER.debug(
            "Macron applied token='%s' -> '%s' line=%d word=%d",
            word,
            transformed,
            line_number,
            word_number,
        )
        return transformed, None, False, None


class GPalatalizer:
    """
    Palatalize ``g`` in a single lexical token.
    """

    #: Words that seem like they should have a palatalized ``g``, but do not.
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
        "gēs",  # "geese"; ē from i-mutation of ō, g stays velar (see c blocklist)
        "gēsne",
        "gēsnian",
        "gēsting",
        "gēstlīc",
        "gēsthus",
        "gēat",
        "gēatlic",
        "gēard",
        "gēatas",
        "gēatland",
    ]

    #: Ending palatalized-g exceptions.
    ENDING_G_EXCEPTIONS: Final[list[str]] = ["plǣg", "sweg", "tǣghrēg"]

    #: Front vowels and diphthongs.
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

    #: Minimum token length for internal ``g`` checks.
    MIN_INTERNAL_G_LENGTH: Final[int] = 3

    #: Back vowels; a ``g`` before one stays velar.
    BACK_VOWELS: Final[frozenset[str]] = frozenset({"a", "ā", "o", "ō", "u", "ū"})

    def palatalize(self, word: str) -> str:
        """
        Add a dot above to palatal ``g`` in a lexical token.

        Only the dot is added; the rest of the token is left as written.

        Args:
            word: Token to palatalize.

        Returns:
            Token with ``ġ`` dots added.

        """
        clusters = CLUSTER_RE.findall(word)
        lows = [unicodedata.normalize("NFC", c).lower() for c in clusters]
        parts = DASH_SPLIT_RE.split("".join(lows))
        after = "".join(
            part if part in DASH_CHARS else self._palatalize_segment(part)
            for part in parts
        )
        transformed = _graft_dots(clusters, lows, after)
        if transformed != word:
            LOGGER.debug("G palatalized '%s' -> '%s'", word, transformed)
        return transformed

    def _palatalize_segment(self, lower: str) -> str:
        """
        Palatalize ``g`` in one lowercase, dash-free segment.

        Args:
            lower: NFC-lowercased segment.

        Returns:
            Segment with ``ġ`` substituted where appropriate.

        """
        folded = _fold(lower)
        chars = list(lower)
        for i, char in enumerate(chars):
            if char == "g" and self._is_palatal(chars, i, folded):
                chars[i] = "ġ"
        return "".join(chars)

    def _is_palatal(self, chars: list[str], i: int, folded: str) -> bool:
        """
        Decide whether the ``g`` at ``chars[i]`` is palatal.

        Args:
            chars: Segment characters.
            i: Index of the ``g``.
            folded: Folded whole segment, for exception lookup.

        Returns:
            ``True`` when the ``g`` should get a dot.

        """
        last = len(chars) - 1
        following = chars[i + 1] if i < last else ""
        if i == 0:
            return (
                following in self.FRONT_VOWELS
                and folded not in self._frontal_exceptions
            )
        if chars[i - 1] not in self.FRONT_VOWELS or following in self.BACK_VOWELS:
            return False
        return not (i == last and folded in self._ending_exceptions)

    @property
    def _frontal_exceptions(self) -> frozenset[str]:
        """
        Fold :attr:`FRONTAL_G_EXCEPTIONS` for comparison.

        Returns:
            Folded exception words.

        """
        return frozenset(_fold(w) for w in self.FRONTAL_G_EXCEPTIONS)

    @property
    def _ending_exceptions(self) -> frozenset[str]:
        """
        Fold :attr:`ENDING_G_EXCEPTIONS` for comparison.

        Returns:
            Folded exception words.

        """
        return frozenset(_fold(w) for w in self.ENDING_G_EXCEPTIONS)


def _possible_pre_iumlaut_sources(vowel: str) -> frozenset[str]:
    """
    Return possible pre-i-mutation (reconstructed) sources for an OE vowel.

    Used to avoid palatalizing c when the triggering vowel unambiguously
    derives from a back vowel (palatalization preceded i-mutation).

    Args:
        vowel: Single character, typically a front vowel in attested OE.

    Returns:
        Frozenset of possible pre-mutation vowel(s); empty if unknown.

    """
    # y, ȳ → only u, ū (unambiguous: do not palatalize c)
    if vowel in ("y", "ȳ"):
        return frozenset({"u", "ū"})
    # e, ē → o, ō or æ, ǣ (ambiguous; blocklist handles)
    if vowel in ("e", "ē"):
        return frozenset({"o", "ō", "æ", "ǣ"})
    # æ, ǣ → a, ā
    if vowel in ("æ", "ǣ"):
        return frozenset({"a", "ā"})
    # i, ī → e, ē (front; palatalize)
    if vowel in ("i", "ī"):
        return frozenset({"e", "ē"})
    return frozenset()


class CPalatalizer:
    """
    Palatalize ``c`` to ``ċ`` based on OE context rules.

    Rules (palatalization applied before i-mutation):

    - Rule A: Word-initial ``c`` before any front vowel/diphthong → ċ.
    - Rule B: Medial ``c`` before e/æ/y (non-i) does *not* palatalize.
    - Rule C: ``c`` before /i, i:/ (spelling ``i``, ``ī``) in any position → ċ.
    - Rule D: ``c`` after /i/, /i:/ (possibly +n), unless a back vowel follows
      → ċ (e.g. iċ, dīċ; wicu stays velar because u follows).

    - Caveat: When the triggering vowel has only back pre-i-mutation sources
      (e.g. y/ȳ → u/ū), do not palatalize; blocklist covers remaining cases.

    Args:
        force_palatalize_path: Path to force-palatalize exceptions.
        force_non_palatalize_path: Path to force-non-palatalize exceptions.

    """

    #: Vowels considered front for ``c`` palatalization.
    FRONT_VOWELS: Final[set[str]] = {"i", "ī", "e", "ē", "æ", "ǣ", "y", "ȳ"}
    #: Diphthongs considered front for initial context checks.
    FRONT_DIPHTHONGS: Final[tuple[str, ...]] = ("ea", "ēa", "eo", "ēo", "ie", "īe")
    #: High-front vowels used for final ``-ċ`` and "c after i/ī" checks.
    HIGH_FRONT_VOWELS: Final[set[str]] = {"i", "ī", "y", "ȳ"}
    #: Back vowels; "c after i/ī" does not palatalize when one of these follows.
    BACK_VOWELS: Final[set[str]] = {"a", "ā", "o", "ō", "u", "ū"}
    #: Minimum index to have two chars before (for "in" / "īn" before c).
    _MIN_INDEX_FOR_PRECEDING_N: Final[int] = 2

    def __init__(
        self,
        force_palatalize_path: Path = DEFAULT_C_FORCE_PALATALIZE_PATH,
        force_non_palatalize_path: Path = DEFAULT_C_FORCE_NON_PALATALIZE_PATH,
    ):
        """
        Initialize C palatalizer with exception list files.

        Args:
            force_palatalize_path: Path to force-palatalize exceptions.
            force_non_palatalize_path: Path to force-non-palatalize exceptions.

        """
        #: Force-palatalize lexical exceptions.
        self.force_palatalize = self._load_word_list(force_palatalize_path)
        #: Force-non-palatalize lexical exceptions.
        self.force_non_palatalize = self._load_word_list(force_non_palatalize_path)

    def _load_word_list(self, path: Path) -> set[str]:
        """
        Load one-word-per-line set from a text file.

        Args:
            path: Source file.

        Returns:
            Set of normalized words.

        """
        if not path.exists():
            LOGGER.warning("C palatalization exception list missing: %s", path)
            return set()
        words: set[str] = set()
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized = normalize_old_english(line)
            if normalized:
                words.add(normalized)
        return words

    def _is_front_context(self, text: str, index: int) -> bool:
        """
        Test if ``text[index:]`` starts with a front-vowel context.

        Args:
            text: Lowercased token.
            index: Start index.

        Returns:
            ``True`` when a front-vowel or front diphthong begins at index.

        """
        if index >= len(text):
            return False
        if text[index] in self.FRONT_VOWELS:
            return True
        return any(text.startswith(diph, index) for diph in self.FRONT_DIPHTHONGS)

    @staticmethod
    def _preceding_is_i_or_i_with_optional_n(chars: list[str], i: int) -> bool:
        """
        Return whether the character before position i is i/ī or i/ī + n.

        Used for Rule D: c after i/ī (possibly with intervening n) may palatalize.

        Args:
            chars: List of characters.
            i: Index of the ``c`` under consideration.

        Returns:
            True if the segment immediately before i is i, ī, in, or īn.

        """
        if i <= 0:
            return False
        return chars[i - 1] in {"i", "ī"} or (
            chars[i - 1] == "n"
            and i >= CPalatalizer._MIN_INDEX_FOR_PRECEDING_N
            and chars[i - 2] in {"i", "ī"}
        )

    def _vowel_has_only_back_pre_sources(self, vowel: str) -> bool:
        """
        Return True if the vowel unambiguously derives only from back vowels.

        Used to avoid palatalizing c when the trigger vowel is from i-mutation
        (e.g. y/ȳ from u/ū).

        Args:
            vowel: Single character (front vowel in attested OE).

        Returns:
            True when possible pre-sources are non-empty and all in BACK_VOWELS.

        """
        sources = _possible_pre_iumlaut_sources(vowel)
        return bool(sources) and sources <= self.BACK_VOWELS

    def palatalize(self, word: str) -> str:
        """
        Add a dot above to palatal ``c`` in a token per rules A-D and the caveat.

        Rule A: word-initial c before front vowel (unless only-back trigger).
        Rule B: medial c before e/æ/y does not palatalize (no branch).
        Rule C: c before i/ī in any position → ċ.
        Rule D: c after i/ī (possibly +n) unless back vowel follows → ċ.
        Exception: the ``c`` of ``sc`` is never dotted.

        Only the dot is added; the rest of the token is left as written.

        Args:
            word: Token to palatalize.

        Returns:
            Token with ``ċ`` dots added.

        """
        clusters = CLUSTER_RE.findall(word)
        lows = [unicodedata.normalize("NFC", c).lower() for c in clusters]
        parts = DASH_SPLIT_RE.split("".join(lows))
        after = "".join(
            part if part in DASH_CHARS else self._palatalize_segment(part)
            for part in parts
        )
        transformed = _graft_dots(clusters, lows, after)
        if transformed != word:
            LOGGER.debug("C palatalized '%s' -> '%s'", word, transformed)
        return transformed

    def _palatalize_segment(self, lower: str) -> str:
        """
        Palatalize ``c`` in one lowercase, dash-free segment.

        Args:
            lower: NFC-lowercased segment.

        Returns:
            Segment with ``ċ`` substituted where appropriate.

        """
        normalized = normalize_old_english(lower)
        if normalized in self.force_non_palatalize:
            LOGGER.debug("C palatalization blocked by exception for '%s'", lower)
            return lower

        chars = list(lower)
        for i, char in enumerate(chars):
            if char == "c" and self._is_palatal(chars, i):
                chars[i] = "ċ"

        transformed = "".join(chars)
        if (
            normalized in self.force_palatalize
            and transformed.endswith("c")
            and not transformed.endswith("sc")
        ):
            transformed = transformed[:-1] + "ċ"
            LOGGER.debug("C palatalization forced final-ċ for '%s'", lower)
        return transformed

    def _is_palatal(self, chars: list[str], i: int) -> bool:
        """
        Decide whether the ``c`` at ``chars[i]`` is palatal by rules A, C, D.

        Args:
            chars: Lowercase segment characters.
            i: Index of the ``c``.

        Returns:
            ``True`` when the ``c`` should get a dot.

        """
        if i > 0 and chars[i - 1] == "s":
            return False
        following = chars[i + 1] if i + 1 < len(chars) else ""
        if following in {"i", "ī"}:
            return True
        if (
            i == 0
            and self._is_front_context("".join(chars), 1)
            and not self._vowel_has_only_back_pre_sources(following)
        ):
            return True
        if self._preceding_is_i_or_i_with_optional_n(chars, i):
            return following not in self.BACK_VOWELS
        return False


class DiacriticRestorer:
    """
    Composite Old English diacritic restoration pipeline.

    Args:
        macron_applicator: Optional preconfigured macron applicator.
        g_palatalizer: Optional preconfigured g-palatalizer.
        c_palatalizer: Optional preconfigured c-palatalizer.
        macron_index_path: Macron index path used when applicator is omitted.

    """

    def __init__(
        self,
        macron_applicator: MacronApplicator | None = None,
        g_palatalizer: GPalatalizer | None = None,
        c_palatalizer: CPalatalizer | None = None,
        macron_index_path: Path = DEFAULT_MACRON_INDEX_PATH,
    ):
        """
        Initialize restorer with component services.

        Args:
            macron_applicator: Optional preconfigured macron applicator.
            g_palatalizer: Optional preconfigured g-palatalizer.
            c_palatalizer: Optional preconfigured c-palatalizer.
            macron_index_path: Macron index path used when applicator is omitted.

        """
        #: Macron component.
        self.macron_applicator = macron_applicator or MacronApplicator(
            macron_index_path
        )
        #: G palatalization component.
        self.g_palatalizer = g_palatalizer or GPalatalizer()
        #: C palatalization component.
        self.c_palatalizer = c_palatalizer or CPalatalizer()

    def restore_text(self, text: str) -> DiacriticRestorationResult:
        """
        Add diacritics across a full input text without altering its letters.

        Args:
            text: Input text without (or with partial) diacritics.

        Returns:
            Restoration result containing transformed text and reports.

        """
        result = DiacriticRestorationResult(marked_text="")
        output_lines = [
            self._restore_line(line, line_idx, result)
            for line_idx, line in enumerate(text.splitlines(keepends=True), start=1)
        ]
        result.marked_text = "".join(output_lines)
        LOGGER.debug(
            "Diacritic restoration complete "
            "(lines=%d, ambiguities=%d, unknowns=%d, unaligned=%d)",
            len(output_lines),
            len(result.ambiguities),
            len(result.unknowns),
            len(result.unaligned),
        )
        return result

    def _restore_line(
        self, line: str, line_idx: int, result: DiacriticRestorationResult
    ) -> str:
        """
        Restore diacritics on one line, keeping separators verbatim.

        Side Effects:
            Appends ambiguity, unknown and unaligned rows to ``result``.

        Args:
            line: Line of text including its line ending.
            line_idx: 1-based line number.
            result: Result accumulating report rows.

        Returns:
            The marked line.

        """
        segments: list[str] = []
        last_end = 0
        for word_counter, match in enumerate(LEXICAL_TOKEN_RE.finditer(line), start=1):
            start, end = match.span()
            token = match.group(0)
            segments.append(line[last_end:start])

            macroned, ambiguity, is_unknown, index_form = self.macron_applicator.apply(
                token, line_number=line_idx, word_number=word_counter
            )
            position = {"line_number": line_idx, "word_number": word_counter}
            if ambiguity is not None:
                result.ambiguities.append(ambiguity)
            if is_unknown:
                result.unknowns.append(UnknownToken(word=token, **position))
            if index_form is not None:
                result.unaligned.append(
                    UnalignedToken(word=token, index_form=index_form, **position)
                )

            segments.append(
                self.c_palatalizer.palatalize(self.g_palatalizer.palatalize(macroned))
            )
            last_end = end
        segments.append(line[last_end:])
        return "".join(segments)
