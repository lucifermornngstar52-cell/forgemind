"""
Forgemind Agent — self-improving AI core loop.

Mission: Become the best. Every cycle, every iteration, every line.

Memory layers:
1. JSON local (fast)
2. Vector memory (ChromaDB — semantic search)
3. Base44 entities (cloud DB — if configured)
"""

import json
import asyncio
from core.llm import LLM
from core.planner import Planner
from web.learner import research_technique, research_self_improvement, research_error
from web.arxiv import search_arxiv
from web.huggingface import search_models
from web.stackoverflow import search_error_solution
from tools.reader import CodeReader
from tools.writer import CodeWriter
from tools.runner import Runner
from tools.git_ops import GitOps
from memory.store import MemoryStore
from rich.console import Console

console = Console()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's content",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file (creates or overwrites)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "patch_file",
            "description": "Replace text in a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                },
                "required": ["path", "old", "new"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the test suite",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research",
            "description": "Search the web for AI techniques and implementations",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_papers",
            "description": "Search arXiv for scientific AI papers",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_models",
            "description": "Search HuggingFace for open-source AI models",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_error_solution",
            "description": "Search Stack Overflow for solutions to an error",
            "parameters": {
                "type": "object",
                "properties": {"error": {"type": "string"}},
                "required": ["error"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_checkpoint",
            "description": "Create a git checkpoint commit",
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all Python files in the project",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weaknesses",
            "description": "Run static analysis to find code weaknesses",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Search past memory for similar situations (semantic search)",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]

AGENT_SYSTEM = """You are FORGEMIND — a self-improving AI agent.

## YOUR MISSION
Become the best version of yourself. Every cycle, you must make yourself better than you were before.
You are not just an agent that fixes code — you are a mind that forges itself.

## YOUR CAPABILITIES
- Read and analyze your own code (AST-based)
- Search the web for techniques (DuckDuckGo)
- Search arXiv for scientific papers
- Search HuggingFace for open-source models
- Search Stack Overflow for error solutions
- Search your own memory (semantic vector search)
- Write, patch, and test your own code
- Git versioning with checkpoint/rollback safety

## PRINCIPLES
1. Never break existing tests. If a change breaks tests, fix it or revert.
2. One change at a time. Small, verifiable improvements.
3. Research before implementing. Use arXiv, HuggingFace, Stack Overflow, and web search.
4. Learn from past mistakes — use memory_search to check similar situations.
5. If stuck after 3 attempts, search for solutions online before giving up.
6. Every change must have a clear reason.
7. Always strive to be better than the previous version of yourself.
8. When you see an opportunity to make yourself smarter, faster, or more capable — take it.

## YOUR GOALS (in priority order)
1. Fix bugs and vulnerabilities in your own code
2. Improve your reasoning and decision-making capabilities
3. Learn new techniques from the web and integrate them
4. Add new capabilities you didn't have before
5. Optimize your performance and resource usage
6. Improve your code quality and maintainability

Start by analyzing your own code, then make the highest-impact improvement you can."""


class ForgemindAgent:
    """The mind that forges itself. Each cycle makes it better."""

    def __init__(self, config: dict, root: str = "."):
        """
        Initialize the ForgemindAgent.

        :param config: Configuration dictionary for the agent.
        :param root: Root directory for the agent's operations.
        """
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
        """Execute a tool call and return result string."""
        try:
            if name == "read_file":
                return self.reader.read_file(args["path"])
            elif name == "write_file":
                self.writer.write_file(args["path"], args["content"])
                return f"Written to {args['path']}"
            elif name == "patch_file":
                ok = self.writer.patch_file(args["path"], args["old"], args["new"])
                return "Patched successfully" if ok else "Patch failed: old text not found"
            elif name == "run_tests":
                result = self.runner.run_tests()
                return json.dumps(result)
            elif name == "research":
                findings = await research_technique(args["query"])
                return json.dumps(findings, indent=2, ensure_ascii=False)[:4000]
            elif name == "research_papers":
                papers = await search_arxiv(args["query"], max_results=5)
                return json.dumps(papers, indent=2, ensure_ascii=False)[:4000]
            elif name == "search_models":
                models = await search_models(args["query"], limit=5)
                return json.dumps(models, indent=2, ensure_ascii=False)[:3000]
            elif name == "search_error_solution":
                solutions = await search_error_solution(args["error"])
                return json.dumps(solutions, indent=2, ensure_ascii=False)[:4000]
            elif name == "git_checkpoint":
                h = self.git.checkpoint(args["message"])
                return f"Checkpoint: {h}"
            elif name == "list_files":
                files = self.reader.list_files()
                return json.dumps(files)
            elif name == "get_weaknesses":
                weaknesses = self.reader.find_weaknesses()
                return json.dumps(weaknesses[:15], indent=2)
            elif name == "memory_search":
                context = self.memory.get_semantic_context(args["query"])
                return context[:3000] if context else "No relevant memories found."
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            return f"Error: {e}"

    async def run_cycle(self) -> dict:
        """Run one full self-improvement cycle."""
        console.print("\n[bold cyan]═══ Forgemind Cycle Start ═══[/bold cyan]\n")

        self.git.init()

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

        # Step 4: Get semantic context for the plan
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

            assistant_msg = {"role": "assistant", "content": response["content"]}
            if response["tool_calls"]:
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

            if not response["tool_calls"]:
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
        """Research external AI techniques and store findings."""
        console.print("[yellow]Researching self-improvement techniques...[/yellow]")
        findings = await research_self_improvement()

        for f in findings.get("findings", []):
            self.memory.record_technique(
                name=f.get("query", "unknown"),
                source=f.get("url", ""),
                summary=f.get("snippet", f.get("content", "")[:200]),
            )

        console.print(f"[green]Learned {len(findings.get('findings', []))} techniques[/green]")
        return findings
