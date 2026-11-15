"""The ``wyrdcraeft`` Textual theme for dictionary browse (ADR 0026 palette)."""

from __future__ import annotations

from textual.theme import Theme

#: Name the browse app registers and activates its theme under.
WYRDCRAEFT_THEME_NAME = "wyrdcraeft"

#: Part-of-speech tag colours as ``(code, text, tint)``. Tags differ in
#: lightness as well as hue, and each text colour is 7:1 or better on its tint.
POS_TAG_COLORS: tuple[tuple[str, str, str], ...] = (
    ("noun", "#f6b874", "#2e1f10"),
    ("verb", "#7fa9f6", "#111a2e"),
    ("adjective", "#c9a2f2", "#2a1d3a"),
    ("adverb", "#9fe0a0", "#1c3322"),
    ("pronoun", "#f2a0b8", "#3c1f2a"),
    ("numeral", "#f5d76e", "#3a3214"),
    ("preposition", "#7fc8e8", "#16303b"),
    ("conjunction", "#c4cf94", "#2c3119"),
    ("interjection", "#ffa596", "#42201b"),
    ("indeclinable", "#7fd6a8", "#173328"),
    ("unknown", "#b4bccb", "#1e2230"),
)


def _pos_tag_variables() -> dict[str, str]:
    """
    Build the ``pos-<code>-text`` and ``pos-<code>-tint`` theme variables.

    Returns:
        Theme variable names mapped to hex colours, two per POS code.

    """
    variables: dict[str, str] = {}
    for code, text_color, tint in POS_TAG_COLORS:
        variables[f"pos-{code}-text"] = text_color
        variables[f"pos-{code}-tint"] = tint
    return variables


#: Browse palette: ground ``#101319``, panel ``#151922``, selected row
#: ``#232a38``, border ``#2a3140``, text ``#dbe0ea``, label ``#8c95a8``,
#: accent ``#e6b36a`` (Textual ``primary``) and Old English forms ``#8fd0c4``
#: (Textual ``accent``). ``border`` is the focused-pane colour and
#: ``border-blurred`` the unfocused one, as in Textual's own variables.
WYRDCRAEFT_THEME = Theme(
    name=WYRDCRAEFT_THEME_NAME,
    dark=True,
    background="#101319",
    surface="#151922",
    panel="#232a38",
    primary="#e6b36a",
    accent="#8fd0c4",
    foreground="#dbe0ea",
    variables={
        "block-cursor-background": "#232a38",
        "block-cursor-foreground": "#dbe0ea",
        "block-cursor-text-style": "none",
        "block-cursor-blurred-background": "#232a38",
        "block-cursor-blurred-foreground": "#dbe0ea",
        "block-cursor-blurred-text-style": "none",
        "border": "#e6b36a",
        "border-blurred": "#2a3140",
        "footer-background": "#151922",
        "text-muted": "#8c95a8",
        "foreground-muted": "#8c95a8",
        "wyrd-selected-row": "#232a38",
        "wyrd-label": "#8c95a8",
        "wyrd-form": "#8fd0c4",
        **_pos_tag_variables(),
    },
)
