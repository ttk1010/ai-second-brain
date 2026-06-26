"""The Knowledge Object — the canonical representation of knowledge.

Every downstream component (Markdown, illustration, metadata, linking) consumes
the same Knowledge Object. It must never contain presentation-specific data:
the `outputs` field holds references (paths/ids) only, never artifact bodies
(see ADR 0001 and DATA_MODEL.md).

The model is intentionally mutable so the pipeline can build it up in stages
(extract -> plan -> link), but it stays strict via `extra="forbid"` and
`validate_assignment=True`.
"""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.models.educational_plan import EducationalPlan
from backend.models.enums import SourceType
from backend.models.metadata import Metadata
from backend.models.relationship import Relationship


class Source(BaseModel):
    """Where the knowledge originated."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: SourceType
    value: str = Field(min_length=1, description="The original URL or keyword")


class KnowledgeObject(BaseModel):
    """The single source of truth for a piece of knowledge."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: uuid4().hex)
    source: Source
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    concepts: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    educational_plan: EducationalPlan | None = None
    references: list[str] = Field(default_factory=list)
    metadata: Metadata = Field(default_factory=Metadata)
    outputs: dict[str, str] = Field(
        default_factory=dict,
        description="Artifact type -> path/id reference. References only, never bodies.",
    )
