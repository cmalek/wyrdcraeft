"""Morphology-related Pydantic models for the Old English morphology generator."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class ParadigmPart(BaseModel):
    """
    Paradigm part model.
    """

    #: The paradigm ID.
    para_id: str
    #: The prefix.
    prefix: str
    #: The pre-vowel.
    pre_vowel: str
    #: The vowel.
    vowel: str
    #: The post-vowel.
    post_vowel: str
    #: The boundary.
    boundary: str
    #: The dental.
    dental: str
    #: The ending.
    ending: str


class ParadigmVariant(BaseModel):
    """
    Paradigm variant model.
    """

    #: The variant ID.
    variant_id: int
    #: The parts: the parts of the variant.
    parts: dict[str, ParadigmPart] = Field(default_factory=dict)


class VerbParadigm(BaseModel):
    """
    Verb paradigm model.
    """

    #: The ID.
    ID: str
    #: The title.
    title: str
    #: The verb type.
    type: str
    #: The verb class.
    class_: str = Field(alias="class")
    #: The subdivision.
    subdivision: str
    #: The verb subclass.
    subclass: str
    #: The Wright's analysis of the word.
    wright: str
    #: The variants: the variants of the verb paradigm.
    variants: list[ParadigmVariant] = Field(default_factory=list)


class Word(BaseModel):
    """
    Lexical entry schema carrying POS flags and paradigm state for one lemma.
    """

    #: The ID.
    nid: int
    #: The title.
    title: str
    #: The Wright's analysis of the word.
    wright: str
    #: The noun.
    noun: int
    #: The pronoun.
    pronoun: int
    #: The adjective.
    adjective: int
    #: The verb.
    verb: int
    #: The participle.
    participle: int | None
    #: The present simple part.
    pspart: int
    #: The past participle part.
    papart: int
    #: The adverb.
    adverb: int
    #: The preposition.
    preposition: int
    #: The conjunction.
    conjunction: int
    #: The interjection.
    interjection: int
    #: The numeral.
    numeral: int
    #: The weak verb.
    vb_weak: int
    #: The weak verb.
    vb_strong: int
    #: The contracted verb.
    vb_contracted: int
    #: The pretpres verb.
    vb_pretpres: int
    #: The anomalous verb.
    vb_anomalous: int
    #: The uncertain verb.
    vb_uncertain: int
    #: The masculine noun.
    n_masc: int
    #: The feminine noun.
    n_fem: int
    #: The neuter noun.
    n_neut: int
    #: The uncertain noun.
    n_uncert: int

    # ------------------------------------------------------------
    # Dynamic fields set during processing
    # ------------------------------------------------------------

    #: The verb paradigm: the paradigm of the verb.
    vb_paradigm: list[VerbParadigm] = Field(default_factory=list)
    #: The adjective paradigm: the paradigm of the adjective.
    adj_paradigm: list[str] = Field(default_factory=list)
    #: The noun paradigm: the paradigm of the noun.
    noun_paradigm: list[str] = Field(default_factory=list)
    #: The syllables: the number of syllables in the word.
    syllables: int = 0
    #: The prefix: the prefix of the word.
    prefix: str = "0"
    #: The long stem: whether the word has a long stem.
    long_stem: int = 0
    #: The stem: the root of the word.
    stem: str = ""


class ManualForm(BaseModel):
    """
    Manual form model for ``manual_forms.txt`` ingest rows.

    Legacy string fields (``wright``, ``paradigm``, ``para_id``, ``wordclass``,
    ``function``, ``class1``-``class3``) remain in memory for generator parity.
    The morphology sink persists surface fields, normalized ``*_key`` columns,
    and foreign keys (``wordclass_id``, ``inflection_code_id``,
    ``morph_class_id``, ``entry_id``) only — not the legacy string columns
    dropped from ``forms`` in Phase D.

    """

    #: Surrogate identifier assigned in ``manual_forms.txt`` load order.
    id: int
    #: The BT: the base form of the word.
    BT: str
    #: The title: the word itself.
    title: str
    #: Macron/dot-preserving normalized lemma title for dictionary joins.
    normalized_title: str
    #: The stem: the root of the word.
    stem: str
    #: The form: the form of the word, meaning the form of the word in the dictionary.
    form: str
    #: The form parts: the parts of the form.
    form_parts: str
    #: The variant: the variant of the word.
    var: str
    #: The probability:
    probability: str
    #: The function: the function of the word.
    function: str
    #: The Wright: the Wright's analysis of the word.
    wright: str
    #: The paradigm: the paradigm of the word, meaning the principal parts of the verb.
    paradigm: str
    #: The paradigm ID: the ID of the paradigm.
    para_id: str
    #: The word class: the class of the word.
    wordclass: str
    #: The class 1: the first class of the word, used for verbs.
    class1: str
    #: The class 2: the second class of the word, used for nouns.
    class2: str
    #: The class 3: the third class of the word, used for adjectives.
    class3: str
    #: The comment.
    comment: str


class GeneratedForm(BaseModel):
    """
    Generated form model for one morphology build output row.

    ``counter`` is the logical primary key for one morphology build output.
    Legacy string fields (``wright``, ``paradigm``, ``para_id``, ``wordclass``,
    ``function``, ``class1``-``class3``) remain in memory for generator parity.
    The morphology sink persists surface fields, normalized ``*_key`` columns,
    and foreign keys only — not the legacy string columns dropped from
    ``forms`` in Phase D.

    """

    #: The counter, used to count the number of generated forms.
    counter: int
    #: The form ID, used to identify the form.
    formi: str
    #: The BT: the base form of the word.
    BT: str
    #: The title: the word itself.
    title: str
    #: Macron/dot-preserving normalized lemma title for dictionary joins.
    normalized_title: str
    #: The stem: the root of the word.
    stem: str
    #: The form: the form of the word, meaning the form of the word in the dictionary.
    form: str
    #: The form parts: the parts of the form.
    form_parts: str
    #: The variant: the variant of the word.
    var: str
    #: The probability.
    probability: str
    #: The function
    function: str
    #: The Wright.
    wright: str
    #: The paradigm.
    paradigm: str
    #: The paradigm ID.
    para_id: str
    #: The word class.
    wordclass: str
    #: The class 1.
    class1: str
    #: The class 2.
    class2: str
    #: The class 3.
    class3: str
    #: The comment.
    comment: str


class FormRow(BaseModel):
    """
    Canonical emitted morphology row used by sinks and query services.

    Legacy string fields (``wright``, ``paradigm``, ``paraID``, ``wordclass``,
    ``function``, ``class1``-``class3``) remain in memory for generator parity.
    The morphology sink persists surface fields (``form``, ``formi``, ``title``,
    ``BT``, ``stem``, …), normalized ``*_key`` columns, and foreign keys
    (``wordclass_id``, ``inflection_code_id``, ``morph_class_id``,
    ``entry_id``) only — not the legacy string columns dropped from ``forms``
    in Phase D.

    """

    #: The output counter value (logical primary key within one build).
    counter: str
    #: Normalized form identifier for lookup/sorting.
    formi: str
    #: Lemma/base token identifier.
    BT: str
    #: Surface title token.
    title: str
    #: Macron/dot-preserving normalized lemma title for dictionary joins.
    normalized_title: str
    #: Stem token.
    stem: str
    #: Emitted form text.
    form: str
    #: Emitted form-parts payload.
    formParts: str  # noqa: N815
    #: Variant identifier.
    var: str
    #: Emitted probability field.
    probability: str
    #: Morphology function code.
    function: str
    #: Wright grammar annotation.
    wright: str
    #: Paradigm label.
    paradigm: str
    #: Paradigm ID.
    paraID: str  # noqa: N815
    #: Word class label.
    wordclass: str
    #: Class-1 metadata field.
    class1: str
    #: Class-2 metadata field.
    class2: str
    #: Class-3 metadata field.
    class3: str
    #: Free-form comment field.
    comment: str


class MorphClassQueryMetadata(BaseModel):
    """
    FK-backed morph-class metadata joined from catalog tables.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this exposes one
        assigned Wright inflection class and its section citations for a form
        row when ``morph_class_id`` is populated. Part-of-speech scope:
        ``cross-PoS``.

    """

    #: Stable catalog business key for the morph class.
    class_key: str
    #: Catalog part-of-speech label.
    pos: str
    #: Canonical display name for the class.
    canonical_name: str
    #: Modern linguistic class label.
    modern_class: str
    #: Wright grammar label for the class.
    wright_label: str
    #: Browse-ready class label.
    display_label: str
    #: Wright section numbers in catalog sort order.
    wright_sections: tuple[int, ...] = ()


class QueryFormRow(FormRow):
    """Indexed morphology row enriched with normalized query keys."""

    #: Normalized joined lemma lookup key payload.
    lemma_key: str
    #: Normalized emitted form lookup key.
    form_key: str
    #: Assigned catalog morph-class identifier when resolved at insert time.
    morph_class_id: int | None = None
    #: FK-backed morph-class metadata joined when ``morph_class_id`` is set.
    morph_class: MorphClassQueryMetadata | None = None


@dataclass(frozen=True)
class _ParadigmVariantDispatchContext:
    """
    Immutable context for paradigm-level variant callback dispatch.

    Args:
        word: Source lexical entry owning the active paradigm.
        paradigm: Active verb paradigm whose variants are being dispatched.

    """

    #: Source lexical entry owning the active paradigm.
    word: Word
    #: Active verb paradigm whose variants are being dispatched.
    paradigm: VerbParadigm


@dataclass(frozen=True)
class _VariantPartDispatchContext:
    """
    Immutable context for variant-level part callback dispatch.

    Args:
        word: Source lexical entry owning the active paradigm.
        paradigm: Active verb paradigm whose parts are being dispatched.
        variant: Active variant whose parts are being dispatched.

    """

    #: Source lexical entry owning the active paradigm.
    word: Word
    #: Active verb paradigm whose parts are being dispatched.
    paradigm: VerbParadigm
    #: Active variant whose parts are being dispatched.
    variant: ParadigmVariant


@dataclass(frozen=True)
class _SoundChangeDispatchContext:
    """
    Immutable context for sound-change callback dispatch.

    Args:
        formhash: Shared form metadata for emitted rows.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        vowel: Active stem vowel for source-row emission.
        post_vowel: Segment after the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Optional weak preterite dental segment.
        ending: Morphological ending for source-row emission.
        function: Morphology function code for source-row emission.
        probability: Optional source-row probability annotation.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Active stem vowel for source-row emission.
    vowel: str
    #: Segment after the active stem vowel.
    post_vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str
    #: Optional weak preterite dental segment.
    dental: str | None
    #: Morphological ending for source-row emission.
    ending: str
    #: Morphology function code for source-row emission.
    function: str
    #: Optional source-row probability annotation.
    probability: str | int | None


