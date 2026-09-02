"""LLM interface — multi-backend with Ollama (local, independent) as primary.

Backends (in priority order):
1. Ollama (local, no API key, fully independent) — qwen2.5:3b or similar
2. OpenAI (fallback, requires API key)
3. Groq (free tier, open-source models, requires key)

Ollama exposes an OpenAI-compatible API at http://localhost:11434/v1,
so we use the same OpenAI client for all backends — just swap base_url.
"""

import os
from openai import OpenAI


class LLM:
    def __init__(self, config: dict):
        self.model = config.get("model", "qwen2.5:3b")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 4096)
        self.backend = self._detect_backend()
        self.client = self._make_client()

    def _detect_backend(self) -> str:
        """Auto-detect which LLM backend to use."""
        backend = os.environ.get("LLM_BACKEND", "").lower()
        if backend:
            return backend

        # Auto: Ollama if available, else OpenAI, else Groq
        if os.environ.get("OLLAMA_HOST") or os.path.exists("/usr/local/bin/ollama"):
            return "ollama"
        if os.environ.get("OPENAI_PROJECT_KEY") or os.environ.get("OPENAI_API_KEY"):
            return "openai"
        if os.environ.get("GROQ_API_KEY"):
            return "groq"
        # Last resort: try ollama anyway
        return "ollama"

    def _make_client(self) -> OpenAI:
        """Create OpenAI-compatible client for the active backend."""
        if self.backend == "ollama":
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            return OpenAI(base_url=f"{host}/v1", api_key="ollama")
        elif self.backend == "groq":
            return OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.environ.get("GROQ_API_KEY", ""),
            )
        else:  # openai
            key = os.environ.get("OPENAI_PROJECT_KEY", os.environ.get("OPENAI_API_KEY", ""))
            return OpenAI(api_key=key)

    def chat(self, messages: list, tools: list = None) -> dict:
        """Send chat completion, return response with optional tool calls."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools and self.backend != "ollama":
            # Ollama with small models handles tool calling poorly — skip for reliability
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        return {
            "content": msg.content or "",
            "tool_calls": msg.tool_calls or [],
            "role": msg.role,
        }

    def chat_simple(self, system: str, user: str) -> str:
        """Simple text-only completion."""
        resp = self.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        return resp["content"]
