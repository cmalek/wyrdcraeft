"""Adverb form generation helpers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .common import print_one_form

if TYPE_CHECKING:
    from ..session import GeneratorSession
    from .shared import FormOutput


def generate_advforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Generate adverb forms and comparative/superlative derivatives.

    Args:
        session: Active morphology generator session.
        output_file: Output stream receiving generated rows.

    """
    for word in session.words:
        if word.adverb == 1:
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
            print_one_form(session, formhash, output_file)
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
                    print_one_form(session, fh, output_file)
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
                    print_one_form(session, fh, output_file)
