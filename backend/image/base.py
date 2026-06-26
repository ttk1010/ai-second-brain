"""Image provider abstraction (interface only in Phase 1).

Illustration generation is a Phase 2 deliverable (ROADMAP.md). This interface is
defined now so the pipeline can be wired against the abstraction from the start
(provider-agnostic, PROJECT_CHARTER.md); the concrete gpt-image-2 implementation
arrives in Phase 2.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.models.enums import AspectRatio, ImageQuality


class ImageError(Exception):
    """Raised when image generation fails."""


class ImageProvider(ABC):
    """Abstract illustration generator."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: AspectRatio,
        quality: ImageQuality,
        output_path: Path,
    ) -> Path:
        """Generate an illustration and write it to ``output_path``.

        Args:
            prompt: The illustration prompt (built from the Knowledge Object).
            aspect_ratio: Decided by the Educational Planner (ADR 0001).
            quality: Quality tier (cost-sensitive; see ADR 0002).
            output_path: Where to write the generated image.

        Returns:
            The path to the written image.

        Raises:
            ImageError: If generation fails.
        """
