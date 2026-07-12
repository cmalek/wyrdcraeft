from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.services.ocr.bt_witness_ocr import (
    DEFAULT_BT_OUTPUT_DIR,
    DEFAULT_BT_SOURCE_DIR,
    BTWitnessOCRConfig,
    BTWitnessOCROrchestrator,
)
from wyrdcraeft.services.ocr.bt_witness_prep import (
    BTWitnessPrepInput,
    BTWitnessPrepRun,
    prepare_pages,
)
from wyrdcraeft.services.ocr.bt_witness_prep.manifest import TILES_MANIFEST_REL
from wyrdcraeft.services.ocr.bt_witness_prep.pipeline import _filter_source_pages
from wyrdcraeft.services.ocr.bt_witness_prep.source import BTSourcePageEnumerator

FIXTURE_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "ocr" / "bt_witness_prep"
)
RECIPE_ID = "bt-two-column-v1"


def test_ocr_group_lists_bosworth_toller(runner) -> None:
    result = runner.invoke(cli, ["ocr", "--help"])
    assert result.exit_code == 0
    assert "bosworth-toller" in result.output


def test_bosworth_toller_help_shows_flags(runner) -> None:
    result = runner.invoke(cli, ["ocr", "bosworth-toller", "--help"])
    assert result.exit_code == 0
    assert "--source-dir" in result.output
    assert "--output-dir" in result.output
    assert "--overlap-px" in result.output
    assert "--pages" in result.output
    assert "--limit" in result.output
    assert "--force" in result.output


