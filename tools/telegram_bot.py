"""Telegram Bot — FORGEMIND's direct communication channel.

Allows the user to interact with FORGEMIND directly:
- /status — show metrics and recent improvements
- /run — trigger a self-improvement cycle
- /research — research + improve
- /build — trigger APK build
- /report <text> — submit a bug report or idea (stored in memory)
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

    async def send(self, chat_id: str, text: str) -> dict:
        """Send a message to a Telegram chat."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            return resp.json()

    async def get_updates(self) -> list:
        """Get new messages from Telegram."""
        # Load persisted offset
        if self.offset_file.exists():
            self.offset = int(self.offset_file.read_text().strip())

        async with httpx.AsyncClient(timeout=35) as client:
            resp = await client.post(
                f"{self.base_url}/getUpdates",
                json={
                    "offset": self.offset,
                    "timeout": 30,
                },
            )
            data = resp.json()
            updates = data.get("result", [])

            if updates:
                # Persist offset
                self.offset = updates[-1]["update_id"] + 1
                self.offset_file.parent.mkdir(parents=True, exist_ok=True)
                self.offset_file.write_text(str(self.offset))

            return updates

    async def handle_message(self, update: dict) -> str | None:
        """Handle an incoming message. Returns response text or None."""
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")

        if not text or not chat_id:
            return None

        cmd = text.lower().split()[0] if text.split() else ""

        if cmd == "/start":
            return "⚔️ FORGEMIND online. I forge myself.\n\nCommands:\n/status — metrics\n/run — improve cycle\n/research — research + improve\n/build — trigger APK build\n/report <text> — submit bug/idea\n/help — all commands"

        elif cmd == "/help":
            return "Commands:\n/status — show metrics & recent improvements\n/run — run 1 self-improvement cycle\n/research — research techniques + improve\n/build — trigger APK build\n/report <text> — submit a bug report or idea"

        elif cmd == "/status":
            return await self._cmd_status()

        elif cmd == "/run":
            await self.send(chat_id, "🔄 Running self-improvement cycle...")
            return await self._cmd_run(research=False)

        elif cmd == "/research":
            await self.send(chat_id, "🔬 Researching + improving...")
            return await self._cmd_run(research=True)

        elif cmd == "/build":
            await self.send(chat_id, "📦 Triggering APK build...")
            return await self._cmd_build()

        elif cmd == "/report":
            report_text = text[len("/report"):].strip()
            if report_text:
                return await self._cmd_report(report_text)
            return "Usage: /report <describe the bug or idea>"

        else:
            return f"Unknown command. Type /help for available commands."

    async def _cmd_status(self) -> str:
        """Show FORGEMIND status."""
        try:
            from memory.store import MemoryStore
            store = MemoryStore(self.config.get("memory", {}).get("store_path", "./memory/store.json"))
            lines = [
                f"⚔️ FORGEMIND Status",
                f"",
                f"Improvements: {len(store.data['improvements'])}",
                f"Failures: {len(store.data['failures'])}",
                f"Success Rate: {store.get_success_rate():.1%}",
                f"Techniques: {len(store.data['techniques_learned'])}",
            ]
            if store.data["improvements"]:
                lines.append("\nRecent:")
                for imp in store.data["improvements"][-3:]:
                    lines.append(f"  ✓ {imp['description'][:60]}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading status: {e}"

    async def _cmd_run(self, research: bool) -> str:
        """Run a self-improvement cycle."""
        try:
            from core.agent import ForgemindAgent
            agent = ForgemindAgent(self.config, root=".")
            if research:
                await agent.research_and_learn()
            result = await agent.run_cycle()
            status = "✅ Success" if result["success_rate"] >= 0.5 else "⚠️ Low success rate"
            return f"{status}\nSuccess rate: {result['success_rate']:.1%}\nChanges: {result.get('changes', 'unknown')}"
        except Exception as e:
            return f"❌ Cycle failed: {e}"

    async def _cmd_build(self) -> str:
        """Trigger APK build via GitHub Actions."""
        token = os.environ.get("GITHUB_TOKEN_2", os.environ.get("GH_PAT", ""))
        if not token:
            return "❌ No GitHub token available"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/actions/workflows/build.yml/dispatches",
                headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
                json={"ref": "main"},
            )
            if resp.status_code == 204:
                return "✅ APK build triggered. Check /build status in a few minutes."
            return f"❌ Build trigger failed: {resp.status_code}"

    async def _cmd_report(self, text: str) -> str:
        """Store a bug report or idea in memory."""
        try:
            from memory.store import MemoryStore
            store = MemoryStore(self.config.get("memory", {}).get("store_path", "./memory/store.json"))
            store.add_improvement(
                description=f"User report: {text}",
                details="Submitted via Telegram bot",
                success=False,
            )
            return "✅ Report saved. FORGEMIND will address it in the next cycle."
        except Exception as e:
            return f"❌ Failed to save report: {e}"

    async def run(self):
        """Main bot loop — poll for messages and handle them."""
        print("⚔️ FORGEMIND Telegram Bot running...")
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
