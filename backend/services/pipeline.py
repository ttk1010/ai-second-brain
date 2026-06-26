"""Knowledge pipeline orchestration.

Wires the components together: classify -> extract -> build -> markdown -> vault.
Components are injected so the pipeline can be unit-tested with a mock LLM
provider and a temporary Vault.

Phase 1 fully supports the Concept pipeline. URLs (News) require the News
extractor, which is a Phase 2 deliverable (ROADMAP.md); for now URL input
returns an ``unsupported`` result with a clear message instead of failing.
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
from backend.parser import ConceptExtractor, KnowledgeObjectBuilder, classify
from backend.planner import EducationalPlanner
from backend.storage import IllustrationWriter, VaultWriter

logger = logging.getLogger(__name__)

PipelineStatus = Literal["created", "unsupported"]


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
        illustration_writer: IllustrationWriter | None = None,
        language: str = "ja",
    ) -> None:
        self._extractor = extractor
        self._builder = builder
        self._planner = planner
        self._markdown = markdown_generator
        self._vault = vault_writer
        self._illustrations = illustration_writer
        self._language = language

    def run(self, raw_input: str, *, overwrite: bool = False) -> PipelineResult:
        """Process ``raw_input`` end to end.

        Raises:
            ValueError: If the input is empty.
        """
        classification = classify(raw_input)

        if classification.source_type is not SourceType.CONCEPT:
            return PipelineResult(
                status="unsupported",
                message=(
                    f"Input classified as {classification.source_type.value}. "
                    "URL/News processing is a Phase 2 feature; only AI concepts "
                    "are supported in Phase 1."
                ),
            )

        concept = classification.normalized_input
        extraction = self._extractor.extract(concept)
        ko = self._builder.from_concept(concept, extraction, language=self._language)
        ko.educational_plan = self._plan(ko)
        self._illustrate(ko, overwrite=overwrite)
        markdown = self._markdown.generate(ko)
        path = self._vault.write(ko, markdown, overwrite=overwrite)

        return PipelineResult(
            status="created",
            message=f"Created note: {ko.outputs['markdown']}",
            knowledge_object=ko,
            path=path,
        )

    def _plan(self, ko: KnowledgeObject) -> EducationalPlan | None:
        """Plan the education for ``ko``, degrading gracefully on failure.

        The Educational Plan enriches outputs but should never block note
        creation: the system is AI-assisted, not AI-dependent (ARCHITECTURE.md).
        A planning failure is logged and the note is still created without a plan.
        """
        try:
            return self._planner.plan(ko)
        except LLMError:
            logger.warning(
                "Educational planning failed for %r; continuing without a plan.", ko.title
            )
            return None

    def _illustrate(self, ko: KnowledgeObject, *, overwrite: bool) -> None:
        """Generate and store the illustration, degrading gracefully on failure.

        Like planning, the illustration enriches the note but must never block its
        creation (AI-assisted, not AI-dependent). A generation failure is logged
        and the note is still created without an illustration.
        """
        if self._illustrations is None:
            return
        try:
            self._illustrations.write(ko, overwrite=overwrite)
        except ImageError:
            logger.warning(
                "Illustration generation failed for %r; continuing without one.", ko.title
            )
