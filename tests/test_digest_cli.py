"""Tests for the ``asb-digest`` CLI (Issue #39), with providers/ranking mocked."""

import json
from pathlib import Path

from backend.digest import cli
from backend.parser import RankedArticle, RankingFetcher

DIGEST_RESPONSE = json.dumps(
    {
        "overview": "今月の概観。",
        "items": [{"rank": 1, "summary": "要約1。"}, {"rank": 2, "summary": "要約2。"}],
        "concepts": ["AIエージェント"],
        "entities": ["OpenAI"],
    }
)


class _MockProvider:
    def complete(self, system: str, user: str, *, response_format: str = "text") -> str:
        return DIGEST_RESPONSE


class _FakeRanking(RankingFetcher):
    def fetch_monthly(self, *, limit: int = 10) -> list[RankedArticle]:
        return [
            RankedArticle(
                rank=i + 1, title=f"見出し{i + 1}", url=f"https://ledge.ai/articles/a{i + 1}"
            )
            for i in range(min(2, limit))
        ]


def _patch(monkeypatch) -> None:
    from backend.services import factory

    monkeypatch.setattr(factory, "OpenAIProvider", lambda model: _MockProvider())
    monkeypatch.setattr(factory, "LedgeAiRankingFetcher", lambda: _FakeRanking())


def _config(tmp_path: Path, vault: Path) -> Path:
    cfg = tmp_path / "settings.toml"
    cfg.write_text(f'vault_path = "{vault}"\nauto_commit = false\n', encoding="utf-8")
    return cfg


def test_digest_cli_creates_note(tmp_path: Path, monkeypatch, capsys) -> None:
    _patch(monkeypatch)
    vault = tmp_path / "vault"
    vault.mkdir()
    cfg = _config(tmp_path, vault)

    code = cli.main(["--month", "2026-08", "--top", "2", "--no-image", "--config", str(cfg)])

    assert code == 0
    note = vault / "08 Digests" / "2026-08 AIニュースTOP2.md"
    assert note.exists()
    assert "## Top Stories" in note.read_text(encoding="utf-8")
    assert "Created note" in capsys.readouterr().out


def test_digest_cli_defaults_month_to_today(tmp_path: Path, monkeypatch, capsys) -> None:
    from datetime import date

    _patch(monkeypatch)
    vault = tmp_path / "vault"
    vault.mkdir()
    cfg = _config(tmp_path, vault)

    code = cli.main(["--top", "2", "--no-image", "--config", str(cfg)])

    assert code == 0
    period = date.today().strftime("%Y-%m")
    assert (vault / "08 Digests" / f"{period} AIニュースTOP2.md").exists()
