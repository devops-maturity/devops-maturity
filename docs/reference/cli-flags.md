# CLI flags reference

## `dm assess`

Run an interactive or AI-powered automated assessment.

```bash
dm assess [OPTIONS]
```

| Flag | Env var fallback | Default | Description |
|---|---|---|---|
| `--project-name`, `-p` | — | Prompted | Project name for the saved record |
| `--project-url`, `-u` | — | — | Project URL for the saved record |
| `--auto` / `--no-auto` | — | `--no-auto` | Enable AI-powered automated assessment |
| `--ai` | — | — | AI provider: `openai`, `anthropic`, `gemini`, `ollama` |
| `--model` | — | Provider default | Model name (e.g., `gpt-4o`) |
| `--provider` | — | Auto-detected | Repo platform: `github`, `gitlab`, `bitbucket` |
| `--repo-token` | `GITHUB_TOKEN` / `GITLAB_TOKEN` / `BITBUCKET_TOKEN` | — | Token for private repository access |
| `--ai-key` | `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | — | AI provider API key |
| `--ollama-url` | — | `http://localhost:11434` | Ollama server base URL |
| `--version` | — | — | Print the installed version and exit |

## `dm config`

Read answers from a YAML file and generate the assessment result.

```bash
dm config [OPTIONS]
```

| Flag | Default | Description |
|---|---|---|
| `--file`, `-f` | `devops-maturity.yml` | Path to the YAML baseline file |
| `--project-name`, `-p` | From YAML / `default` | Override the project name |
| `--project-url`, `-u` | From YAML | Override the project URL |

## `dm list`

Print all assessments stored in the local database.

```bash
dm list
```

No flags. Prints assessment ID, project name, and raw responses for each saved run.
