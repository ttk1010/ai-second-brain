"""Persistence to the external Obsidian Vault and optional Git (ADR 0002)."""

from backend.storage.illustration import IllustrationWriter
from backend.storage.vault import VaultWriter

__all__ = ["IllustrationWriter", "VaultWriter"]
