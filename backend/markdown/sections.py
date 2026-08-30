"""Read and safely replace a single section of a note's Markdown (Issue #29).

Revision must touch only the targeted section so the rest of the note
(frontmatter, other sections, illustration embed) is never disturbed. This
generalizes the section-scoped write pattern from ``linker/related.py`` so the
note reviser can update ``## Summary`` / ``## Background`` / ``## Key Takeaways``
in place, reading the current text back from the Markdown (KO is not persisted,
ADR 0005).
"""

import re

from backend.markdown.template import section

# The body sections a natural-language revision may rewrite. Structural sections
# (Illustration, Related Notes, References, Tags) are managed elsewhere.
EDITABLE_SECTIONS: dict[str, str] = {
    "summary": "Summary",
    "background": "Background",
    "key_takeaways": "Key Takeaways",
}


def _section_re(name: str) -> re.Pattern[str]:
    heading = section(name)
    # Body from just after the heading up to the next "## " heading or EOF.
    return re.compile(
        rf"^{re.escape(heading)}[ \t]*\n(.*?)(?=^## |\Z)",
        re.DOTALL | re.MULTILINE,
    )


def extract_section(markdown: str, name: str) -> str | None:
    """Return the trimmed body of the ``## name`` section, or None when absent."""
    match = _section_re(name).search(markdown)
    return match.group(1).strip() if match else None


def replace_section(markdown: str, name: str, new_body: str) -> str:
    """Return ``markdown`` with the ``## name`` section body set to ``new_body``.

    Only that section changes. Raises ``KeyError`` when the section is absent, so
    a revision never silently writes to the wrong place.
    """
    heading = section(name)
    regex = _section_re(name)
    if not regex.search(markdown):
        raise KeyError(name)
    replacement = f"{heading}\n\n{new_body.strip()}\n\n"
    return regex.sub(lambda _: replacement, markdown, count=1)


def first_embedded_image(markdown: str) -> str | None:
    """Return the first Obsidian image embed target (``![[path]]``), or None.

    Used to locate the note's illustration for in-place regeneration (Issue #29).
    """
    match = re.search(r"!\[\[([^\]]+?\.(?:png|jpg|jpeg|webp))\]\]", markdown, re.IGNORECASE)
    return match.group(1).strip() if match else None
