"""Illustration generation via the ImageProvider abstraction.

The interface lives in ``base``; ``OpenAIImageProvider`` is the gpt-image-2
implementation (Phase 2). Core code depends on the abstraction, never the
concrete provider (PROJECT_CHARTER.md).
"""

from backend.image.base import ImageError, ImageProvider
from backend.image.openai_provider import OpenAIImageProvider

__all__ = ["ImageError", "ImageProvider", "OpenAIImageProvider"]
