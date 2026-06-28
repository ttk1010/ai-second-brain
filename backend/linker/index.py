"""Vault index — a deterministic, read-only view of the existing notes.

Scans the external Vault and parses each note's frontmatter into a compact
record. This is the input the Claude Code relink skill (Issue #23) reasons over
to decide which notes are related. No LLM and no network are involved here
(PROJECT_CHARTER.md: AI-assisted, not AI-dependent; this layer is deterministic).
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from backend.storage.frontmatter import parse_frontmatter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NoteRecord:
    """A single note's structured data, as read from disk."""

    title: str
    name: str  # filename stem — the wikilink target ([[name]])
    path: str  # Vault-relative, POSIX
    tags: list[str] = field(default_factory=list)
    source_type: str = ""
    id: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "name": self.name,
            "path": self.path,
            "tags": self.tags,
            "source_type": self.source_type,
            "id": self.id,
        }


class VaultIndex:
    """An index of every Markdown note in a Vault."""

    def __init__(self, notes: list[NoteRecord]) -> None:
        self.notes = notes

    @classmethod
    def build(cls, vault_path: Path) -> "VaultIndex":
        """Scan ``vault_path`` for Markdown notes and index their frontmatter."""
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

        records: list[NoteRecord] = []
        for note_path in sorted(vault_path.rglob("*.md")):
            record = _read_record(note_path, vault_path)
            if record is not None:
                records.append(record)
        logger.info("Indexed %d notes from %s", len(records), vault_path)
        return cls(records)

    def to_list(self) -> list[dict]:
        """Return a JSON-serializable list of note records."""
        return [note.to_dict() for note in self.notes]


def _read_record(note_path: Path, vault_path: Path) -> NoteRecord | None:
    """Read one note into a record, tolerating missing or malformed frontmatter."""
    try:
        text = note_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning("Could not read %s: %s", note_path, exc)
        return None

    relative = note_path.relative_to(vault_path).as_posix()
    frontmatter = parse_frontmatter(text)

    title = str(frontmatter.get("title") or "").strip() or _title_from_body(text, note_path)
    tags = _string_list(frontmatter.get("tags"))
    source_type = str(frontmatter.get("source_type") or "").strip()
    note_id = str(frontmatter.get("id") or "").strip()

    return NoteRecord(
        title=title,
        name=note_path.stem,
        path=relative,
        tags=tags,
        source_type=source_type,
        id=note_id,
    )


def _title_from_body(text: str, note_path: Path) -> str:
    """Fall back to the first level-1 heading, then the file stem."""
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return note_path.stem


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
