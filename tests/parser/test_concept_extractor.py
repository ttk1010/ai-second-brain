"""Tests for the Concept Extractor and Knowledge Object Builder (Issue #7)."""

import json

import pytest

from backend.llm.base import LLMError
from backend.models import KnowledgeObject, SourceType
from backend.parser import ConceptExtractor, KnowledgeObjectBuilder
from tests.conftest import MockLLMProvider

VALID_RESPONSE = json.dumps(
    {
        "title": "Transformer",
        "summary": "A neural network architecture based on self-attention.",
        "concepts": ["attention", "self-attention"],
        "entities": ["Google"],
        "references": ["https://arxiv.org/abs/1706.03762"],
    }
)


def test_extract_returns_structured_fields() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    extraction = ConceptExtractor(provider).extract("Transformer")

    assert extraction.title == "Transformer"
    assert "attention" in extraction.concepts
    assert extraction.entities == ["Google"]
    # The extractor requests a JSON response.
    assert provider.calls[0][2] == "json"


def test_extract_rejects_empty_concept() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ConceptExtractor(MockLLMProvider(VALID_RESPONSE)).extract("  ")


def test_extract_rejects_invalid_json() -> None:
    with pytest.raises(LLMError, match="invalid JSON"):
        ConceptExtractor(MockLLMProvider("not json")).extract("Transformer")


def test_extract_rejects_non_object_json() -> None:
    with pytest.raises(LLMError, match="JSON object"):
        ConceptExtractor(MockLLMProvider("[1, 2, 3]")).extract("Transformer")


def test_extract_requires_title_and_summary() -> None:
    response = json.dumps({"title": "", "summary": "x"})
    with pytest.raises(LLMError, match="title.*summary"):
        ConceptExtractor(MockLLMProvider(response)).extract("Transformer")


def test_extract_tolerates_missing_optional_lists() -> None:
    response = json.dumps({"title": "MCP", "summary": "A protocol."})
    extraction = ConceptExtractor(MockLLMProvider(response)).extract("MCP")
    assert extraction.concepts == []
    assert extraction.references == []


def test_builder_produces_valid_knowledge_object() -> None:
    extraction = ConceptExtractor(MockLLMProvider(VALID_RESPONSE)).extract("Transformer")
    ko = KnowledgeObjectBuilder().from_concept("Transformer", extraction, language="ja")

    assert isinstance(ko, KnowledgeObject)
    assert ko.source.type is SourceType.CONCEPT
    assert ko.source.value == "Transformer"
    assert ko.title == "Transformer"
    assert ko.metadata.language == "ja"
    assert ko.id  # auto-generated
