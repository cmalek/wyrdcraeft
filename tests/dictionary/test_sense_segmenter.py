"""Tests for Phase 03 BTSenseSegmenter."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from wyrdcraeft.models.dictionary import (
    BTGender,
    BTSense,
    format_sense_display_label,
    sense_path_sort_key,
)
from wyrdcraeft.services.dictionary.sense_metadata import (
    SenseMetadataClassifier,
    promote_entry_gender_from_senses,
)
from wyrdcraeft.services.dictionary.sense_segmenter import BTSenseSegmenter
from wyrdcraeft.services.dictionary.sense_tree import (
    RawSenseFragment,
    SenseTreeNormalizer,
)

_GOLDEN_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "golden_senses.jsonl"
)

_MIN_GOLDEN_PASS_RATE = 0.95


def _load_golden() -> list[dict]:  # type: ignore[type-arg]
    raw = _GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in raw if line.strip()]


@pytest.fixture(scope="module")
def segmenter() -> BTSenseSegmenter:
    return BTSenseSegmenter()


@pytest.fixture(scope="module")
def sense_tree_normalizer() -> SenseTreeNormalizer:
    return SenseTreeNormalizer()


def _golden_sense_matches(
    actual: BTSense,
    *,
    label: str,
    gloss_en: str,
) -> bool:
    return actual.sense_label == label and actual.gloss_en == gloss_en


class TestSenseTreeNormalizer:
    """Unit tests for canonical sense-path normalization."""

    def test_roman_top_level_paths(
        self,
        sense_tree_normalizer: SenseTreeNormalizer,
    ) -> None:
        fragments = [
            RawSenseFragment("I.", "first"),
            RawSenseFragment("II.", "second"),
            RawSenseFragment("III.", "third"),
        ]
        senses = sense_tree_normalizer.normalize(fragments)
        assert [s.sense_path for s in senses] == ["1", "2", "3"]
        assert [s.parent_path for s in senses] == [None, None, None]
        assert [s.source_label_raw for s in senses] == ["I.", "II.", "III."]

    def test_iv_subletter_children(
        self,
        sense_tree_normalizer: SenseTreeNormalizer,
    ) -> None:
        fragments = [
            RawSenseFragment("I.", "first"),
            RawSenseFragment("II.", "second"),
            RawSenseFragment("IVa.", "child-a"),
            RawSenseFragment("IVc.", "child-c"),
        ]
        senses = sense_tree_normalizer.normalize(fragments)
        assert [s.sense_path for s in senses] == ["1", "2", "2.1", "2.3"]
        assert senses[2].source_label_raw == "IVa."
        assert senses[2].parent_path == "2"
        assert senses[3].parent_path == "2"
        assert all(s.warnings for s in senses[2:])

    def test_b_dot_i_style_children(
        self,
        sense_tree_normalizer: SenseTreeNormalizer,
    ) -> None:
        fragments = [
            RawSenseFragment("A.", "alpha"),
            RawSenseFragment("B.", "beta"),
            RawSenseFragment("B. I.", "beta-first"),
        ]
        senses = sense_tree_normalizer.normalize(fragments)
        assert [s.sense_path for s in senses] == ["1", "2", "2.1"]
        assert senses[2].source_label_raw == "B. I."
        assert senses[2].parent_path == "2"

    def test_out_of_order_numerals_use_encounter_order(
        self,
        sense_tree_normalizer: SenseTreeNormalizer,
    ) -> None:
        fragments = [
            RawSenseFragment("I.", "first"),
            RawSenseFragment("III.", "third"),
            RawSenseFragment("II.", "second"),
        ]
        senses = sense_tree_normalizer.normalize(fragments)
        assert [s.sense_path for s in senses] == ["1", "2", "3"]
        assert [s.source_label_raw for s in senses] == ["I.", "III.", "II."]

    def test_orphan_label_nearest_open_ancestor_fallback(
        self,
        sense_tree_normalizer: SenseTreeNormalizer,
    ) -> None:
        fragments = [
            RawSenseFragment("I.", "first"),
            RawSenseFragment("II a.", "orphan-child"),
        ]
        senses = sense_tree_normalizer.normalize(fragments)
        assert [s.sense_path for s in senses] == ["1", "1.1"]
        assert senses[1].parent_path == "1"
        assert senses[1].warnings


class TestSenseDisplayLabels:
    """Arabic display labels for canonical sense paths."""

    def test_format_sense_display_label_top_level(self) -> None:
        assert format_sense_display_label("1") == "1"
        assert format_sense_display_label("3") == "3"

    def test_format_sense_display_label_subsense_letters(self) -> None:
        assert format_sense_display_label("2.1") == "2a"
        assert format_sense_display_label("2.3") == "2c"
        assert format_sense_display_label("4.1") == "4a"

    def test_sense_path_sort_key_orders_subsenses_after_parent(self) -> None:
        paths = ["8", "4.1", "4", "5", "1", "10"]
        assert sorted(paths, key=sense_path_sort_key) == [
            "1",
            "4",
            "4.1",
            "5",
            "8",
            "10",
        ]

    def test_segmenter_display_label_uses_arabic_not_roman(
        self,
        segmenter: BTSenseSegmenter,
    ) -> None:
        body = (
            "<B>I.</B> <I>first</I> :-- one. "
            "<B>II.</B> <I>second</I> :-- two."
        )
        senses = segmenter.segment(body)
        assert [s.display_label for s in senses] == ["1", "2"]
        assert [s.sense_label for s in senses] == ["I", "II"]

    def test_unlabeled_single_sense_has_empty_display_label(
        self,
        segmenter: BTSenseSegmenter,
    ) -> None:
        senses = segmenter.segment("<I>only gloss</I> :-- one.")
        assert len(senses) == 1
        assert senses[0].display_label == ""
        assert senses[0].sense_path == "1"


class TestBTSenseSegmenterUnit:
    """Unit tests for specific segmenter behaviours."""

    def test_no_sense_labels_single_sense(self, segmenter: BTSenseSegmenter) -> None:
        """
        Body with no sense labels produces a single unlabelled sense.
        """
        body = "<B>aad</B> <I>a pile</I> :-- He mycelne aad gesomnode <I>he gathered a great pile,</I> Bd. 3, 16."
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].sense_path == "1"
        assert senses[0].sense_label == ""
        assert senses[0].gloss_en == "a pile"

    def test_bold_roman_numeral_two_senses(self, segmenter: BTSenseSegmenter) -> None:
        """
        Bold <B>I.</B>/<B>II.</B> labels produce two ordered senses.
        """
        body = (
            "<B>ā-barian.</B> <I>Add:</I> "
            "<B>I.</B> <I>to make bare, strip</I> :-- Stōwe rōde ābarude <I>locum cruce denudatum,</I> Angl. 427. "
            "<B>II.</B> <I>to lay bare, expose, disclose:</I>-- Ælfremeda wunda nā ābarian, R. Ben. I. 80, 12."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 2
        assert [s.sense_path for s in senses] == ["1", "2"]
        assert senses[0].sense_label == "I"
        assert senses[0].gloss_en == "to make bare, strip"
        assert senses[1].sense_label == "II"
        assert senses[1].gloss_en == "to lay bare, expose, disclose"

    def test_bold_period_outside_tag(self, segmenter: BTSenseSegmenter) -> None:
        """
        <B>I</B>. (period outside bold tag) is recognised as a sense label.
        """
        body = (
            "<B>ā-beran</B>. <I>Add:</I> "
            "<B>I</B>. with sense of movement, (1) <I>to bear off, bring, carry</I> :-- Se hwæl hine ābær. "
            "<B>II</B>. with sense of rest (metaph.). (1) <I>to bear with, tolerate</I> :-- Seō cyrice."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 2
        assert senses[0].sense_label == "I"
        assert senses[1].sense_label == "II"

    def test_plain_roman_numeral_labels(self, segmenter: BTSenseSegmenter) -> None:
        """
        Plain (unbolded) Roman-numeral labels followed by an italic span are split correctly.
        """
        body = (
            "<B>a-bannan;</B> <I>p.</I> -beōnn, <I>pl.</I> -beōnnon; <I>pp.</I> -bannen. "
            "I. <I>to command, order, summon;</I> mandare, jubere :-- Abannan to beadwe, Elen. 34. "
            "II. <I>to publish, proclaim; with</I> ūt <I>to order out, call forth;</I> edicere :-- Aban ðū."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 2
        assert senses[0].sense_label == "I"
        assert "to command, order, summon" in senses[0].gloss_en
        assert senses[1].sense_label == "II"
        assert "to publish, proclaim" in senses[1].gloss_en

    def test_three_bold_senses(self, segmenter: BTSenseSegmenter) -> None:
        """
        Three bold sense labels I., II., III. all produce senses in order.
        """
        body = (
            "<B>ā-bǣdan.</B> <I>Substitute the following:</I> "
            "<B>I.</B> <I>to force, wring</I> :-- Ele ābǣdan and āwringan, Gr. D. 250, 22. "
            "<B>II.</B> <I>to compel</I>:-- Gif ðæt nȳd ābǣdeþ<I>cum exhiberi,</I> Bd. l, 27. "
            "<B>III.</B> <I>to demand, require.</I> (l) where needed :-- Nāniges fultumes ābǣdeþ."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 3
        assert senses[0].gloss_en == "to force, wring"
        assert senses[1].gloss_en == "to compel"
        assert senses[2].gloss_en == "to demand, require"

    def test_sub_letter_sense_label(self, segmenter: BTSenseSegmenter) -> None:
        """
        <B>II a.</B> sub-letter label is captured and stripped of period.
        """
        body = (
            "<B>headword</B> "
            "<B>II a.</B> <I>of continuity in space</I> :-- Wæs ðæt land genemnad. "
            "<B>II b.</B> <I>of continuous increase</I> :-- Sceal him ðanan."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 2
        assert senses[0].sense_label == "II a"
        assert senses[1].sense_label == "II b"

    def test_letter_sense_label(self, segmenter: BTSenseSegmenter) -> None:
        """
        <B>A.</B> / <B>B.</B> capital-letter labels are supported.
        """
        body = (
            "<B>ā (ō);</B> <I>adv. Ever. Add:</I> "
            "<B>A.</B> <I>always;</I> semper. "
            "<B>B.</B> <I>at any time;</I> unquam."
        )
        senses = segmenter.segment(body)
        labels = [s.sense_label for s in senses]
        assert "A" in labels
        assert "B" in labels

    def test_add_only_body_returns_empty(self, segmenter: BTSenseSegmenter) -> None:
        """
        An editorial Add-only body with no English gloss returns an empty list.
        """
        body = "<B>ā-beatan.</B> <I>Add:</I>-- Ic ðē ðīne tēþ of ābeāte, Lch. i. 326, 15."
        senses = segmenter.segment(body)
        assert senses == []

    def test_crossref_body_returns_empty(self, segmenter: BTSenseSegmenter) -> None:
        """
        A cross-reference-only body produces no senses.
        """
        body = "<B>ā-beofian</B>. v. ā-bifian."
        senses = segmenter.segment(body)
        assert senses == []

    def test_bracket_etymology_stripped(self, segmenter: BTSenseSegmenter) -> None:
        """
        Bracket etymology blocks are stripped before gloss extraction.
        """
        body = (
            "<B>abbadisse,</B> an; <I>f.</I> "
            "[abbad <I>an abbot,</I> isse <I>a female</I> termination, <I>q. v.</I>] "
            "<I>An abbess;</I> abbatissa :-- Riht is ðæt abbadissan fæste."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].gloss_en == "An abbess"

    def test_sense_order_preserved(self, segmenter: BTSenseSegmenter) -> None:
        """
        Senses are returned in document order.
        """
        body = (
            "<B>a-beran;</B> <I>p.</I> -bær; <I>pp.</I> -boren. "
            "I. <I>to bear, carry, suffer;</I> portare, ferre :-- man aberan ne mæg, Mt. 23. "
            "II. <I>to take or carry away;</I> tollere, auferre :-- Abær hine, Ps. 77."
        )
        senses = segmenter.segment(body)
        assert [s.sense_label for s in senses] == ["I", "II"]
        assert "bear, carry, suffer" in senses[0].gloss_en
        assert "take or carry away" in senses[1].gloss_en

    def test_segment_parsed_line_returns_tuple(self, segmenter: BTSenseSegmenter) -> None:
        """
        ``segment_parsed_line`` returns a tuple suitable for ``ParsedBTLine.senses``.
        """
        body = "<B>aad</B> <I>a pile</I> :-- He mycelne aad gesomnode, Bd. 3, 16."
        result = segmenter.segment_parsed_line(body)
        assert isinstance(result.senses, tuple)
        assert len(result.senses) == 1
        assert isinstance(result.senses[0], BTSense)


class TestSenseMetadataClassifier:
    """Unit tests for sense-prefix metadata classification."""

    @pytest.fixture(scope="module")
    def classifier(self) -> SenseMetadataClassifier:
        return SenseMetadataClassifier()

    def test_ef_feminine_gloss(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify("<I>e;f. An offence, wrong, anger;</I>")
        assert metadata.grammatical_context == ("feminine",)
        assert metadata.modifiers == ()
        assert "An offence, wrong, anger" in metadata.remainder

    def test_es_m_masculine(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify("<I>es; m. An apple;</I>")
        assert metadata.grammatical_context == ("masculine",)

    def test_nom_acc_and_genitive(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify("<I>nom. acc; g.</I>")
        assert metadata.grammatical_context == (
            "nominative",
            "accusative",
            "genitive",
        )

    def test_dative_case(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify("<I>dat. To a guest;</I>")
        assert metadata.grammatical_context == ("dative",)

    def test_participle_modifier(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify("<I>part. blessing;</I>")
        assert metadata.modifiers == ("participle",)

    def test_indeclinable_modifier(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify("<I>indecl; f. A law;</I>")
        assert metadata.modifiers == ("indeclinable",)
        assert metadata.grammatical_context == ("feminine",)

    def test_usage_note_with_dative_of_person(
        self,
        classifier: SenseMetadataClassifier,
    ) -> None:
        metadata = classifier.classify(
            "(2) with dat. of person from whom one hides :-- <I>He hid</I>"
        )
        assert metadata.usage_note == "with dative of person"

    def test_usage_note_in_the_phrase(self, classifier: SenseMetadataClassifier) -> None:
        metadata = classifier.classify(
            "only in the phrase <I>on æle-middan</I>=just in the middle"
        )
        assert metadata.usage_note == "in the phrase"

    def test_usage_note_ecclesiastical_term(
        self,
        classifier: SenseMetadataClassifier,
    ) -> None:
        metadata = classifier.classify(
            "as an ecclesiastical term, <I>to excommunicate:--</I>"
        )
        assert metadata.usage_note == "as ecclesiastical term"

    def test_intransitive_leading_modifier(
        self,
        classifier: SenseMetadataClassifier,
    ) -> None:
        metadata = classifier.classify("<I>intrans. To break</I>")
        assert metadata.modifiers == ("intransitive",)
        assert metadata.remainder == "<I>To break</I>"

    def test_intransitive_trailing_modifier(
        self,
        classifier: SenseMetadataClassifier,
    ) -> None:
        metadata = classifier.classify("<I>To break, intrans.</I>")
        assert metadata.modifiers == ("intransitive",)
        assert metadata.remainder == "<I>To break</I>"

    def test_bare_intransitive_prefix_only(
        self,
        classifier: SenseMetadataClassifier,
    ) -> None:
        metadata = classifier.classify("<I>intrans.</I>")
        assert metadata.modifiers == ("intransitive",)
        assert metadata.warnings == ("prefix_only_no_gloss",)


class TestSensePrefixSegmentation:
    """Integration tests for prefix metadata on segmented senses."""

    def test_abylgp_feminine_gloss(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>a-bylgp,</B> -bilgþ, -bilhþ, <I>e;f. An offence, wrong, anger;</I>"
            " offensa, injuria, ira :-- He sceal Cristes abilgþe wrecan"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        sense = senses[0]
        assert sense.grammatical_context == ("feminine",)
        assert sense.gloss_en == "An offence, wrong, anger"
        assert sense.prefix_fragment_raw
        assert sense.source_fragment_raw
        assert sense.source_label_raw == ""

    def test_abeornan_intransitive_gloss(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>a-beornan;</B> <I>p.</I> -bearn, -barn, <I>pl.</I> -burnon;"
            " <I>pp.</I> -bornen, <I>v. intrans. To bvrn;</I> exardere :-- Fyr abarn"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].modifiers == ("intransitive",)
        assert senses[0].gloss_en == "To bvrn"

    def test_adfaer_case_context_and_neuter_gloss(
        self,
        segmenter: BTSenseSegmenter,
    ) -> None:
        body = (
            "<B>ād-fær,</B> <I>nom. acc; g.</I> -færes; <I>pl. nom.</I> -faru;"
            " <I>n. The pile-way, the way to the funeral pile;</I> iter rogi :--"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].grammatical_context == (
            "nominative",
            "accusative",
            "genitive",
            "neuter",
        )
        assert senses[0].gloss_en == "The pile-way, the way to the funeral pile"

    def test_a_law_indeclinable_feminine(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>ā,</B> <I>indecl; f. A law;</I> lex :-- Dryhtnes ā"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].modifiers == ("indeclinable",)
        assert senses[0].grammatical_context == ("feminine",)
        assert senses[0].gloss_en == "A law"

    def test_ecclesiastical_usage_note_sense(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>ā-mānsumian.</B> <I>Dele bracket and add:</I>"
            " <B>II.</B> as an ecclesiastical term, <I>to excommunicate:--</I>"
            " Gif gē ne dōð, ic eōw āmānsumige"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].usage_note == "as ecclesiastical term"
        assert senses[0].gloss_en == "to excommunicate"
        assert senses[0].sense_label == "II"

    def test_in_the_phrase_usage_note(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>æle-midde,</B> an; <I>f. The exact middle;</I> only in the phrase"
            " <I>on æle-middan</I>=just in the middle:-- Seō eorðe stent"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].usage_note == "in the phrase"
        assert senses[0].gloss_en == "The exact middle"

    def test_with_dative_of_person_sense(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>æt-lutian.</B> <I>Add;</I> (2) with dat. of person from whom one hides,"
            " <I>to hide from</I> :-- Hē ætludode his ēhterum"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].usage_note == "with dative of person"
        assert senses[0].gloss_en == "to hide from"

    def test_bare_intransitive_produces_no_sense(
        self,
        segmenter: BTSenseSegmenter,
    ) -> None:
        body = "<B>sample.</B> <I>intrans.</I> :-- OE attestation here"
        senses = segmenter.segment(body)
        assert senses == []

    def test_trailing_intransitive_attached_locally(
        self,
        segmenter: BTSenseSegmenter,
    ) -> None:
        body = (
            "<B>sample.</B> <B>I.</B> <I>To break, intrans.</I> :-- OE text"
            " <B>II.</B> <I>To mend</I> :-- more OE"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 2
        assert senses[0].modifiers == ("intransitive",)
        assert senses[0].gloss_en == "To break"
        assert senses[1].modifiers == ()


class TestCorpusWeirdSenses:
    """Corpus-driven regression tests for odd Bosworth-Toller sense prefixes."""

    _ADLOMA_BODY = (
        "<B>ād-loma,</B> -lama? an; <I>m. One crippled by the flame?</I>"
        " cui flamma claudicationem attulit? -- Earme ādloman"
        " <I>poor wretches, i.e.</I> diaboli, Exon. 46a; Th. 156, 33; Gū. 884."
    )

    def test_aam_es_m_masculine_cleanup(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>aam,</B> es; <I>m. A reed of a weaver's loom.</I>"
            " Exon. 109 a; Th. 417, 22 ; Rä. 36, 8; Cod. Lugd. Grn. v. ām."
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].grammatical_context == ("masculine",)
        assert senses[0].gloss_en == "A reed of a weaver's loom"

    def test_blinnan_participle_modifier(self, segmenter: BTSenseSegmenter) -> None:
        body = (
            "<B>blinnan;</B> <I>part.</I> blinnende; ic blinne, ðū blinnest, blinst,"
            " he blinneþ, blinniþ, blinþ, <I>pl.</I> blinnaþ; <I>p.</I> ic, he blan,"
            " blon, blann, blonn, ðū blunne, <I>pl.</I> blunnon; <I>pp.</I> blunnen;"
            " <I>v. intrans.</I> [be, linnan <I>to cease</I>]"
            " <I>To cease, rest, leave off;</I> cessare, desinere"
        )
        senses = segmenter.segment(body)
        assert len(senses) == 1
        assert senses[0].modifiers == ("participle",)
        assert senses[0].gloss_en == "To cease, rest, leave off"

    def test_adloma_dependency_tail_parse_failure(
        self,
        segmenter: BTSenseSegmenter,
    ) -> None:
        """
        Attestation gloss after ``:--`` bleeds into ``gloss_en`` when tagged italic.

        Regression lock for oe_bt.txt adloma (line 491): ``poor wretches, i.e.``
        should ideally be stripped but currently remains on the gloss tail.
        """
        senses = segmenter.segment(self._ADLOMA_BODY)
        assert len(senses) == 1
        assert senses[0].gloss_en == "One crippled by the flame?; poor wretches, i.e"


class TestEntryGenderPromotion:
    """Unit tests for sense-level gender promotion (Task 5 deferral hook)."""

    def test_promote_single_feminine_context(self) -> None:
        sense = BTSense(
            gloss_en="An offence, wrong, anger",
            sense_path="1",
            parent_path=None,
            source_label_raw="",
            source_fragment_raw="raw",
            prefix_fragment_raw="e;f.",
            modifiers=(),
            grammatical_context=("feminine",),
            usage_note="",
        )
        promoted = promote_entry_gender_from_senses((), (sense,))
        assert promoted == (BTGender.F,)

    def test_no_promotion_when_entry_gender_present(self) -> None:
        sense = BTSense(
            gloss_en="An offence, wrong, anger",
            sense_path="1",
            parent_path=None,
            source_label_raw="",
            source_fragment_raw="raw",
            prefix_fragment_raw="e;f.",
            modifiers=(),
            grammatical_context=("feminine",),
            usage_note="",
        )
        promoted = promote_entry_gender_from_senses((BTGender.M,), (sense,))
        assert promoted == (BTGender.M,)

    def test_no_promotion_with_multiple_senses(self) -> None:
        sense_a = BTSense(
            gloss_en="first",
            sense_path="1",
            parent_path=None,
            source_label_raw="I",
            source_fragment_raw="raw-a",
            prefix_fragment_raw="",
            modifiers=(),
            grammatical_context=("feminine",),
            usage_note="",
        )
        sense_b = BTSense(
            gloss_en="second",
            sense_path="2",
            parent_path=None,
            source_label_raw="II",
            source_fragment_raw="raw-b",
            prefix_fragment_raw="",
            modifiers=(),
            grammatical_context=("masculine",),
            usage_note="",
        )
        promoted = promote_entry_gender_from_senses((), (sense_a, sense_b))
        assert promoted == ()


class TestGoldenSenses:
    """Golden-file acceptance tests: ≥95% exact gloss match required."""

    @pytest.fixture(scope="class")
    def golden_data(self) -> list[dict]:  # type: ignore[type-arg]
        return _load_golden()

    @pytest.fixture(scope="class")
    def seg(self) -> BTSenseSegmenter:
        return BTSenseSegmenter()

    def test_golden_pass_rate(
        self,
        seg: BTSenseSegmenter,
        golden_data: list[dict],  # type: ignore[type-arg]
    ) -> None:
        """
        At least 95 % of golden entries must match exactly on sense count and gloss text.
        """
        total = len(golden_data)
        assert total >= 40, f"Golden file too small: {total} entries"
        passed = 0
        failures: list[str] = []

        for entry in golden_data:
            entry_id = entry["id"]
            body = entry["input_body"]
            expected = entry["expected_senses"]
            actual = seg.segment(body)
            if len(actual) != len(expected):
                failures.append(
                    f"FAIL [{entry_id}]: got {len(actual)} senses, "
                    f"expected {len(expected)}"
                )
                continue
            matched = all(
                _golden_sense_matches(
                    act,
                    label=exp["label"],
                    gloss_en=exp["gloss_en"],
                )
                for act, exp in zip(actual, expected, strict=True)
            )
            if matched:
                passed += 1
            else:
                failures.append(
                    f"FAIL [{entry_id}]: got {actual!r}, expected {expected!r}"
                )

        pass_rate = passed / total
        failure_summary = "\n".join(failures[:10])
        assert pass_rate >= _MIN_GOLDEN_PASS_RATE, (
            f"Golden pass rate {pass_rate:.1%} < 95% ({passed}/{total} passed)\n"
            f"First failures:\n{failure_summary}"
        )

    def test_no_oe_in_attestation_heavy_glosses(
        self,
        seg: BTSenseSegmenter,
        golden_data: list[dict],  # type: ignore[type-arg]
    ) -> None:
        """
        Attestation-heavy entries must not leave OE text in the gloss.
        """
        oe_chars_re = re.compile(r"[āēīōūǣæÆÐðÞþĀĒĪŌŪǢ]")
        attestation_heavy_ids = {"abbad-twosenses-plain", "abannan-plain-twosenses", "aberan-plain-twosenses"}

        for entry in golden_data:
            if entry["id"] not in attestation_heavy_ids:
                continue
            body = entry["input_body"]
            senses = seg.segment(body)
            for sense in senses:
                assert not oe_chars_re.search(sense.gloss_en), (
                    f"OE character found in gloss for [{entry['id']}]: {sense.gloss_en!r}"
                )
