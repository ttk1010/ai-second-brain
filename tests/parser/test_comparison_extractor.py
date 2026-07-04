"""Tests for the Comparison Extractor and builder.from_comparison (Issue #28)."""

import json

import pytest

from backend.llm.base import LLMError
from backend.models import KnowledgeObject, SourceType
from backend.parser import ComparisonExtractor, KnowledgeObjectBuilder
from tests.conftest import MockLLMProvider

VALID_RESPONSE = json.dumps(
    {
        "title": "GPT・Claude・Gemini の比較",
        "short_title": "LLM比較",
        "domain": "AI",
        "summary": "代表的な3モデルを比較する。",
        "background": "用途で選択が変わる。",
        "key_takeaways": ["長文ならGemini", "コードならClaude"],
        "items": ["GPT", "Claude", "Gemini"],
        "rows": [
            {"dimension": "コンテキスト長", "cells": ["400K", "500K", "1M"]},
            {"dimension": "強み", "cells": ["汎用", "コード", "長文"]},
        ],
        "recommendation": "長文処理ならGemini、コードならClaude。",
        "concepts": ["LLM"],
        "entities": ["OpenAI", "Anthropic", "Google"],
        "references": [],
    }
)


def test_extract_returns_structured_comparison() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    extraction = ComparisonExtractor(provider).extract("GPT, Claude, Gemini")

    assert extraction.items == ["GPT", "Claude", "Gemini"]
    assert extraction.rows[0].dimension == "コンテキスト長"
    assert extraction.rows[0].cells == ["400K", "500K", "1M"]
    assert extraction.recommendation.startswith("長文")
    assert provider.calls[0][2] == "json"


def test_extract_pads_short_rows_to_item_count() -> None:
    response = json.dumps(
        {
            "title": "t",
            "summary": "s",
            "items": ["A", "B", "C"],
            "rows": [{"dimension": "x", "cells": ["only-one"]}],
        }
    )
    extraction = ComparisonExtractor(MockLLMProvider(response)).extract("A, B, C")
    assert extraction.rows[0].cells == ["only-one", "", ""]


def test_extract_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ComparisonExtractor(MockLLMProvider(VALID_RESPONSE)).extract("  ")


def test_extract_rejects_invalid_json() -> None:
    with pytest.raises(LLMError, match="invalid JSON"):
        ComparisonExtractor(MockLLMProvider("nope")).extract("A, B")


def test_extract_requires_items() -> None:
    response = json.dumps({"title": "t", "summary": "s", "items": []})
    with pytest.raises(LLMError, match="no items"):
        ComparisonExtractor(MockLLMProvider(response)).extract("A, B")


def test_extract_passes_language_directive() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    ComparisonExtractor(provider).extract("A, B", language="ja")
    assert "Japanese" in provider.calls[0][1]


def test_builder_produces_comparison_knowledge_object() -> None:
    extraction = ComparisonExtractor(MockLLMProvider(VALID_RESPONSE)).extract("GPT, Claude, Gemini")
    ko = KnowledgeObjectBuilder().from_comparison("GPT, Claude, Gemini", extraction, language="ja")

    assert isinstance(ko, KnowledgeObject)
    assert ko.source.type is SourceType.COMPARISON
    assert ko.source.value == "GPT, Claude, Gemini"
    assert ko.comparison is not None
    assert ko.comparison.items == ["GPT", "Claude", "Gemini"]
    assert ko.comparison.rows[0].dimension == "コンテキスト長"
    assert ko.metadata.domain == "AI"
    # Items are also added to concepts so the note links to each item's note.
    for item in ["GPT", "Claude", "Gemini"]:
        assert item in ko.concepts
