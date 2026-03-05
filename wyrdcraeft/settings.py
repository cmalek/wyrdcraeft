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
from .models import AnyLLMConfig


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

    # LLM settings
    #: LLM model identifier.
    llm_model_id: str = Field(
        default="qwen2.5:14b-instruct", description="LLM model ID"
    )
    #: LLM provider name.
    llm_provider: Literal["ollama", "gemini", "openai"] = Field(
        default="ollama", description="LLM provider"
    )
    #: LLM generation temperature.
    llm_temperature: float = Field(default=0.0, description="LLM temperature")
    #: LLM max output tokens.
    llm_max_tokens: int = Field(default=4096, description="LLM max tokens")
    #: LLM request timeout in seconds.
    llm_timeout_s: int = Field(default=120, description="LLM timeout in seconds")
    #: OpenAI API key.
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    #: Gemini API key.
    gemini_api_key: str | None = Field(default=None, description="Gemini API key")

    # OCR + olmocr settings
    #: Upstream OpenAI-compatible base URL for OCR proxy forwarding.
    ocr_upstream_base_url: str = Field(
        default="http://127.0.0.1:8080/v1",
        description="Upstream OpenAI-compatible base URL for OCR proxy forwarding.",
    )
    #: Default olmocr model identifier/path used for OCR pipeline requests.
    ocr_olmocr_model: str = Field(
        default="./data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf",
        description="Default olmocr model identifier or local path.",
    )
    #: Local worker count for olmocr pipeline.
    ocr_olmocr_workers: int = Field(
        default=1,
        description="Local worker count for olmocr pipeline.",
    )
    #: Maximum concurrent requests for local olmocr runs.
    ocr_olmocr_max_concurrent_requests: int = Field(
        default=1,
        description="Maximum concurrent requests for local olmocr runs.",
    )
    #: Target longest image dimension for olmocr rendering.
    ocr_olmocr_target_longest_image_dim: int = Field(
        default=1024,
        description="Target longest image dimension for olmocr rendering.",
    )
    #: Per-page retry budget for olmocr runs.
    ocr_olmocr_max_page_retries: int = Field(
        default=5,
        description="Per-page retry budget for olmocr runs.",
    )
    #: Legacy OCR language option retained for compatibility.
    ocr_legacy_lang: str = Field(
        default="eng+lat",
        description="Legacy OCR language option retained for compatibility.",
    )
    #: Legacy Tesseract PSM option retained for compatibility.
    ocr_legacy_tesseract_psm: int = Field(
        default=4,
        description="Legacy Tesseract PSM option retained for compatibility.",
    )
    #: Legacy oversample DPI option retained for compatibility.
    ocr_legacy_oversample_dpi: int = Field(
        default=400,
        description="Legacy oversample DPI option retained for compatibility.",
    )
    #: Default skip_ocr behavior for the old-english OCR command.
    ocr_skip_ocr: bool = Field(
        default=False,
        description="Default skip_ocr behavior for old-english OCR command.",
    )

    # OCR proxy settings
    #: Bind host for standalone OCR proxy command.
    ocr_proxy_host: str = Field(
        default="127.0.0.1",
        description="Bind host for standalone OCR proxy command.",
    )
    #: Bind port for standalone OCR proxy command.
    ocr_proxy_port: int = Field(
        default=8001,
        description="Bind port for standalone OCR proxy command.",
    )
    #: Clamp cap for completion token fields at proxy boundary.
    ocr_proxy_max_tokens_cap: int = Field(
        default=1500,
        description="Clamp cap for completion token fields at proxy boundary.",
    )
    #: Enable conservative finish_reason length->stop override.
    ocr_proxy_override_length_to_stop: bool = Field(
        default=True,
        description="Enable conservative finish_reason length->stop override.",
    )
    #: Minimum body chars after YAML for length->stop override.
    ocr_proxy_min_body_chars_after_yaml: int = Field(
        default=50,
        description="Minimum body chars after YAML for length->stop override.",
    )
    #: Minimum body lines after YAML for length->stop override.
    ocr_proxy_min_body_lines_after_yaml: int = Field(
        default=5,
        description="Minimum body lines after YAML for length->stop override.",
    )
    #: Synchronize max_tokens and max_completion_tokens when true.
    ocr_proxy_clamp_both_token_fields: bool = Field(
        default=False,
        description="Synchronize max_tokens and max_completion_tokens when true.",
    )
    #: Optional temperature override applied by proxy.
    ocr_proxy_temperature_override: float | None = Field(
        default=None,
        description="Optional temperature override applied by proxy.",
    )
    #: Optional top_p override applied by proxy.
    ocr_proxy_top_p_override: float | None = Field(
        default=None,
        description="Optional top_p override applied by proxy.",
    )
    #: Upstream request timeout in seconds for proxy forwarding.
    ocr_proxy_upstream_timeout_seconds: float = Field(
        default=120.0,
        description="Upstream request timeout in seconds for proxy forwarding.",
    )
    #: Maximum retry attempts for transient upstream proxy request failures.
    ocr_proxy_upstream_max_retries: int = Field(
        default=2,
        description="Maximum retry attempts for transient upstream proxy failures.",
    )
    #: Base backoff in seconds between transient upstream retry attempts.
    ocr_proxy_upstream_retry_backoff_seconds: float = Field(
        default=0.5,
        description="Base retry backoff in seconds for upstream proxy failures.",
    )
    #: Timeout in seconds waiting for managed proxy startup.
    ocr_proxy_startup_timeout_seconds: float = Field(
        default=15.0,
        description="Timeout in seconds waiting for managed proxy startup.",
    )

    # Write-able settings

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

    def validate_settings(self) -> None:  # noqa: PLR0912, PLR0915
        """
        Validate settings and ensure required directories exist.

        Raises:
            ConfigurationError: If settings are invalid

        """
        # Validate output format
        if self.default_output_format not in ["table", "json", "text"]:
            msg = f"Invalid output format: {self.default_output_format}"
            raise ConfigurationError(msg)

        if self.llm_provider not in {"ollama", "gemini", "openai"}:
            msg = f"Invalid LLM provider: {self.llm_provider}"
            raise ConfigurationError(msg)

        try:
            self.llm_provider = self.get_model_provider(self.llm_model_id)
        except ValueError as e:
            raise ConfigurationError(str(e)) from e

        if self.llm_temperature < 0 or self.llm_temperature > 1:
            msg = "LLM temperature must be between 0 and 1"
            raise ConfigurationError(msg)

        if self.llm_max_tokens <= 0:
            msg = "LLM max tokens must be greater than 0"
            raise ConfigurationError(msg)

        # Validate LLM timeout
        if self.llm_timeout_s <= 0:
            msg = "LLM timeout must be greater than 0"
            raise ConfigurationError(msg)

        if self.ocr_olmocr_workers <= 0:
            msg = "ocr_olmocr_workers must be greater than 0"
            raise ConfigurationError(msg)
        if not self.ocr_olmocr_model.strip():
            msg = "ocr_olmocr_model must not be empty"
            raise ConfigurationError(msg)
        if self.ocr_olmocr_max_concurrent_requests <= 0:
            msg = "ocr_olmocr_max_concurrent_requests must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_olmocr_target_longest_image_dim <= 0:
            msg = "ocr_olmocr_target_longest_image_dim must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_olmocr_max_page_retries <= 0:
            msg = "ocr_olmocr_max_page_retries must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_legacy_tesseract_psm <= 0:
            msg = "ocr_legacy_tesseract_psm must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_legacy_oversample_dpi <= 0:
            msg = "ocr_legacy_oversample_dpi must be greater than 0"
            raise ConfigurationError(msg)

        if self.ocr_proxy_port <= 0:
            msg = "ocr_proxy_port must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_max_tokens_cap <= 0:
            msg = "ocr_proxy_max_tokens_cap must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_min_body_chars_after_yaml < 0:
            msg = "ocr_proxy_min_body_chars_after_yaml must be >= 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_min_body_lines_after_yaml < 0:
            msg = "ocr_proxy_min_body_lines_after_yaml must be >= 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_upstream_timeout_seconds <= 0:
            msg = "ocr_proxy_upstream_timeout_seconds must be greater than 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_upstream_max_retries < 0:
            msg = "ocr_proxy_upstream_max_retries must be >= 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_upstream_retry_backoff_seconds < 0:
            msg = "ocr_proxy_upstream_retry_backoff_seconds must be >= 0"
            raise ConfigurationError(msg)
        if self.ocr_proxy_startup_timeout_seconds <= 0:
            msg = "ocr_proxy_startup_timeout_seconds must be greater than 0"
            raise ConfigurationError(msg)

    def get_model_provider(
        self, model_id: str
    ) -> Literal["ollama", "gemini", "openai"]:
        """
        Get the provider for a model ID.

        Args:
            model_id: Model identifier string.

        Raises:
            ValueError: If the model ID is not supported.

        Returns:
            The provider for the model ID.

        """
        if model_id.startswith("qwen"):
            return "ollama"
        if model_id.startswith("gemini"):
            return "gemini"
        if model_id.startswith(("gpt-", "o1", "o3")):
            return "openai"
        msg = f"Unsupported model: {model_id}: Supported models are: "
        "qwen*, gemini*, gpt-*, o1*, o3*"
        raise ValueError(msg)

    @property
    def llm_config(self) -> AnyLLMConfig:
        """
        Get LLM configuration.

        Returns:
            LLM configuration

        """
        return AnyLLMConfig(
            provider=self.llm_provider,
            model_id=self.llm_model_id,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
            timeout_s=self.llm_timeout_s,
        )
