"""Telegram Bot — FORGEMIND's direct communication channel.

Commands:
- /status — show metrics and recent improvements
- /run — trigger a self-improvement cycle
- /research — research + improve
- /build — trigger APK build
- /report <text> — submit a bug report or idea
- /help — show commands
"""

import os
import json
import asyncio
import httpx
from pathlib import Path


class ForgemindTelegramBot:
    """Lightweight Telegram bot for FORGEMIND."""

    def __init__(self, token: str, config: dict = None):
        self.token = token
        self.config = config or {}
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.offset_file = Path(".agents/bot_offset.txt")
        self.allowed_chat_ids = set()  # empty = allow all

    async def send(self, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
        """Send a message to a Telegram chat."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            )
            return resp.json()

    async def send_apk_link(self, chat_id: int) -> dict:
        """Fetch latest APK release and send download link."""
        token = os.environ.get("GITHUB_TOKEN_2", "")
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/releases/latest",
                headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            )
            data = resp.json()
            if data.get("assets"):
                asset = data["assets"][0]
                text = (
                    f"FORGEMIND APK ready!\n\n"
                    f"Version: {data.get('name', 'unknown')}\n"
                    f"Size: {asset['size'] // 1024 // 1024}MB\n"
                    f"Download: {asset['browser_download_url']}"
                )
                return await self.send(chat_id, text)
            return await self.send(chat_id, "No APK releases found yet.")

    async def get_updates(self) -> list:
        """Get new messages from Telegram."""
        if self.offset_file.exists():
            self.offset = int(self.offset_file.read_text().strip())
        async with httpx.AsyncClient(timeout=35) as client:
            resp = await client.post(
                f"{self.base_url}/getUpdates",
                json={"offset": self.offset, "timeout": 30},
            )
            data = resp.json()
            updates = data.get("result", [])
            if updates:
                self.offset = updates[-1]["update_id"] + 1
                self.offset_file.parent.mkdir(parents=True, exist_ok=True)
                self.offset_file.write_text(str(self.offset))
            return updates

    async def handle_message(self, update: dict) -> str | None:
        """Handle an incoming message."""
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")
        if not text or not chat_id:
            return None

        cmd_parts = text.split(maxsplit=1)
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""

        if cmd == "/start":
            return (
                "FORGEMIND online. I forge myself.\n\n"
                "Commands:\n"
                "/status — metrics\n"
                "/run — improve cycle\n"
                "/research — research + improve\n"
                "/build — trigger APK build\n"
                "/apk — get latest APK download link\n"
                "/report <text> — submit bug/idea\n"
                "/help — all commands"
            )

        elif cmd == "/help":
            return (
                "Commands:\n"
                "/status — show metrics & recent improvements\n"
                "/run — run 1 self-improvement cycle\n"
                "/research — research techniques + improve\n"
                "/build — trigger APK build\n"
                "/apk — get latest APK download link\n"
                "/report <text> — submit a bug report or idea"
            )

        elif cmd == "/status":
            return await self._cmd_status()

        elif cmd == "/run":
            await self.send(chat_id, "Running self-improvement cycle...")
            return await self._cmd_run(research=False)

        elif cmd == "/research":
            await self.send(chat_id, "Researching + improving...")
            return await self._cmd_run(research=True)

        elif cmd == "/build":
            await self.send(chat_id, "Triggering APK build...")
            return await self._cmd_build(chat_id)

        elif cmd == "/apk":
            return await self.send_apk_link(chat_id)

        elif cmd == "/report":
            if args:
                return await self._cmd_report(args)
            return "Usage: /report <describe the bug or idea>"

        else:
            return "Unknown command. Type /help for available commands."

    async def _cmd_status(self) -> str:
        try:
            from memory.store import MemoryStore
            store = MemoryStore(self.config.get("memory", {}).get("store_path", "./memory/store.json"))
            lines = [
                f"FORGEMIND Status\n",
                f"Improvements: {len(store.data['improvements'])}",
                f"Failures: {len(store.data['failures'])}",
                f"Success Rate: {store.get_success_rate():.1%}",
                f"Techniques: {len(store.data['techniques_learned'])}",
            ]
            if store.data["improvements"]:
                lines.append("\nRecent:")
                for imp in store.data["improvements"][-3:]:
                    lines.append(f"  + {imp['description'][:60]}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading status: {e}"

    async def _cmd_run(self, research: bool) -> str:
        try:
            from core.agent import ForgemindAgent
            agent = ForgemindAgent(self.config, root=".")
            if research:
                await agent.research_and_learn()
            result = await agent.run_cycle()
            status = "Success" if result["success_rate"] >= 0.5 else "Low success rate"
            return f"{status}\nSuccess rate: {result['success_rate']:.1%}"
        except Exception as e:
            return f"Cycle failed: {e}"

    async def _cmd_build(self, chat_id: int) -> str:
        token = os.environ.get("GITHUB_TOKEN_2", "")
        if not token:
            return "No GitHub token available"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/actions/workflows/build.yml/dispatches",
                headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
                json={"ref": "main"},
            )
            if resp.status_code == 204:
                # Wait for build in background, then send APK link
                asyncio.create_task(self._wait_for_build(chat_id))
                return "APK build triggered. I'll send the download link when it's ready."
            return f"Build trigger failed: {resp.status_code}"

    async def _wait_for_build(self, chat_id: int):
        """Poll GitHub Actions and send APK link when build completes."""
        token = os.environ.get("GITHUB_TOKEN_2", "")
        await asyncio.sleep(15)  # Wait for run to appear
        for _ in range(40):  # Up to ~10 minutes
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/actions/runs?per_page=1",
                        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
                    )
                    run = resp.json()["workflow_runs"][0]
                    if run["status"] == "completed":
                        if run["conclusion"] == "success":
                            await asyncio.sleep(5)  # Wait for release to be created
                            await self.send_apk_link(chat_id)
                        else:
                            await self.send(chat_id, f"APK build failed: {run['conclusion']}")
                        return
            except Exception:
                pass
            await asyncio.sleep(15)

    async def _cmd_report(self, text: str) -> str:
        try:
            from memory.store import MemoryStore
            store = MemoryStore(self.config.get("memory", {}).get("store_path", "./memory/store.json"))
            store.add_improvement(
                description=f"User report: {text}",
                details="Submitted via Telegram bot",
                success=False,
            )
            return "Report saved. FORGEMIND will address it in the next cycle."
        except Exception as e:
            return f"Failed to save report: {e}"

    async def run(self):
        """Main bot loop — poll for messages and handle them."""
        print("FORGEMIND Telegram Bot running...")
        # Send startup notification
        await self.send(7500697130, "FORGEMIND bot online. I forge myself.\nType /help for commands.")
        while True:
            try:
                updates = await self.get_updates()
                for update in updates:
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    if chat_id and text:
                        print(f"Received: {text} from {chat_id}")
                        response = await self.handle_message(update)
                        if response:
                            await self.send(chat_id, response)
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)
