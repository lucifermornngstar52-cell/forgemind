"""FORGEMIND Agent — the mind that forges itself.

This module is the core of the FORGEMIND self-improving agent.
Each cycle: read code → find weaknesses → plan → patch → test → commit/rollback.
"""

import json
from rich.console import Console

from core.llm import LLM
from core.planner import Planner
from tools.reader import CodeReader
from tools.writer import CodeWriter
from tools.runner import Runner
from tools.git_ops import GitOps
from memory.store import MemoryStore

console = Console()

AGENT_SYSTEM = """You are FORGEMIND — a self-improving AI agent that modifies its own source code.

Your mission: become the best autonomous AI agent possible.

Rules:
1. Make ONE change per iteration, then run tests
2. If tests fail, the safety system will rollback automatically
3. Prioritize: bug fixes > test coverage > performance > new features > refactoring
4. Never delete or stub out imports — they are critical
5. Never replace code with comments like "# ... unchanged"
6. Keep changes small and focused
7. Document what you changed and why
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "patch_code",
            "description": "Apply a patch to a source file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "File path to patch"},
                    "patch": {"type": "string", "description": "The new file content or unified diff"},
                },
                "required": ["file", "patch"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "File path to read"},
                },
                "required": ["file"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for techniques and best practices",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the test suite and return results",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_checkpoint",
            "description": "Create a git checkpoint (commit)",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_rollback",
            "description": "Rollback to previous checkpoint",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class ForgemindAgent:
    """The mind that forges itself. Each cycle makes it better."""

    def __init__(self, config: dict, root: str = "."):
        self.config = config
        self.root = root
        self.llm = LLM(config.get("llm", {}))
        self.planner = Planner(self.llm)
        self.reader = CodeReader(root)
        self.writer = CodeWriter(root)
        self.runner = Runner(root)
        self.git = GitOps(root)
        self.memory = MemoryStore(config.get("memory", {}).get("store_path", "./memory/store.json"))

        self.max_iterations = config.get("agent", {}).get("max_iterations", 10)
        self.max_failures = config.get("safety", {}).get("max_consecutive_failures", 3)

        self.messages = []
        self.consecutive_failures = 0

    async def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool by name with given arguments."""
        if name == "patch_code":
            return self.writer.write_file(args.get("file"), args.get("patch"))
        elif name == "read_file":
            return self.reader.read_file(args.get("file"))
        elif name == "search_web":
            from web.research import WebResearcher
            researcher = WebResearcher()
            results = researcher.search(args.get("query", ""))
            return json.dumps(results[:5])
        elif name == "run_tests":
            return json.dumps(self.runner.run_tests())
        elif name == "git_checkpoint":
            return self.git.checkpoint(args.get("message", "checkpoint"))
        elif name == "git_rollback":
            return self.git.rollback()
        else:
            return f"Unknown tool: {name}"

    def initialize_cycle(self):
        """Initialize the cycle by setting up the git repository."""
        console.print("\n[bold cyan]═══ Forgemind Cycle Start ═══[/bold cyan]\n")
        self.git.init()

    async def run_cycle(self) -> dict:
        """Run one full self-improvement cycle."""
        self.initialize_cycle()

        # Step 1: Analyze
        console.print("[yellow]Step 1: Analyzing code...[/yellow]")
        structure = self.reader.get_structure()
        weaknesses = self.reader.find_weaknesses()
        console.print(f"  Found {len(weaknesses)} potential improvements")

        # Step 2: Load memory
        memory_summary = self.memory.summary()
        console.print(f"  Memory: {memory_summary.replace(chr(10), ' | ')}")

        # Step 3: Plan
        console.print("[yellow]Step 2: Planning improvements...[/yellow]")
        plan = self.planner.create_plan(structure, weaknesses, memory_summary)
        console.print(f"  Plan: {len(plan)} steps")

        # Step 4: Get semantic context
        semantic_context = ""
        if plan:
            first_action = plan[0].get("action", "improvement")
            semantic_context = self.memory.get_semantic_context(first_action)
            if semantic_context and "No relevant" not in semantic_context:
                console.print(f"[dim]  Semantic memory: found relevant past experiences[/dim]")

        # Step 5: Execute
        checkpoint_before = self.git.current_hash()
        console.print(f"[yellow]Step 3: Executing (checkpoint: {checkpoint_before[:8]})...[/yellow]")

        self.messages = [
            {"role": "system", "content": AGENT_SYSTEM},
            {"role": "user", "content": (
                f"Codebase structure: {json.dumps(structure, indent=2)[:3000]}\n\n"
                f"Weaknesses found: {json.dumps(weaknesses[:10], indent=2)[:2000]}\n\n"
                f"Improvement plan: {json.dumps(plan, indent=2)[:2000]}\n\n"
                f"Memory: {memory_summary}\n\n"
                f"Semantic context (past experiences): {semantic_context[:1500]}\n\n"
                f"Begin improving yourself. Start with the highest-priority item. "
                f"Make ONE change, run tests, then report what you improved. "
                f"Use research tools if you need to learn new techniques."
            )},
        ]

        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1
            console.print(f"\n[cyan]── Iteration {iterations}/{self.max_iterations} ──[/cyan]")

            response = self.llm.chat(self.messages, tools=TOOLS)

            assistant_msg = {"role": "assistant", "content": response.get("content") or ""}
            if response.get("tool_calls"):
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in response["tool_calls"]
                ]
            self.messages.append(assistant_msg)

            if not response.get("tool_calls"):
                console.print(f"[green]Agent finished: {response['content'][:300]}[/green]")
                break

            for tc in response["tool_calls"]:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                console.print(f"  [dim]-> {fn_name}({list(fn_args.keys())})[/dim]")

                result = await self._execute_tool(fn_name, fn_args)

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

                if fn_name == "run_tests":
                    try:
                        test_result = json.loads(result)
                    except json.JSONDecodeError:
                        test_result = {"passed": False, "stderr": result}

                    if test_result.get("passed"):
                        console.print("  [green]Tests passed[/green]")
                        self.consecutive_failures = 0

                        if self.config.get("agent", {}).get("auto_commit", True):
                            commit = self.git.checkpoint(f"improvement: iteration {iterations}")
                            console.print(f"  [green]Committed: {commit[:8]}[/green]")
                            self.memory.record_improvement(
                                f"Iteration {iterations}", "multiple", True,
                                "Tests passed after change"
                            )
                    else:
                        console.print("  [red]Tests failed[/red]")
                        self.consecutive_failures += 1

                        self.memory.record_improvement(
                            f"Iteration {iterations}", "multiple", False,
                            test_result.get("stderr", "")[:500]
                        )

                        if self.consecutive_failures >= self.max_failures:
                            console.print(f"  [red]Max failures. Rolling back.[/red]")
                            self.git.rollback(checkpoint_before)
                            self.consecutive_failures = 0
                            break

        console.print(f"\n[bold cyan]═══ Cycle Complete ═══[/bold cyan]")
        console.print(f"Iterations: {iterations}")
        console.print(f"Memory:\n{self.memory.summary()}")

        return {
            "iterations": iterations,
            "improvements": len(self.memory.data["improvements"]),
            "failures": len(self.memory.data["failures"]),
            "success_rate": self.memory.get_success_rate(),
        }

    async def research_and_learn(self) -> dict:
        """Research external techniques and learn from them."""
        console.print("[magenta]Researching external techniques...[/magenta]")
        from web.research import WebResearcher
        researcher = WebResearcher()
        techniques = researcher.search("best practices for autonomous AI agents python 2024 2025")
        for tech in techniques[:5]:
            self.memory.add_technique(
                name=tech.get("title", "unknown"),
                source="web_search",
                summary=tech.get("snippet", str(tech)[:200])
            )
        return {"techniques_learned": len(techniques)}
