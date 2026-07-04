from wyrdcraeft.models.morph_catalog import (  # noqa: F401
    MorphClass,
    MorphClassSource,
    MorphClassWrightSection,
    MorphSource,
    WrightSection,
)


def test_morph_catalog_models_importable() -> None:
    assert MorphClass.__tablename__ == "morph_classes"
    assert WrightSection.__tablename__ == "wright_sections"
