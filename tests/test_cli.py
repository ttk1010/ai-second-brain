"""Tests for the CLI entry point (Issue #10), with the pipeline boundary mocked."""

import json
from pathlib import Path

import pytest

from backend import cli

RESPONSE = json.dumps({"title": "Transformer", "summary": "A summary."})


class _MockImageProvider:
    def generate(self, prompt, *, aspect_ratio, quality, output_path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"image-bytes")
        return output_path


def _patch_providers(monkeypatch) -> None:
    """Replace the network-backed providers so the CLI runs offline."""
    monkeypatch.setattr(cli, "OpenAIProvider", lambda model: _MockProvider())
    monkeypatch.setattr(cli, "OpenAIImageProvider", lambda model: _MockImageProvider())


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
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    code = cli.main(["Transformer", "--config", str(cfg)])

    assert code == 0
    assert (vault / "01 Concepts" / "Transformer.md").exists()
    assert (vault / "Images" / "Transformer.png").exists()
    assert "Created note" in capsys.readouterr().out


def test_cli_reports_unsupported_for_malformed_url(
    tmp_path: Path, vault: Path, monkeypatch, capsys
) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    # A malformed URL classifies as UNKNOWN, so it is reported without fetching.
    code = cli.main(["http://", "--config", str(cfg)])

    assert code == 0
    assert "Could not process input" in capsys.readouterr().out


def test_cli_bad_config_returns_2(tmp_path: Path, capsys) -> None:
    code = cli.main(["Transformer", "--config", str(tmp_path / "missing.toml")])
    assert code == 2
    assert "Configuration error" in capsys.readouterr().err


class _MockProvider:
    def complete(self, system: str, user: str, *, response_format: str = "text") -> str:
        return RESPONSE
