from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import VerbParadigm, Word

    from ..session import GeneratorSession


def _assign_verb_by_example(
    words: list[Word], vparadigms: list[VerbParadigm]
) -> list[Word]:
    """
    Step 1: Assign verbs that are paradigm examples themselves.

    Args:
        words: The words to assign.
        vparadigms: The verb paradigms.

    Returns:
        The newly assigned words.

    """
    assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue
        for vp in vparadigms:
            if word.stem == vp.title:
                match = False
                if (
                    (vp.type == "w" and word.vb_weak == 1)
                    or (vp.type == "pp" and word.vb_pretpres == 1)
                    or (vp.type == "a" and word.vb_anomalous == 1)
                    or (vp.type == "s" and word.vb_strong == 1)
                ):
                    match = True
                if match:
                    word.vb_paradigm.append(vp)
        if word.vb_paradigm:
            assigned.append(word)
    return assigned


def _assign_verb_by_stem(
    words: list[Word], assigned_words: list[Word], strict: bool = False
) -> list[Word]:
    """
    Step 2 & 4: Assign verbs by simple stem comparison with already assigned verbs.

    Args:
        words: The words to assign.
        assigned_words: The already assigned words.
        strict: Whether to use strict matching.

    Returns:
        The newly assigned words.

    """
    newly_assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue
        for assigned in assigned_words:
            if word.stem == assigned.stem:
                match = False
                if strict:
                    # Perl Phase 2: only strong match or uncertain
                    if word.vb_strong == assigned.vb_strong or word.vb_uncertain == 1:
                        match = True
                elif (
                    word.vb_strong == assigned.vb_strong
                    or word.vb_weak == assigned.vb_weak
                    or word.vb_pretpres == assigned.vb_pretpres
                    or word.vb_anomalous == assigned.vb_anomalous
                    or word.vb_uncertain == 1
                ):
                    # Perl Phase 4: any class match or uncertain
                    match = True
                if match:
                    word.vb_paradigm = assigned.vb_paradigm[:]
                    newly_assigned.append(word)
                    break
    return newly_assigned


def _assign_verb_by_advanced_stem(
    words: list[Word], assigned_words: list[Word], prefix_re: str
) -> list[Word]:
    """
    Step 5: Assign verbs by advanced stem comparison (prefixes, i/y/ie).

    Args:
        words: The words to assign.
        assigned_words: The already assigned words.
        prefix_re: The prefix regular expression.

    """
    newly_assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue
        # Discover unmarked second prefix
        mod_match1 = re.sub(f"^({prefix_re})-?(.*)", r"\2", word.stem)
        mod_match2 = mod_match1.replace("y", "i")
        mod_match3 = mod_match1.replace("i", "y")
        mod_match4 = mod_match2.replace("i", "ie")

        for assigned in assigned_words:
            if assigned.stem in [mod_match1, mod_match2, mod_match3, mod_match4]:
                match = False
                # Perl Phase 5: any class match or uncertain
                if (
                    word.vb_strong == assigned.vb_strong
                    or word.vb_weak == assigned.vb_weak
                    or word.vb_pretpres == assigned.vb_pretpres
                    or word.vb_anomalous == assigned.vb_anomalous
                    or word.vb_uncertain == 1
                ):
                    match = True
                if match:
                    word.vb_paradigm = assigned.vb_paradigm[:]
                    word.stem = mod_match1  # Update stem as discovered in Perl
                    newly_assigned.append(word)
                    break
    return newly_assigned


def _assign_verb_by_wright(
    words: list[Word], vparadigms: list[VerbParadigm]
) -> list[Word]:
    """
    Step 4: Assign verbs by Wright paragraphs.

    Args:
        words: The words to assign.
        vparadigms: The verb paradigms.

    Returns:
        The newly assigned words.

    """
    newly_assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue
        for vp in vparadigms:
            if (
                vp.wright != "0"
                and word.wright not in {"NULL", "null"}
                and re.search(vp.wright, word.wright)
            ):
                matches = re.findall(vp.wright, word.wright)
                for _ in matches:
                    word.vb_paradigm.append(vp)
        if word.vb_paradigm:
            newly_assigned.append(word)
    return newly_assigned


