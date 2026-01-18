"""
Settings management for oe_json_extractor.
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

from oe_json_extractor.exc import ConfigurationError


class Settings(BaseSettings):
    """
    Application settings with cascading configuration support.

    Note:
        The app_name and app_version fields are readonly (frozen=True) and
        cannot be overridden via configuration files or environment variables.
        Other fields remain configurable as normal.

    """

    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="OE_JSON_EXTRACTOR_",
    )

    # Application settings (readonly - cannot be overridden via configuration)
    app_name: str = Field(
        default="oe_json_extractor",
        description="Application name",
        frozen=True,
    )
    app_version: str = Field(
        default="0.1.0", description="Application version", frozen=True
    )

    # Write-able settings

    # Output settings
    default_output_format: Literal["table", "json", "text"] = Field(
        default="table", description="Default output format"
    )
    enable_colors: bool = Field(default=True, description="Enable colored output")
    quiet_mode: bool = Field(default=False, description="Enable quiet mode")

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    log_file: str | None = Field(default=None, description="Log file path")

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
                / "oe_json_extractor.toml"
            )
        else:  # Unix-like
            global_config = Path("/etc/cookiecutter.project_python_name}}.toml")

        if global_config.exists():
            config_paths.append(global_config)

        # User home configuration
        user_config = Path.home() / ".oe_json_extractor.toml"
        if user_config.exists():
            config_paths.append(user_config)

        # Local configuration
        local_config = Path.cwd() / ".oe_json_extractor.toml"
        if local_config.exists():
            config_paths.append(local_config)

        config_file = os.environ.get("OE_JSON_EXTRACTOR_CONFIG_FILE")
        # Explicit configuration file (highest precedence)
        if config_file:
            explicit_config = Path(config_file)
            if explicit_config.exists():
                config_paths.append(explicit_config)

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
                / "oe_json_extractor"
                / "config.toml"
            )
        else:  # Unix-like
            global_config = Path("/etc/oe_json_extractor/config.toml")

        if global_config.exists():
            paths.append(global_config)

        # User home configuration
        user_config = Path.home() / ".oe_json_extractor.toml"
        if user_config.exists():
            paths.append(user_config)

        # Local configuration
        local_config = Path.cwd() / ".oe_json_extractor.toml"
        if local_config.exists():
            paths.append(local_config)

        return paths

    def validate_settings(self) -> None:
        """
        Validate settings and ensure required directories exist.

        Raises:
            ConfigurationError: If settings are invalid

        """
        # Validate output format
        if self.default_output_format not in ["table", "json", "text"]:
            msg = f"Invalid output format: {self.default_output_format}"
            raise ConfigurationError(msg)
