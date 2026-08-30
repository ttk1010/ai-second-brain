"""Tests for section-scoped Markdown read/replace (Issue #29)."""

import pytest

from backend.markdown import (
    extract_section,
    first_embedded_image,
    replace_section,
)

NOTE = """\
---
title: Transformer
---

# Transformer

## Summary

An architecture based on self-attention.

## Illustration

![[Images/Transformer.png]]

## Background

Introduced in 2017.

## Key Takeaways

- Attention weighs tokens
- Parallelizable

## Tags

#ai
"""


def test_extract_section_returns_trimmed_body() -> None:
    assert extract_section(NOTE, "Summary") == "An architecture based on self-attention."


def test_extract_section_handles_list_body() -> None:
    body = extract_section(NOTE, "Key Takeaways")
    assert body == "- Attention weighs tokens\n- Parallelizable"


def test_extract_section_absent_returns_none() -> None:
    assert extract_section(NOTE, "References") is None


def test_replace_section_only_changes_target() -> None:
    updated = replace_section(NOTE, "Summary", "A much simpler explanation.")
    assert "A much simpler explanation." in updated
    assert extract_section(updated, "Summary") == "A much simpler explanation."
    # Neighboring sections are untouched.
    assert extract_section(updated, "Background") == "Introduced in 2017."
    assert "![[Images/Transformer.png]]" in updated


def test_replace_section_missing_raises() -> None:
    with pytest.raises(KeyError):
        replace_section(NOTE, "References", "x")


def test_first_embedded_image_returns_path() -> None:
    assert first_embedded_image(NOTE) == "Images/Transformer.png"


def test_first_embedded_image_none_when_absent() -> None:
    assert first_embedded_image("# Note\n\nNo image here.") is None
