"""Tests for safe Related Notes updates (Issue #22)."""

from backend.linker import RelatedLink, update_related_section

NOTE = """\
---
id: abc123
title: "BERT"
---

# BERT

## Summary

A language model.

## Illustration

![[Images/BERT.png]]

## Related Notes

- [[old-stub]]

## References

- https://example.com

## Tags

#nlp
"""


def test_updates_only_related_section() -> None:
    links = [RelatedLink("Transformer", "prerequisite"), RelatedLink("Attention")]
    result = update_related_section(NOTE, links)

    assert "## Related Notes\n\n- [[Transformer]] — prerequisite\n- [[Attention]]\n\n" in result
    # The old content is gone, neighbours are untouched.
    assert "old-stub" not in result
    assert "## Summary\n\nA language model." in result
    assert "![[Images/BERT.png]]" in result
    assert "## References\n\n- https://example.com" in result
    assert "#nlp" in result


def test_is_idempotent() -> None:
    links = [RelatedLink("Transformer", "prerequisite")]
    once = update_related_section(NOTE, links)
    twice = update_related_section(once, links)
    assert once == twice


def test_empty_links_render_placeholder() -> None:
    result = update_related_section(NOTE, [])
    assert "## Related Notes\n\n> _(To be generated)_\n\n" in result


def test_deduplicates_links() -> None:
    links = [RelatedLink("Transformer"), RelatedLink("Transformer")]
    result = update_related_section(NOTE, links)
    assert result.count("[[Transformer]]") == 1


def test_inserts_section_when_missing() -> None:
    note = "# Hand Written\n\n## References\n\n- https://x.com\n"
    result = update_related_section(note, [RelatedLink("Transformer")])
    assert "## Related Notes\n\n- [[Transformer]]\n\n## References" in result


def test_appends_section_when_no_references() -> None:
    note = "# Hand Written\n\nSome text.\n"
    result = update_related_section(note, [RelatedLink("Transformer")])
    assert "## Related Notes" in result
    assert "- [[Transformer]]" in result


def test_parse_relationship() -> None:
    assert RelatedLink.parse("Transformer:prerequisite") == RelatedLink(
        "Transformer", "prerequisite"
    )
    assert RelatedLink.parse("Attention") == RelatedLink("Attention", None)
