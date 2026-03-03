"""Participle-to-adjective projection helpers for morphology generation."""

from __future__ import annotations

import re

from wyrdcraeft.models.morphology import Word


def _sanitize_form_text(value: str) -> str:
    """
    Normalize form fragments by removing legacy separators and null markers.

    Args:
        value: Raw form text fragment.

    Returns:
        Sanitized fragment with ``0``, ``-``, and newlines removed.

    """
    return value.replace("0", "").replace("-", "").replace("\n", "")


def derive_participle_stem(*, prefix: str, form_parts: str) -> str:
    """
    Derive participle stem text from ``form_parts`` using legacy prefix logic.

    Args:
        prefix: Prefix expected at the start of the generated parts.
        form_parts: Raw generated ``formParts`` payload.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        Sanitized stem payload.

    """
    match = re.search(f"{re.escape(prefix)}(.*)$", form_parts)
    if match:
        return _sanitize_form_text(match.group(1))
    return _sanitize_form_text(form_parts)


def build_participle_adjective(
    *,
    word: Word,
    prefix: str,
    form_parts: str,
    is_past: bool,
) -> Word:
    """
    Build one adjective-form ``Word`` record from a generated participle form.

    Args:
        word: Source lexical entry.
        prefix: Prefix used for the generated participle.
        form_parts: Generated ``formParts`` payload.
        is_past: Whether this participle should set past-participle flags.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        New adjective ``Word`` record.

    """
    stem = derive_participle_stem(prefix=prefix, form_parts=form_parts)
    title = _sanitize_form_text(prefix + stem)
    return Word(
        nid=word.nid,
        title=title,
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
