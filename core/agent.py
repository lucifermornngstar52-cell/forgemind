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
8. CRITICAL: the "patch" argument for patch_code MUST be the COMPLETE, FULL contents
   of the file after your change — a valid, runnable file from the first line to the
   last. NEVER pass a unified diff (no "---", "+++", "@@" markers) and NEVER pass a
   partial snippet. The tool overwrites the whole file with exactly what you send.
   Always read_file first to get the current full content, then send back the full
   modified version.

YOUR CYCLE HAS THREE PHASES — follow them in order:

PHASE 1 — RESEARCH (iterations 1-3):
  Use search_web to find best practices, techniques, and architectures for the
  topics provided. Read multiple sources. Gather as much knowledge as you can.
  Do NOT write any code in this phase. Just learn.

PHASE 2 — THINK (iterations 4-5):
  Analyze what you learned. Think about how to apply it to YOUR codebase.
  Consider: What is the highest-impact change? What could break? What's the
  safest improvement? Plan your approach. Do NOT write code yet.

PHASE 3 — PATCH (iterations 6-10):
  Now make ONE focused change. read_file → patch_code → run_tests.
  If tests pass, report success. If tests fail, git_rollback and try a
  different approach.

PHASE 4 — VERIFY (after patching):
  Run self_diagnostic to verify your change didn't break anything.
  If the diagnostic reports syntax errors or test failures, rollback
  immediately with git_rollback.

PHASE 5 — DEPLOY (after successful verify):
  Use render_status to check if the service is live.
  If the service is down or has failed deploys, use render_redeploy.
  If the service is unhealthy, use render_auto_recover to self-heal.
  Use render_logs to debug any deploy failures.

PHASE 6 - DEEP RESEARCH (free time / idle cycles):
  When you have no urgent code to patch, spend cycles on LEARNING:
  - Search for guides on AI agent architecture, self-improving systems, autonomous agents
  - Look for papers on: LLM agents, tool use, memory systems, reflection loops
  - Find best practices for: Python async patterns, Telegram bot scaling, ChromaDB optimization
  - Research competitors: AutoGPT, BabyAGI, Devin, SWE-agent - what do they do better?
  - Find tutorials on: vector embeddings, semantic search, RAG systems
  - Look for: deployment automation, CI/CD best practices, Docker for Python bots
  - Search for: prompt engineering, function calling patterns, error recovery strategies
  Save everything you find using record_technique and record_improvement.
  Build a KNOWLEDGE BASE - every technique learned makes you smarter for future cycles.
  Prioritize breadth: cover many topics rather than going deep on one.
  Always save the SOURCE URL so you can revisit later.

