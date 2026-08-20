"""
LLM client wrappers for Gemini, Grok (xAI), and OpenRouter.
API keys are provided by the user at runtime and never stored permanently.
"""

from __future__ import annotations

from typing import Optional, Generator

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def get_gemini_client(api_key: str):
    if not genai:
        raise RuntimeError("google-generativeai package not available")
    genai.configure(api_key=api_key)
    return genai


def get_openai_compatible_client(api_key: str, base_url: str) -> "OpenAI":
    if not OpenAI:
        raise RuntimeError("openai package not available")
    return OpenAI(api_key=api_key, base_url=base_url)


def list_models(provider: str, api_key: str) -> list[str]:
    """Return a sensible default list of current models for the provider (as of Aug 2026)."""
    if provider == "Gemini":
        return [
            "gemini-3.7-flash",      # Latest (Aug 2026)
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.1-pro-preview",
        ]
    elif provider == "Grok":
        return [
            "grok-4.6",              # Latest flagship (Aug 2026)
            "grok-4.5",
            "grok-4",
            "grok-3",
        ]
    elif provider == "OpenRouter":
        return [
            "google/gemini-3.7-flash",
            "google/gemini-3.6-flash",
            "x-ai/grok-4.6",
            "x-ai/grok-4.5",
            "anthropic/claude-sonnet-4",
            "openai/gpt-5",
            "meta-llama/llama-4-70b",
            "mistralai/mistral-large",
        ]
    return []


def generate_text(
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Synchronous generation. Returns the full response text."""
    if not api_key.strip():
        raise ValueError("API key is required")

    if provider == "Gemini":
        client = get_gemini_client(api_key)
        # Combine system + user for Gemini (older SDK style)
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        model_obj = client.GenerativeModel(model)
        response = model_obj.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return response.text or ""

    elif provider in ("Grok", "OpenRouter"):
        base_url = (
            "https://api.x.ai/v1"
            if provider == "Grok"
            else "https://openrouter.ai/api/v1"
        )
        client = get_openai_compatible_client(api_key, base_url)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        extra = {}
        if provider == "OpenRouter":
            extra["extra_headers"] = {
                "HTTP-Referer": "https://writing-studio.local",
                "X-Title": "AI Writing Studio",
            }
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra,
        )
        return completion.choices[0].message.content or ""

    else:
        raise ValueError(f"Unknown provider: {provider}")


def stream_text(
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Generator[str, None, None]:
    """Yield chunks for streaming UI (best-effort)."""
    # For simplicity and reliability we fall back to non-streaming
    # and yield the whole text. Real streaming can be added later.
    text = generate_text(
        provider, api_key, model, system_prompt, user_prompt, temperature, max_tokens
    )
    yield text
