"""OpenAI implementation of the ImageProvider (gpt-image-2).

The ``openai`` SDK is imported lazily so that importing this module (and running
tests with a fake client) never requires the package to be configured or an API
key to be present — mirroring the text ``OpenAIProvider`` (PROJECT_CHARTER.md:
no implementation is tied to a single vendor in the core layer).
"""

import base64
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from backend.image.base import ImageError, ImageProvider
from backend.models.enums import AspectRatio, ImageQuality

if TYPE_CHECKING:
    from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-image-2"

# gpt-image models support a fixed set of sizes. Map each aspect ratio to the
# closest supported resolution (4:3 has no native size, so it uses landscape).
_SIZE_FOR_RATIO: dict[AspectRatio, str] = {
    AspectRatio.WIDE: "1536x1024",
    AspectRatio.STANDARD: "1536x1024",
    AspectRatio.SQUARE: "1024x1024",
    AspectRatio.TALL: "1024x1536",
}


class OpenAIImageProvider(ImageProvider):
    """Illustration generation backed by the OpenAI image API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        api_key: str | None = None,
        client: "OpenAI | None" = None,
    ) -> None:
        self._model = model
        self._client = client
        self._api_key = api_key

    def _get_client(self) -> "OpenAI":
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - defensive
                raise ImageError(
                    "The 'openai' package is required for OpenAIImageProvider."
                ) from exc
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: AspectRatio,
        quality: ImageQuality,
        output_path: Path,
    ) -> Path:
        client = self._get_client()
        size = _SIZE_FOR_RATIO[aspect_ratio]

        try:
            response = client.images.generate(
                model=self._model,
                prompt=prompt,
                size=size,
                quality=quality.value,
                n=1,
            )
        except Exception as exc:  # the SDK raises many error subclasses
            raise ImageError(f"OpenAI image generation failed: {exc}") from exc

        image_bytes = _decode_first_image(response)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        logger.info("Generated illustration: %s (%s, %s)", output_path, size, quality.value)
        return output_path


def _decode_first_image(response: object) -> bytes:
    """Extract and decode the first image's base64 payload from a response."""
    data = getattr(response, "data", None)
    if not data:
        raise ImageError("OpenAI image generation returned no image data.")

    b64 = getattr(data[0], "b64_json", None)
    if not b64:
        raise ImageError("OpenAI image generation returned no base64 image content.")

    try:
        return base64.b64decode(b64)
    except (ValueError, TypeError) as exc:
        raise ImageError(f"OpenAI image generation returned invalid base64: {exc}") from exc
