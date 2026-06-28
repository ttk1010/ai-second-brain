"""Read YAML frontmatter from a note's Markdown text.

Shared by the Vault writer (existing-note lookup) and the linker index, so the
frontmatter-parsing rule lives in one place.
"""

import yaml


def parse_frontmatter(text: str) -> dict:
    """Parse the leading YAML frontmatter block, returning {} when absent/invalid."""
    if not text.startswith("---"):
        return {}
    # Frontmatter is the block between the first two '---' fences.
    parts = text.split("\n", 1)
    if len(parts) < 2:
        return {}
    end = parts[1].find("\n---")
    if end == -1:
        return {}
    block = parts[1][:end]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}
