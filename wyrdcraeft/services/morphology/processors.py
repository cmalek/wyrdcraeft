import re

from .models import VerbParadigm, Word
from .session import GeneratorSession
from .text_utils import OENormalizer

R_STEM_PARADIGM_BY_STEM = {
    "fæder": "fæder",
    "brōþor": "brōþor",
    "mōdor": "mōdor",
    "dōhtor": "dōhtor",
    "sweostor": "sweostor",
}


def _wright_has_token(wright: str, token: str) -> bool:
    """
    Check whether ``wright`` contains the exact semicolon-delimited token.

    Args:
        wright: Wright code string.
        token: Token to match.

    Returns:
        ``True`` if token is present as an exact token; else ``False``.

    """
    return bool(re.search(rf"(?:^|;){re.escape(token)}(?:;|$)", wright))


def _get_r_stem_paradigm(word: Word) -> str | None:
    """
    Resolve opt-in r-stem paradigm for a word.

    Classification uses:
    - exact Wright token ``415``, and/or
    - explicit lexeme stem allowlist.

    Args:
        word: The word to classify.

    Returns:
        Canonical r-stem paradigm label when matched, otherwise ``None``.

    """
    stem_match = word.stem in R_STEM_PARADIGM_BY_STEM
    wright_match = _wright_has_token(word.wright, "415")
    if not (stem_match or wright_match):
        return None
    return R_STEM_PARADIGM_BY_STEM.get(word.stem)


def _assign_verb_by_example(
    words: list[Word], vparadigms: list[VerbParadigm]
) -> list["Word"]:
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
    words: list["Word"], assigned_words: list["Word"], strict: bool = False
) -> list["Word"]:
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
) -> list["Word"]:
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
) -> list["Word"]:
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
    words: list["Word"], assigned_words: list["Word"]
) -> list["Word"]:
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
    words: list["Word"], assigned_words: list["Word"], prefix_re: str
) -> list["Word"]:
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
    words: list["Word"], session: GeneratorSession
) -> list["Word"]:
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


def _assign_verb_fallback(words: list["Word"], session: GeneratorSession) -> None:
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

    # Phase 1: Exact Match (class restricted)
    assigned = _assign_verb_by_example(verbs, vparadigms)

    # Phase 2: Similarity to Assigned (class restricted)
    assigned.extend(_assign_verb_by_stem(verbs, assigned, strict=True))

    # Phase 3: Wright Paragraphs
    assigned.extend(_assign_verb_by_wright(verbs, vparadigms))

    # Phase 4: Similarity to Assigned (class relaxed)
    assigned.extend(_assign_verb_by_stem(verbs, assigned, strict=False))

    # Phase 5: Advanced Stem (Prefix + i/y equivalence, class relaxed)
    assigned.extend(_assign_verb_by_advanced_stem(verbs, assigned, prefix_re))

    # Phase 6: Heuristics
    assigned.extend(_assign_verb_heuristics(verbs, session))

    # Phase 7: Diacritics Disregarded (NO class restriction)
    assigned.extend(_assign_verb_by_diacritics(verbs, assigned))

    # Phase 8: Advanced Diacritics (Prefix + i/y equivalence + diacritics, NO
    # class restriction)
    assigned.extend(_assign_verb_by_advanced_diacritics(verbs, assigned, prefix_re))

    # Phase 9: Fallback
    _assign_verb_fallback(verbs, session)


