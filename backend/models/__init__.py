"""Canonical data structures: Knowledge Object and its parts.

Public API for the model layer. All generators consume the Knowledge Object
(DATA_MODEL.md, ADR 0001).
"""

from backend.models.comparison import ComparisonData, ComparisonRow
from backend.models.educational_plan import EducationalPlan, VisualizationStrategy
from backend.models.enums import AspectRatio, ImageQuality, RelationshipType, SourceType
from backend.models.knowledge_object import KnowledgeObject, Source
from backend.models.metadata import Metadata
from backend.models.relationship import Relationship

__all__ = [
    "AspectRatio",
    "ComparisonData",
    "ComparisonRow",
    "EducationalPlan",
    "ImageQuality",
    "KnowledgeObject",
    "Metadata",
    "Relationship",
    "RelationshipType",
    "Source",
    "SourceType",
    "VisualizationStrategy",
]
