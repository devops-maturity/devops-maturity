# Configuration

## Environment variables

The CLI reads the following environment variables as fallbacks when flags are not provided:

| Variable | Used for |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for AI auto mode |
| `ANTHROPIC_API_KEY` | Anthropic API key for AI auto mode |
| `GEMINI_API_KEY` | Google Gemini API key for AI auto mode |
| `GITHUB_TOKEN` | GitHub personal access token for private repos |
| `GITLAB_TOKEN` | GitLab personal access token for private repos |
| `BITBUCKET_TOKEN` | Bitbucket access token for private repos |

## OAuth for the web interface

The web interface supports Google and GitHub OAuth in addition to username/password login.

### Setup

1. Copy the example environment file:

    ```bash
    cp .env.example .env
    ```

2. **Google OAuth** — create credentials in [Google Cloud Console](https://console.developers.google.com/apis/credentials) with redirect URI `http://localhost:8000/auth/callback/google`, then add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env`.

3. **GitHub OAuth** — create an OAuth app in [GitHub Developer Settings](https://github.com/settings/applications/new) with callback URL `http://localhost:8000/auth/callback/github`, then add `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` to `.env`.

!!! tip
    If OAuth credentials are not configured, users can still register and log in with a username and password.

## Customising criteria

The assessment criteria are defined in `src/config/criteria.yaml`.
You can add, remove, or adjust criteria and their weights to fit your organisation's specific needs.
After modifying the file, reinstall the package (`pip install -e .`) to pick up the changes.
