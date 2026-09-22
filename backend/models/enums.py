"""Enumerations used across the Knowledge Object model.

These mirror the controlled vocabularies defined in DATA_MODEL.md and ADR 0001.
"""

from enum import StrEnum


class SourceType(StrEnum):
    """Classification label of the original input (see ADR 0001).

    Phase 1 processes only CONCEPT and NEWS; PAPER and DOCUMENTATION are handled
    provisionally by the News pipeline, and UNKNOWN falls back or fails fast.
    """

    CONCEPT = "concept"
    NEWS = "news"
    COMPARISON = "comparison"
    DIGEST = "digest"
    PAPER = "paper"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


class RelationshipType(StrEnum):
    """Logical relationship between two Knowledge Objects (DATA_MODEL.md)."""

    PREREQUISITE = "prerequisite"
    RELATED = "related"
    SUCCESSOR = "successor"
    ALTERNATIVE = "alternative"
    IMPLEMENTATION = "implementation"
    REGULATION = "regulation"
    APPLICATION = "application"


class AspectRatio(StrEnum):
    """Illustration aspect ratio, decided by the Educational Planner (ADR 0001).

    The mapping from information type to ratio is defined in PROJECT_CHARTER.md.
    """

    WIDE = "16:9"  # Process / Workflow
    STANDARD = "4:3"  # Hierarchical Structure
    SQUARE = "1:1"  # Single Concept
    TALL = "9:16"  # Step-by-step Guide


class IllustrationStyle(StrEnum):
    """Which wording of the illustration visual language to use (Issue #45).

    Both describe the same hand-drawn, textbook-inspired look. ``EXPLICIT_HAND_DRAWN``
    spells it out for image models that otherwise drift to flat vector graphics
    (gpt-image-2.5-flare on the cloud path, ADR 0016).
    """

    STANDARD = "standard"
    EXPLICIT_HAND_DRAWN = "explicit-hand-drawn"


class ImageQuality(StrEnum):
    """Illustration quality tier. Cost differs widely across tiers (see ADR 0002)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
