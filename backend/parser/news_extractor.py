"""News extraction — the News pipeline's knowledge step.

Fetches an article from a URL, asks the LLM (via the provider abstraction) for
structured fields, and validates the raw shape. It mirrors ``ConceptExtractor`` so
the Builder can normalize both into a Knowledge Object the same way
(DATA_MODEL.md data ownership). Normalization itself is the Builder's job.
"""

import json
from dataclasses import dataclass, field

from backend.llm.base import LLMError, LLMProvider
from backend.parser.fetcher import ArticleFetcher
from backend.prompts.extraction.news import (
    NEWS_SYSTEM_PROMPT,
    build_news_user_prompt,
)


@dataclass(frozen=True)
class NewsExtraction:
    """Raw structured fields extracted from a news article (pre-normalization)."""

    title: str
    summary: str
    url: str
    short_title: str = ""
    published_date: str = ""
    background: str = ""
    key_takeaways: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class NewsExtractor:
    """Extracts structured knowledge fields from a news article URL."""

    def __init__(self, provider: LLMProvider, fetcher: ArticleFetcher) -> None:
        self._provider = provider
        self._fetcher = fetcher

    def extract(self, url: str, *, language: str = "ja") -> NewsExtraction:
        """Fetch ``url`` and extract structured fields.

        Args:
            url: The article URL.
            language: Language for the natural-language fields (e.g. summary).

        Raises:
            ValueError: If the URL is empty.
            FetchError: If the article cannot be fetched or parsed.
            LLMError: If the LLM response is missing or not valid JSON.
        """
        if not url or not url.strip():
            raise ValueError("URL must not be empty.")

        article = self._fetcher.fetch(url.strip())

        raw = self._provider.complete(
            NEWS_SYSTEM_PROMPT,
            build_news_user_prompt(article, language=language),
            response_format="json",
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"News extraction returned invalid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise LLMError("News extraction must return a JSON object.")

        title = str(data.get("title") or "").strip() or article.title.strip()
        summary = str(data.get("summary") or "").strip()
        if not title or not summary:
            raise LLMError("News extraction is missing required 'title' or 'summary'.")

        references = _string_list(data.get("references"))
        if article.url not in references:
            references.append(article.url)

        return NewsExtraction(
            title=title,
            summary=summary,
            url=article.url,
            short_title=str(data.get("short_title") or "").strip(),
            published_date=str(data.get("published_date") or "").strip(),
            background=str(data.get("background") or "").strip(),
            key_takeaways=_string_list(data.get("key_takeaways")),
            concepts=_string_list(data.get("concepts")),
            entities=_string_list(data.get("entities")),
            references=references,
        )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
