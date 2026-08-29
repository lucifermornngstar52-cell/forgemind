"""
Memory store — persistent memory with Base44 database + vector memory.

Two layers:
1. Base44 Entities (cloud DB) — permanent, queryable, cross-session
2. Vector memory (ChromaDB) — semantic search over past experiences
3. JSON store (local) — fast fallback
"""

import json
import os
from pathlib import Path
from datetime import datetime


class MemoryStore:
    """Unified memory: JSON local + Base44 cloud + vector semantic."""

    def __init__(self, path: str = "./memory/store.json"):
        self.path = Path(path)
        self.ephemeral = os.environ.get("RENDER_EXTERNAL_URL") is not None
        self.github_store = None
        if self.ephemeral:
            try:
                from memory.github_store import GitHubStore
                self.github_store = GitHubStore()
                print("[memory] Running on Render — using GitHub persistence")
            except Exception as e:
                print(f"[memory] GitHub store unavailable: {e}")
        self.data = self._load()
        self.vector = None
        self._init_vector()

    def _load(self) -> dict:
        # On Render: load from GitHub API (ephemeral filesystem)
        if self.github_store:
            data = self.github_store.load_memory()
            if data:
                # Also save locally for fast access during this session
                self.save()
                return data
        # Local: load from file
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {
            "improvements": [],
            "failures": [],
            "techniques_learned": [],
            "metrics": {},
        }

    def _init_vector(self):
        """Initialize vector memory if chromadb is available."""
        try:
            from memory.vector_store import VectorMemory
            self.vector = VectorMemory()
        except Exception:
            self.vector = None

    def save(self) -> None:
        # Always save locally
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        # On Render: also sync to GitHub for persistence
        if self.github_store:
            try:
                self.github_store.save_memory(self.data)
            except Exception as e:
                print(f"[memory] GitHub sync failed: {e}")

    def record_improvement(self, desc: str, file: str, success: bool, details: str = "") -> None:
        """Record improvement in all memory layers."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "description": desc,
            "file": file,
            "success": success,
            "details": details,
        }

        # Layer 1: JSON local
        if success:
            self.data["improvements"].append(entry)
        else:
            self.data["failures"].append(entry)
        self.save()

        # Layer 2: Vector memory
        if self.vector:
            self.vector.remember_improvement(desc, file, success, details)

    def record_technique(self, name: str, source: str, summary: str) -> None:
        """Record learned technique in all layers."""
        # JSON
        self.data["techniques_learned"].append({
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "source": source,
            "summary": summary,
        })
        self.save()

        # Vector
        if self.vector:
            self.vector.remember_technique(name, source, summary)

    def update_metric(self, key: str, value: float) -> None:
        self.data["metrics"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        self.save()

    def get_recent_failures(self, count: int = 5) -> list:
        return self.data["failures"][-count:]

    def get_success_rate(self) -> float:
        total = len(self.data["improvements"]) + len(self.data["failures"])
        if total == 0:
            return 0.0
        return len(self.data["improvements"]) / total

    def get_semantic_context(self, query: str) -> str:
        """Get semantically relevant memories for a query."""
        if self.vector:
            return self.vector.get_context(query)
        return "Vector memory not available."

    def summary(self) -> str:
        return (
            f"Improvements: {len(self.data['improvements'])}\n"
            f"Failures: {len(self.data['failures'])}\n"
            f"Success rate: {self.get_success_rate():.1%}\n"
            f"Techniques learned: {len(self.data['techniques_learned'])}\n"
            f"Metrics tracked: {list(self.data['metrics'].keys())}\n"
            f"Vector memory: {'active' if self.vector else 'offline'}"
        )
