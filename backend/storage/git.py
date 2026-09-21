"""Optional Git versioning of the external Vault (ADR 0002).

When the external Vault is itself a Git repository and ``auto_commit`` is enabled,
generated notes are committed there — the note together with its illustration
pages, in one commit (Issue #44). With ``auto_push`` the Vault is also rebased on
and pushed to its remote, so every generation route ends in the same place:
origin/main. This is distinct from this code repository's Git. Implemented with
subprocess to avoid an extra dependency. All operations are best-effort: a git
failure is logged, never raised, and never fails the generation itself.
"""

import logging
import subprocess
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)


def is_git_repo(path: Path) -> bool:
    """Return True if ``path`` is inside a Git working tree."""
    result = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return result is not None and result.returncode == 0 and result.stdout.strip() == "true"


def commit_note(vault_path: Path, paths: Iterable[Path], message: str) -> bool:
    """Stage ``paths`` (files and deletions) and commit them within the Vault.

    Returns True if a commit was made, False if skipped (not a repo, git
    unavailable, or nothing to commit). Never raises — versioning is best-effort.
    """
    if not is_git_repo(vault_path):
        logger.warning("Vault is not a Git repository; skipping auto_commit: %s", vault_path)
        return False

    path_args = [str(p) for p in paths]
    if not path_args:
        return False
    add = _run(["git", "add", "--", *path_args], cwd=vault_path)
    if add is None or add.returncode != 0:
        logger.warning("git add failed; skipping commit.")
        return False

    commit = _run(["git", "commit", "-m", message], cwd=vault_path)
    if commit is None or commit.returncode != 0:
        logger.warning("git commit failed or nothing to commit.")
        return False

    logger.info("Committed to Vault repository: %s", ", ".join(path_args))
    return True


def sync_vault(vault_path: Path) -> bool:
    """Rebase the Vault onto its remote (``git pull --rebase``).

    Run before generating so the idempotency check sees notes pushed by other
    routes (Lambda, GitHub Actions). Returns True on success; False (with a
    warning) when the Vault is not a repo, has no remote, or the pull fails.
    """
    if not is_git_repo(vault_path):
        return False
    pull = _run(["git", "pull", "--rebase"], cwd=vault_path)
    if pull is None or pull.returncode != 0:
        logger.warning("git pull --rebase failed for the Vault; continuing with the local state.")
        return False
    return True


def push_vault(vault_path: Path) -> bool:
    """Rebase on the remote and push the Vault's commits.

    Returns True when the push succeeds. On failure the commits stay local (no
    data loss — the next sync catches up) and a warning is logged.
    """
    if not is_git_repo(vault_path):
        return False
    pull = _run(["git", "pull", "--rebase"], cwd=vault_path)
    if pull is None or pull.returncode != 0:
        logger.warning("git pull --rebase failed; not pushing (commits remain local).")
        return False
    push = _run(["git", "push"], cwd=vault_path)
    if push is None or push.returncode != 0:
        logger.warning("git push failed; commits remain local until the next sync.")
        return False
    logger.info("Pushed Vault commits to the remote.")
    return True


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError) as exc:  # git missing, etc.
        logger.warning("Git command failed (%s): %s", " ".join(args), exc)
        return None
