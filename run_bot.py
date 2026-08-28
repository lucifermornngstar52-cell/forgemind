#!/usr/bin/env python3
"""FORGEMIND Telegram Bot Runner.

Starts the Telegram bot for direct user interaction.
Usage: python run_bot.py
"""

import asyncio
import os
import yaml
from pathlib import Path
from rich.console import Console

console = Console()

def load_config() -> dict:
    config_path = Path("config.yaml")
    if config_path.exists():
        return yaml.safe_load(config_path.read_text())
    return {}

async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        console.print("[bold red]TELEGRAM_BOT_TOKEN not set![/bold red]")
        return

    config = load_config()

    from tools.telegram_bot import ForgemindTelegramBot
    bot = ForgemindTelegramBot(token, config)

    console.print("[bold cyan]╔══════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  FORGEMIND Telegram Bot Online   ║[/bold cyan]")
    console.print("[bold cyan]║  @Fermaindbot                    ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════╝[/bold cyan]")

    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
