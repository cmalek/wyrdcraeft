from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.models.diacritics import DiacriticRestorationResult, MacronAmbiguity


@patch("wyrdcraeft.cli.cli.DiacriticRestorer")
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
                options=["wegas", "wēgas"],
            )
        ],
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
            "options": ["wegas", "wēgas"],
        }
    ]
