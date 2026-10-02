import json
import os
import re
import tempfile

import pytest
import yaml
from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Version" in result.output


def test_list_assessments():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0


def test_config_with_valid_yaml_file():
    data = {
        "project_name": "test-project",
        "project_url": "https://example.com",
        "D101": True,
        "D201": True,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(data, f)
        tmpfile = f.name
    try:
        result = runner.invoke(app, ["config", "--file", tmpfile])
        assert result.exit_code == 0
        assert "score" in result.output.lower()
        assert "Markdown badge" in result.output
        assert "Next steps" in result.output
    finally:
        os.unlink(tmpfile)


def test_config_with_project_name_override():
    data = {"project_name": "original-name", "D101": True}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(data, f)
        tmpfile = f.name
    try:
        result = runner.invoke(
            app, ["config", "--file", tmpfile, "--project-name", "overridden-name"]
        )
        assert result.exit_code == 0
    finally:
        os.unlink(tmpfile)


def test_config_with_nonexistent_file():
    result = runner.invoke(app, ["config", "--file", "/nonexistent/path/file.yml"])
    assert result.exit_code != 0


def test_config_no_file_and_no_default(tmp_path, monkeypatch):
    """Running 'config' without --file and no default file in cwd should exit 1."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 1


# ── Helpers ────────────────────────────────────────────────────────────────────


def _criteria_ids():
    from src.config.loader import load_criteria_config

    _, criteria = load_criteria_config()
    return [c.id for c in criteria]


def _latest_assessment():
    """Return the most recently stored assessment (test database)."""
    from core.model import Assessment, SessionLocal

    db = SessionLocal()
    try:
        return db.query(Assessment).order_by(Assessment.id.desc()).first()
    finally:
        db.close()


def _write_yaml(path, data):
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return str(path)


# ── Interactive assessment ─────────────────────────────────────────────────────


def test_assess_interactive_all_yes_scores_gold():
    ids = _criteria_ids()
    result = runner.invoke(
        app, ["assess"], input="interactive-gold\n" + "y\n" * len(ids)
    )
    assert result.exit_code == 0, result.output
    assert "Your score: 100.0%" in result.output
    assert "Your maturity level: GOLD" in result.output
    assert "Improvement Recommendations" not in result.output
    assert "Assessment saved to database." in result.output

    saved = _latest_assessment()
    assert saved.project_name == "interactive-gold"
    assert saved.project_url is None
    assert saved.responses == {cid: True for cid in ids}


def test_assess_interactive_defaults_to_no_and_lists_recommendations():
    ids = _criteria_ids()
    result = runner.invoke(
        app,
        ["assess", "--project-name", "interactive-wip", "-u", "https://example.com/p"],
        input="\n" * len(ids),
    )
    assert result.exit_code == 0, result.output
    # --project-name was given, so the CLI must not prompt for it.
    assert "Project name" not in result.output
    assert "Your score: 0.0%" in result.output
    assert "Your maturity level: WIP" in result.output
    assert "Improvement Recommendations" in result.output
    for cid in ids:
        assert f"[{cid}]" in result.output

    saved = _latest_assessment()
    assert saved.project_name == "interactive-wip"
    assert saved.project_url == "https://example.com/p"
    assert not any(saved.responses.values())


def test_assess_rejects_unknown_format():
    result = runner.invoke(app, ["assess", "--format", "xml"])
    assert result.exit_code == 1
    assert "--format must be 'text' or 'json'" in result.output


def test_assess_interactive_rejects_json_format():
    result = runner.invoke(app, ["assess", "--format", "json"])
    assert result.exit_code == 1
    assert "not supported in interactive mode" in result.output


# ── list command ───────────────────────────────────────────────────────────────


def test_list_shows_saved_assessments(tmp_path):
    tmpfile = _write_yaml(
        tmp_path / "answers.yml", {"project_name": "listed-project", "D101": True}
    )
    assert runner.invoke(app, ["config", "--file", tmpfile]).exit_code == 0

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Project: listed-project" in result.output
    assert "'D101': True" in result.output


# ── config command ─────────────────────────────────────────────────────────────


def test_config_rejects_unknown_format(tmp_path):
    tmpfile = _write_yaml(tmp_path / "answers.yml", {"D101": True})
    result = runner.invoke(app, ["config", "--file", tmpfile, "--format", "csv"])
    assert result.exit_code == 1
    assert "--format must be 'text' or 'json'" in result.output


def test_config_reads_project_details_from_yaml(tmp_path):
    tmpfile = _write_yaml(
        tmp_path / "answers.yml",
        {"project_name": "yaml-name", "project_url": "https://example.com/y"},
    )
    result = runner.invoke(app, ["config", "--file", tmpfile])
    assert result.exit_code == 0, result.output
    saved = _latest_assessment()
    assert saved.project_name == "yaml-name"
    assert saved.project_url == "https://example.com/y"


def test_config_cli_options_override_yaml(tmp_path):
    tmpfile = _write_yaml(
        tmp_path / "answers.yml",
        {"project_name": "yaml-name", "project_url": "https://example.com/y"},
    )
    result = runner.invoke(
        app,
        ["config", "-f", tmpfile, "-p", "cli-name", "-u", "https://example.com/cli"],
    )
    assert result.exit_code == 0, result.output
    saved = _latest_assessment()
    assert saved.project_name == "cli-name"
    assert saved.project_url == "https://example.com/cli"


def test_config_without_project_name_uses_default(tmp_path):
    tmpfile = _write_yaml(tmp_path / "answers.yml", {"D101": True})
    assert runner.invoke(app, ["config", "--file", tmpfile]).exit_code == 0
    saved = _latest_assessment()
    assert saved.project_name == "default"
    assert saved.project_url is None


def test_config_supports_structured_answers(tmp_path):
    tmpfile = _write_yaml(
        tmp_path / "answers.yml",
        {
            "project_name": "structured",
            "D101": {"status": True, "evidence": [".github/workflows/ci.yml"]},
            "D102": {"answer": True},
            "D103": {"status": False, "evidence": []},
            "D201": {"evidence": ["tests/"]},
        },
    )
    result = runner.invoke(app, ["config", "--file", tmpfile])
    assert result.exit_code == 0, result.output
    saved = _latest_assessment()
    assert saved.responses["D101"] is True
    assert saved.responses["D102"] is True
    assert saved.responses["D103"] is False
    # A mapping without status/answer counts as "not in place".
    assert saved.responses["D201"] is False
    assert "[D101]" not in result.output
    assert "[D103]" in result.output


def test_config_category_breakdown_and_partial_score(tmp_path):
    tmpfile = _write_yaml(
        tmp_path / "answers.yml", {"D101": True, "D102": True, "D103": True}
    )
    result = runner.invoke(app, ["config", "--file", tmpfile])
    assert result.exit_code == 0, result.output
    # Basics carries 2.5 of the 14.5 total weight.
    assert "Your score: 17.2%" in result.output
    assert "Your maturity level: WIP" in result.output
    assert "Category Breakdown:" in result.output
    assert re.search(r"Basics\s+\[█{20}\] 100%", result.output)
    assert re.search(r"Quality\s+\[░{20}\] 0%", result.output)


@pytest.mark.parametrize("filename", ["devops-maturity.yml", "devops-maturity.yaml"])
def test_config_uses_default_file_in_cwd(tmp_path, monkeypatch, filename):
    _write_yaml(tmp_path / filename, {"project_name": f"default-{filename}"})
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0, result.output
    assert _latest_assessment().project_name == f"default-{filename}"


def test_config_prefers_yml_over_yaml(tmp_path, monkeypatch):
    _write_yaml(tmp_path / "devops-maturity.yml", {"project_name": "from-yml"})
    _write_yaml(tmp_path / "devops-maturity.yaml", {"project_name": "from-yaml"})
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["config"]).exit_code == 0
    assert _latest_assessment().project_name == "from-yml"


def test_config_no_default_file_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 1
    assert "No devops-maturity.yml or devops-maturity.yaml found" in result.output


# ── Internal helpers ───────────────────────────────────────────────────────────


def test_category_for_id_known_and_unknown():
    from src.cli.main import _category_for_id

    assert _category_for_id("D101") == "Basics"
    assert _category_for_id("D999") == "Unknown"


def test_help_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("assess", "config", "list"):
        assert command in result.output


def test_print_text_result_skips_missing_descriptions(capsys):
    from src.cli.main import _print_text_result

    _print_text_result(
        {
            "score": 0.0,
            "level": "WIP",
            "badge_url": "https://img.shields.io/badge/x",
            "badge_markdown": "[x](y)",
            "category_scores": {},
            "failed": [{"id": "D101", "criteria": "Branch Builds", "description": ""}],
        }
    )
    out = capsys.readouterr().out
    lines = out.splitlines()
    idx = next(i for i, line in enumerate(lines) if "[D101] Branch Builds" in line)
    # No description line follows the criterion when the description is empty.
    assert lines[idx + 1].strip() == ""


def _first_json_document(text):
    """Return the first JSON object printed in *text*."""
    return json.JSONDecoder().raw_decode(text[text.index("{") :])[0]


def test_config_json_output_contains_the_result(tmp_path):
    tmpfile = _write_yaml(
        tmp_path / "answers.yml",
        {
            "project_name": "json-project",
            "project_url": "https://example.com/j",
            "D101": True,
            "D102": {"status": True, "evidence": ["ci.yml"]},
        },
    )
    result = runner.invoke(app, ["config", "--file", tmpfile, "--format", "json"])
    assert result.exit_code == 0, result.output

    payload = _first_json_document(result.stdout)
    assert payload["project_name"] == "json-project"
    assert payload["project_url"] == "https://example.com/j"
    assert payload["assessment_source"] == "manual"
    assert payload["score"] == 13.8  # 2.0 of 14.5 weighted points
    assert payload["level"] == "WIP"
    assert payload["badge_url"].endswith("DevOps%20Maturity-WIP-blue.svg")
    assert payload["badge_markdown"].startswith("[![DevOps Maturity Badge](")
    assert payload["category_scores"]["Basics"] == 80.0
    assert {p["id"] for p in payload["passed"]} == {"D101", "D102"}
    assert "D103" in {f["id"] for f in payload["failed"]}
    # The human-readable report is not printed in JSON mode.
    assert "Category Breakdown" not in result.output
    assert _latest_assessment().project_name == "json-project"
