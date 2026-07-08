"""Tests for etymology parsing and browse table formatting."""

from __future__ import annotations

from wyrdcraeft.models.dictionary import BTPos
from wyrdcraeft.services.dictionary.etymology_display import (
    format_etymology_display,
    parse_etymology_text,
    partition_etymology_blocks,
    relocate_misplaced_etymology_attestations,
)
from wyrdcraeft.services.dictionary.line_parser import ParsedBTLine


def test_parse_cognate_chain_with_citation() -> None:
    display = parse_etymology_text(
        "[Cf. Cailis <I>nine-pins</I>, Rel. Ant. ii. 224. "
        "<I>O. H. Ger.</I> chegel <I>paxillus, clavus</I>.]"
    )
    assert display.attestations == ()
    assert len(display.references) >= 2
    german = next(row for row in display.references if row.lang_source == "O. H. Ger.")
    assert german.word == "chegel"
    assert "paxillus" in german.meaning
    assert "Rel. Ant. ii. 224" in german.source or any(
        "Rel. Ant. ii. 224" in row.source for row in display.references
    )


def test_parse_multiple_german_cognates() -> None:
    display = parse_etymology_text(
        "[Cf. <I>O. H. Ger.</I> ar-twelan <I>torpere;</I> ar-twellen <I>to delay</I> (<I>intrans.</I>.]"
    )
    assert display.attestations == ()
    assert any(row.word == "ar-twelan" for row in display.references)
    assert any("delay" in row.meaning for row in display.references)


def test_parse_colon_separated_lang_chain() -> None:
    display = parse_etymology_text(
        "[<I>O. Sax.</I> ā-dēlian: <I>O. H. Ger.</I> ar-teilen <I>distinguere, decernere, judicare.</I>]"
    )
    assert any(row.lang_source == "O. Sax." and row.word == "ā-dēlian" for row in display.references)
    assert any(
        row.lang_source == "O. H. Ger." and row.word == "ar-teilen" for row in display.references
    )


def test_parse_norse_words_with_latin_tail() -> None:
    display = parse_etymology_text("[<I>O.Nrs.</I> froða, frauð <I>froth;</I> spuma.]")
    row = display.references[0]
    assert row.lang_source == "O.Nrs."
    assert "froða" in row.word
    assert "froth" in row.meaning
    assert "spuma" in row.meaning


def test_misplaced_attestation_is_flagged() -> None:
    display = parse_etymology_text(
        "[Aldolf his sweord adroh, Lay. 16487. Adraweth ȝoure suerdes, R. Glouc. 361.]"
    )
    assert display.references == ()
    assert len(display.attestations) == 1
    assert "Lay. 16487" in display.attestations[0].source


def test_mixed_attestation_and_cognates_split() -> None:
    display = parse_etymology_text(
        "[Ne oter ne acquerne, beuveyr ne sablyne, Misc. 70, 358. "
        "Cf. <I>O. H. Ger.</I> eihhorn <I>spiriolus: Ger.</I> eichhorn: "
        "<I>Icel.</I> īkorni <I>squirrel.</I>]"
    )
    assert display.attestations
    assert any(row.lang_source == "O. H. Ger." for row in display.references)
    formatted = format_etymology_display(display)
    assert "WARNING: misplaced attestations" in formatted
    assert "Lang/Source" in formatted


def test_partition_mixed_block_splits_attestation_and_etymology() -> None:
    clean, tails = partition_etymology_blocks(
        (
            "[Ne oter ne acquerne, beuveyr ne sablyne, Misc. 70, 358. "
            "Cf. <I>O. H. Ger.</I> eihhorn <I>spiriolus: Ger.</I> eichhorn: "
            "<I>Icel.</I> īkorni <I>squirrel.</I>]",
        )
    )
    assert len(clean) == 1
    assert "O. H. Ger." in clean[0]
    assert "Misc. 70, 358" in tails[0]


def test_relocate_moves_attestation_tail_to_last_sense() -> None:
    from wyrdcraeft.models.dictionary import BTSense

    parsed = ParsedBTLine(
        raw_line=None,
        lookup_keys=(),
        slug_field="",
        headword_macronized="adrōh",
        variants=(),
        pos=BTPos.VERB,
        genders=(),
        editorial_target=None,
        dele_refs=(),
        etymology_blocks=(
            "[Aldolf his sweord adroh, Lay. 16487. "
            "Adraweth ȝoure suerdes, R. Glouc. 361.]",
        ),
        senses=(
            BTSense(
                gloss_en="to draw",
                sense_path="1",
                parent_path=None,
                source_label_raw="",
                source_fragment_raw="<B>ā-drōh.</B> <I>v. To draw</I>",
                prefix_fragment_raw="",
                modifiers=(),
                grammatical_context=(),
                usage_note="",
            ),
        ),
    )
    relocated = relocate_misplaced_etymology_attestations(parsed)
    assert relocated.etymology_blocks == ()
    assert "Lay. 16487" in relocated.senses[-1].source_fragment_raw
    assert " :-- " in relocated.senses[-1].source_fragment_raw


def test_format_etymology_display_renders_table_headers() -> None:
    display = parse_etymology_text("[Cf. <I>O. H. Ger.</I> ezzen <I>depascere.</I>]")
    formatted = format_etymology_display(display)
    assert formatted.startswith("Etymology")
    assert "Lang/Source" in formatted
    assert "O. H. Ger." in formatted
    assert "ezzen" in formatted
