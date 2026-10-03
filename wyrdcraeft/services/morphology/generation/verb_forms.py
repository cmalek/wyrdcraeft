"""Verb generation orchestrator: walk words/paradigms and route to Strong or Weak."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
    _ParadigmVariantDispatchContext,
    _VariantPartDispatchContext,
)
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologyStage,
)
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .scalar_utils import nz
from .strong_verb_forms import StrongVerbGenerator
from .weak_verb_forms import WeakVerbGenerator

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GenerationRunState, WordPool

    from .shared import FormOutput


class VerbFormGenerator:
    """
    Generator for Old English verb forms.

    Args:
        word_pool: Categorized word pool containing loaded lexemes.
        run_state: Cross-stage scalar run state for this run.
        output_file: The output file.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Initialize the verb-form generator context.

        Args:
            word_pool: Categorized word pool containing loaded lexemes.
            run_state: Cross-stage scalar run state for this run.
            output_file: Output handle receiving generated form rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Categorized word pool containing loaded lexemes.
        self.word_pool = word_pool
        #: Cross-stage scalar run state for this run.
        self.run_state = run_state
        #: The output file.
        self.output_file = output_file
        #: Optional live progress coordinator.
        self.progress = progress
        #: Collaborator handling strong-paradigm verb form generation.
        self._strong_generator = StrongVerbGenerator(word_pool, run_state, output_file)
        #: Collaborator handling weak-paradigm verb form generation.
        self._weak_generator = WeakVerbGenerator(word_pool, run_state, output_file)

    def generate(self) -> None:
        """Main entry point to generate all verb forms."""
        for word in self.word_pool.words:
            if word.verb == 1 and (word.pspart + word.papart == 0):
                if self.progress is not None:
                    self.progress.advance(
                        MorphologyStage.VERBS,
                        lemma=word.title,
                        wright=word.wright,
                        forms_written=self.run_state.output_counter,
                    )
                self._process_word(word)

    def _process_word(self, word: Word) -> None:
        """
        Process a single word's paradigms.

        Args:
            word: The word to process.

        """
        for vp in word.vb_paradigm:
            self._process_paradigm(word, vp)

    def _build_verb_formhash_base(self, word: Word, vp: VerbParadigm) -> dict[str, str]:
        """
        Build the base metadata hash used for all emitted verb forms.

        Args:
            word: Lexeme record currently being generated.
            vp: Verb paradigm record currently being generated.

        Returns:
            Base form hash copied per variant and then extended per emitted row.

        """
        return {
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

    def _derive_paradigm_seed_vowels(self, vp: VerbParadigm) -> tuple[str, str, str]:
        """
        Derive boundary and exemplar vowels from the first paradigm variant.

        Args:
            vp: Verb paradigm record currently being generated.

        Returns:
            Three-item tuple ``(boundary_inf, vowel_inf, vowel_pa)`` used by
            branch orchestration to match legacy ordering/probability behavior.

        """
        variant0 = vp.variants[0]
        inf_part = variant0.parts.get("if")
        painsg1_part = variant0.parts.get("painsg1")
        boundary_inf = nz(inf_part.boundary if inf_part else "")
        vowel_inf = nz(inf_part.vowel if inf_part else "")
        vowel_pa = nz(painsg1_part.vowel if painsg1_part else "")
        return boundary_inf, vowel_inf, vowel_pa

    def _process_paradigm(self, word: Word, vp: VerbParadigm) -> None:
        """
        Process a single paradigm and expand each variant into full traversal context.

        Side Effects:
            Invokes ``_dispatch_variant_context`` once per variant in source order.

        Args:
            word: The word to process.
            vp: The paradigm to process.

        """
        formhash_base = self._build_verb_formhash_base(word, vp)
        boundary_inf, vowel_inf, vowel_pa = self._derive_paradigm_seed_vowels(vp)
        context = _ParadigmVariantDispatchContext(word=word, paradigm=vp)
        for variant in vp.variants:
            formhash_var = formhash_base.copy()
            formhash_var["var"] = str(variant.variant_id)
            self._dispatch_variant_context(
                context,
                variant,
                formhash_var,
                boundary_inf,
                vowel_inf,
                vowel_pa,
            )

    def _dispatch_variant_context(  # noqa: PLR0913
        self,
        context: _ParadigmVariantDispatchContext,
        variant: ParadigmVariant,
        formhash_base: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Dispatch one paradigm variant using the shared traversal flow.

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

    def _process_variant(  # noqa: PLR0913
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
        Process a single variant and expand each part into full traversal context.

        Side Effects:
            Invokes ``_dispatch_part_context`` once per part in source order.

        Args:
            word: The word to process.
            vp: The paradigm to process.
            variant: The variant to process.
            formhash_base: The base form hash.
            boundary_inf: The boundary information.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        context = _VariantPartDispatchContext(
            word=word,
            paradigm=vp,
            variant=variant,
        )
        for item in variant.parts.values():
            self._dispatch_part_context(
                context,
                item,
                formhash_base,
                boundary_inf,
                vowel_inf,
                vowel_pa,
            )

    def _dispatch_part_context(  # noqa: PLR0913
        self,
        context: _VariantPartDispatchContext,
        item: ParadigmPart,
        formhash_var: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        """
        Dispatch one variant part using the shared traversal flow.

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
        Process one part and route it into strong or weak generation flow.

        Side Effects:
            Invokes the strong or weak generator exactly once.

        Args:
            word: The word to process.
            vp: The paradigm to process.
            variant: The variant to process.
            item: The part to process.
            formhash_var: The form hash.
            boundary_inf: Infinitive boundary from variant ``0``.
            vowel_inf: Infinitive vowel from variant ``0``.
            vowel_pa: Preterite singular vowel from variant ``0``.

        """
        prefix, pre_vowel, actual_vowel, post_vowel = self._derive_part_stem_segments(
            word,
            item,
            boundary_inf,
        )

        if vp.type == "s":
            self._strong_generator.generate_verb_parts(
                formhash_var,
                word,
                item,
                prefix,
                pre_vowel,
                actual_vowel,
                post_vowel,
                variant.variant_id,
            )
            return

        self._weak_generator.generate_verb_parts(
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
