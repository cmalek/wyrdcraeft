"""Morphology input path defaults live on the generation runner."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.morphology.build_runner import (
    MorphologyBuildRunnerError,
    default_morphology_data_dir,
    resolve_morphology_input_paths,
    validate_morphology_input_paths,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_morphology_input_paths_uses_data_dir_defaults(
    tmp_path: Path,
) -> None:
    dictionary, manual, paradigms, prefixes = resolve_morphology_input_paths(
        data_dir=tmp_path,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    assert dictionary == tmp_path / "dict_adj-vb-part-num-adv-noun.txt"
    assert manual == tmp_path / "manual_forms.txt"
    assert paradigms == tmp_path / "para_vb.txt"
    assert prefixes == tmp_path / "prefixes.txt"


def test_resolve_morphology_input_paths_keeps_overrides(tmp_path: Path) -> None:
    override = tmp_path / "custom.txt"
    dictionary, _, _, _ = resolve_morphology_input_paths(
        data_dir=tmp_path,
        dictionary=override,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    assert dictionary == override


def test_validate_morphology_input_paths_raises_for_missing_file(
    tmp_path: Path,
) -> None:
    paths = resolve_morphology_input_paths(
        data_dir=tmp_path,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    with pytest.raises(MorphologyBuildRunnerError, match="Missing dictionary file"):
        validate_morphology_input_paths(paths)


def test_packaged_default_morphology_data_dir_exists() -> None:
    data_dir = default_morphology_data_dir()
    assert data_dir.is_dir()
    assert (data_dir / "dict_adj-vb-part-num-adv-noun.txt").is_file()
