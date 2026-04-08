"""Repository context fetching for AI-powered auto-assessment.

Supports GitHub, GitLab, and Bitbucket via their respective REST APIs.
"""

import base64
import re
import subprocess
from typing import Optional

import httpx

# File paths that are relevant for DevOps maturity assessment
_CI_RELEVANT_PATHS = [
    ".github/workflows",
    ".gitlab-ci",
    "Jenkinsfile",
    "Dockerfile",
    "docker-compose",
    ".travis.yml",
    "bitbucket-pipelines.yml",
    ".circleci",
    "circleci",
    "sonar-project.properties",
    ".pre-commit-config",
    "Makefile",
    "tox.ini",
    "noxfile",
    ".snyk",
    "cosign",
    "SECURITY",
    "sbom",
    "trivy",
    "dependabot",
]

# Maximum files to fetch to keep prompt size reasonable
_MAX_CI_FILES = 8
_MAX_README_CHARS = 3000
_MAX_CI_FILE_CHARS = 2000
_MAX_FILE_LIST = 150


def detect_remote_url() -> Optional[str]:
    """Detect the git remote origin URL from the current directory."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def parse_provider_and_repo(remote_url: str) -> tuple[str, str, str]:
    """
    Parse a git remote URL and return (provider, owner, repo_name).

    Supports HTTPS and SSH URLs for GitHub, GitLab, and Bitbucket.

    Raises ValueError if the provider cannot be determined.
    """
    patterns = [
        (r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?$", "github"),
        (r"gitlab\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?$", "gitlab"),
        (r"bitbucket\.org[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?$", "bitbucket"),
    ]
    for pattern, provider in patterns:
        m = re.search(pattern, remote_url)
        if m:
            return provider, m.group(1), m.group(2)
    raise ValueError(
        f"Cannot detect provider from URL: {remote_url!r}. "
        "Use --provider to specify github, gitlab, or bitbucket."
    )


def _is_ci_relevant(path: str) -> bool:
    """Return True if *path* is a CI/CD or security-related file."""
    lp = path.lower()
    return any(p.lower() in lp for p in _CI_RELEVANT_PATHS)


def _decode_base64_content(b64: str) -> str:
    """Decode a base64-encoded string, stripping newlines GitHub inserts."""
    try:
        return base64.b64decode(b64.replace("\n", "")).decode("utf-8", errors="replace")
    except Exception:
        return ""


# ── GitHub ─────────────────────────────────────────────────────────────────────


def fetch_github_context(owner: str, repo: str, token: Optional[str] = None) -> dict:
    """Fetch repository context from the GitHub REST API."""
    headers: dict = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    base = f"https://api.github.com/repos/{owner}/{repo}"
    ctx: dict = {
        "provider": "github",
        "owner": owner,
        "repo": repo,
        "description": "",
        "language": "",
        "readme": "",
        "files": [],
        "ci_files": [],
    }

    with httpx.Client(headers=headers, timeout=30) as client:
        # Repository metadata
        r = client.get(base)
        if r.is_success:
            d = r.json()
            ctx["description"] = d.get("description") or ""
            ctx["language"] = d.get("language") or ""

        # Full file tree
        r = client.get(f"{base}/git/trees/HEAD?recursive=1")
        if r.is_success:
            ctx["files"] = [
                i["path"] for i in r.json().get("tree", []) if i.get("type") == "blob"
            ][:_MAX_FILE_LIST]

        # README
        r = client.get(f"{base}/readme")
        if r.is_success:
            ctx["readme"] = _decode_base64_content(r.json().get("content", ""))[
                :_MAX_README_CHARS
            ]

        # CI/CD-relevant files
        fetched = 0
        for fp in ctx["files"]:
            if _is_ci_relevant(fp) and fetched < _MAX_CI_FILES:
                r = client.get(f"{base}/contents/{fp}")
                if r.is_success:
                    content = _decode_base64_content(r.json().get("content", ""))
                    ctx["ci_files"].append(
                        {"path": fp, "content": content[:_MAX_CI_FILE_CHARS]}
                    )
                    fetched += 1

    return ctx


# ── GitLab ─────────────────────────────────────────────────────────────────────


def fetch_gitlab_context(owner: str, repo: str, token: Optional[str] = None) -> dict:
    """Fetch repository context from the GitLab REST API."""
    import urllib.parse

    project_id = urllib.parse.quote(f"{owner}/{repo}", safe="")
    base = f"https://gitlab.com/api/v4/projects/{project_id}"
    headers: dict = {}
    if token:
        headers["PRIVATE-TOKEN"] = token
    ctx: dict = {
        "provider": "gitlab",
        "owner": owner,
        "repo": repo,
        "description": "",
        "language": "",
        "readme": "",
        "files": [],
        "ci_files": [],
    }

    with httpx.Client(headers=headers, timeout=30) as client:
        r = client.get(base)
        if r.is_success:
            d = r.json()
            ctx["description"] = d.get("description") or ""

        # File tree (GitLab paginates at 100 items)
        r = client.get(f"{base}/repository/tree?recursive=true&per_page=100")
        if r.is_success:
            ctx["files"] = [i["path"] for i in r.json() if i.get("type") == "blob"][
                :_MAX_FILE_LIST
            ]

        # README
        for readme_name in ("README.md", "README.rst", "README"):
            encoded = urllib.parse.quote(readme_name, safe="")
            r = client.get(f"{base}/repository/files/{encoded}/raw?ref=HEAD")
            if r.is_success:
                ctx["readme"] = r.text[:_MAX_README_CHARS]
                break

        # CI/CD-relevant files
        fetched = 0
        for fp in ctx["files"]:
            if _is_ci_relevant(fp) and fetched < _MAX_CI_FILES:
                encoded = urllib.parse.quote(fp, safe="")
                r = client.get(f"{base}/repository/files/{encoded}/raw?ref=HEAD")
                if r.is_success:
                    ctx["ci_files"].append(
                        {"path": fp, "content": r.text[:_MAX_CI_FILE_CHARS]}
                    )
                    fetched += 1

    return ctx


# ── Bitbucket ──────────────────────────────────────────────────────────────────


def fetch_bitbucket_context(owner: str, repo: str, token: Optional[str] = None) -> dict:
    """Fetch repository context from the Bitbucket REST API."""
    base = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}"
    headers: dict = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    ctx: dict = {
        "provider": "bitbucket",
        "owner": owner,
        "repo": repo,
        "description": "",
        "language": "",
        "readme": "",
        "files": [],
        "ci_files": [],
    }

    with httpx.Client(headers=headers, timeout=30) as client:
        r = client.get(base)
        if r.is_success:
            d = r.json()
            ctx["description"] = d.get("description") or ""
            ctx["language"] = d.get("language") or ""

        # File listing at repository root (shallow; Bitbucket has no recursive tree endpoint)
        r = client.get(f"{base}/src/HEAD/?pagelen=100")
        if r.is_success:
            ctx["files"] = [
                v["path"]
                for v in r.json().get("values", [])
                if v.get("type") == "commit_file"
            ][:_MAX_FILE_LIST]

        # README
        for readme_name in ("README.md", "README.rst", "README"):
            r = client.get(f"{base}/src/HEAD/{readme_name}")
            if r.is_success:
                ctx["readme"] = r.text[:_MAX_README_CHARS]
                break

        # CI/CD-relevant files
        fetched = 0
        for fp in ctx["files"]:
            if _is_ci_relevant(fp) and fetched < _MAX_CI_FILES:
                r = client.get(f"{base}/src/HEAD/{fp}")
                if r.is_success:
                    ctx["ci_files"].append(
                        {"path": fp, "content": r.text[:_MAX_CI_FILE_CHARS]}
                    )
                    fetched += 1

    return ctx


# ── Public facade ──────────────────────────────────────────────────────────────


def fetch_repo_context(
    provider: str, owner: str, repo: str, token: Optional[str] = None
) -> dict:
    """
    Fetch repository context for *provider*.

    Args:
        provider: One of "github", "gitlab", or "bitbucket".
        owner:    Repository owner / organisation.
        repo:     Repository name.
        token:    Optional API token / personal access token.

    Returns:
        A dict with keys: provider, owner, repo, description, language,
        readme, files, ci_files.
    """
    if provider == "github":
        return fetch_github_context(owner, repo, token)
    elif provider == "gitlab":
        return fetch_gitlab_context(owner, repo, token)
    elif provider == "bitbucket":
        return fetch_bitbucket_context(owner, repo, token)
    else:
        raise ValueError(
            f"Unsupported provider: {provider!r}. "
            "Choose from: github, gitlab, bitbucket."
        )
