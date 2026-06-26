"""Application configuration loading and validation.

Config is a cross-cutting concern used across all backend modules, so it lives
in its own package alongside the ADR 0002 layout.
"""

from backend.config.settings import (
    DEFAULT_SETTINGS_PATH,
    EXAMPLE_SETTINGS_PATH,
    Settings,
    SettingsError,
    load_settings,
)

__all__ = [
    "DEFAULT_SETTINGS_PATH",
    "EXAMPLE_SETTINGS_PATH",
    "Settings",
    "SettingsError",
    "load_settings",
]
