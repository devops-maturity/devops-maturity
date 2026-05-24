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
    # CVE-2026-40217 (litellm): fixed in 1.83.10, but 1.83.10+ requires
    # python<3.14. Litellm 1.83.7 (last to support 3.14) pins python-dotenv
    # to 1.0.1, which has CVE-2026-28684. Both blocked by upstream;
    # ignore until upstream resolves the compatibility constraints.
    session.run(
        "pip-audit",
        "--local",
        "--ignore-vuln", "CVE-2026-40217",
        "--ignore-vuln", "CVE-2026-28684",
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
