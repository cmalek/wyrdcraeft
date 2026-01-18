from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text

if TYPE_CHECKING:
    from unstructured.documents.elements import Element


class SourceLoader:
    """
    Load elements from a source path or URL.
    """

    def load(self, source: str | Path) -> list[Element]:
        """
        Load elements from a source path or URL.

        Args:
            source: The path to the source file or a URL.

        Returns:
            A list of elements.

        """
        source_str = str(source)
        if source_str.startswith(("http://", "https://")):
            return self._load_from_url(source_str)
        return self.load_from_file(Path(source))

    def load_from_file(self, source_path: Path) -> list[Element]:
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

    def _load_from_url(self, url: str) -> list[Element]:
        """
        Load elements from a URL.

        Args:
            url: The URL to load from.

        Returns:
            A list of elements.

        """
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            # We need to preserve the extension if possible, or at least
            # have some way to tell unstructured what it is.
            # But unstructured often looks at the extension.
            # Let's try to infer it from the URL or Content-Type.
            suffix = Path(url).suffix.lower()
            if not suffix:
                content_type = response.headers.get("Content-Type", "")
                if "html" in content_type:
                    suffix = ".html"
                elif "pdf" in content_type:
                    suffix = ".pdf"
                else:
                    suffix = ".txt"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = Path(tmp.name)

            try:
                return self.load_from_file(tmp_path)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
