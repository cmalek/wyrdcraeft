"""
Numeral form generation. Port of Perl generate_numforms from create_dict31.pl
(lines 7927-8429).
"""

import io
import re

from wyrdcraeft.services.morphology.session import GeneratorSession

from .common import print_one_form


def _form_from_parts(form_parts: str) -> str:
    r"""
    Remove [0\\-\\n] from form_parts to get form, matching Perl.

    Args:
        form_parts: The form parts to process.

    Returns:
        The processed form.

    """
    return re.sub(r"[0\-\n]", "", form_parts)


def _num_print(  # noqa: PLR0913
    session: GeneratorSession,
    output_file: io.StringIO,
    formhash: dict[str, str],
    form_parts: str,
    function: str,
    prob: str | int | None = None,
) -> None:
    """
    Helper to set form/formParts/function and call print_one_form.

    Args:
        session: The generator session.
        output_file: The output file handle.
        formhash: The form hash.
        form_parts: The form parts.
        function: The function.
        prob: The probability.

    Returns:
        None.

    """
    if prob is not None:
        # create_dict31 full-flow behavior can carry %formhash probability
        # across subsequent prints; differential oracle mode does not.
        if session.enable_num_probability_carry:
            formhash["probability"] = str(prob)

    fh = formhash.copy()
    fh["function"] = function
    fh["form"] = _form_from_parts(form_parts)
    fh["formParts"] = form_parts.replace("\n", "")
    fh.setdefault("var", "")
    fh.setdefault("paraID", "")
    fh.setdefault("class2", "")
    fh.setdefault("class3", "")
    fh.setdefault("comment", "")
    if prob is not None:
        fh["probability"] = str(prob)
    elif not session.enable_num_probability_carry:
        fh.pop("probability", None)
    print_one_form(session, fh, output_file)


def _stem_no_ea(stem: str) -> str:
    """
    Remove trailing [ea] from stem.

    Note:
        This is the same as Perl s/[ea]$//.

    Args:
        stem: The stem to process.

    Returns:
        The processed stem.

    """
    return re.sub(r"[ea]$", "", stem)


