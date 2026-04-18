# CLI — AI auto mode

Auto mode fetches your repository's file tree, README, and CI/CD configuration from the hosting platform, then sends that context to an AI model to fill in the assessment answers automatically — no manual prompts required.

## Supported AI providers

| Provider | Flag value | API key env var | Notes |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` | GPT-4o and other OpenAI models |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | Claude models |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | Gemini models |
| Ollama | `ollama` | — | Local models, no API key needed |

## Basic usage

```bash
# OpenAI — provider auto-detected from the git remote URL
OPENAI_API_KEY=sk-... dm assess --auto --ai openai

# Specify a model explicitly
OPENAI_API_KEY=sk-... dm assess --auto --ai openai --model gpt-4o

# Anthropic
ANTHROPIC_API_KEY=... dm assess --auto --ai anthropic --model claude-3-5-sonnet-20241022

# Google Gemini
GEMINI_API_KEY=... dm assess --auto --ai gemini

# Ollama (runs locally, no API key needed)
dm assess --auto --ai ollama --model llama3

# Private repository — pass a token so the tool can read repo context
GITHUB_TOKEN=ghp_... dm assess --auto --ai openai
```

## How it works

1. The tool detects the git provider (GitHub, GitLab, or Bitbucket) from the `origin` remote URL.
2. It fetches the repository file tree, README, and CI/CD configuration files using the provider's API.
3. The repository context is sent to the chosen AI model alongside the list of criteria.
4. The AI returns a JSON response with a `true`/`false` answer and a brief rationale for each criterion.
5. Results are saved and displayed in the same format as interactive mode.

!!! note
    The `--provider` flag is auto-detected from the `origin` remote URL of the current git repository.
    Public repositories do not require a token.

!!! warning
    AI auto mode sends repository context to the chosen provider unless you use a local Ollama server.
    Only use it for repositories you are allowed to share with that provider.

## All flags

See [CLI flags reference](../reference/cli-flags.md#dm-assess) for the full list of options.