@dataclass(frozen=True)
class _StrongPrincipalPartContext:
    """
    Immutable context for strong principal-part callback bindings.

    Args:
        formhash: Shared form metadata for emitted rows.
        word: Source lexical entry receiving derived participles.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        post_vowel: Segment after the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        ending: Morphological ending from the active principal part.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Source lexical entry receiving derived participles.
    word: Word
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Segment after the active stem vowel.
    post_vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str
    #: Morphological ending from the active principal part.
    ending: str


@dataclass(frozen=True)
class _StrongInfDerivationContext:
    """
    Immutable context for strong infinitive-derived emitter callbacks.

    Args:
        formhash: Shared form metadata for emitted rows.
        word: Source lexical entry receiving derived participles.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        base_vowel: Base infinitive vowel used for ``ImSg`` derivation.
        post_vowel: Segment after the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Source lexical entry receiving derived participles.
    word: Word
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Base infinitive vowel used for ``ImSg`` derivation.
    base_vowel: str
    #: Segment after the active stem vowel.
    post_vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str


@dataclass(frozen=True)
class _WeakPrincipalPartContext:
    """
    Immutable context for weak principal-part callback bindings.

    Args:
        formhash: Shared form metadata for emitted rows.
        word: Source lexical entry receiving derived participles.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        vowel: Active stem vowel used for weak branch derivations.
        post_vowel: Segment after the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        ending: Morphological ending from the active principal part.
        dental: Weak preterite dental segment from the principal part.
        probability: Base probability annotation for derived branches.
        vowel_inf: Infinitive vowel from variant 0.
        vowel_pa: Preterite singular vowel from variant 0.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Source lexical entry receiving derived participles.
    word: Word
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Active stem vowel used for weak branch derivations.
    vowel: str
    #: Segment after the active stem vowel.
    post_vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str
    #: Morphological ending from the active principal part.
    ending: str
    #: Weak preterite dental segment from the principal part.
    dental: str
    #: Base probability annotation for derived branches.
    probability: str | int | None
    #: Infinitive vowel from variant 0.
    vowel_inf: str
    #: Preterite singular vowel from variant 0.
    vowel_pa: str


@dataclass(frozen=True)
class _WeakInfDerivationContext:
    """
    Immutable context for weak infinitive-derived emitter callbacks.

    Args:
        formhash: Shared form metadata for emitted rows.
        word: Source lexical entry receiving derived participles.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        vowel: Base infinitive vowel for weak-derivation emission.
        post_vowel: Segment after the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Source lexical entry receiving derived participles.
    word: Word
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Base infinitive vowel for weak-derivation emission.
    vowel: str
    #: Segment after the active stem vowel.
    post_vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str


