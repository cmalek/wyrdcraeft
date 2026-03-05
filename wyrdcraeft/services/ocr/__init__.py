"""OCR services for Old English pipeline workflows."""

from .old_english_pipeline import (
    DEFAULT_OCR_LANG,
    DEFAULT_OVERSAMPLE_DPI,
    DEFAULT_TESSERACT_PSM,
    OldEnglishOCRConfig,
    OldEnglishOCROutput,
    build_default_output_dir,
    run_old_english_ocr_pipeline,
)

__all__ = [
    "DEFAULT_OCR_LANG",
    "DEFAULT_OVERSAMPLE_DPI",
    "DEFAULT_TESSERACT_PSM",
    "OldEnglishOCRConfig",
    "OldEnglishOCROutput",
    "build_default_output_dir",
    "run_old_english_ocr_pipeline",
]
