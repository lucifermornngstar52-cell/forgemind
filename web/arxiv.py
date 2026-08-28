"""
arXiv search — access AI/ML research papers without API key.
"""

import httpx
import xml.etree.ElementTree as ET


async def search_arxiv(query: str, max_results: int = 5) -> list:
    """Search arXiv for papers matching the query."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
        )

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        papers = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            link = entry.find("atom:id", ns)
            published = entry.find("atom:published", ns)

            papers.append({
                "title": title.text.strip().replace("\n", " ") if title is not None else "",
                "summary": (summary.text.strip()[:500] if summary is not None else ""),
                "url": link.text if link is not None else "",
                "published": published.text if published is not None else "",
            })

        return papers


async def search_ai_self_improvement() -> list:
    """Search for papers on self-improving AI agents."""
    return await search_arxiv("self-improving AI agent autonomous code", max_results=5)


async def search_technique(technique: str) -> list:
    """Search for papers on a specific technique."""
    return await search_arxiv(technique, max_results=3)
