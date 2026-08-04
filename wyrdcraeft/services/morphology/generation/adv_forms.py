"""Adverb form generation helpers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..progress import MorphologyStage
from .form_rows import print_one_form

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import Word

    from ..progress import MorphologyGenerateProgressCoordinator
    from ..session import GenerationRunState, WordPool
    from .shared import FormOutput


class AdverbFormGenerator:
    """
    Generates adverb surface forms (base, comparative, superlative) for one
    morphology generation run.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: Output stream receiving generated rows.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Bind an adverb form generator to one word pool, run state, and
        output sink.

        Args:
            word_pool: Word pool supplying the lemmas to generate forms for.
            run_state: Mutable per-run generation state.
            output_file: Output stream receiving generated rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Word pool supplying the lemmas to generate forms for.
        self._word_pool = word_pool
        #: Mutable per-run generation state.
        self._run_state = run_state
        #: Output stream receiving generated rows.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """
        Generate adverb forms and comparative/superlative derivatives.

        Side Effects:
            Writes generated rows to the morphology output stream.

        """
        for word in self._word_pool.words:
            if word.adverb == 1:
                self._generate_word(word)

    def _generate_word(self, word: Word) -> None:
        """
        Generate adverb forms and comparative/superlative derivatives for a
        single word.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            word: The word to generate forms for.

        """
        if self._progress is not None:
            self._progress.advance(
                MorphologyStage.ADVERBS,
                lemma=word.title,
                wright=word.wright,
                forms_written=self._run_state.output_counter,
            )
        bt_id = f"{word.nid:06d}"
        formhash = {
            "title": word.title,
            "stem": word.stem,
            "BT": bt_id,
            "wordclass": "adverb",
            "wright": word.wright,
            "var": "",  # Perl generate_advforms does not set var
            "class1": "",
            "class2": "",
            "class3": "",
            "paradigm": "",
            "paraID": "",
            "comment": "",
        }
        formhash["function"] = "Po"
        formhash["probability"] = "0"
        form_parts = f"{word.prefix}-{word.stem}-0"
        formhash["form"] = re.sub(r"[0\-\n]", "", form_parts)
        formhash["formParts"] = form_parts.replace("\n", "")
        print_one_form(self._run_state, formhash, self._output_file)
        stem_co = word.stem
        if stem_co not in ["wel", "yfele", "micle", "lytel"]:
            stem_co = re.sub(r"e$", "", stem_co, flags=re.IGNORECASE)
            for suff, prob in [("or", "0"), ("ur", "1"), ("ar", "2")]:
                fh = formhash.copy()
                fh["function"] = "Co"
                fh["probability"] = prob
                fp = f"{word.prefix}-{stem_co}-{suff}"
                fh["form"] = re.sub(r"[0\-\n]", "", fp)
                fh["formParts"] = fp.replace("\n", "")
                print_one_form(self._run_state, fh, self._output_file)
        stem_su = word.stem
        if stem_su not in ["wel", "yfele", "micle", "lytel"]:
            stem_su = re.sub(r"e$", "", stem_su, flags=re.IGNORECASE)
            for suff, prob in [
                ("ost", "0"),
                ("ust", "1"),
                ("ast", "2"),
                ("st", "2"),
            ]:
                fh = formhash.copy()
                fh["function"] = "Su"
                fh["probability"] = prob
                fp = f"{word.prefix}-{stem_su}-{suff}"
                fh["form"] = re.sub(r"[0\-\n]", "", fp)
                fh["formParts"] = fp.replace("\n", "")
                print_one_form(self._run_state, fh, self._output_file)
