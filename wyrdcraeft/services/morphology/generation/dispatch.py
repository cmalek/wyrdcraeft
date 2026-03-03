"""Generation entrypoint dispatch wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..generators.adj_forms import generate_adjforms as _generate_adjforms
from ..generators.common import generate_advforms as _generate_advforms
from ..generators.noun_forms import generate_nounforms as _generate_nounforms
from ..generators.num_forms import generate_numforms as _generate_numforms
from .verb_engine import VerbFormOrchestrator

if TYPE_CHECKING:
    from ..contracts import FormOutput
    from ..session import GeneratorSession


def generate_vbforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """Generate verb forms via the orchestrator wrapper."""
    VerbFormOrchestrator(session, output_file).generate()


def generate_adjforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """Generate adjective forms via the legacy module."""
    _generate_adjforms(session, output_file)


def generate_advforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """Generate adverb forms via the legacy module."""
    _generate_advforms(session, output_file)


def generate_numforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """Generate numeral forms via the legacy module."""
    _generate_numforms(session, output_file)


def generate_nounforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """Generate noun forms via the legacy module."""
    _generate_nounforms(session, output_file)
