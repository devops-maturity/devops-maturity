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
    session.run(
        "pip-audit",
        "--local",
        # litellm uses weekly versioning (e.g., 1.9 < 1.34 < 1.83 numerically),
        # so pip-audit reports false positives: it thinks 1.9.5 (latest stable)
        # needs "upgrading" to older weekly versions like 1.34.42 or 1.83.0.
        # These CVEs were all fixed in those older versions before the 1.9.x reset.
        "--ignore-vuln", "CVE-2025-0628",
        "--ignore-vuln", "CVE-2025-0330",
        "--ignore-vuln", "CVE-2024-2952",
        "--ignore-vuln", "CVE-2024-4264",
        "--ignore-vuln", "CVE-2024-4890",
        "--ignore-vuln", "CVE-2024-5225",
        "--ignore-vuln", "CVE-2024-4888",
        "--ignore-vuln", "CVE-2024-5710",
        "--ignore-vuln", "CVE-2024-5751",
        "--ignore-vuln", "CVE-2024-9606",
        "--ignore-vuln", "CVE-2024-8984",
        "--ignore-vuln", "CVE-2024-10188",
        "--ignore-vuln", "CVE-2026-35029",
        "--ignore-vuln", "CVE-2026-35030",
        "--ignore-vuln", "GHSA-69x8-hrgq-fjj8",
        # certifi is pinned to <2024.0.0 by litellm, so PYSEC-2024-230
        # (fixed in 2024.7.4) cannot be resolved at our level.
        "--ignore-vuln", "PYSEC-2024-230",
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
