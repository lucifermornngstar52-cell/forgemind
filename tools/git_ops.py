"""Git operations — version control for safety."""

import subprocess
from pathlib import Path
from datetime import datetime


class GitOps:
    def __init__(self, root: str = "."):
        self.root = Path(root)

    def _run(self, *args) -> str:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            cwd=str(self.root),
            timeout=30,
        )
        return result.stdout.strip() + result.stderr.strip()

    def init(self) -> None:
        """Initialize git repo if needed."""
        if not (self.root / ".git").exists():
            self._run("init")
            self._run("config", "user.name", "Forgemind")
            self._run("config", "user.email", "forge@self.ai")
            self._run("add", "-A")
            self._run("commit", "-m", "Initial commit")

    def checkpoint(self, message: str) -> str:
        """Create a checkpoint commit. Returns commit hash."""
        self._run("add", "-A")
        self._run("commit", "-m", message)
        return self._run("rev-parse", "HEAD")

    def rollback(self, commit_hash: str) -> bool:
        """Rollback to a specific commit."""
        self._run("reset", "--hard", commit_hash)
        return True

    def log(self, count: int = 10) -> str:
        """Get recent git log."""
        return self._run("log", f"-{count}", "--oneline")

    def current_hash(self) -> str:
        """Get current commit hash."""
        return self._run("rev-parse", "HEAD")

    def diff_since(self, commit_hash: str) -> str:
        """Get diff since a commit."""
        return self._run("diff", commit_hash, "HEAD")
