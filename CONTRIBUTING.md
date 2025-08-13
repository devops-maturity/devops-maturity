# Contributing to DevOps Maturity Assessment

Thank you for your interest in contributing to the DevOps Maturity Assessment project! We welcome contributions from everyone and are grateful for even the smallest of fixes!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Ways to Contribute

There are many ways to contribute to this project:

1. **🐛 Report bugs** - Help us identify and fix issues
2. **💡 Suggest features** - Share ideas for new functionality
3. **📖 Improve documentation** - Help make our docs clearer and more comprehensive
4. **🔧 Fix issues** - Pick up existing issues and submit fixes
5. **🌟 Add new features** - Implement new capabilities
6. **🧪 Write tests** - Improve our test coverage
7. **🎨 Improve UI/UX** - Enhance the web interface
8. **📱 Create examples** - Add usage examples and tutorials

### Before You Start

1. **Check existing issues** - Look through existing issues to avoid duplicates
2. **Join the discussion** - Comment on issues you'd like to work on
3. **Start small** - Consider starting with good first issues if you're new

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check the existing issues to see if the problem has already been reported.

**When filing a bug report, please include:**

- **Clear title** - Summarize the problem in the title
- **Environment details** - OS, Python version, package version
- **Steps to reproduce** - Detailed steps to reproduce the issue
- **Expected behavior** - What you expected to happen
- **Actual behavior** - What actually happened
- **Screenshots** - If applicable, add screenshots
- **Additional context** - Any other context about the problem

### Suggesting Features

We love feature suggestions! Please open an issue with:

- **Clear title** - Summarize the feature request
- **Motivation** - Why is this feature needed?
- **Detailed description** - How should it work?
- **Examples** - Provide examples of how it would be used
- **Alternatives considered** - Other solutions you've considered

### Questions and Discussions

- Use [GitHub Discussions](https://github.com/devops-maturity/devops-maturity/discussions) for questions and general discussions
- Use [GitHub Issues](https://github.com/devops-maturity/devops-maturity/issues) for bug reports and feature requests

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Local Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/devops-maturity.git
   cd devops-maturity
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Install development tools**
   ```bash
   pip install nox && nox
   ```

5. **Run tests to verify setup**
   ```bash
   nox -s tests
   ```

### Development Environment

The project uses `nox` for task automation. Run `nox -l` to see available sessions.

## Pull Request Process

### Before Submitting

1. **Create a branch** - Create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** - Implement your changes with clear, focused commits

3. **Write tests** - Add tests for new functionality

4. **Run the test suite** - Ensure all tests pass
   ```bash
   nox -s tests
   ```

5. **Update documentation** - Update relevant documentation

6. **Commit your changes** - Use clear, descriptive commit messages
   ```bash
   git commit -m "feat: add new assessment criteria validation"
   ```

### Submitting a Pull Request

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** - Open a PR from your fork to the main repository

3. **Fill out the PR template** - Provide a clear description of your changes

4. **Wait for review** - Maintainers will review your PR and provide feedback

### PR Requirements

- ✅ All tests pass
- ✅ Code follows project style guidelines
- ✅ Documentation is updated (if applicable)
- ✅ Commit messages are clear and descriptive
- ✅ PR description explains the changes and motivation

## Community

### Getting Help

- **GitHub Discussions** - For questions and general discussions
- **GitHub Issues** - For bug reports and feature requests
- **Email** - Contact maintainers directly for sensitive matters

### Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Give constructive feedback
- Celebrate contributions from all community members

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (Apache License 2.0).

---

## Questions?

If you have questions about contributing, please don't hesitate to ask:

- Open a [GitHub Discussion](https://github.com/devops-maturity/devops-maturity/discussions)
- Create an [Issue](https://github.com/devops-maturity/devops-maturity/issues)
- Contact the maintainers directly

We're here to help and appreciate your interest in contributing to the project! 🎉
