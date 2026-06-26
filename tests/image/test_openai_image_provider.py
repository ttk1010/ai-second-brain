"""Tests for the OpenAI image provider (Issue #13), with a fake API client."""

import base64
from pathlib import Path

import pytest

from backend.image import ImageError, OpenAIImageProvider
from backend.models.enums import AspectRatio, ImageQuality

PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-image-content"


class _FakeImage:
    def __init__(self, b64: str | None) -> None:
        self.b64_json = b64


class _FakeResponse:
    def __init__(self, data: list[_FakeImage]) -> None:
        self.data = data


class _FakeImages:
    def __init__(self, response: _FakeResponse | None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.calls: list[dict] = []

    def generate(self, **kwargs: object) -> _FakeResponse:
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


class _FakeClient:
    def __init__(self, images: _FakeImages) -> None:
        self.images = images


def _client(b64: str | None = None, *, error: Exception | None = None) -> _FakeClient:
    payload = base64.b64encode(PNG_BYTES).decode() if b64 is None else b64
    response = _FakeResponse([_FakeImage(payload)])
    return _FakeClient(_FakeImages(response, error=error))


def test_generate_writes_decoded_image(tmp_path: Path) -> None:
    client = _client()
    provider = OpenAIImageProvider(client=client)
    out = tmp_path / "nested" / "img.png"

    result = provider.generate(
        "a diagram",
        aspect_ratio=AspectRatio.WIDE,
        quality=ImageQuality.MEDIUM,
        output_path=out,
    )

    assert result == out
    assert out.read_bytes() == PNG_BYTES  # decoded base64 written verbatim
    # Aspect ratio and quality are translated for the API.
    call = client.images.calls[0]
    assert call["size"] == "1536x1024"
    assert call["quality"] == "medium"
    assert call["model"] == "gpt-image-2"


@pytest.mark.parametrize(
    ("ratio", "size"),
    [
        (AspectRatio.WIDE, "1536x1024"),
        (AspectRatio.STANDARD, "1536x1024"),
        (AspectRatio.SQUARE, "1024x1024"),
        (AspectRatio.TALL, "1024x1536"),
    ],
)
def test_aspect_ratio_maps_to_size(tmp_path: Path, ratio: AspectRatio, size: str) -> None:
    client = _client()
    OpenAIImageProvider(client=client).generate(
        "x",
        aspect_ratio=ratio,
        quality=ImageQuality.LOW,
        output_path=tmp_path / "img.png",
    )
    assert client.images.calls[0]["size"] == size


def test_generate_wraps_api_errors(tmp_path: Path) -> None:
    provider = OpenAIImageProvider(client=_client(error=RuntimeError("boom")))
    with pytest.raises(ImageError, match="image generation failed"):
        provider.generate(
            "x",
            aspect_ratio=AspectRatio.WIDE,
            quality=ImageQuality.HIGH,
            output_path=tmp_path / "img.png",
        )


def test_generate_rejects_empty_data(tmp_path: Path) -> None:
    provider = OpenAIImageProvider(client=_FakeClient(_FakeImages(_FakeResponse([]))))
    with pytest.raises(ImageError, match="no image data"):
        provider.generate(
            "x",
            aspect_ratio=AspectRatio.WIDE,
            quality=ImageQuality.HIGH,
            output_path=tmp_path / "img.png",
        )


def test_generate_rejects_missing_b64(tmp_path: Path) -> None:
    provider = OpenAIImageProvider(client=_client(b64=""))
    with pytest.raises(ImageError, match="no base64"):
        provider.generate(
            "x",
            aspect_ratio=AspectRatio.WIDE,
            quality=ImageQuality.HIGH,
            output_path=tmp_path / "img.png",
        )
