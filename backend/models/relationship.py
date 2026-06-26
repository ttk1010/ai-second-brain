"""Logical relationships between Knowledge Objects (DATA_MODEL.md).

Relationships are logical and independent of storage. The target references
another Knowledge Object by id or by concept name.
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import RelationshipType


class Relationship(BaseModel):
    """A typed, directed link from this Knowledge Object to another."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: RelationshipType
    target: str = Field(min_length=1, description="Target Knowledge Object id or concept name")
    description: str | None = None
