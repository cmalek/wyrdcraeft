"""Strong-verb infinitive derivation helpers for morphology generation."""

from __future__ import annotations

from collections.abc import Callable

#: Callback signature for one strong-form emission operation.
StrongFormEmitter = Callable[[str, str, str | int | None], tuple[str, str]]
#: Callback signature for one strong-form sound-change emission operation.
StrongSoundEmitter = Callable[[str, str, str | int | None], None]
#: Callback signature for one strong-branch action.
StrongBranchAction = Callable[[], None]


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
