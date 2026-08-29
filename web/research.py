"""WebResearcher — deep research module for FORGEMIND.

Searches the web, fetches pages, and builds a knowledge base
before the agent makes any code changes.
"""

import json
import asyncio
import httpx
from bs4 import BeautifulSoup


class WebResearcher:
    """Research external techniques, best practices, and architectures."""

    def __init__(self):
        self.findings = []

    def search(self, query: str, max_results: int = 5) -> list:
        """Search DuckDuckGo and return results."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                soup = BeautifulSoup(resp.text, "html.parser")
                results = []
                for r in soup.select(".result")[:max_results]:
                    title_tag = r.select_one(".result__title a")
                    snippet_tag = r.select_one(".result__snippet")
                    if title_tag:
                        results.append({
                            "title": title_tag.get_text(strip=True),
                            "url": title_tag.get("href", ""),
                            "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                        })
                return results
        except Exception:
            return []

    def fetch_page(self, url: str, max_chars: int = 5000) -> str:
        """Fetch a web page and return cleaned text."""
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                return text[:max_chars]
        except Exception:
            return ""

    def deep_research(self, topics: list) -> dict:
        """
        Deep research: search multiple topics, fetch top results,
        and return a structured knowledge base.
        """
        knowledge_base = {}

        for topic in topics:
            console_search = f"python autonomous AI agent {topic} 2025 2026"
            results = self.search(console_search, max_results=3)

            topic_findings = []
            for result in results[:2]:
                page_text = self.fetch_page(result.get("url", ""), max_chars=3000)
                if page_text:
                    topic_findings.append({
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"],
                        "content": page_text,
                    })

            knowledge_base[topic] = {
                "search_results": results,
                "deep_reads": topic_findings,
            }

        self.findings = knowledge_base
        return knowledge_base

    def summarize_findings(self) -> str:
        """Return a text summary of all research findings."""
        if not self.findings:
            return "No research conducted yet."

        lines = []
        for topic, data in self.findings.items():
            lines.append(f"\n### {topic.upper()}")
            for read in data.get("deep_reads", []):
                lines.append(f"  - {read['title']}")
                lines.append(f"    {read['snippet'][:200]}")
                # Include a portion of the actual content
                content_preview = read.get("content", "")[:500]
                lines.append(f"    Content: {content_preview}")

        return "\n".join(lines)
