"""Startup database runtime for canonical SQLite migrations."""

from __future__ import annotations

import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from wyrdcraeft.db.backup import create_backup, restore_backup
from wyrdcraeft.db.state import BackupStateStore

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

    from wyrdcraeft.settings import Settings

#: Legacy morphology SQLite filename treated as migration input only.
LEGACY_DB_FILENAME = "morphology.sqlite3"
#: Explicit rebuild recipe printed after legacy reset or migration failure.
REBUILD_INSTRUCTIONS = (
    "wyrdcraeft morphology build",
    "wyrdcraeft dictionary build",
    "wyrdcraeft lexicon build",
)


def _noop_echo(_message: str) -> None:
    """
    Ignore one narration message when no echo callback was provided.

    Args:
        _message: Startup narration text that is intentionally discarded.

    """


def _empty_prompt(_message: str) -> str:
    """
    Return the default negative answer when no prompt callback was provided.

    Args:
        _message: Backup deletion prompt text that is intentionally ignored.

    Returns:
        Empty response, which keeps the backup by default.

    """
    return ""


class DatabaseMigrationError(RuntimeError):
    """
    Startup migration failure with traceback and rebuild guidance.

    Args:
        message: Human-readable failure summary.
        traceback_text: Captured traceback from the failed migration.
        rebuild_instructions: Explicit rebuild command recipe.

    """

    #: Captured traceback text from the failed Alembic run.
    traceback_text: str
    #: Explicit rebuild commands printed after a failed migration.
    rebuild_instructions: tuple[str, ...]

    def __init__(
        self,
        message: str,
        *,
        traceback_text: str,
        rebuild_instructions: tuple[str, ...],
    ) -> None:
        """
        Store the startup migration failure details for CLI reporting.

        Args:
            message: Human-readable failure summary.

        Keyword Args:
            traceback_text: Captured traceback from the failed migration.
            rebuild_instructions: Explicit rebuild command recipe.

        """
        super().__init__(message)
        #: Captured traceback text from the failed Alembic run.
        self.traceback_text = traceback_text
        #: Explicit rebuild commands printed after a failed migration.
        self.rebuild_instructions = rebuild_instructions


class LegacyDatabaseResetRequired(RuntimeError):
    """
    Legacy database reset stop signal with rebuild guidance.

    Args:
        backup_path: Backup copy created from the legacy morphology database.
        rebuild_instructions: Explicit rebuild command recipe.

    """

    #: Backup copy created from the legacy morphology database.
    backup_path: Path
    #: Explicit rebuild commands printed after the legacy reset stop.
    rebuild_instructions: tuple[str, ...]

    def __init__(
        self,
        *,
        backup_path: Path,
        rebuild_instructions: tuple[str, ...],
    ) -> None:
        """
        Store the backup path and explicit rebuild recipe for CLI reporting.

        Keyword Args:
            backup_path: Backup copy created from the legacy morphology database.
            rebuild_instructions: Explicit rebuild command recipe.

        """
        message = "\n".join(
            [
                (
                    "Legacy morphology.sqlite3 was backed up and replaced "
                    "with a fresh canonical database."
                ),
                f"backup={backup_path}",
                *rebuild_instructions,
            ]
        )
        super().__init__(message)
        #: Backup copy created from the legacy morphology database.
        self.backup_path = backup_path
        #: Explicit rebuild commands printed after the legacy reset stop.
        self.rebuild_instructions = rebuild_instructions


def create_engine(db_path: Path) -> Engine:
    """
    Build one SQLAlchemy engine for the canonical SQLite database.

    Args:
        db_path: SQLite database path.

    Returns:
        SQLAlchemy engine bound to ``db_path``.

    """
    resolved = db_path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return sqlalchemy_create_engine(f"sqlite:///{resolved}")


def create_session_factory(db_path: Path) -> sessionmaker[Session]:
    """
    Build one SQLAlchemy session factory for the canonical SQLite database.

    Args:
        db_path: SQLite database path.

    Returns:
        Session factory bound to ``db_path``.

    """
    return sessionmaker(bind=create_engine(db_path), future=True)


def build_alembic_config(db_path: Path) -> Config:
    """
    Build the Alembic configuration for one canonical SQLite database.

    Args:
        db_path: SQLite database path that migrations should target.

    Returns:
        Alembic config with absolute script location and SQLite URL.

    """
    repo_root = Path(__file__).resolve().parents[2]
    config = Config(str(repo_root / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str((repo_root / "wyrdcraeft/db/alembic").resolve()),
    )
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.expanduser().resolve()}")
    return config


