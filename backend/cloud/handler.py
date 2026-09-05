"""AWS Lambda handler for instant on-the-go generation (Issue #42, ADR 0015).

Invoked synchronously via a **Lambda Function URL** (chosen over API Gateway to
avoid its ~29s timeout; image generation can take tens of seconds). The request
carries ``{input, guidance?, pages?}``; the handler runs the existing ``backend/``
pipeline against an ephemeral ``/tmp`` Vault, commits the note + illustration to a
GitHub-backed Vault, and returns the PNG so the phone shows it immediately.

Design goals:
- **Reuse:** the pipeline, prompts and Knowledge Object are untouched; only the
  entry point and the GitHub persistence are new.
- **Testable:** auth secret, the pipeline factory and the publisher are injected,
  so the handler is unit-tested with no AWS, OpenAI or network access.

Auth is a shared secret (``Authorization: Bearer <secret>``); the Function URL is
public (``AuthType: NONE``) and this handler verifies the token (ADR 0015).
"""

import base64
import hmac
import json
import logging
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from backend.cloud.github_publisher import GitHubPublisher, PublishError
from backend.config import Settings
from backend.models import KnowledgeObject
from backend.planner import PagesOption
from backend.services import KnowledgePipeline, build_pipeline

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cost guard: cap illustration pages per request (ADR 0015 / Issue #42).
MAX_PAGES = 3

PipelineFactory = Callable[[Path], KnowledgePipeline]


@dataclass
class Handler:
    """Handles one Function URL request. Dependencies are injected for testing."""

    auth_secret: str
    publisher: GitHubPublisher
    pipeline_factory: PipelineFactory

    def handle(self, event: dict) -> dict:
        method = event.get("requestContext", {}).get("http", {}).get("method", "POST")
        if method.upper() != "POST":
            return _json(405, {"error": "Use POST."})
        if not self._authorized(event):
            return _json(401, {"error": "Unauthorized."})

        try:
            payload = _parse_body(event)
        except ValueError as exc:
            return _json(400, {"error": str(exc)})

        input_text = str(payload.get("input") or "").strip()
        if not input_text:
            return _json(400, {"error": "'input' is required."})
        guidance = str(payload.get("guidance") or "").strip()
        pages = _parse_pages(payload.get("pages"))

        vault = Path(tempfile.mkdtemp(prefix="asb-vault-"))
        pipeline = self.pipeline_factory(vault)
        try:
            result = pipeline.run(input_text, guidance=guidance, pages=pages)
        except Exception as exc:  # noqa: BLE001 - report a clean message to the caller
            logger.exception("Generation failed")
            return _json(500, {"error": f"Generation failed: {exc}"})

        if result.status != "created" or result.knowledge_object is None:
            return _json(422, {"status": result.status, "message": result.message})

        ko = result.knowledge_object
        files = _collect_files(vault, ko)
        try:
            commit = self.publisher.publish(files, f"Add note: {ko.title}")
        except PublishError:
            # The note was generated; persistence failed. Still return the image so
            # the user sees the result, flagged so it can be retried/saved later.
            logger.exception("Publish to GitHub failed")
            return _respond(vault, ko, warning="publish-failed")

        return _respond(vault, ko, commit=commit)

    def _authorized(self, event: dict) -> bool:
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        auth = headers.get("authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        return bool(token) and hmac.compare_digest(token, self.auth_secret)


def _parse_body(event: dict) -> dict:
    body = event.get("body")
    if not body:
        return {}
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON body: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def _parse_pages(value: object) -> PagesOption:
    if value == "auto":
        return "auto"
    if value in (None, "", 1, "1"):
        return None
    try:
        count = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return max(1, min(count, MAX_PAGES))


def _illustration_paths(ko: KnowledgeObject) -> list[str]:
    if ko.illustrations:
        return ko.illustrations
    single = ko.outputs.get("illustration")
    return [single] if single else []


def _collect_files(vault: Path, ko: KnowledgeObject) -> dict[str, bytes]:
    """Read the note + illustration(s) produced in the temp Vault, keyed by repo path."""
    files: dict[str, bytes] = {}
    note = ko.outputs.get("markdown")
    if note:
        files[note] = (vault / note).read_bytes()
    for image in _illustration_paths(ko):
        files[image] = (vault / image).read_bytes()
    return files


def _respond(
    vault: Path, ko: KnowledgeObject, *, commit: str | None = None, warning: str | None = None
) -> dict:
    """Return the first illustration as PNG (so the phone previews it), else JSON."""
    images = _illustration_paths(ko)
    if images:
        data = (vault / images[0]).read_bytes()
        headers = {"Content-Type": "image/png"}
        if commit:
            headers["X-ASB-Commit"] = commit
        if warning:
            headers["X-ASB-Warning"] = warning
        return {
            "statusCode": 200,
            "headers": headers,
            "body": base64.b64encode(data).decode("ascii"),
            "isBase64Encoded": True,
        }
    payload: dict[str, object] = {"status": "created", "title": ko.title}
    if commit:
        payload["commit"] = commit
    if warning:
        payload["warning"] = warning
    return _json(200, payload)


def _json(status: int, obj: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(obj, ensure_ascii=False),
    }


def _default_pipeline_factory(vault: Path) -> KnowledgePipeline:
    vault.mkdir(parents=True, exist_ok=True)
    settings = Settings(vault_path=vault)
    return build_pipeline(settings, no_image=False)


def lambda_handler(event: dict, context: object = None) -> dict:
    """AWS Lambda entry point (configured as the container CMD)."""
    handler = Handler(
        auth_secret=os.environ["ASB_AUTH_SECRET"],
        publisher=GitHubPublisher(
            os.environ["GITHUB_REPO"],
            os.environ["GITHUB_TOKEN"],
            branch=os.environ.get("GITHUB_BRANCH", "main"),
        ),
        pipeline_factory=_default_pipeline_factory,
    )
    return handler.handle(event)
