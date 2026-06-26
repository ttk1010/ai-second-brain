"""Tests for the Vault storage layer (Issue #9 / GH #8)."""

from pathlib import Path

import pytest

from backend.models import KnowledgeObject, Source, SourceType
from backend.storage import VaultWriter
from backend.storage.paths import slugify_title


def _ko(
    title: str = "Transformer",
    source_type: SourceType = SourceType.CONCEPT,
) -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=source_type, value=title),
        title=title,
        summary="A summary.",
    )


def test_writes_concept_to_concepts_folder(tmp_path: Path) -> None:
    target = VaultWriter(tmp_path).write(_ko(), "# Transformer\n")
    assert target == tmp_path / "01 Concepts" / "Transformer.md"
    assert target.read_text(encoding="utf-8") == "# Transformer\n"


@pytest.mark.parametrize(
    ("source_type", "folder"),
    [
        (SourceType.CONCEPT, "01 Concepts"),
        (SourceType.NEWS, "06 News"),
        (SourceType.PAPER, "07 Papers"),
        (SourceType.DOCUMENTATION, "00 Inbox"),
        (SourceType.UNKNOWN, "00 Inbox"),
    ],
)
def test_routes_by_source_type(tmp_path: Path, source_type: SourceType, folder: str) -> None:
    target = VaultWriter(tmp_path).write(_ko("X", source_type), "x")
    assert target.parent == tmp_path / folder


def test_creates_missing_folders(tmp_path: Path) -> None:
    VaultWriter(tmp_path).write(_ko(), "x")
    assert (tmp_path / "01 Concepts").is_dir()


def test_collision_appends_suffix(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    first = writer.write(_ko(), "first")
    second = writer.write(_ko(), "second")
    assert first.name == "Transformer.md"
    assert second.name == "Transformer-2.md"
    assert first.read_text(encoding="utf-8") == "first"
    assert second.read_text(encoding="utf-8") == "second"


def test_overwrite_replaces_existing(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    writer.write(_ko(), "first")
    again = writer.write(_ko(), "second", overwrite=True)
    assert again.name == "Transformer.md"
    assert again.read_text(encoding="utf-8") == "second"


def test_records_relative_path_in_outputs(tmp_path: Path) -> None:
    ko = _ko()
    VaultWriter(tmp_path).write(ko, "x")
    assert ko.outputs["markdown"] == "01 Concepts/Transformer.md"


def test_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Vault path does not exist"):
        VaultWriter(tmp_path / "nope").write(_ko(), "x")


def test_japanese_title_is_preserved(tmp_path: Path) -> None:
    target = VaultWriter(tmp_path).write(_ko("自己注意機構"), "x")
    assert target.name == "自己注意機構.md"


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("A/B Testing", "A-B Testing"),
        ("What is MCP?", "What is MCP"),
        ('The "Attention" paper', "The -Attention- paper"),
        ("   ", "untitled"),
    ],
)
def test_slugify_sanitizes(title: str, expected: str) -> None:
    assert slugify_title(title) == expected
