"""Strong-verb infinitive derivation helpers for morphology generation."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from .probability import probability_plus

#: Callback signature for one strong-form emission operation.
StrongFormEmitter = Callable[[str, str, str | int | None], tuple[str, str]]
#: Callback signature for one strong-form sound-change emission operation.
StrongSoundEmitter = Callable[[str, str, str | int | None], None]
#: Callback signature for one strong-branch action.
StrongBranchAction = Callable[[], None]
#: Callback signature for emitting a strong form for a specific active vowel.
StrongVowelFormEmitter = Callable[[str, str, str, str | int | None], tuple[str, str]]
#: Callback signature for emitting strong sound changes for a specific vowel.
StrongVowelSoundEmitter = Callable[[str, str, str, str | int | None], None]
#: Callback signature for consuming one derived participle ``formParts`` value.
StrongParticipleSink = Callable[[str], None]
#: Callback signature for emitting the imperative-singular derivative row.
StrongImSgEmitter = Callable[[str | int | None], None]


def emit_strong_derived_from_inf_sequence(  # noqa: PLR0913
    *,
    ending: str,
    vowel: str,
    probability: str | int | None,
    umlaut_vowels: Sequence[str],
    emit_form_for_vowel: StrongVowelFormEmitter,
    emit_sound_for_vowel: StrongVowelSoundEmitter,
    on_participle: StrongParticipleSink,
    emit_imsg: StrongImSgEmitter,
) -> None:
    """
    Emit the full strong-verb infinitive-derived sequence.

    Side Effects:
        Invokes emission callbacks for non-umlaut, imperative, and umlaut forms.

    Args:
        ending: Original paradigm ending from the infinitive principal part.
        vowel: Base infinitive vowel.
        probability: Base probability scalar for the branch.
        umlaut_vowels: Ordered umlaut vowel variants for the base vowel.
        emit_form_for_vowel: Callback that emits a form for one active vowel.
        emit_sound_for_vowel: Callback that emits sound-change rows for one vowel.
        on_participle: Callback that consumes the emitted participle form-parts.
        emit_imsg: Callback that emits the ``ImSg`` derived row.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    probability_plus_one = probability_plus(probability, delta=1, empty_default=1)
    form_parts = emit_strong_derived_from_inf_non_umlaut(
        ending=ending,
        probability=probability,
        probability_plus_one=probability_plus_one,
        emit_form=lambda ending_value, function, prob_value: emit_form_for_vowel(
            vowel,
            ending_value,
            function,
            prob_value,
        ),
    )
    on_participle(form_parts)
    emit_imsg(probability)

    for mv_idx, mvowel in enumerate(umlaut_vowels):
        mv_prob = int(probability) + mv_idx if probability is not None else mv_idx

        def emit_umlaut(
            ending_value: str,
            function: str,
            prob_value: str | int | None,
            *,
            _mvowel: str = mvowel,
        ) -> tuple[str, str]:
            return emit_form_for_vowel(
                _mvowel,
                ending_value,
                function,
                prob_value,
            )

        def emit_umlaut_sound(
            ending_value: str,
            function: str,
            prob_value: str | int | None,
            *,
            _mvowel: str = mvowel,
        ) -> None:
            emit_sound_for_vowel(
                _mvowel,
                ending_value,
                function,
                prob_value,
            )

        emit_strong_umlaut_for_vowel(
            probability=mv_prob,
            emit_form=emit_umlaut,
            emit_sound=emit_umlaut_sound,
        )