@dataclass(frozen=True)
class _WeakPainsg1DerivationContext:
    """
    Immutable context for weak ``PaInSg1``-derived emitter callbacks.

    Args:
        formhash: Shared form metadata for emitted rows.
        word: Source lexical entry receiving derived participles.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        boundary: Stem-boundary marker used in form-parts payloads.
        dental: Weak preterite dental segment used in derived forms.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Source lexical entry receiving derived participles.
    word: Word
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str
    #: Weak preterite dental segment used in derived forms.
    dental: str


@dataclass(frozen=True)
class _WeakPsinsg2DerivationContext:
    """
    Immutable context for weak ``PsInSg2``-derived emitter callbacks.

    Args:
        formhash: Shared form metadata for emitted rows.
        prefix: Prefix segment prepended to generated forms.
        pre_vowel: Segment before the active stem vowel.
        vowel: Active stem vowel used for this derivation branch.
        boundary: Stem-boundary marker used in form-parts payloads.

    """

    #: Shared form metadata for emitted rows.
    formhash: dict[str, str]
    #: Prefix segment prepended to generated forms.
    prefix: str
    #: Segment before the active stem vowel.
    pre_vowel: str
    #: Active stem vowel used for this derivation branch.
    vowel: str
    #: Stem-boundary marker used in form-parts payloads.
    boundary: str
