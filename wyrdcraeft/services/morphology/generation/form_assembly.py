"""Form assembly helpers for parity-preserving morphology generation."""

from __future__ import annotations


def perl_interpolate(value: str | int | None) -> str:
    """
    Coerce a scalar to a Perl-like interpolation string.

    Side Effects:
        None.

    Args:
        value: Input scalar used while building ``formParts``.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        The interpolated string value, with ``None`` mapped to ``""``.

    """
    if value is None:
        return ""
    return str(value)


def assemble_form_parts(  # noqa: PLR0913
    *,
    class1: str,
    prefix: str,
    pre_vowel: str,
    vowel: str,
    post_vowel: str,
    boundary: str,
    dental: str | None,
    ending: str,
) -> str:
    """
    Assemble a raw ``formParts`` payload using legacy Perl field ordering.

    Side Effects:
        None.

    Args:
        class1: Primary word class marker.
        prefix: Prefix component.
        pre_vowel: Pre-vowel stem component.
        vowel: Vowel component.
        post_vowel: Post-vowel component.
        boundary: Boundary marker from the paradigm part.
        dental: Dental marker for weak forms.
        ending: Ending marker from the paradigm part.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Raw hyphen-joined ``formParts`` prior to normalization.

    """
    if class1 == "s":
        return (
            f"{perl_interpolate(prefix)}-{perl_interpolate(pre_vowel)}"
            f"-{perl_interpolate(vowel)}-{perl_interpolate(post_vowel)}"
            f"-{perl_interpolate(boundary)}-{perl_interpolate(ending)}"
        )
    if dental is None:
        return (
            f"{perl_interpolate(prefix)}-{perl_interpolate(pre_vowel)}"
            f"-{perl_interpolate(vowel)}-{perl_interpolate(post_vowel)}"
            f"-{perl_interpolate(boundary)}-{perl_interpolate(ending)}"
        )
    return (
        f"{perl_interpolate(prefix)}-{perl_interpolate(pre_vowel)}"
        f"-{perl_interpolate(vowel)}-{perl_interpolate(post_vowel)}"
        f"-{perl_interpolate(boundary)}-{perl_interpolate(dental)}"
        f"-{perl_interpolate(ending)}"
    )


def materialize_form(form_parts: str) -> tuple[str, str]:
    """
    Normalize assembled form parts into the emitted ``form`` and ``formParts``.

    Side Effects:
        None.

    Args:
        form_parts: Raw hyphen-joined parts string.

    Keyword Args:
        None.

    Raises:
        None.

    Returns:
        Tuple of ``(form, normalized_form_parts)``.

    """
    normalized_parts = form_parts.replace("\n", "")
    form = normalized_parts.replace("0", "").replace("-", "")
    return form, normalized_parts
