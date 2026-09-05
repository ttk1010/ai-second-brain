"""Tests for the GitHub Git Data API publisher (Issue #42), with a fake HTTP fn."""

import base64
import json

import pytest

from backend.cloud.github_publisher import GitHubPublisher, PublishError


class _FakeHttp:
    """Routes GitHub Git Data API calls to canned responses and records them."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None, dict]] = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, json.loads(body) if body else None, headers))
        if method == "GET" and "/git/ref/heads/" in url:
            return 200, json.dumps({"object": {"sha": "basecommit"}}).encode()
        if method == "GET" and "/git/commits/basecommit" in url:
            return 200, json.dumps({"tree": {"sha": "basetree"}}).encode()
        if method == "POST" and url.endswith("/git/blobs"):
            return 201, json.dumps({"sha": f"blob{len(self.calls)}"}).encode()
        if method == "POST" and url.endswith("/git/trees"):
            return 201, json.dumps({"sha": "newtree"}).encode()
        if method == "POST" and url.endswith("/git/commits"):
            return 201, json.dumps({"sha": "newcommit"}).encode()
        if method == "PATCH" and "/git/refs/heads/" in url:
            return 200, json.dumps({"object": {"sha": "newcommit"}}).encode()
        return 404, b"{}"


def test_publish_makes_one_commit_with_all_files() -> None:
    http = _FakeHttp()
    sha = GitHubPublisher("owner/repo", "tok", http=http).publish(
        {"01 Concepts/AWS.md": b"# AWS", "Images/AWS.png": b"PNG"}, "Add note: AWS"
    )

    assert sha == "newcommit"
    methods = [c[0] for c in http.calls]
    # ref, base commit, 2 blobs, tree, commit, update ref — a single commit.
    assert methods == ["GET", "GET", "POST", "POST", "POST", "POST", "PATCH"]

    blobs = [c for c in http.calls if c[1].endswith("/git/blobs")]
    assert base64.b64decode(blobs[0][2]["content"]) == b"# AWS"

    tree = next(c for c in http.calls if c[1].endswith("/git/trees"))
    assert tree[2]["base_tree"] == "basetree"
    assert {e["path"] for e in tree[2]["tree"]} == {"01 Concepts/AWS.md", "Images/AWS.png"}

    commit = next(c for c in http.calls if c[1].endswith("/git/commits"))
    assert commit[2]["parents"] == ["basecommit"]
    assert commit[2]["message"] == "Add note: AWS"

    assert http.calls[0][3]["Authorization"] == "Bearer tok"


def test_publish_empty_raises() -> None:
    with pytest.raises(PublishError):
        GitHubPublisher("o/r", "t", http=_FakeHttp()).publish({}, "msg")


def test_publish_api_error_raises() -> None:
    def http(method, url, headers, body):
        return 422, b'{"message":"unprocessable"}'

    with pytest.raises(PublishError, match="422"):
        GitHubPublisher("o/r", "t", http=http).publish({"a.md": b"x"}, "msg")
