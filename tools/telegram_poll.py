#!/usr/bin/env python3
"""FORGEMIND Telegram Polling Bot — for GitHub Actions.

Runs in a CI job, checks for new messages, responds, exits.
Triggered every 5 minutes by scheduled workflow.
"""

import os
import json
import httpx
from pathlib import Path


def send_message(token: str, chat_id: int, text: str) -> dict:
    """Send a message via Telegram API."""
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )
        return resp.json()


def get_updates(token: str, offset: int = 0) -> list:
    """Get new messages from Telegram."""
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            f"https://api.telegram.org/bot{token}/getUpdates",
            json={"offset": offset, "timeout": 0, "limit": 10},
        )
        data = resp.json()
        return data.get("result", [])


def handle_command(cmd: str, args: str, chat_id: int, token: str) -> str:
    """Handle a command and return response text."""
    cmd = cmd.lower()

    if cmd == "/start" or cmd == "/help":
        return (
            "FORGEMIND online. I forge myself.\n\n"
            "Commands:\n"
            "/status — metrics\n"
            "/run — improve cycle\n"
            "/build — trigger APK build\n"
            "/apk — get latest APK link\n"
            "/report <text> — bug or idea"
        )

    elif cmd == "/apk":
        gh_token = os.environ.get("GH_PAT", "")
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/releases/latest",
                headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"},
            )
            data = resp.json()
            if data.get("assets"):
                asset = data["assets"][0]
                return f"FORGEMIND APK\nVersion: {data.get('name','?')}\nSize: {asset['size']//1024//1024}MB\nDownload: {asset['browser_download_url']}"
            return "No APK releases yet."

    elif cmd == "/status":
        try:
            from memory.store import MemoryStore
            store = MemoryStore("./memory/store.json")
            return (
                f"FORGEMIND Status\n"
                f"Improvements: {len(store.data['improvements'])}\n"
                f"Failures: {len(store.data['failures'])}\n"
                f"Success Rate: {store.get_success_rate():.1%}\n"
                f"Techniques: {len(store.data['techniques_learned'])}"
            )
        except Exception as e:
            return f"Status error: {e}"

    elif cmd == "/build":
        gh_token = os.environ.get("GH_PAT", "")
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/actions/workflows/build.yml/dispatches",
                headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"},
                json={"ref": "main"},
            )
            if resp.status_code == 204:
                return "APK build triggered! I'll send the link when ready."
            return f"Build failed: {resp.status_code}"

    elif cmd == "/run":
        # Trigger the auto-cycle workflow
        gh_token = os.environ.get("GH_PAT", "")
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://api.github.com/repos/lucifermornngstar52-cell/forgemind/actions/workflows/auto-cycle.yml/dispatches",
                headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"},
                json={"ref": "main"},
            )
            if resp.status_code == 204:
                return "Self-improvement cycle triggered! Check /status in a few minutes."
            return f"Cycle trigger failed: {resp.status_code}"

    elif cmd == "/report":
        if args:
            try:
                from memory.store import MemoryStore
                store = MemoryStore("./memory/store.json")
                store.add_improvement(
                    description=f"User report: {args}",
                    details="Submitted via Telegram bot (CI)",
                    success=False,
                )
                return "Report saved. FORGEMIND will address it next cycle."
            except Exception as e:
                return f"Failed to save: {e}"
        return "Usage: /report <describe the bug or idea>"

    return f"Unknown command: {cmd}. Type /help"


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set")
        return

    # Load offset from git-tracked file
    offset_file = Path(".agents/bot_offset.txt")
    offset = int(offset_file.read_text().strip()) if offset_file.exists() else 0

    updates = get_updates(token, offset)
    if not updates:
        print("No new messages")
        return

    print(f"Processing {len(updates)} update(s)")
    for update in updates:
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")
        if not text or not chat_id:
            continue

        parts = text.split(maxsplit=1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        print(f"  {cmd} from {chat_id}")
        response = handle_command(cmd, args, chat_id, token)
        if response:
            send_message(token, chat_id, response)
            print(f"  -> sent response")

    # Save offset
    new_offset = updates[-1]["update_id"] + 1
    offset_file.parent.mkdir(parents=True, exist_ok=True)
    offset_file.write_text(str(new_offset))

    # Commit offset back to repo
    import subprocess
    subprocess.run(["git", "config", "user.name", "Forgemind Bot"], check=True)
    subprocess.run(["git", "config", "user.email", "forgemind@bot.local"], check=True)
    subprocess.run(["git", "add", str(offset_file)], check=True)
    subprocess.run(["git", "commit", "-m", f"chore: update bot offset to {new_offset}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"Offset saved: {new_offset}")


if __name__ == "__main__":
    main()
