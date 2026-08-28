"""Code writer — applies patches and creates new files."""

import os
from pathlib import Path
import difflib


class CodeWriter:
    def __init__(self, root: str = "."):
        self.root = Path(root)

    def write_file(self, path: str, content: str) -> None:
        """Write content to a file (creates or overwrites)."""
        full = self.root / path if not os.path.isabs(path) else Path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    def patch_file(self, path: str, old: str, new: str) -> bool:
        """Replace old text with new text in a file. Returns True on success."""
        full = self.root / path if not os.path.isabs(path) else Path(path)
        content = full.read_text(encoding="utf-8")
        if old not in content:
            return False
        updated = content.replace(old, new, 1)
        full.write_text(updated, encoding="utf-8")
        return True

    def create_file(self, path: str, content: str) -> None:
        """Create a new file."""
        full = self.root / path if not os.path.isabs(path) else Path(path)
        if full.exists():
            return  # Don't overwrite on create
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    def diff(self, path: str, new_content: str) -> str:
        """Generate a unified diff between current file and new content."""
        full = self.root / path if not os.path.isabs(path) else Path(path)
        old_content = full.read_text(encoding="utf-8") if full.exists() else ""
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
        return "".join(diff)
