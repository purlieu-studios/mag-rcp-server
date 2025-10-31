"""Search code tool for MCP."""

from typing import Any

from mag.config import get_settings
from mag.llm.ollama_client import OllamaClient
from mag.retrieval.vector_store import VectorStore


def search_code(
    query: str,
    max_results: int | None = None,
    filter_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search for code chunks semantically similar to the query.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default from settings).
        filter_type: Filter by code type: 'class', 'method', 'interface', 'property', or 'all'.

    Returns:
        List of search results with metadata.
    """
    settings = get_settings()

    # Use default if not specified
    if max_results is None:
        max_results = settings.default_search_results

    # Initialize components
    vector_store = VectorStore()
    ollama_client = OllamaClient()

    # Generate query embedding
    query_embedding = ollama_client.embed(query)

    # Build metadata filter
    where_filter = None
    if filter_type and filter_type != "all":
        where_filter = {"type": filter_type}

    # Search vector store
    results = vector_store.search(
        query_embedding=query_embedding,
        n_results=max_results,
        where=where_filter,
    )

    # Format results
    formatted_results = []
    for i, doc_id in enumerate(results["ids"]):
        metadata = results["metadatas"][i]
        document = results["documents"][i]
        distance = results["distances"][i]

        # Convert distance to relevance score (1 - distance for cosine)
        relevance_score = 1.0 - distance

        # Only include results above similarity threshold
        if relevance_score < settings.similarity_threshold:
            continue

        result = {
            "content": document,
            "file": metadata.get("file", ""),
            "lines": metadata.get("lines", [0, 0]),
            "type": metadata.get("type", "unknown"),
            "name": metadata.get("name", ""),
            "hierarchy": metadata.get("hierarchy", ""),
            "relevance_score": round(relevance_score, 2),
        }

        formatted_results.append(result)

    return formatted_results