def _assign_verb_by_diacritics(
    words: list[Word], assigned_words: list[Word]
) -> list[Word]:
    """
    Step 6.5: Assign verbs by stem comparison disregarding diacritics.

    Args:
        words: The words to assign.
        assigned_words: The already assigned words.

    Returns:
        The newly assigned words.

    """
    newly_assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue
        stem_dia = OENormalizer.remove_dia_perl(word.stem)
        for assigned in assigned_words:
            stem_dia_assigned = OENormalizer.remove_dia_perl(assigned.stem)
            if stem_dia == stem_dia_assigned:
                word.vb_paradigm = assigned.vb_paradigm[:]
                newly_assigned.append(word)
                break
    return newly_assigned


def _assign_verb_by_advanced_diacritics(
    words: list[Word], assigned_words: list[Word], prefix_re: str
) -> list[Word]:
    """
    Step 6.6: Assign verbs by advanced stem comparison disregarding diacritics.

    Args:
        words: The words to assign.
        assigned_words: The already assigned words.
        prefix_re: The prefix regular expression.

    Returns:
        The newly assigned words.

    """
    newly_assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue
        mod_match1 = re.sub(f"^({prefix_re})-?(.*)", r"\2", word.stem)
        mod_match1 = OENormalizer.remove_dia_perl(mod_match1)
        mod_match2 = mod_match1.replace("y", "i")
        mod_match3 = mod_match1.replace("i", "y")
        mod_match4 = mod_match2.replace("i", "ie")

        for assigned in assigned_words:
            stem_dia_assigned = OENormalizer.remove_dia_perl(assigned.stem)
            if stem_dia_assigned in [mod_match1, mod_match2, mod_match3, mod_match4]:
                word.vb_paradigm = assigned.vb_paradigm[:]
                word.stem = re.sub(f"^({prefix_re})-?(.*)", r"\2", word.stem)
                newly_assigned.append(word)
                break
    return newly_assigned


def _assign_verb_heuristics(  # noqa: PLR0912, PLR0915
    words: list[Word], session: GeneratorSession
) -> list[Word]:
    """
    Step 7: Assign verbs by heuristics (Mitchell).

    Args:
        words: The words to assign.
        session: The generator session.

    Returns:
        The newly assigned words.

    """
    newly_assigned: list[Word] = []
    for word in words:
        if word.vb_paradigm:
            continue

        # STRONG VERBS heuristics
        if word.vb_strong == 1:
            v_match = re.search(
                f"^({OENormalizer.VOWEL}*?.*?)({OENormalizer.VOWEL}+)", word.stem
            )
            if v_match:
                pre_vowel = v_match.group(1)
                vowel = v_match.group(2)
                pv_match = re.search(
                    f"^{OENormalizer.VOWEL}*?.*?{OENormalizer.VOWEL}+({OENormalizer.CONSONANT}.*?){OENormalizer.VOWEL}",
                    word.stem,
                )
                post_vowel = pv_match.group(1) if pv_match else ""
                post_vowel_length = len(post_vowel)
                assigned_id = None

                if vowel in ["\u00ed", "\u00fd"] and post_vowel_length == 1:
                    assigned_id = "1"
                    if post_vowel.startswith("\u00fe"):
                        assigned_id = "2"
                    elif post_vowel.startswith("s"):
                        assigned_id = "3"
                elif vowel == "\u00e9o" and post_vowel_length == 1:
                    assigned_id = "5"
                    if post_vowel.startswith("s"):
                        assigned_id = "6"
                elif vowel == "\u00fa" and post_vowel_length == 1:
                    assigned_id = "9"
                elif vowel == "e" and re.match(r"^l.", post_vowel):
                    assigned_id = "13"
                elif vowel == "e" and post_vowel_length == 2:  # noqa: PLR2004
                    assigned_id = "16"
                elif vowel == "e" and re.match(r"^[rl]$", post_vowel):
                    assigned_id = "19"
                elif vowel == "e" and re.match(r"^[ptcdgfs\u00FE]$", post_vowel):
                    assigned_id = "22"
                elif vowel == "a" and post_vowel_length == 1:
                    assigned_id = "31"
                elif vowel == "eo" and re.match(r"^[rh].", post_vowel):
                    assigned_id = "14"
                elif pre_vowel == "g" and vowel == "ie" and post_vowel_length == 2:  # noqa: PLR2004
                    assigned_id = "63"
                elif vowel in ["i", "y", "ie"] and re.match(r"^[nm].", post_vowel):
                    assigned_id = "10"
                elif vowel == "\u00e1" and post_vowel_length == 1:
                    assigned_id = "40"
                elif vowel == "\u00f3" and post_vowel_length == 1:
                    assigned_id = "48"

                if assigned_id:
                    vp = session.verb_paradigms.get(assigned_id)
                    if vp:
                        word.vb_paradigm.append(vp)

        # WEAK VERBS heuristics
        elif word.vb_weak == 1:
            v_match = re.search(
                f"^({OENormalizer.VOWEL}*?.*?)({OENormalizer.VOWEL}+)", word.stem
            )
            if v_match:
                vowel = v_match.group(2)
                pv_match = re.search(
                    f"^{OENormalizer.VOWEL}*?.*?{OENormalizer.VOWEL}+({OENormalizer.CONSONANT}.*?){OENormalizer.VOWEL}",
                    word.stem,
                )
                post_vowel = pv_match.group(1) if pv_match else ""
                assigned_id = None

                if word.stem.endswith(("rian", "rigan", "rgan")):
                    assigned_id = "73"
                    if word.stem.endswith(("swarian", "gadrian", "timbrian")):
                        assigned_id = "87"
                elif re.search(
                    f"({OENormalizer.VOWEL})({OENormalizer.CONSONANT}*)(ian|igan)$",
                    word.stem,
                ):
                    assigned_id = "87"
                elif re.match(r"^[\u006Caeiyou]$", vowel) and re.match(
                    f"^({OENormalizer.CONSONANT})\\1$", post_vowel
                ):
                    assigned_id = "74"
                    if word.stem.endswith(("fyllan", "fillan")):
                        assigned_id = "76"

                if assigned_id:
                    vp = session.verb_paradigms.get(assigned_id)
                    if vp:
                        word.vb_paradigm.append(vp)

        if word.vb_paradigm:
            newly_assigned.append(word)
    return newly_assigned


