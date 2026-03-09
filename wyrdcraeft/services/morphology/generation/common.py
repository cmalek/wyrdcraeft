# ruff: noqa: I001,PLR0913,ARG002,D417,RUF100,PLC0415
from functools import partial
from typing import Final

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    _ParadigmVariantDispatchContext,
    _SoundChangeDispatchContext,
    _StrongPrincipalPartContext,
    _StrongInfDerivationContext,
    _VariantPartDispatchContext,
    _WeakPrincipalPartContext,
    _WeakInfDerivationContext,
    _WeakPainsg1DerivationContext,
    _WeakPsinsg2DerivationContext,
    VerbParadigm,
    Word,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from .form_rows import generate_and_print_form as _generate_and_print_form
from .form_rows import generate_and_print_manual as _generate_and_print_manual
from .form_rows import emit_form_for_context as _emit_form_for_context_row
from .form_rows import emit_imsg_for_context as _emit_imsg_for_context_row
from .form_rows import output_manual_forms as _output_manual_forms
from .form_rows import print_one_form as _print_one_form
from .paradigm_flow import (
    build_verb_formhash_base,
    derive_part_post_vowel as _derive_part_post_vowel,
    derive_part_pre_vowel as _derive_part_pre_vowel,
    derive_part_prefix as _derive_part_prefix,
    derive_part_stem_segments as _derive_part_stem_segments,
    derive_paradigm_seed_vowels,
    dispatch_paradigm_variants,
    dispatch_variant_parts,
)
from .participles import build_participle_adjective
from .scalar_utils import nz as _nz_scalar
from .scalar_utils import perl_numify as _perl_numify
from .shared import FormOutput
from . import strong_derivation_flow as _strong_derivation_flow
from .strong_principal_flow import (
    emit_strong_principal_form_for_vowel as _emit_strong_principal_form_for_vowel,
    emit_strong_principal_inf_derivation as _emit_strong_principal_inf_derivation,
    emit_strong_principal_participle as _emit_strong_principal_participle,
    generate_strong_verb_parts as _generate_strong_verb_parts,
)
from . import weak_derivation_flow as _weak_derivation_flow
from . import sound_dispatch_flow as _sound_dispatch_flow
from . import weak_principal_flow as _weak_principal_flow


def nz(val: str | int | None) -> str:
    """
    Treat '0' or None as empty string for logic checks, matching Perl's falsy
    behavior for these strings.

    Args:
        val: The value to check.

    Returns:
        The value as a string.

    """
    return _nz_scalar(val)


def perl_numify(val: str) -> float:
    """
    Approximate Perl scalar-to-number coercion for ``==`` comparisons.

    Args:
        val: Value to coerce.

    Returns:
        Numeric value extracted from the start of ``val``, or ``0.0``.

    """
    return _perl_numify(val)


