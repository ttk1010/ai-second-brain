"""Tests for the Lambda Function URL handler (Issue #42), fully mocked."""

import base64
import json
from pathlib import Path

from backend.cloud.github_publisher import PublishError
from backend.cloud.handler import Handler, cloud_settings
from backend.models import (
    IllustrationStyle,
    ImageQuality,
    KnowledgeObject,
    Source,
    SourceType,
)
from backend.services.pipeline import PipelineResult

SECRET = "s3cret"


class _FakePipeline:
    """Writes a note + image into the given Vault and records the run args."""

    def __init__(self, vault: Path, *, status: str = "created") -> None:
        self.vault = vault
        self.status = status
        self.seen: dict | None = None

    def run(
        self, input_text, *, overwrite=False, guidance="", pages=None, plan=True
    ) -> PipelineResult:
        self.seen = {"input": input_text, "guidance": guidance, "pages": pages, "plan": plan}
        if self.status != "created":
            return PipelineResult(status=self.status, message="unsupported")
        note, image = "01 Concepts/Test.md", "Images/Test.png"
        (self.vault / "01 Concepts").mkdir(parents=True, exist_ok=True)
        (self.vault / "Images").mkdir(parents=True, exist_ok=True)
        (self.vault / note).write_text("# Test\n", encoding="utf-8")
        (self.vault / image).write_bytes(b"PNGDATA")
        ko = KnowledgeObject(
            source=Source(type=SourceType.CONCEPT, value=input_text), title="Test", summary="s"
        )
        ko.outputs = {"markdown": note, "illustration": image}
        ko.illustrations = [image]
        return PipelineResult(
            status="created", message="ok", knowledge_object=ko, path=self.vault / note
        )


class _FakePublisher:
    def __init__(self, *, error: bool = False) -> None:
        self.error = error
        self.files: dict | None = None
        self.message: str | None = None

    def publish(self, files, message) -> str:
        if self.error:
            raise PublishError("boom")
        self.files, self.message = files, message
        return "abc1234"


def _event(*, secret: str = SECRET, body: dict | None = None, method: str = "POST") -> dict:
    event: dict = {
        "requestContext": {"http": {"method": method}},
        "headers": {"authorization": f"Bearer {secret}"},
    }
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def _handler(*, publisher=None, status="created"):
    holder: dict = {}

    def factory(vault: Path):
        pipeline = _FakePipeline(vault, status=status)
        holder["pipeline"] = pipeline
        return pipeline

    handler = Handler(
        auth_secret=SECRET,
        publisher=publisher or _FakePublisher(),
        pipeline_factory=factory,
    )
    return handler, holder


def test_generates_commits_and_returns_png() -> None:
    publisher = _FakePublisher()
    handler, holder = _handler(publisher=publisher)

    resp = handler.handle(_event(body={"input": "Transformer"}))

    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "image/png"
    assert resp["isBase64Encoded"] is True
    assert base64.b64decode(resp["body"]) == b"PNGDATA"
    assert resp["headers"]["X-ASB-Commit"] == "abc1234"
    # Both the note and the image were committed in one publish call.
    assert set(publisher.files.keys()) == {"01 Concepts/Test.md", "Images/Test.png"}
    assert publisher.message == "Add note: Test"
    assert holder["pipeline"].seen["input"] == "Transformer"
    # The cloud path skips the Educational Planner for latency (Issue #42).
    assert holder["pipeline"].seen["plan"] is False


def test_pages_clamped_to_max() -> None:
    handler, holder = _handler()
    handler.handle(_event(body={"input": "X", "pages": 9}))
    assert holder["pipeline"].seen["pages"] == 3


def test_pages_auto_passthrough() -> None:
    handler, holder = _handler()
    handler.handle(_event(body={"input": "X", "pages": "auto"}))
    assert holder["pipeline"].seen["pages"] == "auto"


def test_guidance_forwarded() -> None:
    handler, holder = _handler()
    handler.handle(_event(body={"input": "X", "guidance": "高校生向けに"}))
    assert holder["pipeline"].seen["guidance"] == "高校生向けに"


def test_unauthorized_rejected() -> None:
    handler, _ = _handler()
    assert handler.handle(_event(secret="wrong", body={"input": "X"}))["statusCode"] == 401


def test_non_post_rejected() -> None:
    handler, _ = _handler()
    assert handler.handle(_event(body={"input": "X"}, method="GET"))["statusCode"] == 405


def test_missing_input_is_400() -> None:
    handler, _ = _handler()
    assert handler.handle(_event(body={}))["statusCode"] == 400


def test_unsupported_result_is_422() -> None:
    handler, _ = _handler(status="unsupported")
    assert handler.handle(_event(body={"input": "???"}))["statusCode"] == 422


def test_publish_failure_still_returns_image() -> None:
    handler, _ = _handler(publisher=_FakePublisher(error=True))
    resp = handler.handle(_event(body={"input": "X"}))
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "image/png"
    assert resp["headers"]["X-ASB-Warning"] == "publish-failed"


def test_cloud_settings_use_the_fast_image_model(tmp_path: Path) -> None:
    """Issue #45 / ADR 0016: flare high keeps gpt-image-2 medium's detail at ~2x speed,
    with the explicit wording so it stays hand-drawn."""
    settings = cloud_settings(tmp_path)
    assert settings.image_model == "gpt-image-2.5-flare"
    assert settings.image_quality is ImageQuality.HIGH
    assert settings.illustration_style is IllustrationStyle.EXPLICIT_HAND_DRAWN
