"""Optional Git versioning of the external Vault (ADR 0002).

When the external Vault is itself a Git repository and ``auto_commit`` is enabled,
generated notes are committed there. This is distinct from this code repository's
Git. Implemented with subprocess to avoid an extra dependency.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def is_git_repo(path: Path) -> bool:
    """Return True if ``path`` is inside a Git working tree."""
    result = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return result is not None and result.returncode == 0 and result.stdout.strip() == "true"


def commit_note(vault_path: Path, file_path: Path, message: str) -> bool:
    """Stage and commit ``file_path`` within the Vault repository.

    Returns True if a commit was made, False if skipped (not a repo or git
    unavailable). Never raises on git failure — versioning is best-effort.
    """
    if not is_git_repo(vault_path):
        logger.warning("Vault is not a Git repository; skipping auto_commit: %s", vault_path)
        return False

    add = _run(["git", "add", str(file_path)], cwd=vault_path)
    if add is None or add.returncode != 0:
        logger.warning("git add failed; skipping commit.")
        return False

    commit = _run(["git", "commit", "-m", message], cwd=vault_path)
    if commit is None or commit.returncode != 0:
        logger.warning("git commit failed or nothing to commit.")
        return False

    logger.info("Committed note to Vault repository: %s", file_path)
    return True


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError) as exc:  # git missing, etc.
        logger.warning("Git command failed (%s): %s", " ".join(args), exc)
        return None
