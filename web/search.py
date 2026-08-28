"""Web search — find how others build AI systems."""

import httpx
import json
from bs4 import BeautifulSoup


async def web_search(query: str, max_results: int = 5) -> list:
    """Search the web for a query, return list of {title, url, snippet}."""
    # Using DuckDuckGo HTML endpoint (no API key needed)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
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


async def fetch_page(url: str) -> str:
    """Fetch a web page and return cleaned text."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, nav
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Truncate to reasonable length
        return text[:8000] if len(text) > 8000 else text


async def fetch_github_file(url: str) -> str:
    """Fetch raw file content from GitHub."""
    # Convert github.com URL to raw.githubusercontent.com
    raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(raw_url, headers={"User-Agent": "Mozilla/5.0"})
        return resp.text[:12000]
