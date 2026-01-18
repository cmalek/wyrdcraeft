from __future__ import annotations


class OejsonextractorError(Exception):
    """Base exception for all oe_json_extractor errors."""


class ConfigurationError(OejsonextractorError):
    """Raised when settings or configuration fails."""


class FileError(OejsonextractorError):
    """Raised when file I/O operations fail."""
