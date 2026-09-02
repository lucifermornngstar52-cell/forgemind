"""LLM interface — multi-backend with Groq (free, GPT-4 level) as primary.

Backends (in priority order):
1. Groq (free tier, open-source models, 120B params) — openai/gpt-oss-120b
2. Ollama (local fallback, no API key, fully independent)
3. OpenAI (last resort, requires API key)

Groq exposes an OpenAI-compatible API at https://api.groq.com/openai/v1,
so we use the same OpenAI client for all backends — just swap base_url.
"""

import os
from openai import OpenAI


class LLM:
    def __init__(self, config: dict):
        self.model = config.get("model", "openai/gpt-oss-120b")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 4096)
        self.backend = self._detect_backend()
        self.client = self._make_client()

    def _detect_backend(self) -> str:
        """Auto-detect which LLM backend to use."""
        backend = os.environ.get("LLM_BACKEND", "").lower()
        if backend:
            return backend

        # Auto: Groq if key available, else Ollama, else OpenAI
        if os.environ.get("GROQ_API_KEY"):
            return "groq"
        if os.environ.get("OLLAMA_HOST") or os.path.exists("/usr/local/bin/ollama"):
            return "ollama"
        if os.environ.get("OPENAI_PROJECT_KEY") or os.environ.get("OPENAI_API_KEY"):
            return "openai"
        # Last resort: try ollama anyway
        return "ollama"

    def _make_client(self) -> OpenAI:
        """Create OpenAI-compatible client for the active backend."""
        if self.backend == "groq":
            return OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.environ.get("GROQ_API_KEY", ""),
            )
        elif self.backend == "ollama":
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            return OpenAI(base_url=f"{host}/v1", api_key="ollama")
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
        if tools:
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
