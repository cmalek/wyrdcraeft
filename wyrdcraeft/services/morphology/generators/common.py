import re
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from ..generation.form_assembly import assemble_form_parts, materialize_form
from ..generation.participles import build_participle_adjective
from ..generation.probability import (
    format_probability,
    probability_or_zero,
    probability_plus,
)
from ..generation.shared import FormOutput
from ..generation.sound_changes import (
    emit_sound_changed_forms,
)
from ..generation.strong_inflections import (
    dispatch_strong_derived_from_principal_part,
    emit_strong_derived_from_inf_sequence,
)
from ..generation.weak_inflections import (
    dispatch_weak_principal_part_derivations,
    emit_weak_derived_from_inf_sequence,
    emit_weak_derived_from_painsg1_variant,
    emit_weak_derived_from_psinsg2,
    emit_weak_principal_form,
    is_weak_item_shape_window,
)
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


def output_manual_forms(session: GeneratorSession, output_file: FormOutput) -> None:
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
    session: GeneratorSession, form_data: dict[str, str], output_file: FormOutput
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

    def __init__(self, session: GeneratorSession, output_file: FormOutput):
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

        form_parts_raw = assemble_form_parts(
            class1=fh["class1"],
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            dental=dental,
            ending=ending,
        )
        form, form_parts = materialize_form(form_parts_raw)

        fh["form"] = form
        fh["formParts"] = form_parts
        fh["probability"] = format_probability(prob)

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

        new_adj = build_participle_adjective(
            word=word,
            prefix=prefix,
            form_parts=form_parts,
            is_past=is_past,
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

            def emit_form_for_vowel(
                active_vowel: str,
                ending_value: str,
                function: str,
                prob_value: str | int | None,
            ) -> tuple[str, str]:
                return self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    active_vowel,
                    post_vowel,
                    boundary,
                    "",
                    ending_value,
                    function,
                    prob_value,
                )

            def on_inf(
                active_vowel: str,
                prob_value: str | int | None,
            ) -> None:
                self._generate_strong_derived_from_inf(
                    formhash,
                    word,
                    prefix,
                    pre_vowel,
                    active_vowel,
                    post_vowel,
                    boundary,
                    ending,
                    prob_value,
                )

            def on_papt_form_parts(derived_form_parts: str) -> None:
                self._add_participle_to_adjectives(
                    word,
                    prefix,
                    derived_form_parts,
                    is_past=True,
                )

            dispatch_strong_derived_from_principal_part(
                para_id=para_id,
                form_parts=form_parts,
                active_vowel=v,
                probability=prob,
                on_papt_form_parts=on_papt_form_parts,
                on_inf=on_inf,
                emit_form_for_vowel=emit_form_for_vowel,
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
        def emit_form_for_vowel(
            active_vowel: str,
            ending_value: str,
            function: str,
            prob_value: str | int | None,
        ) -> tuple[str, str]:
            return self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                active_vowel,
                post_vowel,
                boundary,
                "",
                ending_value,
                function,
                prob_value,
            )

        def emit_sound_for_vowel(
            active_vowel: str,
            ending_value: str,
            function: str,
            prob_value: str | int | None,
        ) -> None:
            self._generate_and_print_form_with_sound_changes(
                formhash,
                prefix,
                pre_vowel,
                active_vowel,
                post_vowel,
                boundary,
                "",
                ending_value,
                function,
                prob_value,
            )

        def emit_imsg(prob_value: str | int | None) -> None:
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
                prob_value,
            )

        def on_participle(form_parts: str) -> None:
            self._add_participle_to_adjectives(
                word,
                prefix,
                form_parts,
                is_past=False,
            )

        emit_strong_derived_from_inf_sequence(
            ending=ending,
            vowel=vowel,
            probability=prob,
            umlaut_vowels=OENormalizer.iumlaut([vowel]),
            emit_form_for_vowel=emit_form_for_vowel,
            emit_sound_for_vowel=emit_sound_for_vowel,
            on_participle=on_participle,
            emit_imsg=emit_imsg,
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

        def emit_manual(
            sound_changed_form: str,
            source_form_parts: str,
            source_function: str,
            source_probability: str | int | None,
        ) -> None:
            self._generate_and_print_manual(
                formhash,
                sound_changed_form,
                source_form_parts,
                source_function,
                source_probability,
            )

        emit_sound_changed_forms(
            function=function,
            form=form,
            form_parts=form_parts,
            probability=prob,
            sound_change_prob_delta=sound_change_prob_delta,
            emit_manual=emit_manual,
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
        fh["probability"] = format_probability(prob)
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
        prob: str | int | None = 0
        use_item_shape = is_weak_item_shape_window(para_id_num)

        def emit_principal(
            emit_prefix: str,
            emit_pre_vowel: str,
            emit_vowel: str,
            emit_post_vowel: str,
            emit_boundary: str,
            emit_dental: str | None,
            emit_ending: str,
            emit_function: str,
            emit_prob: str | int | None,
        ) -> tuple[str, str]:
            return self._generate_and_print_form(
                formhash,
                emit_prefix,
                emit_pre_vowel,
                emit_vowel,
                emit_post_vowel,
                emit_boundary,
                emit_dental,
                emit_ending,
                emit_function,
                emit_prob,
            )

        fp = emit_weak_principal_form(
            para_id=para_id,
            prefix=prefix,
            default_parts=(pre_vowel, root_vowel_actual, post_vowel, boundary),
            item_parts=(item.pre_vowel, item.vowel, item.post_vowel, item.boundary),
            dental=dental,
            ending=ending,
            variant_id=variant_id,
            use_item_shape=use_item_shape,
            emit_form=emit_principal,
        )

        def on_pspt_participle(form_parts: str) -> None:
            self._add_participle_to_adjectives(
                word,
                prefix,
                form_parts,
                is_past=False,
            )

        def on_papt_participle(form_parts: str) -> None:
            self._add_participle_to_adjectives(
                word,
                prefix,
                form_parts,
                is_past=True,
            )

        def on_inf() -> None:
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

        def on_psinsg2() -> None:
            self._generate_weak_derived_from_psinsg2(
                formhash,
                prefix,
                pre_vowel,
                root_vowel_actual,
                post_vowel,
                boundary,
                prob,
            )

        def on_painsg1() -> None:
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

        dispatch_weak_principal_part_derivations(
            para_id=para_id,
            use_item_shape=use_item_shape,
            form_parts=fp,
            on_pspt_participle=on_pspt_participle,
            on_papt_participle=on_papt_participle,
            on_inf=on_inf,
            on_psinsg2=on_psinsg2,
            on_painsg1=on_painsg1,
        )

    def _generate_weak_derived_from_inf(  # noqa: PLR0912, PLR0913
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
        def emit_form(
            dental: str | None,
            ending: str,
            function: str,
            prob_value: str | int | None,
        ) -> tuple[str, str]:
            return self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                dental,
                ending,
                function,
                prob_value,
            )

        def on_participle(form_parts: str) -> None:
            self._add_participle_to_adjectives(
                word,
                prefix,
                form_parts,
                is_past=False,
            )

        emit_weak_derived_from_inf_sequence(
            class2=formhash.get("class2"),
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            original_ending=original_ending,
            probability=prob,
            emit_form=emit_form,
            on_participle=on_participle,
        )

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
        base_probability = probability_or_zero(prob)
        vowel_list = [vowel]

        # Perl unshifts the paradigm preterite vowel when infinitive and
        # preterite vowels differ in the exemplar.
        if vowel_inf and vowel_pa and vowel_inf != vowel_pa:
            vowel_list.insert(0, vowel_pa)

        for vcount, current_vowel in enumerate(vowel_list):
            curr_prob = base_probability + vcount

            def emit_form(
                ending: str,
                function: str,
                prob_value: str | int | None,
                *,
                _current_vowel: str = current_vowel,
            ) -> None:
                self._generate_and_print_form(
                    formhash,
                    prefix,
                    pre_vowel,
                    _current_vowel,
                    pv_simp,
                    boundary,
                    dental,
                    ending,
                    function,
                    prob_value,
                )

            def emit_manual(
                form: str,
                form_parts: str,
                function: str,
                prob_value: str | int | None,
            ) -> None:
                self._generate_and_print_manual(
                    formhash,
                    form,
                    form_parts,
                    function,
                    prob_value,
                )

            form_parts = emit_weak_derived_from_painsg1_variant(
                prefix=prefix,
                pre_vowel=pre_vowel,
                vowel=current_vowel,
                post_vowel_simple=pv_simp,
                boundary=boundary,
                dental=dental,
                probability=curr_prob,
                emit_form=emit_form,
                emit_manual=emit_manual,
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
        probability_plus_one = probability_plus(
            probability,
            delta=1,
            empty_default=1,
        )
        # Perl: $post_vowel =~ s/(.)\1/$1/;
        pv_simp = re.sub(r"(.)\1", r"\1", post_vowel)

        def emit_form(
            ending: str,
            function: str,
            prob_value: str | int | None,
        ) -> None:
            self._generate_and_print_form(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                pv_simp,
                boundary,
                None,
                ending,
                function,
                prob_value,
            )

        def emit_sound(
            ending: str,
            function: str,
            prob_value: str | int | None,
            consonant_change_prob: int,
        ) -> None:
            self._generate_and_print_form_with_sound_changes(
                formhash,
                prefix,
                pre_vowel,
                vowel,
                pv_simp,
                boundary,
                None,
                ending,
                function,
                prob_value,
                consonant_change_prob,
            )

        emit_weak_derived_from_psinsg2(
            probability=probability,
            probability_plus_one=probability_plus_one,
            emit_form=emit_form,
            emit_sound=emit_sound,
        )


def generate_vbforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Wrapper for VerbFormGenerator.

    Args:
        session: The session.
        output_file: The output file.

    """
    from ..generation.verb_engine import VerbFormOrchestrator

    orchestrator = VerbFormOrchestrator(session, output_file)
    orchestrator.generate()


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