def _assign_verb_fallback(words: list[Word], session: GeneratorSession) -> None:
    """
    Step 8: Final fallback for verbs.

    Args:
        words: The words to assign.
        session: The generator session.

    """
    for word in words:
        if word.vb_paradigm:
            continue
        if word.vb_strong == 1:
            vp = session.verb_paradigms.get("13")
        else:
            vp = session.verb_paradigms.get("76")
        if vp:
            word.vb_paradigm.append(vp)


def set_verb_paradigm(session: GeneratorSession) -> None:
    """
    Set the verb paradigm.

    Note:
        This function matches Perl's set_verb_paradigm exactly.

    Args:
        session: The generator session.

    """
    vparadigms = list(session.verb_paradigms.values())
    verbs = session.verbs
    prefix_re = session.prefix_regex

    # Clear existing paradigms
    for word in verbs:
        word.vb_paradigm = []

    assigned: list[Word] = []
    phase_steps = [
        ("exact_match_strict", lambda: _assign_verb_by_example(verbs, vparadigms)),
        (
            "stem_similarity_strict",
            lambda: _assign_verb_by_stem(verbs, assigned, strict=True),
        ),
        ("wright_match", lambda: _assign_verb_by_wright(verbs, vparadigms)),
        (
            "stem_similarity_relaxed",
            lambda: _assign_verb_by_stem(verbs, assigned, strict=False),
        ),
        (
            "advanced_stem_relaxed",
            lambda: _assign_verb_by_advanced_stem(verbs, assigned, prefix_re),
        ),
        ("heuristics_mitchell", lambda: _assign_verb_heuristics(verbs, session)),
        # Quirk: match without class restriction for parity with Perl ordering.
        ("diacritics_relaxed", lambda: _assign_verb_by_diacritics(verbs, assigned)),
        (
            "advanced_diacritics_relaxed",
            lambda: _assign_verb_by_advanced_diacritics(verbs, assigned, prefix_re),
        ),
    ]
    for _phase_name, phase in phase_steps:
        assigned.extend(phase())

    # Phase 9: Fallback
    _assign_verb_fallback(verbs, session)
