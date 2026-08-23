"""Tests for the Digest Extractor and builder.from_digest (Issue #39)."""

import json

import pytest

from backend.llm.base import LLMError
from backend.models import KnowledgeObject, SourceType
from backend.parser import DigestExtractor, KnowledgeObjectBuilder, RankedArticle
from tests.conftest import MockLLMProvider

RANKED = [
    RankedArticle(rank=1, title="見出し1", url="https://ledge.ai/articles/a1"),
    RankedArticle(rank=2, title="見出し2", url="https://ledge.ai/articles/a2"),
]

VALID_RESPONSE = json.dumps(
    {
        "overview": "今月はエージェントが話題。",
        "items": [
            {"rank": 1, "label": "数学の難問に反例", "summary": "要約1。"},
            {"rank": 2, "label": "AIブラウザ統合", "summary": "要約2。"},
        ],
        "concepts": ["AIエージェント"],
        "entities": ["OpenAI"],
    }
)


def test_extract_returns_overview_and_summaries() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    extraction = DigestExtractor(provider).extract(RANKED, "2026-08")

    assert extraction.overview == "今月はエージェントが話題。"
    assert extraction.summaries == {1: "要約1。", 2: "要約2。"}
    assert extraction.labels == {1: "数学の難問に反例", 2: "AIブラウザ統合"}
    assert extraction.concepts == ["AIエージェント"]
    # The titles are passed to the LLM (title-based summaries, no body fetch).
    assert "見出し1" in provider.calls[0][1]
    assert provider.calls[0][2] == "json"


def test_extract_rejects_empty_ranking() -> None:
    with pytest.raises(ValueError, match="at least one ranked article"):
        DigestExtractor(MockLLMProvider(VALID_RESPONSE)).extract([], "2026-08")


def test_extract_rejects_invalid_json() -> None:
    with pytest.raises(LLMError, match="invalid JSON"):
        DigestExtractor(MockLLMProvider("nope")).extract(RANKED, "2026-08")


def test_builder_produces_digest_knowledge_object() -> None:
    extraction = DigestExtractor(MockLLMProvider(VALID_RESPONSE)).extract(RANKED, "2026-08")
    ko = KnowledgeObjectBuilder().from_digest("2026-08", RANKED, extraction, top=2)

    assert isinstance(ko, KnowledgeObject)
    assert ko.source.type is SourceType.DIGEST
    assert ko.source.value == "2026-08"  # idempotency key = period
    assert ko.title == "2026-08 AIニュースTOP2"
    assert ko.metadata.domain == "AI"
    assert ko.digest is not None
    assert [i.rank for i in ko.digest.items] == [1, 2]
    assert ko.digest.items[0].summary == "要約1。"
    assert ko.digest.items[0].label == "数学の難問に反例"
    assert ko.digest.items[1].url == "https://ledge.ai/articles/a2"
    # References list every ranked article's URL.
    assert ko.references == ["https://ledge.ai/articles/a1", "https://ledge.ai/articles/a2"]


def test_builder_tolerates_missing_summaries() -> None:
    from backend.parser.digest_extractor import DigestExtraction

    extraction = DigestExtraction(overview="o", summaries={})
    ko = KnowledgeObjectBuilder().from_digest("2026-08", RANKED, extraction)
    assert ko.digest.items[0].summary == ""


def test_illustration_prompt_uses_the_label_not_a_truncated_title() -> None:
    from backend.parser.digest_extractor import DigestExtraction
    from backend.prompts.illustration import build_illustration_prompt

    long_title = [RankedArticle(rank=1, title="と" * 40 + "「未完の見出し", url="https://x/1")]
    extraction = DigestExtraction(overview="o", labels={1: "数学の難問に反例"})
    ko = KnowledgeObjectBuilder().from_digest("2026-08", long_title, extraction, top=1)

    prompt = build_illustration_prompt(ko)
    assert "1. 数学の難問に反例" in prompt
    # The raw (truncated, bracket-dangling) title is not used as the caption.
    assert "「未完の見出し" not in prompt
