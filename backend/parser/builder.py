"""Knowledge Object Builder — normalizes extractions into the canonical model.

This is the single component that produces a Knowledge Object (ADR 0001). It is
independent of how the input was obtained; downstream components consume only the
resulting Knowledge Object.
"""

from backend.models import KnowledgeObject, Metadata, Source, SourceType
from backend.parser.concept_extractor import ConceptExtraction
from backend.parser.news_extractor import NewsExtraction


class KnowledgeObjectBuilder:
    """Builds Knowledge Objects from extraction results."""

    def from_concept(
        self,
        concept: str,
        extraction: ConceptExtraction,
        *,
        language: str = "ja",
    ) -> KnowledgeObject:
        """Normalize a concept extraction into a Knowledge Object."""
        return KnowledgeObject(
            source=Source(type=SourceType.CONCEPT, value=concept.strip()),
            title=extraction.title,
            short_title=extraction.short_title,
            summary=extraction.summary,
            background=extraction.background,
            key_takeaways=extraction.key_takeaways,
            concepts=extraction.concepts,
            entities=extraction.entities,
            references=extraction.references,
            metadata=Metadata(language=language),
        )

    def from_news(
        self,
        extraction: NewsExtraction,
        *,
        language: str = "ja",
    ) -> KnowledgeObject:
        """Normalize a news extraction into a Knowledge Object.

        Both pipelines produce the same canonical model; only the source differs
        (the URL), so downstream components stay input-agnostic (ARCHITECTURE.md).
        """
        return KnowledgeObject(
            source=Source(type=SourceType.NEWS, value=extraction.url),
            title=extraction.title,
            short_title=extraction.short_title,
            summary=extraction.summary,
            background=extraction.background,
            key_takeaways=extraction.key_takeaways,
            concepts=extraction.concepts,
            entities=extraction.entities,
            references=extraction.references,
            metadata=Metadata(language=language),
        )
