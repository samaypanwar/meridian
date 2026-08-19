from __future__ import annotations

import json
from typing import Any

import httpx

from meridian.config import Settings, get_settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(
    messages: list[dict[str, str]],
    schema: dict[str, Any] | None = None,
    *,
    json_mode: bool = False,
    settings: Settings | None = None,
) -> dict[str, Any] | str:
    settings = settings or get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError("MERIDIAN_OPENROUTER_API_KEY is not set")

    body: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
    }
    if schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": schema, "strict": True},
        }
    elif json_mode:
        body["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    response = httpx.post(OPENROUTER_URL, headers=headers, json=body, timeout=120.0)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if schema is not None or json_mode:
        return _parse_json_content(content)
    return content


def _parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response was not a JSON object")
    return parsed
