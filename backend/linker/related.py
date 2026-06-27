"""Safe, idempotent updates to a note's "Related Notes" section.

The Claude Code relink skill (Issue #23) decides *which* notes are related; this
module performs the *write* deterministically, touching only the Related Notes
section so the rest of the note (frontmatter, summary, illustration, …) is never
disturbed. Re-running with the same links is a no-op.
"""

import re
from dataclasses import dataclass

from backend.markdown.template import PLACEHOLDER, section

_RELATED_HEADING = section("Related Notes")
# Captures the Related Notes section body up to the next "## " heading or EOF.
_SECTION_RE = re.compile(
    rf"^{re.escape(_RELATED_HEADING)}[ \t]*\n(.*?)(?=^## |\Z)",
    re.DOTALL | re.MULTILINE,
)


@dataclass(frozen=True)
class RelatedLink:
    """A link to another note, with an optional relationship type."""

    title: str
    relationship: str | None = None

    @classmethod
    def parse(cls, value: str) -> "RelatedLink":
        """Parse a ``Title`` or ``Title:relationship`` string (titles have no colon)."""
        title, _, rel = value.partition(":")
        return cls(title=title.strip(), relationship=rel.strip() or None)


def render_related(links: list[RelatedLink]) -> str:
    """Render the body of the Related Notes section (links or a placeholder)."""
    seen: set[str] = set()
    lines: list[str] = []
    for link in links:
        title = link.title.strip()
        if not title or title in seen:
            continue
        seen.add(title)
        line = f"- [[{title}]]"
        if link.relationship:
            line += f" — {link.relationship}"
        lines.append(line)
    return "\n".join(lines) if lines else PLACEHOLDER


def update_related_section(markdown: str, links: list[RelatedLink]) -> str:
    """Return ``markdown`` with its Related Notes section set to ``links``.

    Only the Related Notes section changes. If the section is absent, it is
    inserted before References (or appended). The operation is idempotent.
    """
    body = render_related(links)
    block_body = f"\n{body}\n\n"

    if _SECTION_RE.search(markdown):
        return _SECTION_RE.sub(lambda _: f"{_RELATED_HEADING}\n{block_body}", markdown, count=1)

    new_section = f"{_RELATED_HEADING}\n\n{body}\n\n"
    references = section("References")
    if references in markdown:
        return markdown.replace(references, f"{new_section}{references}", 1)
    return f"{markdown.rstrip()}\n\n{new_section}".rstrip() + "\n"
