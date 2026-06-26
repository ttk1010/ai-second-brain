"""Application settings loaded from ``config/settings.toml``.

The settings are validated with pydantic. Type and format are checked by the
``Settings`` model; the existence of ``vault_path`` is verified separately by
``load_settings`` so that tests and CI can construct settings without a real
Vault on disk (see ADR 0002).
"""

import logging
import tomllib
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.models.enums import AspectRatio, ImageQuality

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = Path("config/settings.toml")
EXAMPLE_SETTINGS_PATH = Path("config/settings.example.toml")

# Placeholder shipped in settings.example.toml; a real config must replace it.
_VAULT_PATH_PLACEHOLDER = "/path/to/your/Obsidian/AI Second Brain"


class Settings(BaseSettings):
    """Validated application configuration.

    Field formats are validated here. Whether ``vault_path`` actually exists on
    disk is checked by ``load_settings``, not by the model itself.
    """

    model_config = SettingsConfigDict(extra="forbid", validate_assignment=True)

    vault_path: Path
    image_output_dir: str = "Images"
    default_aspect_ratio: AspectRatio = AspectRatio.WIDE
    image_model: str = "gpt-image-2"
    image_quality: ImageQuality = ImageQuality.MEDIUM
    default_language: str = "ja"
    auto_commit: bool = Field(default=False)


class SettingsError(Exception):
    """Raised when settings cannot be loaded or are invalid."""


def load_settings(
    path: Path = DEFAULT_SETTINGS_PATH,
    *,
    validate_vault: bool = True,
) -> Settings:
    """Load and validate settings from a TOML file.

    Args:
        path: Path to the TOML settings file.
        validate_vault: When True, verify that ``vault_path`` exists and is a
            directory, and that it is not the example placeholder.

    Raises:
        SettingsError: If the file is missing, malformed, or invalid.
    """
    if not path.exists():
        raise SettingsError(
            f"Settings file not found: {path}. "
            f"Copy {EXAMPLE_SETTINGS_PATH} to {path} and fill in your values."
        )

    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise SettingsError(f"Invalid TOML in {path}: {exc}") from exc

    try:
        settings = Settings(**data)
    except ValueError as exc:
        raise SettingsError(f"Invalid settings in {path}: {exc}") from exc

    if validate_vault:
        _validate_vault_path(settings.vault_path, path)

    logger.info("Loaded settings from %s (vault_path=%s)", path, settings.vault_path)
    return settings


def _validate_vault_path(vault_path: Path, source: Path) -> None:
    if str(vault_path) == _VAULT_PATH_PLACEHOLDER:
        raise SettingsError(
            f"vault_path in {source} is still the example placeholder. "
            "Set it to your external Obsidian Vault path."
        )
    if not vault_path.exists():
        raise SettingsError(
            f"vault_path does not exist: {vault_path}. Set it to your external Obsidian Vault path."
        )
    if not vault_path.is_dir():
        raise SettingsError(f"vault_path is not a directory: {vault_path}.")
