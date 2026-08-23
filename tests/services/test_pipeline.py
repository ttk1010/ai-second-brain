"""End-to-end tests for the Knowledge Pipeline (Issue #10 / GH #9)."""

import json
from pathlib import Path

import pytest

from backend.image.base import ImageError, ImageProvider
from backend.markdown import MarkdownGenerator
from backend.models import SourceType
from backend.parser import (
    ComparisonExtractor,
    ConceptExtractor,
    DigestExtractor,
    KnowledgeObjectBuilder,
    NewsExtractor,
    RankedArticle,
    RankingFetcher,
)
from backend.parser.fetcher import ArticleFetcher, FetchedArticle
from backend.planner import EducationalPlanner
from backend.services import KnowledgePipeline
from backend.storage import IllustrationWriter, VaultWriter
from tests.conftest import MockLLMProvider

RESPONSE = json.dumps(
    {
        "title": "Transformer",
        "summary": "A neural network architecture based on self-attention.",
        "concepts": ["attention"],
        "entities": ["Google"],
        "references": ["https://arxiv.org/abs/1706.03762"],
    }
)

PLAN_RESPONSE = json.dumps(
    {
        "learning_objective": "Understand self-attention.",
        "target_audience": "Software engineers.",
        "prerequisites": ["neural networks"],
        "key_messages": ["Attention weighs tokens"],
        "visualization": {"aspect_ratio": "16:9", "description": "Attention diagram."},
    }
)


COMPARISON_RESPONSE = json.dumps(
    {
        "title": "GPT・Claude・Gemini の比較",
        "short_title": "LLM比較",
        "summary": "3モデルを比較する。",
        "items": ["GPT", "Claude", "Gemini"],
        "rows": [{"dimension": "強み", "cells": ["汎用", "コード", "長文"]}],
        "recommendation": "用途で選ぶ。",
    }
)


DIGEST_RESPONSE = json.dumps(
    {
        "overview": "今月はエージェントが話題。",
        "items": [{"rank": 1, "summary": "要約1。"}, {"rank": 2, "summary": "要約2。"}],
        "concepts": ["AIエージェント"],
        "entities": ["OpenAI"],
    }
)


class _FakeRanking(RankingFetcher):
    def __init__(self, count: int = 2) -> None:
        self._count = count

    def fetch_monthly(self, *, limit: int = 10) -> list[RankedArticle]:
        n = min(self._count, limit)
        return [
            RankedArticle(
                rank=i + 1, title=f"見出し{i + 1}", url=f"https://ledge.ai/articles/a{i + 1}"
            )
            for i in range(n)
        ]


class _FakeImageProvider(ImageProvider):
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error

    def generate(self, prompt, *, aspect_ratio, quality, output_path) -> Path:
        if self.error is not None:
            raise self.error
        output_path.write_bytes(b"image-bytes")
        return output_path


class _FakeFetcher(ArticleFetcher):
    def fetch(self, url: str) -> FetchedArticle:
        return FetchedArticle(url=url, title="Article", text="Some article body.")


def _pipeline(
    vault: Path,
    response: str = RESPONSE,
    plan_response: str = PLAN_RESPONSE,
    image_provider: ImageProvider | None = None,
    with_news: bool = False,
    with_comparison: bool = False,
    with_digest: bool = False,
    ranking: "RankingFetcher | None" = None,
) -> KnowledgePipeline:
    illustration_writer = (
        IllustrationWriter(vault, image_provider) if image_provider is not None else None
    )
    news_extractor = NewsExtractor(MockLLMProvider(response), _FakeFetcher()) if with_news else None
    comparison_extractor = (
        ComparisonExtractor(MockLLMProvider(COMPARISON_RESPONSE)) if with_comparison else None
    )
    digest_extractor = DigestExtractor(MockLLMProvider(DIGEST_RESPONSE)) if with_digest else None
    ranking_fetcher = ranking if ranking is not None else (_FakeRanking() if with_digest else None)
    return KnowledgePipeline(
        extractor=ConceptExtractor(MockLLMProvider(response)),
        builder=KnowledgeObjectBuilder(),
        planner=EducationalPlanner(MockLLMProvider(plan_response)),
        markdown_generator=MarkdownGenerator(),
        vault_writer=VaultWriter(vault),
        news_extractor=news_extractor,
        comparison_extractor=comparison_extractor,
        digest_extractor=digest_extractor,
        ranking_fetcher=ranking_fetcher,
        illustration_writer=illustration_writer,
    )


