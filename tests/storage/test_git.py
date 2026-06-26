"""Tests for optional Vault Git versioning (Issue #10)."""

import subprocess
from pathlib import Path

from backend.storage.git import commit_note, is_git_repo


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def test_is_git_repo_false_for_plain_dir(tmp_path: Path) -> None:
    assert is_git_repo(tmp_path) is False


def test_is_git_repo_true_after_init(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    assert is_git_repo(tmp_path) is True


def test_commit_note_in_repo(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    note = tmp_path / "note.md"
    note.write_text("# Note\n", encoding="utf-8")

    assert commit_note(tmp_path, note, "Add note: Note") is True

    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert "Add note: Note" in log.stdout


def test_commit_note_skips_non_repo(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("# Note\n", encoding="utf-8")
    assert commit_note(tmp_path, note, "msg") is False
