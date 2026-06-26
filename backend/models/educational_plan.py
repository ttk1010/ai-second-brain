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


class EducationalPlan(BaseModel):
    """The teaching strategy that drives all educational outputs."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    learning_objective: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    key_messages: list[str] = Field(default_factory=list)
    visualization_strategy: VisualizationStrategy
