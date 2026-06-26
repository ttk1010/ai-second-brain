"""Tests for the Knowledge Object data model (Issue #4).

These tests describe expected behavior: valid construction, serialization
round-trips, strict validation, id auto-generation, and aspect-ratio retention.
"""

import pytest
from pydantic import ValidationError

from backend.models import (
    AspectRatio,
    EducationalPlan,
    KnowledgeObject,
    Metadata,
    Relationship,
    RelationshipType,
    Source,
    SourceType,
    VisualizationStrategy,
)


def _minimal_knowledge_object() -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture based on self-attention.",
    )


def _full_knowledge_object() -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture based on self-attention.",
        concepts=["attention", "self-attention"],
        entities=["Google"],
        relationships=[
            Relationship(type=RelationshipType.PREREQUISITE, target="attention"),
        ],
        educational_plan=EducationalPlan(
            learning_objective="Understand how attention powers Transformers.",
            target_audience="Engineers familiar with ML.",
            prerequisites=["neural networks"],
            key_messages=["Attention replaces recurrence."],
            visualization_strategy=VisualizationStrategy(aspect_ratio=AspectRatio.WIDE),
        ),
        references=["https://arxiv.org/abs/1706.03762"],
        metadata=Metadata(tags=["nlp"], confidence=0.9, language="ja"),
        outputs={"markdown": "01 Concepts/transformer.md"},
    )


def test_minimal_construction_succeeds() -> None:
    ko = _minimal_knowledge_object()
    assert ko.title == "Transformer"
    assert ko.source.type is SourceType.CONCEPT
    assert ko.educational_plan is None
    assert ko.concepts == []


def test_id_is_auto_generated_and_unique() -> None:
    a = _minimal_knowledge_object()
    b = _minimal_knowledge_object()
    assert a.id
    assert a.id != b.id


def test_explicit_id_is_respected() -> None:
    ko = KnowledgeObject(
        id="custom-id",
        source=Source(type=SourceType.CONCEPT, value="x"),
        title="x",
        summary="x",
    )
    assert ko.id == "custom-id"


def test_json_round_trip_preserves_values() -> None:
    ko = _full_knowledge_object()
    dumped = ko.model_dump_json()
    restored = KnowledgeObject.model_validate_json(dumped)
    assert restored == ko


def test_aspect_ratio_is_retained_in_plan() -> None:
    ko = _full_knowledge_object()
    assert ko.educational_plan is not None
    assert ko.educational_plan.visualization_strategy.aspect_ratio is AspectRatio.WIDE


def test_outputs_holds_references_only() -> None:
    ko = _full_knowledge_object()
    assert ko.outputs == {"markdown": "01 Concepts/transformer.md"}


@pytest.mark.parametrize("field", ["title", "summary"])
def test_empty_required_strings_are_rejected(field: str) -> None:
    kwargs = {
        "source": Source(type=SourceType.CONCEPT, value="x"),
        "title": "x",
        "summary": "x",
    }
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        KnowledgeObject(**kwargs)


def test_unknown_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObject(
            source=Source(type=SourceType.CONCEPT, value="x"),
            title="x",
            summary="x",
            titel="typo",  # intentional typo to trigger extra="forbid"
        )


def test_invalid_assignment_is_rejected() -> None:
    ko = _minimal_knowledge_object()
    with pytest.raises(ValidationError):
        ko.title = ""


def test_confidence_out_of_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Metadata(confidence=2.0)


def test_staged_build_allows_mutation() -> None:
    ko = _minimal_knowledge_object()
    ko.concepts = ["attention"]
    ko.relationships = [Relationship(type=RelationshipType.RELATED, target="RNN")]
    assert ko.concepts == ["attention"]
    assert ko.relationships[0].target == "RNN"
