import os
import typer
import yaml
from importlib.metadata import version
from core.model import UserResponse, Assessment, SessionLocal
from core.scorer import calculate_score, score_to_level
from web.main import criteria
from core.badge import get_badge_url

app = typer.Typer(help="Run DevOps maturity assessment interactively.")


def version_callback(value: bool):
    if value:
        typer.echo(f"DevOps Maturity CLI Version: {version('devops-maturity')}")
        raise typer.Exit()


def save_responses(responses):
    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    typer.secho(f"\nYour score: {score:.2f}", fg=typer.colors.BLUE, bold=True)
    typer.secho(f"Your maturity level: {level}", fg=typer.colors.GREEN, bold=True)
    typer.secho(f"Badge URL: {get_badge_url(level)}\n", fg=typer.colors.CYAN)

    # Save to database
    db = SessionLocal()
    responses_dict = {r.id: r.answer for r in responses}
    assessment = Assessment(responses=responses_dict)
    db.add(assessment)
    db.commit()
    db.close()
    typer.secho("Assessment saved to database.", fg=typer.colors.GREEN, bold=True)


@app.command(name="assess")
def assess():
    """Run an interactive DevOps maturity assessment."""
    responses = []
    typer.echo("DevOps Maturity Assessment\n")
    for c in criteria:
        answer = typer.confirm(f"{c.id} {c.criteria} (yes/no)", default=False)
        responses.append(UserResponse(id=c.id, answer=answer))
    save_responses(responses)


@app.command(name="list")
def list_assessments():
    """List all assessments from the database."""
    db = SessionLocal()
    assessments = db.query(Assessment).all()
    db.close()
    for a in assessments:
        typer.echo(f"ID: {a.id} | Responses: {a.responses}")


@app.command(name="config")
def assess_from_file(
    file_path: str = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to the YAML file (default: devops-maturity.yml or devops-maturity.yaml)",
    ),
):
    """
    Read answers from a YAML file and generate the DevOps maturity assessment result.
    """
    if file_path is None:
        if os.path.exists("devops-maturity.yml"):
            file_path = "devops-maturity.yml"
        elif os.path.exists("devops-maturity.yaml"):
            file_path = "devops-maturity.yaml"
        else:
            typer.secho(
                "No devops-maturity.yml or devops-maturity.yaml found in current directory.",
                fg=typer.colors.RED,
                bold=True,
            )
            raise typer.Exit(1)

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    responses = []
    for c in criteria:
        answer = bool(data.get(c.id, False))
        responses.append(UserResponse(id=c.id, answer=answer))
    save_responses(responses)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
):
    # Do other global stuff, handle other global options here
    return


if __name__ == "__main__":
    app()
