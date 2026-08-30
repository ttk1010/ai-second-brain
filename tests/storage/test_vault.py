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


def test_short_title_drives_filename(tmp_path: Path) -> None:
    ko = KnowledgeObject(
        source=Source(type=SourceType.NEWS, value="https://ledge.ai/x"),
        title="Sakana AI、複数AIモデルの集合知を活用する「Sakana Fugu」提供開始",
        short_title="Sakana Fugu",
        summary="A summary.",
    )
    target = VaultWriter(tmp_path).write(ko, "x")
    # Filename uses the concise short_title; the full title stays in the object.
    assert target == tmp_path / "06 News" / "Sakana Fugu.md"
    assert ko.title.startswith("Sakana AI")


def test_falls_back_to_title_without_short_title(tmp_path: Path) -> None:
    target = VaultWriter(tmp_path).write(_ko("Transformer"), "x")
    assert target.name == "Transformer.md"


def test_records_relative_path_in_outputs(tmp_path: Path) -> None:
    ko = _ko()
    VaultWriter(tmp_path).write(ko, "x")
    assert ko.outputs["markdown"] == "01 Concepts/Transformer.md"


def test_find_existing_matches_by_source(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    ko = _ko("Transformer")
    ko.source.value = "Transformer"
    from backend.markdown import MarkdownGenerator

    writer.write(ko, MarkdownGenerator().generate(ko))

    found = writer.find_existing(SourceType.CONCEPT, "Transformer")
    assert found is not None and found.name == "Transformer.md"


def test_find_existing_returns_none_when_absent(tmp_path: Path) -> None:
    assert VaultWriter(tmp_path).find_existing(SourceType.CONCEPT, "Nope") is None


def test_find_existing_is_source_type_scoped(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    ko = _ko("Transformer")
    from backend.markdown import MarkdownGenerator

    writer.write(ko, MarkdownGenerator().generate(ko))
    # Same value but a different source type does not match (different folder).
    assert writer.find_existing(SourceType.NEWS, "Transformer") is None


# --- In-place overwrite: no duplicates, keep the name (Issue #39) -----------


def _existing(writer: VaultWriter, *, source: str, short_title: str) -> Path:
    """Write a note whose frontmatter source is ``source`` under a short_title stem."""
    from backend.markdown import MarkdownGenerator

    ko = KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value=source),
        title=source,
        short_title=short_title,
        summary="A summary.",
    )
    return writer.write(ko, MarkdownGenerator().generate(ko))


def test_pinned_stem_reuses_existing_filename_on_overwrite(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    _existing(writer, source="uv, Poetry", short_title="Old Name")

    ko = KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="uv, Poetry"),
        title="uv, Poetry",
        short_title="A Better New Name",  # a "improved" title on regeneration
        summary="A summary.",
    )
    assert writer.pinned_stem(ko, overwrite=True) == "Old Name"


def test_pinned_stem_is_none_without_overwrite(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    _existing(writer, source="uv, Poetry", short_title="Old Name")
    ko = KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="uv, Poetry"),
        title="uv, Poetry",
        summary="A summary.",
    )
    assert writer.pinned_stem(ko, overwrite=False) is None


def test_pinned_stem_is_none_when_no_existing_note(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    ko = _ko("Brand New")
    assert writer.pinned_stem(ko, overwrite=True) is None


def test_pinned_stem_logs_title_drift(tmp_path: Path, caplog) -> None:
    import logging

    writer = VaultWriter(tmp_path)
    _existing(writer, source="uv, Poetry", short_title="Old Name")
    ko = KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="uv, Poetry"),
        title="uv, Poetry",
        short_title="A Better New Name",
        summary="A summary.",
    )
    with caplog.at_level(logging.INFO):
        writer.pinned_stem(ko, overwrite=True)
    assert any("Keeping existing filename" in r.message for r in caplog.records)


def test_write_with_pinned_stem_replaces_in_place(tmp_path: Path) -> None:
    writer = VaultWriter(tmp_path)
    _existing(writer, source="uv, Poetry", short_title="Old Name")

    ko = KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="uv, Poetry"),
        title="uv, Poetry",
        short_title="A Better New Name",
        summary="Updated.",
    )
    stem = writer.pinned_stem(ko, overwrite=True)
    target = writer.write(ko, "# updated\n", overwrite=True, stem=stem)

    folder = tmp_path / "01 Concepts"
    # Exactly one note remains, under the original filename; no duplicate created.
    assert target.name == "Old Name.md"
    assert sorted(p.name for p in folder.glob("*.md")) == ["Old Name.md"]


def test_find_existing_warns_on_duplicates(tmp_path: Path, caplog) -> None:
    import logging

    writer = VaultWriter(tmp_path)
    # Two notes sharing the same source (a Vault duplicated before this fix).
    _existing(writer, source="uv, Poetry", short_title="Name A")
    _existing(writer, source="uv, Poetry", short_title="Name B")

    with caplog.at_level(logging.WARNING):
        found = writer.find_existing(SourceType.CONCEPT, "uv, Poetry")
    assert found is not None
    assert any("Multiple notes share source" in r.message for r in caplog.records)


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
