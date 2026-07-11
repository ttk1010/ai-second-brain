"""Comparison extraction — the Comparison pipeline's knowledge step.

Takes a free-form list of items to compare, asks the LLM (via the provider
abstraction) for a structured comparison, and validates the raw shape.
Normalization into a Knowledge Object is the Builder's job (DATA_MODEL.md).
"""

import json
from dataclasses import dataclass, field

from backend.llm.base import LLMError, LLMProvider
from backend.prompts.extraction.comparison import (
    COMPARISON_SYSTEM_PROMPT,
    build_comparison_user_prompt,
)


@dataclass(frozen=True)
class ComparisonRowExtraction:
    """A raw comparison row: a dimension and one cell per item."""

    dimension: str
    cells: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComparisonExtraction:
    """Raw structured fields extracted for a comparison (pre-normalization)."""

    title: str
    summary: str
    short_title: str = ""
    domain: str = ""
    background: str = ""
    key_takeaways: list[str] = field(default_factory=list)
    items: list[str] = field(default_factory=list)
    rows: list[ComparisonRowExtraction] = field(default_factory=list)
    recommendation: str = ""
    concepts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class ComparisonExtractor:
    """Extracts a structured comparison from a list of items."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(
        self, items_input: str, *, language: str = "ja", guidance: str = ""
    ) -> ComparisonExtraction:
        """Extract a structured comparison for the given items.

        Raises:
            ValueError: If the input is empty.
            LLMError: If the LLM response is missing or not valid JSON, or has no
                items to compare.
        """
        if not items_input or not items_input.strip():
            raise ValueError("Comparison input must not be empty.")

        raw = self._provider.complete(
            COMPARISON_SYSTEM_PROMPT,
            build_comparison_user_prompt(items_input.strip(), language=language, guidance=guidance),
            response_format="json",
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Comparison extraction returned invalid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise LLMError("Comparison extraction must return a JSON object.")

        title = str(data.get("title") or "").strip()
        summary = str(data.get("summary") or "").strip()
        if not title or not summary:
            raise LLMError("Comparison extraction is missing required 'title' or 'summary'.")

        items = _string_list(data.get("items"))
        if not items:
            raise LLMError("Comparison extraction returned no items to compare.")

        return ComparisonExtraction(
            title=title,
            summary=summary,
            short_title=str(data.get("short_title") or "").strip(),
            domain=str(data.get("domain") or "").strip(),
            background=str(data.get("background") or "").strip(),
            key_takeaways=_string_list(data.get("key_takeaways")),
            items=items,
            rows=_rows(data.get("rows"), len(items)),
            recommendation=str(data.get("recommendation") or "").strip(),
            concepts=_string_list(data.get("concepts")),
            entities=_string_list(data.get("entities")),
            references=_string_list(data.get("references")),
        )


def _rows(value: object, item_count: int) -> list[ComparisonRowExtraction]:
    if not isinstance(value, list):
        return []
    rows: list[ComparisonRowExtraction] = []
    for raw_row in value:
        if not isinstance(raw_row, dict):
            continue
        dimension = str(raw_row.get("dimension") or "").strip()
        if not dimension:
            continue
        cells = _string_list(raw_row.get("cells"))
        # Pad/truncate so every row aligns to the item columns.
        cells = (cells + [""] * item_count)[:item_count]
        rows.append(ComparisonRowExtraction(dimension=dimension, cells=cells))
    return rows


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
