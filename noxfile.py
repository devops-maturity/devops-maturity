import nox


@nox.session
def tests(session):
    """Run the tests."""
    session.install("pytest", "pytest-cov")
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
    session.run("uvicorn", "src.web.main:app", "--reload")
