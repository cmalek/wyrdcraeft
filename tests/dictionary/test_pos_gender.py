"""Tests for BTPosGenderExtractor using real oe_bt.txt prefix fragments."""

from __future__ import annotations

import pytest

from wyrdcraeft.models.dictionary import BTGender, BTPos
from wyrdcraeft.services.dictionary.pos_gender import BTPosGenderExtractor


@pytest.fixture
def extractor() -> BTPosGenderExtractor:
    """Shared extractor instance."""
    return BTPosGenderExtractor()


@pytest.mark.parametrize(
    ("fragment", "expected_pos", "expected_genders"),
    [
        # Nouns with single gender (real oe_bt.txt fragments)
        ("es; <I>m. A reed of a weaver's loom.</I>", BTPos.NOUN, (BTGender.M,)),
        ("e; <I>f. An oak:</I>", BTPos.NOUN, (BTGender.F,)),
        ("es; <I>n. Power of body, strength;</I>", BTPos.NOUN, (BTGender.N,)),
        (
            "abbod, abbud, abbot, es; <I>m:</I> abboda, an; <I>m. An abbot;</I>",
            BTPos.NOUN,
            (BTGender.M,),
        ),
        ("an; <I>f. An abbess;</I>", BTPos.NOUN, (BTGender.F,)),
        ("an; <I>m. An abbot;</I>", BTPos.NOUN, (BTGender.M,)),
        (
            "es; <I>m. The state</I> or <I>dignity of an abbot;</I>",
            BTPos.NOUN,
            (BTGender.M,),
        ),
        ("es; <I>m.</I> [ācan == ācum.", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. An oak-tree;</I>", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. Accent</I>", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. Oak-drink,", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. A parent</I>", BTPos.NOUN, (BTGender.M,)),
        ("an; <I>m. An oak wood on a slope</I>", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. An oak wood</I>", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m.</I> [ac-lǣc = ag-lǣc", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. An oak-twig:--</I>", BTPos.NOUN, (BTGender.M,)),
        ("a; <I>m. An oak wood:--</I>", BTPos.NOUN, (BTGender.M,)),
        ("aad, es; <I>m. A funeral pile,", BTPos.NOUN, (BTGender.M,)),
        ("an; <I>m. Filth;</I>", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. A sewer, gutter, sink;</I>", BTPos.NOUN, (BTGender.M,)),
        ("an; <I>m. An addice</I> or <I>adze,", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. The flame of the funeral pile;</I>", BTPos.NOUN, (BTGender.M,)),
        ("an; <I>m. One crippled by the flame?</I>", BTPos.NOUN, (BTGender.M,)),
        ("es; <I>m. A business;</I>", BTPos.NOUN, (BTGender.M,)),
        ("an; <I>m. A messenger of the law;</I>", BTPos.NOUN, (BTGender.M,)),
        ("an; <I>m. An adulterer;</I>", BTPos.NOUN, (BTGender.M,)),
        # Multi-gender nouns
        (
            "an; <I>m. and f. A mate, an equal, companion;</I>",
            BTPos.NOUN,
            (BTGender.M, BTGender.F),
        ),
        (
            "an; <I>m. and f. A companion, mate, consort,",
            BTPos.NOUN,
            (BTGender.M, BTGender.F),
        ),
        (
            "an; <I>m. and f. A consort, an equal</I>",
            BTPos.NOUN,
            (BTGender.M, BTGender.F),
        ),
        (
            "an; <I>m. or f. A link, a chain of links,",
            BTPos.NOUN,
            (BTGender.M, BTGender.F),
        ),
        (
            "an; <I>m. or f. The top of the head</I>",
            BTPos.NOUN,
            (BTGender.M, BTGender.F),
        ),
        # Verbs (paradigm lines)
        (
            "ic -bace, ðū -bæcest, -bæcst, he -bæceþ, -bæcþ, <I>pl.</I> -bacaþ; "
            "<I>p.</I> -bōc, <I>pl.</I> -bōcon; <I>pp.</I> -bacen <I>To bake;</I>",
            BTPos.VERB,
            (),
        ),
        (
            "<I>p.</I> -bǣdde; <I>pp.</I> -bǣded <I>To restrain, repel, compel;</I>",
            BTPos.VERB,
            (),
        ),
        (
            "<I>p.</I> ode; <I>pp.</I> od <I>To offend, to make angry;</I>",
            BTPos.VERB,
            (),
        ),
        (
            "<I>p.</I> -beōnn, <I>pl.</I> -beōnnon ; <I>pp.</I> -bannen. I. "
            "<I>to command, order, summon;</I>",
            BTPos.VERB,
            (),
        ),
        (
            "<I>. p.</I> ede; <I>pp.</I> ed [a, barian <I>to make bare;</I> "
            "bær, se bara; <I>adj.</I> <I>bare</I>] <I>To make bare,</I>",
            BTPos.VERB,
            (),
        ),
        (
            "<I>p.</I> -beāg, -beāh, <I>pl.</I> -bugon; <I>pp.</I> -bogen "
            "<I>To iow, bend, incline,</I>",
            BTPos.VERB,
            (),
        ),
        # Adjectives
        ("<I>adj. Bending;</I>", BTPos.ADJ, ()),
        ("<I>adj. Sagacious, crafty, cunning;</I>", BTPos.ADJ, ()),
        ("<I>adj.</I> <B>I</B>. <I>inspired</I>", BTPos.ADJ, ()),
        ("<I>adj. Ulcerated</I>", BTPos.ADJ, ()),
        ("<I>adj. Blinded;</I>", BTPos.ADJ, ()),
        ("<I>adj. Brought to light</I>", BTPos.ADJ, ()),
        ("<I>adj. Clear and evident by proof,", BTPos.ADJ, ()),
        ("<I>adj. Pallid, pale, livid:--</I>", BTPos.ADJ, ()),
        ("<I>adj. Eternal;</I>", BTPos.ADJ, ()),
        ("<I>adj. Oak-whole</I> or <I>sound, entire;</I>", BTPos.ADJ, ()),
        # Adverbs
        ("aa, aaa; <I>adv. Always, ever, for ever;</I>", BTPos.ADV, ()),
        ("<I>adv. Ever.</I>", BTPos.ADV, ()),
        ("<I>adv. Early:--</I>", BTPos.ADV, ()),
        # Prepositions
        ("<I>prep. acc. To, for;</I>", BTPos.PREP, ()),
        ("<I>prep. Omit:</I>", BTPos.PREP, ()),
        ("<I>prep. dat. Between;</I>", BTPos.PREP, ()),
        ("<I>prep. dat.</I> marking (1) position :--", BTPos.PREP, ()),
        ("<I>prep. dat.</I> [æt <I>at,</I> foran <I>fore</I>]", BTPos.PREP, ()),
        ("<I>prep. Towards;</I>", BTPos.PREP, ()),
        ("<I>prep. acc. Against;</I>", BTPos.PREP, ()),
        ("of: <I>prep. Of, from:</I>", BTPos.PREP, ()),
        ("<I>prep.</I> [æft, <I>q. v;</I> er, <I>q.v.</I>]", BTPos.PREP, ()),
        ("<I>prep. Add:</I>", BTPos.PREP, ()),
        # Conjunctions
        ("ach, ah, oc; <I>conj.</I> X. <I>but;</I>", BTPos.CONJ, ()),
        ("<I>conj.</I> ERE, <I>before that;</I>", BTPos.CONJ, ()),
        ("<I>conj. Add:</I>", BTPos.CONJ, ()),
        ("<I>conj.</I> AND;", BTPos.CONJ, ()),
        ("<I>conj. Unless;</I>", BTPos.CONJ, ()),
        ("<I>conj.</I> [be, ūtan <I>out</I>].", BTPos.CONJ, ()),
        # Indeclinables
        ("<I>indecl; f. A law;</I>", BTPos.INDECL, (BTGender.F,)),
        ("<I>indecl. f. Law, statute, custom,", BTPos.INDECL, (BTGender.F,)),
        ("<I>indecl. f. Life;</I>", BTPos.INDECL, (BTGender.F,)),
        ("<I>indecl. f. A river, stream;</I>", BTPos.INDECL, (BTGender.F,)),
        ("<I>indecl. in sing, but sometimes gen.</I>", BTPos.INDECL, ()),
        ("<I>indecl. in sing; pl. nom. acc.</I>", BTPos.INDECL, ()),
        ("<I>indecl:</I> but Lat.", BTPos.INDECL, ()),
        # Interjections
        ("<I>interj. O! alas!</I>", BTPos.INTERJ, ()),
        ("<I>interj. Behold ;</I>", BTPos.INTERJ, ()),
        ("<I>interj. O certainly! O assuredly!</I>", BTPos.INTERJ, ()),
        ("<I>interj. 0! alas! Oh!</I>", BTPos.INTERJ, ()),
        # Pronouns
        ("<I>pron.</I> [ā + ge + hwæðer]. I. of two,", BTPos.PRON, ()),
        ("<I>pron. Either, each, both;</I>", BTPos.PRON, ()),
        ("<I>pron. Each;</I>", BTPos.PRON, ()),
        ("<I>pron.</I> [ā, hwā <I>who</I>]", BTPos.PRON, ()),
        # Unknown / empty
        ("", BTPos.UNKNOWN, ()),
        ("   ", BTPos.UNKNOWN, ()),
        ("<I>to bake:</I>", BTPos.UNKNOWN, ()),
        ("DER. abbad-dōm, -hād,", BTPos.UNKNOWN, ()),
    ],
)
def test_extract_pos_gender(
    extractor: BTPosGenderExtractor,
    fragment: str,
    expected_pos: BTPos,
    expected_genders: tuple[BTGender, ...],
) -> None:
    """Real BT prefix fragments resolve to expected POS and genders."""
    result = extractor.extract(fragment)
    assert result.pos == expected_pos
    assert result.genders == expected_genders


def test_verb_paradigm_takes_priority_over_adj_in_bracket(
    extractor: BTPosGenderExtractor,
) -> None:
    """Verb paradigm detection wins when both verb endings and adj appear."""
    fragment = (
        "<I>. p.</I> ede; <I>pp.</I> ed [a, barian <I>to make bare;</I> "
        "bær, se bara; <I>adj.</I> <I>bare</I>] <I>To make bare,</I>"
    )
    result = extractor.extract(fragment)
    assert result.pos == BTPos.VERB


def test_multi_gender_abbad_line(extractor: BTPosGenderExtractor) -> None:
    """Abbad line with m: and m. returns masculine noun once."""
    fragment = (
        "abbod, abbud, abbot, es; <I>m:</I> abboda, an; <I>m. An abbot;</I>"
    )
    result = extractor.extract(fragment)
    assert result.pos == BTPos.NOUN
    assert result.genders == (BTGender.M,)
