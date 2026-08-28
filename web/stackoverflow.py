"""
Stack Overflow search — find solutions to errors and bugs.
No API key needed, 300 requests/day without key.
"""

import httpx


async def search_stackoverflow(query: str, limit: int = 5) -> list:
    """Search Stack Overflow for answers."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.stackexchange.com/2.3/search/advanced",
            params={
                "order": "desc",
                "sort": "relevance",
                "q": query,
                "site": "stackoverflow",
                "pagesize": limit,
                "filter": "withbody",
            },
        )
        items = resp.json().get("items", [])
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "score": item.get("score", 0),
                "tags": item.get("tags", []),
                "answer_count": item.get("answer_count", 0),
                "body": (item.get("body", "") or "")[:2000],
            }
            for item in items
        ]


async def search_error_solution(error_message: str) -> list:
    """Search for solutions to a specific error message."""
    # Clean up error message for search
    clean = error_message.strip().split("\n")[0][:200]
    return await search_stackoverflow(clean, limit=5)
