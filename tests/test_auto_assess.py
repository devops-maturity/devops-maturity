"""Tests for the AI-powered auto-assessment feature.

These tests cover:
- repo_fetcher: URL parsing and provider detection
- ai_client: prompt building and AI response parsing
- CLI: --auto flag validation (mocked network calls)
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli.ai_client import (
    DEFAULT_MODELS,
    build_assessment_prompt,
    call_ai,
    parse_ai_response,
)
from src.cli.repo_fetcher import (
    detect_remote_url,
    fetch_repo_context,
    parse_provider_and_repo,
)
from src.cli.main import app
from src.core.model import Criteria, UserResponse

runner = CliRunner()


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_criteria():
    return [
        Criteria(id="D101", category="Basics", criteria="Branch Builds", weight=1.0,
                 description="Trigger a build on every branch push."),
        Criteria(id="D201", category="Quality", criteria="Unit Testing", weight=1.0,
                 description="Run unit tests on every build."),
        Criteria(id="D301", category="Security", criteria="Vulnerability Scanning", weight=1.0,
                 description="Scan code for vulnerabilities."),
    ]


@pytest.fixture()
def sample_repo_context():
    return {
        "provider": "github",
        "owner": "acme",
        "repo": "myapp",
        "description": "A sample app",
        "language": "Python",
        "readme": "# MyApp\nA sample application.",
        "files": [
            ".github/workflows/ci.yml",
            "Dockerfile",
            "README.md",
            "src/main.py",
        ],
        "ci_files": [
            {
                "path": ".github/workflows/ci.yml",
                "content": "on: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest",
            }
        ],
    }


# ── repo_fetcher: parse_provider_and_repo ─────────────────────────────────────

@pytest.mark.parametrize("url,expected_provider,expected_owner,expected_repo", [
    # GitHub HTTPS
    ("https://github.com/octocat/Hello-World.git", "github", "octocat", "Hello-World"),
    ("https://github.com/octocat/Hello-World", "github", "octocat", "Hello-World"),
    # GitHub SSH
    ("git@github.com:octocat/Hello-World.git", "github", "octocat", "Hello-World"),
    # GitLab HTTPS
    ("https://gitlab.com/mygroup/myproject.git", "gitlab", "mygroup", "myproject"),
    # GitLab SSH
    ("git@gitlab.com:mygroup/myproject.git", "gitlab", "mygroup", "myproject"),
    # Bitbucket HTTPS
    ("https://bitbucket.org/teamname/reponame.git", "bitbucket", "teamname", "reponame"),
    # Bitbucket SSH
    ("git@bitbucket.org:teamname/reponame.git", "bitbucket", "teamname", "reponame"),
])
def test_parse_provider_and_repo(url, expected_provider, expected_owner, expected_repo):
    provider, owner, repo = parse_provider_and_repo(url)
    assert provider == expected_provider
    assert owner == expected_owner
    assert repo == expected_repo


def test_parse_provider_and_repo_unknown_raises():
    with pytest.raises(ValueError, match="Cannot detect provider"):
        parse_provider_and_repo("https://example.com/user/repo.git")


# ── repo_fetcher: detect_remote_url ───────────────────────────────────────────

def test_detect_remote_url_returns_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("cli.repo_fetcher.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="https://github.com/acme/myapp.git\n")
        url = detect_remote_url()
    assert url == "https://github.com/acme/myapp.git"


def test_detect_remote_url_no_git_returns_none(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.chdir(tmp_path)
    with patch("cli.repo_fetcher.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        url = detect_remote_url()
    assert url is None


# ── repo_fetcher: fetch_repo_context unsupported provider ─────────────────────

def test_fetch_repo_context_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        fetch_repo_context("bitbucket-server", "owner", "repo")


# ── ai_client: build_assessment_prompt ────────────────────────────────────────

def test_build_assessment_prompt_contains_criteria_ids(sample_criteria, sample_repo_context):
    prompt = build_assessment_prompt(sample_criteria, sample_repo_context)
    for c in sample_criteria:
        assert c.id in prompt


def test_build_assessment_prompt_contains_repo_info(sample_criteria, sample_repo_context):
    prompt = build_assessment_prompt(sample_criteria, sample_repo_context)
    assert "acme" in prompt
    assert "myapp" in prompt
    assert "github" in prompt


def test_build_assessment_prompt_contains_file_list(sample_criteria, sample_repo_context):
    prompt = build_assessment_prompt(sample_criteria, sample_repo_context)
    assert ".github/workflows/ci.yml" in prompt


def test_build_assessment_prompt_contains_ci_content(sample_criteria, sample_repo_context):
    prompt = build_assessment_prompt(sample_criteria, sample_repo_context)
    assert "ubuntu-latest" in prompt


def test_build_assessment_prompt_empty_context(sample_criteria):
    ctx = {"provider": "github", "owner": "x", "repo": "y", "files": [], "ci_files": []}
    prompt = build_assessment_prompt(sample_criteria, ctx)
    assert "D101" in prompt


# ── ai_client: parse_ai_response ──────────────────────────────────────────────

def test_parse_ai_response_basic(sample_criteria):
    raw = json.dumps({"D101": True, "D201": False, "D301": True, "suggestions": ["Add tests"]})
    responses, suggestions = parse_ai_response(raw, sample_criteria)
    assert len(responses) == 3
    resp_map = {r.id: r.answer for r in responses}
    assert resp_map["D101"] is True
    assert resp_map["D201"] is False
    assert resp_map["D301"] is True
    assert suggestions == ["Add tests"]


def test_parse_ai_response_markdown_fences(sample_criteria):
    raw = "```json\n{\"D101\": true, \"D201\": true, \"D301\": false}\n```"
    responses, suggestions = parse_ai_response(raw, sample_criteria)
    resp_map = {r.id: r.answer for r in responses}
    assert resp_map["D101"] is True
    assert resp_map["D301"] is False


def test_parse_ai_response_missing_keys_default_false(sample_criteria):
    """Criteria not in the AI response should default to False."""
    raw = json.dumps({"D101": True})
    responses, _ = parse_ai_response(raw, sample_criteria)
    resp_map = {r.id: r.answer for r in responses}
    assert resp_map["D201"] is False
    assert resp_map["D301"] is False


def test_parse_ai_response_no_suggestions(sample_criteria):
    raw = json.dumps({"D101": True, "D201": False, "D301": False})
    _, suggestions = parse_ai_response(raw, sample_criteria)
    assert suggestions == []


def test_parse_ai_response_invalid_json_raises(sample_criteria):
    with pytest.raises(ValueError, match="Could not parse"):
        parse_ai_response("not json at all", sample_criteria)


def test_parse_ai_response_extracts_embedded_json(sample_criteria):
    """AI sometimes wraps JSON in prose – we should still extract it."""
    inner = {"D101": True, "D201": True, "D301": True, "suggestions": []}
    raw = f"Here is my assessment:\n{json.dumps(inner)}\nHope that helps."
    responses, _ = parse_ai_response(raw, sample_criteria)
    assert all(r.answer for r in responses)


# ── ai_client: DEFAULT_MODELS ─────────────────────────────────────────────────

def test_default_models_defined_for_all_providers():
    for provider in ("openai", "anthropic", "gemini", "ollama"):
        assert provider in DEFAULT_MODELS
        assert DEFAULT_MODELS[provider]


# ── ai_client: call_ai via litellm ────────────────────────────────────────────

def _make_litellm_response(content: str) -> MagicMock:
    """Build a mock that mimics a litellm ModelResponse object."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_call_ai_openai_invokes_litellm(sample_criteria, sample_repo_context):
    content = json.dumps({"D101": True, "D201": False, "D301": True})
    with patch("src.cli.ai_client.litellm.completion", return_value=_make_litellm_response(content)) as mock_llm:
        result = call_ai("openai", "gpt-4o", "test prompt", api_key="sk-test")
    mock_llm.assert_called_once()
    call_kwargs = mock_llm.call_args[1] if mock_llm.call_args[1] else mock_llm.call_args[0][0]
    assert result == content


