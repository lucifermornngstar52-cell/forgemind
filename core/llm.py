"""LLM interface — GPT-4o with function calling."""

import json
import os
from openai import OpenAI


class LLM:
    def __init__(self, config: dict):
        self.model = config.get("model", "gpt-4o")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 4096)
        self.client = OpenAI(api_key=os.environ.get("OPENAI_PROJECT_KEY", os.environ.get("OPENAI_API_KEY", "")))

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
