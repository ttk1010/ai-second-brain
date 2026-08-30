"""Tests for the CLI entry point (Issue #10), with the pipeline boundary mocked."""

import json
from pathlib import Path

import pytest

from backend import cli

# Superset response: satisfies the concept extractor and the comparison extractor
# (which also needs "items"), so one mock works for both CLI paths.
RESPONSE = json.dumps(
    {
        "title": "Transformer",
        "short_title": "Transformer",
        "summary": "A summary.",
        "items": ["GPT", "Claude"],
        "rows": [{"dimension": "strength", "cells": ["general", "code"]}],
    }
)


class _MockImageProvider:
    def generate(
        self, prompt, *, aspect_ratio, quality, output_path, reference_images=None
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"image-bytes")
        return output_path


def _patch_providers(monkeypatch) -> None:
    """Replace the network-backed providers (built in the factory) so the CLI runs offline."""
    from backend.services import factory

    monkeypatch.setattr(factory, "OpenAIProvider", lambda model: _MockProvider())
    monkeypatch.setattr(factory, "OpenAIImageProvider", lambda model: _MockImageProvider())


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


def test_cli_compare_creates_comparison_note(
    tmp_path: Path, vault: Path, monkeypatch, capsys
) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    code = cli.main(["GPT, Claude", "--compare", "--no-image", "--config", str(cfg)])

    assert code == 0
    # --compare routes to the Comparison pipeline -> 04 Comparisons.
    assert list((vault / "04 Comparisons").glob("*.md"))
    content = next((vault / "04 Comparisons").glob("*.md")).read_text(encoding="utf-8")
    assert "## Comparison" in content


def test_cli_pages_generates_multipage_series(
    tmp_path: Path, vault: Path, monkeypatch, capsys
) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    code = cli.main(["Transformer", "--pages", "3", "--config", str(cfg)])

    assert code == 0
    images = sorted(p.name for p in (vault / "Images").glob("*.png"))
    assert images == ["Transformer-p2.png", "Transformer-p3.png", "Transformer.png"]
    note = (vault / "01 Concepts" / "Transformer.md").read_text(encoding="utf-8")
    assert "![[Images/Transformer-p2.png]]" in note


def test_cli_pages_with_no_image_creates_no_images(
    tmp_path: Path, vault: Path, monkeypatch, capsys
) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    # --no-image wins over --pages: no illustrations at all.
    code = cli.main(["Transformer", "--pages", "3", "--no-image", "--config", str(cfg)])

    assert code == 0
    assert not (vault / "Images").exists()


def test_cli_rejects_invalid_pages(tmp_path: Path, vault: Path, monkeypatch) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    with pytest.raises(SystemExit):
        cli.main(["Transformer", "--pages", "0", "--config", str(cfg)])


def test_cli_no_image_skips_illustration(tmp_path: Path, vault: Path, monkeypatch, capsys) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    code = cli.main(["Transformer", "--no-image", "--config", str(cfg)])

    assert code == 0
    assert (vault / "01 Concepts" / "Transformer.md").exists()
    # No illustration is generated.
    assert not (vault / "Images").exists()


def test_cli_guidance_is_recorded_in_the_note(
    tmp_path: Path, vault: Path, monkeypatch, capsys
) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)

    code = cli.main(
        ["Transformer", "--guidance", "高校生向けに", "--no-image", "--config", str(cfg)]
    )

    assert code == 0
    note = (vault / "01 Concepts" / "Transformer.md").read_text(encoding="utf-8")
    assert 'guidance: "高校生向けに"' in note


def test_cli_captured_from_creates_news_note(
    tmp_path: Path, vault: Path, monkeypatch, capsys
) -> None:
    _patch_providers(monkeypatch)
    cfg = _write_config(tmp_path, vault)
    body = tmp_path / "article.txt"
    body.write_text("ログイン必須サイトの記事本文。", encoding="utf-8")

    code = cli.main(
        [
            "--captured-from",
            "https://atmarkit.itmedia.co.jp/ait/articles/x.html",
            "--text-file",
            str(body),
            "--no-image",
            "--config",
            str(cfg),
        ]
    )

    assert code == 0
    assert (vault / "06 News" / "Transformer.md").exists()
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
        # The planner has its own schema; return a valid plan (with pages when a
        # multi-page series was requested) so the CLI --pages path is exercised.
        if "educational planner" in system.lower():
            plan = {
                "learning_objective": "Understand it.",
                "target_audience": "Engineers.",
                "visualization": {"aspect_ratio": "16:9"},
            }
            if "sequential illustration pages" in user:
                plan["pages"] = [
                    {
                        "title": f"Page {i}",
                        "learning_objective": f"Teach part {i}.",
                        "aspect_ratio": "16:9",
                    }
                    for i in range(1, 4)
                ]
            return json.dumps(plan)
        return RESPONSE
