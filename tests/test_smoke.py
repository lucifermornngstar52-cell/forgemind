"""Smoke tests — Forgemind must keep these passing at all times."""

import pytest
from tools.reader import CodeReader
from tools.writer import CodeWriter
from tools.runner import Runner
from tools.git_ops import GitOps
from memory.store import MemoryStore
from core.planner import Planner
from core.llm import LLM


def test_code_reader_lists_files():
    reader = CodeReader(".")
    files = reader.list_files()
    assert len(files) > 0
    assert any("agent.py" in f for f in files)


def test_code_reader_gets_structure():
    reader = CodeReader(".")
    structure = reader.get_structure()
    assert isinstance(structure, dict)
    assert len(structure) > 0


def test_memory_store_loads():
    store = MemoryStore("./memory/store.json")
    assert isinstance(store.data, dict)
    assert "improvements" in store.data
    assert "failures" in store.data


def test_memory_record():
    store = MemoryStore("./memory/test_store.json")
    store.record_improvement("test", "test.py", True, "test details")
    assert len(store.data["improvements"]) >= 1
    assert store.get_success_rate() > 0


def test_writer_diff():
    writer = CodeWriter(".")
    diff = writer.diff("nonexistent.py", "new content")
    assert isinstance(diff, str)


def test_git_ops_init():
    git = GitOps(".")
    # Should not crash
    git.init()


def test_config_exists():
    from pathlib import Path
    assert Path("config.yaml").exists()


def test_requirements_exist():
    from pathlib import Path
    assert Path("requirements.txt").exists()
