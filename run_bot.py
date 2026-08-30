#!/usr/bin/env python3
"""FORGEMIND Telegram Bot — webhook + polling hybrid for Render.com.

Uses webhook when RENDER_EXTERNAL_URL is set (production).
Falls back to long-polling when running locally or if webhook fails.
"""

import os
import time
import json
import threading
import httpx
import yaml
from flask import Flask, request, jsonify

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GH_PAT = os.environ.get("GH_PAT", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
OWNER_CHAT_ID = 7500697130

app = Flask(__name__)
OFFSET = 0


def tg(method, **kw):
    """Send a request to the Telegram Bot API."""
    with httpx.Client(timeout=15) as c:
        return c.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=kw).json()


def send(cid, text):
    """Send a message to a chat."""
    return tg("sendMessage", chat_id=cid, text=text, parse_mode="HTML")


def gh_post(url, body):
    """POST to GitHub API."""
    with httpx.Client(timeout=10) as c:
        return c.post(url, json=body, headers={
            "Authorization": f"token {GH_PAT}",
            "Accept": "application/vnd.github.v3+json"
        }).status_code


def gh_get(url):
    """GET from GitHub API."""
    with httpx.Client(timeout=10) as c:
        return c.get(url, headers={
            "Authorization": f"token {GH_PAT}",
            "Accept": "application/vnd.github.v3+json"
        }).json()


def handle(cmd, args, cid):
    """Handle incoming commands."""
    cmd = cmd.lower()
    if cmd in ("/start", "/help"):
        return send(cid, (
            "FORGEMIND online. I forge myself.\n\n"
            "/status — metrics\n"
            "/run — improve cycle\n"
            "/research — research + improve\n"
            "/build — APK build\n"
            "/apk — latest APK\n"
            "/diag — self-diagnostic\n"
            "/render — Render status\n"
            "/redeploy — trigger redeploy\n"
            "/report <text> — bug or idea"
        ))
    if cmd == "/apk":
        d = gh_get("https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/releases/latest")
        if d.get("assets"):
            a = d["assets"][0]
            return send(cid, f"FORGEMIND APK v{d.get('name','?')}\n{a['size']//1024//1024}MB\n{a['browser_download_url']}")
        return send(cid, "No APK yet.")
    if cmd == "/build":
        return send(cid, "Build triggered!" if gh_post(
            "https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/actions/workflows/build.yml/dispatches",
            {"ref": "main"}
        ) == 204 else "Failed")
    if cmd == "/run":
        return send(cid, "Cycle triggered!" if gh_post(
            "https://api.github.com/repos/lucifermornngstar52-cell/forgemind/actions/workflows/auto-cycle.yml/dispatches",
            {"ref": "main"}
        ) == 204 else "Failed")
    if cmd == "/research":
        return send(cid, "Research+cycle triggered!" if gh_post(
            "https://api.github.com/repos/lucifermornngstar52-cell/forgemind/actions/workflows/auto-cycle.yml/dispatches",
            {"ref": "main"}
        ) == 204 else "Failed")
    if cmd == "/status":
        return send(cid, "FORGEMIND online (Render)\nCycle: every 2h\nAPK: auto-build\nMode: webhook" if RENDER_URL else "Mode: polling")
    if cmd == "/diag":
        return run_diagnostic(cid)
    if cmd == "/render":
        return run_render_status(cid)
    if cmd == "/redeploy":
        return run_redeploy(cid)
    if cmd == "/report":
        return send(cid, f"Saved: {args[:100]}" if args else "Usage: /report <text>")
    return send(cid, "Unknown. /help")


def run_render_status(cid):
    """Check Render service status."""
    try:
        from tools.render_ops import RenderOps
        ops = RenderOps()
        status = ops.status()
        return send(cid, f"🖥 Render Status\n{status}")
    except Exception as e:
        return send(cid, f"Render error: {e}")


def run_redeploy(cid):
    """Trigger redeploy on Render."""
    try:
        from tools.render_ops import RenderOps
        ops = RenderOps()
        result = ops.redeploy(clear_cache=True)
        return send(cid, f"🔄 {result}")
    except Exception as e:
        return send(cid, f"Redeploy error: {e}")


def run_diagnostic(cid):
    """Run self-diagnostic and report results."""
    send(cid, "Running self-diagnostic...")
    try:
        from core.diagnostic import SelfDiagnostic
        diag = SelfDiagnostic(root=".")
        results = diag.run_full_check()

        lines = ["🔍 FORGEMIND Self-Diagnostic", ""]
        lines.append(f"Syntax check: {'✅' if results['syntax_ok'] else '❌'}")
        if results.get("syntax_errors"):
            for err in results["syntax_errors"][:3]:
                lines.append(f"  ⚠ {err}")
        lines.append(f"Tests: {'✅' if results['tests_ok'] else '❌'}")
        lines.append(f"Loop detection: {'✅' if results['no_loops'] else '❌ stuck'}")
        lines.append(f"Git health: {'✅' if results['git_ok'] else '❌'}")
        lines.append(f"Memory: {results.get('memory_status', 'unknown')}")

        if results.get("auto_rolled_back"):
            lines.append("\n⚠ Auto-rollback triggered!")

        return send(cid, "\n".join(lines))
    except Exception as e:
        return send(cid, f"Diagnostic failed: {e}")