def generate_numforms(session: GeneratorSession, output_file: io.StringIO) -> None:  # noqa: PLR0912, PLR0915
    """
    Generate numeral forms.  Processes words where numeral==1. For noun
    numerals: cardinals as nouns (wine, cwēne, spere paradigms). For all
    numerals: cardinals/ordinals as adjectives (blinda paradigm).

    Note:
        Port of Perl ``sub generate_numforms``.

    """
    for word in session.words:
        if word.numeral != 1:
            continue

        bt_id = f"{word.nid:06d}"
        prefix = word.prefix
        stem = word.stem
        stem_no_ea = _stem_no_ea(stem)

        # CARDINALS AS NOUNS (only when noun==1)
        if word.noun == 1:
            formhash_base = {
                "title": word.title,
                "stem": stem,
                "BT": bt_id,
                "wordclass": "numeral",
                "class1": "strong",
                "wright": word.wright,
            }

            # Masculine (wine paradigm)
            formhash_base["paradigm"] = "wine"
            for s in [stem, stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-0"
                    _num_print(session, output_file, formhash_base, fp, "PlMaNo")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-e"
                    _num_print(session, output_file, formhash_base, fp, "PlMaNo")

            for s in [stem, stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-0"
                    _num_print(session, output_file, formhash_base, fp, "PlMaAc")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-e"
                    _num_print(session, output_file, formhash_base, fp, "PlMaAc")

            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-a"
                    _num_print(session, output_file, formhash_base, fp, "PlMaGe")

            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-um"
                    _num_print(session, output_file, formhash_base, fp, "PlMaDa")

            # Feminine (cwēne paradigm)
            formhash_base["paradigm"] = "cwēne"
            for s in [stem, stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-0"
                    _num_print(session, output_file, formhash_base, fp, "PlFeNo")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-e"
                    _num_print(session, output_file, formhash_base, fp, "PlFeNo")

            for s in [stem, stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-0"
                    _num_print(session, output_file, formhash_base, fp, "PlFeAc")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-e"
                    _num_print(session, output_file, formhash_base, fp, "PlFeAc")

            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-a"
                    _num_print(session, output_file, formhash_base, fp, "PlFeGe")

            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-um"
                    _num_print(session, output_file, formhash_base, fp, "PlFeDa")

            # Neuter (spere paradigm)
            formhash_base["paradigm"] = "spere"
            for s in [stem, stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-0"
                    _num_print(session, output_file, formhash_base, fp, "PlNeNo")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-u"
                    _num_print(session, output_file, formhash_base, fp, "PlNeNo")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-o"
                    _num_print(session, output_file, formhash_base, fp, "PlNeNo")

            for s in [stem, stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-0"
                    _num_print(session, output_file, formhash_base, fp, "PlNeAc")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-u"
                    _num_print(session, output_file, formhash_base, fp, "PlNeAc")
            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-o"
                    _num_print(session, output_file, formhash_base, fp, "PlNeAc")

            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-a"
                    _num_print(session, output_file, formhash_base, fp, "PlNeGe")

            for s in [stem_no_ea]:
                if s:
                    fp = f"{prefix}-{s}-um"
                    _num_print(session, output_file, formhash_base, fp, "PlNeDa")

        # CARDINALS AND ORDINALS AS ADJECTIVES (all numerals)
        # alt_title = prefix + "-" + stem, then s/[eao]$//
        alt_title = f"{prefix}-{stem}"
        alt_title = re.sub(r"[eao]$", "", alt_title)

        formhash_adj = {
            "title": word.title,
            "stem": stem,
            "BT": bt_id,
            "wordclass": "numeral",
            "class1": "weak",
            "paradigm": "blinda",
            "wright": word.wright,
        }

        if session.enable_num_probability_carry:
            # Full-flow create_dict31 behavior: use shared $probability from
            # prior adjective generation.
            prob_ena = int(getattr(session, "perl_probability", 0) or 0) + 1
        else:
            # Differential oracle behavior (tests/differential/perl_lib.pl):
            # -ena gets probability 1 and non--ena forms keep probability unset.
            prob_ena = 1

        # Pl Ma
        fp = f"{alt_title}-an"
        _num_print(session, output_file, formhash_adj, fp, "PoPlMaNo")
        _num_print(session, output_file, formhash_adj, fp, "PoPlMaAc")
        fp = f"{alt_title}-ra"
        _num_print(session, output_file, formhash_adj, fp, "PoPlMaGe")
        fp = f"{alt_title}-ena"
        _num_print(session, output_file, formhash_adj, fp, "PoPlMaGe", prob_ena)
        fp = f"{alt_title}-um"
        _num_print(session, output_file, formhash_adj, fp, "PoPlMaDa")

        # Pl Ne
        fp = f"{alt_title}-an"
        _num_print(session, output_file, formhash_adj, fp, "PoPlNeNo")
        _num_print(session, output_file, formhash_adj, fp, "PoPlNeAc")
        fp = f"{alt_title}-ra"
        _num_print(session, output_file, formhash_adj, fp, "PoPlNeGe")
        fp = f"{alt_title}-ena"
        _num_print(session, output_file, formhash_adj, fp, "PoPlNeGe", prob_ena)
        fp = f"{alt_title}-um"
        _num_print(session, output_file, formhash_adj, fp, "PoPlNeDa")

        # Pl Fe
        fp = f"{alt_title}-an"
        _num_print(session, output_file, formhash_adj, fp, "PoPlFeNo")
        _num_print(session, output_file, formhash_adj, fp, "PoPlFeAc")
        fp = f"{alt_title}-ra"
        _num_print(session, output_file, formhash_adj, fp, "PoPlFeGe")
        fp = f"{alt_title}-ena"
        _num_print(session, output_file, formhash_adj, fp, "PoPlFeGe", prob_ena)
        fp = f"{alt_title}-um"
        _num_print(session, output_file, formhash_adj, fp, "PoPlFeDa")
