"""Knowledge Linker — identifies relationships between knowledge."""

from backend.linker.index import NoteRecord, VaultIndex
from backend.linker.related import RelatedLink, render_related, update_related_section

__all__ = [
    "NoteRecord",
    "RelatedLink",
    "VaultIndex",
    "render_related",
    "update_related_section",
]
