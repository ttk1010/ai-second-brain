"""Tests for the IllustrationWriter (Issue #14), with a fake image provider."""

from pathlib import Path

import pytest

from backend.image.base import ImageError, ImageProvider
from backend.models import (
    AspectRatio,
    EducationalPlan,
    ImageQuality,
    KnowledgeObject,
    Source,
    SourceType,
    VisualizationStrategy,
)
from backend.storage import IllustrationWriter


class _FakeImageProvider(ImageProvider):
    """Records calls and writes placeholder bytes (or raises)."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict] = []

    def generate(self, prompt, *, aspect_ratio, quality, output_path) -> Path:
        self.calls.append(
            {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "output_path": output_path,
            }
        )
        if self.error is not None:
            raise self.error
        output_path.write_bytes(b"image-bytes")
        return output_path


def _ko(*, plan: EducationalPlan | None = None) -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture based on self-attention.",
        concepts=["attention"],
        educational_plan=plan,
    )


def _plan(ratio: AspectRatio) -> EducationalPlan:
    return EducationalPlan(
        learning_objective="Understand self-attention.",
        target_audience="Engineers.",
        visualization_strategy=VisualizationStrategy(aspect_ratio=ratio),
    )


def test_write_saves_image_and_records_reference(tmp_path: Path) -> None:
    provider = _FakeImageProvider()
    writer = IllustrationWriter(tmp_path, provider, image_output_dir="Images")
    ko = _ko(plan=_plan(AspectRatio.SQUARE))

    result = writer.write(ko)

    assert result == tmp_path / "Images" / "Transformer.png"
    assert result.read_bytes() == b"image-bytes"
    # Vault-relative reference recorded (posix), never an absolute path.
    assert ko.outputs["illustration"] == "Images/Transformer.png"
    # Aspect ratio comes from the Educational Plan.
    assert provider.calls[0]["aspect_ratio"] is AspectRatio.SQUARE


def test_write_uses_default_aspect_ratio_without_plan(tmp_path: Path) -> None:
    provider = _FakeImageProvider()
    writer = IllustrationWriter(tmp_path, provider, default_aspect_ratio=AspectRatio.TALL)
    writer.write(_ko(plan=None))
    assert provider.calls[0]["aspect_ratio"] is AspectRatio.TALL


def test_write_passes_quality(tmp_path: Path) -> None:
    provider = _FakeImageProvider()
    writer = IllustrationWriter(tmp_path, provider, quality=ImageQuality.HIGH)
    writer.write(_ko())
    assert provider.calls[0]["quality"] is ImageQuality.HIGH


def test_write_avoids_overwriting_existing_image(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider())
    first = writer.write(_ko())
    second = writer.write(_ko())
    assert first.name == "Transformer.png"
    assert second.name == "Transformer-2.png"


def test_write_overwrite_reuses_path(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider())
    first = writer.write(_ko())
    second = writer.write(_ko(), overwrite=True)
    assert first == second


def test_write_propagates_image_errors(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider(error=ImageError("boom")))
    with pytest.raises(ImageError):
        writer.write(_ko())
