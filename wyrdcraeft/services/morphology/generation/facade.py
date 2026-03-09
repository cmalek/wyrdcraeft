"""Human-centric external facade for morphology generation entrypoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .adj_forms import generate_adjforms as _generate_adjforms
from .adv_forms import generate_advforms as _generate_advforms
from .common import generate_vbforms as _generate_vbforms
from .form_rows import output_manual_forms as _output_manual_forms
from .noun_forms import generate_nounforms as _generate_nounforms
from .num_forms import generate_numforms as _generate_numforms

if TYPE_CHECKING:
    from ..contracts import FormOutput
    from ..session import GeneratorSession


class MorphologyGenerationFacade:
    """
    Stable facade exposing clear morphology generation entrypoints.

    Args:
        session: Active generation session.
        output_file: Output sink receiving emitted rows.

    """

    def __init__(self, session: GeneratorSession, output_file: FormOutput) -> None:
        """
        Initialize a facade bound to one generation session and output sink.

        Args:
            session: Active generation session.
            output_file: Output sink receiving emitted rows.

        """
        #: Active generation session.
        self._session = session
        #: Output sink receiving emitted rows.
        self._output_file = output_file

    def output_manual_forms(self) -> None:
        """
        Emit curated manual rows before paradigm-driven generation.

        Side Effects:
            Writes rows to the morphology output stream.

        Note:
            Cross-PoS scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) both require manual exceptions for
            irregular outcomes; this facade method preserves existing row order.

        """
        _output_manual_forms(self._session, self._output_file)

    def generate_verbs(self) -> None:
        """
        Emit all generated verb rows for the bound session.

        Side Effects:
            Writes rows to the morphology output stream.

        Note:
            Verb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) define strong/weak paradigm
            behavior; this facade method preserves parity implementation flow.

        """
        _generate_vbforms(self._session, self._output_file)

    def generate_adjectives(self) -> None:
        """
        Emit all generated adjective rows for the bound session.

        Side Effects:
            Writes rows to the morphology output stream.

        Note:
            Adjective scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe adjective inflection
            categories; this facade method preserves existing generation output.

        """
        _generate_adjforms(self._session, self._output_file)

    def generate_adverbs(self) -> None:
        """
        Emit all generated adverb rows for the bound session.

        Side Effects:
            Writes rows to the morphology output stream.

        Note:
            Adverb scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe adverbial morphology
            classes; this facade method preserves existing generation output.

        """
        _generate_advforms(self._session, self._output_file)

    def generate_numerals(self) -> None:
        """
        Emit all generated numeral rows for the bound session.

        Side Effects:
            Writes rows to the morphology output stream.

        Note:
            Numeral scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe numeral inflection
            patterns; this facade method preserves existing generation output.

        """
        _generate_numforms(self._session, self._output_file)

    def generate_nouns(self) -> None:
        """
        Emit all generated noun rows for the bound session.

        Side Effects:
            Writes rows to the morphology output stream.

        Note:
            Noun scope. Wright (``data/OldEnglishGrammar.pdf``) and Tichý
            (``data/Ondej_Tich_40-54-1.pdf``) describe noun declension classes;
            this facade method preserves existing generation output.

        """
        _generate_nounforms(self._session, self._output_file)
