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
        filename. When more than one note shares the same ``source`` (a Vault that
        was already duplicated before Issue #39's fix), a warning is logged and the
        first (name-sorted) match is returned deterministically so behavior is
        stable; duplicates are left for the user to remove.
        """
        folder = self._vault_path / folder_for(source_type)
        if not folder.is_dir():
            return None
        wanted = source.strip()
        matches = [
            note
            for note in sorted(folder.glob("*.md"))
            if str(parse_frontmatter(note.read_text(encoding="utf-8")).get("source") or "").strip()
            == wanted
        ]
        if not matches:
            return None
        if len(matches) > 1:
            names = ", ".join(note.name for note in matches)
            logger.warning(
                "Multiple notes share source %r: %s. Using %s; remove the duplicates.",
                wanted,
                names,
                matches[0].name,
            )
        return matches[0]

    def pinned_stem(self, ko: KnowledgeObject, *, overwrite: bool) -> str | None:
        """Return the filename stem to reuse when regenerating ``ko`` (Issue #39).

        On ``overwrite``, an existing note for the same ``source`` is rewritten in
        place under its current filename (decision: option A — keep the name so
        Obsidian ``[[links]]`` and illustration embeds never break). Returns that
        existing stem, or ``None`` when there is nothing to pin to (no overwrite,
        or no existing note) so callers fall back to the short_title-derived name.

        A drift between the existing filename and the freshly generated
        short_title is logged, not applied: the improved title is available but the
        filename stays put to preserve links. Shared here so the same in-place
        resolution can back Issue #29's illustration-only regeneration later.
        """
        if not overwrite:
            return None
        existing = self.find_existing(ko.source.type, ko.source.value)
        if existing is None:
            return None
        stem = existing.stem
        regenerated = slugify_title(ko.short_title or ko.title)
        if regenerated != stem:
            logger.info(
                "Keeping existing filename %r (regenerated title would be %r) to preserve links.",
                stem,
                regenerated,
            )
        return stem

    def write(
        self,
        ko: KnowledgeObject,
        markdown: str,
        *,
        overwrite: bool = False,
        stem: str | None = None,
    ) -> Path:
        """Write ``markdown`` for ``ko`` into the Vault.

        Returns the absolute path written. Records the Vault-relative path in
        ``ko.outputs['markdown']``. ``stem`` pins the filename (Issue #39): when
        given (from :meth:`pinned_stem` on overwrite) the note is written under
        that exact name so an existing note is replaced in place instead of
        duplicated; otherwise the name is derived from the short_title.

        Raises:
            FileNotFoundError: If the Vault path does not exist.
        """
        if not self._vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self._vault_path}")

        folder = self._vault_path / folder_for(ko.source.type)
        folder.mkdir(parents=True, exist_ok=True)

        target = resolve_target(
            folder, stem or slugify_title(ko.short_title or ko.title), overwrite=overwrite
        )
        target.write_text(markdown, encoding="utf-8")

        relative = target.relative_to(self._vault_path)
        ko.outputs = {**ko.outputs, "markdown": str(relative)}

        logger.info("Wrote Knowledge Node: %s", relative)
        return target
