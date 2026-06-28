"""Persist Knowledge Nodes into the external Obsidian Vault (ADR 0002).

The Vault lives outside this repository at ``vault_path``. This writer turns a
Knowledge Object plus its rendered Markdown into a file on disk (a Knowledge
Node) and records the relative path back into ``ko.outputs`` (references only,
ADR 0001).
"""

import logging
from pathlib import Path

from backend.models import KnowledgeObject
from backend.models.enums import SourceType
from backend.storage.frontmatter import parse_frontmatter
from backend.storage.paths import folder_for, resolve_target, slugify_title

logger = logging.getLogger(__name__)


class VaultWriter:
    """Writes Markdown notes into a Vault directory."""

    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path

    def find_existing(self, source_type: SourceType, source: str) -> Path | None:
        """Return an existing note whose frontmatter ``source`` matches, if any.

        Used for idempotent generation: the same concept/URL is not regenerated.
        The match is on the canonical ``source`` value, not the (short_title-based)
        filename.
        """
        folder = self._vault_path / folder_for(source_type)
        if not folder.is_dir():
            return None
        wanted = source.strip()
        for note in sorted(folder.glob("*.md")):
            frontmatter = parse_frontmatter(note.read_text(encoding="utf-8"))
            if str(frontmatter.get("source") or "").strip() == wanted:
                return note
        return None

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