@patch("wyrdcraeft.cli.ocr.BTWitnessOCROrchestrator")
def test_bosworth_toller_default_prep(mock_orchestrator_cls, runner, tmp_path) -> None:
    mock_orchestrator = mock_orchestrator_cls.return_value
    mock_run = MagicMock(spec=BTWitnessPrepRun)
    mock_run.preprocessed_pages = (MagicMock(),)
    mock_run.tiles = (MagicMock(), MagicMock())
    mock_orchestrator.run_prep.return_value = mock_run

    result = runner.invoke(
        cli,
        [
            "ocr",
            "bosworth-toller",
            "--source-dir",
            str(FIXTURE_DIR),
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 0
    mock_orchestrator_cls.assert_called_once_with()
    config = mock_orchestrator.run_prep.call_args.args[0]
    assert isinstance(config, BTWitnessOCRConfig)
    assert config.source_dir == FIXTURE_DIR
    assert config.output_dir == tmp_path / "out"
    assert config.page_ids is None
    assert config.limit is None
    assert config.force is False
    assert "Bosworth-Toller witness prep complete." in result.output


@patch("wyrdcraeft.cli.ocr.BTWitnessOCROrchestrator")
def test_bosworth_toller_passes_overlap_px(mock_orchestrator_cls, runner, tmp_path) -> None:
    mock_orchestrator = mock_orchestrator_cls.return_value
    mock_run = MagicMock(spec=BTWitnessPrepRun)
    mock_run.preprocessed_pages = ()
    mock_run.tiles = ()
    mock_orchestrator.run_prep.return_value = mock_run

    result = runner.invoke(
        cli,
        [
            "ocr",
            "bosworth-toller",
            "--source-dir",
            str(FIXTURE_DIR),
            "--output-dir",
            str(tmp_path / "out"),
            "--overlap-px",
            "40",
        ],
    )

    assert result.exit_code == 0
    config = mock_orchestrator.run_prep.call_args.args[0]
    assert config.overlap_px == 40


def test_bosworth_toller_passes_page_filter_and_force(runner, tmp_path) -> None:
    with patch("wyrdcraeft.cli.ocr.BTWitnessOCROrchestrator") as mock_cls:
        mock_orchestrator = mock_cls.return_value
        mock_run = MagicMock(spec=BTWitnessPrepRun)
        mock_run.preprocessed_pages = ()
        mock_run.tiles = ()
        mock_orchestrator.run_prep.return_value = mock_run

        result = runner.invoke(
            cli,
            [
                "ocr",
                "bosworth-toller",
                "--source-dir",
                str(FIXTURE_DIR),
                "--output-dir",
                str(tmp_path / "out"),
                "--pages",
                "bt-0002,bt-0007",
                "--limit",
                "1",
                "--force",
            ],
        )

    assert result.exit_code == 0
    config = mock_orchestrator.run_prep.call_args.args[0]
    assert config.page_ids == ("bt-0002", "bt-0007")
    assert config.limit == 1
    assert config.force is True


def test_bosworth_toller_surfaces_prep_errors(runner, tmp_path) -> None:
    with patch("wyrdcraeft.cli.ocr.BTWitnessOCROrchestrator") as mock_cls:
        mock_cls.return_value.run_prep.side_effect = RuntimeError("blocked")

        result = runner.invoke(
            cli,
            [
                "ocr",
                "bosworth-toller",
                "--source-dir",
                str(FIXTURE_DIR),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

    assert result.exit_code != 0
    assert "blocked" in result.output


def test_orchestrator_refuses_nonempty_output_without_force(tmp_path) -> None:
    output_dir = tmp_path / "prep"
    (output_dir / "manifests").mkdir(parents=True)

    orchestrator = BTWitnessOCROrchestrator()
    config = BTWitnessOCRConfig(
        source_dir=FIXTURE_DIR,
        output_dir=output_dir,
        force=False,
    )

    with pytest.raises(RuntimeError, match="--force"):
        orchestrator.run_prep(config)


def test_orchestrator_refuses_existing_tiles_dir_without_force(tmp_path) -> None:
    output_dir = tmp_path / "prep"
    (output_dir / "tiles").mkdir(parents=True)

    orchestrator = BTWitnessOCROrchestrator()
    config = BTWitnessOCRConfig(
        source_dir=FIXTURE_DIR,
        output_dir=output_dir,
        force=False,
    )

    with pytest.raises(RuntimeError, match="--force"):
        orchestrator.run_prep(config)


def test_orchestrator_allows_nonempty_output_with_force(tmp_path) -> None:
    output_dir = tmp_path / "prep"
    (output_dir / "manifests").mkdir(parents=True)
    (output_dir / TILES_MANIFEST_REL).write_text("{}\n", encoding="utf-8")

    captured: list[BTWitnessPrepInput] = []

    def _capture(prep_input: BTWitnessPrepInput) -> BTWitnessPrepRun:
        captured.append(prep_input)
        return prepare_pages(
            BTWitnessPrepInput(
                source_dir=prep_input.source_dir,
                output_dir=tmp_path / "fresh",
                recipe_id=prep_input.recipe_id,
                overlap_px=prep_input.overlap_px,
                page_ids=prep_input.page_ids,
                limit=prep_input.limit,
            ),
        )

    orchestrator = BTWitnessOCROrchestrator(prep_runner=_capture)
    config = BTWitnessOCRConfig(
        source_dir=FIXTURE_DIR,
        output_dir=output_dir,
        page_ids=("bt-0002",),
        force=True,
    )

    run = orchestrator.run_prep(config)

    assert captured[0].page_ids == ("bt-0002",)
    assert len(run.preprocessed_pages) == 1


def test_default_paths_match_spec() -> None:
    assert Path("data/bosworth_toller/jp2") == DEFAULT_BT_SOURCE_DIR
    assert Path("data/ocr/bosworth-toller/prep") == DEFAULT_BT_OUTPUT_DIR


def test_filter_source_pages_by_page_ids() -> None:
    enumerator = BTSourcePageEnumerator(RECIPE_ID)
    source_pages = enumerator.enumerate(FIXTURE_DIR)

    filtered = _filter_source_pages(
        source_pages,
        page_ids=("bt-0007", "bt-0010"),
        limit=None,
    )

    assert [page.page_id for page in filtered] == ["bt-0007", "bt-0010"]


def test_filter_source_pages_applies_limit_after_page_ids() -> None:
    enumerator = BTSourcePageEnumerator(RECIPE_ID)
    source_pages = enumerator.enumerate(FIXTURE_DIR)

    filtered = _filter_source_pages(
        source_pages,
        page_ids=("bt-0007", "bt-0010"),
        limit=1,
    )

    assert [page.page_id for page in filtered] == ["bt-0007"]


def test_bosworth_toller_zero_page_filter_raises_click_exception(
    runner,
    tmp_path,
) -> None:
    result = runner.invoke(
        cli,
        [
            "ocr",
            "bosworth-toller",
            "--source-dir",
            str(FIXTURE_DIR),
            "--output-dir",
            str(tmp_path / "out"),
            "--pages",
            "bt-missing",
        ],
    )

    assert result.exit_code != 0
    assert "bt-missing" in result.output


def test_filter_source_pages_zero_match_raises() -> None:
    enumerator = BTSourcePageEnumerator(RECIPE_ID)
    source_pages = enumerator.enumerate(FIXTURE_DIR)

    with pytest.raises(ValueError, match="bt-missing"):
        _filter_source_pages(
            source_pages,
            page_ids=("bt-missing",),
            limit=None,
        )
