"""Minimal Ollama HTTP client (stdlib only).

Talks to a local Ollama server's ``/api/chat`` and ``/api/tags``. Supports multimodal
messages (base64 images attached to a user turn) and JSON-forced output for structured
extraction. Kept dependency-free (urllib) and easily faked in tests.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field


class OllamaError(RuntimeError):
    """Raised when the Ollama server is unreachable or returns an error."""


@dataclass
class ChatMessage:
    role: str                       # "system" | "user" | "assistant"
    content: str
    images: list[str] = field(default_factory=list)   # base64-encoded image data

    def to_dict(self) -> dict:
        d: dict = {"role": self.role, "content": self.content}
        if self.images:
            d["images"] = self.images
        return d


class OllamaClient:
    """Thin wrapper around a local Ollama server."""

    def __init__(self, base_url: str, model: str, *, timeout: float = 600.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise OllamaError(f"Ollama request to {url} failed: {exc}") from exc

    def list_models(self) -> list[str]:
        url = f"{self.base_url}/api/tags"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                tags = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise OllamaError(f"cannot reach Ollama at {self.base_url}: {exc}") from exc
        return [m["name"] for m in tags.get("models", [])]

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        format_json: bool = False,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        """Send a chat completion and return the assistant's text."""
        payload = {
            "model": model or self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if format_json:
            payload["format"] = "json"
        result = self._post("/api/chat", payload)
        return result.get("message", {}).get("content", "")