def test_call_ai_unsupported_provider_raises():
    with pytest.raises(ValueError, match="Unsupported AI provider"):
        call_ai("unknown", "gpt-4o", "test prompt", api_key="key")


def test_call_ai_missing_key_raises():
    with pytest.raises(ValueError, match="API key"):
        call_ai("openai", "gpt-4o", "test prompt", api_key=None)


def test_call_ai_ollama_no_key_required():
    content = json.dumps({"D101": True})
    with patch("src.cli.ai_client.litellm.completion", return_value=_make_litellm_response(content)):
        result = call_ai("ollama", "ollama/llama3", "test prompt")
    assert result == content


def test_call_ai_gemini_adds_prefix():
    content = json.dumps({"D101": True})
    with patch("src.cli.ai_client.litellm.completion", return_value=_make_litellm_response(content)) as mock_llm:
        call_ai("gemini", "gemini-1.5-flash", "test prompt", api_key="gkey")
    called_model = mock_llm.call_args[1]["model"]
    assert called_model == "gemini/gemini-1.5-flash"


# ── CLI: --auto validation ─────────────────────────────────────────────────────

def test_assess_auto_requires_ai_flag():
    """--auto without --ai should exit with an error."""
    with patch("src.cli.main.detect_remote_url", return_value="https://github.com/a/b.git"):
        result = runner.invoke(app, ["assess", "--auto"])
    assert result.exit_code != 0
    assert "--ai" in result.output or "required" in result.output.lower()