def set_adj_paradigm(session: GeneratorSession) -> None:  # noqa: PLR0912, PLR0915
    """Set the adjective paradigm."""
    # Perl ``set_adj_paradigm`` iterates over the full word list and returns it.
    # Keep a dedicated mutable pool (separate list, same objects) for
    # ``generate_adjforms`` so verb-generated participles can be appended there.
    adjectives = session.words
    session.adjectives = list(adjectives)

    for word in adjectives:
        word.adj_paradigm = []
        if "feald" in word.stem:
            word.numeral = 0

        wright = word.wright
        if "425" in wright:
            if re.search(r"[\u00E6\u00C6]|ea", word.stem):
                word.adj_paradigm.append("gl\u00e6d")
            else:
                word.adj_paradigm.append("til")
        elif "426" in wright:
            word.adj_paradigm.append("blind")
        elif "428" in wright:
            word.adj_paradigm.append("h\u00e9ah")
        elif "430" in wright:
            word.adj_paradigm.append("manig")
        elif "431" in wright:
            word.adj_paradigm.append("h\u00e1lig")
        elif "434" in wright:
            word.adj_paradigm.append("wilde")
        elif "436" in wright:
            word.adj_paradigm.append("gearu")
        elif "437" in wright:
            word.adj_paradigm.append("blind")

        if "\u00fe" + "weorh" in word.stem:  # þweorh
            word.adj_paradigm = ["\u00fe" + "weorh"]

    # Stem comparison
    for word in adjectives:
        if not word.adj_paradigm:
            for other in adjectives:
                if other.adj_paradigm and word.stem == other.stem:
                    word.adj_paradigm = [other.adj_paradigm[0]]
                    break

    # Heuristics
    for word in adjectives:
        if not word.adj_paradigm:
            if re.search(r"(sum|lic|l\u00EDc|isc)$", word.stem):
                word.adj_paradigm.append("til")
            elif re.search(r"(cund|feald|f\u00E6st|l\u00E9as|full|iht)$", word.stem):
                word.adj_paradigm.append("blind")
            elif re.search(r"(ihte|b\u01FDre|ede|wende)$", word.stem):
                word.adj_paradigm.append("wilde")
            elif word.syllables < 2:  # noqa: PLR2004
                if not OENormalizer.stem_length(word.stem):
                    if re.search(r"[\u00E6\u00C6]|ea", word.stem):
                        word.adj_paradigm.append("gl\u00e6d")
                    else:
                        word.adj_paradigm.append("til")
                elif re.search(f"{OENormalizer.VOWEL}h$", word.stem):
                    word.adj_paradigm.append("h\u00e9ah")
                elif re.search(f"{OENormalizer.CONSONANT}h$", word.stem):
                    word.adj_paradigm.append("\u00fe" + "weorh")
                else:
                    word.adj_paradigm.append("blind")
            elif word.stem.endswith(("u", "o")):
                word.adj_paradigm.append("gearu")
            elif word.stem.endswith("e"):
                word.adj_paradigm.append("wilde")
            elif OENormalizer.stem_length(word.stem):
                word.adj_paradigm.append("h\u00e1lig")
            else:
                word.adj_paradigm.append("manig")


