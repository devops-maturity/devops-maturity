import typer
from ..core.model import Criteria, UserResponse
from ..core.scorer import calculate_score, score_to_level
from ..badges.generator import generate_badge

app = typer.Typer()


@app.command()
def check():
    """Run DevOps maturity assessment interactively."""
    questions = [
        Criteria(id="ci", question="Do you use continuous integration?", weight=1.0),
        Criteria(id="cd", question="Do you have continuous delivery?", weight=1.0),
        Criteria(id="iac", question="Do you use infrastructure as code?", weight=1.0),
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
