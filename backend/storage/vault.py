"""Persist Knowledge Nodes into the external Obsidian Vault (ADR 0002).

The Vault lives outside this repository at ``vault_path``. This writer turns a
Knowledge Object plus its rendered Markdown into a file on disk (a Knowledge
Node) and records the relative path back into ``ko.outputs`` (references only,
ADR 0001).
"""

import logging
from pathlib import Path

from backend.models import KnowledgeObject
from backend.storage.paths import folder_for, resolve_target, slugify_title

logger = logging.getLogger(__name__)


class VaultWriter:
    """Writes Markdown notes into a Vault directory."""

    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path

    def write(
        self,
        ko: KnowledgeObject,
        markdown: str,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write ``markdown`` for ``ko`` into the Vault.

        Returns the absolute path written. Records the Vault-relative path in
        ``ko.outputs['markdown']``.

        Raises:
            FileNotFoundError: If the Vault path does not exist.
        """
        if not self._vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self._vault_path}")

        folder = self._vault_path / folder_for(ko.source.type)
        folder.mkdir(parents=True, exist_ok=True)

        target = resolve_target(
            folder, slugify_title(ko.short_title or ko.title), overwrite=overwrite
        )
        target.write_text(markdown, encoding="utf-8")

        relative = target.relative_to(self._vault_path)
        ko.outputs = {**ko.outputs, "markdown": str(relative)}

        logger.info("Wrote Knowledge Node: %s", relative)
        return target
