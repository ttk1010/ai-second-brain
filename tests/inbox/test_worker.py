"""Tests for the Inbox worker (Issue #26), with a fake pipeline."""

from pathlib import Path

from backend.inbox import InboxWorker
from backend.services import PipelineResult


class _FakePipeline:
    """Records inputs and returns a status per input (default 'created')."""

    def __init__(self, behavior: dict[str, str] | None = None) -> None:
        self.behavior = behavior or {}
        self.calls: list[str] = []

    def run(self, raw_input: str, *, overwrite: bool = False) -> PipelineResult:
        self.calls.append(raw_input)
        status = self.behavior.get(raw_input, "created")
        if status == "raise":
            raise RuntimeError("boom")
        return PipelineResult(status=status, message="", path=None)


def _stub(inbox: Path, name: str, content: str) -> Path:
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / name
    path.write_text(content, encoding="utf-8")
    return path


def test_processes_and_consumes_stubs(tmp_path: Path) -> None:
    inbox = tmp_path / "00 Inbox"
    _stub(inbox, "a.md", "Transformer")
    _stub(inbox, "b.md", "https://example.com/news")
    pipeline = _FakePipeline()

    summary = InboxWorker(pipeline, inbox).process_all()

    assert summary.created == 2
    assert sorted(pipeline.calls) == ["Transformer", "https://example.com/news"]
    # Consumed: stubs removed on success.
    assert list(inbox.glob("*.md")) == []


def test_extracts_first_meaningful_line(tmp_path: Path) -> None:
    inbox = tmp_path / "00 Inbox"
    # Frontmatter + a markdown heading; the input is the heading text.
    _stub(inbox, "note.md", "---\ntags: []\n---\n\n# Diffusion Model\n\nsome body\n")
    pipeline = _FakePipeline()

    InboxWorker(pipeline, inbox).process_all()
    assert pipeline.calls == ["Diffusion Model"]


def test_existing_note_is_consumed_as_skipped(tmp_path: Path) -> None:
    inbox = tmp_path / "00 Inbox"
    _stub(inbox, "a.md", "Transformer")
    pipeline = _FakePipeline({"Transformer": "exists"})

    summary = InboxWorker(pipeline, inbox).process_all()
    assert summary.skipped == 1
    assert list(inbox.glob("*.md")) == []  # still consumed


def test_failure_leaves_stub_in_place(tmp_path: Path) -> None:
    inbox = tmp_path / "00 Inbox"
    _stub(inbox, "a.md", "Transformer")
    pipeline = _FakePipeline({"Transformer": "raise"})

    summary = InboxWorker(pipeline, inbox).process_all()
    assert summary.failed == 1
    assert (inbox / "a.md").exists()  # left for retry


def test_unsupported_leaves_stub_in_place(tmp_path: Path) -> None:
    inbox = tmp_path / "00 Inbox"
    _stub(inbox, "a.md", "http://")
    pipeline = _FakePipeline({"http://": "unsupported"})

    summary = InboxWorker(pipeline, inbox).process_all()
    assert summary.unsupported == 1
    assert (inbox / "a.md").exists()


def test_empty_stub_falls_back_to_filename(tmp_path: Path) -> None:
    inbox = tmp_path / "00 Inbox"
    _stub(inbox, "MCP.md", "")  # empty body -> use filename stem
    pipeline = _FakePipeline()

    InboxWorker(pipeline, inbox).process_all()
    assert pipeline.calls == ["MCP"]


def test_missing_inbox_is_noop(tmp_path: Path) -> None:
    summary = InboxWorker(_FakePipeline(), tmp_path / "nope").process_all()
    assert summary == summary.__class__()
