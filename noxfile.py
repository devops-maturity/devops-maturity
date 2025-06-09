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
    session.run("pytest", "--cov=src", "tests")


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
def render(session):
    """Deoploy to render.com"""
    if not RENDER:
        return
    session.install("uvicorn")
    session.install(".")
    session.run("uvicorn", "src.web.main:app", "--host", "0.0.0.0")
