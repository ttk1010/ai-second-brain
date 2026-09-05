"""Commit generated notes/images to a GitHub-backed Vault (Issue #42, ADR 0015).

The Lambda has no persistent disk and cannot use iCloud, so the cloud path
persists the generated note + illustration by committing them to a private
GitHub repository (the Vault). The Mac then ``git pull``s the change into its
local Vault, and iCloud carries it to the iPhone (ADR 0015).

Uses the GitHub **Git Data API** (blob -> tree -> commit -> update ref) so all
files land in a single commit without cloning the repo — lightweight and a good
fit for a stateless, short-lived Lambda, and unaffected by Vault size growth.

The HTTP call is injected (``http``) so the publisher is unit-tested without any
network access.
"""

import base64
import json
import logging
from collections.abc import Callable

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.github.com"

# (method, url, headers, body) -> (status_code, response_bytes)
HttpFn = Callable[[str, str, dict[str, str], bytes | None], tuple[int, bytes]]


class PublishError(Exception):
    """Raised when committing to GitHub fails."""


def _httpx_request(
    method: str, url: str, headers: dict[str, str], body: bytes | None
) -> tuple[int, bytes]:
    response = httpx.request(method, url, headers=headers, content=body, timeout=30.0)
    return response.status_code, response.content


class GitHubPublisher:
    """Commits a set of files to a GitHub repository in one commit."""

    def __init__(
        self,
        repo: str,
        token: str,
        *,
        branch: str = "main",
        http: HttpFn | None = None,
    ) -> None:
        """``repo`` is ``owner/name``; ``token`` is a fine-grained PAT with contents:write."""
        self._repo = repo
        self._token = token
        self._branch = branch
        self._http = http or _httpx_request

    def publish(self, files: dict[str, bytes], message: str) -> str:
        """Commit ``files`` (repo-relative POSIX path -> bytes) and return the commit SHA.

        Raises:
            PublishError: If any GitHub API call fails, or there is nothing to commit.
        """
        if not files:
            raise PublishError("No files to publish.")

        ref = self._request("GET", f"/repos/{self._repo}/git/ref/heads/{self._branch}")
        base_commit = ref["object"]["sha"]
        base = self._request("GET", f"/repos/{self._repo}/git/commits/{base_commit}")
        base_tree = base["tree"]["sha"]

        tree = []
        for path, content in files.items():
            blob = self._request(
                "POST",
                f"/repos/{self._repo}/git/blobs",
                {"content": base64.b64encode(content).decode("ascii"), "encoding": "base64"},
            )
            tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})

        new_tree = self._request(
            "POST", f"/repos/{self._repo}/git/trees", {"base_tree": base_tree, "tree": tree}
        )
        commit = self._request(
            "POST",
            f"/repos/{self._repo}/git/commits",
            {"message": message, "tree": new_tree["sha"], "parents": [base_commit]},
        )
        self._request(
            "PATCH",
            f"/repos/{self._repo}/git/refs/heads/{self._branch}",
            {"sha": commit["sha"]},
        )
        logger.info(
            "Published %d file(s) to %s@%s as %s",
            len(files),
            self._repo,
            self._branch,
            commit["sha"][:7],
        )
        return commit["sha"]

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-second-brain",
        }
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        status, data = self._http(method, f"{_API}{path}", headers, body)
        if not 200 <= status < 300:
            raise PublishError(f"GitHub API {method} {path} failed ({status}): {data[:300]!r}")
        return json.loads(data) if data else {}
