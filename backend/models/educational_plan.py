"""The Educational Plan — defines *how* knowledge should be taught.

Part of the Knowledge Object. The Educational Planner owns this, including the
illustration aspect ratio; the Illustration Generator only consumes it (ADR 0001).
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import AspectRatio


class VisualizationStrategy(BaseModel):
    """How the knowledge should be visualized, including the chosen aspect ratio."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    aspect_ratio: AspectRatio
    description: str | None = Field(default=None, description="What the illustration should convey")


class PageSpec(BaseModel):
    """One page of a multi-page illustration series (Issue #41).

    Each page teaches a distinct facet of the same Knowledge Object (e.g.
    overview -> mechanism -> example -> caveats) while the whole series keeps a
    single, consistent visual language. Present only when the user opted into
    multiple pages; the single-page case leaves ``EducationalPlan.pages`` empty.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    title: str = Field(min_length=1, description="Short facet title (also the page caption)")
    learning_objective: str = Field(min_length=1, description="What this page should teach")
    description: str | None = Field(default=None, description="What this page's illustration shows")
    aspect_ratio: AspectRatio


class EducationalPlan(BaseModel):
    """The teaching strategy that drives all educational outputs."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    learning_objective: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    key_messages: list[str] = Field(default_factory=list)
    visualization_strategy: VisualizationStrategy
    pages: list[PageSpec] = Field(
        default_factory=list,
        description=(
            "Sequential illustration pages for a multi-page note (Issue #41). "
            "Empty for the default single-page illustration."
        ),
    )
