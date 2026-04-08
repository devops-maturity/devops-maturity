"""AI client for automated DevOps Maturity assessment.

Supports OpenAI, Anthropic, Google Gemini, and Ollama via their HTTP APIs.
All network calls are made with ``httpx`` (already a project dependency).
"""

import json
import re
from typing import Optional

import httpx

from core.model import Criteria, UserResponse

# Default models per provider
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-haiku-20240307",
    "gemini": "gemini-1.5-flash",
    "ollama": "llama3",
}

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]+?)\s*```")
_JSON_OBJ_RE = re.compile(r"\{[\s\S]+\}")


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


# ── Provider-specific callers ──────────────────────────────────────────────────

def _call_openai(prompt: str, model: str, api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=120) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _call_anthropic(prompt: str, model: str, api_key: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=120) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


def _call_gemini(prompt: str, model: str, api_key: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    with httpx.Client(timeout=120) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _call_ollama(prompt: str, model: str, base_url: str) -> str:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
    }
    with httpx.Client(timeout=300) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


# ── Public facade ──────────────────────────────────────────────────────────────

def call_ai(
    provider: str,
    model: str,
    prompt: str,
    api_key: Optional[str] = None,
    ollama_url: str = "http://localhost:11434",
) -> str:
    """
    Call the specified AI *provider* and return the raw response text.

    Args:
        provider:   One of "openai", "anthropic", "gemini", "ollama".
        model:      Model name (e.g. "gpt-4o", "claude-3-haiku-20240307").
        prompt:     The user prompt to send.
        api_key:    API key (not required for Ollama).
        ollama_url: Base URL for the Ollama server (default: localhost:11434).

    Raises:
        ValueError: For unsupported providers or missing API keys.
        httpx.HTTPStatusError: If the provider returns an error response.
    """
    if provider == "openai":
        if not api_key:
            raise ValueError("An API key is required for OpenAI. Set OPENAI_API_KEY.")
        return _call_openai(prompt, model, api_key)
    elif provider == "anthropic":
        if not api_key:
            raise ValueError("An API key is required for Anthropic. Set ANTHROPIC_API_KEY.")
        return _call_anthropic(prompt, model, api_key)
    elif provider == "gemini":
        if not api_key:
            raise ValueError("An API key is required for Gemini. Set GEMINI_API_KEY.")
        return _call_gemini(prompt, model, api_key)
    elif provider == "ollama":
        return _call_ollama(prompt, model, ollama_url)
    else:
        raise ValueError(
            f"Unsupported AI provider: {provider!r}. "
            "Choose from: openai, anthropic, gemini, ollama."
        )


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
