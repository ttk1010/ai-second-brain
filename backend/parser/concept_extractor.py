"""Concept extraction — the Concept pipeline's knowledge step.

Takes a concept keyword, asks the LLM (via the provider abstraction) for
structured fields, and validates the raw shape. Normalization into a full
Knowledge Object is the Builder's job (DATA_MODEL.md data ownership).
"""

import json
from dataclasses import dataclass, field

from backend.llm.base import LLMError, LLMProvider
from backend.prompts.extraction.concept import (
    CONCEPT_SYSTEM_PROMPT,
    build_concept_user_prompt,
)


@dataclass(frozen=True)
class ConceptExtraction:
    """Raw structured fields extracted for a concept (pre-normalization)."""

    title: str
    summary: str
    concepts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class ConceptExtractor:
    """Extracts structured knowledge fields from a concept keyword."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(self, concept: str) -> ConceptExtraction:
        """Extract structured fields for the given concept.

        Raises:
            ValueError: If the concept is empty.
            LLMError: If the LLM response is missing or not valid JSON.
        """
        if not concept or not concept.strip():
            raise ValueError("Concept must not be empty.")

        raw = self._provider.complete(
            CONCEPT_SYSTEM_PROMPT,
            build_concept_user_prompt(concept.strip()),
            response_format="json",
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Concept extraction returned invalid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise LLMError("Concept extraction must return a JSON object.")

        title = str(data.get("title") or "").strip()
        summary = str(data.get("summary") or "").strip()
        if not title or not summary:
            raise LLMError("Concept extraction is missing required 'title' or 'summary'.")

        return ConceptExtraction(
            title=title,
            summary=summary,
            concepts=_string_list(data.get("concepts")),
            entities=_string_list(data.get("entities")),
            references=_string_list(data.get("references")),
        )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
