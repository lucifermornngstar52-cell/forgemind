"""Google API integration — Gemini, Search, and OAuth helpers.

Uses GOOGLE_EMAIL and GOOGLE_PASSWORD from environment for authentication.
Requires GOOGLE_GEMINI_KEY for Gemini API access (get from aistudio.google.com).
"""

import os
import json
import httpx
from typing import Optional


class GoogleAPI:
    """Google services integration for FORGEMIND."""

    def __init__(self):
        self.email = os.environ.get("GOOGLE_EMAIL", "")
        self.password = os.environ.get("GOOGLE_PASSWORD", "")
        self.gemini_key = os.environ.get("GOOGLE_GEMINI_KEY", "")
        self.search_key = os.environ.get("GOOGLE_SEARCH_KEY", "")
        self.search_cx = os.environ.get("GOOGLE_SEARCH_CX", "")

    async def gemini_complete(self, prompt: str, model: str = "gemini-2.0-flash") -> str:
        """Use Google Gemini for text completion (alternative to GPT-4o)."""
        if not self.gemini_key:
            raise ValueError("GOOGLE_GEMINI_KEY not set. Get one from aistudio.google.com")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
                },
            )
            data = resp.json()
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            raise RuntimeError(f"Gemini API error: {data}")

    async def google_search(self, query: str, max_results: int = 5) -> list:
        """Use Google Custom Search API for web research."""
        if not self.search_key or not self.search_cx:
            raise ValueError("GOOGLE_SEARCH_KEY or GOOGLE_SEARCH_CX not set")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.search_key,
                    "cx": self.search_cx,
                    "q": query,
                    "num": max_results,
                },
            )
            data = resp.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return results

    def status(self) -> dict:
        """Check which Google services are configured."""
        return {
            "gemini": bool(self.gemini_key),
            "google_search": bool(self.search_key and self.search_cx),
            "google_account": bool(self.email),
        }