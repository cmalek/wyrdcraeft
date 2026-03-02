from pathlib import Path

from wyrdcraeft.models.morphology import (
    ManualForm,
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
)

from .text_utils import OENormalizer


def load_dictionary(path: str) -> list[Word]:
    """
    Load the dictionary from a file.

    Args:
        path: The path to the dictionary file.

    Returns:
        A list of :class:`~wyrdcraeft.models.morphology.Word` objects.

    """
    _path = Path(path)

    words = []
    with _path.open(encoding="utf-8") as f:
        for line in f:
            # Perl: $line = move_accents(eth2thorn(lc($line)))
            _line = OENormalizer.move_accents(OENormalizer.eth2thorn(line.lower()))
            parts = _line.strip("\r\n").split("\t")
            if len(parts) < 23:  # noqa: PLR2004
                continue

            mypspa = 0
            mypp = 0
            if parts[7] == "1":
                if parts[1].endswith("nde"):
                    mypspa = 1
                else:
                    mypp = 1

            def to_int(val: str) -> int:
                if not val or val.lower() == "null":
                    return 0
                try:
                    return int(val)
                except ValueError:
                    return 0

            word = Word(
                nid=to_int(parts[0]),
                title=parts[1],
                wright=parts[2],
                noun=to_int(parts[3]),
                pronoun=to_int(parts[4]),
                adjective=to_int(parts[5]),
                verb=to_int(parts[6]),
                participle=to_int(parts[7]),
                pspart=mypspa,
                papart=mypp,
                adverb=to_int(parts[8]),
                preposition=to_int(parts[9]),
                conjunction=to_int(parts[10]),
                interjection=to_int(parts[11]),
                numeral=to_int(parts[12]),
                vb_weak=to_int(parts[13]),
                vb_strong=to_int(parts[14]),
                vb_contracted=to_int(parts[15]),
                vb_pretpres=to_int(parts[16]),
                vb_anomalous=to_int(parts[17]),
                vb_uncertain=to_int(parts[18]),
                n_masc=to_int(parts[19]),
                n_fem=to_int(parts[20]),
                n_neut=to_int(parts[21]),
                n_uncert=to_int(parts[22]),
                stem=parts[1],
            )
            words.append(word)
    return words


def load_forms(path: str) -> list[ManualForm]:
    """
    Load the manual forms from a file.

    Args:
        path: The path to the manual forms file.

    Returns:
        A list of :class:`~wyrdcraeft.models.morphology.ManualForm` objects.

    """
    _path = Path(path)

    forms = []
    with _path.open(encoding="utf-8") as f:
        for line in f:
            _line = line.strip("\r\n")
            # Perl: $forms_line = move_accents(eth2thorn($forms_line));
            _line = OENormalizer.move_accents(OENormalizer.eth2thorn(_line))
            parts = _line.split("\t")
            if len(parts) < 16:  # noqa: PLR2004
                # Fill with empty strings if missing
                parts += [""] * (16 - len(parts))

            # Perl: $form{stem} =~ s/.*-//;
            stem = parts[1].lower()
            if "-" in stem:
                stem = stem.split("-")[-1]

            # Perl: $form{form} =~ s/-//;  (replaces first hyphen only, not /g)
            form_val = parts[3].lower().replace("-", "", 1)

            form = ManualForm(
                BT=parts[0],
                title=parts[1].lower(),
                stem=stem,
                form=form_val,
                form_parts=parts[3].lower(),
                var=parts[5],
                probability=parts[6],
                function=parts[7],
                wright=parts[8],
                paradigm=parts[9].lower(),
                para_id=parts[10],
                wordclass=parts[11].lower(),
                class1=parts[12].lower(),
                class2=parts[13].lower(),
                class3=parts[14].lower(),
                comment=parts[15],
            )
            forms.append(form)
    return forms


def load_paradigms(path: str) -> dict[str, VerbParadigm]:
    """
    Load the paradigms from a file.

    Args:
        path: The path to the paradigms file.

    Returns:
        A dictionary of :class:`~wyrdcraeft.models.morphology.VerbParadigm` objects.

    """
    _path = Path(path)

    paradigms = {}
    with _path.open(encoding="utf-8") as f:
        for line in f:
            # Perl: $vparadigm_line = eth2thorn(lc($vparadigm_line));
            _line = OENormalizer.eth2thorn(line.lower()).strip("\r\n")
            parts = _line.split("\t")
            if len(parts) < 16:  # noqa: PLR2004
                continue

            id_ = parts[0]
            variant_id = int(parts[7])
            para_name = parts[8]

            if id_ not in paradigms:
                paradigms[id_] = VerbParadigm.model_validate(
                    {
                        "ID": parts[0],
                        "title": OENormalizer.eth2thorn(parts[1]),
                        "type": parts[2],
                        "class": parts[3],
                        "subdivision": parts[4],
                        "subclass": parts[5],
                        "wright": parts[6],
                        "variants": [],
                    }
                )

            p = paradigms[id_]
            # Ensure variant exists
            while len(p.variants) <= variant_id:
                p.variants.append(ParadigmVariant(variant_id=len(p.variants)))

            variant = p.variants[variant_id]

            variant.parts[para_name] = ParadigmPart(
                para_id=para_name,
                prefix=parts[9],
                pre_vowel=parts[10],
                vowel=parts[11],
                post_vowel=parts[12],
                boundary=parts[13],
                dental=parts[14],
                ending=parts[15],
            )
    return paradigms


def load_prefixes(path: str) -> list[str]:
    """
    Load the prefixes from a file.

    Args:
        path: The path to the prefixes file.

    Returns:
        A list of prefixes.

    """
    _path = Path(path)
    with _path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
