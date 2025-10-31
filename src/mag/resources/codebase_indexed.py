"""Codebase indexed resource for MCP."""

import json
from datetime import datetime
from typing import Any

from mag.retrieval.vector_store import VectorStore


def get_codebase_indexed() -> str:
    """
    Get summary of indexed codebase as JSON string.

    Returns:
        JSON string with codebase summary.
    """
    vector_store = VectorStore()
    stats = vector_store.get_stats()

    # Build summary
    summary = {
        "total_files": stats.get("unique_files_sampled", 0),
        "total_chunks": stats["total_chunks"],
        "languages": ["csharp"],
        "index_stats": {
            "code_types": stats.get("code_types", []),
            "total_chunks": stats["total_chunks"],
        },
        "last_updated": datetime.now().isoformat(),
        "collection_name": stats.get("collection_name", "csharp_codebase"),
    }

    return json.dumps(summary, indent=2)
