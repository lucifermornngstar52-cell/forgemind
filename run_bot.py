#!/usr/bin/env python3
"""FORGEMIND Telegram Bot — persistent polling for Render.com."""

import os, time, httpx

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GH_PAT = os.environ.get("GH_PAT", "")
OFFSET = 0

def tg(method, **kw):
    with httpx.Client(timeout=15) as c:
        return c.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=kw).json()

def send(cid, text):
    return tg("sendMessage", chat_id=cid, text=text, parse_mode="HTML")

def gh_post(url, body):
    with httpx.Client(timeout=10) as c:
        return c.post(url, json=body, headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}).status_code

def gh_get(url):
    with httpx.Client(timeout=10) as c:
        return c.get(url, headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}).json()

def handle(cmd, args, cid):
    cmd = cmd.lower()
    if cmd in ("/start", "/help"):
        return send(cid, "FORGEMIND online. I forge myself.\n\n/status — metrics\n/run — improve cycle\n/build — APK build\n/apk — latest APK\n/report <text> — bug or idea")
    if cmd == "/apk":
        d = gh_get("https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/releases/latest")
        if d.get("assets"):
            a = d["assets"][0]
            return send(cid, f"FORGEMIND APK v{d.get('name','?')}\n{a['size']//1024//1024}MB\n{a['browser_download_url']}")
        return send(cid, "No APK yet.")
    if cmd == "/build":
        return send(cid, "Build triggered!" if gh_post("https://api.github.com/repos/lucifermornngstar52-cell/forgemind-mobile/actions/workflows/build.yml/dispatches", {"ref":"main"})==204 else "Failed")
    if cmd == "/run":
        return send(cid, "Cycle triggered!" if gh_post("https://api.github.com/repos/lucifermornngstar52-cell/forgemind/actions/workflows/auto-cycle.yml/dispatches", {"ref":"main"})==204 else "Failed")
    if cmd == "/status":
        return send(cid, "FORGEMIND online (Render)\nCycle: every 2h\nAPK: auto-build")
    if cmd == "/report":
        return send(cid, f"Saved: {args[:100]}" if args else "Usage: /report <text>")
    return send(cid, "Unknown. /help")

def main():
    global OFFSET
    print("FORGEMIND bot started")
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
                    handle(p[0], p[1] if len(p)>1 else "", c)
        except Exception as e:
            print(f"Err: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
