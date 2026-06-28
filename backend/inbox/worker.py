"""Process the Vault's 00 Inbox queue into notes.

Each stub in ``00 Inbox/`` holds a URL or concept (the first non-empty line).
The worker runs it through the pipeline and, on success, consumes (deletes) the
stub — the real note is written under 01 Concepts / 06 News. Failures are left
in place for a later retry and are logged (no silent failures). Generation is
idempotent (#24), so re-running is safe.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from backend.services import KnowledgePipeline

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
            raw = _extract_input(stub)
            if not raw:
                logger.warning("Empty inbox stub, leaving in place: %s", stub.name)
                failed += 1
                continue

            try:
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


def _extract_input(stub: Path) -> str:
    """Read the capture input from a stub: first non-empty body line, else stem."""
    text = stub.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)
    for line in body.splitlines():
        cleaned = line.strip().lstrip("#-*> ").strip()
        if cleaned:
            return cleaned
    return stub.stem


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
