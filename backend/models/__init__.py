"""Canonical data structures: Knowledge Object and its parts.

Public API for the model layer. All generators consume the Knowledge Object
(DATA_MODEL.md, ADR 0001).
"""

from backend.models.educational_plan import EducationalPlan, VisualizationStrategy
from backend.models.enums import AspectRatio, RelationshipType, SourceType
from backend.models.knowledge_object import KnowledgeObject, Source
from backend.models.metadata import Metadata
from backend.models.relationship import Relationship

__all__ = [
    "AspectRatio",
    "EducationalPlan",
    "KnowledgeObject",
    "Metadata",
    "Relationship",
    "RelationshipType",
    "Source",
    "SourceType",
    "VisualizationStrategy",
]
