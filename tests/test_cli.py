import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from src.cli.main import app
from src.core.model import Assessment, User, SessionLocal, init_db


class TestCLI:
    """Test the CLI functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        # Initialize test database
        init_db()
    
    def test_assess_command_help(self):
        """Test that assess command shows help."""
        result = self.runner.invoke(app, ["assess", "--help"])
        assert result.exit_code == 0
        assert "Run an interactive DevOps maturity assessment" in result.stdout
    
    def test_list_command_help(self):
        """Test that list command shows help."""
        result = self.runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all assessments from the database" in result.stdout
    
    def test_config_command_help(self):
        """Test that config command shows help."""
        result = self.runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Read answers from a YAML file" in result.stdout
    
    def test_version_option(self):
        """Test version option."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Version:" in result.stdout
    
    @patch('src.cli.main.typer.confirm')
    @patch('src.cli.main.typer.prompt')
    def test_assess_command_interactive(self, mock_prompt, mock_confirm):
        """Test interactive assessment command."""
        # Mock user inputs
        mock_prompt.return_value = "test-project"
        mock_confirm.side_effect = [True, False, True]  # Simulate yes/no answers
        
        result = self.runner.invoke(app, ["assess"])
        
        # Should complete successfully
        assert result.exit_code == 0
        assert "DevOps Maturity Assessment" in result.stdout
        assert "Your score:" in result.stdout
        assert "Your maturity level:" in result.stdout
        assert "Badge URL:" in result.stdout
        assert "Assessment saved to database" in result.stdout
    
    @patch('src.cli.main.typer.confirm')
    def test_assess_command_with_project_name(self, mock_confirm):
        """Test assessment command with project name parameter."""
        # Mock user inputs for criteria questions
        mock_confirm.side_effect = [True, True, False]  # Simulate yes/no answers
        
        result = self.runner.invoke(app, ["assess", "--project-name", "my-test-project"])
        
        # Should complete successfully
        assert result.exit_code == 0
        assert "DevOps Maturity Assessment" in result.stdout
        assert "Your score:" in result.stdout
        assert "Assessment saved to database" in result.stdout
    
    def test_config_command_with_valid_file(self):
        """Test config command with a valid YAML file."""
        # Create a temporary config file
        test_config = {
            "project_name": "test-config-project",
            "ci_cd_pipeline": True,
            "version_control": True,
            "automated_testing": False,
            "code_review": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_file_path = f.name
        
        try:
            result = self.runner.invoke(app, ["config", "--file", temp_file_path])
            
            # Should complete successfully
            assert result.exit_code == 0
            assert "Your score:" in result.stdout
            assert "Assessment saved to database" in result.stdout
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def test_config_command_file_not_found(self):
        """Test config command with non-existent file."""
        result = self.runner.invoke(app, ["config", "--file", "nonexistent.yml"])
        
        # Should fail with file not found
        assert result.exit_code != 0
    
    def test_config_command_auto_detect_file(self):
        """Test config command auto-detecting devops-maturity.yml file."""
        # Create a devops-maturity.yml file in current directory
        test_config = {
            "project_name": "auto-detected-project",
            "ci_cd_pipeline": True,
            "version_control": False
        }
        
        original_cwd = os.getcwd()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                
                with open("devops-maturity.yml", "w") as f:
                    yaml.dump(test_config, f)
                
                result = self.runner.invoke(app, ["config"])
                
                # Should complete successfully
                assert result.exit_code == 0
                assert "Your score:" in result.stdout
                assert "Assessment saved to database" in result.stdout
                
            finally:
                os.chdir(original_cwd)
    
    def test_config_command_no_file_found(self):
        """Test config command when no config file is found."""
        original_cwd = os.getcwd()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                
                result = self.runner.invoke(app, ["config"])
                
                # Should fail with appropriate error message
                assert result.exit_code == 1
                assert "No devops-maturity.yml or devops-maturity.yaml found" in result.stdout
                
            finally:
                os.chdir(original_cwd)
    
    def test_config_command_project_name_override(self):
        """Test config command with project name override."""
        test_config = {
            "project_name": "original-name",
            "ci_cd_pipeline": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_file_path = f.name
        
        try:
            result = self.runner.invoke(app, [
                "config", 
                "--file", temp_file_path,
                "--project-name", "overridden-name"
            ])
            
            # Should complete successfully
            assert result.exit_code == 0
            assert "Your score:" in result.stdout
            assert "Assessment saved to database" in result.stdout
            
        finally:
            os.unlink(temp_file_path)
    
    def test_list_command_empty_database(self):
        """Test list command with empty database."""
        # Clear any existing assessments
        db = SessionLocal()
        db.query(Assessment).delete()
        db.commit()
        db.close()
        
        result = self.runner.invoke(app, ["list"])
        
        # Should complete successfully even with no assessments
        assert result.exit_code == 0
    
    def test_list_command_with_assessments(self):
        """Test list command with existing assessments."""
        # Add a test assessment to the database
        db = SessionLocal()
        test_assessment = Assessment(
            project_name="test-list-project",
            responses={"test_criteria": True}
        )
        db.add(test_assessment)
        db.commit()
        db.close()
        
        result = self.runner.invoke(app, ["list"])
        
        # Should show the assessment
        assert result.exit_code == 0
        assert "test-list-project" in result.stdout
    
    def test_cli_main_function(self):
        """Test that the CLI main function can be called directly."""
        # This tests the if __name__ == "__main__" block
        with patch('src.cli.main.app') as mock_app:
            # Import and run the main block
            import src.cli.main
            
            # Since we can't easily test the main block directly,
            # we'll just verify the app is properly defined
            assert hasattr(src.cli.main, 'app')
            assert src.cli.main.app is not None