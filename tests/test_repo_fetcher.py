"""Tests for the repository context fetchers (GitHub, GitLab, Bitbucket).

All HTTP traffic is served by an in-process mock transport, so these tests
never touch the network.
"""

import base64
import subprocess
from unittest.mock import patch

import httpx
import pytest

from src.cli import repo_fetcher
from src.cli.repo_fetcher import (
    _decode_base64_content,
    _is_ci_relevant,
    detect_remote_url,
    fetch_bitbucket_context,
    fetch_github_context,
    fetch_gitlab_context,
    fetch_repo_context,
)


def _b64(text: str) -> str:
    """Encode *text* the way the GitHub contents API does (wrapped lines)."""
    encoded = base64.b64encode(text.encode()).decode()
    return "\n".join(encoded[i : i + 20] for i in range(0, len(encoded), 20))


@pytest.fixture()
def http_routes(monkeypatch):
    """Route every request made by ``repo_fetcher`` to an in-memory table.

    The fixture returns ``(routes, requests)``: fill ``routes`` with
    ``{raw path+query: httpx.Response}`` entries; unknown paths get a 404.
    ``requests`` records every request so tests can inspect headers.
    """
    routes: dict[str, httpx.Response] = {}
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        key = request.url.raw_path.decode()
        return routes.get(key, httpx.Response(404, json={"message": "Not Found"}))

    real_client = httpx.Client

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(repo_fetcher.httpx, "Client", client_factory)
    return routes, requests


# ── Helpers ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "path,expected",
    [
        (".github/workflows/ci.yml", True),
        (".gitlab-ci.yml", True),
        ("Jenkinsfile", True),
        ("docker/Dockerfile", True),
        ("SECURITY.md", True),
        ("security.md", True),
        (".github/dependabot.yml", True),
        ("src/app/main.py", False),
        ("README.md", False),
    ],
)
def test_is_ci_relevant(path, expected):
    assert _is_ci_relevant(path) is expected


def test_decode_base64_content_handles_wrapped_lines():
    assert _decode_base64_content(_b64("hello world\n")) == "hello world\n"


def test_decode_base64_content_invalid_returns_empty_string():
    assert _decode_base64_content("not base64!") == ""


def test_detect_remote_url_without_git_binary_returns_none():
    with patch(
        "cli.repo_fetcher.subprocess.run", side_effect=FileNotFoundError("git")
    ) as mock_run:
        assert detect_remote_url() is None
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0] == ["git", "remote", "get-url", "origin"]


def test_detect_remote_url_strips_whitespace():
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="git@github.com:acme/app.git\n"
    )
    with patch("cli.repo_fetcher.subprocess.run", return_value=completed):
        assert detect_remote_url() == "git@github.com:acme/app.git"


# ── GitHub ─────────────────────────────────────────────────────────────────────


def test_fetch_github_context_collects_metadata_files_and_ci(http_routes):
    routes, requests = http_routes
    base = "/repos/acme/app"
    routes[base] = httpx.Response(
        200, json={"description": "Demo app", "language": "Python"}
    )
    routes[f"{base}/git/trees/HEAD?recursive=1"] = httpx.Response(
        200,
        json={
            "tree": [
                {"path": ".github", "type": "tree"},
                {"path": ".github/workflows/ci.yml", "type": "blob"},
                {"path": "Dockerfile", "type": "blob"},
                {"path": "src/app.py", "type": "blob"},
            ]
        },
    )
    routes[f"{base}/readme"] = httpx.Response(200, json={"content": _b64("# Demo\n")})
    routes[f"{base}/contents/.github/workflows/ci.yml"] = httpx.Response(
        200, json={"content": _b64("on: [push]\n")}
    )
    # Dockerfile is CI-relevant but cannot be fetched: it must be skipped.

    ctx = fetch_github_context("acme", "app", token="secret-token")

    assert ctx == {
        "provider": "github",
        "owner": "acme",
        "repo": "app",
        "description": "Demo app",
        "language": "Python",
        "readme": "# Demo\n",
        "files": [".github/workflows/ci.yml", "Dockerfile", "src/app.py"],
        "ci_files": [{"path": ".github/workflows/ci.yml", "content": "on: [push]\n"}],
    }
    assert all(r.url.host == "api.github.com" for r in requests)
    assert requests[0].headers["Authorization"] == "token secret-token"
    assert requests[0].headers["Accept"] == "application/vnd.github.v3+json"


