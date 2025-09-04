# GitHub Copilot Instructions for DevOps Maturity Assessment

## Project Overview

This repository contains the **DevOps Maturity Assessment** tool - a comprehensive solution for evaluating and improving DevOps practices. The project provides both a CLI interface and a web application built on the DevOps Maturity Specification.

### Key Components

- **CLI Tool** (`src/cli/`): Interactive command-line assessment using Typer
- **Web Application** (`src/web/`): FastAPI-based web interface with Jinja2 templates
- **Core Logic** (`src/core/`): Assessment models, scoring, and badge generation
- **Configuration** (`src/config/`): YAML-based criteria and configuration management

## Architecture & Technologies

### Backend Stack
- **FastAPI**: Web framework for REST API and web interface
- **Typer**: CLI framework for interactive assessments
- **SQLAlchemy**: ORM for database operations (SQLite by default)
- **Pydantic**: Data validation and serialization
- **Jinja2**: Template engine for web UI

### Authentication & Security
- **OAuth Integration**: Google and GitHub OAuth support via Authlib
- **Session Management**: Secure session handling with middleware
- **Password Hashing**: bcrypt for secure password storage

### Assessment Engine
- **YAML Configuration**: Criteria defined in `src/config/criteria.yaml`
- **Scoring System**: Weighted scoring algorithm in `src/core/scorer.py`
- **Badge Generation**: Dynamic badge creation in `src/core/badge.py`

## Development Environment Setup

### Prerequisites
- Python 3.9+ (supports 3.9-3.13)
- pip or uv for package management

### Local Development
```bash
# Clone and install
git clone https://github.com/devops-maturity/devops-maturity.git
cd devops-maturity
pip install -e .

# For development with additional tools
pip install -e .[dev,test]

# Using nox for task automation
pip install nox
```

### Available Commands
- `devops-maturity assess` or `dm assess`: Run CLI assessment
- `uvicorn src.web.main:app --reload`: Start development web server
- `nox -s tests`: Run test suite
- `nox -s lint`: Run linting
- `nox -s preview`: Start web preview (requires installation)

## Code Patterns & Conventions

### Project Structure
```
src/
├── cli/           # Command-line interface
├── web/           # Web application (FastAPI)
├── core/          # Business logic and models
├── config/        # Configuration management
└── __init__.py    # Version management
```

### Database Models
- Use SQLAlchemy declarative base for all models
- Models are defined in `src/core/model.py`
- Database initialization happens automatically on startup
- SQLite used for development, easily swappable for production

### Data Validation
- All data structures use Pydantic models
- Input validation handled automatically by FastAPI/Pydantic
- Assessment responses follow the `UserResponse` model pattern

### Configuration Management
- Criteria definitions in YAML format (`src/config/criteria.yaml`)
- Environment variables for OAuth and secrets (`.env` file)
- Configuration loading handled in `src/config/loader.py`

## Testing Guidelines

### Test Structure
- Tests located in `tests/` directory
- Use pytest for all testing
- FastAPI TestClient for web endpoint testing
- Coverage reporting available via pytest-cov

### Running Tests
```bash
# Run all tests
nox -s tests

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_web.py -v
```

### Test Patterns
- Use FastAPI's TestClient for web testing
- Mock external dependencies when necessary
- Test both CLI and web interfaces
- Validate assessment scoring logic

## Development Workflows

### Adding New Assessment Criteria
1. Update `src/config/criteria.yaml` with new criteria
2. Ensure proper categorization and weighting
3. Test scoring calculations in `src/core/scorer.py`
4. Update documentation if needed

### Web Interface Development
- Templates are in `src/web/templates/`
- Static files in `src/web/static/`
- FastAPI routes in `src/web/main.py`
- Use Jinja2 template inheritance patterns

### CLI Development
- Main CLI logic in `src/cli/main.py`
- Use Typer's interactive features for user input
- Maintain consistency with web interface scoring
- Provide clear progress feedback

### OAuth Integration
- Configure OAuth apps in respective platforms
- Use `.env` file for credentials (never commit secrets)
- Fallback to username/password if OAuth not configured
- Test both authentication methods

## Common Development Tasks

### Adding New Routes
```python
# In src/web/main.py
@app.get("/new-endpoint")
async def new_endpoint(request: Request):
    return templates.TemplateResponse("template.html", {"request": request})
```

### Adding CLI Commands
```python
# In src/cli/main.py
@app.command()
def new_command():
    """New CLI command description."""
    typer.echo("Command implementation")
```

### Database Operations
```python
# Standard pattern for database operations
from src.core.model import SessionLocal

def get_data():
    db = SessionLocal()
    try:
        # Database operations
        return result
    finally:
        db.close()
```

## Quality Assurance

### Linting & Formatting
- Pre-commit hooks configured (`.pre-commit-config.yaml`)
- Use `nox -s lint` to run all checks
- Follow existing code style patterns

### Dependencies
- Core dependencies in `pyproject.toml`
- Development dependencies in `[project.optional-dependencies]`
- Use `uv.lock` for reproducible builds

### Security Considerations
- Never commit OAuth secrets or API keys
- Use environment variables for sensitive configuration
- Validate all user inputs through Pydantic models
- Follow FastAPI security best practices

## Troubleshooting

### Common Issues
- **ModuleNotFoundError**: Ensure you've installed the package with `pip install -e .`
- **Database Issues**: Delete `devops_maturity.db` to reset local database
- **OAuth Errors**: Check `.env` configuration and callback URLs
- **Template Errors**: Verify template paths and Jinja2 syntax

### Development Tips
- Use `uvicorn --reload` for automatic reloading during web development
- Run tests frequently with `pytest` to catch regressions early
- Use the CLI to test scoring logic before implementing in web interface
- Check logs for OAuth debugging information

## Contributing Guidelines

When contributing to this project:
1. Follow the existing code patterns and structure
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all linting passes
5. Test both CLI and web interfaces
6. Consider backwards compatibility for assessment data

For more detailed contribution guidelines, see `CONTRIBUTING.md` in the repository root.