def test_concept_end_to_end(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run("Transformer")

    assert result.status == "created"
    assert result.path == tmp_path / "01 Concepts" / "Transformer.md"
    assert result.path.exists()
    content = result.path.read_text(encoding="utf-8")
    assert "# Transformer" in content
    assert "[[attention]]" in content
    assert result.knowledge_object is not None
    assert result.knowledge_object.outputs["markdown"] == "01 Concepts/Transformer.md"
    # The Educational Plan is attached to the Knowledge Object.
    plan = result.knowledge_object.educational_plan
    assert plan is not None
    assert plan.learning_objective == "Understand self-attention."


def test_guidance_is_recorded_in_metadata_and_frontmatter(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run("Transformer", guidance="高校生向けに")

    assert result.knowledge_object is not None
    assert result.knowledge_object.metadata.guidance == "高校生向けに"
    content = result.path.read_text(encoding="utf-8")
    assert 'guidance: "高校生向けに"' in content


def test_no_guidance_leaves_metadata_none(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run("Transformer")

    assert result.knowledge_object is not None
    assert result.knowledge_object.metadata.guidance is None
    assert "guidance:" not in result.path.read_text(encoding="utf-8")


CAPTURED_URL = "https://atmarkit.itmedia.co.jp/ait/articles/x.html"


def test_run_captured_creates_news_note(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_news=True).run_captured(
        CAPTURED_URL, "ログイン必須記事の本文テキスト。", title="元記事"
    )

    assert result.status == "created"
    assert result.path.parent.name == "06 News"
    assert result.knowledge_object is not None
    # Stored as News with the source URL, so idempotency matches the URL path.
    assert result.knowledge_object.source.value == CAPTURED_URL


def test_run_captured_is_idempotent(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path, with_news=True)
    pipeline.run_captured(CAPTURED_URL, "本文。")
    second = pipeline.run_captured(CAPTURED_URL, "本文。")

    assert second.status == "exists"


def test_run_captured_requires_text(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="text must not be empty"):
        _pipeline(tmp_path, with_news=True).run_captured(CAPTURED_URL, "   ")


def test_run_captured_requires_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source URL is required"):
        _pipeline(tmp_path, with_news=True).run_captured("  ", "body")


def test_run_captured_unsupported_without_news_extractor(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run_captured(CAPTURED_URL, "body")
    assert result.status == "unsupported"


def test_run_digest_creates_digest_note(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_digest=True).run_digest("2026-08", top=2)

    assert result.status == "created"
    assert result.path.parent.name == "08 Digests"
    assert result.path.name == "2026-08 AIニュースTOP2.md"
    content = result.path.read_text(encoding="utf-8")
    assert "## Top Stories" in content
    assert "[見出し1](https://ledge.ai/articles/a1) — 要約1。" in content


def test_run_digest_is_idempotent(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path, with_digest=True)
    pipeline.run_digest("2026-08", top=2)
    assert pipeline.run_digest("2026-08", top=2).status == "exists"


def test_run_digest_requires_period(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="period"):
        _pipeline(tmp_path, with_digest=True).run_digest("  ")


def test_run_digest_unsupported_without_ranking(tmp_path: Path) -> None:
    assert _pipeline(tmp_path).run_digest("2026-08").status == "unsupported"


def test_run_digest_unsupported_when_ranking_empty(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_digest=True, ranking=_FakeRanking(count=0)).run_digest(
        "2026-08"
    )
    assert result.status == "unsupported"


def test_render_digest_builds_from_authored_data(tmp_path: Path) -> None:
    from backend.parser.digest_extractor import DigestExtraction

    ranked = [RankedArticle(rank=1, title="見出し1", url="https://ledge.ai/articles/a1")]
    extraction = DigestExtraction(
        overview="概観。", summaries={1: "要約1。"}, labels={1: "ラベル1"}
    )
    # No ranking fetcher / digest extractor needed — the text is already authored.
    result = _pipeline(tmp_path).render_digest("2026-08", ranked, extraction, top=1)

    assert result.status == "created"
    assert result.path.parent.name == "08 Digests"
    assert result.knowledge_object.digest.items[0].label == "ラベル1"
    assert "要約1。" in result.path.read_text(encoding="utf-8")


def test_render_digest_requires_ranked(tmp_path: Path) -> None:
    from backend.parser.digest_extractor import DigestExtraction

    with pytest.raises(ValueError, match="at least one ranked"):
        _pipeline(tmp_path).render_digest("2026-08", [], DigestExtraction(overview="o"))


def test_illustration_generated_and_embedded(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, image_provider=_FakeImageProvider()).run("Transformer")

    assert result.status == "created"
    image = tmp_path / "Images" / "Transformer.png"
    assert image.exists()
    assert result.knowledge_object is not None
    assert result.knowledge_object.outputs["illustration"] == "Images/Transformer.png"
    # The note embeds the illustration.
    content = result.path.read_text(encoding="utf-8")
    assert "![[Images/Transformer.png]]" in content


def test_illustration_failure_does_not_block_note_creation(tmp_path: Path) -> None:
    provider = _FakeImageProvider(error=ImageError("boom"))
    result = _pipeline(tmp_path, image_provider=provider).run("Transformer")

    assert result.status == "created"
    assert result.path is not None and result.path.exists()
    assert result.knowledge_object is not None
    assert "illustration" not in result.knowledge_object.outputs
    # The note falls back to the placeholder.
    assert "No illustration available" in result.path.read_text(encoding="utf-8")


def test_planning_failure_does_not_block_note_creation(tmp_path: Path) -> None:
    # An unparsable plan response must not prevent the note from being written.
    result = _pipeline(tmp_path, plan_response="not json").run("Transformer")

    assert result.status == "created"
    assert result.path is not None and result.path.exists()
    assert result.knowledge_object is not None
    assert result.knowledge_object.educational_plan is None


def test_url_input_creates_news_note(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_news=True).run("https://openai.com/news/")

    assert result.status == "created"
    assert result.path == tmp_path / "06 News" / "Transformer.md"
    assert result.path.exists()
    assert result.knowledge_object is not None
    assert result.knowledge_object.source.type is SourceType.NEWS
    assert result.knowledge_object.source.value == "https://openai.com/news/"


def test_url_input_unsupported_without_news_extractor(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run("https://openai.com/news/")
    assert result.status == "unsupported"
    # Nothing should be written.
    assert not any(tmp_path.iterdir())


def test_comparison_input_creates_comparison_note(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_comparison=True).run("compare: GPT, Claude, Gemini")

    assert result.status == "created"
    assert result.path == tmp_path / "04 Comparisons" / "LLM比較.md"
    assert result.path.exists()
    assert result.knowledge_object is not None
    assert result.knowledge_object.source.type is SourceType.COMPARISON
    content = result.path.read_text(encoding="utf-8")
    assert "## Comparison" in content
    assert "| 観点 | GPT | Claude | Gemini |" in content


def test_comparison_unsupported_without_extractor(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run("compare: GPT, Claude")
    assert result.status == "unsupported"


def test_malformed_url_is_unsupported(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_news=True).run("http://")
    assert result.status == "unsupported"
    assert not any(tmp_path.iterdir())


def test_empty_input_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        _pipeline(tmp_path).run("   ")


def test_rerun_skips_existing_source(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    first = pipeline.run("Transformer")
    second = pipeline.run("Transformer")

    assert first.status == "created"
    assert second.status == "exists"
    assert second.path == first.path
    # No duplicate note is created.
    assert len(list((tmp_path / "01 Concepts").glob("*.md"))) == 1


def test_overwrite_regenerates_existing(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    pipeline.run("Transformer")
    again = pipeline.run("Transformer", overwrite=True)

    assert again.status == "created"
    assert len(list((tmp_path / "01 Concepts").glob("*.md"))) == 1


def test_overwrite_is_passed_through(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    first = pipeline.run("Transformer")
    second = pipeline.run("Transformer", overwrite=True)
    assert first.path == second.path  # same file, overwritten