def ensure_database_ready(
    *,
    settings: Settings,
    interactive: bool,
    echo: Callable[[str], None] | None = None,
    prompt: Callable[[str], str] | None = None,
) -> None:
    """
    Ensure the canonical SQLite database is ready for one CLI invocation.

    Keyword Args:
        settings: Loaded application settings.
        interactive: Whether prompting the user is allowed.
        echo: Optional progress narrator callback.
        prompt: Optional prompt callback for backup deletion confirmation.

    Raises:
        DatabaseMigrationError: Migration failed after creating a backup.
        LegacyDatabaseResetRequired: A legacy morphology database was reset.

    """
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=interactive,
        echo=echo,
        prompt=prompt,
    )
    runtime.ensure_ready()


def _remove_file_if_present(path: Path) -> None:
    """
    Delete one file when it exists.

    Args:
        path: Filesystem path that may need cleanup.

    Side Effects:
        Removes ``path`` when present.

    """
    path.unlink(missing_ok=True)


class DatabaseStartupRuntime:
    """
    Own the startup decision tree for canonical database readiness.

    Args:
        settings: Loaded application settings.
        interactive: Whether prompting the user is allowed.
        echo: Optional progress narrator callback.
        prompt: Optional prompt callback for backup deletion confirmation.
        now: Optional clock override used in tests.

    """

    #: Loaded application settings used to resolve the canonical DB path.
    settings: Settings
    #: Whether the runtime may prompt before deleting old backups.
    interactive: bool
    #: Narration callback for locked startup stage names.
    _echo: Callable[[str], None]
    #: Prompt callback for backup deletion confirmation.
    _prompt: Callable[[str], str]
    #: Clock used for backup timestamping and sidecar metadata.
    _now: Callable[[], datetime]
    #: Canonical SQLite database path under the configured app-data directory.
    db_path: Path
    #: Legacy morphology SQLite input path beside the canonical database.
    legacy_db_path: Path
    #: JSON sidecar store used for retained-backup prompt state.
    state_store: BackupStateStore
    #: Application version used in backup prompt narration.
    version: str

    def __init__(
        self,
        *,
        settings: Settings,
        interactive: bool,
        echo: Callable[[str], None] | None = None,
        prompt: Callable[[str], str] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        """
        Capture one startup runtime configuration and its collaborators.

        Keyword Args:
            settings: Loaded application settings.
            interactive: Whether prompting the user is allowed.
            echo: Optional progress narrator callback.
            prompt: Optional prompt callback for backup deletion confirmation.
            now: Optional clock override used in tests.

        """
        #: Loaded application settings used to resolve the canonical DB path.
        self.settings = settings
        #: Whether the runtime may prompt before deleting old backups.
        self.interactive = interactive
        #: Narration callback for locked startup stage names.
        self._echo = echo or _noop_echo
        #: Prompt callback for backup deletion confirmation.
        self._prompt = prompt or _empty_prompt
        #: Clock used for backup timestamping and sidecar metadata.
        self._now = now or (lambda: datetime.now(UTC))
        #: Canonical SQLite database path under the configured app-data directory.
        self.db_path = settings.get_canonical_db_path()
        #: Legacy morphology SQLite input path beside the canonical database.
        self.legacy_db_path = self.db_path.with_name(LEGACY_DB_FILENAME)
        #: JSON sidecar store used for retained-backup prompt state.
        self.state_store = BackupStateStore(self.db_path)
        #: Application version used in backup prompt narration.
        self.version = settings.app_version

    def ensure_ready(self) -> None:
        """
        Run the startup database decision tree once.

        Raises:
            DatabaseMigrationError: Migration failed after creating a backup.
            LegacyDatabaseResetRequired: A legacy morphology database was reset.

        """
        self._handle_pending_backup()
        self._emit("checking canonical database")

        if self.legacy_db_path.exists() and not self.db_path.exists():
            self._emit("found legacy database")
            backup_path = self._create_backup(self.legacy_db_path)
            self._reset_to_fresh_canonical_db()
            self._emit("rebuild required")
            raise LegacyDatabaseResetRequired(
                backup_path=backup_path,
                rebuild_instructions=REBUILD_INSTRUCTIONS,
            )

        if self.db_path.exists():
            self._emit("found canonical database")

        self._emit("checking alembic revision")
        current_revision = self._get_current_revision()
        head_revision = self._get_head_revision()
        if not self.db_path.exists():
            self._run_migration_attempt(
                backup_path=None,
                cleanup_paths=(self.db_path,),
            )
            return
        if current_revision is None:
            backup_path = self._create_backup(self.db_path)
            self._reset_to_fresh_canonical_db()
            self._emit("rebuild required")
            raise LegacyDatabaseResetRequired(
                backup_path=backup_path,
                rebuild_instructions=REBUILD_INSTRUCTIONS,
            )
        if current_revision is not None and current_revision == head_revision:
            return

        backup_path = self._create_backup(self.db_path)
        self._run_migration_attempt(backup_path=backup_path)

    def _reset_to_fresh_canonical_db(self) -> None:
        """
        Replace any existing canonical DB with a fresh Alembic-managed file.

        Side Effects:
            Removes ``self.db_path`` before running the migration bootstrap.

        """
        _remove_file_if_present(self.db_path)
        self._run_migration_attempt(
            backup_path=None,
            cleanup_paths=(self.db_path,),
        )

    def _create_backup(self, source_path: Path) -> Path:
        """
        Create one retained backup and update the canonical sidecar state.

        Args:
            source_path: SQLite database path that should be copied.

        Returns:
            Path to the newly created backup.

        Side Effects:
            Writes a timestamped backup copy and saves prompt state beside the
            canonical database.

        """
        self._emit("creating backup")
        backup_path = create_backup(
            source_path,
            migration_version=self.version,
            retention=1,
            now=self._now(),
        )
        self.state_store.save(
            {
                "backup_path": str(backup_path),
                "created_at": self._now().isoformat(),
                "migration_version": self.version,
            }
        )
        return backup_path

    def _apply_migrations_with_narration(self) -> None:
        """
        Apply Alembic migrations and emit the locked success narration.

        Side Effects:
            Runs Alembic bootstrap or upgrade work against the canonical DB.

        """
        self._emit("applying migrations")
        self._apply_migrations()
        self._emit("migration complete")

    def _run_migration_attempt(
        self,
        *,
        backup_path: Path | None,
        cleanup_paths: tuple[Path, ...] = (),
    ) -> None:
        """
        Run one narrated migration attempt with shared failure recovery.

        Keyword Args:
            backup_path: Optional canonical-db backup to restore after failure.
            cleanup_paths: Filesystem paths to remove after a failed attempt.

        Raises:
            DatabaseMigrationError: Migration failed after cleanup or restore.

        """
        try:
            self._apply_migrations_with_narration()
        except Exception as exc:
            self._emit("restoring backup after migration failure")
            if backup_path is not None:
                restore_backup(backup_path, self.db_path)
            for path in cleanup_paths:
                _remove_file_if_present(path)
            message = "Database migration failed."
            raise DatabaseMigrationError(
                message,
                traceback_text=traceback.format_exc(),
                rebuild_instructions=REBUILD_INSTRUCTIONS,
            ) from exc

    def _apply_migrations(self) -> None:
        """
        Run the Alembic bootstrap and upgrade path.

        Side Effects:
            Creates the SQLite database file and Alembic bookkeeping table when
            needed, then upgrades to the current head revision.

        """
        config = build_alembic_config(self.db_path)
        command.ensure_version(config)
        command.upgrade(config, "head")

    def _get_current_revision(self) -> str | None:
        """
        Read the current Alembic revision from the canonical database.

        Returns:
            Current revision string, or ``None`` when the database is missing or
            has not been versioned yet.

        """
        if not self.db_path.exists():
            return None
        engine = create_engine(self.db_path)
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except SQLAlchemyError:
            return None
        finally:
            engine.dispose()

    def _get_head_revision(self) -> str | None:
        """
        Read the current Alembic head revision from the scripts directory.

        Returns:
            Head revision string, or ``None`` when no revisions exist yet.

        """
        config = build_alembic_config(self.db_path)
        script_directory = ScriptDirectory.from_config(config)
        return script_directory.get_current_head()

    def _handle_pending_backup(self) -> None:
        """
        Offer to delete one retained backup from a prior successful migration.

        Side Effects:
            Prints a reminder or prompt, optionally deleting the backup and its
            sidecar state.

        """
        state = self.state_store.load()
        if state is None:
            return

        backup_path = Path(state["backup_path"])
        if not backup_path.exists():
            self.state_store.clear()
            return

        prompt_text = _format_backup_prompt_text(
            created_at=state["created_at"],
            migration_version=state["migration_version"],
        )
        if not self.interactive:
            self._echo(f"{prompt_text} Non-interactive mode kept the backup.")
            return

        if self._prompt(prompt_text).strip().lower() == "y":
            backup_path.unlink(missing_ok=True)
            self.state_store.clear()

    def _emit(self, stage: str) -> None:
        """
        Narrate one locked startup stage.

        Args:
            stage: Locked narration label to emit.

        """
        self._echo(stage)


def _format_backup_prompt_text(*, created_at: str, migration_version: str) -> str:
    """
    Build the locked backup deletion prompt text.

    Keyword Args:
        created_at: ISO timestamp recorded in the sidecar state.
        migration_version: Application version that caused the backup.

    Returns:
        Locked prompt string for interactive backup deletion confirmation.

    """
    backup_date = datetime.fromisoformat(created_at).date().isoformat()
    return (
        f"Found backup database from {backup_date}, caused by migration to "
        f"{migration_version}. Delete it? Answer `y` if you have used "
        "wyrdcraeft successfully since the last migration. [y/N]"
    )
