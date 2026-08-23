"""Monthly digest structure — a ranked list of the period's top stories (Issue #39).

Like ``ComparisonData`` (ADR 0007), this is an optional Knowledge Object field
set only for digest notes. It keeps the ranked stories (rank, title, URL, one-line
summary) so the Markdown note and the illustration are both generated from the
Knowledge Object (ADR 0001 / ADR 0010), never from raw input.
"""

from pydantic import BaseModel, ConfigDict, Field


class DigestItem(BaseModel):
    """One ranked story in a digest."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    summary: str = ""


class DigestData(BaseModel):
    """A period's ranked top stories, in rank order."""

    model_config = ConfigDict(extra="forbid")

    period: str = Field(min_length=1, description="Label for the period, e.g. '2026-08'.")
    items: list[DigestItem] = Field(default_factory=list)
