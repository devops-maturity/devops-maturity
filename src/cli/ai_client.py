"""AI client for automated DevOps Maturity assessment.

Uses ``litellm`` to support OpenAI, Anthropic, Google Gemini, Ollama, and
many other providers through a single unified interface.
"""

import json
import os
import re
from typing import Optional

import litellm

from core.model import Criteria, UserResponse

# litellm model names per provider (used when no --model is given)
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-haiku-20240307",
    "gemini": "gemini/gemini-1.5-flash",
    "ollama": "ollama/llama3",
}

# Provider name → litellm model prefix that must be prepended
_PROVIDER_MODEL_PREFIX: dict[str, str] = {
    "gemini": "gemini/",
    "ollama": "ollama/",
}

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]+?)\s*```")
_JSON_OBJ_RE = re.compile(r"\{[\s\S]+\}")

# Suppress litellm's verbose logging by default
litellm.suppress_debug_info = True


# ── Prompt builder ─────────────────────────────────────────────────────────────

def build_assessment_prompt(criteria: list[Criteria], repo_context: dict) -> str:
    """
    Build the LLM prompt that asks the model to assess a repository against
    the DevOps Maturity criteria.

    Returns a string ready to send as the user message.
    """
    file_list = "\n".join(
        f"  - {f}" for f in repo_context.get("files", [])[:100]
    )
    readme_excerpt = repo_context.get("readme", "")[:2000]

    ci_sections = ""
    for cf in repo_context.get("ci_files", []):
        ci_sections += f"\n### {cf['path']}\n```\n{cf['content'][:1500]}\n```\n"

    criteria_lines = "\n".join(
        f"- {c.id}: {c.criteria} — {c.description}" for c in criteria
    )

    criteria_ids = ", ".join(f'"{c.id}"' for c in criteria)

    return f"""You are a DevOps expert performing a maturity assessment for the repository \
{repo_context.get('owner', 'unknown')}/{repo_context.get('repo', 'unknown')}.

## Repository Information
- Provider: {repo_context.get('provider', 'unknown')}
- Language: {repo_context.get('language', 'unknown')}
- Description: {repo_context.get('description', 'N/A')}

## File Tree (up to 100 files)
{file_list if file_list else "  (no files detected)"}

## README (excerpt)
{readme_excerpt if readme_excerpt else "(no README found)"}

## CI/CD Configuration Files
{ci_sections if ci_sections else "No CI/CD configuration files found."}

## DevOps Maturity Criteria
For each criterion, determine whether it is satisfied based on the repository evidence above.

{criteria_lines}

## Instructions
Respond with a JSON object where:
- Keys are criterion IDs ({criteria_ids})
- Values are boolean (true = criterion met, false = not met)
- Include a "suggestions" key with a list of up to 5 concrete improvement suggestions as strings

Example format:
{{
  "D101": true,
  "D102": false,
  "suggestions": ["Add branch build triggers in your CI config"]
}}

Respond ONLY with valid JSON. Do not include any prose, markdown, or explanation outside the JSON object.
"""


def _resolve_model(provider: str, model: str) -> str:
    """
    Ensure the model name uses the litellm prefix required for the provider.

    e.g. "gemini-1.5-flash" → "gemini/gemini-1.5-flash"
         "llama3"           → "ollama/llama3"
    OpenAI and Anthropic models need no prefix.
    """
    prefix = _PROVIDER_MODEL_PREFIX.get(provider, "")
    if prefix and not model.startswith(prefix):
        return f"{prefix}{model}"
    return model


# ── Public facade ──────────────────────────────────────────────────────────────

def call_ai(
    provider: str,
    model: str,
    prompt: str,
    api_key: Optional[str] = None,
    ollama_url: str = "http://localhost:11434",
) -> str:
    """
    Call the specified AI *provider* via litellm and return the response text.

    litellm provides a unified OpenAI-compatible interface that supports
    OpenAI, Anthropic, Google Gemini, Ollama, and 100+ other providers
    without requiring provider-specific SDKs.

    Args:
        provider:   One of "openai", "anthropic", "gemini", "ollama".
        model:      Model name (e.g. "gpt-4o", "claude-3-haiku-20240307").
                    Provider-specific prefixes (e.g. "gemini/", "ollama/")
                    are added automatically when needed.
        prompt:     The user prompt to send.
        api_key:    API key (not required for Ollama).
        ollama_url: Base URL for the Ollama server (default: localhost:11434).

    Raises:
        ValueError: For unsupported providers or missing API keys.
        litellm.exceptions.APIError: If the provider returns an error response.
    """
    valid_providers = {"openai", "anthropic", "gemini", "ollama"}
    if provider not in valid_providers:
        raise ValueError(
            f"Unsupported AI provider: {provider!r}. "
            f"Choose from: {', '.join(sorted(valid_providers))}."
        )

    if provider != "ollama" and not api_key:
        raise ValueError(
            f"An API key is required for {provider!r}. "
            f"Set {provider.upper()}_API_KEY."
        )

    litellm_model = _resolve_model(provider, model)

    kwargs: dict = {
        "model": litellm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    if api_key:
        kwargs["api_key"] = api_key

    if provider == "ollama":
        kwargs["api_base"] = ollama_url
    elif provider == "openai":
        kwargs["response_format"] = {"type": "json_object"}

    # Set a generous timeout so large prompts complete
    os.environ.setdefault("LITELLM_REQUEST_TIMEOUT", "120")

    response = litellm.completion(**kwargs)
    return response.choices[0].message.content  # type: ignore[union-attr]


def parse_ai_response(
    raw: str, criteria: list[Criteria]
) -> tuple[list[UserResponse], list[str]]:
    """
    Parse the AI JSON response into a list of :class:`UserResponse` objects
    and a list of suggestion strings.

    The function tolerates JSON wrapped in markdown code fences.

    Returns:
        (responses, suggestions)
    """
    text = raw.strip()

    # Strip markdown code fences if present
    m = _JSON_BLOCK_RE.search(text)
    if m:
        text = m.group(1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Last resort: find the first JSON object in the response
        m2 = _JSON_OBJ_RE.search(text)
        if m2:
            data = json.loads(m2.group(0))
        else:
            raise ValueError(
                f"Could not parse AI response as JSON.\nRaw output:\n{raw[:500]}"
            )

    responses = [
        UserResponse(id=c.id, answer=bool(data.get(c.id, False)))
        for c in criteria
    ]

    raw_suggestions = data.get("suggestions", [])
    suggestions: list[str] = (
        [str(s) for s in raw_suggestions]
        if isinstance(raw_suggestions, list)
        else []
    )

    return responses, suggestions
