"""Vault path helpers: folder routing, filename slugging, collision handling.

Folder layout follows PROJECT_CHARTER.md. Phase 1 uses a coarse SourceType ->
folder mapping; finer classification (Models, Companies, Laws) is deferred to a
later issue once content analysis exists.
"""

from pathlib import Path

from backend.models.enums import SourceType

INBOX_FOLDER = "00 Inbox"

_FOLDER_BY_SOURCE: dict[SourceType, str] = {
    SourceType.CONCEPT: "01 Concepts",
    SourceType.COMPARISON: "04 Comparisons",
    SourceType.NEWS: "06 News",
    SourceType.PAPER: "07 Papers",
    SourceType.DOCUMENTATION: INBOX_FOLDER,
    SourceType.UNKNOWN: INBOX_FOLDER,
}

# Characters not allowed in file names across common filesystems.
_INVALID_CHARS = '/\\:*?"<>|'


def folder_for(source_type: SourceType) -> str:
    """Return the Vault folder name for a source type."""
    return _FOLDER_BY_SOURCE.get(source_type, INBOX_FOLDER)


def slugify_title(title: str) -> str:
    """Turn a note title into a safe file name stem (without extension).

    Obsidian supports non-ASCII names, so we keep readable titles (including
    Japanese) and only strip filesystem-invalid characters.
    """
    cleaned = "".join("-" if ch in _INVALID_CHARS else ch for ch in title)
    cleaned = " ".join(cleaned.split()).strip(" .-")
    return cleaned or "untitled"


def resolve_target(
    folder: Path,
    stem: str,
    *,
    overwrite: bool,
    suffix: str = ".md",
) -> Path:
    """Resolve the final file path inside ``folder`` for ``stem``.

    When ``overwrite`` is False and the file exists, append a numeric suffix
    (``-2``, ``-3``, ...) instead of overwriting, to protect existing files.
    ``suffix`` is the file extension (e.g. ``.md`` for notes, ``.png`` for
    illustrations).
    """
    candidate = folder / f"{stem}{suffix}"
    if overwrite or not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = folder / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
