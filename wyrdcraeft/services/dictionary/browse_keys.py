"""
Keys, focus regions and footer groups for dictionary browse (ADR 0028).

The browse app has three keyboard regions, in tab order: the search input,
the results list and the entry column. The footer lists only the keys that
can act in the focused region; the bindings here carry the footer labels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.widgets import ListView

if TYPE_CHECKING:
    from textual.binding import BindingType

#: Id of the search input, the first focus region.
SEARCH_INPUT_ID = "search-input"

#: Footer group that shows ``up`` and ``down`` as one ``↑↓ Move`` item.
MOVE_GROUP = Binding.Group("Move", compact=True)

#: Footer group for the forms primary switch keys (``←`` ``→``).
TABLE_GROUP = Binding.Group("Table", compact=True)

#: Footer group for the forms secondary switch keys (``[`` ``]``).
DEGREE_GROUP = Binding.Group("Degree", compact=True)

#: App-level keys. ``c`` and ``/`` are inert while the search input has focus
#: (it types them); ``escape`` acts only there. ``tab`` is a priority binding
#: so the footer shows it in place of the screen's hidden ``focus_next``.
APP_BINDINGS: list[BindingType] = [
    Binding("c", "copy_definition", "Copy"),
    Binding("slash", "focus_search", "Search", key_display="/"),
    Binding("escape", "focus_results", "Results", show=False),
    Binding("tab", "app.focus_next", "Switch pane", priority=True),
]

#: Search-input keys: ``up``/``down`` move the results selection while focus
#: stays in the input.
SEARCH_BINDINGS: list[BindingType] = [
    Binding("up", "app.move_results(-1)", "Move", group=MOVE_GROUP),
    Binding("down", "app.move_results(1)", "Move", group=MOVE_GROUP),
]


def focus_action_allowed(
    action: str,
    *,
    search_focused: bool,
    has_definition_line: bool,
) -> bool:
    """
    Decide whether an app-level browse action is live in the current focus.

    Args:
        action: Action name without namespace.

    Keyword Args:
        search_focused: Whether the search input has keyboard focus.
        has_definition_line: Whether the open entry has a definition line.

    Returns:
        ``False`` for ``copy_definition`` and ``focus_search`` while the search
        input has focus, for ``copy_definition`` without a definition line,
        and for ``focus_results`` outside the search input; ``True`` otherwise.

    """
    if action == "copy_definition":
        return has_definition_line and not search_focused
    if action == "focus_search":
        return not search_focused
    if action == "focus_results":
        return search_focused
    return True


class ResultsList(ListView):
    """
    The results list, with footer labels for its move and open keys.

    The keys and actions are ListView's own; only the footer text differs.
    """

    #: ``up``/``down`` move the selection and ``enter`` opens the entry.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("up", "cursor_up", "Move", group=MOVE_GROUP),
        Binding("down", "cursor_down", "Move", group=MOVE_GROUP),
        Binding("enter", "select_cursor", "Open", key_display="⏎"),
    ]
