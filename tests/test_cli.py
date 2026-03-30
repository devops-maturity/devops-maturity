import os
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
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
        yaml.dump(data, f)
        tmpfile = f.name
    try:
        result = runner.invoke(app, ["config", "--file", tmpfile])
        assert result.exit_code == 0
        assert "score" in result.output.lower()
    finally:
        os.unlink(tmpfile)


def test_config_with_project_name_override():
    data = {"project_name": "original-name", "D101": True}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
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
