"""Educational Planner — decides *how* a Knowledge Object should be taught.

This is the heart of the system (ARCHITECTURE.md). It consumes a Knowledge Object
and produces an Educational Plan that drives both Markdown and illustration
outputs. The plan, including the illustration aspect ratio, is owned here
(ADR 0001); downstream components only consume it.

The LLM is reached through the provider abstraction so no core logic is tied to a
single vendor (PROJECT_CHARTER.md). The aspect ratio defaults to 16:9 and only
changes when the model picks another valid ratio (Illustration Principles).
"""

import json
import logging
from typing import Literal

from backend.llm.base import LLMError, LLMProvider
from backend.models import KnowledgeObject
from backend.models.educational_plan import EducationalPlan, PageSpec, VisualizationStrategy
from backend.models.enums import AspectRatio
from backend.prompts.planning.educational import (
    PLAN_SYSTEM_PROMPT,
    build_plan_user_prompt,
)

logger = logging.getLogger(__name__)

# Illustration Principles: 16:9 is the default; another ratio is used only when it
# improves comprehension.
DEFAULT_ASPECT_RATIO = AspectRatio.WIDE

# A multi-page illustration series is capped to keep cost bounded (Issue #41):
# every extra page is another image API call.
MAX_PAGES = 6

# How the user chose the number of illustration pages (Issue #41): an integer for
# an explicit count, "auto" to let the planner decide, or None/1 for the default
# single illustration.
PagesOption = int | Literal["auto"] | None


class EducationalPlanner:
    """Builds an Educational Plan from a Knowledge Object."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def plan(
        self, ko: KnowledgeObject, *, guidance: str = "", pages: PagesOption = None
    ) -> EducationalPlan:
        """Produce an Educational Plan for the given Knowledge Object.

        ``guidance`` is the user's optional generation-time instruction (Issue #32).
        ``pages`` opts into a multi-page illustration series (Issue #41): an
        integer requests that many pages, ``"auto"`` lets the planner choose, and
        ``None``/1 keeps the default single illustration.

        Raises:
            LLMError: If the LLM response is missing or not valid JSON, or if
                required fields are absent.
        """
        raw = self._provider.complete(
            PLAN_SYSTEM_PROMPT,
            build_plan_user_prompt(ko, guidance=guidance, pages=_prompt_pages(pages)),
            response_format="json",
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Educational planning returned invalid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise LLMError("Educational planning must return a JSON object.")

        learning_objective = str(data.get("learning_objective") or "").strip()
        target_audience = str(data.get("target_audience") or "").strip()
        if not learning_objective or not target_audience:
            raise LLMError(
                "Educational planning is missing required "
                "'learning_objective' or 'target_audience'."
            )

        visualization = data.get("visualization")
        if not isinstance(visualization, dict):
            visualization = {}

        return EducationalPlan(
            learning_objective=learning_objective,
            target_audience=target_audience,
            prerequisites=_string_list(data.get("prerequisites")),
            key_messages=_string_list(data.get("key_messages")),
            visualization_strategy=VisualizationStrategy(
                aspect_ratio=_aspect_ratio(visualization.get("aspect_ratio")),
                description=_optional_str(visualization.get("description")),
            ),
            pages=_parse_pages(data.get("pages"), pages),
        )


def _prompt_pages(pages: PagesOption) -> int | str | None:
    """Normalize the page request for the prompt, clamping explicit counts."""
    if pages is None or pages == "auto":
        return pages
    return max(1, min(int(pages), MAX_PAGES))


def _parse_pages(value: object, requested: PagesOption) -> list[PageSpec]:
    """Parse the optional multi-page breakdown from the plan response (Issue #41).

    Returns an empty list (single illustration) when no multi-page series was
    requested or when the model returned nothing usable, so planning degrades
    gracefully to the default one-image behavior.
    """
    if requested is None or requested == 1:
        return []
    if not isinstance(value, list):
        return []

    specs: list[PageSpec] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        objective = str(item.get("learning_objective") or "").strip()
        if not title or not objective:
            continue
        specs.append(
            PageSpec(
                title=title,
                learning_objective=objective,
                description=_optional_str(item.get("description")),
                aspect_ratio=_aspect_ratio(item.get("aspect_ratio")),
            )
        )
        if len(specs) >= MAX_PAGES:
            break

    # A single usable page is not a series; fall back to the default one image.
    return specs if len(specs) >= 2 else []


def _aspect_ratio(value: object) -> AspectRatio:
    """Map a raw aspect-ratio value to the enum, defaulting to 16:9."""
    try:
        return AspectRatio(str(value).strip())
    except ValueError:
        logger.warning("Unknown aspect ratio %r; defaulting to %s", value, DEFAULT_ASPECT_RATIO)
        return DEFAULT_ASPECT_RATIO


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
