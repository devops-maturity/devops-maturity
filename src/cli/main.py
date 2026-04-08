import os
from typing import Optional

import typer
import yaml
from core.model import UserResponse, Assessment, SessionLocal, init_db
from core.scorer import calculate_score, score_to_level, calculate_category_scores
from core.badge import get_badge_url
from core import __version__
from config.loader import load_criteria_config
from cli.ai_client import (
    DEFAULT_MODELS,
    build_assessment_prompt,
    call_ai,
    parse_ai_response,
)
from cli.repo_fetcher import (
    detect_remote_url,
    fetch_repo_context,
    parse_provider_and_repo,
)

# Load criteria and categories from config
categories, criteria = load_criteria_config()

# Initialize database
init_db()

app = typer.Typer(
    help="Run DevOps maturity assessment interactively.", add_completion=False
)


def version_callback(value: bool):
    if value:
        typer.echo(f"Version: {__version__}")
        raise typer.Exit()


def save_responses(responses, project_name=None, project_url=None):
    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    typer.secho(f"\nYour score: {score:.1f}%", fg=typer.colors.BLUE, bold=True)
    typer.secho(f"Your maturity level: {level}", fg=typer.colors.GREEN, bold=True)
    typer.secho(f"Badge URL: {get_badge_url(level)}\n", fg=typer.colors.CYAN)

    # Category breakdown
    category_scores = calculate_category_scores(criteria, responses)
    typer.secho("Category Breakdown:", fg=typer.colors.YELLOW, bold=True)
    for cat, cat_score in category_scores.items():
        bar_len = int(cat_score / 5)  # 20 chars = 100%
        bar = "█" * bar_len + "░" * (20 - bar_len)
        color = typer.colors.GREEN if cat_score >= 60 else typer.colors.RED
        typer.secho(f"  {cat:<22} [{bar}] {cat_score:.0f}%", fg=color)

    # Improvement recommendations
    response_map = {r.id: r.answer for r in responses}
    missing = [c for c in criteria if not response_map.get(c.id)]
    if missing:
        typer.secho("\nImprovement Recommendations:", fg=typer.colors.YELLOW, bold=True)
        current_cat = None
        for c in missing:
            if c.category != current_cat:
                current_cat = c.category
                typer.secho(f"\n  {current_cat}:", fg=typer.colors.CYAN, bold=True)
            typer.secho(f"    [{c.id}] {c.criteria}", fg=typer.colors.WHITE)
            if c.description:
                typer.secho(f"         {c.description}", fg=typer.colors.BRIGHT_BLACK)

    typer.echo("")

    # Save to database
    db = SessionLocal()
    responses_dict = {r.id: r.answer for r in responses}
    assessment = Assessment(
        project_name=project_name or "default",
        project_url=project_url or None,
        responses=responses_dict,
    )
    db.add(assessment)
    db.commit()
    db.close()
    typer.secho("Assessment saved to database.", fg=typer.colors.GREEN, bold=True)


@app.command(name="assess")
def assess(
    project_name: str = typer.Option(
        None,
        "--project-name",
        "-p",
        help="Name of the project for this assessment",
    ),
    project_url: str = typer.Option(
        None,
        "--project-url",
        "-u",
        help="URL of the project for this assessment (optional)",
    ),
    auto: bool = typer.Option(
        False,
        "--auto/--no-auto",
        help="Use AI-powered automated assessment instead of interactive prompts.",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help=(
            "Git repository provider: github, gitlab, or bitbucket. "
            "Auto-detected from the current git remote when omitted."
        ),
    ),
    ai: Optional[str] = typer.Option(
        None,
        "--ai",
        help="AI provider to use: openai, anthropic, gemini, or ollama.",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="AI model name (e.g. gpt-4o). Uses a sensible default for each provider.",
    ),
    repo_token: Optional[str] = typer.Option(
        None,
        "--repo-token",
        envvar="REPO_TOKEN",
        help=(
            "API token for the git provider (for private repos). "
            "Can also be set via GITHUB_TOKEN, GITLAB_TOKEN, or BITBUCKET_TOKEN env vars."
        ),
    ),
    ai_api_key: Optional[str] = typer.Option(
        None,
        "--ai-key",
        help=(
            "API key for the AI provider. "
            "Can also be set via OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY env vars."
        ),
    ),
    ollama_url: str = typer.Option(
        "http://localhost:11434",
        "--ollama-url",
        help="Base URL for a local Ollama server.",
    ),
):
    """Run an interactive DevOps maturity assessment.

    Pass --auto to perform an AI-powered automated assessment of the current
    Git repository without answering questions manually.

    Example (AI-powered):

        devops-maturity assess --auto --ai openai --model gpt-4o
    """
    if auto:
        _run_auto_assess(
            project_name=project_name,
            project_url=project_url,
            provider=provider,
            ai=ai,
            model=model,
            repo_token=repo_token,
            ai_api_key=ai_api_key,
            ollama_url=ollama_url,
        )
        return

    # ── Interactive mode ──────────────────────────────────────────────────────
    responses = []
    typer.echo("DevOps Maturity Assessment\n")

    # Ask for project name if not provided
    if project_name is None:
        project_name = typer.prompt("Project name", default="default")

    for c in criteria:
        answer = typer.confirm(f"{c.id} {c.criteria} (yes/no)", default=False)
        responses.append(UserResponse(id=c.id, answer=answer))
    save_responses(responses, project_name, project_url)


