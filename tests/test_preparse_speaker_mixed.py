from __future__ import annotations

from wyrdcraeft.ingest.pipeline import StructureParser, ingest_auto
from wyrdcraeft.models.parsing import RawBlock
from wyrdcraeft.models import TextMetadata
from pathlib import Path


def test_speaker_aware_splitting_same_kind() -> None:
    blocks = [
        RawBlock(
            text="Saturnus cwæð:\nSaga mē hwæt wisdom sīe.",
            category="NarrativeText",
            page=1,
        ),
        RawBlock(
            text="Salomon cwæð:\nIc þe secge sōð.", category="NarrativeText", page=1
        ),
    ]
    doc = StructureParser().parse(blocks)
    # Should split into two provisional sections due to speaker change
    assert len(doc.sections) == 2
    assert doc.sections[0].speaker_hint is not None
    assert doc.sections[1].speaker_hint is not None


def test_mixed_mode_splitting() -> None:
    blocks = [
        RawBlock(text="Þa com se cyning to tune.", category="NarrativeText", page=1),
        RawBlock(
            text="Hwæt! wē Gār-Dena in gēar-dagum\nþēodcyninga þrym gefrūnon",
            category="NarrativeText",
            page=1,
        ),
        RawBlock(text="Þa spræc he eft.", category="NarrativeText", page=1),
    ]
    doc = StructureParser().parse(blocks)
    # prose, verse, prose => three sections
    assert [s.kind for s in doc.sections] == ["prose", "verse", "prose"]
