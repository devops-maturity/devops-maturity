import typer
from ..core.model import Criteria, UserResponse
from ..core.scorer import calculate_score, score_to_level
from ..badges.generator import generate_badge

app = typer.Typer()


@app.command()
def check():
    """Run DevOps maturity assessment interactively."""
    questions = [
        # CI/CD Basics
        Criteria(
            id="build_branch",
            question="Build a specific branch (CI/CD Basics, must have)",
            weight=1.0,
        ),
        Criteria(
            id="build_pr",
            question="Build upon pull request (CI/CD Basics, must have)",
            weight=1.0,
        ),
        Criteria(
            id="docker", question="Docker (CI/CD Basics, nice to have)", weight=0.5
        ),
        # Quality
        Criteria(
            id="func_test",
            question="Automated Testing: Functional testing (Quality, must have)",
            weight=1.0,
        ),
        Criteria(
            id="perf_test",
            question="Automated Testing: Performance testing (Quality, must have)",
            weight=1.0,
        ),
        Criteria(
            id="code_coverage",
            question="Code Coverage (Quality, nice to have)",
            weight=0.5,
        ),
        Criteria(
            id="accessibility",
            question="Accessibility Testing (Quality, nice to have)",
            weight=0.5,
        ),
        # Security
        Criteria(
            id="security_scan",
            question="Security scan (Security, must have)",
            weight=1.0,
        ),
        Criteria(
            id="license_scan",
            question="License scan (Security, nice to have)",
            weight=0.5,
        ),
        # Secure Supply Chain
        Criteria(
            id="doc_build_chain",
            question="Documented Build Chain (Secure Supply Chain, must have)",
            weight=1.0,
        ),
        Criteria(
            id="cicd_as_code",
            question="CICD as coded (Secure Supply Chain, must have)",
            weight=1.0,
        ),
        Criteria(
            id="signed_artifacts",
            question="Artifacts are signed (Secure Supply Chain, nice to have)",
            weight=0.5,
        ),
        Criteria(
            id="artifactory_download",
            question="Artifactory download for Package Managers (Secure Supply Chain, nice to have)",
            weight=0.5,
        ),
        # Reporting
        Criteria(
            id="reporting",
            question="Email/Slack reporting functionality (Reporting, must have)",
            weight=1.0,
        ),
        # Analysis
        Criteria(
            id="quality_gate",
            question="Quality Gate (Analysis, nice to have)",
            weight=0.5,
        ),
        Criteria(
            id="code_lint", question="Code Lint (Analysis, nice to have)", weight=0.5
        ),
        Criteria(
            id="static_analysis",
            question="Static code analysis (Analysis, nice to have)",
            weight=0.5,
        ),
        Criteria(
            id="dynamic_analysis",
            question="Dynamic code analysis (Analysis, nice to have)",
            weight=0.5,
        ),
    ]
    responses = []
    for q in questions:
        answer = typer.confirm(q.question)
        responses.append(UserResponse(id=q.id, answer=answer))

    score = calculate_score(questions, responses)
    level = score_to_level(score)
    typer.echo(f"Your score is {score:.1f}% -> Level: {level}")
    generate_badge(score, level, "devops-maturity.svg")
    typer.echo("Badge saved to devops-maturity.svg")
