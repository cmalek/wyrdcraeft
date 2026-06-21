"""Generation entrypoint dispatch wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .facade import MorphologyGenerationFacade

if TYPE_CHECKING:
    from ..contracts import FormOutput
    from ..progress import MorphologyGenerateProgressCoordinator
    from ..session import GeneratorSession


def generate_vbforms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Generate verb forms via the migrated generation module.

    Note:
        Verb inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is verb.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    MorphologyGenerationFacade(
        session,
        output_file,
        progress=progress,
    ).generate_verbs()


def output_manual_forms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Emit manual forms via the migrated generation module.

    Note:
        Manual exceptions are curated against ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this outputs cross-Part
        of Speech override forms that do not come from regular paradigms.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    MorphologyGenerationFacade(
        session,
        output_file,
        progress=progress,
    ).output_manual_forms()


def generate_adjforms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Generate adjective forms via the legacy module.

    Note:
        Adjective inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is adjective.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    MorphologyGenerationFacade(
        session,
        output_file,
        progress=progress,
    ).generate_adjectives()


def generate_advforms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Generate adverb forms via the migrated generation module.

    Note:
        Adverb morphology follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is adverb.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    MorphologyGenerationFacade(
        session,
        output_file,
        progress=progress,
    ).generate_adverbs()


def generate_numforms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Generate numeral forms via the legacy module.

    Note:
        Numeral inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is numeral.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    MorphologyGenerationFacade(
        session,
        output_file,
        progress=progress,
    ).generate_numerals()


def generate_nounforms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    """
    Generate noun forms via the legacy module.

    Note:
        Noun inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is noun.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """
    MorphologyGenerationFacade(
        session,
        output_file,
        progress=progress,
    ).generate_nouns()
