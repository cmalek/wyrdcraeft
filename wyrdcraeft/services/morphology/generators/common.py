import re
from functools import partial
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from ..generation.form_assembly import assemble_form_parts, materialize_form
from ..generation.paradigm_flow import (
    build_verb_formhash_base,
    derive_paradigm_seed_vowels,
    dispatch_paradigm_variants,
    dispatch_variant_parts,
)
from ..generation.participles import build_participle_adjective
from ..generation.probability import (
    format_probability,
)
from ..generation.shared import FormOutput
from ..generation.sound_changes import (
    emit_sound_changed_from_source,
)
from ..generation.strong_inflections import (
    emit_strong_principal_part_sequence,
    emit_strong_derived_from_inf_sequence,
)
from ..generation.weak_inflections import (
    emit_weak_derived_from_inf_sequence,
    emit_weak_derived_from_painsg1_context,
    emit_weak_derived_from_psinsg2_context,
    emit_weak_principal_part_sequence,
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

    def __init__(self, session: GeneratorSession, output_file: FormOutput) -> None:
        """
        Initialize the verb-form generator context.

        Args:
            session: Active generation session containing loaded lexemes.
            output_file: Output handle receiving generated form rows.

        """
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
        formhash_base = build_verb_formhash_base(word, vp)
        boundary_inf, vowel_inf, vowel_pa = derive_paradigm_seed_vowels(vp)

        dispatch_paradigm_variants(
            variants=vp.variants,
            formhash_base=formhash_base,
            boundary_inf=boundary_inf,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            on_variant=partial(self._process_variant, word, vp),
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
        dispatch_variant_parts(
            variant=variant,
            formhash_var=formhash_base,
            boundary_inf=boundary_inf,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            on_part=partial(self._process_part, word, vp, variant),
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
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """  # noqa: E501
        prefix, pre_vowel, actual_vowel, post_vowel = self._derive_part_stem_segments(
            word,
            item,
            boundary_inf,
        )

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

    def _derive_part_stem_segments(
        self,
        word: Word,
        item: ParadigmPart,
        boundary_inf: str,
    ) -> tuple[str, str, str, str]:
        """
        Bind stem segments used by strong and weak part generators.

        Side Effects:
            None.

        Args:
            word: Active lexeme record.
            item: Active paradigm part.
            boundary_inf: Infinitive boundary from variant ``0``.

        Returns:
            Four-item tuple ``(prefix, pre_vowel, vowel, post_vowel)``.

        """
        prefix = self._get_prefix(word, item)
        post_vowel = self._get_post_vowel(word, item, boundary_inf)
        pre_vowel, actual_vowel = self._get_pre_vowel(word)
        return prefix, pre_vowel, actual_vowel, post_vowel

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

    def _emit_form_for_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        *,
        dental: str | None = "",
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        """
        Emit one generated form for a fixed stem context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            function: Morphological function code.

        Keyword Args:
            dental: Dental segment for weak forms.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
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
            prob,
        )

    def _emit_sound_changed_form_for_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        prob: str | int | None,
        *,
        dental: str | None = "",
        sound_change_prob_delta: int = 1,
    ) -> None:
        """
        Emit one source row and its sound-change derivatives for a stem context.

        Side Effects:
            Writes generated and derived rows to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation for the source row.

        Keyword Args:
            dental: Dental segment for weak-form contexts.
            sound_change_prob_delta: Probability delta used on derived forms.

        """
        self._generate_and_print_form_with_sound_changes(
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
            sound_change_prob_delta=sound_change_prob_delta,
        )

    def _emit_imsg_for_context(  # noqa: PLR0913
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
        Emit the imperative-singular row for one fixed stem context.

        Side Effects:
            Writes one ``ImSg`` row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            prob: Optional probability annotation.

        """
        self._emit_form_for_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            "0",
            "ImSg",
            prob=prob,
        )

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

    def _emit_strong_vowel_form_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        post_vowel: str,
        boundary: str,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        """
        Emit one strong-form row for a pre-bound stem context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            active_vowel: Active ablaut/umlaut vowel.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_form_for_context(
            formhash,
            prefix,
            pre_vowel,
            active_vowel,
            post_vowel,
            boundary,
            ending,
            function,
            prob=prob,
        )

    def _emit_strong_vowel_sound_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        post_vowel: str,
        boundary: str,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit strong sound-changed rows for one pre-bound stem context.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            active_vowel: Active ablaut/umlaut vowel.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        """
        self._emit_sound_changed_form_for_context(
            formhash,
            prefix,
            pre_vowel,
            active_vowel,
            post_vowel,
            boundary,
            ending,
            function,
            prob,
        )

    def _emit_strong_inf_derivation_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        word: Word,
        prefix: str,
        pre_vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        active_vowel: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit strong infinitive-derived rows for one selected active vowel.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            formhash: The mutable form metadata hash.
            word: Active lexeme record.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            active_vowel: Active ablaut/umlaut vowel.
            prob: Optional probability annotation.

        """
        self._generate_strong_derived_from_inf(
            formhash,
            word,
            prefix,
            pre_vowel,
            active_vowel,
            post_vowel,
            boundary,
            ending,
            prob,
        )

    def _emit_weak_principal_form_context(  # noqa: PLR0913
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
    ) -> tuple[str, str]:
        """
        Emit one weak principal-form row for a pre-bound stem context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            dental: Dental segment for weak forms.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_form_for_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            ending,
            function,
            dental=dental,
            prob=prob,
        )

    def _emit_weak_inf_form_context(  # noqa: PLR0913
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
    ) -> tuple[str, str]:
        """
        Emit one weak infinitive-derived row for a pre-bound stem context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            post_vowel: Stem segment after the active vowel.
            boundary: Boundary consonant segment.
            dental: Dental segment for weak forms.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._emit_weak_principal_form_context(
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

    def _emit_weak_painsg1_form_for_vowel_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        boundary: str,
        dental: str,
        current_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> tuple[str, str]:
        """
        Emit one ``PaInSg1`` weak form row for a selected vowel variant.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            boundary: Boundary consonant segment.
            dental: Weak dental suffix segment.
            current_vowel: Active vowel for this variant.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            current_vowel,
            post_vowel_simple,
            boundary,
            dental,
            ending,
            function,
            prob,
        )

    def _emit_weak_psinsg2_form_with_post_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        boundary: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> None:
        """
        Emit one weak ``PsInSg2``-branch form row with simplified post-vowel.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment.

        """
        self._generate_and_print_form(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel_simple,
            boundary,
            None,
            ending,
            function,
            prob,
        )

    def _emit_weak_psinsg2_sound_with_post_context(  # noqa: PLR0913
        self,
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        boundary: str,
        ending: str,
        function: str,
        prob: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
    ) -> None:
        """
        Emit one weak ``PsInSg2`` sound-change branch with simplified post-vowel.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            formhash: The mutable form metadata hash.
            prefix: Prefix segment.
            pre_vowel: Stem segment before the active vowel.
            vowel: Active vowel segment.
            boundary: Boundary consonant segment.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            consonant_change_prob: Probability delta used by sound changes.
            post_vowel_simple: Simplified post-vowel segment.

        """
        self._generate_and_print_form_with_sound_changes(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel_simple,
            boundary,
            None,
            ending,
            function,
            prob,
            sound_change_prob_delta=consonant_change_prob,
        )

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
        emit_strong_principal_part_sequence(
            para_id=para_id,
            ending=ending,
            vowels=[item.vowel],
            emit_form_for_vowel=partial(
                self._emit_strong_vowel_form_context,
                formhash,
                prefix,
                pre_vowel,
                post_vowel,
                boundary,
            ),
            on_papt_form_parts=partial(
                self._add_participle_to_adjectives,
                word,
                prefix,
                is_past=True,
            ),
            on_inf=partial(
                self._emit_strong_inf_derivation_context,
                formhash,
                word,
                prefix,
                pre_vowel,
                post_vowel,
                boundary,
                ending,
            ),
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

        Note:
            Wright (``Old English Grammar``, §§474-475) describes strong verbs
            as deriving preterite and participle stems by vowel alternation
            (ablaut) across a fixed stem set. This routine emits those
            infinitive-derived rows in that legacy order. Tichý (2017, p. 43)
            keeps the same traditional strong/weak split for transparent
            morphological analysis.

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
        emit_strong_derived_from_inf_sequence(
            ending=ending,
            vowel=vowel,
            probability=prob,
            umlaut_vowels=OENormalizer.iumlaut([vowel]),
            emit_form_for_vowel=partial(
                self._emit_strong_vowel_form_context,
                formhash,
                prefix,
                pre_vowel,
                post_vowel,
                boundary,
            ),
            emit_sound_for_vowel=partial(
                self._emit_strong_vowel_sound_context,
                formhash,
                prefix,
                pre_vowel,
                post_vowel,
                boundary,
            ),
            on_participle=partial(
                self._add_participle_to_adjectives,
                word,
                prefix,
                is_past=False,
            ),
            emit_imsg=partial(
                self._emit_imsg_for_context,
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
            ),
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
        def emit_source_form() -> tuple[str, str]:
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

        emit_sound_changed_from_source(
            function=function,
            probability=prob,
            sound_change_prob_delta=sound_change_prob_delta,
            emit_source_form=emit_source_form,
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

        Args:
            formhash: The form hash.
            form: The generated form text.
            form_parts: The generated form-parts payload.
            function: The morphology function code.
            prob: The probability annotation.

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
        emit_weak_principal_part_sequence(
            para_id=para_id,
            para_id_num=para_id_num,
            variant_id=variant_id,
            prefix=prefix,
            default_parts=(pre_vowel, root_vowel_actual, post_vowel, boundary),
            item_parts=(item.pre_vowel, item.vowel, item.post_vowel, item.boundary),
            dental=dental,
            ending=ending,
            emit_form=partial(self._emit_weak_principal_form_context, formhash),
            on_pspt_participle=partial(
                self._add_participle_to_adjectives,
                word,
                prefix,
                is_past=False,
            ),
            on_papt_participle=partial(
                self._add_participle_to_adjectives,
                word,
                prefix,
                is_past=True,
            ),
            on_inf=partial(
                self._generate_weak_derived_from_inf,
                formhash,
                word,
                prefix,
                pre_vowel,
                root_vowel_actual,
                post_vowel,
                boundary,
                ending,
                prob,
            ),
            on_psinsg2=partial(
                self._generate_weak_derived_from_psinsg2,
                formhash,
                prefix,
                pre_vowel,
                root_vowel_actual,
                post_vowel,
                boundary,
                prob,
            ),
            on_painsg1=partial(
                self._generate_weak_derived_from_painsg1,
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
            ),
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

        Note:
            Wright (``Old English Grammar``, §§474 and 520) describes weak
            verbs as forming preterites and participles with dental suffixes.
            This helper keeps that weak-class dental sequencing in the same
            deterministic order used by the legacy generator and by Tichý's
            class-based analyzer design (2017, p. 43).

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
        emit_weak_derived_from_inf_sequence(
            class2=formhash.get("class2"),
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            original_ending=original_ending,
            probability=prob,
            emit_form=partial(
                self._emit_weak_inf_form_context,
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
            ),
            on_participle=partial(
                self._add_participle_to_adjectives,
                word,
                prefix,
                is_past=False,
            ),
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
        emit_weak_derived_from_painsg1_context(
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            dental=dental,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            probability=prob,
            emit_form_for_vowel=partial(
                self._emit_weak_painsg1_form_for_vowel_context,
                formhash,
                prefix,
                pre_vowel,
                boundary,
                dental,
            ),
            emit_manual=partial(self._generate_and_print_manual, formhash),
            on_participle=partial(
                self._add_participle_to_adjectives,
                word,
                prefix,
                is_past=True,
            ),
        )

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

        Args:
            formhash: The form hash.
            prefix: The prefix segment.
            pre_vowel: The pre-vowel segment.
            vowel: The active vowel segment.
            post_vowel: The post-vowel segment.
            boundary: The boundary segment.
            prob: The probability annotation.

        """
        emit_weak_derived_from_psinsg2_context(
            probability=prob,
            post_vowel=post_vowel,
            emit_form_with_post=partial(
                self._emit_weak_psinsg2_form_with_post_context,
                formhash,
                prefix,
                pre_vowel,
                vowel,
                boundary,
            ),
            emit_sound_with_post=partial(
                self._emit_weak_psinsg2_sound_with_post_context,
                formhash,
                prefix,
                pre_vowel,
                vowel,
                boundary,
            ),
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
    """
    Delegate adjective form generation to the extracted module.

    Args:
        session: Active morphology generator session.
        output_file: Output stream receiving generated rows.

    """
    from .adj_forms import generate_adjforms as _generate_adjforms

    _generate_adjforms(session, output_file)


def generate_advforms(session, output_file):
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


def generate_numforms(session, output_file):
    """
    Delegate numeral form generation to the extracted module.

    Args:
        session: Active morphology generator session.
        output_file: Output stream receiving generated rows.

    """
    from .num_forms import generate_numforms as _generate_numforms

    _generate_numforms(session, output_file)


def generate_nounforms(session, output_file):
    """
    Delegate noun form generation to the extracted module.

    Args:
        session: Active morphology generator session.
        output_file: Output stream receiving generated rows.

    """
    from .noun_forms import generate_nounforms as _generate_nounforms

    _generate_nounforms(session, output_file)
