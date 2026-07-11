"""Tests for the Educational Planner (Issue #11)."""

import json

import pytest

from backend.llm.base import LLMError
from backend.models import AspectRatio, KnowledgeObject, Source, SourceType
from backend.planner import EducationalPlanner
from tests.conftest import MockLLMProvider

VALID_RESPONSE = json.dumps(
    {
        "learning_objective": "Understand how self-attention powers Transformers.",
        "target_audience": "Software engineers new to deep learning.",
        "prerequisites": ["linear algebra", "neural networks"],
        "key_messages": ["Attention weighs tokens", "Parallelizable"],
        "visualization": {
            "aspect_ratio": "4:3",
            "description": "A diagram of the attention mechanism.",
        },
    }
)


def _ko() -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture based on self-attention.",
        concepts=["attention"],
        entities=["Google"],
    )


def test_plan_returns_structured_plan() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    plan = EducationalPlanner(provider).plan(_ko())

    assert plan.learning_objective.startswith("Understand")
    assert plan.target_audience
    assert "linear algebra" in plan.prerequisites
    assert plan.key_messages == ["Attention weighs tokens", "Parallelizable"]
    assert plan.visualization_strategy.aspect_ratio is AspectRatio.STANDARD
    # The planner requests a JSON response.
    assert provider.calls[0][2] == "json"


def test_plan_passes_language_directive_from_metadata() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    EducationalPlanner(provider).plan(_ko())  # metadata language defaults to ja
    assert "Japanese" in provider.calls[0][1]


def test_plan_passes_guidance_to_prompt() -> None:
    provider = MockLLMProvider(VALID_RESPONSE)
    EducationalPlanner(provider).plan(_ko(), guidance="高校生向けに")
    assert "高校生向けに" in provider.calls[0][1]


def test_plan_rejects_invalid_json() -> None:
    with pytest.raises(LLMError, match="invalid JSON"):
        EducationalPlanner(MockLLMProvider("not json")).plan(_ko())


def test_plan_rejects_non_object_json() -> None:
    with pytest.raises(LLMError, match="JSON object"):
        EducationalPlanner(MockLLMProvider("[1, 2, 3]")).plan(_ko())


def test_plan_requires_objective_and_audience() -> None:
    response = json.dumps({"learning_objective": "", "target_audience": "x"})
    with pytest.raises(LLMError, match="learning_objective.*target_audience"):
        EducationalPlanner(MockLLMProvider(response)).plan(_ko())


def test_plan_defaults_aspect_ratio_when_missing() -> None:
    response = json.dumps(
        {
            "learning_objective": "Understand X.",
            "target_audience": "Engineers.",
        }
    )
    plan = EducationalPlanner(MockLLMProvider(response)).plan(_ko())
    assert plan.visualization_strategy.aspect_ratio is AspectRatio.WIDE
    assert plan.visualization_strategy.description is None


def test_plan_defaults_aspect_ratio_when_unknown() -> None:
    response = json.dumps(
        {
            "learning_objective": "Understand X.",
            "target_audience": "Engineers.",
            "visualization": {"aspect_ratio": "21:9"},
        }
    )
    plan = EducationalPlanner(MockLLMProvider(response)).plan(_ko())
    assert plan.visualization_strategy.aspect_ratio is AspectRatio.WIDE


def test_plan_tolerates_missing_optional_lists() -> None:
    response = json.dumps(
        {
            "learning_objective": "Understand X.",
            "target_audience": "Engineers.",
        }
    )
    plan = EducationalPlanner(MockLLMProvider(response)).plan(_ko())
    assert plan.prerequisites == []
    assert plan.key_messages == []
