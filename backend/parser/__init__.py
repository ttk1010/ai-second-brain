"""Input classification and extraction (Concept / News pipelines)."""

from backend.parser.builder import KnowledgeObjectBuilder
from backend.parser.classifier import Classification, classify
from backend.parser.comparison_extractor import ComparisonExtraction, ComparisonExtractor
from backend.parser.concept_extractor import ConceptExtraction, ConceptExtractor
from backend.parser.fetcher import (
    ArticleFetcher,
    FetchedArticle,
    FetchError,
    HttpArticleFetcher,
)
from backend.parser.news_extractor import NewsExtraction, NewsExtractor

__all__ = [
    "ArticleFetcher",
    "Classification",
    "ComparisonExtraction",
    "ComparisonExtractor",
    "ConceptExtraction",
    "ConceptExtractor",
    "FetchError",
    "FetchedArticle",
    "HttpArticleFetcher",
    "KnowledgeObjectBuilder",
    "NewsExtraction",
    "NewsExtractor",
    "classify",
]
