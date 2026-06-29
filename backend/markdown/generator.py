"""Markdown generation from a Knowledge Object.

Consumes only the Knowledge Object — never raw input or presentation data flowing
back into the model (ADR 0001). Output is deterministic: the same Knowledge
Object (and ``created`` date) always yields the same Markdown.
"""

from datetime import date

from backend.markdown.template import (
    ILLUSTRATION_PLACEHOLDER,
    PLACEHOLDER,
    heading,
    section,
)
from backend.models import KnowledgeObject


class MarkdownGenerator:
    """Renders a Knowledge Object as a standard Markdown note."""

    def generate(self, ko: KnowledgeObject, *, created: date | None = None) -> str:
        """Render ``ko`` as Markdown.

        Args:
            ko: The Knowledge Object to render.
            created: The creation date for the frontmatter. Injectable for
                deterministic output; defaults to today.
        """
        created = created or date.today()
        parts = [
            self._frontmatter(ko, created),
            heading(ko.title),
            self._summary(ko),
            self._illustration(ko),
            self._comparison(ko),
            self._background(ko),
            self._key_takeaways(ko),
            self._related_notes(ko),
            self._references(ko),
            self._tags(ko),
        ]
        # _comparison returns None when the note is not a comparison.
        return "\n\n".join(p for p in parts if p is not None) + "\n"

    def _frontmatter(self, ko: KnowledgeObject, created: date) -> str:
        tags = _unique(ko.metadata.tags + ko.concepts)
        lines = [
            "---",
            f"id: {ko.id}",
            f"title: {_yaml_str(ko.title)}",
            f"source_type: {ko.source.type.value}",
            f"source: {_yaml_str(ko.source.value)}",
            f"created: {created.isoformat()}",
            f"language: {ko.metadata.language}",
        ]
        lines.append("tags:")
        if tags:
            lines.extend(f"  - {tag}" for tag in tags)
        else:
            lines[-1] = "tags: []"
        lines.append("---")
        return "\n".join(lines)

    def _summary(self, ko: KnowledgeObject) -> str:
        return f"{section('Summary')}\n\n{ko.summary}"

    def _illustration(self, ko: KnowledgeObject) -> str:
        path = ko.outputs.get("illustration")
        if not path:
            return f"{section('Illustration')}\n\n{ILLUSTRATION_PLACEHOLDER}"
        # Obsidian embed by Vault-relative path (robust to folder location).
        return f"{section('Illustration')}\n\n![[{path}]]"

    def _comparison(self, ko: KnowledgeObject) -> str | None:
        comp = ko.comparison
        if comp is None or not comp.items:
            return None
        header = "| 観点 | " + " | ".join(_cell(i) for i in comp.items) + " |"
        separator = "| --- | " + " | ".join(["---"] * len(comp.items)) + " |"
        lines = [header, separator]
        for row in comp.rows:
            cells = (row.cells + [""] * len(comp.items))[: len(comp.items)]
            rendered = " | ".join(_cell(c) for c in cells)
            lines.append(f"| {_cell(row.dimension)} | {rendered} |")
        table = "\n".join(lines)
        if comp.recommendation:
            table = f"{table}\n\n{comp.recommendation}"
        return f"{section('Comparison')}\n\n{table}"

    def _background(self, ko: KnowledgeObject) -> str:
        if not ko.background:
            return f"{section('Background')}\n\n{PLACEHOLDER}"
        return f"{section('Background')}\n\n{ko.background}"

    def _key_takeaways(self, ko: KnowledgeObject) -> str:
        takeaways = _unique(ko.key_takeaways)
        if not takeaways:
            return f"{section('Key Takeaways')}\n\n{PLACEHOLDER}"
        items = "\n".join(f"- {item}" for item in takeaways)
        return f"{section('Key Takeaways')}\n\n{items}"

    def _related_notes(self, ko: KnowledgeObject) -> str:
        targets = _unique(ko.concepts + [rel.target for rel in ko.relationships])
        if not targets:
            return f"{section('Related Notes')}\n\n{PLACEHOLDER}"
        links = "\n".join(f"- [[{target}]]" for target in targets)
        return f"{section('Related Notes')}\n\n{links}"

    def _references(self, ko: KnowledgeObject) -> str:
        if not ko.references:
            return f"{section('References')}\n\n{PLACEHOLDER}"
        refs = "\n".join(f"- {ref}" for ref in ko.references)
        return f"{section('References')}\n\n{refs}"

    def _tags(self, ko: KnowledgeObject) -> str:
        tags = _unique(ko.metadata.tags + ko.concepts)
        if not tags:
            return f"{section('Tags')}\n\n{PLACEHOLDER}"
        rendered = " ".join(f"#{tag.replace(' ', '-')}" for tag in tags)
        return f"{section('Tags')}\n\n{rendered}"


def _unique(items: list[str]) -> list[str]:
    """Preserve order while removing duplicates and blanks."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _cell(value: str) -> str:
    """Make a string safe for a Markdown table cell (escape pipes, flatten newlines)."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def _yaml_str(value: str) -> str:
    """Quote a string for safe single-line YAML."""
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