def set_noun_paradigm(session: GeneratorSession) -> None:  # noqa: PLR0912, PLR0915
    """Set the noun paradigm."""
    nouns = session.nouns
    prefix_re = session.prefix_regex
    vowel_re = OENormalizer.VOWEL
    lvowel_re = OENormalizer.LVOWEL

    assigned: list[Word] = []

    for word in nouns:
        word.noun_paradigm = []
        wright = word.wright
        if session.enable_r_stem_nouns:
            r_stem_paradigm = _get_r_stem_paradigm(word)
            if r_stem_paradigm:
                word.noun_paradigm.append(r_stem_paradigm)
                assigned.append(word)
                continue
        if re.search(r"335|339|387|354|386|337|340|341|352", wright):
            word.noun_paradigm.append("st\u00e1n")
        elif "356" in wright:
            word.noun_paradigm.append("cynn")
        elif re.search(r"343|349|348", wright):
            word.noun_paradigm.append("word")
        elif re.search(r"344|350|357|393|358", wright):
            word.noun_paradigm.append("hof")
        elif "336" in wright:
            word.noun_paradigm.append("d\u00e6g")
        elif "345" in wright:
            word.noun_paradigm.append("f\u00e6t")
        elif re.search(r"367|368|373|376|390|366|372|370|375|378", wright):
            word.noun_paradigm.append("\u00e1r")
        elif "383" in wright:
            word.noun_paradigm.append("strengu")
        elif "397" in wright:
            word.noun_paradigm.append("feld")
        elif "398" in wright:
            if "hand" not in word.noun_paradigm:
                word.noun_paradigm.append("hand")
            if "duru" not in word.noun_paradigm:
                word.noun_paradigm.append("duru")
        elif "396" in wright:
            word.noun_paradigm.append("sunu")
        elif re.search(r"359|360", wright):
            word.noun_paradigm.append("bearu")
        elif re.search(r"362|363", wright):
            word.noun_paradigm.append("bealu")
        elif re.search(r"380|381", wright):
            word.noun_paradigm.append("beadu")
        elif "401" in wright:
            word.noun_paradigm.append("guma")
        elif "402" in wright:
            word.noun_paradigm.append("fr\u00e9a")
        elif "404" in wright:
            word.noun_paradigm.append("tunge")
        elif "405" in wright:
            word.noun_paradigm.append("b\u00e9o")
        elif "407" in wright:
            word.noun_paradigm.append("\u00e9age")
        elif "418" in wright:
            word.noun_paradigm.append("w\u00edgend")

        if word.noun_paradigm:
            assigned.append(word)

    # Simple stem comparison
    for word in nouns:
        if not word.noun_paradigm:
            for other in assigned:
                if word.stem == other.stem:
                    word.noun_paradigm = [other.noun_paradigm[0]]
                    assigned.append(word)
                    break

    # Advanced stem comparison
    for word in nouns:
        if not word.noun_paradigm:
            mod_match1 = re.sub(f"^({prefix_re})-?(.*)", r"\2", word.stem)
            mod_match2 = mod_match1.replace("y", "i")
            mod_match3 = mod_match1.replace("i", "y")
            mod_match4 = mod_match2.replace("i", "ie")

            for other in assigned:
                if other.stem in [mod_match1, mod_match2, mod_match3, mod_match4]:
                    word.noun_paradigm = [other.noun_paradigm[0]]
                    assigned.append(word)
                    break

    # Heuristics
    for i, word in enumerate(nouns):
        if not word.noun_paradigm:
            v_match = re.search(
                f"^({vowel_re}?{vowel_re}?.*?)({vowel_re}{vowel_re}?)", word.stem
            )
            vowel = v_match.group(2) if v_match else ""

            if word.stem.endswith("a"):
                if re.search(lvowel_re, vowel):
                    word.noun_paradigm.append("fr\u00e9a")
                else:
                    word.noun_paradigm.append("guma")
            if word.stem.endswith("e"):
                if word.n_fem == 1:
                    word.noun_paradigm.append("tunge")
                if word.n_masc == 1:
                    word.noun_paradigm.append("st\u00e1n")
                if word.n_neut == 1:
                    word.noun_paradigm.append("hof")
            if word.stem.endswith("nd") and word.n_masc == 1:
                word.noun_paradigm.append("w\u00edgend")
            if re.search(r"(els|scipe)$", word.stem):
                word.noun_paradigm.append("st\u00e1n")
            if word.stem.endswith("incel"):
                word.noun_paradigm.append("hof")
            if re.search(r"(ness|niss|nyss|ung)$", word.stem):
                word.noun_paradigm.append("\u00e1r")

            # Buggy indexing matching Perl
            buggy_word = session.words[i]
            if re.search(r"[\u00e6\u01fd]", vowel) and buggy_word.syllables < 2:  # noqa: PLR2004
                if word.n_masc == 1:
                    word.noun_paradigm.append("d\u00e6g")
                if word.n_neut == 1:
                    word.noun_paradigm.append("f\u00e6t")

            if word.noun_paradigm:
                assigned.append(word)

    # Second stem comparison
    for word in nouns:
        if not word.noun_paradigm:
            for other in assigned:
                if word.stem == other.stem:
                    word.noun_paradigm = [other.noun_paradigm[0]]
                    assigned.append(word)
                    break

    # Second advanced stem comparison
    for word in nouns:
        if not word.noun_paradigm:
            mod_match1 = re.sub(f"^({prefix_re})-?(.*)", r"\2", word.stem)
            mod_match2 = mod_match1.replace("y", "i")
            mod_match3 = mod_match1.replace("i", "y")
            mod_match4 = mod_match2.replace("i", "ie")

            for other in assigned:
                if other.stem in [mod_match1, mod_match2, mod_match3, mod_match4]:
                    word.noun_paradigm = [other.noun_paradigm[0]]
                    assigned.append(word)
                    break

    # Final fallback
    for i, word in enumerate(nouns):
        if not word.noun_paradigm:
            if word.n_masc == 1 or word.n_uncert == 1:
                word.noun_paradigm.append("st\u00e1n")

            # Buggy indexing matching Perl
            buggy_word = session.words[i]
            if word.n_neut == 1:
                if OENormalizer.stem_length(buggy_word.stem):
                    word.noun_paradigm.append("word")
                else:
                    word.noun_paradigm.append("hof")

            if word.n_fem == 1:
                word.noun_paradigm.append("\u00e1r")
