"""Tests for the settings loader (Issue #5)."""

from pathlib import Path

import pytest

from backend.config import EXAMPLE_SETTINGS_PATH, Settings, SettingsError, load_settings
from backend.models.enums import AspectRatio, ImageQuality

VALID_TOML = """\
vault_path = "{vault}"
image_output_dir = "Images"
default_aspect_ratio = "16:9"
image_model = "gpt-image-2"
default_language = "ja"
auto_commit = false
"""


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_valid_settings(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    cfg = _write(tmp_path / "settings.toml", VALID_TOML.format(vault=vault))

    settings = load_settings(cfg)

    assert settings.vault_path == vault
    assert settings.image_model == "gpt-image-2"
    assert settings.default_aspect_ratio is AspectRatio.WIDE
    assert settings.auto_commit is False


def test_defaults_are_applied(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    cfg = _write(tmp_path / "settings.toml", f'vault_path = "{vault}"\n')

    settings = load_settings(cfg)

    assert settings.image_output_dir == "Images"
    assert settings.image_quality is ImageQuality.MEDIUM
    assert settings.default_language == "ja"
    assert settings.auto_commit is False


def test_missing_file_raises_with_guidance(tmp_path: Path) -> None:
    with pytest.raises(SettingsError, match="not found"):
        load_settings(tmp_path / "missing.toml")


def test_missing_vault_path_raises(tmp_path: Path) -> None:
    cfg = _write(tmp_path / "settings.toml", 'image_model = "gpt-image-2"\n')
    with pytest.raises(SettingsError, match="Invalid settings"):
        load_settings(cfg, validate_vault=False)


def test_invalid_aspect_ratio_raises(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path / "settings.toml",
        'vault_path = "/tmp/v"\ndefault_aspect_ratio = "3:2"\n',
    )
    with pytest.raises(SettingsError, match="Invalid settings"):
        load_settings(cfg, validate_vault=False)


def test_invalid_quality_raises(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path / "settings.toml",
        'vault_path = "/tmp/v"\nimage_quality = "ultra"\n',
    )
    with pytest.raises(SettingsError, match="Invalid settings"):
        load_settings(cfg, validate_vault=False)


def test_unknown_field_is_forbidden(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path / "settings.toml",
        'vault_path = "/tmp/v"\nunknown_option = true\n',
    )
    with pytest.raises(SettingsError, match="Invalid settings"):
        load_settings(cfg, validate_vault=False)


def test_placeholder_vault_path_is_detected(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path / "settings.toml",
        'vault_path = "/path/to/your/Obsidian/AI Second Brain"\n',
    )
    with pytest.raises(SettingsError, match="placeholder"):
        load_settings(cfg, validate_vault=True)


def test_nonexistent_vault_path_is_detected(tmp_path: Path) -> None:
    cfg = _write(tmp_path / "settings.toml", f'vault_path = "{tmp_path / "nope"}"\n')
    with pytest.raises(SettingsError, match="does not exist"):
        load_settings(cfg, validate_vault=True)


def test_vault_path_must_be_directory(tmp_path: Path) -> None:
    a_file = _write(tmp_path / "afile", "x")
    cfg = _write(tmp_path / "settings.toml", f'vault_path = "{a_file}"\n')
    with pytest.raises(SettingsError, match="not a directory"):
        load_settings(cfg, validate_vault=True)


def test_example_settings_file_loads() -> None:
    # The shipped example must be structurally valid (vault check skipped).
    settings = load_settings(EXAMPLE_SETTINGS_PATH, validate_vault=False)
    assert isinstance(settings, Settings)
    assert settings.image_model == "gpt-image-2"
