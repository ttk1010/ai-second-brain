"""Tests for the Input Classifier (Issue #6 / GH #10)."""

import pytest

from backend.models.enums import SourceType
from backend.parser import classify


@pytest.mark.parametrize("concept", ["Transformer", "MCP", "RLHF", "Agentic Commerce"])
def test_keywords_classify_as_concept(concept: str) -> None:
    result = classify(concept)
    assert result.source_type is SourceType.CONCEPT
    assert result.is_url is False
    assert result.normalized_input == concept


@pytest.mark.parametrize(
    "url",
    [
        "https://openai.com/news/",
        "http://ledge.ai/article/123",
        "https://example.com/path?q=1&lang=ja",
        "https://日本語.example.com/記事",
    ],
)
def test_urls_classify_as_news(url: str) -> None:
    result = classify(url)
    assert result.source_type is SourceType.NEWS
    assert result.is_url is True


def test_arxiv_url_is_news_for_now() -> None:
    # Phase 1 routes papers through the News pipeline (ADR 0001).
    result = classify("https://arxiv.org/abs/1706.03762")
    assert result.source_type is SourceType.NEWS


@pytest.mark.parametrize("bad", ["", "   ", "\n\t"])
def test_empty_input_raises(bad: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        classify(bad)


@pytest.mark.parametrize("malformed", ["http://", "https://", "http:// "])
def test_malformed_url_is_unknown(malformed: str) -> None:
    result = classify(malformed)
    assert result.source_type is SourceType.UNKNOWN
    assert result.is_url is False


def test_input_is_normalized() -> None:
    result = classify("  Transformer  ")
    assert result.normalized_input == "Transformer"


def test_url_with_surrounding_whitespace() -> None:
    result = classify("  https://example.com/x  ")
    assert result.source_type is SourceType.NEWS
    assert result.normalized_input == "https://example.com/x"
