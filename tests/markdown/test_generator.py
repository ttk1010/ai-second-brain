"""Tests for the Markdown Generator (Issue #8 / GH #7)."""

from datetime import date

import pytest

from backend.markdown import MarkdownGenerator
from backend.models import (
    KnowledgeObject,
    Metadata,
    Relationship,
    RelationshipType,
    Source,
    SourceType,
)

FIXED_DATE = date(2026, 6, 26)


def _full_ko() -> KnowledgeObject:
    return KnowledgeObject(
        id="abc123",
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture based on self-attention.",
        concepts=["attention", "self-attention"],
        relationships=[Relationship(type=RelationshipType.PREREQUISITE, target="RNN")],
        references=["https://arxiv.org/abs/1706.03762"],
        metadata=Metadata(tags=["nlp"], language="ja"),
    )


def _minimal_ko() -> KnowledgeObject:
    return KnowledgeObject(
        id="min1",
        source=Source(type=SourceType.CONCEPT, value="MCP"),
        title="MCP",
        summary="A protocol for connecting tools to models.",
    )


def test_generates_all_sections() -> None:
    md = MarkdownGenerator().generate(_full_ko(), created=FIXED_DATE)
    for header in (
        "# Transformer",
        "## Summary",
        "## Illustration",
        "## Background",
        "## Key Takeaways",
        "## Related Notes",
        "## References",
        "## Tags",
    ):
        assert header in md


def test_frontmatter_is_parseable_yaml() -> None:
    md = MarkdownGenerator().generate(_full_ko(), created=FIXED_DATE)
    assert md.startswith("---\n")
    frontmatter = md.split("---\n")[1]
    assert "id: abc123" in frontmatter
    assert 'title: "Transformer"' in frontmatter
    assert "created: 2026-06-26" in frontmatter
    assert "language: ja" in frontmatter


def test_related_notes_use_wikilinks() -> None:
    md = MarkdownGenerator().generate(_full_ko(), created=FIXED_DATE)
    assert "[[attention]]" in md
    assert "[[RNN]]" in md  # from the relationship target


def test_references_are_listed() -> None:
    md = MarkdownGenerator().generate(_full_ko(), created=FIXED_DATE)
    assert "- https://arxiv.org/abs/1706.03762" in md


def test_output_is_deterministic() -> None:
    gen = MarkdownGenerator()
    a = gen.generate(_full_ko(), created=FIXED_DATE)
    b = gen.generate(_full_ko(), created=FIXED_DATE)
    assert a == b


def test_missing_data_renders_placeholders() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    # No concepts/relationships/references -> placeholders, not crashes.
    assert "_(To be generated)_" in md
    assert "## Related Notes\n\n> _(To be generated)_" in md
    assert "## References\n\n> _(To be generated)_" in md


def test_illustration_placeholder_when_absent() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    assert "## Illustration\n\n> _(No illustration available.)_" in md


def test_illustration_embedded_when_present() -> None:
    ko = _minimal_ko()
    ko.outputs = {"illustration": "Images/MCP.png"}
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)
    assert "## Illustration\n\n![[Images/MCP.png]]" in md


def test_background_and_takeaways_placeholder_when_absent() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    assert "## Background\n\n> _(To be generated)_" in md
    assert "## Key Takeaways\n\n> _(To be generated)_" in md


def test_comparison_table_rendered_when_present() -> None:
    from backend.models import ComparisonData, ComparisonRow

    ko = _minimal_ko()
    ko.comparison = ComparisonData(
        items=["GPT", "Claude"],
        rows=[
            ComparisonRow(dimension="context", cells=["400K", "500K"]),
            ComparisonRow(dimension="strength", cells=["general", "code"]),
        ],
        recommendation="Use Claude for code.",
    )
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)

    assert "## Comparison" in md
    assert "| 観点 | GPT | Claude |" in md
    assert "| context | 400K | 500K |" in md
    assert "| strength | general | code |" in md
    assert "Use Claude for code." in md


def test_no_comparison_section_for_normal_notes() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    assert "## Comparison" not in md


def test_background_and_takeaways_rendered_when_present() -> None:
    ko = _minimal_ko()
    ko.background = "MCP standardizes how tools connect to models."
    ko.key_takeaways = ["Open protocol", "Reduces integration glue"]
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)

    assert "## Background\n\nMCP standardizes how tools connect to models." in md
    assert "## Key Takeaways\n\n- Open protocol\n- Reduces integration glue" in md


def test_tags_combine_metadata_and_concepts() -> None:
    md = MarkdownGenerator().generate(_full_ko(), created=FIXED_DATE)
    tags_section = md.split("## Tags")[1]
    assert "#nlp" in tags_section
    assert "#self-attention" in tags_section


def test_defaults_created_to_today() -> None:
    md = MarkdownGenerator().generate(_minimal_ko())
    assert f"created: {date.today().isoformat()}" in md


def test_yaml_escapes_quotes_in_title() -> None:
    ko = _minimal_ko()
    ko.title = 'The "Attention" Paper'
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)
    assert r'title: "The \"Attention\" Paper"' in md


@pytest.mark.parametrize("ko_factory", [_full_ko, _minimal_ko])
def test_note_ends_with_single_newline(ko_factory) -> None:
    md = MarkdownGenerator().generate(ko_factory(), created=FIXED_DATE)
    assert md.endswith("\n")
    assert not md.endswith("\n\n")


def test_published_date_in_frontmatter_and_body_when_present() -> None:
    ko = _minimal_ko()
    ko.metadata.published_date = date(2026, 7, 4)
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)

    assert "published_date: 2026-07-04" in md
    # A visible line sits directly under the title, above the summary.
    assert "# MCP\n\n📅 2026-07-04\n\n## Summary" in md


def test_no_published_date_when_absent() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    assert "published_date:" not in md
    assert "📅" not in md


def test_domain_in_frontmatter_and_tags_when_present() -> None:
    ko = _full_ko()
    ko.metadata.domain = "生物学"
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)

    assert 'domain: "生物学"' in md
    # The domain also becomes the leading tag, in frontmatter and the Tags section.
    assert "  - 生物学" in md
    assert "#生物学" in md.split("## Tags")[1]


def test_no_domain_line_when_absent() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    assert "domain:" not in md


def test_guidance_in_frontmatter_when_present() -> None:
    ko = _minimal_ko()
    ko.metadata.guidance = "高校生向けに"
    md = MarkdownGenerator().generate(ko, created=FIXED_DATE)

    assert 'guidance: "高校生向けに"' in md
    # Guidance is provenance, not a tag.
    assert "#高校生向けに" not in md


def test_no_guidance_line_when_absent() -> None:
    md = MarkdownGenerator().generate(_minimal_ko(), created=FIXED_DATE)
    assert "guidance:" not in md
