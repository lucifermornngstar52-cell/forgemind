"""Learner — studies external AI implementations and extracts techniques."""

import json
from web.search import web_search, fetch_page, fetch_github_file


async def research_technique(technique: str) -> dict:
    """Search the web for a specific AI technique and return findings."""
    results = await web_search(f"AI {technique} implementation python 2024 2025", max_results=5)

    findings = []
    for r in results[:3]:
        try:
            if "github.com" in r["url"]:
                content = await fetch_github_file(r["url"])
            else:
                content = await fetch_page(r["url"])
            findings.append({
                "source": r["title"],
                "url": r["url"],
                "content": content[:4000],
            })
        except Exception as e:
            findings.append({
                "source": r["title"],
                "url": r["url"],
                "error": str(e),
            })

    return {
        "technique": technique,
        "findings": findings,
    }


async def research_self_improvement() -> dict:
    """Research self-improving AI systems and their architectures."""
    queries = [
        "self-improving AI agent architecture python",
        "SWE-agent autonomous code improvement",
        "Aider AI code refactoring tool",
        "OpenDevin autonomous coding agent",
        "AI agent self-modification safety",
    ]

    all_findings = []
    for q in queries:
        results = await web_search(q, max_results=3)
        for r in results[:2]:
            try:
                content = await fetch_page(r["url"])
                all_findings.append({
                    "query": q,
                    "source": r["title"],
                    "url": r["url"],
                    "snippet": r.get("snippet", ""),
                    "content": content[:3000],
                })
            except:
                pass

    return {"findings": all_findings}
