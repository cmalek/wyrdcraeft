#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, ClassVar

import click
from pydantic import Field, ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

#: Default path to the TOML configuration file for olmocr_hf.
DEFAULT_CONFIG_FILE = Path.home() / ".hf_olmocr.toml"


class Settings(BaseSettings):
    """
    Application settings for running ``olmocr.pipeline``.

    Settings are resolved from three sources, in ascending order of precedence:

    1. A TOML configuration file.
    2. Environment variables prefixed with ``OLMOCR_``.
    3. Explicit initialization arguments, which are supplied by CLI options.

    The CLI wiring in :func:`main` uses this precedence so that command-line
    overrides win over environment variables, and environment variables win over
    the TOML file.
    """

    model_config = SettingsConfigDict(
        env_prefix="OLMOCR_",
        extra="ignore",
        case_sensitive=False,
    )

    workspace: Path = Field(
        default=Path("./olmocr-workspace"),
        description="Local workspace directory used by olmocr.",
    )
    server: str = Field(
        ...,
        description="OpenAI-compatible inference endpoint base URL.",
    )
    api_key: str = Field(
        ...,
        description="API key used to authenticate to the inference endpoint.",
    )
    model: str = Field(
        ...,
        description="Provider-specific model or endpoint name.",
    )
    pdfs: str = Field(
        ...,
        description="PDF path, glob, or directory value passed to olmocr.",
    )
    workers: int = Field(
        default=1,
        ge=1,
        description="Number of local olmocr workers.",
    )
    max_concurrent_requests: int = Field(
        default=2,
        ge=1,
        description="Maximum number of concurrent remote inference requests.",
    )
    pages_per_group: int = Field(
        default=1,
        ge=1,
        description="Number of PDF pages grouped into each model request.",
    )
    markdown: bool = Field(
        default=True,
        description="Whether markdown output is enabled.",
    )
    extra_args: str | None = Field(
        default=None,
        description="Additional raw command-line arguments appended to olmocr.",
    )

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
        Customize pydantic-settings source precedence.

        Args:
            settings_cls: The concrete settings class being instantiated.
            init_settings: Source for explicit initialization arguments.
            env_settings: Source for environment variables.
            dotenv_settings: Source for values loaded from dotenv files.
            file_secret_settings: Source for file-based secrets.

        Returns:
            A tuple of settings sources in descending precedence order.

        Notes:
            The TOML file path is read from ``settings_cls._toml_file`` when
            present, and otherwise defaults to :data:`DEFAULT_CONFIG_FILE`.

        """
        toml_file = getattr(settings_cls, "_toml_file", DEFAULT_CONFIG_FILE)
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=toml_file),
            dotenv_settings,
            file_secret_settings,
        )

    def normalized_server(self) -> str:
        """
        Return the normalized server URL.

        Ensures the configured server URL ends with a trailing slash, which is
        convenient when pointing at OpenAI-compatible ``/v1/`` endpoints.

        Returns:
            The normalized server URL.

        """
        server = self.server.strip()
        if not server.endswith("/"):
            server += "/"
        return server

    def build_command(self) -> list[str]:
        """
        Build the ``olmocr.pipeline`` subprocess command.

        Returns:
            The full argument vector that will be passed to
            :func:`subprocess.run`.

        """
        cmd = [
            sys.executable,
            "-m",
            "olmocr.pipeline",
            str(self.workspace),
            "--server",
            self.normalized_server(),
            "--api_key",
            self.api_key,
            "--workers",
            str(self.workers),
            "--max_concurrent_requests",
            str(self.max_concurrent_requests),
            "--pages_per_group",
            str(self.pages_per_group),
            "--model",
            self.model,
            "--pdfs",
            self.pdfs,
        ]

        if self.markdown:
            cmd.append("--markdown")

        if self.extra_args:
            cmd.extend(shlex.split(self.extra_args))

        print(cmd)

        return cmd


def load_settings(config_file: Path | None = None, **overrides: Any) -> Settings:
    """
    Load application settings with an optional TOML config override.

    Args:
        config_file: Optional TOML configuration file path. When omitted,
            :data:`DEFAULT_CONFIG_FILE` is used.
        **overrides: Explicit field overrides. Values of ``None`` are ignored so
            that unset CLI options do not suppress environment or TOML values.

    Returns:
        The resolved :class:`Settings` instance.

    """
    clean_overrides = {
        key: value for key, value in overrides.items() if value is not None
    }

    class ConfiguredSettings(Settings):
        """Concrete settings subclass bound to a specific TOML file path."""

        _toml_file: ClassVar[Path] = config_file or DEFAULT_CONFIG_FILE

    return ConfiguredSettings(**clean_overrides)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--config",
    "config_file",
    type=click.Path(path_type=Path, dir_okay=False),
    default=DEFAULT_CONFIG_FILE,
    show_default=str(DEFAULT_CONFIG_FILE),
    help="Path to the TOML config file.",
)
@click.option(
    "--workspace",
    type=click.Path(path_type=Path),
    help="Workspace directory. Env: OLMOCR_WORKSPACE",
)
@click.option(
    "--server",
    type=str,
    help="OpenAI-compatible endpoint base URL. Env: OLMOCR_SERVER",
)
@click.option(
    "--api-key",
    type=str,
    help="Endpoint API key. Env: OLMOCR_API_KEY",
)
@click.option(
    "--model",
    type=str,
    help="Endpoint model or endpoint name. Env: OLMOCR_MODEL",
)
@click.option(
    "--pdfs",
    type=str,
    help="PDF path, glob, or directory. Env: OLMOCR_PDFS",
)
@click.option(
    "--workers",
    type=int,
    help="Local worker count. Env: OLMOCR_WORKERS",
)
@click.option(
    "--max-concurrent-requests",
    type=int,
    help="Max concurrent remote requests. Env: OLMOCR_MAX_CONCURRENT_REQUESTS",
)
@click.option(
    "--pages-per-group",
    type=int,
    help="Pages per group. Env: OLMOCR_PAGES_PER_GROUP",
)
@click.option(
    "--markdown/--no-markdown",
    default=None,
    help="Enable or disable markdown output. Env: OLMOCR_MARKDOWN",
)
@click.option(
    "--extra-args",
    type=str,
    help='Extra raw args appended to olmocr, e.g. --extra-args="--foo bar".',
)
@click.option(
    "--print-command/--no-print-command",
    default=True,
    show_default=True,
    help="Print the resolved olmocr command before executing it.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the resolved command and exit without running it.",
)
def main(  # noqa: PLR0913
    config_file: Path,
    workspace: Path | None,
    server: str | None,
    api_key: str | None,
    model: str | None,
    pdfs: str | None,
    workers: int | None,
    max_concurrent_requests: int | None,
    pages_per_group: int | None,
    markdown: bool | None,
    extra_args: str | None,
    print_command: bool,
    dry_run: bool,
) -> None:
    """
    Run ``olmocr.pipeline`` using TOML, environment, and CLI settings.

    Args:
        config_file: TOML configuration file path.
        workspace: Optional workspace override.
        server: Optional inference endpoint URL override.
        api_key: Optional API key override.
        model: Optional model or endpoint name override.
        pdfs: Optional PDF path, glob, or directory override.
        workers: Optional worker count override.
        max_concurrent_requests: Optional concurrency override.
        pages_per_group: Optional pages-per-group override.
        markdown: Optional markdown-output override.
        extra_args: Optional extra raw olmocr arguments.
        print_command: Whether to print the resolved command.
        dry_run: Whether to skip command execution after printing it.

    Raises:
        SystemExit: Raised with exit code ``2`` for invalid configuration, or
            with the subprocess return code if ``olmocr.pipeline`` fails.

    """
    try:
        settings = load_settings(
            config_file=config_file,
            workspace=workspace,
            server=server,
            api_key=api_key,
            model=model,
            pdfs=pdfs,
            workers=workers,
            max_concurrent_requests=max_concurrent_requests,
            pages_per_group=pages_per_group,
            markdown=markdown,
            extra_args=extra_args,
        )
    except ValidationError as exc:
        click.echo("Invalid configuration:\n", err=True)
        click.echo(str(exc), err=True)
        raise SystemExit(2) from exc

    settings.workspace.mkdir(parents=True, exist_ok=True)
    cmd = settings.build_command()

    if print_command or dry_run:
        click.echo(f"Config file: {config_file}")
        click.echo("Resolved command:")
        click.echo(shlex.join(cmd))

    if dry_run:
        return

    env = os.environ.copy()
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


if __name__ == "__main__":
    main()
