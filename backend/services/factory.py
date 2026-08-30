"""Construct a fully wired KnowledgePipeline from settings.

Shared by the ``asb`` CLI and the ``asb-inbox`` worker so the pipeline is built
in exactly one place (dependency injection, CLAUDE.md). The OpenAI providers are
constructed here but reached only through their abstractions inside the pipeline.
"""

from backend.config import Settings
from backend.image import OpenAIImageProvider
from backend.llm import OpenAIProvider
from backend.markdown import MarkdownGenerator
from backend.parser import (
    ComparisonExtractor,
    ConceptExtractor,
    DigestExtractor,
    HttpArticleFetcher,
    KnowledgeObjectBuilder,
    LedgeAiRankingFetcher,
    NewsExtractor,
)
from backend.planner import EducationalPlanner
from backend.services.pipeline import KnowledgePipeline
from backend.services.reviser import NoteReviser
from backend.storage import IllustrationWriter, VaultWriter


def build_pipeline(settings: Settings, *, no_image: bool = False) -> KnowledgePipeline:
    """Build a KnowledgePipeline from settings.

    Args:
        settings: Loaded application settings.
        no_image: When True, illustrations are not generated (cost saving).
    """
    provider = OpenAIProvider(model=settings.llm_model)

    illustration_writer = None
    if not no_image:
        illustration_writer = IllustrationWriter(
            settings.vault_path,
            OpenAIImageProvider(model=settings.image_model),
            image_output_dir=settings.image_output_dir,
            quality=settings.image_quality,
            default_aspect_ratio=settings.default_aspect_ratio,
        )

    return KnowledgePipeline(
        extractor=ConceptExtractor(provider),
        builder=KnowledgeObjectBuilder(),
        planner=EducationalPlanner(provider),
        markdown_generator=MarkdownGenerator(),
        vault_writer=VaultWriter(settings.vault_path),
        news_extractor=NewsExtractor(provider, HttpArticleFetcher()),
        comparison_extractor=ComparisonExtractor(provider),
        digest_extractor=DigestExtractor(provider),
        ranking_fetcher=LedgeAiRankingFetcher(),
        illustration_writer=illustration_writer,
        language=settings.default_language,
    )


def build_reviser(settings: Settings, *, no_image: bool = False) -> NoteReviser:
    """Build a NoteReviser from settings (Issue #29).

    Args:
        settings: Loaded application settings.
        no_image: When True, the illustration cannot be revised (text sections
            only); saves building the image provider.
    """
    image_provider = None if no_image else OpenAIImageProvider(model=settings.image_model)
    return NoteReviser(
        VaultWriter(settings.vault_path),
        OpenAIProvider(model=settings.llm_model),
        settings.vault_path,
        image_provider=image_provider,
        quality=settings.image_quality,
        default_aspect_ratio=settings.default_aspect_ratio,
        language=settings.default_language,
    )
