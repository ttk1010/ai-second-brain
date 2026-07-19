"""Knowledge pipeline orchestration.

Wires the components together: classify -> extract -> build -> plan ->
illustrate -> markdown -> vault. Components are injected so the pipeline can be
unit-tested with a mock LLM provider and a temporary Vault.

Both the Concept and News pipelines produce the same canonical Knowledge Object
and share the same finalization tail (ARCHITECTURE.md). The News extractor is
optional: when it is not configured, URL input returns an ``unsupported`` result
instead of failing.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.image.base import ImageError
from backend.llm.base import LLMError
from backend.markdown import MarkdownGenerator
from backend.models import KnowledgeObject, SourceType
from backend.models.educational_plan import EducationalPlan
from backend.parser import (
    ComparisonExtractor,
    ConceptExtractor,
    KnowledgeObjectBuilder,
    NewsExtractor,
    classify,
)
from backend.parser.fetcher import FetchedArticle
from backend.planner import EducationalPlanner
from backend.storage import IllustrationWriter, VaultWriter

logger = logging.getLogger(__name__)

PipelineStatus = Literal["created", "exists", "unsupported"]


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of running the pipeline on one input."""

    status: PipelineStatus
    message: str
    knowledge_object: KnowledgeObject | None = None
    path: Path | None = None


class KnowledgePipeline:
    """Turns raw input into a stored Knowledge Node."""

    def __init__(
        self,
        extractor: ConceptExtractor,
        builder: KnowledgeObjectBuilder,
        planner: EducationalPlanner,
        markdown_generator: MarkdownGenerator,
        vault_writer: VaultWriter,
        *,
        news_extractor: NewsExtractor | None = None,
        comparison_extractor: ComparisonExtractor | None = None,
        illustration_writer: IllustrationWriter | None = None,
        language: str = "ja",
    ) -> None:
        self._extractor = extractor
        self._builder = builder
        self._planner = planner
        self._markdown = markdown_generator
        self._vault = vault_writer
        self._news = news_extractor
        self._comparison = comparison_extractor
        self._illustrations = illustration_writer
        self._language = language

    def run(self, raw_input: str, *, overwrite: bool = False, guidance: str = "") -> PipelineResult:
        """Process ``raw_input`` end to end.

        ``guidance`` is the user's optional generation-time instruction (Issue #32):
        a free-text steer (tone, audience, emphasis) applied to extraction,
        planning, and illustration. It does not affect idempotency — the same
        source is still skipped unless ``overwrite`` is set (decision A).

        Raises:
            ValueError: If the input is empty.
        """
        classification = classify(raw_input)
        source_type = classification.source_type
        value = classification.normalized_input

        supported = (
            source_type is SourceType.CONCEPT
            or (source_type is SourceType.NEWS and self._news is not None)
            or (source_type is SourceType.COMPARISON and self._comparison is not None)
        )
        if not supported:
            return PipelineResult(
                status="unsupported",
                message=(
                    f"Could not process input (classified as {source_type.value}). "
                    "Provide an AI concept keyword or a valid article URL."
                ),
            )

        # Idempotency: skip (and avoid all API calls) if this source already exists.
        if not overwrite:
            existing = self._vault.find_existing(source_type, value)
            if existing is not None:
                return PipelineResult(
                    status="exists",
                    message=(
                        f"Note already exists: {existing.name}. Use --overwrite to regenerate."
                    ),
                    path=existing,
                )

        if source_type is SourceType.CONCEPT:
            extraction = self._extractor.extract(value, language=self._language, guidance=guidance)
            ko = self._builder.from_concept(value, extraction, language=self._language)
        elif source_type is SourceType.COMPARISON:  # supported implies the extractor is present
            comparison = self._comparison.extract(value, language=self._language, guidance=guidance)
            ko = self._builder.from_comparison(value, comparison, language=self._language)
        else:  # NEWS (supported implies the news extractor is present)
            extraction = self._news.extract(value, language=self._language, guidance=guidance)
            ko = self._builder.from_news(extraction, language=self._language)

        self._record_guidance(ko, guidance)
        return self._finalize(ko, overwrite=overwrite, guidance=guidance)

    def run_captured(
        self,
        url: str,
        text: str,
        *,
        title: str = "",
        overwrite: bool = False,
        guidance: str = "",
    ) -> PipelineResult:
        """Process an article whose body text was captured by the user (Issue #38).

        For login-required sites, the user brings the already-rendered body text
        (from their own logged-in browser) plus the source ``url``; the fetch step
        is skipped entirely. The note is stored as News (source = ``url``), so
        idempotency and folder routing match the URL path.

        Raises:
            ValueError: If ``url`` or ``text`` is empty.
        """
        if not url or not url.strip():
            raise ValueError("A source URL is required for captured content.")
        if not text or not text.strip():
            raise ValueError("Captured article text must not be empty.")

        source = url.strip()
        if self._news is None:
            return PipelineResult(
                status="unsupported",
                message="Captured content needs the News pipeline, which is not configured.",
            )

        if not overwrite:
            existing = self._vault.find_existing(SourceType.NEWS, source)
            if existing is not None:
                return PipelineResult(
                    status="exists",
                    message=(
                        f"Note already exists: {existing.name}. Use --overwrite to regenerate."
                    ),
                    path=existing,
                )

        article = FetchedArticle(url=source, title=title.strip() or source, text=text.strip())
        extraction = self._news.extract_from_article(
            article, language=self._language, guidance=guidance
        )
        ko = self._builder.from_news(extraction, language=self._language)

        self._record_guidance(ko, guidance)
        return self._finalize(ko, overwrite=overwrite, guidance=guidance)

    @staticmethod
    def _record_guidance(ko: KnowledgeObject, guidance: str) -> None:
        """Record the guidance as provenance (Issue #32): how the note was generated."""
        if guidance.strip():
            ko.metadata.guidance = guidance.strip()

    def _finalize(
        self, ko: KnowledgeObject, *, overwrite: bool, guidance: str = ""
    ) -> PipelineResult:
        """Shared tail for every pipeline: plan, illustrate, render, store."""
        ko.educational_plan = self._plan(ko, guidance=guidance)
        self._illustrate(ko, overwrite=overwrite, guidance=guidance)
        markdown = self._markdown.generate(ko)
        path = self._vault.write(ko, markdown, overwrite=overwrite)

        return PipelineResult(
            status="created",
            message=f"Created note: {ko.outputs['markdown']}",
            knowledge_object=ko,
            path=path,
        )

    def _plan(self, ko: KnowledgeObject, *, guidance: str = "") -> EducationalPlan | None:
        """Plan the education for ``ko``, degrading gracefully on failure.

        The Educational Plan enriches outputs but should never block note
        creation: the system is AI-assisted, not AI-dependent (ARCHITECTURE.md).
        A planning failure is logged and the note is still created without a plan.
        """
        try:
            return self._planner.plan(ko, guidance=guidance)
        except LLMError:
            logger.warning(
                "Educational planning failed for %r; continuing without a plan.", ko.title
            )
            return None

    def _illustrate(self, ko: KnowledgeObject, *, overwrite: bool, guidance: str = "") -> None:
        """Generate and store the illustration, degrading gracefully on failure.

        Like planning, the illustration enriches the note but must never block its
        creation (AI-assisted, not AI-dependent). A generation failure is logged
        and the note is still created without an illustration.
        """
        if self._illustrations is None:
            return
        try:
            self._illustrations.write(ko, overwrite=overwrite, guidance=guidance)
        except ImageError:
            logger.warning(
                "Illustration generation failed for %r; continuing without one.", ko.title
            )
