"""
Adjective form generation. Port of Perl generate_adjforms from create_dict31.pl.
"""

import io
import re
from collections.abc import Iterable

from wyrdcraeft.services.morphology.models import Word
from wyrdcraeft.services.morphology.session import GeneratorSession
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .common import print_one_form

def _dedupe_preserve_first(values: Iterable[str]) -> list[str]:
    """Return unique values, preserving first-seen order."""
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique

def _perl_hash_order(values: list[str]) -> list[str]:
    """Return deterministic title ordering without Perl runtime dependency."""
    return _dedupe_preserve_first(values)

def _form_from_parts(form_parts: str) -> str:
    r"""
    Remove [0\\-\\n] from form_parts to get form.

    Note:
        This is the same as Perl s/[0\-\n]//.

    Args:
        form_parts: The form parts to process.

    Returns:
        The processed form.

    """
    return re.sub(r"[0\-\n]", "", form_parts)


def _adj_print(  # noqa: PLR0913
    session: GeneratorSession,
    output_file: io.StringIO,
    formhash: dict[str, str],
    form_parts: str,
    func: str,
    prob: str,
) -> None:
    """
    Helper to set ``form``/``formParts``/``function``/``probability`` and call
    ``print_one_form``.

    Note:
        Matches Perl implementation of ``_adj_print`` function.

    Args:
        session: The generator session.
        output_file: The output file handle.
        formhash: The form hash.
        form_parts: The form parts.
        func: The function.
        prob: The probability.

    """
    fh = formhash.copy()
    fh["function"] = func
    fh["probability"] = prob
    fh["form"] = _form_from_parts(form_parts)
    fh["formParts"] = form_parts.replace("\n", "")
    print_one_form(session, fh, output_file)


def _build_weak_title_array(word: Word, paradigm: str) -> list[str]:
    """Build title_array for weak forms, matching Perl logic."""
    vowel_regex = OENormalizer.VOWEL
    title_array: list[str] = []
    title_alt = word.stem

    # Original
    title_array.append(f"{word.prefix}-{title_alt}")

    # u -> w at end
    if re.search(r"u$", title_alt):
        title_alt = re.sub(r"u$", "w", title_alt)
        title_array.append(f"{word.prefix}-{title_alt}")

    # Drop final vowel
    if re.search(f"{vowel_regex}$", title_alt):
        title_alt = re.sub(f"({vowel_regex})$", "", title_alt)
        title_array.append(f"{word.prefix}-{title_alt}")

    # hālig syncope (only for hālig paradigm, not participles)
    is_halig = "hālig" in paradigm
    if is_halig and (word.papart + word.pspart) == 0:
        # Perl: $title_alt =~ s/($vowel_regex.*)$vowel_regex(.*?)$/$1$2/;
        new_alt = re.sub(
            f"({vowel_regex}.*){vowel_regex}(.*)$",
            r"\1\2",
            title_alt,
        )
        if new_alt != title_alt:
            title_alt = new_alt
            title_array.append(f"{word.prefix}-{title_alt}")

    # Drop trailing h
    if re.search(r"h$", title_alt):
        title_alt = re.sub(r"h$", "", title_alt)
        title_array.append(f"{word.prefix}-{title_alt}")

    return title_array


