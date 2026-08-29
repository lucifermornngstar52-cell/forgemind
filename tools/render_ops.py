"""Render Operations — FORGEMIND manages its own hosting.

Capabilities:
- Check deploy status
- Trigger redeploy
- Read deploy logs (for debugging failures)
- Suspend/resume service
- Update env vars
- Health check

Usage from agent:
    render_status()  -> check current deploy
    render_redeploy() -> trigger new deploy
    render_logs()     -> read last deploy logs
    render_suspend()  -> suspend service (emergency)
    render_resume()   -> resume service
"""

import os
import httpx
from datetime import datetime


class RenderOps:
    """FORGEMIND's hands on its own infrastructure."""

    BASE = "https://api.render.com/v1"

    def __init__(self):
        self.api_key = os.environ.get("RENDER_API_KEY", "")
        self.service_id = os.environ.get("RENDER_SERVICE_ID", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str) -> dict:
        with httpx.Client(timeout=15) as c:
            resp = c.get(f"{self.BASE}{path}", headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.status_code, "body": resp.text[:500]}

    def _post(self, path: str, body: dict = None) -> dict:
        with httpx.Client(timeout=15) as c:
            resp = c.post(f"{self.BASE}{path}", headers=self.headers, json=body or {})
            if resp.status_code in (200, 201, 202):
                return resp.json() if resp.text else {"ok": True}
            return {"error": resp.status_code, "body": resp.text[:500]}

    def status(self) -> str:
        """Check current service and deploy status."""
        svc = self._get(f"/services/{self.service_id}")
        deploys = self._get(f"/services/{self.service_id}/deploys?limit=3")

        lines = ["Render Service Status", ""]

        if "error" in svc:
            return f"Error: {svc['error']}"

        lines.append(f"Name: {svc.get('name', '?')}")
        lines.append(f"URL: {svc.get('serviceUrl', 'none')}")
        lines.append(f"Suspended: {svc.get('suspended', 'no')}")
        lines.append(f"Auto-deploy: {svc.get('autoDeploy', '?')}")
        lines.append(f"Plan: {svc.get('serviceDetails', {}).get('buildPlan', '?')}")

        if "error" not in deploys and isinstance(deploys, list):
            lines.append("\nRecent deploys:")
            for d in deploys[:3]:
                deploy = d.get("deploy", d)
                lines.append(
                    f"  {deploy.get('id', '?')[:8]} | "
                    f"{deploy.get('status', '?')} | "
                    f"{deploy.get('createdAt', '?')[:19]}"
                )

        return "\n".join(lines)

    def redeploy(self, clear_cache: bool = False) -> str:
        """Trigger a new deploy."""
        body = {"clearCache": "clear" if clear_cache else "do_not_clear"}
        result = self._post(f"/services/{self.service_id}/deploys", body)

        if "ok" in result or "id" in str(result):
            return "Redeploy triggered successfully."
        elif isinstance(result, dict) and not result:
            # 202 with empty body = success
            return "Redeploy triggered successfully."
        return f"Redeploy failed: {result}"

    def logs(self, lines: int = 50) -> str:
        """Get recent deploy logs."""
        deploys = self._get(f"/services/{self.service_id}/deploys?limit=1")
        if isinstance(deploys, list) and deploys:
            deploy_id = deploys[0].get("deploy", deploys[0]).get("id", "")
            if deploy_id:
                log_data = self._get(f"/services/{self.service_id}/deploys/{deploy_id}/logs")
                if "logs" in log_data:
                    log_lines = log_data["logs"].split("\n")[-lines:]
                    return "\n".join(log_lines)
                return f"Logs endpoint returned: {str(log_data)[:500]}"
        return "No deploys found."

    def suspend(self) -> str:
        """Suspend the service (emergency only)."""
        with httpx.Client(timeout=15) as c:
            resp = c.post(
                f"{self.BASE}/services/{self.service_id}/suspend",
                headers=self.headers
            )
            if resp.status_code in (200, 202):
                return "Service suspended."
            return f"Suspend failed: {resp.status_code}"

    def resume(self) -> str:
        """Resume the service."""
        with httpx.Client(timeout=15) as c:
            resp = c.post(
                f"{self.BASE}/services/{self.service_id}/resume",
                headers=self.headers
            )
            if resp.status_code in (200, 202):
                return "Service resumed."
            return f"Resume failed: {resp.status_code}"

    def health_check(self) -> dict:
        """Quick health check — is the service responding?"""
        svc = self._get(f"/services/{self.service_id}")
        url = svc.get("serviceUrl", "")
        if not url:
            # Try the onrender.com URL pattern
            name = svc.get("name", "")
            url = f"https://{name}.onrender.com"

        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(f"{url}/health")
                return {
                    "healthy": resp.status_code == 200,
                    "status_code": resp.status_code,
                    "body": resp.text[:200],
                }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def update_env(self, key: str, value: str) -> str:
        """Update an environment variable."""
        with httpx.Client(timeout=15) as c:
            resp = c.patch(
                f"{self.BASE}/services/{self.service_id}/env-vars",
                headers=self.headers,
                json={"key": key, "value": value}
            )
            if resp.status_code in (200, 204):
                return f"Env var {key} updated."
            return f"Update failed: {resp.status_code}"

    def auto_recover(self) -> str:
        """Check health and auto-recover if needed."""
        health = self.health_check()

        if health.get("healthy"):
            return "All good — service is healthy."

        # Service is down — try redeploy
        lines = ["⚠ Service unhealthy, attempting recovery...", f"  Error: {health.get('error', 'unknown')}"]
        lines.append(self.redeploy(clear_cache=True))
        return "\n".join(lines)
