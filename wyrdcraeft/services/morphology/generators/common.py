import io
import re
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
    Word as WordModel,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from ..text_utils import OENormalizer


def nz(val: str | int | None) -> str:
    """
    Treat '0' or None as empty string for logic checks, matching Perl's falsy
    behavior for these strings.

    Args:
        val: The value to check.

    Returns:
        The value as a string.

    """
    if val is None or val in {"0", 0}:
        return ""
    return str(val)


def perl_numify(val: str) -> float:
    """
    Approximate Perl scalar-to-number coercion for ``==`` comparisons.

    Args:
        val: Value to coerce.

    Returns:
        Numeric value extracted from the start of ``val``, or ``0.0``.

    """
    match = re.match(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))", val)
    if not match:
        return 0.0
    try:
        return float(match.group(1))
    except ValueError:
        return 0.0


def output_manual_forms(session: GeneratorSession, output_file: io.StringIO) -> None:
    """
    Output manual forms to the output file. Perl load_forms prints each form
    to OUTPUT first; Python must match this behavior for parity.

    Args:
        session: The generator session (contains manual_forms).
        output_file: The output file handle.

    """
    for mf in session.manual_forms:
        form_data = {
            "BT": mf.BT,
            "title": mf.title,
            "stem": mf.stem,
            "form": mf.form,
            "formParts": mf.form_parts,
            "var": mf.var,
            "probability": mf.probability,
            "function": mf.function,
            "wright": mf.wright,
            "paradigm": mf.paradigm,
            "paraID": mf.para_id,
            "wordclass": mf.wordclass,
            "class1": mf.class1,
            "class2": mf.class2,
            "class3": mf.class3,
            "comment": mf.comment,
        }
        print_one_form(session, form_data, output_file)


def print_one_form(
    session: GeneratorSession, form_data: dict[str, str], output_file: io.StringIO
) -> None:
    r"""
    Print one form to the output file.  A form in this context is a single form
    of a word.

    Notes:
        Matches Perl implementation of print_one_form function:

        .. code-block:: perl

            print(OUTPUT "$main::output_counter\t$formi\t$form{BT}\t$form{title}\t$form{stem}\t$form{form}\t$form{formParts}\t$form{var}\t" . (defined $form{probability} ? $form{probability} : "") . "\t$form{function}\t$form{wright}\t$form{paradigm}\t$form{paraID}\t$form{wordclass}\t$form{class1}\t$form{class2}\t$form{class3}\t$form{comment}\n");

        - In Perl, ``$form{probability}`` prints as empty string if undefined.
        - In Perl, if ``$count`` is greater than 0, a second line is printed with the probability incremented by 1.

    Args:
        session: The session.
        form_data: The form data.
        output_file: The output file.

    """  # noqa: E501
    form_val = form_data["form"]
    formi = OENormalizer.normalize_output(form_val)

    prob = form_data.get("probability")
    prob_str = str(prob) if prob is not None else ""

    form_parts = form_data.get("formParts", "")

    line = (
        f"{session.output_counter}\t"
        f"{formi}\t"
        f"{form_data['BT']}\t"
        f"{form_data['title']}\t"
        f"{form_data['stem']}\t"
        f"{form_data['form']}\t"
        f"{form_parts}\t"
        f"{form_data['var']}\t"
        f"{prob_str}\t"
        f"{form_data['function']}\t"
        f"{form_data['wright']}\t"
        f"{form_data['paradigm']}\t"
        f"{form_data['paraID']}\t"
        f"{form_data['wordclass']}\t"
        f"{form_data['class1']}\t"
        f"{form_data['class2']}\t"
        f"{form_data['class3']}\t"
        f"{form_data['comment']}\n"
    )
    output_file.write(line)
    session.output_counter += 1

    # remove double consonants from formi with lower probability
    reduced_formi, count = re.subn(
        f"({OENormalizer.CONSONANT_REGEX.pattern})\\1", r"\1", formi
    )
    if count > 0:
        prob_val = int(str(prob)) if prob not in {None, ""} else 0
        line = (
            f"{session.output_counter}\t"
            f"{reduced_formi}\t"
            f"{form_data['BT']}\t"
            f"{form_data['title']}\t"
            f"{form_data['stem']}\t"
            f"{form_data['form']}\t"
            f"{form_parts}\t"
            f"{form_data['var']}\t"
            f"{prob_val + 1}\t"
            f"{form_data['function']}\t"
            f"{form_data['wright']}\t"
            f"{form_data['paradigm']}\t"
            f"{form_data['paraID']}\t"
            f"{form_data['wordclass']}\t"
            f"{form_data['class1']}\t"
            f"{form_data['class2']}\t"
            f"{form_data['class3']}\t"
            f"{form_data['comment']}\n"
        )
        output_file.write(line)
        session.output_counter += 1


