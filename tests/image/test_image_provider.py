"""Tests for the ImageProvider interface (Issue #7, Phase 1 = interface only)."""

from pathlib import Path

from backend.image import ImageProvider
from backend.models.enums import AspectRatio, ImageQuality


def test_image_provider_is_abstract() -> None:
    # The interface exists but cannot be instantiated directly in Phase 1.
    try:
        ImageProvider()  # type: ignore[abstract]
    except TypeError:
        return
    raise AssertionError("ImageProvider should be abstract")


def test_concrete_provider_can_implement_interface(tmp_path: Path) -> None:
    class FakeImageProvider(ImageProvider):
        def generate(
            self,
            prompt: str,
            *,
            aspect_ratio: AspectRatio,
            quality: ImageQuality,
            output_path: Path,
        ) -> Path:
            output_path.write_bytes(b"fake")
            return output_path

    out = tmp_path / "img.png"
    result = FakeImageProvider().generate(
        "a diagram",
        aspect_ratio=AspectRatio.WIDE,
        quality=ImageQuality.MEDIUM,
        output_path=out,
    )
    assert result == out
    assert out.exists()