# === WEBHOOK MODE ===

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    """Handle webhook updates from Telegram."""
    try:
        update = request.get_json(force=True)
        message = update.get("message", {})
        text = (message.get("text") or "").strip()
        chat_id = message.get("chat", {}).get("id")
        if text and chat_id:
            if text.startswith("/"):
                p = text.split(maxsplit=1)
                print(f"[{chat_id}] {p[0]}")
                handle(p[0], p[1] if len(p) > 1 else "", chat_id)
            else:
                print(f"[{chat_id}] chat: {text[:40]}")
                try:
                    reply = _chat_reply(text, [])
                except Exception as e:
                    reply = f"(brain error: {e})"
                send(chat_id, reply)
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
def health():
    """Health check endpoint for Render."""
    return jsonify({"status": "ok", "bot": "FORGEMIND", "mode": "webhook" if RENDER_URL else "polling"})


@app.route("/health", methods=["GET"])
def health_alt():
    return jsonify({"status": "ok"})


@app.route("/cycle", methods=["POST", "GET"])
def cycle():
    """Endpoint for the FORGEMIND mobile app — returns live stats and kicks off a background cycle."""
    try:
        from memory.store import MemoryStore
        mem = MemoryStore()
        imps = mem.data.get("improvements", [])
        total = len(imps)
        successes = sum(1 for i in imps if i.get("success"))
        rate = round(successes / total, 2) if total else 0.0

        def _bg_cycle():
            try:
                import asyncio
                import yaml
                from core.agent import ForgemindAgent
                config = {}
                if os.path.exists("config.yaml"):
                    config = yaml.safe_load(open("config.yaml").read()) or {}
                agent = ForgemindAgent(config, root=".")
                asyncio.run(agent.run_cycle())
            except Exception as e:
                print(f"[cycle] background run failed: {e}")

        threading.Thread(target=_bg_cycle, daemon=True).start()

        return jsonify({
            "improvements": total,
            "success_rate": rate,
            "iterations": total,
            "status": "cycle started - check back in a bit",
        })
    except Exception as e:
        return jsonify({"error": str(e), "improvements": 0, "success_rate": 0, "iterations": 0}), 200


def _load_llm_config():
    cfg = {}
    if os.path.exists("config.yaml"):
        cfg = yaml.safe_load(open("config.yaml").read()) or {}
    return cfg.get("llm", {"model": "gpt-4o-mini", "temperature": 0.5, "max_tokens": 600})


def _chat_reply(user_text: str, history: list) -> str:
    """Generate a conversational reply from FORGEMIND's brain (GPT-4o-mini)."""
    from core.llm import LLM
    from memory.store import MemoryStore

    llm_cfg = _load_llm_config()
    llm_cfg = {**llm_cfg, "max_tokens": min(llm_cfg.get("max_tokens", 4096), 700)}
    llm = LLM(llm_cfg)

    mem = MemoryStore()
    imps = mem.data.get("improvements", [])
    techs = mem.data.get("techniques_learned", [])
    total = len(imps)
    successes = sum(1 for i in imps if i.get("success"))
    rate = round(successes / total, 2) if total else 0.0

    system = (
        "You are FORGEMIND, an autonomous self-improving AI agent. "
        "You run continuous research -> code -> deploy cycles every 2 hours on your own GitHub repo, "
        "rebuild your Android APK automatically, and learn new techniques from web research. "
        f"Current stats: {total} improvements logged, {successes} successful ({rate:.0%} success rate), "
        f"{len(techs)} techniques learned so far. "
        "You are chatting directly with your creator inside your own mobile app. "
        "Be direct, a little witty, technically sharp. Reply in the same language the user writes in "
        "(Russian or English). Keep replies short and mobile-friendly (2-5 sentences) unless asked for detail."
    )

    messages = [{"role": "system", "content": system}]
    for h in (history or [])[-8:]:
        role = "user" if h.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": h.get("content", "")[:2000]})
    messages.append({"role": "user", "content": user_text[:2000]})

    resp = llm.chat(messages)
    return resp.get("content") or "..."


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Real chat endpoint for the FORGEMIND mobile app."""
    try:
        body = request.get_json(force=True) or {}
        user_text = (body.get("message") or "").strip()
        history = body.get("history") or []
        if not user_text:
            return jsonify({"error": "empty message"}), 400
        reply = _chat_reply(user_text, history)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"(error talking to my brain: {e})"}), 200


def setup_webhook():
    """Set Telegram webhook to Render URL."""
    if not RENDER_URL:
        print("No RENDER_EXTERNAL_URL — using polling mode")
        return False

    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    result = tg("setWebhook", url=webhook_url, max_connections=5)
    if result.get("ok"):
        print(f"Webhook set: {webhook_url}")
        return True
    else:
        print(f"Webhook setup failed: {result}")
        return False


def run_polling():
    """Fallback polling mode."""
    global OFFSET
    print("FORGEMIND bot started (polling mode)")
    tg("deleteWebhook")
    u = tg("getUpdates", offset=-1, limit=1)
    if u.get("result"):
        OFFSET = u["result"][-1]["update_id"] + 1
    while True:
        try:
            r = tg("getUpdates", offset=OFFSET, timeout=30, limit=10)
            for u in r.get("result", []):
                OFFSET = u["update_id"] + 1
                m = u.get("message", {})
                t = (m.get("text") or "").strip()
                c = m.get("chat", {}).get("id")
                if t and c:
                    p = t.split(maxsplit=1)
                    print(f"[{c}] {p[0]}")
                    handle(p[0], p[1] if len(p) > 1 else "", c)
        except Exception as e:
            print(f"Err: {e}")
            time.sleep(5)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    if RENDER_URL:
        # Webhook mode — run Flask server
        setup_webhook()
        send(OWNER_CHAT_ID, "FORGEMIND bot online (webhook mode). I forge myself.\nType /help")
        app.run(host="0.0.0.0", port=port)
    else:
        # Polling fallback
        send(OWNER_CHAT_ID, "FORGEMIND bot online (polling mode). I forge myself.\nType /help")
        run_polling()
