"""
Learner — studies external AI implementations from multiple sources.

Sources (no API keys needed):
- DuckDuckGo: web search
- arXiv: scientific papers
- HuggingFace: open-source models
- Stack Overflow: error solutions
- GitHub: source code
"""

import json
from web.search import web_search, fetch_page, fetch_github_file
from web.arxiv import search_arxiv, search_ai_self_improvement
from web.huggingface import search_models, search_code_search
from web.stackoverflow import search_error_solution


async def research_technique(technique: str) -> dict:
    """Research a technique across all sources."""
    findings = []

    # Web search
    results = await web_search(f"AI {technique} implementation python 2024 2025", max_results=5)
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
                "type": "web",
            })
        except Exception as e:
            findings.append({"source": r["title"], "url": r["url"], "error": str(e), "type": "web"})

    # arXiv papers
    papers = await search_arxiv(technique, max_results=3)
    for p in papers:
        findings.append({
            "source": p["title"],
            "url": p["url"],
            "content": p["summary"],
            "type": "paper",
        })

    # HuggingFace models
    models = await search_models(technique, limit=3)
    for m in models:
        findings.append({
            "source": m["id"],
            "url": f"https://huggingface.co/{m['id']}",
            "content": f"Downloads: {m['downloads']}, Tags: {m['tags']}",
            "type": "model",
        })

    return {"technique": technique, "findings": findings}


async def research_self_improvement() -> dict:
    """Research self-improving AI systems from all sources."""
    all_findings = []

    # arXiv papers
    try:
        papers = await search_ai_self_improvement()
    except Exception as e:
        papers = []
    for p in papers:
        all_findings.append({
            "query": "self-improving AI",
            "source": p["title"],
            "url": p["url"],
            "snippet": p["summary"][:200],
            "content": p["summary"],
            "type": "paper",
        })

    # Web search
    queries = [
        "self-improving AI agent architecture python",
        "SWE-agent autonomous code improvement",
        "Aider AI code refactoring tool",
        "OpenDevin autonomous coding agent",
    ]

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
                    "type": "web",
                })
            except:
                pass

    # HuggingFace models for code improvement
    try:
        models = await search_models("code improvement agent", limit=3)
    except Exception as e:
        models = []
    for m in models:
        all_findings.append({
            "query": "code improvement",
            "source": m["id"],
            "url": f"https://huggingface.co/{m['id']}",
            "snippet": f"Downloads: {m['downloads']}",
            "content": f"Tags: {m['tags']}",
            "type": "model",
        })

    return {"findings": all_findings}


async def research_error(error_message: str) -> dict:
    """Research a specific error to find solutions."""
    # Stack Overflow
    so_results = await search_error_solution(error_message)
    # Web search
    web_results = await web_search(f"python {error_message[:100]} fix", max_results=3)

    return {
        "error": error_message[:200],
        "stack_overflow": [
            {"title": r["title"], "url": r["url"], "solution": r["body"][:1000]}
            for r in so_results[:3]
        ],
        "web": [
            {"title": r["title"], "url": r["url"], "snippet": r.get("snippet", "")}
            for r in web_results
        ],
    }
