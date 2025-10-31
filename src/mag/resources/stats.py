"""Statistics resource for MCP."""

import json
import time
from pathlib import Path
from typing import Any

from mag.config import get_settings
from mag.retrieval.vector_store import VectorStore


# Track server start time
_start_time = time.time()


def get_stats() -> str:
    """
    Get real-time statistics and health metrics as JSON string.

    Returns:
        JSON string with server statistics.
    """
    settings = get_settings()
    vector_store = VectorStore()

    # Get vector store stats
    vs_stats = vector_store.get_stats()

    # Calculate vector DB size if possible
    chroma_path = settings.chroma_persist_dir
    db_size_mb = 0.0

    if chroma_path.exists():
        try:
            total_size = sum(
                f.stat().st_size for f in chroma_path.rglob("*") if f.is_file()
            )
            db_size_mb = total_size / (1024 * 1024)  # Convert to MB
        except Exception:
            pass

    # Build statistics
    stats = {
        "vector_db_size_mb": round(db_size_mb, 2),
        "total_chunks": vs_stats["total_chunks"],
        "embedding_model": settings.embedding_model,
        "llm_model": settings.llm_model,
        "uptime_seconds": int(time.time() - _start_time),
        "codebase_root": str(settings.codebase_root),
        "chunk_size_tokens": settings.chunk_size_tokens,
    }

    return json.dumps(stats, indent=2)
