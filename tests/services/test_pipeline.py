"""End-to-end tests for the Knowledge Pipeline (Issue #10 / GH #9)."""

import json
from pathlib import Path

import pytest

from backend.image.base import ImageError, ImageProvider
from backend.markdown import MarkdownGenerator
from backend.models import SourceType
from backend.parser import ConceptExtractor, KnowledgeObjectBuilder, NewsExtractor
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
) -> KnowledgePipeline:
    illustration_writer = (
        IllustrationWriter(vault, image_provider) if image_provider is not None else None
    )
    news_extractor = NewsExtractor(MockLLMProvider(response), _FakeFetcher()) if with_news else None
    return KnowledgePipeline(
        extractor=ConceptExtractor(MockLLMProvider(response)),
        builder=KnowledgeObjectBuilder(),
        planner=EducationalPlanner(MockLLMProvider(plan_response)),
        markdown_generator=MarkdownGenerator(),
        vault_writer=VaultWriter(vault),
        news_extractor=news_extractor,
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


def test_malformed_url_is_unsupported(tmp_path: Path) -> None:
    result = _pipeline(tmp_path, with_news=True).run("http://")
    assert result.status == "unsupported"
    assert not any(tmp_path.iterdir())


def test_empty_input_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        _pipeline(tmp_path).run("   ")


def test_overwrite_is_passed_through(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    first = pipeline.run("Transformer")
    second = pipeline.run("Transformer", overwrite=True)
    assert first.path == second.path  # same file, overwritten
