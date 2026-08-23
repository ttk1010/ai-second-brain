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


class _FakeArticleFetcher:
    def fetch(self, url: str):
        from backend.parser.fetcher import FetchedArticle

        return FetchedArticle(url=url, title="t", text=f"本文テキスト for {url}")


def test_fetch_prints_ranking_with_bodies(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "LedgeAiRankingFetcher", lambda: _FakeRanking())
    monkeypatch.setattr(cli, "HttpArticleFetcher", lambda: _FakeArticleFetcher())

    code = cli.main(["fetch", "--top", "2"])

    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["top"] == 2
    assert len(out["articles"]) == 2
    assert out["articles"][0]["url"].endswith("a1")
    assert out["articles"][0]["body"].startswith("本文テキスト")


def test_build_from_authored_json_uses_labels(tmp_path: Path, monkeypatch, capsys) -> None:
    _patch(monkeypatch)
    vault = tmp_path / "vault"
    vault.mkdir()
    cfg = _config(tmp_path, vault)
    authored = {
        "period": "2026-08",
        "overview": "概観。",
        "concepts": ["AIエージェント"],
        "entities": ["OpenAI"],
        "items": [
            {
                "rank": 1,
                "title": "見出し1",
                "url": "https://ledge.ai/articles/a1",
                "label": "ヤコビアン予想に反例",
                "summary": "要約1。",
            }
        ],
    }
    src = tmp_path / "digest.json"
    src.write_text(json.dumps(authored, ensure_ascii=False), encoding="utf-8")

    code = cli.main(["build", "--from", str(src), "--no-image", "--config", str(cfg)])

    assert code == 0
    note = vault / "08 Digests" / "2026-08 AIニュースTOP1.md"
    assert note.exists()
    content = note.read_text(encoding="utf-8")
    assert "[見出し1](https://ledge.ai/articles/a1) — 要約1。" in content
    # The label is for the illustration tile, not the note body.
    assert "ヤコビアン予想に反例" not in content
