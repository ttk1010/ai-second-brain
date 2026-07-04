"""Knowledge Object Builder — normalizes extractions into the canonical model.

This is the single component that produces a Knowledge Object (ADR 0001). It is
independent of how the input was obtained; downstream components consume only the
resulting Knowledge Object.
"""

from datetime import date

from backend.models import (
    ComparisonData,
    ComparisonRow,
    KnowledgeObject,
    Metadata,
    Source,
    SourceType,
)
from backend.parser.comparison_extractor import ComparisonExtraction
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
            metadata=Metadata(
                language=language, published_date=_parse_date(extraction.published_date)
            ),
        )

    def from_comparison(
        self,
        items_input: str,
        extraction: ComparisonExtraction,
        *,
        language: str = "ja",
    ) -> KnowledgeObject:
        """Normalize a comparison extraction into a Knowledge Object.

        The compared items go into both the structured ``comparison`` and the
        ``concepts`` list, so the note links to each item's own concept note.
        """
        comparison = ComparisonData(
            items=extraction.items,
            rows=[ComparisonRow(dimension=r.dimension, cells=r.cells) for r in extraction.rows],
            recommendation=extraction.recommendation,
        )
        concepts = _unique(extraction.concepts + extraction.items)
        return KnowledgeObject(
            source=Source(type=SourceType.COMPARISON, value=items_input.strip()),
            title=extraction.title,
            short_title=extraction.short_title,
            summary=extraction.summary,
            background=extraction.background,
            key_takeaways=extraction.key_takeaways,
            concepts=concepts,
            entities=extraction.entities,
            comparison=comparison,
            references=extraction.references,
            metadata=Metadata(language=language),
        )


def _parse_date(value: str) -> date | None:
    """Parse an ISO ``YYYY-MM-DD`` string, returning None when empty or invalid."""
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, TypeError):
        return None


def _unique(items: list[str]) -> list[str]:
    """Preserve order while removing duplicates and blanks."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result
