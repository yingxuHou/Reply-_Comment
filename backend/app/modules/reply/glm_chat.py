from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


@dataclass
class ChatResult:
    content: str
    latency_ms: int
    model: str


class GLMChatClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_s: float = 10.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.2) -> ChatResult:
        started = time.time()
        url = self.base_url + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": messages, "temperature": temperature}
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        choices = data.get("choices") or []
        msg = (choices[0] or {}).get("message") if choices else {}
        content = (msg or {}).get("content") or ""
        latency_ms = int((time.time() - started) * 1000)
        return ChatResult(content=content, latency_ms=latency_ms, model=self.model)


def get_chat_client() -> Optional[GLMChatClient]:
    api_key = (settings.glm_api_key or "").strip()
    if not api_key:
        return None
    return GLMChatClient(api_key=api_key, base_url=settings.glm_base_url, model=settings.glm_chat_model)

