"""Thin wrapper around the OpenRouter chat completions API.

No global config: api_key and model are passed in per-call, since the Streamlit
UI lets the user paste a key and pick a model at runtime.
"""
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

CURATED_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-70b-instruct",
]


class LLMError(Exception):
    pass


def call_llm(api_key: str, model: str, system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
    if not api_key:
        raise LLMError("No OpenRouter API key provided.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise LLMError(f"Network error calling OpenRouter: {e}") from e

    if resp.status_code == 401:
        raise LLMError("OpenRouter rejected the API key (401 Unauthorized).")
    if resp.status_code == 429:
        raise LLMError("OpenRouter rate limit hit (429). Try again shortly.")
    if resp.status_code >= 400:
        raise LLMError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected OpenRouter response shape: {data}") from e
