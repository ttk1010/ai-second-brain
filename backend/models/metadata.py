"""Metadata describing a Knowledge Object — never its presentation (ADR 0001)."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Metadata(BaseModel):
    """Descriptive metadata, reusable across all output formats.

    Describes the knowledge itself (source, dates, tags), not how it is rendered.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    source_url: str | None = None
    published_date: date | None = None
    author: str | None = None
    domain: str | None = Field(
        default=None,
        description="Field this knowledge belongs to (e.g. 'AI'); AI is the default focus.",
    )
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reading_time: int | None = Field(default=None, ge=0, description="Estimated minutes")
    language: str = "ja"