def test_fetch_github_context_without_token_sends_no_auth(http_routes):
    _, requests = http_routes
    ctx = fetch_github_context("acme", "app")
    assert "Authorization" not in requests[0].headers
    # Every endpoint failed, so the context keeps its empty defaults.
    assert ctx["description"] == ""
    assert ctx["language"] == ""
    assert ctx["readme"] == ""
    assert ctx["files"] == []
    assert ctx["ci_files"] == []


def test_fetch_github_context_null_metadata_becomes_empty_string(http_routes):
    routes, _ = http_routes
    routes["/repos/acme/app"] = httpx.Response(
        200, json={"description": None, "language": None}
    )
    ctx = fetch_github_context("acme", "app")
    assert ctx["description"] == ""
    assert ctx["language"] == ""


def test_fetch_github_context_limits_ci_files_and_sizes(http_routes):
    routes, _ = http_routes
    base = "/repos/acme/app"
    workflows = [f".github/workflows/wf{i}.yml" for i in range(10)]
    routes[f"{base}/git/trees/HEAD?recursive=1"] = httpx.Response(
        200, json={"tree": [{"path": p, "type": "blob"} for p in workflows]}
    )
    routes[f"{base}/readme"] = httpx.Response(200, json={"content": _b64("R" * 5000)})
    for p in workflows:
        routes[f"{base}/contents/{p}"] = httpx.Response(
            200, json={"content": _b64("x" * 5000)}
        )

    ctx = fetch_github_context("acme", "app")

    assert len(ctx["ci_files"]) == repo_fetcher._MAX_CI_FILES
    assert [f["path"] for f in ctx["ci_files"]] == workflows[
        : repo_fetcher._MAX_CI_FILES
    ]
    assert all(
        len(f["content"]) == repo_fetcher._MAX_CI_FILE_CHARS for f in ctx["ci_files"]
    )
    assert len(ctx["readme"]) == repo_fetcher._MAX_README_CHARS


# ── GitLab ─────────────────────────────────────────────────────────────────────


def test_fetch_gitlab_context_collects_metadata_files_and_ci(http_routes):
    routes, requests = http_routes
    base = "/api/v4/projects/acme%2Fapp"
    routes[base] = httpx.Response(200, json={"description": "GitLab demo"})
    routes[f"{base}/repository/tree?recursive=true&per_page=100"] = httpx.Response(
        200,
        json=[
            {"path": ".gitlab-ci.yml", "type": "blob"},
            {"path": "docs", "type": "tree"},
            {"path": "Makefile", "type": "blob"},
        ],
    )
    # README.md is missing, README.rst exists: the loop must fall through.
    routes[f"{base}/repository/files/README.rst/raw?ref=HEAD"] = httpx.Response(
        200, text="Demo\n====\n"
    )
    routes[f"{base}/repository/files/.gitlab-ci.yml/raw?ref=HEAD"] = httpx.Response(
        200, text="stages: [test]\n"
    )

    ctx = fetch_gitlab_context("acme", "app", token="glpat-123")

    assert ctx["provider"] == "gitlab"
    assert ctx["description"] == "GitLab demo"
    assert ctx["language"] == ""
    assert ctx["readme"] == "Demo\n====\n"
    assert ctx["files"] == [".gitlab-ci.yml", "Makefile"]
    assert ctx["ci_files"] == [
        {"path": ".gitlab-ci.yml", "content": "stages: [test]\n"}
    ]
    assert all(r.url.host == "gitlab.com" for r in requests)
    assert requests[0].headers["PRIVATE-TOKEN"] == "glpat-123"


def test_fetch_gitlab_context_without_token_and_no_data(http_routes):
    _, requests = http_routes
    ctx = fetch_gitlab_context("acme", "app")
    assert "PRIVATE-TOKEN" not in requests[0].headers
    assert ctx["readme"] == ""
    assert ctx["files"] == []
    assert ctx["ci_files"] == []
    # All three README candidates were tried.
    tried = [
        r.url.raw_path.decode() for r in requests if "/repository/files/" in str(r.url)
    ]
    assert [p.split("/repository/files/")[1].split("/")[0] for p in tried] == [
        "README.md",
        "README.rst",
        "README",
    ]


