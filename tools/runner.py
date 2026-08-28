"""Runner — executes builds and tests, captures output."""

import subprocess
from pathlib import Path


class Runner:
    def __init__(self, root: str = "."):
        self.root = Path(root)

    def run_tests(self) -> dict:
        """Run pytest and return result."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=str(self.root),
            timeout=120,
        )
        return {
            "passed": result.returncode == 0,
            "stdout": result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout,
            "stderr": result.stderr[-4000:] if len(result.stderr) > 4000 else result.stderr,
            "returncode": result.returncode,
        }

    def run_command(self, cmd: list, timeout: int = 60) -> dict:
        """Run arbitrary command and return output."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.root),
            timeout=timeout,
        )
        return {
            "passed": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "returncode": result.returncode,
        }

    def lint(self) -> dict:
        """Run basic Python syntax check."""
        result = subprocess.run(
            ["python", "-m", "py_compile"] + [
                str(f) for f in self.root.rglob("*.py")
                if ".git" not in str(f) and "__pycache__" not in str(f)
            ],
            capture_output=True,
            text=True,
            cwd=str(self.root),
            timeout=60,
        )
        return {
            "passed": result.returncode == 0,
            "stderr": result.stderr[-4000:],
        }
