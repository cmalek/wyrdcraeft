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
            "applied_form": None,
            "policy": None,
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
    assert unk_payload == [{"line_number": 1, "word_number": 1, "word": "foo"}]


def test_source_mark_diacritics_writes_unaligned_report(runner, temp_dir):
    from wyrdcraeft.services.markup import MacronApplicator

    index_path = temp_dir / "index.json"
    index_path.write_text(
        json.dumps({"unique": {"ærþling": "ǣrst"}, "ambiguous": {}}), encoding="utf-8"
    )
    source_file = temp_dir / "poem.txt"
    source_file.write_text("ærþling\n", encoding="utf-8")

    with patch(
        "wyrdcraeft.cli.source.MacronApplicator",
        lambda policy: MacronApplicator(index_path, policy=policy),
    ):
        result = runner.invoke(cli, ["source", "mark-diacritics", str(source_file)])

    assert result.exit_code == 0, result.output
    unaligned = json.loads(
        (temp_dir / "poem.unaligned.txt").read_text(encoding="utf-8")
    )
    assert unaligned[0]["word"] == "ærþling"
    assert unaligned[0]["index_form"] == "ǣrst"
    assert (temp_dir / "poem.fixed.txt").read_text(encoding="utf-8") == "ærþling\n"


@patch("wyrdcraeft.cli.source.MacronApplicator")
@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_passes_ambiguity_policy(
    mock_restorer_cls, mock_applicator_cls, runner, temp_dir
):
    source_file = temp_dir / "source.txt"
    source_file.write_text("raw", encoding="utf-8")
    mock_restorer_cls.return_value.restore_text.return_value = (
        DiacriticRestorationResult(marked_text="raw")
    )

    default = runner.invoke(cli, ["source", "mark-diacritics", str(source_file)])
    chosen = runner.invoke(
        cli,
        ["source", "mark-diacritics", str(source_file), "--ambiguity-policy", "union"],
    )
    bad = runner.invoke(
        cli,
        ["source", "mark-diacritics", str(source_file), "--ambiguity-policy", "maybe"],
    )

    assert default.exit_code == 0, default.output
    assert chosen.exit_code == 0, chosen.output
    policies = [c.kwargs["policy"] for c in mock_applicator_cls.call_args_list]
    assert policies == ["auto", "union"]
    assert bad.exit_code == 2


@patch("wyrdcraeft.cli.source.MacronApplicator", new=MagicMock())
@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_counts_guessed_tokens(
    mock_restorer_cls, runner, temp_dir, monkeypatch
):
    import wyrdcraeft.cli.source as source_module

    source_file = temp_dir / "source.txt"
    source_file.write_text("ac", encoding="utf-8")
    guessed = MacronAmbiguity(
        line_number=1,
        word_number=1,
        word="ac",
        options=[AmbiguityOption(form="ac"), AmbiguityOption(form="āc")],
        applied_form="āc",
        policy="union",
    )
    mock_restorer_cls.return_value.restore_text.return_value = (
        DiacriticRestorationResult(marked_text="āc", ambiguities=[guessed])
    )
    # print_info writes to a stderr console CliRunner does not capture.
    messages: list[str] = []
    monkeypatch.setattr(source_module, "print_info", messages.append)

    result = runner.invoke(cli, ["source", "mark-diacritics", str(source_file)])

    assert result.exit_code == 0, result.output
    assert any("Guessed: 1" in m for m in messages)
