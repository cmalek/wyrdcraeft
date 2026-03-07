"""Generation entrypoint dispatch wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .adj_forms import generate_adjforms as _generate_adjforms
from .adv_forms import generate_advforms as _generate_advforms
from .common import (
    generate_vbforms as _generate_vbforms,
)
from .form_rows import output_manual_forms as _output_manual_forms
from .noun_forms import generate_nounforms as _generate_nounforms
from .num_forms import generate_numforms as _generate_numforms

if TYPE_CHECKING:
    from ..contracts import FormOutput
    from ..session import GeneratorSession


def generate_vbforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Generate verb forms via the migrated generation module.

    Note:
        Verb inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is verb.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    """
    _generate_vbforms(session, output_file)


def output_manual_forms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Emit manual forms via the migrated generation module.

    Note:
        Manual exceptions are curated against ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this outputs cross-Part
        of Speech override forms that do not come from regular paradigms.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    """
    _output_manual_forms(session, output_file)


def generate_adjforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Generate adjective forms via the legacy module.

    Note:
        Adjective inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is adjective.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    """
    _generate_adjforms(session, output_file)


def generate_advforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Generate adverb forms via the migrated generation module.

    Note:
        Adverb morphology follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is adverb.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    """
    _generate_advforms(session, output_file)


def generate_numforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Generate numeral forms via the legacy module.

    Note:
        Numeral inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is numeral.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    """
    _generate_numforms(session, output_file)


def generate_nounforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Generate noun forms via the legacy module.

    Note:
        Noun inflection behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this emits forms where
        the Part of Speech is noun.

    Args:
        session: Active generation session.
        output_file: Form output sink.

    """
    _generate_nounforms(session, output_file)
