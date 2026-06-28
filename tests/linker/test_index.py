"""Tests for the Vault index (Issue #22)."""

from pathlib import Path

import pytest

from backend.linker import VaultIndex

NOTE = """\
---
id: abc123
title: "Transformer"
source_type: concept
created: 2026-06-27
tags:
  - attention
  - self-attention
---

# Transformer

## Summary

A neural network architecture.
"""


def _write(vault: Path, relative: str, content: str) -> None:
    path = vault / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_indexes_frontmatter(tmp_path: Path) -> None:
    _write(tmp_path, "01 Concepts/Transformer.md", NOTE)
    index = VaultIndex.build(tmp_path)

    assert len(index.notes) == 1
    record = index.notes[0]
    assert record.title == "Transformer"
    assert record.id == "abc123"
    assert record.source_type == "concept"
    assert record.tags == ["attention", "self-attention"]
    assert record.path == "01 Concepts/Transformer.md"  # vault-relative, posix


def test_build_scans_recursively(tmp_path: Path) -> None:
    _write(tmp_path, "01 Concepts/A.md", NOTE)
    _write(tmp_path, "06 News/B.md", NOTE)
    index = VaultIndex.build(tmp_path)
    assert len(index.notes) == 2


def test_build_tolerates_missing_frontmatter(tmp_path: Path) -> None:
    _write(tmp_path, "freeform.md", "# Hand Written\n\nSome notes.")
    index = VaultIndex.build(tmp_path)
    assert index.notes[0].title == "Hand Written"  # falls back to the heading
    assert index.notes[0].tags == []


def test_title_falls_back_to_filename(tmp_path: Path) -> None:
    _write(tmp_path, "no-heading.md", "just text, no frontmatter, no heading")
    index = VaultIndex.build(tmp_path)
    assert index.notes[0].title == "no-heading"


def test_build_tolerates_malformed_frontmatter(tmp_path: Path) -> None:
    _write(tmp_path, "bad.md", "---\ntitle: : : broken\n  - nope\n---\n# Fallback\n")
    index = VaultIndex.build(tmp_path)
    # Malformed YAML -> empty frontmatter -> heading fallback, no crash.
    assert index.notes[0].title == "Fallback"


def test_to_list_is_serializable(tmp_path: Path) -> None:
    _write(tmp_path, "01 Concepts/Transformer.md", NOTE)
    data = VaultIndex.build(tmp_path).to_list()
    assert data == [
        {
            "title": "Transformer",
            "name": "Transformer",
            "path": "01 Concepts/Transformer.md",
            "tags": ["attention", "self-attention"],
            "source_type": "concept",
            "id": "abc123",
        }
    ]


def test_build_rejects_missing_vault(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        VaultIndex.build(tmp_path / "nope")
