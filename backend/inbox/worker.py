"""Process the Vault's 00 Inbox queue into notes.

Each stub in ``00 Inbox/`` holds a URL or concept (the first non-empty line), or
captured article content — a ``source:`` URL in the frontmatter plus the article
body text, for login-required sites the fetcher cannot reach (Issue #38). The
worker runs each through the pipeline and, on success, consumes (deletes) the
stub — the real note is written under 01 Concepts / 06 News. Failures are left
in place for a later retry and are logged (no silent failures). Generation is
idempotent (#24), so re-running is safe.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from backend.parser.fetcher import FetchedArticle
from backend.services import KnowledgePipeline

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InboxSummary:
    """Counts from one inbox processing run."""

    created: int = 0
    skipped: int = 0  # note already existed
    unsupported: int = 0
    failed: int = 0


class InboxWorker:
    """Processes URL/concept stubs from an inbox directory."""

    def __init__(
        self,
        pipeline: KnowledgePipeline,
        inbox_dir: Path,
        *,
        overwrite: bool = False,
    ) -> None:
        self._pipeline = pipeline
        self._inbox_dir = inbox_dir
        self._overwrite = overwrite

    def process_all(self) -> InboxSummary:
        """Process every ``*.md`` stub in the inbox directory once."""
        if not self._inbox_dir.is_dir():
            return InboxSummary()

        created = skipped = unsupported = failed = 0
        for stub in sorted(self._inbox_dir.glob("*.md")):
            captured = _parse_captured(stub)
            raw = "" if captured is not None else _extract_input(stub)
            if captured is None and not raw:
                logger.warning("Empty inbox stub, leaving in place: %s", stub.name)
                failed += 1
                continue

            try:
                if captured is not None:
                    result = self._pipeline.run_captured(
                        captured.url,
                        captured.text,
                        title=captured.title,
                        overwrite=self._overwrite,
                    )
                else:
                    result = self._pipeline.run(raw, overwrite=self._overwrite)
            except Exception as exc:  # noqa: BLE001 - one bad stub must not stop the rest
                logger.warning("Failed to process inbox stub %s: %s", stub.name, exc)
                failed += 1
                continue

            if result.status in ("created", "exists"):
                stub.unlink()  # consume the queue item
                if result.status == "created":
                    created += 1
                else:
                    skipped += 1
            else:  # unsupported
                logger.warning("Unsupported inbox input in %s: %r", stub.name, raw)
                unsupported += 1

        return InboxSummary(
            created=created, skipped=skipped, unsupported=unsupported, failed=failed
        )


def _parse_captured(stub: Path) -> FetchedArticle | None:
    """Parse a captured-article stub, or None when the stub is not one.

    A captured stub carries a ``source:`` URL in its frontmatter plus the article
    body text below (Issue #38). The body is what the user copied from their own
    logged-in browser, so the fetch step is skipped.
    """
    text = stub.read_text(encoding="utf-8")
    front = _parse_frontmatter(text)
    source = front.get("source", "").strip()
    if not _URL_RE.match(source):
        return None
    body = _strip_frontmatter(text).strip()
    if not body:
        return None
    title = front.get("title", "").strip()
    return FetchedArticle(url=source, title=title or source, text=body)


def _extract_input(stub: Path) -> str:
    """Read the capture input from a stub: first non-empty body line, else stem."""
    text = stub.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)
    for line in body.splitlines():
        cleaned = line.strip().lstrip("#-*> ").strip()
        if cleaned:
            return cleaned
    return stub.stem


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse simple ``key: value`` pairs from a leading YAML frontmatter block."""
    if not text.startswith("---"):
        return {}
    parts = text.split("\n", 1)
    if len(parts) < 2:
        return {}
    end = parts[1].find("\n---")
    if end == -1:
        return {}
    front: dict[str, str] = {}
    for line in parts[1][:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip():
            front[key.strip()] = value.strip()
    return front


def _strip_frontmatter(text: str) -> str:
    """Return the note body with any leading YAML frontmatter removed."""
    if not text.startswith("---"):
        return text
    parts = text.split("\n", 1)
    if len(parts) < 2:
        return text
    end = parts[1].find("\n---")
    if end == -1:
        return text
    return parts[1][end + 4 :]
