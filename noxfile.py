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
    # Every advisory ignored below is a transitive issue blocked by litellm on
    # Python 3.14. litellm 1.83.7 is the last release that supports Python 3.14,
    # and it hard-pins aiohttp==3.13.5 and python-dotenv==1.0.1. The fixes for
    # the aiohttp and litellm advisories ship only in newer releases that require
    # python<3.14, so they cannot be applied while we still support 3.14
    # (pinning a newer aiohttp directly is a ResolutionImpossible against
    # litellm's exact pin). Revisit and drop these once litellm restores
    # Python 3.14 support.
    session.run(
        "pip-audit",
        "--local",
        # litellm 1.83.7 and its hard-pinned dependencies
        "--ignore-vuln", "CVE-2026-40217",  # litellm -> fixed in 1.83.10 (python<3.14)
        "--ignore-vuln", "CVE-2026-47102",  # litellm -> fixed in 1.83.10 (python<3.14)
        "--ignore-vuln", "CVE-2026-47101",  # litellm -> fixed in 1.83.14 (python<3.14)
        "--ignore-vuln", "CVE-2026-49468",  # litellm -> fixed in 1.84.0 (python<3.14)
        "--ignore-vuln", "CVE-2026-28684",  # python-dotenv 1.0.1 (pinned by litellm 1.83.7)
        # aiohttp 3.13.5 (hard-pinned by litellm 1.83.7); all fixed in 3.14.x
        "--ignore-vuln", "PYSEC-2026-237",
        "--ignore-vuln", "CVE-2026-34993",
        "--ignore-vuln", "CVE-2026-47265",
        "--ignore-vuln", "CVE-2026-50269",
        "--ignore-vuln", "CVE-2026-54273",
        "--ignore-vuln", "CVE-2026-54274",
        "--ignore-vuln", "CVE-2026-54276",
        "--ignore-vuln", "CVE-2026-54277",
        "--ignore-vuln", "CVE-2026-54278",
        "--ignore-vuln", "CVE-2026-54279",
        "--ignore-vuln", "CVE-2026-54280",
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