# ── Bitbucket ──────────────────────────────────────────────────────────────────


def test_fetch_bitbucket_context_collects_metadata_files_and_ci(http_routes):
    routes, requests = http_routes
    base = "/2.0/repositories/acme/app"
    routes[base] = httpx.Response(
        200, json={"description": "Bitbucket demo", "language": "go"}
    )
    routes[f"{base}/src/HEAD/?pagelen=100"] = httpx.Response(
        200,
        json={
            "values": [
                {"path": "bitbucket-pipelines.yml", "type": "commit_file"},
                {"path": "cmd", "type": "commit_directory"},
                {"path": "main.go", "type": "commit_file"},
            ]
        },
    )
    routes[f"{base}/src/HEAD/README.md"] = httpx.Response(200, text="# BB demo\n")
    routes[f"{base}/src/HEAD/bitbucket-pipelines.yml"] = httpx.Response(
        200, text="pipelines: {}\n"
    )

    ctx = fetch_bitbucket_context("acme", "app", token="bb-token")

    assert ctx["provider"] == "bitbucket"
    assert ctx["description"] == "Bitbucket demo"
    assert ctx["language"] == "go"
    assert ctx["readme"] == "# BB demo\n"
    assert ctx["files"] == ["bitbucket-pipelines.yml", "main.go"]
    assert ctx["ci_files"] == [
        {"path": "bitbucket-pipelines.yml", "content": "pipelines: {}\n"}
    ]
    assert all(r.url.host == "api.bitbucket.org" for r in requests)
    assert requests[0].headers["Authorization"] == "Bearer bb-token"


def test_fetch_bitbucket_context_without_token_and_no_data(http_routes):
    routes, requests = http_routes
    base = "/2.0/repositories/acme/app"
    routes[f"{base}/src/HEAD/?pagelen=100"] = httpx.Response(
        200, json={"values": [{"path": "Jenkinsfile", "type": "commit_file"}]}
    )
    ctx = fetch_bitbucket_context("acme", "app")
    assert "Authorization" not in requests[0].headers
    assert ctx["description"] == ""
    assert ctx["readme"] == ""
    assert ctx["files"] == ["Jenkinsfile"]
    # The CI file could not be downloaded, so nothing is attached.
    assert ctx["ci_files"] == []


# ── Facade ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "provider,target",
    [
        ("github", "fetch_github_context"),
        ("gitlab", "fetch_gitlab_context"),
        ("bitbucket", "fetch_bitbucket_context"),
    ],
)
def test_fetch_repo_context_dispatches_to_provider(monkeypatch, provider, target):
    calls = []

    def fake_fetch(owner, repo, token=None):
        calls.append((owner, repo, token))
        return {"provider": provider}

    monkeypatch.setattr(repo_fetcher, target, fake_fetch)
    assert fetch_repo_context(provider, "acme", "app", "tok") == {"provider": provider}
    assert calls == [("acme", "app", "tok")]


def test_fetch_gitlab_context_skips_unreadable_ci_files(http_routes):
    routes, _ = http_routes
    base = "/api/v4/projects/acme%2Fapp"
    routes[f"{base}/repository/tree?recursive=true&per_page=100"] = httpx.Response(
        200,
        json=[
            {"path": "Dockerfile", "type": "blob"},
            {"path": "src/main.py", "type": "blob"},
        ],
    )
    ctx = fetch_gitlab_context("acme", "app")
    assert ctx["files"] == ["Dockerfile", "src/main.py"]
    assert ctx["ci_files"] == []


def test_fetch_bitbucket_context_tree_failure_leaves_files_empty(http_routes):
    routes, requests = http_routes
    base = "/2.0/repositories/acme/app"
    routes[base] = httpx.Response(200, json={"description": None, "language": None})
    ctx = fetch_bitbucket_context("acme", "app")
    assert ctx["description"] == ""
    assert ctx["language"] == ""
    assert ctx["files"] == []
    assert ctx["ci_files"] == []
    assert not any("pipelines" in str(r.url) for r in requests)
