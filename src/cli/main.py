import typer
from src.core.model import UserResponse, Assessment, SessionLocal
from src.core.scorer import calculate_score, score_to_level
from src.web.main import criteria

app = typer.Typer(help="Run DevOps maturity assessment interactively.")


@app.command(name="assess")
def assess():
    """Run an interactive DevOps maturity assessment."""
    responses = []
    typer.echo("DevOps Maturity Assessment\n")
    for c in criteria:
        answer = typer.confirm(f"{c.question} (yes/no)", default=False)
        responses.append(UserResponse(id=c.id, answer=answer))
    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    typer.echo(f"\nYour score: {score:.2f}")
    typer.echo(f"Your maturity level: {level}")

    # Save to database
    db = SessionLocal()
    responses_dict = {r.id: r.answer for r in responses}
    assessment = Assessment(responses=responses_dict)
    db.add(assessment)
    db.commit()
    db.close()
    typer.echo("Assessment saved to database.")


@app.command(name="list")
def list_assessments():
    """List all assessments from the database."""
    db = SessionLocal()
    assessments = db.query(Assessment).all()
    db.close()
    for a in assessments:
        typer.echo(f"ID: {a.id} | Responses: {a.responses}")


if __name__ == "__main__":
    app()
