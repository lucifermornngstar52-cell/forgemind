"""Memory store — persistent JSON memory of what worked and what didn't."""

import json
from pathlib import Path
from datetime import datetime


class MemoryStore:
    def __init__(self, path: str = "./memory/store.json"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {
            "improvements": [],
            "failures": [],
            "techniques_learned": [],
            "metrics": {},
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_improvement(self, desc: str, file: str, success: bool, details: str = "") -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "description": desc,
            "file": file,
            "success": success,
            "details": details,
        }
        if success:
            self.data["improvements"].append(entry)
        else:
            self.data["failures"].append(entry)
        self.save()

    def record_technique(self, name: str, source: str, summary: str) -> None:
        self.data["techniques_learned"].append({
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "source": source,
            "summary": summary,
        })
        self.save()

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

    def summary(self) -> str:
        return (
            f"Improvements: {len(self.data['improvements'])}\n"
            f"Failures: {len(self.data['failures'])}\n"
            f"Success rate: {self.get_success_rate():.1%}\n"
            f"Techniques learned: {len(self.data['techniques_learned'])}\n"
            f"Metrics tracked: {list(self.data['metrics'].keys())}"
        )