def emit_strong_derived_from_inf_non_umlaut(
    *,
    ending: str,
    probability: str | int | None,
    probability_plus_one: int,
    emit_form: StrongFormEmitter,
) -> str:
    """
    Emit non-umlaut strong-verb forms derived from the infinitive principal part.

    Side Effects:
        Writes generated rows through ``emit_form``.

    Args:
        ending: Original paradigm ending from the infinitive part.
        probability: Base probability scalar.
        probability_plus_one: Incremented probability scalar.
        emit_form: Callback that emits one generated form.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Final participle ``formParts`` string used for adjective derivation.

    """
    if "an" in ending:
        emit_form("anne", "IdIf", probability)
        emit_form("enne", "IdIf", probability)
        _, participle_form_parts = emit_form("ende", "PsPt", probability)

        emit_form("e", "PsInSg1", probability)
        emit_form("u", "PsInSg1", probability_plus_one)
        emit_form("o", "PsInSg1", probability_plus_one)
        emit_form("æ", "PsInSg1", probability_plus_one)

        emit_form("aþ", "PsInPl", probability)
        emit_form("eþ", "PsInPl", probability_plus_one)
        emit_form("es", "PsInPl", probability_plus_one)
        emit_form("as", "PsInPl", probability_plus_one)

        emit_form("e", "PsSuSg", probability)
        emit_form("en", "PsSuPl", probability)
        emit_form("aþ", "ImPl", probability)
        return participle_form_parts

    emit_form("nne", "IdIf", probability)
    _, participle_form_parts = emit_form("nde", "PsPt", probability)

    emit_form("0", "PsInSg1", probability)
    emit_form("þ", "PsInPl", probability)
    emit_form("0", "PsSuSg", probability)
    emit_form("n", "PsSuPl", probability)
    emit_form("þ", "ImPl", probability)
    return participle_form_parts


def emit_strong_umlaut_for_vowel(
    *,
    probability: int,
    emit_form: StrongFormEmitter,
    emit_sound: StrongSoundEmitter,
) -> None:
    """
    Emit umlaut-derived ``PsInSg2`` and ``PsInSg3`` strong-verb forms.

    Side Effects:
        Writes generated rows through ``emit_form`` and ``emit_sound``.

    Args:
        probability: Base umlaut probability for this vowel variant.
        emit_form: Callback that emits one generated form.
        emit_sound: Callback that emits one sound-change branch.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        ``None``.

    """
    emit_form("stu", "PsInSg2", probability + 1)
    emit_form("est", "PsInSg2", probability + 1)
    emit_form("ist", "PsInSg2", probability + 1)
    emit_form("s", "PsInSg2", probability + 1)
    emit_sound("st", "PsInSg2", probability)

    emit_form("eþ", "PsInSg3", probability + 1)
    emit_form("iþ", "PsInSg3", probability + 1)
    emit_sound("þ", "PsInSg3", probability)


def dispatch_strong_verb_part_branches(
    *,
    para_id: str,
    on_papt: StrongBranchAction,
    on_inf: StrongBranchAction,
    on_painsg1: StrongBranchAction,
    on_painpl: StrongBranchAction,
) -> bool:
    """
    Dispatch strong-verb principal-part branch actions for one ``para_id``.

    Side Effects:
        Invokes at least one branch callback when a branch matches.

    Args:
        para_id: Principal function identifier from paradigm row.
        on_papt: Callback for past-participle branch side effects.
        on_inf: Callback for infinitive-derived branch.
        on_painsg1: Callback for ``PaInSg1``-derived branch.
        on_painpl: Callback for ``PaInPl``-derived branch.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Raises:
        Does not raise directly.

    Returns:
        ``True`` when any branch callback was invoked, else ``False``.

    """
    invoked = False
    para_id_lower = para_id.lower()

    if para_id_lower == "papt":
        on_papt()
        invoked = True

    if para_id_lower == "if":
        on_inf()
        return True
    if para_id_lower == "painsg1":
        on_painsg1()
        return True
    if para_id_lower == "painpl":
        on_painpl()
        return True
    return invoked


def emit_strong_painsg1_derived(
    *,
    probability: str | int | None,
    emit_form: StrongFormEmitter,
) -> None:
    """
    Emit ``PaInSg1``-derived strong-verb side branch forms.

    Side Effects:
        Writes generated rows through ``emit_form``.

    Args:
        probability: Base probability scalar for branch emissions.
        emit_form: Callback that emits one generated form.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        ``None``.

    """
    emit_form("0", "PaInSg3", probability)


def emit_strong_painpl_derived(
    *,
    probability: str | int | None,
    emit_form: StrongFormEmitter,
) -> None:
    """
    Emit ``PaInPl``-derived strong-verb side branch forms.

    Side Effects:
        Writes generated rows through ``emit_form``.

    Args:
        probability: Base probability scalar for branch emissions.
        emit_form: Callback that emits one generated form.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        ``None``.

    """
    emit_form("e", "PaInSg2", probability)
    emit_form("e", "PaSuSg", probability)
    emit_form("en", "PaSuPl", probability)
