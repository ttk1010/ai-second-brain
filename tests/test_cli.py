"""Tests for the CLI entry point (Issue #10), with the pipeline boundary mocked."""

import json
from pathlib import Path

import pytest

from backend import cli

RESPONSE = json.dumps({"title": "Transformer", "summary": "A summary."})


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    v.mkdir()
    return v


def _write_config(tmp_path: Path, vault: Path) -> Path:
    cfg = tmp_path / "settings.toml"
    cfg.write_text(f'vault_path = "{vault}"\nauto_commit = false\n', encoding="utf-8")
    return cfg


def test_cli_creates_note(tmp_path: Path, vault: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "OpenAIProvider", lambda model: _MockProvider())
    cfg = _write_config(tmp_path, vault)

    code = cli.main(["Transformer", "--config", str(cfg)])

    assert code == 0
    assert (vault / "01 Concepts" / "Transformer.md").exists()
    assert "Created note" in capsys.readouterr().out


def test_cli_reports_unsupported_url(tmp_path: Path, vault: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "OpenAIProvider", lambda model: _MockProvider())
    cfg = _write_config(tmp_path, vault)

    code = cli.main(["https://openai.com/news/", "--config", str(cfg)])

    assert code == 0
    assert "Phase 2" in capsys.readouterr().out


def test_cli_bad_config_returns_2(tmp_path: Path, capsys) -> None:
    code = cli.main(["Transformer", "--config", str(tmp_path / "missing.toml")])
    assert code == 2
    assert "Configuration error" in capsys.readouterr().err


class _MockProvider:
    def complete(self, system: str, user: str, *, response_format: str = "text") -> str:
        return RESPONSE
