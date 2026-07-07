"""Browse startup progress helpers for dictionary browse workflow."""

from __future__ import annotations

import sys
from enum import StrEnum
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

if TYPE_CHECKING:
    from collections.abc import Callable


class DictionaryBrowseStartupStage(StrEnum):
    """Stable stage labels for dictionary browse startup progress."""

    #: Database connect stage label.
    CONNECT = "connect database"
    #: Dictionary-table validation stage label.
    VALIDATE = "validate dictionary tables"
    #: Startup-ready stage label.
    READY = "ready"


def run_browse_startup_progress(
    callback: Callable[[DictionaryBrowseStartupStage], object],
    *,
    enabled: bool = True,
) -> None:
    """
    Run browse startup work while showing stable stderr progress stages.

    Args:
        callback: Callable invoked once per startup stage in order.

    Keyword Args:
        enabled: Whether progress rendering is enabled.

    Side Effects:
        Executes ``callback`` for each startup stage.

    """
    stages = (
        DictionaryBrowseStartupStage.CONNECT,
        DictionaryBrowseStartupStage.VALIDATE,
        DictionaryBrowseStartupStage.READY,
    )
    if not enabled:
        for stage in stages:
            callback(stage)
        return

    console = Console(file=sys.stderr, force_terminal=sys.stderr.isatty())
    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        redirect_stdout=False,
        redirect_stderr=False,
        refresh_per_second=10,
    )
    with progress:
        task_id = progress.add_task("starting dictionary browse", total=len(stages))
        for stage in stages:
            callback(stage)
            progress.update(task_id, advance=1, description=stage.value)


__all__ = [
    "DictionaryBrowseStartupStage",
    "run_browse_startup_progress",
]
