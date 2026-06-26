"""Markdown note template.

The standard note structure (CLAUDE.md, ARCHITECTURE.md). Kept separate from the
generator so the template can evolve without touching generation logic. Markdown
must stay valuable without AI tools (Markdown Rules).

Sections whose content is not yet produced in Phase 1 (Background, Key Takeaways,
Illustration) render a placeholder so the note structure stays stable while later
issues fill them in.
"""

PLACEHOLDER = "> _(To be generated)_"
ILLUSTRATION_PLACEHOLDER = "> _(Illustration will be generated in Phase 2.)_"

SECTION_ORDER = (
    "Summary",
    "Illustration",
    "Background",
    "Key Takeaways",
    "Related Notes",
    "References",
    "Tags",
)


def heading(title: str) -> str:
    return f"# {title}"


def section(name: str) -> str:
    return f"## {name}"