def test_assess_auto_invalid_ai_provider():
    with patch("src.cli.main.detect_remote_url", return_value="https://github.com/a/b.git"):
        result = runner.invoke(app, ["assess", "--auto", "--ai", "unknown-provider",
                                     "--ai-key", "fake-key"])
    assert result.exit_code != 0
    assert "Unknown AI provider" in result.output


def test_assess_auto_invalid_repo_provider():
    with patch("src.cli.main.detect_remote_url", return_value="https://github.com/a/b.git"):
        result = runner.invoke(app, [
            "assess", "--auto",
            "--provider", "svn",
            "--ai", "openai",
            "--ai-key", "fake-key",
        ])
    assert result.exit_code != 0
    assert "Unknown provider" in result.output


def test_assess_auto_missing_api_key_no_env(monkeypatch):
    """When no key is passed and no env var is set, should exit with error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with patch("src.cli.main.detect_remote_url", return_value="https://github.com/a/b.git"):
        result = runner.invoke(app, ["assess", "--auto", "--ai", "openai"])
    assert result.exit_code != 0
    assert "OPENAI_API_KEY" in result.output


def test_assess_auto_no_remote_url_no_provider(monkeypatch):
    """If git remote is not detected and --provider is absent, should exit with error."""
    with patch("src.cli.main.detect_remote_url", return_value=None):
        result = runner.invoke(app, [
            "assess", "--auto", "--ai", "ollama", "--provider", ""
        ])
    assert result.exit_code != 0


def test_assess_auto_success_mocked(monkeypatch):
    """Full happy-path test with all external calls mocked."""
    fake_context = {
        "provider": "github",
        "owner": "acme",
        "repo": "myapp",
        "description": "Test",
        "language": "Python",
        "readme": "# Test",
        "files": [".github/workflows/ci.yml"],
        "ci_files": [{"path": ".github/workflows/ci.yml", "content": "on: [push]"}],
    }
    from src.config.loader import load_criteria_config
    _, real_criteria = load_criteria_config()
    ai_json = {c.id: True for c in real_criteria}
    ai_json["suggestions"] = ["Keep up the great work!"]

    with (
        patch("src.cli.main.detect_remote_url", return_value="https://github.com/acme/myapp.git"),
        patch("src.cli.main.fetch_repo_context", return_value=fake_context),
        patch("src.cli.main.call_ai", return_value=json.dumps(ai_json)),
    ):
        result = runner.invoke(app, [
            "assess", "--auto",
            "--ai", "openai",
            "--ai-key", "sk-test",
        ])

    assert result.exit_code == 0, result.output
    assert "score" in result.output.lower()
    assert "Keep up the great work!" in result.output
