from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ============================================================
# Enums
# ============================================================


class PartOfSpeech(str, enum.Enum):
    """
    Part of speech enumeration.
    """

    NOUN = "noun"
    VERB = "verb"
    ADJ = "adjective"
    ADV = "adverb"
    PRON = "pronoun"
    ART = "article"
    PREP = "preposition"
    CONJ = "conjunction"
    INTERJ = "interjection"
    NUM = "numeral"
    PARTICLE = "particle"
    OTHER = "other"


class ExpressionType(str, enum.Enum):
    """
    Expression type enumeration.
    """

    WORD = "word"
    IDIOM = "idiom"
    FORMULA = "formula"
    COLLOCATION = "collocation"


class Gender(str, enum.Enum):
    """
    Gender enumeration.
    """

    MASC = "masc"
    FEM = "fem"
    NEUT = "neut"
    COMMON = "common"
    UNKNOWN = "unknown"


class NounDeclension(str, enum.Enum):
    """
    Noun declension enumeration.
    """

    A_STEM = "a_stem"
    O_STEM = "o_stem"
    I_STEM = "i_stem"
    U_STEM = "u_stem"
    JA_STEM = "ja_stem"
    JO_STEM = "jo_stem"
    WA_STEM = "wa_stem"
    WO_STEM = "wo_stem"
    WEAK = "weak"
    R_NOUN = "r_noun"
    ROOT = "root"
    I_MUTATION = "i_mutation"
    OTHER = "other"


# ============================================================
# Core lexicon models
# ============================================================


class VariantSpelling(BaseModel):
    """
    Variant spelling model.
    """

    #: Spelling
    spelling: str

    #: Normalized form
    normalized: str

    #: Dialect
    dialect: str | None = None

    #: Period
    period: str | None = None

    #: Source note
    source_note: str | None = None


class Example(BaseModel):
    """
    Example model.
    """

    #: Old English text
    old_english: str

    #: Translation
    translation: str | None = None

    #: Source
    source: str | None = None


class Sense(BaseModel):
    """
    Sense model.
    """

    #: Sense order
    sense_order: int

    #: Sense name
    sense_name: str

    #: Definition
    definition: str

    #: Latin definition
    latin_definition: str | None = None

    #: Usage note
    usage_note: str | None = None

    #: Part of speech
    pos: PartOfSpeech | None = None

    #: Examples
    examples: list[Example] = Field(default_factory=list)

    senses: list[Sense] = Field(default_factory=list)


class ExpressionComponent(BaseModel):
    """
    Expression component model.
    """

    #: Position
    position: int

    #: Surface form
    surface_form: str | None = None

    #: Lemma display
    lemma_display: str | None = None


class Morphology(BaseModel):
    """
    Morphology model.
    """

    #: Primary part of speech
    primary_pos: PartOfSpeech | None = None

    #: Gender
    gender: Gender | None = None

    #: Noun declension
    noun_declension: NounDeclension | None = None

    #: Whether the noun or adjective is a long stem
    is_long_stem: bool | None = None

    # Verb principal parts (best-effort)

    #: Verb class
    verb_class: str | None = None
    #: Verb present 1st person singular
    present_i_1_sg: list[str] = Field(default_factory=list)
    #: Verb present 2nd person singular
    present_i_2_sg: list[str] = Field(default_factory=list)
    #: Verb present 3rd person singular
    present_i_3_sg: list[str] = Field(default_factory=list)
    #: Verb present 1st person plural
    present_i_pl: list[str] = Field(default_factory=list)
    #: Verb past 1st person singular
    past_i_1_sg: list[str] = Field(default_factory=list)
    #: Verb past 2nd person singular
    past_i_2_sg: list[str] = Field(default_factory=list)
    #: Verb past 3rd person singular
    past_i_3_sg: list[str] = Field(default_factory=list)
    #: Verb past 1st person plural
    past_i_pl: list[str] = Field(default_factory=list)
    #: Present participle
    present_participle: list[str] = Field(default_factory=list)
    #: Past participle
    past_participle: str | None = None


class LexicalExpression(BaseModel):
    """
    The single head entry for both words and idioms.
    """

    model_config = ConfigDict(extra="forbid")

    #: Display form
    display_form: str

    #: Normalized form
    normalized: str

    #: Search form
    search_form: str

    #: Expression type
    expression_type: ExpressionType

    #: IPA
    ipa: str | None = None

    #: Etymology
    etymology: dict[str, str] | None = None

    #: Senses
    senses: list[Sense] = Field(default_factory=list)

    #: Variants
    variants: list[VariantSpelling] = Field(default_factory=list)

    #: Derived forms
    derived_forms: list[str] = Field(default_factory=list)

    #: Components
    components: list[ExpressionComponent] = Field(default_factory=list)

    #: Morphology
    morphology: Morphology | None = None

    #: Similar entries
    similar_entries: list[str] = Field(default_factory=list)
