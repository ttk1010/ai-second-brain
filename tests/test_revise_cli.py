"""Tests for the ``asb-revise`` CLI (Issue #29), pipeline boundary mocked."""

import json
from pathlib import Path

import pytest

from backend.revise import cli

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

## Background

2017年に登場。

## Illustration

![[Images/Transformer.png]]
"""


class _MockLLM:
    def __init__(self, target: str = "summary", rewrite: str = "やさしい要約。") -> None:
        self.target = target
        self.rewrite = rewrite

    def complete(self, system: str, user: str, *, response_format: str = "text") -> str:
        if response_format == "json":
            return json.dumps({"target": self.target})
        return self.rewrite


class _MockImageProvider:
    def generate(
        self, prompt, *, aspect_ratio, quality, output_path, reference_images=None
    ) -> Path:
        output_path.write_bytes(b"revised")
        return output_path


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    (v / "01 Concepts").mkdir(parents=True)
    (v / "01 Concepts" / "Transformer.md").write_text(NOTE, encoding="utf-8")
    (v / "Images").mkdir()
    (v / "Images" / "Transformer.png").write_bytes(b"original")
    return v


def _cfg(tmp_path: Path, vault: Path) -> Path:
    cfg = tmp_path / "settings.toml"
    cfg.write_text(f'vault_path = "{vault}"\nauto_commit = false\n', encoding="utf-8")
    return cfg


def _patch(monkeypatch, *, target: str = "summary") -> None:
    from backend.services import factory

    monkeypatch.setattr(factory, "OpenAIProvider", lambda model: _MockLLM(target=target))
    monkeypatch.setattr(factory, "OpenAIImageProvider", lambda model: _MockImageProvider())


def test_revise_section(tmp_path: Path, vault: Path, monkeypatch, capsys) -> None:
    _patch(monkeypatch)
    code = cli.main(["Transformer", "要約をやさしく", "--config", str(_cfg(tmp_path, vault))])
    assert code == 0
    content = (vault / "01 Concepts" / "Transformer.md").read_text(encoding="utf-8")
    assert "やさしい要約。" in content
    assert "Revised Summary" in capsys.readouterr().out


def test_revise_illustration(tmp_path: Path, vault: Path, monkeypatch, capsys) -> None:
    _patch(monkeypatch)
    code = cli.main(
        ["Transformer", "白背景で", "--illustration", "--config", str(_cfg(tmp_path, vault))]
    )
    assert code == 0
    assert (vault / "Images" / "Transformer.png").read_bytes() == b"revised"


def test_revise_not_found_reports(tmp_path: Path, vault: Path, monkeypatch, capsys) -> None:
    _patch(monkeypatch)
    code = cli.main(["Missing", "直して", "--config", str(_cfg(tmp_path, vault))])
    assert code == 0
    assert "No note found" in capsys.readouterr().out


def test_section_and_illustration_are_mutually_exclusive(
    tmp_path: Path, vault: Path, monkeypatch
) -> None:
    _patch(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(
            [
                "Transformer",
                "x",
                "--section",
                "summary",
                "--illustration",
                "--config",
                str(_cfg(tmp_path, vault)),
            ]
        )
