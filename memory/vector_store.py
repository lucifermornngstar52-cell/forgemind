"""
Vector memory — semantic search over past improvements and techniques.
Uses ChromaDB locally (no API key, no account needed).
"""

import chromadb
from datetime import datetime


class VectorMemory:
    def __init__(self, path: str = "./memory/chroma"):
        self.client = chromadb.PersistentClient(path=path)
        self.improvements = self.client.get_or_create_collection(
            name="improvements",
            metadata={"description": "Recorded code improvements and their outcomes"}
        )
        self.techniques = self.client.get_or_create_collection(
            name="techniques",
            metadata={"description": "Learned techniques from external sources"}
        )
        self.failures = self.client.get_or_create_collection(
            name="failures",
            metadata={"description": "Failed improvements and what went wrong"}
        )

    def remember_improvement(self, description: str, file: str, success: bool, details: str = "") -> None:
        """Store an improvement in vector memory for semantic recall."""
        collection = self.improvements if success else self.failures
        ts = datetime.now().isoformat()
        doc_id = f"{ts}_{file}_{success}"

        collection.add(
            ids=[doc_id],
            documents=[f"{description}. File: {file}. Details: {details}"],
            metadatas=[{
                "description": description,
                "file": file,
                "success": success,
                "timestamp": ts,
                "details": details[:500],
            }]
        )

    def remember_technique(self, name: str, source: str, summary: str) -> None:
        """Store a learned technique in vector memory."""
        ts = datetime.now().isoformat()
        self.techniques.add(
            ids=[f"{ts}_{name}"],
            documents=[f"{name}. Source: {source}. {summary}"],
            metadatas=[{
                "name": name,
                "source": source,
                "summary": summary[:500],
                "timestamp": ts,
            }]
        )

    def search_similar(self, query: str, collection: str = "improvements", n: int = 5) -> list:
        """Find similar past experiences."""
        col = self.improvements if collection == "improvements" else \
              self.techniques if collection == "techniques" else self.failures

        results = col.query(
            query_texts=[query],
            n_results=n,
        )

        out = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            out.append({
                "document": doc,
                "metadata": meta,
                "distance": results["distances"][0][i] if "distances" in results else 0,
            })
        return out

    def search_improvements(self, query: str, n: int = 5) -> list:
        """Search past improvements for similar situations."""
        return self.search_similar(query, "improvements", n)

    def search_failures(self, query: str, n: int = 5) -> list:
        """Search past failures to avoid repeating mistakes."""
        return self.search_similar(query, "failures", n)

    def search_techniques(self, query: str, n: int = 5) -> list:
        """Search learned techniques."""
        return self.search_similar(query, "techniques", n)

    def get_context(self, query: str) -> str:
        """Get combined context from all memory collections for a query."""
        improvements = self.search_improvements(query, n=3)
        failures = self.search_failures(query, n=3)
        techniques = self.search_techniques(query, n=3)

        parts = []
        if improvements:
            parts.append("Similar past improvements:\n" + "\n".join(
                f"  - {m['metadata']['description']} ({'success' if m['metadata']['success'] else 'failed'})"
                for m in improvements
            ))
        if failures:
            parts.append("Similar past failures (avoid these):\n" + "\n".join(
                f"  - {m['metadata']['description']}: {m['metadata']['details'][:100]}"
                for m in failures
            ))
        if techniques:
            parts.append("Relevant learned techniques:\n" + "\n".join(
                f"  - {m['metadata']['name']}: {m['metadata']['summary'][:100]}"
                for m in techniques
            ))

        return "\n\n".join(parts) if parts else "No relevant memories found."
