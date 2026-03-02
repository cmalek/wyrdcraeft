from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.models.diacritics import (
    AmbiguityOption,
    DiacriticRestorationResult,
    MacronAmbiguity,
    UnknownToken,
)


@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_writes_text_and_ambiguities(
    mock_restorer_cls, runner, temp_dir
):
    source_file = temp_dir / "source.txt"
    output_file = temp_dir / "marked.txt"
    ambiguities_file = temp_dir / "ambiguities.json"
    source_file.write_text("raw", encoding="utf-8")

    mock_restorer = MagicMock()
    mock_restorer.restore_text.return_value = DiacriticRestorationResult(
        marked_text="mārked",
        ambiguities=[
            MacronAmbiguity(
                line_number=3,
                word_number=5,
                word="wegas",
                options=[
                    AmbiguityOption(
                        form="wegas",
                        part_of_speech="noun",
                        definitions=["way"],
                    ),
                    AmbiguityOption(
                        form="wēgas",
                        part_of_speech="noun",
                        definitions=["ways"],
                    ),
                ],
            )
        ],
        unknowns=[],
    )
    mock_restorer_cls.return_value = mock_restorer

    result = runner.invoke(
        cli,
        [
            "source",
            "mark-diacritics",
            str(source_file),
            str(output_file),
            "--ambiguities-output",
            str(ambiguities_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8") == "mārked"

    payload = json.loads(ambiguities_file.read_text(encoding="utf-8"))
    assert payload == [
        {
            "line_number": 3,
            "word_number": 5,
            "word": "wegas",
            "options": [
                {"form": "wegas", "part_of_speech": "noun", "definitions": ["way"]},
                {"form": "wēgas", "part_of_speech": "noun", "definitions": ["ways"]},
            ],
        }
    ]


@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_default_paths(mock_restorer_cls, runner, temp_dir):
    """With only input given, paths default to stem + infix + extension."""
    source_file = temp_dir / "poem.txt"
    source_file.write_text("raw", encoding="utf-8")

    mock_restorer = MagicMock()
    mock_restorer.restore_text.return_value = DiacriticRestorationResult(
        marked_text="fixed",
        ambiguities=[],
        unknowns=[],
    )
    mock_restorer_cls.return_value = mock_restorer

    result = runner.invoke(
        cli,
        ["source", "mark-diacritics", str(source_file)],
    )

    assert result.exit_code == 0
    assert (temp_dir / "poem.fixed.txt").read_text(encoding="utf-8") == "fixed"
    assert json.loads((temp_dir / "poem.anomalies.txt").read_text()) == []
    assert json.loads((temp_dir / "poem.unknown.txt").read_text()) == []


@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_writes_unknowns_file(
    mock_restorer_cls, runner, temp_dir
):
    source_file = temp_dir / "in.txt"
    source_file.write_text("x", encoding="utf-8")

    mock_restorer = MagicMock()
    mock_restorer.restore_text.return_value = DiacriticRestorationResult(
        marked_text="x",
        ambiguities=[],
        unknowns=[
            UnknownToken(line_number=1, word_number=1, word="foo"),
        ],
    )
    mock_restorer_cls.return_value = mock_restorer

    result = runner.invoke(
            cli,
            [
                "source",
                "mark-diacritics",
                str(source_file),
                str(temp_dir / "out.txt"),
                "--ambiguities-output",
                str(temp_dir / "anom.json"),
                "--unknown-output",
                str(temp_dir / "unk.json"),
            ],
    )

    assert result.exit_code == 0
    unk_payload = json.loads((temp_dir / "unk.json").read_text())
    assert unk_payload == [
        {"line_number": 1, "word_number": 1, "word": "foo"}
    ]
