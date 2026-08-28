"""Code reader — reads and analyzes own source files."""

import os
import ast
from pathlib import Path


class CodeReader:
    def __init__(self, root: str = "."):
        self.root = Path(root)

    def list_files(self, ext: str = ".py") -> list:
        """List all Python files in the project."""
        return [str(f) for f in self.root.rglob(f"*{ext}")
                if not any(p in str(f) for p in [".git", "__pycache__", "venv", ".venv"])]

    def read_file(self, path: str) -> str:
        """Read a file's content."""
        full = self.root / path if not os.path.isabs(path) else Path(path)
        return full.read_text(encoding="utf-8")

    def get_structure(self) -> dict:
        """Get AST structure of a file — functions, classes, imports."""
        files = {}
        for path in self.list_files():
            try:
                content = self.read_file(path)
                tree = ast.parse(content)
                items = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        items.append({
                            "type": "function",
                            "name": node.name,
                            "line": node.lineno,
                            "args": [a.arg for a in node.args.args],
                        })
                    elif isinstance(node, ast.ClassDef):
                        items.append({
                            "type": "class",
                            "name": node.name,
                            "line": node.lineno,
                        })
                files[path] = {
                    "lines": len(content.splitlines()),
                    "items": items,
                }
            except SyntaxError:
                files[path] = {"lines": 0, "items": [], "error": "syntax_error"}
        return files

    def find_weaknesses(self) -> list:
        """Simple static analysis — find potential improvements."""
        weaknesses = []
        for path in self.list_files():
            try:
                content = self.read_file(path)
                lines = content.splitlines()

                # Long functions
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        length = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                        if length > 50:
                            weaknesses.append({
                                "file": path,
                                "issue": "long_function",
                                "function": node.name,
                                "lines": length,
                                "suggestion": f"Function {node.name} is {length} lines — consider splitting",
                            })

                # No docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if not ast.get_docstring(node):
                            weaknesses.append({
                                "file": path,
                                "issue": "missing_docstring",
                                "name": node.name,
                                "line": node.lineno,
                            })

                # Bare except
                for i, line in enumerate(lines):
                    if "except:" in line or "except Exception:" in line:
                        pass  # Flag for review
                    if "TODO" in line or "FIXME" in line:
                        weaknesses.append({
                            "file": path,
                            "line": i + 1,
                            "issue": "todo",
                            "text": line.strip(),
                        })

            except Exception:
                pass

        return weaknesses
