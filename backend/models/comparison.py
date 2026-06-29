"""Comparison data — the structured part of a Comparison Knowledge Object.

Represents "compare A vs B vs C across these dimensions" as data, so the Markdown
comparison table is rendered deterministically from it (ADR 0007). Like the rest
of the Knowledge Object, it holds knowledge, not presentation.
"""

from pydantic import BaseModel, ConfigDict, Field


class ComparisonRow(BaseModel):
    """One comparison dimension and its value per compared item (aligned to items)."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    dimension: str = Field(min_length=1)
    cells: list[str] = Field(default_factory=list)


class ComparisonData(BaseModel):
    """A comparison of several items across dimensions, with a recommendation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    items: list[str] = Field(default_factory=list, description="The things being compared")
    rows: list[ComparisonRow] = Field(default_factory=list, description="Dimension-by-item cells")
    recommendation: str = Field(default="", description="Which to choose when, in short")
