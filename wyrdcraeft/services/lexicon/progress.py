"""Browse startup progress helpers for lexicon service."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

from wyrdcraeft.cli.utils import create_stderr_console

if TYPE_CHECKING:
    from collections.abc import Callable


class LexiconBrowseStartupStage(StrEnum):
    """Stable stage labels for lexicon browse startup progress."""

    #: Database connect stage label.
    CONNECT = "connect database"
    #: Lexicon-table validation stage label.
    VALIDATE = "validate lexicon tables"
    #: Startup-ready stage label.
    READY = "ready"


def run_browse_startup_progress(
    callback: Callable[[LexiconBrowseStartupStage], object],
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
        LexiconBrowseStartupStage.CONNECT,
        LexiconBrowseStartupStage.VALIDATE,
        LexiconBrowseStartupStage.READY,
    )
    if not enabled:
        for stage in stages:
            callback(stage)
        return

    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=create_stderr_console(),
        redirect_stdout=False,
        redirect_stderr=False,
        refresh_per_second=10,
    )
    with progress:
        task_id = progress.add_task("starting lexicon browse", total=len(stages))
        for stage in stages:
            callback(stage)
            progress.update(task_id, advance=1, description=stage.value)