def _gen_strong_glaed_til(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``glæd``/``til`` paradigm.

    Note:
        Matches Perl ``glæd``/``til`` block.

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    title_alt = f"{word.prefix}-{word.stem}"
    if re.search(r"[\u00e6\u00c6]|ea", paradigm):
        stem_alt = re.sub(r"[\u00e6]|ea", "a", word.stem, flags=re.IGNORECASE)
        stem_alt = re.sub(r"[\u00c6]", "a", stem_alt)
        title_alt = f"{word.prefix}-{stem_alt}"

    base = f"{word.prefix}-{word.stem}"
    # Sg Ma
    _adj_print(session, output_file, formhash, f"{base}-0", "PoSgMaNo", "0")
    _adj_print(session, output_file, formhash, f"{base}-ne", "PoSgMaAc", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoSgMaAc", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-es", "PoSgMaGe", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-um", "PoSgMaDa", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-0", "PoSgMaDa", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-e", "PoSgMaIs", "0")
    # Sg Ne
    _adj_print(session, output_file, formhash, f"{base}-0", "PoSgNeNo", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoSgNeAc", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-es", "PoSgNeGe", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-um", "PoSgNeDa", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-0", "PoSgNeDa", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-e", "PoSgNeIs", "0")
    # Sg Fe
    _adj_print(session, output_file, formhash, f"{title_alt}-u", "PoSgFeNo", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-o", "PoSgFeNo", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-0", "PoSgFeAc", "0")
    _adj_print(session, output_file, formhash, f"{base}-re", "PoSgFeGe", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoSgFeGe", "1")
    _adj_print(session, output_file, formhash, f"{base}-re", "PoSgFeDa", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoSgFeDa", "1")
    # Pl Ma
    _adj_print(session, output_file, formhash, f"{title_alt}-e", "PoPlMaNo", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-0", "PoPlMaNo", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-e", "PoPlMaAc", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-0", "PoPlMaAc", "1")
    _adj_print(session, output_file, formhash, f"{base}-ra", "PoPlMaGe", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoPlMaGe", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-um", "PoPlMaDa", "0")
    # Pl Ne
    _adj_print(session, output_file, formhash, f"{title_alt}-u", "PoPlNeNo", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-o", "PoPlNeNo", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-u", "PoPlNeAc", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-o", "PoPlNeAc", "1")
    _adj_print(session, output_file, formhash, f"{base}-ra", "PoPlNeGe", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoPlNeGe", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-um", "PoPlNeDa", "0")
    # Pl Fe
    _adj_print(session, output_file, formhash, f"{title_alt}-a", "PoPlFeNo", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-o", "PoPlFeNo", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-a", "PoPlFeAc", "0")
    _adj_print(session, output_file, formhash, f"{title_alt}-o", "PoPlFeAc", "1")
    _adj_print(session, output_file, formhash, f"{base}-ra", "PoPlFeGe", "0")
    _adj_print(session, output_file, formhash, f"{base}-0", "PoPlFeGe", "1")
    _adj_print(session, output_file, formhash, f"{title_alt}-um", "PoPlFeDa", "0")


def _gen_strong_blind(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``blind`` paradigm.

    Note:
        Matches Perl ``blind`` block.

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    base = f"{word.prefix}-{word.stem}"
    forms = [
        ("PoSgMaNo", "0", "0"),
        ("PoSgMaAc", "ne", "0"),
        ("PoSgMaAc", "0", "1"),
        ("PoSgMaGe", "es", "0"),
        ("PoSgMaDa", "um", "0"),
        ("PoSgMaDa", "0", "1"),
        ("PoSgMaIs", "e", "0"),
        ("PoSgNeNo", "0", "0"),
        ("PoSgNeAc", "0", "0"),
        ("PoSgNeGe", "es", "0"),
        ("PoSgNeDa", "um", "0"),
        ("PoSgNeDa", "0", "1"),
        ("PoSgNeIs", "e", "0"),
        ("PoSgFeNo", "0", "0"),
        ("PoSgFeAc", "e", "0"),
        ("PoSgFeGe", "re", "0"),
        ("PoSgFeGe", "0", "1"),
        ("PoSgFeDa", "re", "0"),
        ("PoSgFeDa", "0", "1"),
        ("PoPlMaNo", "e", "0"),
        ("PoPlMaNo", "0", "1"),
        ("PoPlMaAc", "e", "0"),
        ("PoPlMaAc", "0", "1"),
        ("PoPlMaGe", "ra", "0"),
        ("PoPlMaGe", "0", "1"),
        ("PoPlMaDa", "um", "0"),
        ("PoPlNeNo", "0", "0"),
        ("PoPlNeAc", "0", "0"),
        ("PoPlNeGe", "ra", "0"),
        ("PoPlNeGe", "0", "1"),
        ("PoPlNeDa", "um", "0"),
        ("PoPlFeNo", "a", "0"),
        ("PoPlFeNo", "e", "1"),
        ("PoPlFeAc", "a", "0"),
        ("PoPlFeAc", "e", "1"),
        ("PoPlFeGe", "ra", "0"),
        ("PoPlFeGe", "0", "1"),
        ("PoPlFeDa", "um", "0"),
    ]
    for func, ending, prob in forms:
        _adj_print(session, output_file, formhash, f"{base}-{ending}", func, prob)


def _gen_strong_heah_thweorh(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``hēah``/``þweorh`` paradigm (h-stem).

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    title_alt = f"{word.prefix}-{word.stem}"
    if "weorh" in paradigm:  # þweorh
        stem_alt = re.sub(r"e([ao])", "\u0113\\1", word.stem)  # e+ao -> ēa/ēo
        stem_alt = re.sub(r"([^\u0113])o", lambda m: f"{m.group(1)}ō", stem_alt)
        title_alt = f"{word.prefix}-{stem_alt}"
    title_alt = re.sub(r"h$", "", title_alt)
    forms = [
        ("PoSgMaNo", f"{title_alt}h-0", "0"),
        ("PoSgMaAc", f"{title_alt}-ne", "0"),
        ("PoSgMaAc", f"{title_alt}n-ne", "1"),
        ("PoSgMaGe", f"{title_alt}-s", "0"),
        ("PoSgMaGe", f"{title_alt}-es", "0"),
        ("PoSgMaDa", f"{title_alt}-m", "0"),
        ("PoSgMaDa", f"{title_alt}-um", "1"),
        ("PoSgMaIs", f"{title_alt}-0", "0"),
        ("PoSgNeNo", f"{title_alt}h-0", "0"),
        ("PoSgNeAc", f"{title_alt}h-0", "0"),
        ("PoSgNeGe", f"{title_alt}-s", "0"),
        ("PoSgNeGe", f"{title_alt}-es", "0"),
        ("PoSgNeDa", f"{title_alt}-m", "0"),
        ("PoSgNeDa", f"{title_alt}-um", "1"),
        ("PoSgNeIs", f"{title_alt}-0", "0"),
        ("PoSgFeNo", f"{title_alt}-0", "0"),
        ("PoSgFeAc", f"{title_alt}-0", "0"),
        ("PoSgFeGe", f"{title_alt}-re", "0"),
        ("PoSgFeGe", f"{title_alt}r-re", "1"),
        ("PoSgFeDa", f"{title_alt}-re", "0"),
        ("PoSgFeDa", f"{title_alt}r-re", "1"),
        ("PoPlMaNo", f"{title_alt}-0", "0"),
        ("PoPlMaAc", f"{title_alt}-0", "0"),
        ("PoPlMaGe", f"{title_alt}-ra", "0"),
        ("PoPlMaGe", f"{title_alt}r-ra", "1"),
        ("PoPlMaDa", f"{title_alt}-m", "0"),
        ("PoPlMaDa", f"{title_alt}-um", "1"),
        ("PoPlNeNo", f"{title_alt}-0", "0"),
        ("PoPlNeAc", f"{title_alt}-0", "0"),
        ("PoPlNeGe", f"{title_alt}-ra", "0"),
        ("PoPlNeGe", f"{title_alt}r-ra", "1"),
        ("PoPlNeDa", f"{title_alt}-m", "0"),
        ("PoPlNeDa", f"{title_alt}-um", "1"),
        ("PoPlFeNo", f"{title_alt}-0", "0"),
        ("PoPlFeAc", f"{title_alt}-0", "0"),
        ("PoPlFeGe", f"{title_alt}-ra", "0"),
        ("PoPlFeGe", f"{title_alt}r-ra", "1"),
        ("PoPlFeDa", f"{title_alt}-m", "0"),
        ("PoPlFeDa", f"{title_alt}-um", "1"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(session, output_file, formhash, form_parts, func, prob)


def _gen_strong_manig(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``māniġ`` paradigm.

    Note:
        Matches Perl māniġ block: no base-0 variants for PoSgMaAc, PoSgMaDa,
        PoSgNeDa, PoSgFeGe, PoSgFeDa, PoPlMaNo, PoPlMaAc, PoPlMaGe, PoPlNeGe,
        PoPlFeGe.

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    base = f"{word.prefix}-{word.stem}"
    forms = [
        ("PoSgMaNo", "0", "0"),
        ("PoSgMaAc", "ne", "0"),
        ("PoSgMaGe", "es", "0"),
        ("PoSgMaDa", "um", "0"),
        ("PoSgMaIs", "e", "0"),
        ("PoSgNeNo", "0", "0"),
        ("PoSgNeAc", "0", "0"),
        ("PoSgNeGe", "es", "0"),
        ("PoSgNeDa", "um", "0"),
        ("PoSgNeIs", "e", "0"),
        ("PoSgFeNo", "0", "0"),
        ("PoSgFeAc", "e", "0"),
        ("PoSgFeGe", "re", "0"),
        ("PoSgFeDa", "re", "0"),
        ("PoPlMaNo", "e", "0"),
        ("PoPlMaAc", "e", "0"),
        ("PoPlMaGe", "ra", "0"),
        ("PoPlMaDa", "um", "0"),
        ("PoPlNeNo", "0", "0"),
        ("PoPlNeAc", "0", "0"),
        ("PoPlNeGe", "ra", "0"),
        ("PoPlNeDa", "um", "0"),
        ("PoPlFeNo", "a", "0"),
        ("PoPlFeNo", "e", "1"),
        ("PoPlFeAc", "a", "0"),
        ("PoPlFeAc", "e", "1"),
        ("PoPlFeGe", "ra", "0"),
        ("PoPlFeDa", "um", "0"),
    ]
    for func, ending, prob in forms:
        _adj_print(session, output_file, formhash, f"{base}-{ending}", func, prob)


def _gen_strong_halig(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``hāliġ`` paradigm (ja-stem with syncope).

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    vowel_regex = OENormalizer.VOWEL
    title_alt = word.stem
    if word.papart != 1:
        title_alt = re.sub(f"({vowel_regex}.*){vowel_regex}(.*)$", r"\1\2", title_alt)
    title_alt = f"{word.prefix}-{title_alt}"
    base = f"{word.prefix}-{word.stem}"
    forms = [
        ("PoSgMaNo", f"{base}-0", "0"),
        ("PoSgMaAc", f"{base}-ne", "0"),
        ("PoSgMaGe", f"{title_alt}-es", "0"),
        ("PoSgMaGe", f"{base}-es", "1"),
        ("PoSgMaDa", f"{title_alt}-um", "0"),
        ("PoSgMaDa", f"{base}-um", "1"),
        ("PoSgMaIs", f"{title_alt}-e", "0"),
        ("PoSgMaIs", f"{base}-e", "1"),
        ("PoSgNeNo", f"{base}-0", "0"),
        ("PoSgNeAc", f"{base}-0", "0"),
        ("PoSgNeGe", f"{title_alt}-es", "0"),
        ("PoSgNeGe", f"{base}-es", "1"),
        ("PoSgNeDa", f"{title_alt}-um", "0"),
        ("PoSgNeDa", f"{base}-um", "1"),
        ("PoSgNeIs", f"{title_alt}-e", "0"),
        ("PoSgNeIs", f"{base}-e", "1"),
        ("PoSgFeNo", f"{base}-u", "0"),
        ("PoSgFeNo", f"{base}-o", "1"),
        ("PoSgFeAc", f"{title_alt}-e", "0"),
        ("PoSgFeAc", f"{base}-e", "1"),
        ("PoSgFeGe", f"{base}-re", "0"),
        ("PoSgFeDa", f"{base}-re", "0"),
        ("PoPlMaNo", f"{title_alt}-e", "0"),
        ("PoPlMaNo", f"{base}-e", "1"),
        ("PoPlMaAc", f"{title_alt}-e", "0"),
        ("PoPlMaAc", f"{base}-e", "1"),
        ("PoPlMaGe", f"{base}-ra", "0"),
        ("PoPlMaDa", f"{title_alt}-um", "0"),
        ("PoPlMaDa", f"{base}-um", "1"),
        ("PoPlNeNo", f"{base}-u", "0"),
        ("PoPlNeNo", f"{base}-o", "1"),
        ("PoPlNeAc", f"{base}-u", "0"),
        ("PoPlNeAc", f"{base}-o", "1"),
        ("PoPlNeGe", f"{base}-ra", "0"),
        ("PoPlNeDa", f"{title_alt}-um", "0"),
        ("PoPlNeDa", f"{base}-um", "1"),
        ("PoPlFeNo", f"{base}-a", "0"),
        ("PoPlFeNo", f"{base}-e", "1"),
        ("PoPlFeAc", f"{base}-a", "0"),
        ("PoPlFeAc", f"{base}-e", "1"),
        ("PoPlFeGe", f"{base}-ra", "0"),
        ("PoPlFeDa", f"{title_alt}-um", "0"),
        ("PoPlFeDa", f"{base}-um", "1"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(session, output_file, formhash, form_parts, func, prob)


def _gen_strong_wilde(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``wilde`` paradigm (i-stem, stem drops final e).

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    title_alt = re.sub(r"e$", "", word.stem)
    title_alt = f"{word.prefix}-{title_alt}"
    forms = [
        ("PoSgMaNo", f"{title_alt}-e", "0"),
        ("PoSgMaAc", f"{title_alt}-ne", "0"),
        ("PoSgMaGe", f"{title_alt}-es", "0"),
        ("PoSgMaDa", f"{title_alt}-um", "0"),
        ("PoSgMaIs", f"{title_alt}-e", "0"),
        ("PoSgNeNo", f"{title_alt}-e", "0"),
        ("PoSgNeAc", f"{title_alt}-e", "0"),
        ("PoSgNeGe", f"{title_alt}-es", "0"),
        ("PoSgNeDa", f"{title_alt}-um", "0"),
        ("PoSgNeIs", f"{title_alt}-e", "0"),
        ("PoSgFeNo", f"{title_alt}-u", "0"),
        ("PoSgFeNo", f"{title_alt}-o", "1"),
        ("PoSgFeAc", f"{title_alt}-e", "0"),
        ("PoSgFeGe", f"{title_alt}-re", "0"),
        ("PoSgFeDa", f"{title_alt}-re", "0"),
        ("PoPlMaNo", f"{title_alt}-e", "0"),
        ("PoPlMaAc", f"{title_alt}-e", "0"),
        ("PoPlMaGe", f"{title_alt}-ra", "0"),
        ("PoPlMaDa", f"{title_alt}-um", "0"),
        ("PoPlNeNo", f"{title_alt}-u", "0"),
        ("PoPlNeNo", f"{title_alt}-o", "1"),
        ("PoPlNeAc", f"{title_alt}-u", "0"),
        ("PoPlNeAc", f"{title_alt}-o", "1"),
        ("PoPlNeGe", f"{title_alt}-ra", "0"),
        ("PoPlNeDa", f"{title_alt}-um", "0"),
        ("PoPlFeNo", f"{title_alt}-a", "0"),
        ("PoPlFeNo", f"{title_alt}-e", "0"),
        ("PoPlFeAc", f"{title_alt}-a", "0"),
        ("PoPlFeAc", f"{title_alt}-e", "0"),
        ("PoPlFeGe", f"{title_alt}-ra", "0"),
        ("PoPlFeDa", f"{title_alt}-um", "0"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(session, output_file, formhash, form_parts, func, prob)


def _gen_strong_gearu(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    formhash: dict[str, str],
) -> None:
    """
    Strong ``gearu`` paradigm (u-stem).

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        formhash: The form hash.

    """
    title_alt = re.sub(r".$", "", word.stem)
    title_alt = f"{word.prefix}-{title_alt}"
    forms = [
        ("PoSgMaNo", f"{title_alt}-u", "0"),
        ("PoSgMaNo", f"{title_alt}-o", "1"),
        ("PoSgMaAc", f"{title_alt}-one", "0"),
        ("PoSgMaGe", f"{title_alt}-wes", "0"),
        ("PoSgMaGe", f"{title_alt}-uwes", "1"),
        ("PoSgMaGe", f"{title_alt}-owes", "2"),
        ("PoSgMaDa", f"{title_alt}-wum", "0"),
        ("PoSgMaIs", f"{title_alt}-we", "0"),
        ("PoSgNeNo", f"{title_alt}-u", "0"),
        ("PoSgNeNo", f"{title_alt}-o", "1"),
        ("PoSgNeAc", f"{title_alt}-u", "0"),
        ("PoSgNeAc", f"{title_alt}-o", "1"),
        ("PoSgNeGe", f"{title_alt}-wes", "0"),
        ("PoSgNeDa", f"{title_alt}-wum", "0"),
        ("PoSgNeIs", f"{title_alt}-we", "0"),
        ("PoSgFeNo", f"{title_alt}-u", "0"),
        ("PoSgFeNo", f"{title_alt}-o", "1"),
        ("PoSgFeAc", f"{title_alt}-we", "0"),
        ("PoSgFeGe", f"{title_alt}-ore", "0"),
        ("PoSgFeDa", f"{title_alt}-ore", "0"),
        ("PoPlMaNo", f"{title_alt}-e", "0"),
        ("PoPlMaAc", f"{title_alt}-e", "0"),
        ("PoPlMaGe", f"{title_alt}-ora", "0"),
        ("PoPlMaDa", f"{title_alt}-wum", "0"),
        ("PoPlNeNo", f"{title_alt}-u", "0"),
        ("PoPlNeNo", f"{title_alt}-o", "1"),
        ("PoPlNeAc", f"{title_alt}-u", "0"),
        ("PoPlNeAc", f"{title_alt}-o", "1"),
        ("PoPlNeGe", f"{title_alt}-ora", "0"),
        ("PoPlNeDa", f"{title_alt}-wum", "0"),
        ("PoPlFeNo", f"{title_alt}-wa", "0"),
        ("PoPlFeNo", f"{title_alt}-we", "0"),
        ("PoPlFeAc", f"{title_alt}-wa", "0"),
        ("PoPlFeAc", f"{title_alt}-we", "0"),
        ("PoPlFeGe", f"{title_alt}-ora", "0"),
        ("PoPlFeDa", f"{title_alt}-wum", "0"),
    ]
    for func, form_parts, prob in forms:
        _adj_print(session, output_file, formhash, form_parts, func, prob)


def _gen_weak(
    session: GeneratorSession,
    output_file: io.StringIO,
    word: Word,
    paradigm: str,
) -> None:
    """
    Weak (definite) adjective forms for all adjectives.

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.
        paradigm: The paradigm.

    """
    bt_id = f"{word.nid:06d}"
    title_array = _build_weak_title_array(word, paradigm)
    base_fh = {
        "title": word.title,
        "stem": word.stem,
        "BT": bt_id,
        "wordclass": "adjective",
        "class1": "weak",
        "paradigm": "blinda",
        "wright": word.wright,
        "var": "",
        "paraID": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }
    if word.papart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "past"
    if word.pspart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "present"
    if word.pronoun == 1:
        base_fh["wordclass"] = "pronoun"
    for y, base in enumerate(title_array):
        prob = str(y)
        session.perl_probability = int(prob)
        forms = [
            ("PoSgMaNo", f"{base}-a"),
            ("PoSgMaAc", f"{base}-an"),
            ("PoSgMaGe", f"{base}-an"),
            ("PoSgMaDa", f"{base}-an"),
            ("PoSgNeNo", f"{base}-e"),
            ("PoSgNeAc", f"{base}-e"),
            ("PoSgNeGe", f"{base}-an"),
            ("PoSgNeDa", f"{base}-an"),
            ("PoSgFeNo", f"{base}-e"),
            ("PoSgFeAc", f"{base}-an"),
            ("PoSgFeGe", f"{base}-an"),
            ("PoSgFeDa", f"{base}-an"),
            ("PoPlMaNo", f"{base}-an"),
            ("PoPlMaAc", f"{base}-an"),
            ("PoPlMaGe", f"{base}-ra"),
            ("PoPlMaGe", f"{base}-ena"),
            ("PoPlMaDa", f"{base}-um"),
            ("PoPlNeNo", f"{base}-an"),
            ("PoPlNeAc", f"{base}-an"),
            ("PoPlNeGe", f"{base}-ra"),
            ("PoPlNeGe", f"{base}-ena"),
            ("PoPlNeDa", f"{base}-um"),
            ("PoPlFeNo", f"{base}-an"),
            ("PoPlFeAc", f"{base}-an"),
            ("PoPlFeGe", f"{base}-ra"),
            ("PoPlFeGe", f"{base}-ena"),
            ("PoPlFeDa", f"{base}-um"),
        ]
        for i, (func, form_parts) in enumerate(forms):
            fh = base_fh.copy()
            fh["function"] = func
            # Perl: no probability before first -ena (index 15); prob+1 from
            # first -ena onwards
            fh["probability"] = str(int(prob) + 1) if i >= 15 else ""  # noqa: PLR2004
            fh["form"] = _form_from_parts(form_parts)
            fh["formParts"] = form_parts.replace("\n", "")
            print_one_form(session, fh, output_file)


def _build_comparative_title_array(  # noqa: PLR0912
    word: Word,
    paradigm: str,
    use_perl_hash_order: bool,
) -> tuple[list[str], str]:
    """
    Build ``title_array`` for comparative, which is used to generate the
    comparative forms.

    Returns:
        A tuple containing the title_array and the comparative suffix.

    Args:
        word: The word.
        paradigm: The paradigm.
        use_perl_hash_order: Whether to use Perl ``keys %hash`` ordering
            semantics (full-flow parity mode).

    """
    vowel_regex = OENormalizer.VOWEL
    title_array: list[str] = []
    c = "0"
    stem = word.stem
    if stem == "g\u00f3d":
        title_array = [
            f"{word.prefix}-beter",
            f"{word.prefix}-betr",
            f"{word.prefix}-bettr",
            f"{word.prefix}-s\u00e9lr",
            f"{word.prefix}-selr",
        ]
    elif stem == "yfel":
        title_array = [f"{word.prefix}-wiers"]
    elif stem == "micel":
        title_array = [f"{word.prefix}-m\u00e1r"]
    elif stem == "lytel":
        title_array = [f"{word.prefix}-l\u01fdss"]
    else:
        c = "r"
        match = re.search(f"({vowel_regex}[eao]?)", stem)
        if match:
            vowels = OENormalizer.iumlaut([match.group(1)])
            for v in vowels:
                title_alt = re.sub(f"{vowel_regex}[eao]?", v, stem, count=1)
                title_array.append(f"{word.prefix}-{title_alt}")
                if re.search(r"u$", title_alt):
                    title_alt = re.sub(r"u$", "w", title_alt)
                    title_array.append(f"{word.prefix}-{title_alt}")
                if re.search(f"{vowel_regex}$", title_alt):
                    title_alt = re.sub(f"({vowel_regex})$", "", title_alt)
                    title_array.append(f"{word.prefix}-{title_alt}")
                if "hālig" in paradigm:
                    if (word.papart + word.pspart) == 0:
                        new_alt = re.sub(
                            f"({vowel_regex}.*){vowel_regex}(.*)$", r"\1\2", title_alt
                        )
                        if new_alt != title_alt:
                            title_array.append(f"{word.prefix}-{new_alt}")
                            title_alt = new_alt
                if re.search(r"h$", title_alt):
                    title_alt = re.sub(r"h$", "", title_alt)
                    title_array.append(f"{word.prefix}-{title_alt}")
    if use_perl_hash_order:
        return (_perl_hash_order(title_array), c)

    # Differential oracle mode expects deterministic lexical ordering here.
    seen: set[str] = set()
    unique: list[str] = []
    for t in title_array:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    unique.sort()
    return (unique, c)


def _gen_comparative(
    session: GeneratorSession, output_file: io.StringIO, word: Word
) -> None:
    """
    Comparative (Co) weak forms for all adjectives.

    Note:
        This is for the ``weak`` block in Perl.

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    use_perl_hash_order = len(session.adjectives) > len(session.words)
    title_array, c = _build_comparative_title_array(
        word, paradigm, use_perl_hash_order
    )
    bt_id = f"{word.nid:06d}"
    base_fh = {
        "title": word.title,
        "stem": word.stem,
        "BT": bt_id,
        "wordclass": "adjective",
        "class1": "weak",
        "paradigm": "blinda",
        "wright": word.wright,
        "var": "",
        "paraID": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }
    if word.papart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "past"
    if word.pspart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "present"
    for y, base in enumerate(title_array):
        prob = abs(y - 2)
        session.perl_probability = prob
        forms = [
            ("CoSgMaNo", f"{base}-{c}-a"),
            ("CoSgMaAc", f"{base}-{c}-an"),
            ("CoSgMaGe", f"{base}-{c}-an"),
            ("CoSgMaDa", f"{base}-{c}-an"),
            ("CoSgNeNo", f"{base}-{c}-e"),
            ("CoSgNeAc", f"{base}-{c}-e"),
            ("CoSgNeGe", f"{base}-{c}-an"),
            ("CoSgNeDa", f"{base}-{c}-an"),
            ("CoSgFeNo", f"{base}-{c}-e"),
            ("CoSgFeAc", f"{base}-{c}-an"),
            ("CoSgFeGe", f"{base}-{c}-an"),
            ("CoSgFeDa", f"{base}-{c}-an"),
            ("CoPlMaNo", f"{base}-{c}-an"),
            ("CoPlMaAc", f"{base}-{c}-an"),
            ("CoPlMaGe", f"{base}-{c}-a"),
            ("CoPlMaGe", f"{base}-{c}-ena"),
            ("CoPlMaDa", f"{base}-{c}-um"),
            ("CoPlNeNo", f"{base}-{c}-an"),
            ("CoPlNeAc", f"{base}-{c}-an"),
            ("CoPlNeGe", f"{base}-{c}-a"),
            ("CoPlNeGe", f"{base}-{c}-ena"),
            ("CoPlNeDa", f"{base}-{c}-um"),
            ("CoPlFeNo", f"{base}-{c}-an"),
            ("CoPlFeAc", f"{base}-{c}-an"),
            ("CoPlFeGe", f"{base}-{c}-a"),
            ("CoPlFeGe", f"{base}-{c}-ena"),
            ("CoPlFeDa", f"{base}-{c}-um"),
        ]
        for i, (func, form_parts) in enumerate(forms):
            fh = base_fh.copy()
            fh["function"] = func
            # Perl: no probability before first -ena (index 15); prob+1 from
            # first -ena onwards
            fh["probability"] = str(prob + 1) if i >= 15 else ""  # noqa: PLR2004
            fh["form"] = _form_from_parts(form_parts)
            fh["formParts"] = form_parts.replace("\n", "")
            print_one_form(session, fh, output_file)


def _build_superlative_title_array(  # noqa: PLR0912
    word: Word,
    paradigm: str,
    use_perl_hash_order: bool,
) -> tuple[list[str], str]:
    """
    Build ``title_array`` for superlative weak.

    Args:
        word: The word.
        paradigm: The paradigm.
        use_perl_hash_order: Whether to use Perl ``keys %hash`` ordering
            semantics (full-flow parity mode).

    Returns:
        A tuple containing the title array and the ``s`` suffix.

    """
    vowel_regex = OENormalizer.VOWEL
    title_array: list[str] = []
    s = "0"
    stem = word.stem
    if stem == "g\u00f3d":
        title_array = [
            f"{word.prefix}-betst",
            f"{word.prefix}-betest",
            f"{word.prefix}-best",
            f"{word.prefix}-s\u00e9lest",
        ]
    elif stem == "yfel":
        title_array = [f"{word.prefix}-wierrest", f"{word.prefix}-wyrst"]
    elif stem == "micel":
        title_array = [f"{word.prefix}-m\u01fdst"]
    elif stem == "lytel":
        title_array = [f"{word.prefix}-l\u01fdst"]
    else:
        s = "ost"
        match = re.search(f"({vowel_regex}[eao]?)", stem)
        if match:
            vowels = OENormalizer.iumlaut([match.group(1)])
            for v in vowels:
                title_alt = re.sub(f"{vowel_regex}[eao]?", v, stem, count=1)
                title_array.append(f"{word.prefix}-{title_alt}")
                if re.search(r"u$", title_alt):
                    title_alt = re.sub(r"u$", "w", title_alt)
                    title_array.append(f"{word.prefix}-{title_alt}")
                if re.search(f"{vowel_regex}$", title_alt):
                    title_alt = re.sub(f"({vowel_regex})$", "", title_alt)
                    title_array.append(f"{word.prefix}-{title_alt}")
                if "hālig" in paradigm:
                    if (word.papart + word.pspart) == 0:
                        new_alt = re.sub(
                            f"({vowel_regex}.*){vowel_regex}(.*)$", r"\1\2", title_alt
                        )
                        if new_alt != title_alt:
                            title_array.append(f"{word.prefix}-{new_alt}")
    if use_perl_hash_order:
        return (_perl_hash_order(title_array), s)

    # Differential oracle mode expects deterministic lexical ordering here.
    seen: set[str] = set()
    unique: list[str] = []
    for t in title_array:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    unique.sort()
    return (unique, s)


def _gen_superlative(
    session: GeneratorSession, output_file: io.StringIO, word: Word
) -> None:
    """
    Generate superlative adjective forms: weak (Sp) forms then strong (Sp)
    forms.

    Note:
        Matches Perl ``superlative`` block.

    Args:
        session: The generator session.
        output_file: The output file handle.
        word: The word.

    """
    paradigm = word.adj_paradigm[0] if word.adj_paradigm else ""
    use_perl_hash_order = len(session.adjectives) > len(session.words)
    title_array, s = _build_superlative_title_array(
        word, paradigm, use_perl_hash_order
    )
    bt_id = f"{word.nid:06d}"
    base_fh = {
        "title": word.title,
        "stem": word.stem,
        "BT": bt_id,
        "wordclass": "adjective",
        "class1": "weak",
        "paradigm": "blinda",
        "wright": word.wright,
        "var": "",
        "paraID": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }
    if word.papart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "past"
    if word.pspart == 1:
        base_fh["wordclass"] = "participle"
        base_fh["class2"] = "present"
    for y, base in enumerate(title_array):
        prob = abs(y - 2)
        session.perl_probability = prob
        forms = [
            ("SpSgMaNo", f"{base}-{s}-a"),
            ("SpSgMaAc", f"{base}-{s}-an"),
            ("SpSgMaGe", f"{base}-{s}-an"),
            ("SpSgMaDa", f"{base}-{s}-an"),
            ("SpSgNeNo", f"{base}-{s}-e"),
            ("SpSgNeAc", f"{base}-{s}-e"),
            ("SpSgNeGe", f"{base}-{s}-an"),
            ("SpSgNeDa", f"{base}-{s}-an"),
            ("SpSgFeNo", f"{base}-{s}-e"),
            ("SpSgFeAc", f"{base}-{s}-an"),
            ("SpSgFeGe", f"{base}-{s}-an"),
            ("SpSgFeDa", f"{base}-{s}-an"),
            ("SpPlMaNo", f"{base}-{s}-an"),
            ("SpPlMaAc", f"{base}-{s}-an"),
            ("SpPlMaGe", f"{base}-{s}-a"),
            ("SpPlMaGe", f"{base}-{s}-ena"),
            ("SpPlMaDa", f"{base}-{s}-um"),
            ("SpPlNeNo", f"{base}-{s}-an"),
            ("SpPlNeAc", f"{base}-{s}-an"),
            ("SpPlNeGe", f"{base}-{s}-a"),
            ("SpPlNeGe", f"{base}-{s}-ena"),
            ("SpPlNeDa", f"{base}-{s}-um"),
            ("SpPlFeNo", f"{base}-{s}-an"),
            ("SpPlFeAc", f"{base}-{s}-an"),
            ("SpPlFeGe", f"{base}-{s}-a"),
            ("SpPlFeGe", f"{base}-{s}-ena"),
            ("SpPlFeDa", f"{base}-{s}-um"),
        ]
        for i, (func, form_parts) in enumerate(forms):
            fh = base_fh.copy()
            fh["function"] = func
            # Perl: no probability before first -ena (index 15); prob+1 from
            # first -ena onwards
            fh["probability"] = str(prob + 1) if i >= 15 else ""  # noqa: PLR2004
            fh["form"] = _form_from_parts(form_parts)
            fh["formParts"] = form_parts.replace("\n", "")
            print_one_form(session, fh, output_file)
    # Superlative strong forms - use same ``title_array``, ``class1=strong``
    paradigm_val = word.adj_paradigm[0] if word.adj_paradigm else ""
    strong_fh = {
        "title": word.title,
        "stem": word.stem,
        "BT": bt_id,
        "wordclass": "adjective",
        "class1": "strong",
        "paradigm": paradigm_val,
        "wright": word.wright,
        "var": "",
        "paraID": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }
    if word.papart == 1:
        strong_fh["wordclass"] = "participle"
        strong_fh["class2"] = "past"
    if word.pspart == 1:
        strong_fh["wordclass"] = "participle"
        strong_fh["class2"] = "present"
    for y, base in enumerate(title_array):
        prob = abs(y - 2)
        # Match Perl superlative strong exactly (SpSgMaAc has -ne,-0; SpPlFeNo
        # has -a,-e,-0; etc.)
        forms = [
            ("SpSgMaNo", f"{base}-{s}-0"),
            ("SpSgMaAc", f"{base}-{s}-ne"),
            ("SpSgMaAc", f"{base}-{s}-0"),
            ("SpSgMaGe", f"{base}-{s}-es"),
            ("SpSgMaDa", f"{base}-{s}-um"),
            ("SpSgMaDa", f"{base}-{s}-0"),
            ("SpSgNeNo", f"{base}-{s}-0"),
            ("SpSgNeAc", f"{base}-{s}-0"),
            ("SpSgNeGe", f"{base}-{s}-es"),
            ("SpSgNeDa", f"{base}-{s}-um"),
            ("SpSgNeDa", f"{base}-{s}-0"),
            ("SpSgFeNo", f"{base}-{s}-0"),
            ("SpSgFeAc", f"{base}-{s}-e"),
            ("SpSgFeGe", f"{base}-{s}-re"),
            ("SpSgFeGe", f"{base}-{s}-0"),
            ("SpSgFeDa", f"{base}-{s}-re"),
            ("SpSgFeDa", f"{base}-{s}-0"),
            ("SpPlMaNo", f"{base}-{s}-e"),
            ("SpPlMaNo", f"{base}-{s}-0"),
            ("SpPlMaAc", f"{base}-{s}-e"),
            ("SpPlMaAc", f"{base}-{s}-0"),
            ("SpPlMaGe", f"{base}-{s}-ra"),
            ("SpPlMaGe", f"{base}-{s}-0"),
            ("SpPlMaDa", f"{base}-{s}-um"),
            ("SpPlNeNo", f"{base}-{s}-e"),
            ("SpPlNeNo", f"{base}-{s}-0"),
            ("SpPlNeAc", f"{base}-{s}-e"),
            ("SpPlNeAc", f"{base}-{s}-0"),
            ("SpPlNeGe", f"{base}-{s}-ra"),
            ("SpPlNeGe", f"{base}-{s}-0"),
            ("SpPlNeDa", f"{base}-{s}-um"),
            ("SpPlFeNo", f"{base}-{s}-a"),
            ("SpPlFeNo", f"{base}-{s}-e"),
            ("SpPlFeNo", f"{base}-{s}-0"),
            ("SpPlFeAc", f"{base}-{s}-a"),
            ("SpPlFeAc", f"{base}-{s}-e"),
            ("SpPlFeAc", f"{base}-{s}-0"),
            ("SpPlFeGe", f"{base}-{s}-ra"),
            ("SpPlFeGe", f"{base}-{s}-0"),
            ("SpPlFeDa", f"{base}-{s}-um"),
        ]
        # Perl superlative strong: formhash has no probability initially;
        # indices 0,1 get empty; indices 2+ either set prob+1/prob+2 or carry
        # over from previous form.
        # Explicit sets from create_dict31.pl:
        # prob+1 at 2,5,10,14,16,18,20,22,25,27,32,35;
        # prob+2 at 29,33,36,38.
        prob_plus_1 = {2, 5, 10, 14, 16, 18, 20, 22, 25, 27, 32, 35}
        prob_plus_2 = {29, 33, 36, 38}
        carried = ""
        for i, (func, form_parts) in enumerate(forms):
            fh = strong_fh.copy()
            fh["function"] = func
            if i < 2:  # noqa: PLR2004
                fh["probability"] = ""
            elif i in prob_plus_1:
                carried = str(prob + 1)
                fh["probability"] = carried
            elif i in prob_plus_2:
                carried = str(prob + 2)
                fh["probability"] = carried
            else:
                fh["probability"] = carried
            fh["form"] = _form_from_parts(form_parts)
            fh["formParts"] = form_parts.replace("\n", "")
            print_one_form(session, fh, output_file)


def generate_adjforms(session: GeneratorSession, output_file: io.StringIO) -> None:  # noqa: PLR0912
    """
    Generate adjective forms.

    Note:
        Port of Perl ``generate_adjforms``.

    Args:
        session: The generator session.
        output_file: The output file handle.

    """
    # Perl main flow calls generate_adjforms on a mutable adjective pool that
    # starts as all words and then gets additional generated participles.
    words = [
        w
        for w in session.adjectives
        if (w.adjective == 1 or (w.pspart + w.papart) > 0) and w.numeral != 1
    ]
    for word in words:
        paradigm = (
            word.adj_paradigm[0]
            if word.adj_paradigm
            else ("wilde" if (word.pspart or word.papart) else "")
        )
        bt_id = f"{word.nid:06d}"
        formhash = {
            "title": word.title,
            "stem": word.stem,
            "BT": bt_id,
            "wordclass": "adjective",
            "class1": "strong",
            "paradigm": paradigm,
            "wright": word.wright,
            "var": "",
            "paraID": "",
            "class2": "",
            "class3": "",
            "comment": "",
        }
        if word.pronoun == 1:
            formhash["wordclass"] = "pronoun"
        # Manig: papart + short stem -> override paradigm
        if "manig" in paradigm or (
            word.papart == 1 and not OENormalizer.stem_length(word.stem)
        ):
            if word.papart == 1:
                word.adj_paradigm = ["manig"]
                formhash["wordclass"] = "participle"
                formhash["class2"] = "past"
                formhash["paradigm"] = "manig"
            _gen_strong_manig(session, output_file, word, formhash)
        elif (
            "hālig" in paradigm
            or (word.papart == 1 and OENormalizer.stem_length(word.stem))
        ):
            if word.papart == 1:
                word.adj_paradigm = ["hālig"]
                formhash["wordclass"] = "participle"
                formhash["class2"] = "past"
                formhash["paradigm"] = "halig"
            _gen_strong_halig(session, output_file, word, formhash)
        elif "wilde" in paradigm or word.pspart == 1:
            if word.pspart == 1:
                word.adj_paradigm = ["wilde"]
                formhash["wordclass"] = "participle"
                formhash["class2"] = "present"
                formhash["paradigm"] = "wilde"
            _gen_strong_wilde(session, output_file, word, formhash)
        elif re.search(r"gl\u00e6d|glæd|til", paradigm, re.IGNORECASE):
            _gen_strong_glaed_til(session, output_file, word, formhash)
        elif "blind" in paradigm:
            _gen_strong_blind(session, output_file, word, formhash)
        elif re.search(r"hēah|weorh", paradigm):
            _gen_strong_heah_thweorh(session, output_file, word, formhash)
        elif "gearu" in paradigm:
            _gen_strong_gearu(session, output_file, word, formhash)
        # else: no strong paradigm match, but still generate weak forms
        _gen_weak(session, output_file, word, paradigm)

        # Comparative and Superlative (only for adjectives, not numerals or pronouns)
        if word.numeral == 0 and word.pronoun == 0:
            _gen_comparative(session, output_file, word)
            _gen_superlative(session, output_file, word)

    # Full-flow create_dict31 behavior carries a shared $probability into
    # generate_numforms after adjective generation has run.
    session.enable_num_probability_carry = True
