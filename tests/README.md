# DevOps Maturity Assessment Tests

This directory contains comprehensive tests for the DevOps Maturity Assessment tool.

## Test Structure

### Core Tests (`test_core.py`)
- **TestScorer**: Tests for the scoring algorithm
  - Score calculation with various answer combinations
  - Maturity level assignment based on scores
  - Edge cases like empty criteria and missing responses
- **TestBadge**: Tests for badge URL generation
  - All maturity levels (WIP, PASSING, BRONZE, SILVER, GOLD)
  - Case insensitive handling
  - Invalid level fallback to WIP
- **TestModels**: Tests for data model validation
  - Criteria and UserResponse model creation

### Configuration Tests (`test_config.py`)
- **TestConfigLoader**: Tests for configuration loading
  - Loading criteria from YAML configuration
  - Validation of categories and criteria structure
  - Unique ID validation
  - Positive weight validation
  - Custom configuration file handling

### CLI Tests (`test_cli.py`)
- **TestCLI**: Tests for command-line interface
  - Help text for all commands
  - Interactive assessment flow
  - Configuration file processing
  - Assessment listing
  - Project name handling
  - Error cases (missing files, etc.)

### Web Interface Tests (`test_web.py`)
- **TestWebInterface**: Tests for web application
  - Form page rendering
  - Assessment submission and validation
  - User authentication (register/login/logout)
  - OAuth endpoint existence
  - Assessment editing authorization
  - Error handling for invalid requests

### Database Tests (`test_database.py`)
- **TestDatabase**: Tests for data persistence
  - Assessment creation and retrieval
  - User creation with various scenarios
  - Unique constraint validation
  - JSON response storage
  - Multiple assessments per user
  - Database initialization

## Running Tests

### With Nox (Recommended)
```bash
nox -s tests
```

### With Pytest Directly
```bash
# Install dependencies first
pip install -e .[test]

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_core.py

# Run with coverage
pytest --cov=src tests/
```

### Test Validation
```bash
# Validate test structure without running
python validate_tests.py
```

## Test Coverage

The test suite provides comprehensive coverage of:

- **Core Business Logic**: Scoring algorithms, badge generation, data models
- **Configuration Management**: YAML loading, validation, error handling  
- **CLI Functionality**: All commands, user interactions, file processing
- **Web Interface**: Form handling, authentication, assessment management
- **Data Persistence**: Database operations, constraints, relationships

## Test Dependencies

The tests require the following packages:
- `pytest` - Test framework
- `fastapi` - For TestClient (web tests)
- `typer` - For CliRunner (CLI tests)
- `sqlalchemy` - For database tests
- `pydantic` - For model validation
- `pyyaml` - For configuration tests

## Test Data

Tests use:
- In-memory SQLite databases for isolation
- Temporary files for configuration testing
- Mock objects for external dependencies
- Fixtures for common test data setup

## Best Practices

- Each test class focuses on a specific component
- Tests are isolated and don't depend on each other
- Descriptive test names that explain what is being tested
- Edge cases and error conditions are covered
- Setup and teardown methods ensure clean test environments