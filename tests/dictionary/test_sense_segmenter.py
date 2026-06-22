"""Tests for Phase 03 BTSenseSegmenter."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from wyrdcraeft.models.dictionary import BTSense
from wyrdcraeft.services.dictionary.sense_segmenter import BTSenseSegmenter

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


class TestBTSenseSegmenterUnit:
    """Unit tests for specific segmenter behaviours."""

    def test_no_sense_labels_single_sense(self, segmenter: BTSenseSegmenter) -> None:
        """
        Body with no sense labels produces a single unlabelled sense.
        """
        body = "<B>aad</B> <I>a pile</I> :-- He mycelne aad gesomnode <I>he gathered a great pile,</I> Bd. 3, 16."
        senses = segmenter.segment(body)
        assert len(senses) == 1
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
        assert isinstance(result, tuple)
        assert len(result) == 1
        assert isinstance(result[0], BTSense)


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
            expected = [
                BTSense(sense_label=s["label"], gloss_en=s["gloss_en"])
                for s in entry["expected_senses"]
            ]
            actual = seg.segment(body)
            if actual == expected:
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
