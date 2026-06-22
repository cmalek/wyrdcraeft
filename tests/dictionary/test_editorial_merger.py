"""Tests for Phase 04 BTEditorialMerger and BTTargetResolver."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTPos, BTSense
from wyrdcraeft.services.dictionary.editorial_merger import (
    BTEditorialMerger,
    BTEditRecord,
)
from wyrdcraeft.services.dictionary.line_parser import BTLineParser, ParsedBTLine
from wyrdcraeft.services.dictionary.sense_segmenter import BTSenseSegmenter
from wyrdcraeft.services.dictionary.target_resolver import BTTargetResolver

_GOLDEN_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "golden_merged.jsonl"
)


def _load_golden() -> list[dict]:  # type: ignore[type-arg]
    raw = _GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in raw if line.strip()]


def _parse_lines(
    parser: BTLineParser,
    segmenter: BTSenseSegmenter,
    line_specs: list[dict],  # type: ignore[type-arg]
) -> list[ParsedBTLine]:
    parsed: list[ParsedBTLine] = []
    for spec in line_specs:
        pl = parser.parse(spec["line_no"], spec["text"])
        if pl.skip_reason is None and pl.raw_line is not None:
            senses = segmenter.segment_parsed_line(pl.raw_line.raw_text)
            pl = dataclasses.replace(pl, senses=senses)
        parsed.append(pl)
    return parsed


def _entry_to_comparable(entry: BTConsolidatedEntry) -> dict:  # type: ignore[type-arg]
    return {
        "norm_key": entry.norm_key,
        "headword_raw": entry.headword_raw,
        "pos": entry.pos,
        "senses": [
            {"sense_label": s.sense_label, "gloss_en": s.gloss_en}
            for s in entry.senses
        ],
        "see_also": list(entry.see_also),
        "source_line_nos": list(entry.source_line_nos),
    }


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def parser() -> BTLineParser:
    return BTLineParser()


@pytest.fixture(scope="module")
def segmenter() -> BTSenseSegmenter:
    return BTSenseSegmenter()


@pytest.fixture(scope="module")
def merger() -> BTEditorialMerger:
    return BTEditorialMerger()


@pytest.fixture(scope="module")
def resolver() -> BTTargetResolver:
    return BTTargetResolver()


# ---------------------------------------------------------------------------
# Golden fixture round-trip
# ---------------------------------------------------------------------------


class TestGoldenMerged:
    """Round-trip the golden_merged.jsonl fixture through the merger."""

    def test_golden_file_exists(self) -> None:
        assert _GOLDEN_PATH.exists(), f"Golden fixture missing: {_GOLDEN_PATH}"

    def test_golden_min_records(self) -> None:
        records = _load_golden()
        assert len(records) >= 30, (
            f"Expected ≥30 golden records, got {len(records)}"
        )

    @pytest.mark.parametrize(
        "record",
        _load_golden(),
        ids=[r["id"] for r in _load_golden()],
    )
    def test_golden_record(
        self,
        record: dict,  # type: ignore[type-arg]
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        parsed = _parse_lines(parser, segmenter, record["source_lines"])
        entries, _ = merger.merge(parsed)
        exp = record["expected"]

        matching = [e for e in entries if e.norm_key == exp["norm_key"] and e.pos == exp["pos"]]
        assert matching, (
            f"[{record['id']}] No entry with norm_key={exp['norm_key']!r}, "
            f"pos={exp['pos']!r} in {[_entry_to_comparable(e) for e in entries]}"
        )
        entry = matching[0]
        assert entry.senses == [
            BTSense(sense_label=s["sense_label"], gloss_en=s["gloss_en"])
            for s in exp["senses"]
        ], (
            f"[{record['id']}] Senses mismatch:\n"
            f"  got  = {[(s.sense_label, s.gloss_en) for s in entry.senses]}\n"
            f"  want = {[(s['sense_label'], s['gloss_en']) for s in exp['senses']]}"
        )


# ---------------------------------------------------------------------------
# Homograph resolution: 'a' → adv vs. prep as TWO entries
# ---------------------------------------------------------------------------


class TestHomographResolution:
    """Verify that entries with same norm_key but distinct POS are kept separate."""

    def test_a_homographs_two_entries(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        lines_raw = [
            (
                3,
                "a@<B>ā,</B> aa, aaa; <I>adv. Always, ever, for ever;</I>"
                " semper :-- Ac ā sceal ðæt wiðerwearde gemetgian. Bt. 21.@a,-a,a-",
            ),
            (
                2,
                "a@<B>a;</B> <I>prep. acc. To, for;</I> in :--"
                " A worlda world, Ps. Th. 18, 8.@a,-a,a-",
            ),
        ]
        parsed = [
            dataclasses.replace(
                parser.parse(ln, raw),
                senses=segmenter.segment_parsed_line(parser.parse(ln, raw).raw_line.raw_text)
                if parser.parse(ln, raw).raw_line
                else (),
            )
            for ln, raw in lines_raw
        ]
        entries, _ = merger.merge(parsed)
        pos_values = {e.pos for e in entries}
        assert BTPos.ADV in pos_values, "Expected adv entry"
        assert BTPos.PREP in pos_values, "Expected prep entry"
        assert len(entries) == 2, f"Expected exactly 2 homograph entries, got {len(entries)}"


# ---------------------------------------------------------------------------
# Specific editorial operation scenarios
# ---------------------------------------------------------------------------


class TestSubstituteAsSeed:
    """SUBSTITUTE-only groups produce entries when no MAIN exists."""

    def test_substitute_as_seed(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        raw = (
            "abaedan@<B>ā-bǣdan.</B> <I>Substitute the following:</I>"
            " <B>I.</B> <I>to force, wring</I> :-- X."
            " <B>II.</B> <I>to compel</I>:-- Y."
            " <B>III.</B> <I>to demand, require.</I>@a-bædan"
        )
        pl = parser.parse(27, raw)
        assert pl.raw_line is not None
        pl = dataclasses.replace(pl, senses=segmenter.segment_parsed_line(pl.raw_line.raw_text))

        entries, _ = merger.merge([pl])
        assert len(entries) == 1
        assert entries[0].norm_key == "abædan"
        glosses = [s.gloss_en for s in entries[0].senses]
        assert glosses == ["to force, wring", "to compel", "to demand, require"]


class TestBareDeleClearsSenses:
    """Bare DELE applied to a MAIN entry should clear all senses."""

    def test_dele_clears_senses(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        lines_raw = [
            (
                116,
                "abitweonum@<B>a-bitweōnum;</B> <I>prep. Between;</I> inter :--"
                " Sēt him a-bitweōnum <I>he sat between them.</I>@a-bi-tweonum,a-bitweonum",
            ),
            (
                117,
                "abitweonum@<B>a-bitweōnum</B>. <I>Dele</I>.@a-bi-tweonum,a-bitweonum",
            ),
        ]
        parsed = _parse_lines(parser, segmenter, [
            {"line_no": ln, "text": raw} for ln, raw in lines_raw
        ])
        entries, edits = merger.merge(parsed)
        assert len(entries) == 1
        assert entries[0].norm_key == "abitweonum"
        assert entries[0].senses == [], f"Expected empty senses after bare Dele, got {entries[0].senses}"

        bare_deles = [ed for ed in edits if ed.scope == "bare_dele"]
        assert bare_deles, "Expected at least one bare_dele audit record"


class TestDeleAndAdd:
    """DELE_AND_ADD applied together: specified refs removed, new senses added."""

    def test_adon_dele_and_add(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        lines_raw = [
            (
                497,
                "adon@<B>a-dōn;</B> <I>v. a. To take away, remove, banish;</I>"
                " tollere :-- Adō ða buteran.@a-don",
            ),
            (
                498,
                "adon@<B>ā-dōn.</B> <I>Dele</I> Ælfc. T. 5, 25,"
                " <I>and add: with words further marking removal,</I>"
                " (1) fram:-- Ic ādyde hosp, Jos. 5, 9.@a-don",
            ),
        ]
        parsed = _parse_lines(parser, segmenter, [
            {"line_no": ln, "text": raw} for ln, raw in lines_raw
        ])
        entries, _ = merger.merge(parsed)
        assert any(e.norm_key == "adon" for e in entries)


class TestEditorialUnknownRedistribution:
    """Editorial lines with pos=unknown are redistributed to unambiguous MAIN groups."""

    def test_dele_redistributed_to_known_pos(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        """DELE line (pos=unknown) applied to MAIN (pos=prep) via redistribution."""
        lines_raw = [
            (
                116,
                "abitweonum@<B>a-bitweōnum;</B> <I>prep. Between;</I> inter :-- X.@a-bi-tweonum",
            ),
            (
                117,
                "abitweonum@<B>a-bitweōnum</B>. <I>Dele</I>.@a-bi-tweonum",
            ),
        ]
        parsed = _parse_lines(parser, segmenter, [
            {"line_no": ln, "text": raw} for ln, raw in lines_raw
        ])
        # Before fix: would produce entry with senses from MAIN; with fix: senses cleared.
        entries, _edits = merger.merge(parsed)
        assert len(entries) == 1
        assert entries[0].pos == BTPos.PREP
        assert entries[0].senses == [], "Redistribution must apply Dele to the MAIN entry"


# ---------------------------------------------------------------------------
# BTEditRecord dataclass
# ---------------------------------------------------------------------------


class TestBTEditRecord:
    """Verify BTEditRecord fields are populated correctly."""

    def test_bare_dele_audit_record(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        lines_raw = [
            (10, "x@<B>x-wōrd;</B> <I>n. A word;</I> verbum :-- X.@x-word"),
            (11, "x@<B>x-wōrd</B>. <I>Dele</I>.@x-word"),
        ]
        parsed = _parse_lines(parser, segmenter, [
            {"line_no": ln, "text": raw} for ln, raw in lines_raw
        ])
        _, edits = merger.merge(parsed)
        assert edits, "Expected at least one edit record"
        dele_records = [e for e in edits if e.scope == "bare_dele"]
        assert dele_records
        rec = dele_records[0]
        assert isinstance(rec, BTEditRecord)
        assert rec.applied is True
        assert rec.source_line_no == 11

    def test_add_audit_record_has_correct_norm_key(
        self,
        parser: BTLineParser,
        segmenter: BTSenseSegmenter,
        merger: BTEditorialMerger,
    ) -> None:
        lines_raw = [
            (
                20,
                "abarian@<B>a-barian;</B> <I>p.</I> ede"
                " <I>To make bare, manifest;</I> denudare :-- Gif ðū abarast.@a-barian",
            ),
            (
                21,
                "abarian@<B>ā-barian.</B> <I>Add:</I>"
                " <B>I.</B> <I>to make bare, strip</I> :-- Stōwe rōde ābarude.@a-barian",
            ),
        ]
        parsed = _parse_lines(parser, segmenter, [
            {"line_no": ln, "text": raw} for ln, raw in lines_raw
        ])
        _entries, edits = merger.merge(parsed)
        add_records = [e for e in edits if "add" in e.op.value]
        assert add_records, f"Expected add audit records, got {edits}"
        assert all(r.target_norm_key == "abarian" for r in add_records)


# ---------------------------------------------------------------------------
# BTTargetResolver
# ---------------------------------------------------------------------------


class TestBTTargetResolver:
    """Unit tests for BTTargetResolver."""

    def test_resolve_for_x_in_dict(self, resolver: BTTargetResolver) -> None:
        body = (
            "<B>ā-bisgung</B> e; <I>f. Substitute the following for</I>"
            " ā-bysgung <I>in Dict</I>."
        )
        result = resolver.resolve_for_x_in_dict(body)
        assert result is not None
        assert result == "abysgung"

    def test_slug_to_norm_key(self, resolver: BTTargetResolver) -> None:
        assert resolver.slug_to_norm_key("a-bædan") == "abædan"
        assert resolver.slug_to_norm_key("abbod-rice,abbod") == "abbodrice"

    def test_slug_to_norm_key_empty_returns_none(self, resolver: BTTargetResolver) -> None:
        assert resolver.slug_to_norm_key("") is None

    def test_merge_key_for_line(
        self,
        parser: BTLineParser,
        resolver: BTTargetResolver,
    ) -> None:
        raw = "abbad@<B>abbad,</B> es; <I>m. An abbot;</I> abbās :-- X.@abbad"
        pl = parser.parse(37, raw)
        key = resolver.merge_key_for_line(pl)
        assert key is not None
        norm_key, pos = key
        assert norm_key == "abbad"
        assert pos == BTPos.NOUN

    def test_merge_key_none_for_skipped_line(self, resolver: BTTargetResolver) -> None:
        from wyrdcraeft.services.dictionary.line_parser import ParsedBTLine

        skipped = ParsedBTLine(
            raw_line=None,
            lookup_keys=[],
            slug_field="",
            skip_reason="no <B> headword",
            pos=BTPos.UNKNOWN,
            genders=[],
            variants=[],
            senses=(),
            etymology_blocks=[],
            headword_macronized="",
            editorial_target=None,
            dele_refs=[],
        )
        assert resolver.merge_key_for_line(skipped) is None
