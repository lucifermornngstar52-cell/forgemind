"""Self-Diagnostic — FORGEMIND's health monitoring system.

Checks syntax, tests, loop detection, git health, and memory integrity.
Auto-rolls back if critical issues are found after a change.
"""

import os
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime


class SelfDiagnostic:
    """The mirror — FORGEMIND checks its own health."""

    def __init__(self, root: str = "."):
        self.root = Path(root)
        self.issues = []

    def check_syntax(self) -> dict:
        """Check all Python files for syntax errors."""
        errors = []
        py_files = [
            f for f in self.root.rglob("*.py")
            if ".git" not in str(f)
            and "__pycache__" not in str(f)
            and "chroma" not in str(f)
        ]

        for pyfile in py_files:
            try:
                source = pyfile.read_text(encoding="utf-8")
                # Quick check: is this a diff file?
                if source.startswith("--- ") and "+++" in source[:100]:
                    errors.append(f"{pyfile.name}: contains diff format, not valid Python")
                    continue
                ast.parse(source, filename=str(pyfile))
            except SyntaxError as e:
                errors.append(f"{pyfile.name}:{e.lineno}: {e.msg}")
            except Exception as e:
                errors.append(f"{pyfile.name}: {e}")

        return {
            "syntax_ok": len(errors) == 0,
            "syntax_errors": errors,
            "files_checked": len(py_files),
        }

    def check_tests(self) -> dict:
        """Run test suite."""
        test_dir = self.root / "tests"
        if not test_dir.exists():
            return {"tests_ok": True, "message": "No tests directory"}

        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--timeout=30"],
                capture_output=True, text=True,
                cwd=str(self.root), timeout=120
            )
            return {
                "tests_ok": result.returncode == 0,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            }
        except Exception as e:
            return {"tests_ok": False, "error": str(e)}

    def check_loops(self) -> dict:
        """Detect if the agent is stuck patching the same file repeatedly."""
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-20", "--name-only"],
                capture_output=True, text=True,
                cwd=str(self.root), timeout=10
            )
            file_counts = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line and not line.startswith(("auto:", "fix:", "feat:", "Initial")):
                    continue
                if line and ".py" in line:
                    file_counts[line] = file_counts.get(line, 0) + 1

            stuck_files = [f for f, c in file_counts.items() if c >= 5]
            return {
                "no_loops": len(stuck_files) == 0,
                "stuck_files": stuck_files,
            }
        except Exception:
            return {"no_loops": True, "stuck_files": []}

    def check_git_health(self) -> dict:
        """Check git repository health."""
        try:
            # Check if HEAD is clean
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True,
                cwd=str(self.root), timeout=10
            )
            uncommitted = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Check recent commits for syntax-breaking patterns
            log_result = subprocess.run(
                ["git", "log", "--oneline", "-5", "--format=%s"],
                capture_output=True, text=True,
                cwd=str(self.root), timeout=10
            )
            recent_commits = log_result.stdout.strip().split("\n")

            # Check for diff-format commits (broken)
            broken_commits = [
                c for c in recent_commits
                if "--- " in c and "+++" in c
            ]

            return {
                "git_ok": len(broken_commits) == 0,
                "uncommitted_files": uncommitted,
                "broken_commits": broken_commits,
            }
        except Exception as e:
            return {"git_ok": False, "error": str(e)}

    def check_memory(self) -> dict:
        """Check memory store integrity."""
        store_path = self.root / "memory" / "store.json"
        if not store_path.exists():
            return {"memory_status": "no store file"}

        try:
            data = json.loads(store_path.read_text())
            improvements = len(data.get("improvements", []))
            failures = len(data.get("failures", []))
            return {
                "memory_status": f"{improvements} imp, {failures} fail",
                "corrupt": False,
            }
        except Exception as e:
            return {"memory_status": f"corrupt: {e}", "corrupt": True}

    def run_full_check(self) -> dict:
        """Run all diagnostic checks."""
        print("🔍 Running self-diagnostic...")

        syntax = self.check_syntax()
        print(f"  Syntax: {'OK' if syntax['syntax_ok'] else 'FAIL'} ({syntax['files_checked']} files)")

        tests = self.check_tests()
        print(f"  Tests: {'OK' if tests['tests_ok'] else 'FAIL'}")

        loops = self.check_loops()
        print(f"  Loops: {'OK' if loops['no_loops'] else 'STUCK'}")

        git = self.check_git_health()
        print(f"  Git: {'OK' if git['git_ok'] else 'FAIL'}")

        memory = self.check_memory()
        print(f"  Memory: {memory['memory_status']}")

        auto_rolled_back = False

        # Auto-rollback if syntax is broken
        if not syntax["syntax_ok"]:
            print("  ⚠ Critical: syntax errors detected — attempting rollback...")
            auto_rolled_back = self._auto_rollback()
            if auto_rolled_back:
                print("  ✅ Rolled back to last good state")
            else:
                print("  ❌ Rollback failed")

        return {
            "syntax_ok": syntax["syntax_ok"],
            "syntax_errors": syntax.get("syntax_errors", []),
            "tests_ok": tests["tests_ok"],
            "no_loops": loops["no_loops"],
            "stuck_files": loops.get("stuck_files", []),
            "git_ok": git["git_ok"],
            "memory_status": memory["memory_status"],
            "auto_rolled_back": auto_rolled_back,
            "timestamp": datetime.now().isoformat(),
        }

    def _auto_rollback(self) -> bool:
        """Rollback to previous commit if current state is broken."""
        try:
            # Get the previous commit hash
            result = subprocess.run(
                ["git", "log", "--format=%H", "-2"],
                capture_output=True, text=True,
                cwd=str(self.root), timeout=10
            )
            commits = result.stdout.strip().split("\n")
            if len(commits) >= 2:
                prev_commit = commits[1]
                subprocess.run(
                    ["git", "reset", "--hard", prev_commit],
                    capture_output=True, text=True,
                    cwd=str(self.root), timeout=10
                )
                return True
        except Exception as e:
            print(f"  Rollback error: {e}")
        return False

    def check_after_change(self, file_path: str) -> dict:
        """Quick check after a specific file was changed."""
        pyfile = self.root / file_path
        if not pyfile.exists() or not file_path.endswith(".py"):
            return {"ok": True}

        try:
            source = pyfile.read_text(encoding="utf-8")
            if source.startswith("--- ") and "+++" in source[:100]:
                return {"ok": False, "error": "File contains diff format — not valid Python"}
            ast.parse(source, filename=file_path)
            return {"ok": True}
        except SyntaxError as e:
            return {"ok": False, "error": f"{file_path}:{e.lineno}: {e.msg}"}
