"""Tests for the NoteReviser (Issue #29), with mock LLM/image providers."""

import json
from pathlib import Path

import pytest

from backend.image.base import ImageProvider
from backend.models.enums import AspectRatio, ImageQuality
from backend.services import NoteReviser
from backend.storage import VaultWriter

NOTE = """\
---
title: Transformer
source_type: concept
source: "Transformer"
language: ja
---

# Transformer

## Summary

自己注意に基づくアーキテクチャ。

## Illustration

![[Images/Transformer.png]]

## Background

2017年に登場。

## Key Takeaways

- トークンを重み付け

## Tags

#ai
"""


class _MockLLM:
    def __init__(self, *, target: str = "summary", rewrite: str = "もっと易しい説明。") -> None:
        self.target = target
        self.rewrite = rewrite
        self.calls: list[tuple[str, str, str]] = []

    def complete(self, system: str, user: str, *, response_format: str = "text") -> str:
        self.calls.append((system, user, response_format))
        if response_format == "json":
            return json.dumps({"target": self.target})
        return self.rewrite


class _FakeImageProvider(ImageProvider):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(
        self, prompt, *, aspect_ratio, quality, output_path, reference_images=None
    ) -> Path:
        self.calls.append({"prompt": prompt, "output_path": output_path, "refs": reference_images})
        output_path.write_bytes(b"revised-image")
        return output_path


def _vault(tmp_path: Path, *, with_image: bool = True) -> Path:
    (tmp_path / "01 Concepts").mkdir(parents=True)
    (tmp_path / "01 Concepts" / "Transformer.md").write_text(NOTE, encoding="utf-8")
    if with_image:
        (tmp_path / "Images").mkdir()
        (tmp_path / "Images" / "Transformer.png").write_bytes(b"original")
    return tmp_path


def _reviser(vault: Path, *, llm: _MockLLM | None = None, image: _FakeImageProvider | None = None):
    return NoteReviser(
        VaultWriter(vault),
        llm or _MockLLM(),
        vault,
        image_provider=image,
        quality=ImageQuality.MEDIUM,
        default_aspect_ratio=AspectRatio.WIDE,
        language="ja",
    )


def test_revise_section_rewrites_only_that_section(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    llm = _MockLLM(target="summary", rewrite="やさしい要約。")
    result = _reviser(vault, llm=llm).revise("Transformer", "要約をやさしく")

    assert result.status == "revised"
    assert result.target == "summary"
    content = (vault / "01 Concepts" / "Transformer.md").read_text(encoding="utf-8")
    assert "## Summary\n\nやさしい要約。" in content
    # Other sections untouched.
    assert "2017年に登場。" in content
    assert "![[Images/Transformer.png]]" in content


def test_explicit_section_skips_classification(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    llm = _MockLLM(rewrite="厚い背景。")
    result = _reviser(vault, llm=llm).revise("Transformer", "背景を厚く", section="background")

    assert result.status == "revised"
    assert result.target == "background"
    # No JSON classification call was made (section was forced).
    assert all(fmt != "json" for _, _, fmt in llm.calls)
    assert "## Background\n\n厚い背景。" in (vault / "01 Concepts" / "Transformer.md").read_text(
        encoding="utf-8"
    )


def test_revise_illustration_uses_existing_image_as_reference(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    image = _FakeImageProvider()
    result = _reviser(vault, image=image).revise(
        "Transformer", "白背景で描き直して", illustration=True
    )

    assert result.status == "revised"
    assert result.target == "illustration"
    img_path = vault / "Images" / "Transformer.png"
    # The existing image is passed as the reference and overwritten in place.
    assert image.calls[0]["refs"] == [img_path]
    assert image.calls[0]["output_path"] == img_path
    assert img_path.read_bytes() == b"revised-image"


def test_auto_classifies_illustration_target(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    image = _FakeImageProvider()
    llm = _MockLLM(target="illustration")
    result = _reviser(vault, llm=llm, image=image).revise("Transformer", "図を描き直して")
    assert result.status == "revised"
    assert result.target == "illustration"
    assert len(image.calls) == 1


def test_illustration_without_image_provider_is_unsupported(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = _reviser(vault, image=None).revise("Transformer", "描き直して", illustration=True)
    assert result.status == "unsupported"
    assert "image generation" in result.message


def test_not_found_returns_status(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = _reviser(vault).revise("Nonexistent", "要約を直して")
    assert result.status == "not_found"


def test_missing_section_is_unsupported(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    # Force a section the note does not contain.
    result = _reviser(vault).revise("Transformer", "x", section="references")
    assert result.status == "unsupported"


def test_empty_instruction_raises(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with pytest.raises(ValueError):
        _reviser(vault).revise("Transformer", "   ")


def test_find_note_by_title_and_source(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    writer = VaultWriter(vault)
    assert writer.find_note("Transformer") is not None  # by stem/title
    assert writer.find_note("Nope") is None
