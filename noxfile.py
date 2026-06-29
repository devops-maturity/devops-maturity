import nox
import os

# check if running in CI environment
GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"
# https://render.com/docs/environment-variables
RENDER = os.environ.get("RENDER") == "true"


@nox.session
def tests(session):
    """Run the tests."""
    session.install("-e", ".[test]")
    session.run(
        "pytest", "--cov=src", "--cov-report=term-missing", "--cov-report=xml", "tests"
    )


@nox.session
def lint(session):
    """Run the linters."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def build(session):
    """Build the project."""
    session.install("build")
    session.run("python", "-m", "build")


@nox.session
def preview(session):
    """Preview the project."""
    session.install("uvicorn")
    session.install(".")
    if GITHUB_ACTIONS:
        return
    session.run("uvicorn", "src.web.main:app", "--reload")


@nox.session
def docs(session):
    """Build and serve the MkDocs documentation locally."""
    session.install("mkdocs", "mkdocs-material")
    if GITHUB_ACTIONS:
        session.run("mkdocs", "build", "--strict")
    else:
        session.run("mkdocs", "serve")


@nox.session
def licenses(session):
    """Scan dependency licenses."""
    session.install("pip-licenses", ".")
    session.run(
        "pip-licenses", "--order=license", "--format=plain-vertical", "--with-urls"
    )


@nox.session
def vulnerability_scan(session):
    """Scan dependencies for known vulnerabilities."""
    session.install("pip-audit", ".")
    # The ignored CVEs are all blocked by litellm's Python 3.14 support:
    # litellm's fixes (1.83.10 / 1.83.14 / 1.84.0) all require python<3.14,
    # but we still support Python 3.14, where litellm is pinned at 1.83.7
    # (the last release supporting 3.14). 1.83.7 also pins python-dotenv==1.0.1
    # (CVE-2026-28684). The aiohttp CVE batch is resolved by pinning
    # aiohttp>=3.14.1 in pyproject.toml. Revisit once litellm restores 3.14
    # support so these can be fixed instead of ignored.
    session.run(
        "pip-audit",
        "--local",
        "--ignore-vuln",
        "CVE-2026-40217",  # litellm: fixed in 1.83.10 (requires python<3.14)
        "--ignore-vuln",
        "CVE-2026-28684",  # python-dotenv: pinned to 1.0.1 by litellm 1.83.7
        "--ignore-vuln",
        "CVE-2026-47102",  # litellm: fixed in 1.83.10 (requires python<3.14)
        "--ignore-vuln",
        "CVE-2026-47101",  # litellm: fixed in 1.83.14 (requires python<3.14)
        "--ignore-vuln",
        "CVE-2026-49468",  # litellm: fixed in 1.84.0 (requires python<3.14)
    )


@nox.session
def deploy(session):
    """Deploy the project"""
    if not RENDER:
        session.log("Skipping deploy: RENDER not set.")
        return
    session.install("uvicorn")
    session.install(".")
    session.run("uvicorn", "src.web.main:app", "--host", "0.0.0.0")
