"""Digest summarization — turns ranked headlines into one-line summaries (Issue #39).

Takes the period's ranked articles (title + URL, from the RankingFetcher) and asks
the LLM for a one-line summary per rank plus an overall overview. It does not fetch
article bodies, so it stays cheap (ADR 0010). Normalization into a Knowledge Object
is the Builder's job (DATA_MODEL.md).
"""

import json
from dataclasses import dataclass, field

from backend.llm.base import LLMError, LLMProvider
from backend.parser.ranking import RankedArticle
from backend.prompts.extraction.digest import (
    DIGEST_SYSTEM_PROMPT,
    build_digest_user_prompt,
)


@dataclass(frozen=True)
class DigestExtraction:
    """Raw digest fields extracted from the ranked headlines (pre-normalization)."""

    overview: str
    summaries: dict[int, str] = field(default_factory=dict)
    concepts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)


class DigestExtractor:
    """Summarizes a period's ranked headlines into a digest."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(
        self,
        ranked: list[RankedArticle],
        period: str,
        *,
        language: str = "ja",
        guidance: str = "",
    ) -> DigestExtraction:
        """Summarize the ranked headlines.

        Raises:
            ValueError: If there are no ranked articles.
            LLMError: If the LLM response is missing or not valid JSON.
        """
        if not ranked:
            raise ValueError("Digest needs at least one ranked article.")

        titles = [article.title for article in ranked]
        raw = self._provider.complete(
            DIGEST_SYSTEM_PROMPT,
            build_digest_user_prompt(titles, period, language=language, guidance=guidance),
            response_format="json",
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Digest summarization returned invalid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise LLMError("Digest summarization must return a JSON object.")

        summaries: dict[int, str] = {}
        for item in data.get("items") or []:
            if not isinstance(item, dict):
                continue
            try:
                rank = int(item.get("rank"))
            except (TypeError, ValueError):
                continue
            summary = str(item.get("summary") or "").strip()
            if rank and summary:
                summaries[rank] = summary

        return DigestExtraction(
            overview=str(data.get("overview") or "").strip(),
            summaries=summaries,
            concepts=_string_list(data.get("concepts")),
            entities=_string_list(data.get("entities")),
        )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
