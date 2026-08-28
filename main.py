#!/usr/bin/env python3
"""
Forgemind — Self-Improving AI Agent
Entry point.

Usage:
    python main.py              # Run one improvement cycle
    python main.py --research   # Research techniques then improve
    python main.py --loop N     # Run N cycles
    python main.py --status     # Show memory & metrics
"""

import asyncio
import argparse
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def load_config() -> dict:
    """
    Load the configuration from a YAML file.

    Returns:
        dict: The configuration settings.
    """
    config_path = Path("config.yaml")
    if config_path.exists():
        return yaml.safe_load(config_path.read_text())
    return {}


async def run_cycle(research: bool = False) -> dict:
    """
    Execute a single improvement cycle.

    Args:
        research (bool): If True, perform research before the cycle.

    Returns:
        dict: The result of the cycle execution.
    """
    from core.agent import ForgemindAgent

    config = load_config()
    agent = ForgemindAgent(config, root=".")

    if research:
        console.print("[bold magenta]Phase 0: Researching external techniques...[/bold magenta]")
        await agent.research_and_learn()

    return await agent.run_cycle()


async def run_loops(count: int, research: bool = False) -> None:
    """
    Run multiple improvement cycles.

    Args:
        count (int): Number of cycles to run.
        research (bool): If True, perform research during the first cycle.
    """
    for i in range(count):
        console.print(f"\n[bold blue]═══════ CYCLE {i+1}/{count} ═══════[/bold blue]")
        result = await run_cycle(research=(research and i == 0))

        # Safety: stop if success rate drops below 30%
        if result["success_rate"] > 0 and result["success_rate"] < 0.3:
            console.print("[bold red]Success rate too low. Stopping for safety.[/bold red]")
            break


def show_status() -> None:
    """
    Display the current status of the agent's memory and metrics.
    """
    from memory.store import MemoryStore
    config = load_config()
    store = MemoryStore(config.get("memory", {}).get("store_path", "./memory/store.json"))

    table = Table(title="Forgemind Status", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="green")

    table.add_row("Improvements", str(len(store.data["improvements"])))
    table.add_row("Failures", str(len(store.data["failures"])))
    table.add_row("Success Rate", f"{store.get_success_rate():.1%}")
    table.add_row("Techniques Learned", str(len(store.data["techniques_learned"])))

    console.print(table)

    if store.data["improvements"]:
        console.print("\n[bold]Recent improvements:[/bold]")
        for imp in store.data["improvements"][-5:]:
            console.print(f"  ✓ {imp['description']} ({imp['timestamp'][:10]})")

    if store.data["failures"]:
        console.print("\n[bold red]Recent failures:[/bold red]")
        for fail in store.data["failures"][-3:]:
            console.print(f"  ✗ {fail['description']} — {fail.get('details', '')[:100]}")


def main():
    """
    Parse command-line arguments and initiate the appropriate action.
    """
    parser = argparse.ArgumentParser(description="Forgemind — Self-Improving AI Agent")
    parser.add_argument("--research", action="store_true", help="Research techniques before improving")
    parser.add_argument("--loop", type=int, default=1, help="Number of cycles to run")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    console.print("[bold cyan]╔══════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║        SELFFORGE v0.1.0          ║[/bold cyan]")
    console.print("[bold cyan]║   Self-Improving AI Agent         ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════╝[/bold cyan]")

    asyncio.run(run_loops(args.loop, args.research))


if __name__ == "__main__":
    main()
