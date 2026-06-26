"""Illustration generation via the ImageProvider abstraction.

Phase 1 ships the interface only; the gpt-image-2 implementation is Phase 2.
"""

from backend.image.base import ImageError, ImageProvider

__all__ = ["ImageError", "ImageProvider"]