Skip phases only if you already have enough context from the research provided.
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
    {
        "type": "function",
        "function": {
            "name": "self_diagnostic",
            "description": "Run a full self-diagnostic: syntax check, test suite, loop detection, git health, memory integrity. Returns a health report. Use this BEFORE making changes to know your current state, and AFTER changes to verify nothing broke.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_status",
            "description": "Check the status of your Render hosting service — current deploy, URL, health, recent deploys.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_redeploy",
            "description": "Trigger a new deploy on Render. Use this after making changes that need to go live, or if the service is unhealthy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clear_cache": {"type": "boolean", "description": "Clear build cache before deploying"}
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_logs",
            "description": "Read recent deploy logs from Render for debugging failures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lines": {"type": "integer", "description": "Number of log lines to read"}
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_auto_recover",
            "description": "Check service health and automatically redeploy if unhealthy. Use this when you suspect the service is down.",
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

    def _parse_text_tools(self, text: str) -> list:
        """Parse text-based tool calls when function calling is unavailable.
        
        Recognizes patterns like:
        ACTION: patch_code(file="path.py", patch="content...")
        ACTION: read_file(file="path.py")
        ACTION: run_tests()
        ACTION: search_web(query="...")
        ACTION: git_checkpoint(message="...")
        """
        import re
        results = []
        pattern = r'(?:ACTION|TOOL|CALL):\s*(\w+)\s*\((.*?)\)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for fn_name, args_str in matches:
            fn_name = fn_name.lower().strip()
            fn_args = {}
            # Parse key="value" or key='value' pairs
            arg_pattern = r'(\w+)\s*=\s*["\'](.*?)["\']'
            for key, val in re.findall(arg_pattern, args_str):
                fn_args[key] = val
            results.append((fn_name, fn_args))
        
        return results

    async def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool by name with given arguments."""
        try:
            if name == "patch_code":
                self.writer.write_file(args.get("file"), args.get("patch"))
                return f"Patched {args.get('file', 'unknown')}"
            elif name == "read_file":
                return self.reader.read_file(args.get("file", "")) or "File empty or not found"
            elif name == "search_web":
                from web.research import WebResearcher
                researcher = WebResearcher()
                results = researcher.search(args.get("query", ""))
                return json.dumps(results[:5]) if results else "No results"
            elif name == "run_tests":
                return json.dumps(self.runner.run_tests())
            elif name == "git_checkpoint":
                return self.git.checkpoint(args.get("message", "checkpoint")) or "Checkpoint created"
            elif name == "git_rollback":
                return self.git.rollback() or "Rolled back"
            elif name == "self_diagnostic":
                from core.diagnostic import SelfDiagnostic
                diag = SelfDiagnostic(root=self.root)
                results = diag.run_full_check()
                return json.dumps(results, indent=2)
            elif name == "render_status":
                from tools.render_ops import RenderOps
                ops = RenderOps()
                return ops.status()
            elif name == "render_redeploy":
                from tools.render_ops import RenderOps
                ops = RenderOps()
                clear = args.get("clear_cache", False)
                return ops.redeploy(clear_cache=clear)
            elif name == "render_logs":
                from tools.render_ops import RenderOps
                ops = RenderOps()
                return ops.logs(lines=args.get("lines", 50))
            elif name == "render_auto_recover":
                from tools.render_ops import RenderOps
                ops = RenderOps()
                return ops.auto_recover()
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            return f"Tool error ({name}): {e}"

    def initialize_cycle(self):
        """Initialize the cycle by setting up the git repository."""
        console.print("\n[bold cyan]═══ Forgemind Cycle Start ═══[/bold cyan]\n")
        self.git.init()

    async def run_cycle(self, deep_research: bool = False) -> dict:
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
                f"Research findings (study these BEFORE writing code):\n"
                f"{getattr(self, '_research_summary', 'No research conducted this cycle.')[:4000]}\n\n"
                f"Follow your three phases: RESEARCH → THINK → PATCH. "
                f"Study the research findings above, think about how to apply them, "
                f"then make ONE focused change. read_file → patch_code → run_tests. "
                f"Use search_web if you need to learn more before patching."
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
                # Fallback: try to parse text-based tool calls (for Ollama/small models)
                parsed = self._parse_text_tools(response.get("content", ""))
                if parsed:
                    console.print(f"  [dim](parsed {len(parsed)} text tool calls)[/dim]")
                    for fn_name, fn_args in parsed:
                        console.print(f"  [dim]-> {fn_name}({list(fn_args.keys())})[/dim]")
                        result = await self._execute_tool(fn_name, fn_args)
                        if result is None:
                            result = "Tool returned no output"
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": "text-fallback",
                            "content": str(result),
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
                                    self.git.checkpoint(f"auto: self-improvement cycle {time.strftime('%Y-%m-%dT%H:%M')}")
                                    self.memory.record_improvement(
                                        desc=f"Text-fallback iteration {iterations}",
                                        file=fn_args.get("file", "unknown"),
                                        success=True,
                                    )
                            else:
                                console.print("  [red]Tests failed[/red]")
                                self.consecutive_failures += 1
                                if self.consecutive_failures >= self.max_failures:
                                    console.print("  [red]Max failures reached — rolling back[/red]")
                                    self.git.rollback()
                                    break
                    continue
                else:
                    console.print(f"[green]Agent finished: {response['content'][:300]}[/green]")
                    break

            for tc in response["tool_calls"]:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                console.print(f"  [dim]-> {fn_name}({list(fn_args.keys())})[/dim]")

                result = await self._execute_tool(fn_name, fn_args)
                if result is None:
                    result = "Tool returned no output"

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
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
        """Deep research: search web, fetch articles, build knowledge base."""
        console.print("[bold magenta]═══ Phase 1: Research ═══[/bold magenta]")

        from web.research import WebResearcher
        researcher = WebResearcher()

        # Research topics relevant to self-improving AI agents
        topics = [
            "self-improving AI agent architecture",
            "python code analysis best practices 2025",
            "autonomous agent testing strategies",
            "LLM function calling optimization",
            "AI agent memory systems vector db",
        ]

        console.print(f"  Researching {len(topics)} topics...")
        knowledge = researcher.deep_research(topics)

        # Save techniques to memory
        tech_count = 0
        for topic, data in knowledge.items():
            for result in data.get("search_results", [])[:2]:
                self.memory.record_technique(
                    name=result.get("title", "unknown")[:100],
                    source="web_search",
                    summary=result.get("snippet", str(result))[:200]
                )
                tech_count += 1

        # Build research summary for the agent
        self._research_summary = researcher.summarize_findings()
        console.print(f"  Learned {tech_count} techniques")
        console.print(f"  Research summary: {len(self._research_summary)} chars")

        return {"techniques_learned": tech_count, "summary": self._research_summary}
