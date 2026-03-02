from __future__ import annotations

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from ..models.diacritics import (
    POS_CODE_LABELS,
    AmbiguityOption,
    DiacriticRestorationResult,
    MacronAmbiguity,
    MacronIndexPayload,
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
    r"[^\W\d_]+(?:[-\u2013\u2014][^\W\d_]+)*", re.UNICODE
)
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


class MacronApplicator:
    """
    Apply dictionary-backed macrons to lexical tokens.
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
                marked_form_raw = TRAILING_HEADWORD_PUNCT_RE.sub(
                    "", headword_match.group(1).strip()
                )
                if not _is_oe_wordlike(marked_form_raw):
                    continue

                parsed_count += 1
                for raw_normalized_form in normalized_part.split(","):
                    normalized_form = raw_normalized_form.strip()
                    if (
                        not normalized_form
                        or not _is_oe_wordlike(normalized_form)
                        or normalized_form.startswith("-")
                        or normalized_form.endswith("-")
                    ):
                        continue
                    key = normalize_old_english(normalized_form)
                    marked = marked_form_raw.lower()
                    if key is None:
                        continue
                    candidates.setdefault(key, set()).add(marked)

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
    ) -> tuple[str, MacronAmbiguity | None, bool]:
        """
        Apply macrons to a single lexical token.

        Args:
            word: Verbatim lexical token.
            line_number: 1-based line number.
            word_number: 1-based lexical token number within line.

        Returns:
            Tuple of (transformed token, optional ambiguity row, is_unknown).
            is_unknown is True when the token normalized but was not in the index.

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
            return word, None, False

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
            return word, ambiguity, False

        marked = self.index.unique.get(normalized)
        if marked is None:
            LOGGER.debug(
                "Macron no-match token='%s' line=%d word=%d",
                word,
                line_number,
                word_number,
            )
            return word, None, True

        transformed = _apply_case_pattern(word, marked)
        LOGGER.debug(
            "Macron applied token='%s' -> '%s' line=%d word=%d",
            word,
            transformed,
            line_number,
            word_number,
        )
        return transformed, None, False


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

    def palatalize(self, word: str) -> str:
        """
        Palatalize ``g`` in a lexical token.

        Args:
            word: Token to palatalize.

        Returns:
            Palatalized token.

        """
        original = word
        lower = word.lower()

        if "-" in lower:
            parts = lower.split("-")
            palatalized_parts = [self.palatalize(part) for part in parts]
            palatalized = "-".join(palatalized_parts)
            return _apply_case_pattern(original, palatalized)

        if (
            lower.startswith("g")
            and len(lower) > 1
            and lower[1] in self.FRONT_VOWELS
            and lower not in self.FRONTAL_G_EXCEPTIONS
        ):
            lower = "ġ" + lower[1:]

        if (
            lower.endswith("g")
            and len(lower) > 1
            and lower[-2] in self.FRONT_VOWELS
            and lower not in self.ENDING_G_EXCEPTIONS
        ):
            lower = lower[:-1] + "ġ"

        if len(lower) >= self.MIN_INTERNAL_G_LENGTH:
            chars = list(lower)
            for i, char in enumerate(chars):
                if char != "g" or i == 0 or i == len(chars) - 1:
                    continue
                if (
                    chars[i - 1] in self.FRONT_VOWELS
                    and chars[i + 1] in self.FRONT_VOWELS
                ):
                    chars[i] = "ġ"
            lower = "".join(chars)

        first_g = lower.find("g")
        if first_g > 0 and lower[first_g - 1] in self.FRONT_VOWELS:
            lower = lower[:first_g] + "ġ" + lower[first_g + 1 :]

        transformed = _apply_case_pattern(original, lower)
        if transformed != word:
            LOGGER.debug("G palatalized '%s' -> '%s'", word, transformed)
        return transformed


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
        Palatalize ``c`` in a lexical token per rules A-D and i-mutation caveat.

        Rule A: word-initial c before front vowel (unless only-back trigger).
        Rule B: medial c before e/æ/y does not palatalize (no branch).
        Rule C: c before i/ī in any position → ċ.
        Rule D: c after i/ī (possibly +n) unless back vowel follows → ċ.

        Args:
            word: Token to palatalize.

        Returns:
            Palatalized token.

        """
        original = word
        lower = word.lower()

        if "-" in lower:
            parts = lower.split("-")
            palatalized_parts = [self.palatalize(part) for part in parts]
            palatalized = "-".join(palatalized_parts)
            return _apply_case_pattern(original, palatalized)

        normalized = normalize_old_english(lower)
        if normalized in self.force_non_palatalize:
            LOGGER.debug("C palatalization blocked by exception for '%s'", word)
            return word

        chars = list(lower)
        for i, char in enumerate(chars):
            if char != "c":
                continue

            should_palatalize = False

            # Rule C: c before i/ī in any position
            if i + 1 < len(chars) and chars[i + 1] in {"i", "ī"}:
                should_palatalize = True

            # Rule A: word-initial c before front vowel (not when only-back, e.g. y/ȳ)
            if (
                not should_palatalize
                and i == 0
                and self._is_front_context(lower, i + 1)
                and i + 1 < len(chars)
                and not self._vowel_has_only_back_pre_sources(chars[i + 1])
            ):
                should_palatalize = True

            # Rule D: c after i/ī (possibly +n) unless back vowel follows
            if not should_palatalize and self._preceding_is_i_or_i_with_optional_n(
                chars, i
            ):
                should_palatalize = (
                    i == len(chars) - 1 or chars[i + 1] not in self.BACK_VOWELS
                )

            if should_palatalize:
                chars[i] = "ċ"

        transformed_lower = "".join(chars)

        if normalized in self.force_palatalize and transformed_lower.endswith("c"):
            transformed_lower = transformed_lower[:-1] + "ċ"
            LOGGER.debug(
                "C palatalization forced final-ċ exception for '%s' -> '%s'",
                word,
                transformed_lower,
            )

        transformed = _apply_case_pattern(original, transformed_lower)
        if transformed != word:
            LOGGER.debug("C palatalized '%s' -> '%s'", word, transformed)
        return transformed


class DiacriticRestorer:
    """
    Composite Old English diacritic restoration pipeline.
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
        Restore diacritics across a full input text.

        Args:
            text: Input text without (or with partial) diacritics.

        Returns:
            Restoration result containing transformed text and ambiguities.

        """
        ambiguities: list[MacronAmbiguity] = []
        unknowns: list[UnknownToken] = []
        output_lines: list[str] = []

        for line_idx, line in enumerate(text.splitlines(keepends=True), start=1):
            segments: list[str] = []
            last_end = 0
            for word_counter, match in enumerate(
                LEXICAL_TOKEN_RE.finditer(line), start=1
            ):
                start, end = match.span()
                token = match.group(0)
                segments.append(line[last_end:start])

                macroned, ambiguity, is_unknown = self.macron_applicator.apply(
                    token,
                    line_number=line_idx,
                    word_number=word_counter,
                )
                if ambiguity is not None:
                    ambiguities.append(ambiguity)
                if is_unknown:
                    unknowns.append(
                        UnknownToken(
                            line_number=line_idx,
                            word_number=word_counter,
                            word=token,
                        )
                    )

                palatalized_g = self.g_palatalizer.palatalize(macroned)
                palatalized_c = self.c_palatalizer.palatalize(palatalized_g)
                segments.append(palatalized_c)
                last_end = end

            segments.append(line[last_end:])
            output_lines.append("".join(segments))

        restored_text = "".join(output_lines)
        LOGGER.debug(
            "Diacritic restoration complete (lines=%d, ambiguities=%d, unknowns=%d)",
            len(output_lines),
            len(ambiguities),
            len(unknowns),
        )
        return DiacriticRestorationResult(
            marked_text=restored_text,
            ambiguities=ambiguities,
            unknowns=unknowns,
        )
