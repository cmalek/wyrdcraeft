"""
Settings management for wyrdcraeft.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from .exc import ConfigurationError
from .paths import get_canonical_db_path


class Settings(BaseSettings):
    """
    Application settings with cascading configuration support.

    Note:
        The app_name and app_version fields are readonly (frozen=True) and
        cannot be overridden via configuration files or environment variables.
        Other fields remain configurable as normal.

    """

    #: Pydantic settings configuration for env, dotenv, and config file loading.
    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="wyrdcraeft_",
    )

    # Application settings (readonly - cannot be overridden via configuration)
    #: Application name (readonly).
    app_name: str = Field(
        default="wyrdcraeft",
        description="Application name",
        frozen=True,
    )
    #: Application version (readonly).
    app_version: str = Field(
        default="0.1.0", description="Application version", frozen=True
    )

    # Write-able settings

    # Application data settings
    #: Override OS-specific application data directory.
    app_data_dir: Path | None = Field(
        default=None,
        description="Override OS-specific application data directory.",
    )

    # Output settings
    #: Default output rendering format.
    default_output_format: Literal["table", "json", "text"] = Field(
        default="table", description="Default output format"
    )
    #: Whether colored output is enabled.
    enable_colors: bool = Field(default=True, description="Enable colored output")
    #: Whether quiet mode is enabled.
    quiet_mode: bool = Field(default=False, description="Enable quiet mode")

    # Diacritic disambiguate UI
    #: Maximum rows shown in Attested Forms table.
    max_attested_rows: int = Field(
        default=5,
        description="Max rows shown in Attested Forms table (diacritic disambiguate).",
    )
    #: Lemma cadence for live morphology generation progress updates.
    morphology_progress_every_words: int = Field(
        default=5,
        description="Lemma cadence for live morphology generation progress updates.",
    )

    # Logging settings
    #: Logging verbosity level.
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    #: Optional log file path.
    log_file: str | None = Field(default=None, description="Log file path")

    @classmethod
    def default_settings_path(cls) -> Path:
        """
        Return the default local settings file path used by the CLI.

        Returns:
            The default settings file path.

        """
        return Path.cwd() / ".wyrdcraeft.toml"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Load settings from file with cascading configuration.

        Args:
            config_file: Optional path to configuration file
            settings_cls: The settings class to load.
            init_settings: The initial settings to load.
            env_settings: The environment settings to load.
            dotenv_settings: The dotenv settings to load.
            file_secret_settings: The file secret settings to load.

        Returns:
            Loaded settings instance

        """
        # Define configuration file paths in order of precedence
        config_paths = []

        # Global configuration
        if os.name == "nt":  # Windows
            global_config = (
                Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
                / "wyrdcraeft.toml"
            )
        else:  # Unix-like
            global_config = Path("/etc/cookiecutter.project_python_name}}.toml")

        if global_config.exists():
            config_paths.append(global_config)

        # User home configuration
        config_dir = Path.home() / ".config"
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
        user_config = config_dir / "wyrdcraeft.toml"
        if user_config.exists():
            config_paths.append(user_config)

        # Local configuration
        local_config = Path.cwd() / ".wyrdcraeft.toml"
        if local_config.exists():
            config_paths.append(local_config)

        # Explicit configuration file (highest precedence). Support both the
        # canonical uppercase key and the historical mixed-case key.
        for key in ("WYRDCRAEFT_CONFIG_FILE", "wyrdcraeft_CONFIG_FILE"):
            config_file = os.environ.get(key)
            if not config_file:
                continue
            explicit_config = Path(config_file)
            if explicit_config.exists():
                config_paths.append(explicit_config)
                break

        # Load settings with file configuration
        if config_paths:
            # Use the last (highest precedence) config file
            config_file_path = config_paths[-1]
            return (TomlConfigSettingsSource(settings_cls, config_file_path.resolve()),)

        # Fallback: return the defaults you were passed in, preserving
        # SettingsConfigDict behavior
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    def get_config_paths(self) -> list[Path]:
        """
        Get list of configuration file paths that were loaded.
        Use this for debugging.

        Returns:
            List of configuration file paths

        """
        paths = []

        # Global configuration
        if os.name == "nt":  # Windows
            global_config = (
                Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
                / "wyrdcraeft"
                / "config.toml"
            )
        else:  # Unix-like
            global_config = Path("/etc/wyrdcraeft.toml")

        if global_config.exists():
            paths.append(global_config)

        # User home configuration
        config_dir = Path.home() / ".config"
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
        user_config = config_dir / "wyrdcraeft.toml"
        if user_config.exists():
            paths.append(user_config)

        # Local configuration
        local_config = Path.cwd() / ".wyrdcraeft.toml"
        if local_config.exists():
            paths.append(local_config)

        return paths

    def get_canonical_db_path(self) -> Path:
        """
        Resolve the canonical SQLite database path for these settings.

        Returns:
            Absolute path to ``wyrdcraeft.sqlite3`` under the configured
            application data directory.

        """
        return get_canonical_db_path(app_data_dir=self.app_data_dir)

    def validate_settings(self) -> None:
        """
        Validate settings and ensure required directories exist.

        Raises:
            ConfigurationError: If settings are invalid

        """
        if self.default_output_format not in ["table", "json", "text"]:
            msg = f"Invalid output format: {self.default_output_format}"
            raise ConfigurationError(msg)
