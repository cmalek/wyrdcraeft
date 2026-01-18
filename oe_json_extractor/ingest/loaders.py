from __future__ import annotations

from typing import TYPE_CHECKING

from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text

if TYPE_CHECKING:
    from pathlib import Path

    from unstructured.documents.elements import Element


def load_elements(source_path: Path) -> "list[Element]":  # noqa: UP037
    """
    Load elements from a source path.

    Args:
        source_path: The path to the source file.

    Returns:
        A list of elements.

    """
    suffix = source_path.suffix.lower()

    if suffix in {".html", ".htm"}:
        return partition_html(filename=str(source_path))
    if suffix == ".pdf":
        return partition_pdf(
            filename=str(source_path),
            extract_images_in_pdf=False,
            infer_table_structure=False,
        )
    if suffix in {".txt", ".text"}:
        return partition_text(filename=str(source_path))
    msg = f"Unsupported source format: {suffix}"
    raise ValueError(msg)
