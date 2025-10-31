"""Explain symbol tool for MCP."""

from typing import Any

from mag.config import get_settings
from mag.llm.ollama_client import OllamaClient
from mag.retrieval.vector_store import VectorStore


def explain_symbol(
    symbol: str,
    include_usage: bool = True,
) -> dict[str, Any]:
    """
    Explain a specific symbol using RAG.

    Args:
        symbol: Symbol to explain (e.g., 'EntityManager.CreateEntity').
        include_usage: Whether to include usage examples.

    Returns:
        Dictionary with explanation and metadata.
    """
    vector_store = VectorStore()
    ollama_client = OllamaClient()

    # Parse symbol (handle qualified names)
    parts = symbol.split(".")
    symbol_name = parts[-1]
    parent_name = parts[-2] if len(parts) > 1 else None

    # Search for the symbol definition
    definition_query = f"{symbol} definition"
    definition_embedding = ollama_client.embed(definition_query)

    # Search for definition with metadata filtering
    where_filter = {"name": symbol_name}
    if parent_name:
        where_filter["parent"] = parent_name

    results = vector_store.search(
        query_embedding=definition_embedding,
        n_results=5,
        where=where_filter if parent_name else None,
    )

    # Find best match
    definition_chunk = None
    definition_location = None

    if results["ids"]:
        # Take the first (most relevant) result
        definition_chunk = results["documents"][0]
        metadata = results["metadatas"][0]

        definition_location = {
            "file": metadata.get("file", ""),
            "line": metadata.get("lines", [0])[0],
        }

    # Search for usage examples if requested
    usage_examples = []
    if include_usage:
        usage_query = f"{symbol_name} usage example"
        usage_embedding = ollama_client.embed(usage_query)

        usage_results = vector_store.search(
            query_embedding=usage_embedding,
            n_results=5,
        )

        for i, usage_id in enumerate(usage_results["ids"]):
            usage_metadata = usage_results["metadatas"][i]
            # Only include if it references the symbol but isn't the definition
            if symbol_name in usage_results["documents"][i]:
                if usage_id != (results["ids"][0] if results["ids"] else None):
                    usage_examples.append(
                        {
                            "file": usage_metadata.get("file", ""),
                            "line": usage_metadata.get("lines", [0])[0],
                        }
                    )

        # Limit to top 3 usage examples
        usage_examples = usage_examples[:3]

    # Build context for explanation
    context_parts = []

    if definition_chunk:
        context_parts.append(f"# Symbol Definition\n{definition_chunk}\n")

    if usage_examples:
        context_parts.append(f"# Found {len(usage_examples)} usage examples\n")

    context = "\n".join(context_parts)

    # Generate explanation using LLM
    if definition_chunk:
        explanation = ollama_client.explain_code(
            code=definition_chunk,
            context=context,
            question=f"Explain the symbol '{symbol}' in detail.",
        )
    else:
        explanation = f"Symbol '{symbol}' not found in the indexed codebase."

    return {
        "symbol": symbol,
        "explanation": explanation,
        "definition_location": definition_location,
        "usage_examples": usage_examples if include_usage else None,
    }
