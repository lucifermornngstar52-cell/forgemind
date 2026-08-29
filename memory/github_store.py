"""GitHub Store — persistent storage via GitHub API.

Saves FORGEMIND's memory to the GitHub repo so it survives Render restarts.
On Render, the filesystem is ephemeral — every deploy starts fresh.
This module syncs memory to GitHub on save and loads from GitHub on startup.
"""

import os
import json
import base64
import httpx
from pathlib import Path
from datetime import datetime


class GitHubStore:
    """Persistent storage backed by GitHub repo."""

    REPO = "lucifermornngstar52-cell/forgemind"
    MEMORY_PATH = "memory/store.json"
    OFFSET_PATH = "memory/bot_state.json"

    def __init__(self):
        self.token = os.environ.get("GH_PAT", "")
        self.base = f"https://api.github.com/repos/{self.REPO}/contents"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _api_get(self, path: str) -> dict | None:
        """Get file content from GitHub."""
        try:
            with httpx.Client(timeout=15) as c:
                resp = c.get(f"{self.base}/{path}", headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return {"content": content, "sha": data["sha"]}
            return None
        except Exception:
            return None

    def _api_put(self, path: str, content: str, sha: str = None, message: str = "") -> bool:
        """Write file content to GitHub."""
        try:
            data = {
                "message": message or f"chore: update {path}",
                "content": base64.b64encode(content.encode()).decode(),
            }
            if sha:
                data["sha"] = sha

            with httpx.Client(timeout=15) as c:
                resp = c.put(f"{self.base}/{path}", json=data, headers=self.headers)
                return resp.status_code in (200, 201)
        except Exception:
            return False

    def load_memory(self) -> dict:
        """Load memory store from GitHub."""
        result = self._api_get(self.MEMORY_PATH)
        if result:
            return json.loads(result["content"])
        return {
            "improvements": [],
            "failures": [],
            "techniques_learned": [],
            "metrics": {},
        }

    def save_memory(self, data: dict) -> bool:
        """Save memory store to GitHub."""
        content = json.dumps(data, indent=2, ensure_ascii=False)
        existing = self._api_get(self.MEMORY_PATH)
        sha = existing["sha"] if existing else None
        return self._api_put(
            self.MEMORY_PATH, content, sha,
            f"chore: persist memory ({len(data.get('improvements', []))} improvements)"
        )

    def load_bot_state(self) -> dict:
        """Load bot state (offset, last_seen, etc.) from GitHub."""
        result = self._api_get(self.OFFSET_PATH)
        if result:
            return json.loads(result["content"])
        return {"offset": 0, "last_seen": None}

    def save_bot_state(self, state: dict) -> bool:
        """Save bot state to GitHub."""
        state["last_seen"] = datetime.now().isoformat()
        content = json.dumps(state, indent=2)
        existing = self._api_get(self.OFFSET_PATH)
        sha = existing["sha"] if existing else None
        return self._api_put(
            self.OFFSET_PATH, content, sha,
            "chore: persist bot state"
        )
