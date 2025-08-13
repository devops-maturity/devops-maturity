# DevOps Maturity Assessment

[![PyPI - Version](https://img.shields.io/pypi/v/devops-maturity)](https://pypi.org/project/devops-maturity/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/devops-maturity)
[![CI](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml/badge.svg)](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml)
[![PASSING](https://img.shields.io/badge/DevOps%20Maturity-PASSING-green.svg)](https://devops-maturity.github.io/)

## Overview

**DevOps Maturity Assessment** helps you evaluate and improve your DevOps practices.

It provides both a **web UI** and a **CLI**, built on the [DevOps Maturity Specification][Specification] — a standardized set of guidelines for DevOps best practices.

## 🎥 Demo

Explore how the DevOps Maturity Assessment works in both interfaces:

- [Web App Demo on YouTube](https://www.youtube.com/watch?v=BGpz0iP61c4)
- [CLI Demo on YouTube](https://www.youtube.com/watch?v=RZJtcynyC08)

## Features

- **Interactive CLI**: Perform assessments directly from your terminal.
- **Web Interface**: Easy-to-use web app for taking assessments and viewing results.
- **Maturity Scoring**: Receive a maturity score, level, and badge based on your answers.
- **Progress Tracking**: View your assessment history to monitor improvement over time.
- **Customizable Criteria**: Adapt the assessment to fit your organization’s specific needs.
- **Open Source**: Built with Python and open to community contributions.


## Quick Start

### Run the CLI

Install from PyPI and start the interactive assessment:

```bash
pip install devops-maturity

# Start the assessment
devops-maturity assess

# Or use the shortcut command
dm assess
```

> [!TIP]
> `dm` is a convenient alias for `devops-maturity`, making it quicker to type.

You'll be guided through a series of questions and receive a maturity score, level, and badge. See it in action:

![DevOps Maturity CLI Demo][CLIDemo]

### Launch the Web Interface

To preview the web interface locally:

```bash
git clone https://github.com/devops-maturity/devops-maturity.git
cd devops-maturity
pip install nox
nox -s preview
```

Then visit http://127.0.0.1:8000 in your browser.

#### Web Interface Preview

Experience the full web interface workflow:

**1. Start Your Assessment**
![DevOps Maturity Assessment Home][WebHome]

**2. View Your Results**
![DevOps Maturity Assessment Results][WebResult]

**3. Track Assessment History**
![DevOps Maturity Assessment List][WebList]


## Configuration

### OAuth Setup (Optional)

To enable Google and GitHub OAuth login for the web interface:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. **For Google OAuth:**
   - Go to [Google Cloud Console](https://console.developers.google.com/apis/credentials)
   - Create OAuth 2.0 credentials
   - Set authorized redirect URI to: `http://localhost:8000/auth/callback/google`
   - Copy the client ID and secret to your `.env` file

3. **For GitHub OAuth:**
   - Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
   - Create a new OAuth app
   - Set authorization callback URL to: `http://localhost:8000/auth/callback/github`
   - Copy the client ID and secret to your `.env` file

If OAuth credentials are not configured, users can still register and login with username/password.

## Show Your Support

If you find this tool helpful, please consider giving it a ⭐️ — your support helps others discover and adopt it.

Want to show your project aligns with the [DevOps Maturity Specification][Specification]? Add this badge to your README:

```markdown
[![DevOps Maturity](https://img.shields.io/badge/DevOps%20Maturity%20Specification-1.0.0-yellow)](https://devops-maturity.github.io/)
```


## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

- 📖 **Read our [Contributing Guide](CONTRIBUTING.md)** for detailed instructions
- 🐛 **Report bugs** or suggest features via [GitHub Issues](https://github.com/devops-maturity/devops-maturity/issues)
- 💬 **Join discussions** in [GitHub Discussions](https://github.com/devops-maturity/devops-maturity/discussions)
- 🔒 **Security**: See our [Security Policy](SECURITY.md) for reporting vulnerabilities
- 📋 **Governance**: Learn about our project governance in [GOVERNANCE.md](GOVERNANCE.md)

## License

This project is licensed under the [Apache License 2.0][LICENSE].

[LICENSE]: https://github.com/devops-maturity/devops-maturity/blob/main/LICENSE
[Specification]: https://devops-maturity.github.io/
[CLIDemo]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/demo.gif?raw=true
[WebHome]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/home.png?raw=true
[WebResult]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/result.png?raw=true
[WebList]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/list.png?raw=true