class VerbFormGenerator:
    """
    Generator for Old English verb forms.

    Args:
        session: The session.
        output_file: The output file.

    """

    #: The changes for strong verbs of type 2.
    S2_CHANGES: Final[list[tuple[str, str]]] = [
        ("dst$", "tst"),
        ("þst$", "tst"),
        ("tst$", "st"),
        ("ngst$", "ncst"),
        ("ncst$", "nst"),
        ("gst$", "hst"),
        ("hst$", "xst"),
    ]
    #: The changes for strong verbs of type 3.
    S3_CHANGES: Final[list[tuple[str, str]]] = [
        (r"[td]þ$", "tt"),
        (r"tt$", "t"),
        (r"þþ$", "þ"),
        (r"þ$", "t"),
        (r"sþ$", "st"),
        (r"ngþ$", "ncþ"),
        (r"gþ$", "hþ"),
    ]

    def __init__(self, session: GeneratorSession, output_file: io.StringIO):
        #: The generator session.
        self.session = session
        #: The output file.
        self.output_file = output_file

    def generate(self) -> None:
        """Main entry point to generate all verb forms."""
        for word in self.session.words:
            if word.verb == 1 and (word.pspart + word.papart == 0):
                self._process_word(word)

    def _process_word(self, word: Word) -> None:
        """
        Process a single word's paradigms.

        Args:
            word: The word to process.

        """
        for vp in word.vb_paradigm:
            self._process_paradigm(word, vp)

    def _process_paradigm(self, word: Word, vp: VerbParadigm) -> None:
        """
        Process a single paradigm.

        Notes:
            Matches Perl implementation of ``process_paradigm`` function:

            .. code-block:: perl

                my $formhash_base = {
                    title => $word->title,
                    stem => $word->stem,
                    BT => sprintf("%06d", $word->nid),
                    wordclass => "verb",
                    class1 => $vp->type,
                    class2 => $vp->class_,
                    class3 => $vp->subclass,
                    paradigm => $vp->title,
                    paraID => $vp->ID,
                    wright => $word->wright,
                    comment => "",
                };

                my $boundary_inf = $_->{variant}[0]{if}{boundary};

                foreach my $variant (@{ $vp->variants }) {
                    process_variant($word, $vp, $variant, $formhash_base, $boundary_inf);
                }

        Args:
            word: The word to process.
            vp: The paradigm to process.

        """  # noqa: E501
        formhash_base = {
            "title": word.title,
            "stem": word.stem,
            "BT": f"{word.nid:06d}",
            "wordclass": "verb",
            "class1": vp.type,
            "class2": vp.class_,
            "class3": vp.subclass,
            "paradigm": vp.title,
            "paraID": vp.ID,
            "wright": word.wright,
            "comment": "",
        }
        variant0 = vp.variants[0]
        inf_part = variant0.parts.get("if")
        painsg1_part = variant0.parts.get("painsg1")
        boundary_inf = nz(inf_part.boundary if inf_part else "")
        vowel_inf = nz(inf_part.vowel if inf_part else "")
        vowel_pa = nz(painsg1_part.vowel if painsg1_part else "")

        for variant in vp.variants:
            self._process_variant(
                word, vp, variant, formhash_base, boundary_inf, vowel_inf, vowel_pa
            )

    def _process_variant(
        self,
        word: Word,
        vp: VerbParadigm,
        variant: ParadigmVariant,
        formhash_base: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Process a single variant of a paradigm.

        Notes:
            Matches Perl implementation of process_variant function:

            .. code-block:: perl

                foreach my $item (@{ $variant->parts }) {
                    process_part($word, $vp, $variant, $item, $formhash_var, $boundary_inf);
                }

        Args:
            word: The word to process.
            vp: The paradigm to process.
            variant: The variant to process.
            formhash_base: The base form hash.
            boundary_inf: The boundary information.

        """  # noqa: E501
        formhash_var = formhash_base.copy()
        formhash_var["var"] = str(variant.variant_id)
        for item in variant.parts.values():
            self._process_part(
                word, vp, variant, item, formhash_var, boundary_inf, vowel_inf, vowel_pa
            )

    def _process_part(  # noqa: PLR0913
        self,
        word: Word,
        vp: VerbParadigm,
        variant: ParadigmVariant,
        item: ParadigmPart,
        formhash_var: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Process a single part of a variant.

        Notes:
            Matches Perl implementation of process_part function:

            .. code-block:: perl

                foreach my $item (@{ $variant->parts }) {
                    process_part($word, $vp, $variant, $item, $formhash_var, $boundary_inf);
                }

        Args:
            word: The word to process.
            vp: The paradigm to process.
            variant: The variant to process.
            item: The part to process.
            formhash_var: The form hash.
            boundary_inf: The boundary information.

        """  # noqa: E501
        prefix = self._get_prefix(word, item)
        post_vowel = self._get_post_vowel(word, item, boundary_inf)
        pre_vowel, actual_vowel = self._get_pre_vowel(word)

        if vp.type == "s":
            self._generate_strong_verb_parts(
                formhash_var,
                word,
                item,
                prefix,
                pre_vowel,
                actual_vowel,
                post_vowel,
                variant.variant_id,
            )
        else:
            self._generate_weak_verb_parts(
                formhash_var,
                word,
                item,
                prefix,
                pre_vowel,
                actual_vowel,
                post_vowel,
                variant.variant_id,
                vp.ID,
                vowel_inf,
                vowel_pa,
            )

    def _get_prefix(self, word: Word, item: ParadigmPart) -> str:
        """
        Determine the prefix for a part.

        Note:
            Matches Perl implementation of get_prefix function:

            .. code-block:: perl

                if ($prefix ne $item->{prefix}) {
                    $prefix = $prefix . "-" . $item->{prefix};
                }

        Args:
            word: The word.
            item: The item.

        Returns:
            The prefix.

        """
        prefix = word.prefix
        if prefix != item.prefix:
            prefix = f"{prefix}-{item.prefix}"
        return prefix

    def _get_post_vowel(self, word: Word, item: ParadigmPart, boundary_inf: str) -> str:
        """
        Extract post-vowel from word stem.

        Note:
            Matches Perl implementation of derive_post_vowel function:

            .. code-block:: perl

                if ($item->{postVowel} ne "") {
                    $post_vowel = $item->{postVowel};
                }

            The regex pattern is:

            .. code-block:: perl

                m/$vowel_regex$vowel_regex*?($consonant_regex.*?)$boundary_inf$vowel_regex+n$/

        Args:
            word: The word.
            item: The item.
            boundary_inf: The boundary information.

        Returns:
            The post-vowel.

        """
        if not nz(item.post_vowel):
            return ""

        if boundary_inf:
            pattern = (
                f"{OENormalizer.VOWEL_REGEX.pattern}{OENormalizer.VOWEL_REGEX.pattern}*?"
                f"({OENormalizer.CONSONANT_REGEX.pattern}.*?){re.escape(boundary_inf)}"
                f"{OENormalizer.VOWEL_REGEX.pattern}+n$"
            )
        else:
            pattern = (
                f"{OENormalizer.VOWEL_REGEX.pattern}{OENormalizer.VOWEL_REGEX.pattern}*?"
                f"({OENormalizer.CONSONANT_REGEX.pattern}.*?){OENormalizer.VOWEL_REGEX.pattern}+n$"
            )
        match = re.search(pattern, word.stem)
        return match.group(1) if match else ""

    def _get_pre_vowel(self, word: Word) -> tuple[str, str]:
        """
        Extract pre-vowel and actual vowel from word stem.

        Note:
            Matches Perl implementation of derive_pre_vowel function:

            .. code-block:: perl

                $stem =~ m/^($vowel_regex*?.*?)($vowel_regex$vowel_regex?)/;


        Args:
            word: The word.

        Returns:
            The pre-vowel and actual vowel.

        """
        pattern = (
            f"^({OENormalizer.VOWEL_REGEX.pattern}*?.*?)"
            f"({OENormalizer.VOWEL_REGEX.pattern}{{1,2}})"
        )
        match = re.search(pattern, word.stem)
        if match:
            return match.group(1), match.group(2)
        return "", ""

    def _generate_and_print_form(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        """
        Generate and print a form.

        Note:
            Matches Perl implementation of generate_and_print_form function:

            .. code-block:: perl

                if ($formhash->{class1} eq "s") {
                    $form_parts = "$prefix-$pre_vowel-$vowel-$post_vowel-$boundary-$ending";
                } else {
                    $form_parts = "$prefix-$pre_vowel-$vowel-$post_vowel-$boundary-" . (defined $dental ? $dental : "") . "-$ending";
                }

        Args:
            formhash: The form hash.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            dental: The dental.
            ending: The ending.
            function: The function.

        Keyword Args:
            prob: The probability.

        Returns:
            The form and form parts as a tuple.

        """  # noqa: E501
        fh = formhash.copy()
        fh["function"] = function

        # Ensure values are strings and handle None/0 as Perl does in interpolation
        def p_interp(val):
            if val is None:
                return ""
            return str(val)

        if fh["class1"] == "s":
            form_parts = (
                f"{p_interp(prefix)}-{p_interp(pre_vowel)}-{p_interp(vowel)}"
                f"-{p_interp(post_vowel)}-{p_interp(boundary)}-{p_interp(ending)}"
            )
        else:
            if dental is None:
                form_parts = (
                    f"{p_interp(prefix)}-{p_interp(pre_vowel)}-{p_interp(vowel)}"
                    f"-{p_interp(post_vowel)}-{p_interp(boundary)}-{p_interp(ending)}"
                )
            else:
                d = p_interp(dental)
                form_parts = (
                    f"{p_interp(prefix)}-{p_interp(pre_vowel)}-{p_interp(vowel)}"
                    f"-{p_interp(post_vowel)}-{p_interp(boundary)}-{d}-{p_interp(ending)}"
                )

        form = form_parts.replace("0", "").replace("-", "").replace("\n", "")
        form_parts = form_parts.replace("\n", "")

        fh["form"] = form
        fh["formParts"] = form_parts
        fh["probability"] = "" if prob is None else str(prob)

        print_one_form(self.session, fh, self.output_file)
        return form, form_parts

    def _add_participle_to_adjectives(
        self, word: Word, prefix: str, form_parts: str, is_past: bool
    ) -> None:
        r"""
        Add a participle to adjectives.

        Notes:
            Matches Perl implementation of ``add_participle_to_adjectives`` function:

            .. code-block:: perl
                $stem = $1 if $form_parts =~ m/$prefix(.*)$/;
                $stem =~ s/[0\-\n]//g;

        Args:
            word: The word.
            prefix: The prefix.
            form_parts: The form parts.
            is_past: Whether the form is past.

        Returns:
            The stem.

        """
        # Perl uses numeric ``==`` here, not string ``eq``.
        if perl_numify(prefix) != perl_numify(word.prefix):
            return

        match = re.search(f"{re.escape(prefix)}(.*)$", form_parts)
        if match:
            stem = match.group(1).replace("0", "").replace("-", "").replace("\n", "")
        else:
            stem = form_parts.replace("0", "").replace("-", "").replace("\n", "")

        # In Python, we add to session.adjectives
        # We need to create a new Word object or similar structure
        # For now, let's just store it in a way Phase 5 can use.
        # The Perl code adds to a global @adjectives array.
        # We'll add to session.adjectives which is a list[Word].

        new_adj = WordModel(
            nid=word.nid,
            title=(prefix + stem).replace("0", "").replace("-", "").replace("\n", ""),
            wright=word.wright,
            noun=0,
            pronoun=0,
            adjective=1,
            verb=0,
            participle=0,
            pspart=1 if not is_past else 0,
            papart=1 if is_past else 0,
            adverb=0,
            preposition=0,
            conjunction=0,
            interjection=0,
            numeral=0,
            vb_weak=0,
            vb_strong=0,
            vb_contracted=0,
            vb_pretpres=0,
            vb_anomalous=0,
            vb_uncertain=0,
            n_masc=0,
            n_fem=0,
            n_neut=0,
            n_uncert=0,
            prefix=prefix,
            stem=stem,
        )
        self.session.adjectives.append(new_adj)

    def _generate_strong_verb_parts(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        item: ParadigmPart,
        prefix: str,
        pre_vowel: str,
        root_vowel_actual: str,
        post_vowel: str,
        variant_id: int,
    ) -> None:
        """
        Matches Perl's generate_strong_verb_parts.

        Notes:
            Matches Perl implementation of ``generate_strong_verb_parts`` function:

        Args:
            formhash: The form hash.
            word: The word to process.
            item: The part to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            root_vowel_actual: The root vowel actual.
            post_vowel: The post-vowel.
            variant_id: The variant ID.

        """
        para_id = item.para_id
        ending = item.ending
        boundary = item.boundary

        vowel_list = [item.vowel]

        for vcount, v in enumerate(vowel_list):
            prob = 1 if vcount == 1 else None
            _, form_parts = self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                v,
                post_vowel,
                boundary,
                "",
                ending,
                para_id,
                prob,
            )

            if para_id.lower() == "papt":
                self._add_participle_to_adjectives(word, prefix, form_parts, True)  # noqa: FBT003

            if para_id.lower() == "if":
                self._generate_strong_derived_from_inf(
                    formhash,
                    word,
                    prefix,
                    pre_vowel,
                    v,
                    post_vowel,
                    boundary,
                    ending,
                    prob,
                )
            elif para_id.lower() == "painsg1":
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    v,
                    post_vowel,
                    boundary,
                    "",
                    "0",
                    "PaInSg3",
                    prob,
                )
            elif para_id.lower() == "painpl":
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    v,
                    post_vowel,
                    boundary,
                    "",
                    "e",
                    "PaInSg2",
                    prob,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    v,
                    post_vowel,
                    boundary,
                    "",
                    "e",
                    "PaSuSg",
                    prob,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    v,
                    post_vowel,
                    boundary,
                    "",
                    "en",
                    "PaSuPl",
                    prob,
                )

    def _generate_strong_derived_from_inf(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        prob: str | int | None,
    ) -> None:
        """
        Generate strong verbs derived from inf.

        Notes:
            Matches Perl implementation of ``generate_strong_derived_from_inf``
            function.

        Args:
            formhash: The form hash.
            word: The word to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            ending: The ending.
            prob: The probability.

        """
        if "an" in ending:
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "anne",
                "IdIf",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "enne",
                "IdIf",
                prob,
            )
            _, fp = self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "ende",
                "PsPt",
                prob,
            )
            self._add_participle_to_adjectives(word, prefix, fp, False)  # noqa: FBT003

            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "e",
                "PsInSg1",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "u",
                "PsInSg1",
                (int(prob) + 1 if prob is not None else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "o",
                "PsInSg1",
                (int(prob) + 1 if prob is not None else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "æ",
                "PsInSg1",
                (int(prob) + 1 if prob is not None else 1),
            )

            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "aþ",
                "PsInPl",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "eþ",
                "PsInPl",
                (int(prob) + 1 if prob is not None else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "es",
                "PsInPl",
                (int(prob) + 1 if prob is not None else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "as",
                "PsInPl",
                (int(prob) + 1 if prob is not None else 1),
            )

            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "e",
                "PsSuSg",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "en",
                "PsSuPl",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "aþ",
                "ImPl",
                prob,
            )
        else:
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "nne",
                "IdIf",
                prob,
            )
            _, fp = self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "nde",
                "PsPt",
                prob,
            )
            self._add_participle_to_adjectives(word, prefix, fp, False)  # noqa: FBT003

            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "0",
                "PsInSg1",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "þ",
                "PsInPl",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "0",
                "PsSuSg",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "n",
                "PsSuPl",
                prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                "",
                "þ",
                "ImPl",
                prob,
            )

        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            "",
            "0",
            "ImSg",
            prob,
        )

        # Umlaut forms
        mvowels = OENormalizer.iumlaut([vowel])
        for mv_idx, mvowel in enumerate(mvowels):
            mv_prob = int(prob) + mv_idx if prob is not None else mv_idx

            # PsInSg2
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "stu",
                "PsInSg2",
                mv_prob + 1,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "est",
                "PsInSg2",
                mv_prob + 1,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "ist",
                "PsInSg2",
                mv_prob + 1,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "s",
                "PsInSg2",
                mv_prob + 1,
            )
            self._generate_and_print_form_with_sound_changes(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "st",
                "PsInSg2",
                mv_prob,
            )

            # PsInSg3
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "eþ",
                "PsInSg3",
                mv_prob + 1,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "iþ",
                "PsInSg3",
                mv_prob + 1,
            )
            self._generate_and_print_form_with_sound_changes(
                formhash,
                prefix,
                pre_vowel,
                mvowel,
                post_vowel,
                boundary,
                "",
                "þ",
                "PsInSg3",
                mv_prob,
            )

    def _generate_and_print_form_with_sound_changes(  # noqa: PLR0912, PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
        sound_change_prob_delta: int = 1,
    ) -> None:
        """
        Matches Perl's generate_and_print_form_with_sound_changes.

        Notes:
            Matches Perl implementation of ``generate_and_print_form_with_sound_changes``
            function:

        Args:
            formhash: The form hash.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            dental: The dental.
            ending: The ending.
            function: The function.
            prob: The probability.

        """  # noqa: E501
        form, form_parts = self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            dental,
            ending,
            function,
            prob,
        )
        sound_prob = int(prob or 0) + sound_change_prob_delta

        # Sound changes for PsInSg2/3
        if function == "PsInSg2":
            # Perl uses sequential s/// which modifies $form. We'll do the same.
            if "dst" in form:
                form = form.replace("dst", "tst")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
            if "þst" in form:
                form = form.replace("þst", "tst")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
            if "tst" in form:
                form = form.replace("tst", "st")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
            if "ngst" in form:
                form = form.replace("ngst", "ncst")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
            if "ncst" in form:
                form = form.replace("ncst", "nst")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
            if "gst" in form:
                form = form.replace("gst", "hst")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
            if "hst" in form:
                form = form.replace("hst", "xst")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )
        elif function == "PsInSg3":
            # Perl: if ($form =~ s/[td]\x{00FE}$/tt/g)
            match = re.search(r"[td]þ$", form)
            if match:
                form = re.sub(r"[td]þ$", "tt", form)
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

            # Perl: if ($form =~ s/[dt]t$/t/g)
            match = re.search(r"[dt]t$", form)
            if match:
                form = re.sub(r"[dt]t$", "t", form)
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

            # Perl: if ($form =~ s/\x{00FE}\x{00FE}$/\x{00FE}/g)
            if "þþ" in form:
                form = form.replace("þþ", "þ")
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

            # Perl: if ($form =~ s/\x{00FE}$/t/g)
            if form.endswith("þ"):
                form = form[:-1] + "t"
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

            # Perl: if ($form =~ s/s\x{00FE}$/st/g)
            if form.endswith("sþ"):
                form = form[:-2] + "st"
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

            # Perl: if ($form =~ s/ng\x{00FE}$/nc\x{00FE}/g)
            if form.endswith("ngþ"):
                form = form[:-3] + "ncþ"
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

            # Perl: if ($form =~ s/g\x{00FE}$/h\x{00FE}/g)
            if form.endswith("gþ"):
                form = form[:-2] + "hþ"
                self._generate_and_print_manual(
                    formhash, form, form_parts, function, sound_prob
                )

    def _generate_and_print_manual(
        self,
        formhash: dict[str, str],
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        """
        Matches Perl's generate_and_print_manual.
        """
        fh = formhash.copy()
        fh["form"] = form
        fh["formParts"] = form_parts
        fh["function"] = function
        fh["probability"] = "" if prob is None else str(prob)
        print_one_form(self.session, fh, self.output_file)

    def _generate_weak_verb_parts(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        item: ParadigmPart,
        prefix: str,
        pre_vowel: str,
        root_vowel_actual: str,
        post_vowel: str,
        variant_id: int,
        para_id_num: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Matches Perl's generate_weak_verb_parts.

        Args:
            formhash: The form hash.
            word: The word to process.
            item: The part to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            root_vowel_actual: The root vowel actual.
            post_vowel: The post-vowel.
            variant_id: The variant ID.
            para_id_num: The paradigm ID number.
            vowel_inf: The infinitive vowel from variant 0.
            vowel_pa: The preterite singular vowel from variant 0.

        """
        para_id = item.para_id
        ending = item.ending
        dental = item.dental
        boundary = item.boundary
        para_id_int = int(para_id_num) if str(para_id_num).isdigit() else None

        prob: str | int | None = 0

        # Perl: if (($ID > 88) && ($ID < 93))
        if para_id_int is not None and 88 < para_id_int < 93:
            _, fp = self._generate_and_print_form(
                formhash,
                prefix,
                item.pre_vowel,
                item.vowel,
                item.post_vowel,
                item.boundary,
                dental,
                ending,
                para_id,
                0,
            )
            if para_id.lower() == "pspt":
                self._add_participle_to_adjectives(word, prefix, fp, False)  # noqa: FBT003
            if para_id.lower() == "papt":
                self._add_participle_to_adjectives(word, prefix, fp, True)  # noqa: FBT003
        else:
            # Original form from paradigm file
            principal_prob: str | int | None = (
                None if (para_id.lower() == "painsg1" and variant_id == 0) else prob
            )
            _, fp = self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                root_vowel_actual,
                post_vowel,
                boundary,
                dental,
                ending,
                para_id,
                principal_prob,
            )
            if para_id.lower() == "pspt":
                self._add_participle_to_adjectives(word, prefix, fp, False)  # noqa: FBT003
            if para_id.lower() == "papt":
                self._add_participle_to_adjectives(word, prefix, fp, True)  # noqa: FBT003

            # Derived forms
            if para_id.lower() == "if":
                self._generate_weak_derived_from_inf(
                formhash,
                word,
                prefix,
                pre_vowel,
                root_vowel_actual,
                    post_vowel,
                    boundary,
                    ending,
                    prob,
                )
            elif para_id.lower() == "psinsg2":
                self._generate_weak_derived_from_psinsg2(
                    formhash,
                    prefix,
                    pre_vowel,
                    root_vowel_actual,
                    post_vowel,
                    boundary,
                    prob,
                )
            elif para_id.lower() == "painsg1":
                self._generate_weak_derived_from_painsg1(
                    formhash,
                    word,
                    prefix,
                    pre_vowel,
                    root_vowel_actual,
                    post_vowel,
                    boundary,
                    dental,
                    prob,
                    vowel_inf,
                    vowel_pa,
                )

    def _generate_weak_derived_from_inf(  # noqa: PLR0912, PLR0913, PLR0915
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        original_ending: str,
        prob: str | int | None,
    ) -> None:
        """
        Generate weak verbs derived from inf.

        Notes:
            Matches Perl implementation of ``generate_weak_derived_from_inf``
            function.

        Args:
            formhash: The form hash.
            word: The word to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            original_ending: The original ending.
            prob: The probability.

        """
        probability = prob if prob is not None else ""

        # create_dict31.pl applies this branch to weak verbs generally.
        if formhash.get("class2") in {"", "1", "2"}:
            iending = "i" if original_ending.lower().startswith("i") else ""

            # If the form ends in a vowel, the initial vowel of the ending is deleted
            fp_base = f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}"
            perl_inf_vowel_end = bool(
                re.search(r"[æaeyouÆAEIYOUǣāēīȳōūǢĀĒĪȲŌŪ][0-]*?$", fp_base)
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                None,
                original_ending,
                "if",
                probability,
            )
            if perl_inf_vowel_end:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    None,
                    "n",
                    "if",
                    probability,
                )

            # IdIf
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "anne",
                "IdIf",
                probability,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "enne",
                "IdIf",
                probability,
            )
            if perl_inf_vowel_end:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "nne",
                    "IdIf",
                    probability,
                )

            # PsInSg1
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "e",
                "PsInSg1",
                probability,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "u",
                "PsInSg1",
                (int(probability) + 1 if probability != "" else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "o",
                "PsInSg1",
                (int(probability) + 1 if probability != "" else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "æ",
                "PsInSg1",
                (int(probability) + 1 if probability != "" else 1),
            )
            if perl_inf_vowel_end:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    None,
                    "0",
                    "PsInSg1",
                    probability,
                )

            # PsInPl
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "aþ",
                "PsInPl",
                probability,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "eþ",
                "PsInPl",
                (int(probability) + 1 if probability != "" else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "es",
                "PsInPl",
                (int(probability) + 1 if probability != "" else 1),
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "as",
                "PsInPl",
                (int(probability) + 1 if probability != "" else 1),
            )
            if perl_inf_vowel_end:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "þ",
                    "PsInPl",
                    probability,
                )

            # PsSuSg
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "e",
                "PsSuSg",
                probability,
            )
            if perl_inf_vowel_end:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    None,
                    "0",
                    "PsSuSg",
                    probability,
                )

            # PsSuPl
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "en",
                "PsSuPl",
                probability,
            )
            if re.search(
                f"{OENormalizer.VOWEL_REGEX.pattern}$", fp_base, re.IGNORECASE
            ):
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "n",
                    "PsSuPl",
                    probability,
                )

            # ImPl
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "aþ",
                "ImPl",
                probability,
            )
            if perl_inf_vowel_end:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    None,
                    "þ",
                    "ImPl",
                    probability,
                )

            # PsPt
            _, fp = self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                iending,
                "ende",
                "PsPt",
                probability,
            )
            if perl_inf_vowel_end:
                _, fp = self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "nde",
                    "PsPt",
                    probability,
                )
            self._add_participle_to_adjectives(word, prefix, fp, False)  # noqa: FBT003

        # Perl: if ($word->{class2} == 2)
        elif formhash.get("class2") == "2":
            for iending in ["ig", "ige", ""]:
                # Perl: my $prob_c2 = 0;
                prob_c2 = 0

                fp_base = f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}"
                perl_inf_vowel_end = bool(
                    re.search(r"[æaeyouÆAEIYOUǣāēīȳōūǢĀĒĪȲŌŪ][0-]*?$", fp_base)
                )

                # if (only for ig and ige)
                if iending != "":
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        iending,
                        "an",
                        "if",
                        prob_c2,
                    )
                    if perl_inf_vowel_end:
                        self._generate_and_print_form(
                            formhash,
                            prefix,
                            pre_vowel,
                            vowel,
                            post_vowel,
                            boundary,
                            None,
                            "n",
                            "if",
                            prob_c2,
                        )
                elif perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        None,
                        "n",
                        "if",
                        prob_c2,
                    )

                # IdIf
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "anne",
                    "IdIf",
                    prob_c2,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "enne",
                    "IdIf",
                    prob_c2,
                )
                if perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        iending,
                        "nne",
                        "IdIf",
                        prob_c2,
                    )

                # ImSg
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "a",
                    "ImSg",
                    prob_c2,
                )
                if perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        None,
                        "0",
                        "ImSg",
                        prob_c2,
                    )

                # PsInSg1
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "e",
                    "PsInSg1",
                    prob_c2,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "u",
                    "PsInSg1",
                    prob_c2 + 1,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "o",
                    "PsInSg1",
                    prob_c2 + 1,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "æ",
                    "PsInSg1",
                    prob_c2 + 1,
                )
                if perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        None,
                        "0",
                        "PsInSg1",
                        prob_c2,
                    )

                # PsInPl
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "aþ",
                    "PsInPl",
                    prob_c2,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "eþ",
                    "PsInPl",
                    prob_c2 + 1,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "es",
                    "PsInPl",
                    prob_c2 + 1,
                )
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "as",
                    "PsInPl",
                    prob_c2 + 1,
                )
                if perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        iending,
                        "þ",
                        "PsInPl",
                        prob_c2,
                    )

                # PsSuSg
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "e",
                    "PsSuSg",
                    prob_c2,
                )
                if perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        None,
                        "0",
                        "PsSuSg",
                        prob_c2,
                    )

                # PsSuPl
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "en",
                    "PsSuPl",
                    prob_c2,
                )
                if re.search(
                    f"{OENormalizer.VOWEL_REGEX.pattern}$", fp_base, re.IGNORECASE
                ):
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        iending,
                        "n",
                        "PsSuPl",
                        prob_c2,
                    )

                # ImPl
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "aþ",
                    "ImPl",
                    prob_c2,
                )
                if perl_inf_vowel_end:
                    self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        None,
                        "þ",
                        "ImPl",
                        prob_c2,
                    )

                # Past participle
                _, fp = self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    vowel,
                    post_vowel,
                    boundary,
                    iending,
                    "ende",
                    "PsPt",
                    prob_c2,
                )
                if perl_inf_vowel_end:
                    _, fp = self._generate_and_print_form(
                        formhash,
                        prefix,
                        pre_vowel,
                        vowel,
                        post_vowel,
                        boundary,
                        iending,
                        "nde",
                        "PsPt",
                        prob_c2,
                    )
                self._add_participle_to_adjectives(word, prefix, fp, False)  # noqa: FBT003

    def _generate_weak_derived_from_painsg1(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str,
        prob: str | int | None,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Generate weak verbs derived from painsg1.

        Args:
            formhash: The form hash.
            word: The word to process.
            prefix: The prefix.
            pre_vowel: The pre-vowel.
            vowel: The vowel.
            post_vowel: The post-vowel.
            boundary: The boundary.
            dental: The dental.
            prob: The probability.
            vowel_inf: The infinitive vowel from variant 0.
            vowel_pa: The preterite singular vowel from variant 0.

        """
        pv_simp = re.sub(r"(.)\1", r"\1", post_vowel)
        base_probability = int(prob or 0)
        vowel_list = [vowel]

        # Perl unshifts the paradigm preterite vowel when infinitive and
        # preterite vowels differ in the exemplar.
        if vowel_inf and vowel_pa and vowel_inf != vowel_pa:
            vowel_list.insert(0, vowel_pa)

        for vcount, current_vowel in enumerate(vowel_list):
            curr_prob = base_probability + vcount

            # PaInSg1
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "e",
                "PaInSg1",
                curr_prob,
            )

            # PaInSg2
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "est",
                "PaInSg2",
                curr_prob,
            )
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "es",
                "PaInSg2",
                curr_prob + 1,
            )

            # PaInSg3
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "e",
                "PaInSg3",
                curr_prob,
            )

            # PaInPl
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "on",
                "PaInPl",
                curr_prob,
            )

            # PaSuSg
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "e",
                "PaSuSg",
                curr_prob,
            )

            # PaSuPl
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                current_vowel,
                pv_simp,
                boundary,
                dental,
                "en",
                "PaSuPl",
                curr_prob,
            )

            # PaPt uses no explicit ending in Perl.
            form_parts = (
                f"{prefix}-{pre_vowel}-{current_vowel}-{pv_simp}-{boundary}-{dental}"
            )
            form = form_parts.replace("0", "").replace("-", "")
            self._generate_and_print_manual(
                formhash, form, form_parts, "PaPt", curr_prob
            )

            # t-ed > t-t; t-t > t
            if form.endswith("ted"):
                form = re.sub(r"ted$", "tt", form)
                self._generate_and_print_manual(
                    formhash, form, form_parts, "PaPt", curr_prob + 1
                )
            if form.endswith("tt"):
                form = re.sub(r"tt$", "t", form)
                self._generate_and_print_manual(
                    formhash, form, form_parts, "PaPt", curr_prob + 1
                )

            self._add_participle_to_adjectives(word, prefix, form_parts, True)  # noqa: FBT003

    def _generate_weak_derived_from_psinsg2(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        prob: str | int | None,
    ) -> None:
        """
        Matches Perl's generate_weak_derived_from_psinsg2.
        """
        probability = prob if prob is not None else ""
        # Perl: $post_vowel =~ s/(.)\1/$1/;
        pv_simp = re.sub(r"(.)\1", r"\1", post_vowel)

        # PsInSg2 -est, -es, -ist, -s, -st
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "est",
            "PsInSg2",
            (int(probability) + 1 if probability != "" else 1),
        )
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "es",
            "PsInSg2",
            (int(probability) + 1 if probability != "" else 1),
        )
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "ist",
            "PsInSg2",
            (int(probability) + 1 if probability != "" else 1),
        )
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "s",
            "PsInSg2",
            (int(probability) + 1 if probability != "" else 1),
        )

        # Sound changes for PsInSg2
        self._generate_and_print_form_with_sound_changes(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "st",
            "PsInSg2",
            probability,
        )

        # PsInSg3 -eþ, -ieþ, -iþ, -þ
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "eþ",
            "PsInSg3",
            (int(probability) + 1 if probability != "" else 1),
        )

        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "ieþ",
            "PsInSg3",
            (int(probability) + 1 if probability != "" else 1),
        )
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "iþ",
            "PsInSg3",
            (int(probability) + 1 if probability != "" else 1),
        )

        # Sound changes for PsInSg3
        self._generate_and_print_form_with_sound_changes(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "þ",
            "PsInSg3",
            (int(probability) + 1 if probability != "" else 1),
            0,
        )

        # ImSg -e; -ie; -0
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "e",
            "ImSg",
            probability,
        )
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "ie",
            "ImSg",
            probability,
        )
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            pv_simp,
            boundary,
            None,
            "0",
            "ImSg",
            probability,
        )


def generate_vbforms(session: GeneratorSession, output_file: io.StringIO) -> None:
    """
    Wrapper for VerbFormGenerator.

    Args:
        session: The session.
        output_file: The output file.

    """
    generator = VerbFormGenerator(session, output_file)
    generator.generate()


def generate_adjforms(session, output_file):
    """Perl: sub generate_adjforms"""
    from .adj_forms import generate_adjforms as _generate_adjforms

    _generate_adjforms(session, output_file)


def generate_advforms(session, output_file):
    """Perl: sub generate_advforms"""
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


def generate_numforms(session, output_file):
    """Perl: sub generate_numforms"""
    from .num_forms import generate_numforms as _generate_numforms

    _generate_numforms(session, output_file)


def generate_nounforms(session, output_file):
    """Perl: sub generate_nounforms"""
    from .noun_forms import generate_nounforms as _generate_nounforms

    _generate_nounforms(session, output_file)
