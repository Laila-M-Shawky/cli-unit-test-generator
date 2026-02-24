import os
import requests
from typing import Dict, Any


class LLMClientError(RuntimeError):
    pass


class OpenAICompatibleClient:
    """
    Minimal OpenAI-compatible Chat Completions client via HTTP.
    Works with OpenAI and many OpenAI-compatible gateways.

    Env:
      - OPENAI_API_KEY (required)
      - OPENAI_BASE_URL (optional; default https://api.openai.com)
      - OPENAI_MODEL (optional; default gpt-4o-mini)
      - OPENAI_TIMEOUT_SECONDS (optional; default 60)
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise LLMClientError("Missing OPENAI_API_KEY environment variable.")

        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.timeout = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

    def chat_completions(self, messages: list[dict], temperature: float = 0.0, max_tokens: int = 900) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            raise LLMClientError(f"Network error calling LLM: {e}") from e

        if resp.status_code >= 400:
            raise LLMClientError(f"LLM API error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMClientError(f"Unexpected LLM response shape: {data}") from e