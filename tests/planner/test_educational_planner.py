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


# --- Multi-page series (Issue #41) ------------------------------------------


def _pages_response(count: int) -> str:
    data = json.loads(VALID_RESPONSE)
    data["pages"] = [
        {
            "title": f"Page {i}",
            "learning_objective": f"Teach part {i}.",
            "aspect_ratio": "16:9",
            "description": f"Illustration {i}.",
        }
        for i in range(1, count + 1)
    ]
    return json.dumps(data)


def test_plan_default_has_no_pages() -> None:
    plan = EducationalPlanner(MockLLMProvider(_pages_response(3))).plan(_ko())
    # Without a page request, any returned pages are ignored (single illustration).
    assert plan.pages == []


def test_plan_parses_requested_pages() -> None:
    plan = EducationalPlanner(MockLLMProvider(_pages_response(3))).plan(_ko(), pages=3)
    assert [p.title for p in plan.pages] == ["Page 1", "Page 2", "Page 3"]
    assert plan.pages[0].learning_objective == "Teach part 1."


def test_plan_requesting_pages_puts_count_in_prompt() -> None:
    provider = MockLLMProvider(_pages_response(4))
    EducationalPlanner(provider).plan(_ko(), pages=4)
    assert "exactly 4 sequential illustration pages" in provider.calls[0][1]


def test_plan_auto_pages_asks_planner_to_choose() -> None:
    provider = MockLLMProvider(_pages_response(3))
    plan = EducationalPlanner(provider).plan(_ko(), pages="auto")
    assert "between 2 and 6" in provider.calls[0][1]
    assert len(plan.pages) == 3


def test_plan_caps_pages_at_maximum() -> None:
    plan = EducationalPlanner(MockLLMProvider(_pages_response(10))).plan(_ko(), pages=10)
    assert len(plan.pages) == 6  # MAX_PAGES


def test_plan_single_usable_page_falls_back_to_single_image() -> None:
    # A "series" of one is not a series; degrade to the default single image.
    plan = EducationalPlanner(MockLLMProvider(_pages_response(1))).plan(_ko(), pages=2)
    assert plan.pages == []
