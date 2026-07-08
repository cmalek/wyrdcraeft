"""Resolve packaged Bosworth-Toller dictionary source file paths."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def _packaged_dictionary_path(relative_name: str) -> Path:
    """
    Resolve one file under ``wyrdcraeft/etc/dictionary``.

    Args:
        relative_name: Basename of the packaged dictionary asset.

    Returns:
        Absolute path to the bundled dictionary resource file.

    """
    return Path(
        str(resources.files("wyrdcraeft").joinpath("etc/dictionary", relative_name))
    )


def default_bt_source_path() -> Path:
    """
    Resolve the packaged Bosworth-Toller ``oe_bt.txt`` source file.

    Returns:
        Path to the bundled Bosworth-Toller source text.

    """
    return _packaged_dictionary_path("oe_bt.txt")


def default_wright_source_path() -> Path:
    """
    Resolve the packaged Wright markdown source file.

    Returns:
        Path to the bundled Wright section markdown corpus.

    """
    return _packaged_dictionary_path("wright.md")


def default_bt_abbreviations_path() -> Path:
    """
    Resolve the packaged Bosworth-Toller abbreviations JSON file.

    Returns:
        Path to the bundled abbreviation lookup table.

    """
    return _packaged_dictionary_path("bosworth_and_toller_abbreviations.json")