def output_manual_forms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Output manual forms to the output file. Perl load_forms prints each form
    to OUTPUT first; Python must match this behavior for parity.

    Args:
        session: The generator session (contains manual_forms).
        output_file: The output file handle.

    """
    _output_manual_forms(session, output_file)


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
    _print_one_form(session, form_data, output_file)


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
        context = _ParadigmVariantDispatchContext(word=word, paradigm=vp)

        dispatch_paradigm_variants(
            variants=vp.variants,
            formhash_base=formhash_base,
            boundary_inf=boundary_inf,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            on_variant=partial(self._dispatch_variant_context, context),
        )

    def _dispatch_variant_context(
        self,
        context: _ParadigmVariantDispatchContext,
        variant: ParadigmVariant,
        formhash_base: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Dispatch one paradigm variant using shared typed callback context.

        Side Effects:
            Delegates one variant traversal through ``_process_variant``.

        Args:
            context: Shared paradigm-level dispatch context.
            variant: Active variant being dispatched.
            formhash_base: Variant-scoped form hash payload.
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        self._process_variant(
            context.word,
            context.paradigm,
            variant,
            formhash_base,
            boundary_inf,
            vowel_inf,
            vowel_pa,
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
        context = _VariantPartDispatchContext(
            word=word,
            paradigm=vp,
            variant=variant,
        )
        dispatch_variant_parts(
            variant=variant,
            formhash_var=formhash_base,
            boundary_inf=boundary_inf,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            on_part=partial(self._dispatch_part_context, context),
        )

    def _dispatch_part_context(
        self,
        context: _VariantPartDispatchContext,
        item: ParadigmPart,
        formhash_var: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Dispatch one variant part using shared typed callback context.

        Side Effects:
            Delegates one part traversal through ``_process_part``.

        Args:
            context: Shared variant-level dispatch context.
            item: Active part being dispatched.
            formhash_var: Variant-scoped form hash payload.
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        self._process_part(
            context.word,
            context.paradigm,
            context.variant,
            item,
            formhash_var,
            boundary_inf,
            vowel_inf,
            vowel_pa,
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
        return _derive_part_stem_segments(word, item, boundary_inf)

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
        return _derive_part_prefix(word, item)

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
        return _derive_part_post_vowel(word, item, boundary_inf)

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
        return _derive_part_pre_vowel(word)

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
        return _generate_and_print_form(
            self.session,
            self.output_file,
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            dental,
            ending,
            function,
            prob=prob,
        )

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
        return _emit_form_for_context_row(
            self.session,
            self.output_file,
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
        _sound_dispatch_flow.emit_sound_changed_form_for_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            ending,
            function,
            prob,
            dental=dental,
            sound_change_prob_delta=sound_change_prob_delta,
            emit_with_sound_changes=self._generate_and_print_form_with_sound_changes,
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
        _emit_imsg_for_context_row(
            self.session,
            self.output_file,
            formhash,
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            prob,
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
        return _strong_derivation_flow.emit_strong_vowel_form_context(
            formhash,
            prefix,
            pre_vowel,
            post_vowel,
            boundary,
            active_vowel,
            ending,
            function,
            prob,
            emit_form_for_context=self._emit_form_for_context,
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
        _strong_derivation_flow.emit_strong_vowel_sound_context(
            formhash,
            prefix,
            pre_vowel,
            post_vowel,
            boundary,
            active_vowel,
            ending,
            function,
            prob,
            emit_sound_for_context=self._emit_sound_changed_form_for_context,
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
        _strong_derivation_flow.emit_strong_inf_derivation_for_context(
            formhash,
            word,
            prefix,
            pre_vowel,
            post_vowel,
            boundary,
            ending,
            active_vowel,
            prob,
            generate_strong_derived_from_inf=self._generate_strong_derived_from_inf,
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
        return _weak_derivation_flow.emit_weak_inf_form(
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
            emit_weak_principal_form=self._emit_weak_principal_form_context,
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
        return _weak_derivation_flow.emit_weak_painsg1_form_for_vowel(
            formhash,
            prefix,
            pre_vowel,
            boundary,
            dental,
            current_vowel,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form=self._generate_and_print_form,
        )

    def _emit_weak_painsg1_form_for_vowel_derivation_context(
        self,
        context: _WeakPainsg1DerivationContext,
        current_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> tuple[str, str]:
        """
        Emit one ``PaInSg1`` form row from a pre-bound weak derivation context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            current_vowel: Active vowel for this variant.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_painsg1_form_for_vowel_from_context(
            context,
            current_vowel,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_for_vowel=self._emit_weak_painsg1_form_for_vowel_context,
        )

    def _emit_weak_painsg1_manual_context(
        self,
        context: _WeakPainsg1DerivationContext,
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit one manual row from a pre-bound weak ``PaInSg1`` context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            form: Emitted surface form.
            form_parts: Structured form-parts payload.
            function: Morphological function code.
            prob: Optional probability annotation.

        """
        _weak_derivation_flow.emit_weak_painsg1_manual_context(
            context,
            form,
            form_parts,
            function,
            prob,
            emit_manual=self._generate_and_print_manual,
        )

    def _emit_weak_painsg1_participle_context(
        self, context: _WeakPainsg1DerivationContext, form_parts: str
    ) -> None:
        """
        Attach a past participle emitted from a weak ``PaInSg1`` branch.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak ``PaInSg1`` derivation context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_derivation_flow.emit_weak_painsg1_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
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
        _weak_derivation_flow.emit_weak_psinsg2_form_with_post_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            boundary,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_with_post=self._generate_and_print_form,
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
        _weak_derivation_flow.emit_weak_psinsg2_sound_with_post_context(
            formhash,
            prefix,
            pre_vowel,
            vowel,
            boundary,
            ending,
            function,
            prob,
            consonant_change_prob,
            post_vowel_simple,
            emit_sound_with_post=self._generate_and_print_form_with_sound_changes,
        )

    def _emit_weak_psinsg2_form_with_post_derivation_context(
        self,
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> None:
        """
        Emit one weak ``PsInSg2`` form row from a pre-bound derivation context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak ``PsInSg2`` derivation context.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            post_vowel_simple: Simplified post-vowel segment.

        """
        _weak_derivation_flow.emit_weak_psinsg2_form_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            post_vowel_simple,
            emit_form_with_post_context=self._emit_weak_psinsg2_form_with_post_context,
        )

    def _emit_weak_psinsg2_sound_with_post_derivation_context(
        self,
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        prob: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
    ) -> None:
        """
        Emit one weak ``PsInSg2`` sound-change row from a pre-bound context.

        Side Effects:
            Writes generated and sound-changed rows to the output stream.

        Args:
            context: Shared weak ``PsInSg2`` derivation context.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.
            consonant_change_prob: Probability delta used by sound changes.
            post_vowel_simple: Simplified post-vowel segment.

        """
        _weak_derivation_flow.emit_weak_psinsg2_sound_with_post_derivation_context(
            context,
            ending,
            function,
            prob,
            consonant_change_prob,
            post_vowel_simple,
            emit_sound_with_post_context=self._emit_weak_psinsg2_sound_with_post_context,
        )

    def _emit_strong_principal_form_for_vowel_context(
        self,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        """
        Emit one strong principal-part row for a selected active vowel.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared strong principal-part context.
            active_vowel: Active stem vowel for this emitted row.
            ending: Morphological ending.
            function: Morphological function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _emit_strong_principal_form_for_vowel(
            context,
            active_vowel,
            ending,
            function,
            prob,
            emit_strong_vowel_form=self._emit_strong_vowel_form_context,
        )

    def _emit_strong_principal_participle_context(
        self, context: _StrongPrincipalPartContext, form_parts: str
    ) -> None:
        """
        Attach a past participle emitted from a strong principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared strong principal-part context.
            form_parts: Form-parts payload for the derived participle.

        """
        _emit_strong_principal_participle(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_strong_principal_inf_derivation_context(
        self,
        context: _StrongPrincipalPartContext,
        active_vowel: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit strong infinitive-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared strong principal-part context.
            active_vowel: Active stem vowel for this derivation branch.
            prob: Optional probability annotation.

        """
        _emit_strong_principal_inf_derivation(
            context,
            active_vowel,
            prob,
            emit_strong_inf_derivation_for_context=self._emit_strong_inf_derivation_context,
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
        _generate_strong_verb_parts(
            formhash=formhash,
            word=word,
            item=item,
            prefix=prefix,
            pre_vowel=pre_vowel,
            post_vowel=post_vowel,
            emit_form_for_vowel=self._emit_strong_principal_form_for_vowel_context,
            on_papt_participle=self._emit_strong_principal_participle_context,
            on_inf=self._emit_strong_principal_inf_derivation_context,
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
        _strong_derivation_flow.generate_strong_derived_from_inf(
            formhash=formhash,
            word=word,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            ending=ending,
            probability=prob,
            emit_form_for_vowel=self._emit_strong_derived_inf_form_for_vowel_context,
            emit_sound_for_vowel=self._emit_strong_derived_inf_sound_for_vowel_context,
            on_participle=self._emit_strong_derived_inf_participle_context,
            emit_imsg=self._emit_strong_derived_inf_imsg_context,
        )

    def _emit_strong_derived_inf_form_for_vowel_context(
        self,
        context: _StrongInfDerivationContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        """
        Emit one strong infinitive-derived row for a selected active vowel.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared strong-derivation emission context.
            active_vowel: Active vowel used for the emitted row.
            ending: Ending segment for the emitted row.
            function: Morphology function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _strong_derivation_flow.emit_strong_derived_inf_form_for_vowel_context(
            context,
            active_vowel,
            ending,
            function,
            prob,
            emit_strong_vowel_form_context=self._emit_strong_vowel_form_context,
        )

    def _emit_strong_derived_inf_sound_for_vowel_context(
        self,
        context: _StrongInfDerivationContext,
        active_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        """
        Emit sound-change rows for one strong infinitive-derived vowel branch.

        Side Effects:
            Writes one or more rows to the morphology output stream.

        Args:
            context: Shared strong-derivation emission context.
            active_vowel: Active vowel used for source-row assembly.
            ending: Ending segment for the source row.
            function: Morphology function code.
            prob: Optional probability annotation.

        """
        _strong_derivation_flow.emit_strong_derived_inf_sound_for_vowel_context(
            context,
            active_vowel,
            ending,
            function,
            prob,
            emit_strong_vowel_sound_context=self._emit_strong_vowel_sound_context,
        )

    def _emit_strong_derived_inf_participle_context(
        self, context: _StrongInfDerivationContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from infinitive-derived strong rows.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared strong-derivation emission context.
            form_parts: Form-parts payload for the derived participle.

        """
        _strong_derivation_flow.emit_strong_derived_inf_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_strong_derived_inf_imsg_context(
        self, context: _StrongInfDerivationContext, prob: str | int | None
    ) -> None:
        """
        Emit the strong imperative-singular derivative for infinitive branches.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared strong-derivation emission context.
            prob: Optional probability annotation.

        """
        _strong_derivation_flow.emit_strong_derived_inf_imsg_context(
            context,
            prob,
            emit_imsg_for_context=self._emit_imsg_for_context,
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
            sound_change_prob_delta: Probability increment for derived rows.

        """  # noqa: E501
        _sound_dispatch_flow.generate_and_print_form_with_sound_changes(
            formhash=formhash,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            dental=dental,
            ending=ending,
            function=function,
            probability=prob,
            sound_change_prob_delta=sound_change_prob_delta,
            emit_source_form_with_context=self._emit_source_form_with_sound_dispatch_context,
            emit_manual_with_context=self._emit_manual_sound_changed_dispatch_context,
        )

    def _emit_source_form_with_sound_dispatch_context(
        self, context: _SoundChangeDispatchContext
    ) -> tuple[str, str]:
        """
        Emit the source row for sound-change derivations using dispatch context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared source-row dispatch context.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _sound_dispatch_flow.emit_source_form_with_sound_dispatch_context(
            context,
            emit_source_form_with_sound_context_callback=self._emit_source_form_with_sound_context,
        )

    def _emit_source_form_with_sound_context(  # noqa: PLR0913
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
        Emit the source row used for downstream sound-change derivations.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The form hash.
            prefix: The prefix segment.
            pre_vowel: The pre-vowel segment.
            vowel: The active vowel segment.
            post_vowel: The post-vowel segment.
            boundary: The boundary segment.
            dental: The optional weak dental segment.
            ending: The ending segment.
            function: The function code.
            prob: Optional source-row probability annotation.

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

    def _emit_manual_sound_changed_dispatch_context(
        self,
        context: _SoundChangeDispatchContext,
        sound_changed_form: str,
        source_form_parts: str,
        source_function: str,
        source_probability: str | int | None,
    ) -> None:
        """
        Emit one manual sound-change row using shared dispatch context.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared source-row dispatch context.
            sound_changed_form: The emitted sound-changed form text.
            source_form_parts: The source form-parts payload.
            source_function: The morphology function code.
            source_probability: Optional probability annotation.

        """
        _sound_dispatch_flow.emit_manual_sound_changed_dispatch_context(
            context,
            sound_changed_form,
            source_form_parts,
            source_function,
            source_probability,
            emit_manual_sound_changed_context_callback=self._emit_manual_sound_changed_context,
        )

    def _emit_manual_sound_changed_context(
        self,
        formhash: dict[str, str],
        sound_changed_form: str,
        source_form_parts: str,
        source_function: str,
        source_probability: str | int | None,
    ) -> None:
        """
        Emit one manually assembled row for a sound-changed derivative.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            formhash: The form hash.
            sound_changed_form: The emitted sound-changed form text.
            source_form_parts: The source form-parts payload.
            source_function: The morphology function code.
            source_probability: Optional probability annotation.

        """
        self._generate_and_print_manual(
            formhash,
            sound_changed_form,
            source_form_parts,
            source_function,
            source_probability,
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
        _generate_and_print_manual(
            self.session,
            self.output_file,
            formhash,
            form,
            form_parts,
            function,
            prob,
        )

    def _emit_weak_principal_pspt_participle_context(
        self, context: _WeakPrincipalPartContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from a weak principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_principal_flow.emit_weak_principal_pspt_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_principal_papt_participle_context(
        self, context: _WeakPrincipalPartContext, form_parts: str
    ) -> None:
        """
        Attach a past participle emitted from a weak principal-part row.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak principal-part context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_principal_flow.emit_weak_principal_papt_participle_context(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
        )

    def _emit_weak_principal_inf_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak infinitive-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        """
        _weak_principal_flow.emit_weak_principal_inf_derivation_context(
            context,
            generate_weak_derived_from_inf=self._generate_weak_derived_from_inf,
        )

    def _emit_weak_principal_psinsg2_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak ``PsInSg2``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows to the morphology output stream.

        Args:
            context: Shared weak principal-part context.

        """
        _weak_principal_flow.emit_weak_principal_psinsg2_derivation_context(
            context,
            generate_weak_derived_from_psinsg2=self._generate_weak_derived_from_psinsg2,
        )

    def _emit_weak_principal_painsg1_derivation_context(
        self, context: _WeakPrincipalPartContext
    ) -> None:
        """
        Emit weak ``PaInSg1``-derived rows from a principal-part context.

        Side Effects:
            Writes generated rows and participle side effects to output/session.

        Args:
            context: Shared weak principal-part context.

        """
        _weak_principal_flow.emit_weak_principal_painsg1_derivation_context(
            context,
            generate_weak_derived_from_painsg1=self._generate_weak_derived_from_painsg1,
        )

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
        _weak_principal_flow.generate_weak_verb_parts_with_context(
            formhash=formhash,
            word=word,
            item=item,
            prefix=prefix,
            pre_vowel=pre_vowel,
            root_vowel_actual=root_vowel_actual,
            post_vowel=post_vowel,
            variant_id=variant_id,
            para_id_num=para_id_num,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            emit_form_for_context=self._emit_weak_principal_form_context,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
            generate_weak_derived_from_inf=self._generate_weak_derived_from_inf,
            generate_weak_derived_from_psinsg2=self._generate_weak_derived_from_psinsg2,
            generate_weak_derived_from_painsg1=self._generate_weak_derived_from_painsg1,
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
        _weak_derivation_flow.generate_weak_derived_from_inf(
            formhash=formhash,
            word=word,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            original_ending=original_ending,
            probability=prob,
            emit_form=self._emit_weak_derived_inf_form_context,
            on_participle=self._emit_weak_derived_inf_participle_context,
        )

    def _emit_weak_derived_inf_form_context(
        self,
        context: _WeakInfDerivationContext,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        """
        Emit one weak infinitive-derived row for a selected dental/ending pair.

        Side Effects:
            Writes one row to the morphology output stream.

        Args:
            context: Shared weak-derivation emission context.
            dental: Optional weak-dental segment for the emitted row.
            ending: Ending segment for the emitted row.
            function: Morphology function code.
            prob: Optional probability annotation.

        Returns:
            Two-item tuple of emitted ``(form, form_parts)``.

        """
        return _weak_derivation_flow.emit_weak_derived_inf_form(
            context,
            dental,
            ending,
            function,
            prob,
            emit_weak_inf_form=self._emit_weak_inf_form_context,
        )

    def _emit_weak_derived_inf_participle_context(
        self, context: _WeakInfDerivationContext, form_parts: str
    ) -> None:
        """
        Attach a present participle emitted from infinitive-derived weak rows.

        Side Effects:
            Adds one adjective-row candidate to session state.

        Args:
            context: Shared weak-derivation emission context.
            form_parts: Form-parts payload for the derived participle.

        """
        _weak_derivation_flow.emit_weak_derived_inf_participle(
            context,
            form_parts,
            add_participle_to_adjectives=self._add_participle_to_adjectives,
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
        _weak_derivation_flow.generate_weak_derived_from_painsg1(
            formhash=formhash,
            word=word,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            dental=dental,
            vowel_inf=vowel_inf,
            vowel_pa=vowel_pa,
            probability=prob,
            emit_form_for_vowel=self._emit_weak_painsg1_form_for_vowel_derivation_context,
            emit_manual=self._emit_weak_painsg1_manual_context,
            on_participle=self._emit_weak_painsg1_participle_context,
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
        _weak_derivation_flow.generate_weak_derived_from_psinsg2(
            formhash=formhash,
            prefix=prefix,
            pre_vowel=pre_vowel,
            vowel=vowel,
            post_vowel=post_vowel,
            boundary=boundary,
            probability=prob,
            emit_form_with_post=self._emit_weak_psinsg2_form_with_post_derivation_context,
            emit_sound_with_post=self._emit_weak_psinsg2_sound_with_post_derivation_context,
        )


def generate_vbforms(session: GeneratorSession, output_file: FormOutput) -> None:
    """
    Wrapper for VerbFormGenerator.

    Args:
        session: The session.
        output_file: The output file.

    """
    from .verb_engine import VerbFormOrchestrator

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
    Delegate adverb form generation to the extracted module.

    Args:
        session: Active morphology generator session.
        output_file: Output stream receiving generated rows.

    """
    from .adv_forms import generate_advforms as _generate_advforms

    _generate_advforms(session, output_file)


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