def _run_auto_assess(
    project_name: Optional[str],
    project_url: Optional[str],
    provider: Optional[str],
    ai: Optional[str],
    model: Optional[str],
    repo_token: Optional[str],
    ai_api_key: Optional[str],
    ollama_url: str,
) -> None:
    """Orchestrate an AI-powered automated assessment."""

    # ── Validate required args ────────────────────────────────────────────────
    if not ai:
        typer.secho(
            "Error: --ai is required for auto-assessment. "
            "Choose from: openai, anthropic, gemini, ollama.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    ai = ai.lower()
    valid_ai = {"openai", "anthropic", "gemini", "ollama"}
    if ai not in valid_ai:
        typer.secho(
            f"Error: Unknown AI provider {ai!r}. Choose from: {', '.join(sorted(valid_ai))}.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    resolved_model = model or DEFAULT_MODELS[ai]

    # ── Resolve API key for AI provider ──────────────────────────────────────
    resolved_ai_key = ai_api_key
    if not resolved_ai_key and ai != "ollama":
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }
        env_var = env_key_map.get(ai, "")
        resolved_ai_key = os.environ.get(env_var)
        if not resolved_ai_key:
            typer.secho(
                f"Error: API key required for {ai!r}. "
                f"Set {env_var} or pass --ai-key.",
                fg=typer.colors.RED,
                bold=True,
            )
            raise typer.Exit(1)

    # ── Detect git provider / repository ─────────────────────────────────────
    remote_url = detect_remote_url()

    resolved_provider: Optional[str] = provider
    owner: Optional[str] = None
    repo_name: Optional[str] = None

    if remote_url:
        try:
            detected_provider, owner, repo_name = parse_provider_and_repo(remote_url)
            if not resolved_provider:
                resolved_provider = detected_provider
        except ValueError:
            pass

    if not resolved_provider:
        typer.secho(
            "Error: Could not detect a git provider from the remote URL. "
            "Use --provider to specify github, gitlab, or bitbucket.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    resolved_provider = resolved_provider.lower()
    valid_providers = {"github", "gitlab", "bitbucket"}
    if resolved_provider not in valid_providers:
        typer.secho(
            f"Error: Unknown provider {resolved_provider!r}. "
            f"Choose from: {', '.join(sorted(valid_providers))}.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    if not owner or not repo_name:
        typer.secho(
            "Error: Could not determine owner/repository from the remote URL.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    # ── Resolve repo token ────────────────────────────────────────────────────
    resolved_repo_token = repo_token
    if not resolved_repo_token:
        token_env_map = {
            "github": "GITHUB_TOKEN",
            "gitlab": "GITLAB_TOKEN",
            "bitbucket": "BITBUCKET_TOKEN",
        }
        resolved_repo_token = os.environ.get(token_env_map.get(resolved_provider, ""))

    # ── Fetch repository context ──────────────────────────────────────────────
    typer.secho(
        f"\n🔍 Fetching repository context from {resolved_provider}: "
        f"{owner}/{repo_name} …",
        fg=typer.colors.CYAN,
    )
    try:
        repo_context = fetch_repo_context(
            resolved_provider, owner, repo_name, resolved_repo_token
        )
    except Exception as exc:
        typer.secho(
            f"Error fetching repository context: {exc}",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    typer.secho(
        f"  ✔ {len(repo_context.get('files', []))} files found, "
        f"{len(repo_context.get('ci_files', []))} CI/CD config file(s) fetched.",
        fg=typer.colors.GREEN,
    )

    # Use the project_url from the remote when not provided
    final_project_url = project_url or remote_url
    final_project_name = project_name or repo_name

    # ── Ask AI to assess ──────────────────────────────────────────────────────
    typer.secho(
        f"\n🤖 Sending repository context to {ai} ({resolved_model}) …",
        fg=typer.colors.CYAN,
    )
    prompt = build_assessment_prompt(criteria, repo_context)
    try:
        raw_response = call_ai(
            provider=ai,
            model=resolved_model,
            prompt=prompt,
            api_key=resolved_ai_key,
            ollama_url=ollama_url,
        )
    except Exception as exc:
        typer.secho(
            f"Error calling AI provider: {exc}",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    try:
        responses, suggestions = parse_ai_response(raw_response, criteria)
    except Exception as exc:
        typer.secho(
            f"Error parsing AI response: {exc}",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    typer.secho("  ✔ AI assessment complete.", fg=typer.colors.GREEN)

    # ── Display AI suggestions ────────────────────────────────────────────────
    if suggestions:
        typer.secho(
            "\n💡 AI Improvement Suggestions:", fg=typer.colors.YELLOW, bold=True
        )
        for suggestion in suggestions:
            typer.secho(f"  • {suggestion}", fg=typer.colors.WHITE)

    # ── Save results ──────────────────────────────────────────────────────────
    save_responses(responses, final_project_name, final_project_url)


@app.command(name="list")
def list_assessments():
    """List all assessments from the database."""
    db = SessionLocal()
    assessments = db.query(Assessment).all()
    db.close()
    for a in assessments:
        typer.echo(f"ID: {a.id} | Project: {a.project_name} | Responses: {a.responses}")


@app.command(name="config")
def assess_from_file(
    file_path: str = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to the YAML file (default: devops-maturity.yml or devops-maturity.yaml)",
    ),
    project_name: str = typer.Option(
        None,
        "--project-name",
        "-p",
        help="Name of the project for this assessment (overrides project_name in YAML file)",
    ),
    project_url: str = typer.Option(
        None,
        "--project-url",
        "-u",
        help="URL of the project for this assessment (overrides project_url in YAML file, optional)",
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

    # Get project name from CLI argument, YAML file, or default
    final_project_name = project_name or data.get("project_name") or "default"
    # Get project URL from CLI argument or YAML file
    final_project_url = project_url or data.get("project_url") or None

    responses = []
    for c in criteria:
        answer = bool(data.get(c.id, False))
        responses.append(UserResponse(id=c.id, answer=answer))
    save_responses(responses, final_project_name, final_project_url)


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
