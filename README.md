# DevOps Maturity Assessment

[![PyPI - Version](https://img.shields.io/pypi/v/devops-maturity)](https://pypi.org/project/devops-maturity/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/devops-maturity)
[![CI](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml/badge.svg)](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml)
[![PASSING](https://img.shields.io/badge/DevOps%20Maturity-PASSING-green.svg)](https://devops-maturity.github.io/)

## Overview

**DevOps Maturity Assessment** helps teams turn broad DevOps, DevSecOps, and software supply chain expectations into a score, a gap list, and a shareable badge.

Use it when you want a quick baseline before a platform improvement program, an audit-ready checklist for delivery practices, or a lightweight badge that makes engineering maturity visible in a README.

It provides both a **web UI** and a **CLI**, built on the [DevOps Maturity Specification][Specification] — a standardized set of guidelines for DevOps best practices.

## Why teams use it

- **Fast baseline**: answer a short weighted checklist and get a maturity level in minutes.
- **Clear next steps**: see category scores and prioritized missing practices instead of a raw pass/fail list.
- **Repository-aware AI mode**: optionally let an LLM inspect repository metadata, README content, and CI configuration.
- **Shareable signal**: publish a badge that makes DevOps maturity visible to users, contributors, and stakeholders.
- **Portable scoring model**: use the same criteria from the CLI, web UI, or a YAML file in automation.

## 🎥 Demo

Explore how the DevOps Maturity Assessment works in both interfaces:

- [Web App Demo on YouTube](https://www.youtube.com/watch?v=BGpz0iP61c4)
- [CLI Demo on YouTube](https://www.youtube.com/watch?v=RZJtcynyC08)

## Features

- **Interactive CLI**: Perform assessments directly from your terminal.
- **AI-Powered Automated Assessment**: Let an LLM assess your repository automatically using repository metadata, CI config, and README content — no manual answers required.
- **Web Interface**: Easy-to-use web app for taking assessments and viewing results.
- **Maturity Scoring**: Receive a maturity score, level, and badge based on your answers.
- **Progress Tracking**: View your assessment history to monitor improvement over time.
- **Customizable Criteria**: Adapt the assessment to fit your organization’s specific needs.
- **Open Source**: Built with Python and open to community contributions.


## Quick Start

### Try it in 60 seconds

```bash
pip install devops-maturity
dm assess
```

You will get:

- an overall percentage score
- a maturity level (`WIP`, `PASSING`, `BRONZE`, `SILVER`, or `GOLD`)
- per-category scores
- improvement recommendations
- a badge URL you can add to your README

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

### Run from a YAML file

Use `devops-maturity.yml` when you want a repeatable baseline that can be reviewed in pull requests:

```bash
dm config --file devops-maturity.yml
```

This is useful for CI jobs, internal platform reviews, and recurring maturity checkpoints.

### AI-Powered Automated Assessment

Skip the manual questions and let an LLM assess your repository automatically.
The tool fetches your file tree, README, and CI/CD configuration files from the repository platform and sends that context to the AI model of your choice.

**Supported AI providers**: OpenAI, Anthropic, Google Gemini, Ollama (local)

```bash
# OpenAI — provider auto-detected from the git remote URL
OPENAI_API_KEY=sk-... devops-maturity assess --auto --ai openai

# Anthropic
ANTHROPIC_API_KEY=... devops-maturity assess --auto --ai anthropic --model claude-3-5-sonnet-20241022

# Google Gemini
GEMINI_API_KEY=... devops-maturity assess --auto --ai gemini

# Ollama (no API key required, runs locally)
devops-maturity assess --auto --ai ollama --model llama3
```

| Flag | Env var fallback | Default | Notes |
|---|---|---|---|
| `--auto` | — | — | Enable AI-powered mode |
| `--ai` | — | — | AI provider: `openai`, `anthropic`, `gemini`, `ollama` |
| `--model` | — | Provider default | Model name (e.g. `gpt-4o`, `claude-3-haiku-20240307`) |
| `--provider` | — | Auto-detected | Repo platform: `github`, `gitlab`, `bitbucket` |
| `--repo-token` | `GITHUB_TOKEN` / `GITLAB_TOKEN` / `BITBUCKET_TOKEN` | — | Required for private repos |
| `--ai-key` | `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | — | AI provider API key |
| `--ollama-url` | — | `http://localhost:11434` | Ollama server base URL |

> [!NOTE]
> The `--provider` flag is auto-detected from the `origin` remote URL of the current git repository.
> For public repositories no `--repo-token` is needed.

> [!IMPORTANT]
> AI mode sends repository context to the selected provider unless you use local Ollama. Use `--repo-token` only for private repositories you are allowed to assess.

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
