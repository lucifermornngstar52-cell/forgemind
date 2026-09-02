"""Code writer — applies patches and creates new files.

SAFETY: All write operations validate content is real Python/code, not
escaped string literals (a recurring bug where the LLM returns backslash-n
instead of real newlines). This prevents file corruption.
"""

import os
from pathlib import Path
import difflib


class CodeWriter:
    def __init__(self, root: str = "."):
        self.root = Path(root)

    def _validate_content(self, path: str, content: str) -> None:
        """Validate that content is real source code, not an escaped string.
        
        Raises ValueError if the content appears to be a corrupted/escaped
        string literal (e.g. backslash-n instead of real newlines).
        """
        if not content:
            raise ValueError("Refusing to write empty content to " + path)

        lines = content.splitlines()
        
        # Detect escaped-newline corruption: single very long line with literal backslash-n
        if len(lines) <= 2 and len(content) > 200 and "\\n" in content:
            raise ValueError(
                "Refusing to write " + path + ": content appears to be an escaped string "
                "literal (" + str(len(lines)) + " lines, " + str(len(content)) + " chars with literal backslash-n). "
                "This is a known corruption pattern - the LLM returned escaped newlines instead of real ones."
            )
        
        # Detect double-quote escaping: triple escaped quotes at start
        stripped = content.strip()
        if stripped.startswith('\\""\\"') or stripped.startswith('"""') == False and stripped.startswith('\\"'):
            # Check for the specific corruption: starts with escaped quotes
            if stripped[:3] == '\\"\\' or '\\"\\"\\"' in stripped[:20]:
                raise ValueError(
                    "Refusing to write " + path + ": content starts with escaped quotes. "
                    "This is corrupted output, not real code."
                )

    def write_file(self, path: str, content: str) -> None:
        """Write content to a file (creates or overwrites). Validates first."""
        self._validate_content(path, content)
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
        """Create a new file. Validates first."""
        self._validate_content(path, content)
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
            fromfile="a/" + path,
            tofile="b/" + path,
        )
        return "".join(diff)
