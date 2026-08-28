"""
HuggingFace integration — access open-source models and code.
No API key needed for basic search and model info.
"""

import httpx


async def search_models(query: str, limit: int = 5) -> list:
    """Search HuggingFace for models matching a query."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://huggingface.co/api/models",
            params={"search": query, "limit": limit, "sort": "downloads", "direction": -1},
        )
        models = resp.json()
        return [
            {
                "id": m.get("id", ""),
                "downloads": m.get("downloads", 0),
                "tags": m.get("tags", [])[:5],
                "last_modified": m.get("lastModified", ""),
            }
            for m in models
        ]


async def get_model_info(model_id: str) -> dict:
    """Get detailed info about a specific model."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"https://huggingface.co/api/models/{model_id}")
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Model not found: {model_id}"}


async def search_code_search(query: str, limit: int = 5) -> list:
    """Search HuggingFace datasets for code-related datasets."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://huggingface.co/api/datasets",
            params={"search": query, "limit": limit},
        )
        return resp.json() if resp.status_code == 200 else []
