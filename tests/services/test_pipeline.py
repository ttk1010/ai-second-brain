"""End-to-end tests for the Knowledge Pipeline (Issue #10 / GH #9)."""

import json
from pathlib import Path

import pytest

from backend.markdown import MarkdownGenerator
from backend.parser import ConceptExtractor, KnowledgeObjectBuilder
from backend.planner import EducationalPlanner
from backend.services import KnowledgePipeline
from backend.storage import VaultWriter
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


def _pipeline(
    vault: Path,
    response: str = RESPONSE,
    plan_response: str = PLAN_RESPONSE,
) -> KnowledgePipeline:
    return KnowledgePipeline(
        extractor=ConceptExtractor(MockLLMProvider(response)),
        builder=KnowledgeObjectBuilder(),
        planner=EducationalPlanner(MockLLMProvider(plan_response)),
        markdown_generator=MarkdownGenerator(),
        vault_writer=VaultWriter(vault),
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


def test_planning_failure_does_not_block_note_creation(tmp_path: Path) -> None:
    # An unparsable plan response must not prevent the note from being written.
    result = _pipeline(tmp_path, plan_response="not json").run("Transformer")

    assert result.status == "created"
    assert result.path is not None and result.path.exists()
    assert result.knowledge_object is not None
    assert result.knowledge_object.educational_plan is None


def test_url_input_is_unsupported(tmp_path: Path) -> None:
    result = _pipeline(tmp_path).run("https://openai.com/news/")
    assert result.status == "unsupported"
    assert "Phase 2" in result.message
    # Nothing should be written.
    assert not any(tmp_path.iterdir())


def test_empty_input_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        _pipeline(tmp_path).run("   ")


def test_overwrite_is_passed_through(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    first = pipeline.run("Transformer")
    second = pipeline.run("Transformer", overwrite=True)
    assert first.path == second.path  # same file, overwritten
