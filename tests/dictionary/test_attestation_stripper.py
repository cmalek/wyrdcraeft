"""Tests for Phase 03 BTAttestationStripper."""

from __future__ import annotations

import re

import pytest

from wyrdcraeft.services.dictionary.attestation_stripper import (
    BTAttestationStripper,
    _contains_oe_chars,
    _is_citation_span,
    _is_editorial_marker,
    _is_grammatical_abbrev,
    _strip_editorial_directive,
    _strip_leading_gram_prefix,
)

_OE_CHARS_RE = re.compile(r"[āēīōūǣæÆÐðÞþĀĒĪŌŪǢ]")


@pytest.fixture(scope="module")
def stripper() -> BTAttestationStripper:
    return BTAttestationStripper()


class TestHelpers:
    """Unit tests for module-level helper functions."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("m.", True),
            ("f.", True),
            ("n.", True),
            ("adj.", True),
            ("adv.", True),
            ("p.", True),
            ("pp.", True),
            ("pl.", True),
            ("v. trans.", True),
            ("v. a.", True),
            ("sg.", True),
            ("dat.", True),
            # not abbreviations
            ("an abbot", False),
            ("to bake", False),
            ("f. An oak", False),  # combined gender+gloss
        ],
    )
    def test_is_grammatical_abbrev(self, text: str, expected: bool) -> None:
        """
        ``_is_grammatical_abbrev`` distinguishes grammar markers from glosses.
        """
        assert _is_grammatical_abbrev(text) == expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Add", True),
            ("add", True),
            ("Substitute", True),
            ("dele", True),
            ("Omit", True),
            # not editorial
            ("an abbot", False),
            ("to bake", False),
        ],
    )
    def test_is_editorial_marker(self, text: str, expected: bool) -> None:
        """
        ``_is_editorial_marker`` detects supplement editorial directives.
        """
        assert _is_editorial_marker(text) == expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("āban and wordum", True),
            ("ǣlces cynnes", True),
            ("a pile", False),
            ("An abbot", False),
        ],
    )
    def test_contains_oe_chars(self, text: str, expected: bool) -> None:
        """
        ``_contains_oe_chars`` detects OE-specific Unicode codepoints.
        """
        assert _contains_oe_chars(text) == expected

    @pytest.mark.parametrize(
        ("text", "citation_expected"),
        [
            ("m.", True),
            ("Add", True),
            ("add:", True),
            ("v. l.", True),  # short all-lowercase abbrev
            ("an abbot", False),
            ("to bake", False),
            ("honour", False),
        ],
    )
    def test_is_citation_span(self, text: str, citation_expected: bool) -> None:
        """
        ``_is_citation_span`` returns True for grammar/editorial markers and citations.
        """
        assert _is_citation_span(text) == citation_expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("f. An oak", "An oak"),
            ("m. An abbot", "An abbot"),
            ("n. Power of body, strength", "Power of body, strength"),
            ("adj. Bending", "Bending"),
            ("v. trans. To bend", "To bend"),
            ("adv. Ever", "Ever"),
            # no prefix → unchanged
            ("To bake", "To bake"),
            ("an abbot", "an abbot"),
        ],
    )
    def test_strip_leading_gram_prefix(self, text: str, expected: str) -> None:
        """
        ``_strip_leading_gram_prefix`` removes leading gender/POS prefixes.
        """
        assert _strip_leading_gram_prefix(text) == expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Substitute: A property", "A property"),
            ("Add: some new sense", "some new sense"),
            ("Dele.", ""),
            # no directive → unchanged
            ("to bake", "to bake"),
            ("an abbot", "an abbot"),
        ],
    )
    def test_strip_editorial_directive(self, text: str, expected: str) -> None:
        """
        ``_strip_editorial_directive`` removes leading supplement editorial verbs.
        """
        assert _strip_editorial_directive(text) == expected


class TestBTAttestationStripperUnit:
    """Unit tests for BTAttestationStripper.strip."""

    def test_simple_gloss_with_colon_dash_separator(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        ``:--`` is the canonical attestation separator.
        """
        body = "<B>aad</B> <I>a pile</I> :-- He mycelne aad gesomnode <I>he gathered a great pile,</I> Bd. 3, 16."
        assert stripper.strip(body) == "a pile"

    def test_gender_gloss_combined_span(self, stripper: BTAttestationStripper) -> None:
        """
        Combined gender-gloss italic spans like ``<I>f. An oak:</I>`` yield clean glosses.
        """
        body = "<B>aac,</B> e; <I>f. An oak:</I> -- Aac-tūn <I>Acton Beauchamp,</I> Kmbl. i. 90, 19."
        gloss = stripper.strip(body)
        assert gloss == "An oak"

    def test_secondary_separator_italic_ends_colon(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        ``</I>--`` (colon inside italic) is handled as the attestation separator.
        """
        body = "<B>a-bacan</B> <I>to bake:</I>-- Nim ǣlces cynnes melo and ābacæ man hlāf."
        gloss = stripper.strip(body)
        assert gloss == "to bake"

    def test_grammatical_abbrevs_filtered(self, stripper: BTAttestationStripper) -> None:
        """
        Grammar markers like ``<I>p.</I>`` and ``<I>pp.</I>`` are removed from the gloss.
        """
        body = (
            "<B>a-bacan,</B> ic -bace, <I>pl.</I> -bacaþ; <I>p.</I> -bōc, <I>pl.</I> -bōcon; "
            "<I>pp.</I> -bacen <I>To bake;</I> pinsere, coquere :-- Se hlāf."
        )
        gloss = stripper.strip(body)
        assert gloss == "To bake"
        assert "pl" not in gloss.lower()
        assert "pp" not in gloss.lower()

    def test_bracket_etymology_removed(self, stripper: BTAttestationStripper) -> None:
        """
        ``[…]`` bracket blocks are stripped before gloss extraction.
        """
        body = (
            "<B>abbadisse,</B> an; <I>f.</I> "
            "[abbad <I>an abbot,</I> isse <I>a female</I> termination, <I>q. v.</I>] "
            "<I>An abbess;</I> abbatissa :-- Riht is ðæt abbadissan fæste."
        )
        gloss = stripper.strip(body)
        assert gloss == "An abbess"
        assert "an abbot" not in gloss.lower()

    def test_editorial_add_only_returns_empty(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        An ``<I>Add:</I>`` span with no following gloss produces an empty string.
        """
        body = "<B>ā-beatan.</B> <I>Add:</I>-- Ic ðē ðīne tēþ of ābeāte, Lch. i. 326, 15."
        gloss = stripper.strip(body)
        assert gloss == ""

    def test_substitute_directive_stripped_from_gloss(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        ``Substitute:`` editorial prefix is removed from the kept gloss span.
        """
        body = "<B>agenness.</B> <I>Substitute: A property</I> :-- Seō sunne hæfd dreō."
        gloss = stripper.strip(body)
        assert gloss == "A property"

    def test_no_oe_chars_in_gloss_after_stripping(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        OE text in citation spans does not leak into the English gloss.
        """
        body = (
            "<B>abbod,</B> es; <I>m:</I> abboda, an; <I>m.</I> I. "
            "<I>an abbot;</I> abbās :-- Se ārwurða abbad Albīnus <I>the reverend abbot Albinus,</I> Bd. pref."
        )
        gloss = stripper.strip(body)
        assert gloss == "an abbot"
        assert not _OE_CHARS_RE.search(gloss), f"OE chars in gloss: {gloss!r}"

    def test_multiple_gloss_spans_joined(self, stripper: BTAttestationStripper) -> None:
        """
        Multiple English italic spans (e.g. split around OE connector) are joined with ``;``.
        """
        body = (
            "II. <I>to publish, proclaim; with</I> ūt <I>to order out, call forth;</I> edicere :-- text."
        )
        gloss = stripper.strip(body)
        assert "to publish, proclaim" in gloss
        assert "to order out" in gloss

    def test_crossref_body_returns_empty(self, stripper: BTAttestationStripper) -> None:
        """
        Cross-reference bodies with no italic content return an empty string.
        """
        body = "<B>ā-beofian</B>. v. ā-bifian."
        gloss = stripper.strip(body)
        assert gloss == ""

    def test_n_gender_gloss_combined(self, stripper: BTAttestationStripper) -> None:
        """
        Combined ``<I>n. English gloss;</I>`` spans strip the ``n.`` prefix.
        """
        body = "<B>ABAL,</B> afol, es; <I>n. Power of body, strength;</I> vigor :-- Ðīn abal."
        gloss = stripper.strip(body)
        assert gloss == "Power of body, strength"

    def test_pp_of_filtered_as_short_abbrev(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        ``<I>pp. of</I>`` is treated as a short abbreviation and filtered.
        """
        body = "<B>a-bēag</B> <I>bowed down,</I> Beo. Th. 1555; B. 775; <I>p. of</I> a-būgan."
        gloss = stripper.strip(body)
        assert gloss == "bowed down"
        assert "of" not in gloss or gloss.count("of") == 0

    def test_no_separator_retains_full_gloss(
        self, stripper: BTAttestationStripper
    ) -> None:
        """
        Entries with no attestation separator keep all italic gloss content.
        """
        body = "<B>abbud</B> <I>an abbot.</I> Chr. 803; Erl. 60, 13: Bd. 5, 23. v. abbad."
        gloss = stripper.strip(body)
        assert gloss == "an abbot"
