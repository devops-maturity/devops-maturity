import json
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


def _build_result(responses, project_name=None, project_url=None, source="manual"):
    """Build a result dict shared by text and JSON output paths."""
    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    badge_url = get_badge_url(level)
    badge_markdown = (
        f"[![DevOps Maturity Badge]({badge_url})](https://devops-maturity.github.io/)"
    )

    category_scores = calculate_category_scores(criteria, responses)
    response_map = {r.id: r.answer for r in responses}
    failed = [
        {"id": c.id, "criteria": c.criteria, "description": c.description}
        for c in criteria
        if not response_map.get(c.id)
    ]
    passed = [
        {"id": c.id, "criteria": c.criteria} for c in criteria if response_map.get(c.id)
    ]

    return {
        "project_name": project_name or "default",
        "project_url": project_url,
        "assessment_source": source,
        "score": round(score, 1),
        "level": level,
        "badge_url": badge_url,
        "badge_markdown": badge_markdown,
        "category_scores": {cat: round(s, 1) for cat, s in category_scores.items()},
        "passed": passed,
        "failed": failed,
    }


def _save_to_db(responses, project_name=None, project_url=None):
    """Persist assessment to the database."""
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


def save_responses(
    responses, project_name=None, project_url=None, output_format="text"
):
    result = _build_result(responses, project_name, project_url)

    if output_format == "json":
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_text_result(result)

    _save_to_db(responses, project_name, project_url)
    typer.secho("Assessment saved to database.", fg=typer.colors.GREEN, bold=True)


def _category_for_id(criteria_id: str) -> str:
    for c in criteria:
        if c.id == criteria_id:
            return c.category
    return "Unknown"


def _print_text_result(result):
    """Pretty-print the assessment result to the terminal."""
    typer.secho(
        f"\nYour score: {result['score']:.1f}%", fg=typer.colors.BLUE, bold=True
    )
    typer.secho(
        f"Your maturity level: {result['level']}", fg=typer.colors.GREEN, bold=True
    )
    typer.secho(f"Badge URL: {result['badge_url']}", fg=typer.colors.CYAN)
    typer.echo(f"Markdown badge: {result['badge_markdown']}\n")

    # Category breakdown
    typer.secho("Category Breakdown:", fg=typer.colors.YELLOW, bold=True)
    for cat, cat_score in result["category_scores"].items():
        bar_len = int(cat_score / 5)  # 20 chars = 100%
        bar = "█" * bar_len + "░" * (20 - bar_len)
        color = typer.colors.GREEN if cat_score >= 60 else typer.colors.RED
        typer.secho(f"  {cat:<22} [{bar}] {cat_score:.0f}%", fg=color)

    # Improvement recommendations
    if result["failed"]:
        typer.secho("\nImprovement Recommendations:", fg=typer.colors.YELLOW, bold=True)
        current_cat = None
        for c in result["failed"]:
            cat = _category_for_id(c["id"])
            if cat != current_cat:
                current_cat = cat
                typer.secho(f"\n  {cat}:", fg=typer.colors.CYAN, bold=True)
            typer.secho(f"    [{c['id']}] {c['criteria']}", fg=typer.colors.WHITE)
            if c.get("description"):
                typer.secho(
                    f"         {c['description']}", fg=typer.colors.BRIGHT_BLACK
                )

    typer.echo("")
    typer.secho("Next steps:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  1. Commit a devops-maturity.yml baseline for repeatable reviews.")
    typer.echo("  2. Add the Markdown badge to your README to make progress visible.")
    typer.echo("  3. Re-run the assessment after improving the missing practices.\n")


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
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text (default) or json.",
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

    Use --format json for machine-readable output (useful in CI pipelines).

    Example (AI-powered):

        devops-maturity assess --auto --ai openai --model gpt-4o

    Example (JSON output from file):

        devops-maturity config --file devops-maturity.yml --format json
    """
    if output_format not in ("text", "json"):
        typer.secho(
            f"Error: --format must be 'text' or 'json', got {output_format!r}.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

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
            output_format=output_format,
        )
        return

    # ── Interactive mode ──────────────────────────────────────────────────────
    if output_format == "json":
        typer.secho(
            "Error: --format json is not supported in interactive mode. "
            "Use --auto or the 'config' command with a YAML file instead.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    responses = []
    typer.echo("DevOps Maturity Assessment\n")

    # Ask for project name if not provided
    if project_name is None:
        project_name = typer.prompt("Project name", default="default")

    for c in criteria:
        answer = typer.confirm(f"{c.id} {c.criteria} (yes/no)", default=False)
        responses.append(UserResponse(id=c.id, answer=answer))
    save_responses(responses, project_name, project_url, output_format)


def _run_auto_assess(
    project_name: Optional[str],
    project_url: Optional[str],
    provider: Optional[str],
    ai: Optional[str],
    model: Optional[str],
    repo_token: Optional[str],
    ai_api_key: Optional[str],
    ollama_url: str,
    output_format: str = "text",
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
                f"Error: API key required for {ai!r}. Set {env_var} or pass --ai-key.",
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

    # ── Build result ──────────────────────────────────────────────────────────
    result = _build_result(
        responses, final_project_name, final_project_url, source="ai"
    )
    if suggestions:
        result["ai_suggestions"] = suggestions

    if output_format == "json":
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_text_result(result)
        if suggestions:
            typer.secho(
                "\n💡 AI Improvement Suggestions:", fg=typer.colors.YELLOW, bold=True
            )
            for suggestion in suggestions:
                typer.secho(f"  • {suggestion}", fg=typer.colors.WHITE)

    _save_to_db(responses, final_project_name, final_project_url)
    typer.secho("Assessment saved to database.", fg=typer.colors.GREEN, bold=True)


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
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text (default) or json.",
    ),
):
    """
    Read answers from a YAML file and generate the DevOps maturity assessment result.

    Use --format json for machine-readable output (useful in CI pipelines).
    """
    if output_format not in ("text", "json"):
        typer.secho(
            f"Error: --format must be 'text' or 'json', got {output_format!r}.",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

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
        raw = data.get(c.id, False)
        # Support both boolean and structured {status: true/false, evidence: [...]}
        if isinstance(raw, dict):
            answer = bool(raw.get("status", raw.get("answer", False)))
        else:
            answer = bool(raw)
        responses.append(UserResponse(id=c.id, answer=answer))
    save_responses(responses, final_project_name, final_project_url, output_format)


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
