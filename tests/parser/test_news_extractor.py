"""Tests for the News Extractor (Issue #15), with a fake fetcher and mock LLM."""

import json

import pytest

from backend.llm.base import LLMError
from backend.parser import NewsExtractor
from backend.parser.fetcher import ArticleFetcher, FetchedArticle, FetchError
from backend.parser.news_extractor import NewsExtraction
from tests.conftest import MockLLMProvider

ARTICLE = FetchedArticle(
    url="https://example.com/news",
    title="OpenAI ships GPT",
    text="OpenAI announced a new model today. It improves reasoning.",
)

VALID_RESPONSE = json.dumps(
    {
        "title": "OpenAI ships a new model",
        "short_title": "GPT-5.6",
        "published_date": "2026-07-04",
        "summary": "OpenAI released a model that improves reasoning.",
        "concepts": ["reasoning", "large language models"],
        "entities": ["OpenAI"],
        "references": ["https://example.com/news"],
    }
)


class _FakeFetcher(ArticleFetcher):
    def __init__(
        self, article: FetchedArticle | None = None, error: Exception | None = None
    ) -> None:
        self._article = article
        self._error = error

    def fetch(self, url: str) -> FetchedArticle:
        if self._error is not None:
            raise self._error
        assert self._article is not None
        return self._article


def test_extract_returns_structured_fields() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    extraction = NewsExtractor(provider, _FakeFetcher(ARTICLE)).extract("https://example.com/news")

    assert extraction.title == "OpenAI ships a new model"
    assert "OpenAI" in extraction.entities
    assert "reasoning" in extraction.concepts
    assert extraction.url == "https://example.com/news"
    assert extraction.short_title == "GPT-5.6"
    assert extraction.published_date == "2026-07-04"
    # The extractor requests a JSON response.
    assert provider.calls[0][2] == "json"
    # The article body is included in the prompt.
    assert "improves reasoning" in provider.calls[0][1]


def test_extract_passes_language_directive() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    NewsExtractor(provider, _FakeFetcher(ARTICLE)).extract("u", language="en")
    assert "English" in provider.calls[0][1]


def test_extract_rejects_empty_url() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        NewsExtractor(MockLLMProvider(VALID_RESPONSE), _FakeFetcher(ARTICLE)).extract("  ")


def test_extract_propagates_fetch_errors() -> None:
    extractor = NewsExtractor(
        MockLLMProvider(VALID_RESPONSE), _FakeFetcher(error=FetchError("boom"))
    )
    with pytest.raises(FetchError):
        extractor.extract("https://example.com/news")


def test_extract_rejects_invalid_json() -> None:
    with pytest.raises(LLMError, match="invalid JSON"):
        NewsExtractor(MockLLMProvider("not json"), _FakeFetcher(ARTICLE)).extract("u")


def test_extract_requires_summary() -> None:
    response = json.dumps({"title": "x", "summary": ""})
    with pytest.raises(LLMError, match="title.*summary"):
        NewsExtractor(MockLLMProvider(response), _FakeFetcher(ARTICLE)).extract("u")


def test_extract_falls_back_to_article_title() -> None:
    response = json.dumps({"summary": "A summary of the article."})
    extraction = NewsExtractor(MockLLMProvider(response), _FakeFetcher(ARTICLE)).extract("u")
    assert extraction.title == "OpenAI ships GPT"


def test_extract_always_includes_source_url_in_references() -> None:
    response = json.dumps({"title": "t", "summary": "s", "references": []})
    extraction = NewsExtractor(MockLLMProvider(response), _FakeFetcher(ARTICLE)).extract("u")
    assert "https://example.com/news" in extraction.references


def test_builder_produces_news_knowledge_object() -> None:
    from backend.models import KnowledgeObject, SourceType
    from backend.parser import KnowledgeObjectBuilder

    extraction = NewsExtractor(MockLLMProvider(VALID_RESPONSE), _FakeFetcher(ARTICLE)).extract(
        "https://example.com/news"
    )
    ko = KnowledgeObjectBuilder().from_news(extraction, language="ja")

    assert isinstance(ko, KnowledgeObject)
    assert ko.source.type is SourceType.NEWS
    assert ko.source.value == "https://example.com/news"
    assert ko.title == "OpenAI ships a new model"
    assert "OpenAI" in ko.entities
    assert ko.metadata.language == "ja"


def test_builder_parses_published_date() -> None:
    from datetime import date

    from backend.parser import KnowledgeObjectBuilder

    extraction = NewsExtraction(title="t", summary="s", url="u", published_date="2026-07-04")
    ko = KnowledgeObjectBuilder().from_news(extraction)
    assert ko.metadata.published_date == date(2026, 7, 4)


@pytest.mark.parametrize("value", ["", "   ", "not-a-date", "2026-13-40"])
def test_builder_omits_unparseable_published_date(value: str) -> None:
    from backend.parser import KnowledgeObjectBuilder

    extraction = NewsExtraction(title="t", summary="s", url="u", published_date=value)
    ko = KnowledgeObjectBuilder().from_news(extraction)
    assert ko.metadata.published_date is None
