"""Tests for optional Vault Git versioning (Issue #10, extended by Issue #44)."""

import subprocess
from pathlib import Path

from backend.storage.git import commit_note, is_git_repo, push_vault, sync_vault


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def _clone_with_remote(tmp_path: Path) -> Path:
    """A working clone whose origin is a local bare repository with one commit."""
    remote = tmp_path / "remote.git"
    remote.mkdir()
    subprocess.run(
        ["git", "init", "--bare", "--initial-branch=main"],
        cwd=remote,
        capture_output=True,
        check=True,
    )
    seed = tmp_path / "seed"
    seed.mkdir()
    _init_repo(seed)
    (seed / "seed.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "checkout", "-b", "main"], cwd=seed, capture_output=True, check=True)
    subprocess.run(["git", "add", "seed.md"], cwd=seed, check=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=seed, capture_output=True, check=True)
    subprocess.run(["git", "push", str(remote), "main"], cwd=seed, capture_output=True, check=True)
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", str(remote), str(clone)], cwd=tmp_path, capture_output=True, check=True
    )
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=clone, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=clone, check=True)
    return clone


def _log(path: Path) -> str:
    return subprocess.run(
        ["git", "log", "--oneline"], cwd=path, capture_output=True, text=True, check=True
    ).stdout


def test_is_git_repo_false_for_plain_dir(tmp_path: Path) -> None:
    assert is_git_repo(tmp_path) is False


def test_is_git_repo_true_after_init(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    assert is_git_repo(tmp_path) is True


def test_commit_note_stages_note_and_illustrations_together(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    note = tmp_path / "note.md"
    note.write_text("# Note\n", encoding="utf-8")
    images = tmp_path / "Images"
    images.mkdir()
    page1 = images / "note.png"
    page2 = images / "note-p2.png"
    page1.write_bytes(b"png1")
    page2.write_bytes(b"png2")

    assert commit_note(tmp_path, [note, page1, page2], "Add note: Note") is True

    assert "Add note: Note" in _log(tmp_path)
    shown = subprocess.run(
        ["git", "show", "--name-only", "--format="],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "note.md" in shown
    assert "Images/note.png" in shown
    assert "Images/note-p2.png" in shown


def test_commit_note_stages_a_deletion(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    stub = tmp_path / "stub.md"
    stub.write_text("stub\n", encoding="utf-8")
    assert commit_note(tmp_path, [stub], "Add stub") is True

    stub.unlink()
    assert commit_note(tmp_path, [stub], "Consume inbox stub: stub.md") is True
    assert "Consume inbox stub" in _log(tmp_path)


def test_commit_note_skips_non_repo(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("# Note\n", encoding="utf-8")
    assert commit_note(tmp_path, [note], "msg") is False


def test_commit_note_skips_empty_paths(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    assert commit_note(tmp_path, [], "msg") is False


def test_sync_vault_pulls_remote_commits(tmp_path: Path) -> None:
    clone = _clone_with_remote(tmp_path)
    other = tmp_path / "other"
    subprocess.run(
        ["git", "clone", str(tmp_path / "remote.git"), str(other)],
        capture_output=True,
        check=True,
    )
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=other, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=other, check=True)
    (other / "remote-note.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "remote-note.md"], cwd=other, check=True)
    subprocess.run(
        ["git", "commit", "-m", "remote note"], cwd=other, capture_output=True, check=True
    )
    subprocess.run(["git", "push"], cwd=other, capture_output=True, check=True)

    assert sync_vault(clone) is True
    assert (clone / "remote-note.md").exists()


def test_sync_vault_false_for_non_repo(tmp_path: Path) -> None:
    assert sync_vault(tmp_path) is False


def test_push_vault_pushes_local_commit(tmp_path: Path) -> None:
    clone = _clone_with_remote(tmp_path)
    (clone / "local-note.md").write_text("y\n", encoding="utf-8")
    assert commit_note(clone, [clone / "local-note.md"], "Add note: local") is True

    assert push_vault(clone) is True

    remote_log = subprocess.run(
        ["git", "log", "--oneline", "main"],
        cwd=tmp_path / "remote.git",
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "Add note: local" in remote_log


def test_push_vault_false_without_remote(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "a.md").write_text("a\n", encoding="utf-8")
    commit_note(tmp_path, [tmp_path / "a.md"], "Add a")
    assert push_vault(tmp_path) is False


def test_push_vault_false_for_non_repo(tmp_path: Path) -> None:
    assert push_vault(tmp_path) is False
