"""Tests for the IllustrationWriter (Issue #14), with a fake image provider."""

from pathlib import Path

import pytest

from backend.image.base import ImageError, ImageProvider
from backend.models import (
    AspectRatio,
    EducationalPlan,
    ImageQuality,
    KnowledgeObject,
    PageSpec,
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

    def generate(
        self, prompt, *, aspect_ratio, quality, output_path, reference_images=None
    ) -> Path:
        self.calls.append(
            {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "output_path": output_path,
                "reference_images": reference_images,
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

    assert result == [tmp_path / "Images" / "Transformer.png"]
    assert result[0].read_bytes() == b"image-bytes"
    # Vault-relative reference recorded (posix), never an absolute path.
    assert ko.outputs["illustration"] == "Images/Transformer.png"
    assert ko.illustrations == ["Images/Transformer.png"]
    # Aspect ratio comes from the Educational Plan.
    assert provider.calls[0]["aspect_ratio"] is AspectRatio.SQUARE
    # A single image gets no reference (no series to stay consistent with).
    assert provider.calls[0]["reference_images"] is None


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
    assert first[0].name == "Transformer.png"
    assert second[0].name == "Transformer-2.png"


def test_write_overwrite_reuses_path(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider())
    first = writer.write(_ko())
    second = writer.write(_ko(), overwrite=True)
    assert first == second


def test_write_propagates_image_errors(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider(error=ImageError("boom")))
    with pytest.raises(ImageError):
        writer.write(_ko())


# --- Multi-page series (Issue #41) ------------------------------------------


def _page(title: str, ratio: AspectRatio = AspectRatio.WIDE) -> PageSpec:
    return PageSpec(title=title, learning_objective=f"Teach {title}.", aspect_ratio=ratio)


def _plan_with_pages(*titles: str) -> EducationalPlan:
    plan = _plan(AspectRatio.WIDE)
    plan.pages = [_page(t) for t in titles]
    return plan


def test_write_multipage_generates_one_image_per_page(tmp_path: Path) -> None:
    provider = _FakeImageProvider()
    writer = IllustrationWriter(tmp_path, provider, image_output_dir="Images")
    ko = _ko(plan=_plan_with_pages("Overview", "Mechanism", "Example"))

    result = writer.write(ko)

    names = [p.name for p in result]
    assert names == ["Transformer.png", "Transformer-p2.png", "Transformer-p3.png"]
    # Ordered references recorded; outputs['illustration'] mirrors the first page.
    assert ko.illustrations == [
        "Images/Transformer.png",
        "Images/Transformer-p2.png",
        "Images/Transformer-p3.png",
    ]
    assert ko.outputs["illustration"] == "Images/Transformer.png"
    assert len(provider.calls) == 3


def test_write_multipage_anchors_later_pages_to_first(tmp_path: Path) -> None:
    provider = _FakeImageProvider()
    writer = IllustrationWriter(tmp_path, provider, image_output_dir="Images")
    ko = _ko(plan=_plan_with_pages("Overview", "Mechanism", "Example"))

    writer.write(ko)

    first_target = tmp_path / "Images" / "Transformer.png"
    # Page 1 has no reference; every later page is anchored to page 1's style.
    assert provider.calls[0]["reference_images"] is None
    assert provider.calls[1]["reference_images"] == [first_target]
    assert provider.calls[2]["reference_images"] == [first_target]


def test_write_multipage_overwrite_cleans_shrunk_series(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider(), image_output_dir="Images")
    writer.write(_ko(plan=_plan_with_pages("A", "B", "C", "D")))
    folder = tmp_path / "Images"
    assert (folder / "Transformer-p4.png").exists()

    # Regenerate as a shorter series: orphaned pages must be removed.
    writer.write(_ko(plan=_plan_with_pages("A", "B")), overwrite=True)
    assert (folder / "Transformer.png").exists()
    assert (folder / "Transformer-p2.png").exists()
    assert not (folder / "Transformer-p3.png").exists()
    assert not (folder / "Transformer-p4.png").exists()


def test_write_overwrite_single_cleans_previous_pages(tmp_path: Path) -> None:
    writer = IllustrationWriter(tmp_path, _FakeImageProvider(), image_output_dir="Images")
    writer.write(_ko(plan=_plan_with_pages("A", "B", "C")))
    folder = tmp_path / "Images"
    assert (folder / "Transformer-p2.png").exists()

    # Regenerate as a single image: the old extra pages must be removed.
    writer.write(_ko(plan=_plan(AspectRatio.WIDE)), overwrite=True)
    assert (folder / "Transformer.png").exists()
    assert not (folder / "Transformer-p2.png").exists()
    assert not (folder / "Transformer-p3.png").exists()
