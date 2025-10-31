"""List files tool for MCP."""

from pathlib import Path
from typing import Any

import pathspec

from mag.config import get_settings
from mag.indexer.parser import CSharpParser
from mag.retrieval.vector_store import VectorStore


def list_files(
    pattern: str | None = None,
    type_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    List all indexed files with metadata.

    Args:
        pattern: Optional glob pattern to filter files (e.g., "**/*Manager.cs").
        type_filter: Filter by code type: 'class', 'interface', 'struct', or 'all'.

    Returns:
        List of file information dictionaries.
    """
    vector_store = VectorStore()

    # Get all indexed files
    all_files = vector_store.list_files(limit=1000)

    # Apply pattern filter if specified
    if pattern:
        spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])
        all_files = [f for f in all_files if spec.match_file(f)]

    # Build file information
    results = []

    for file_path_str in all_files:
        # Get chunks for this file to extract metadata
        file_results = vector_store.collection.get(
            where={"file": file_path_str},
            limit=100,  # Limit to avoid huge results
        )

        if not file_results["ids"]:
            continue

        # Extract symbols and types from metadata
        symbols = set()
        types = set()

        for metadata in file_results["metadatas"]:
            if metadata:
                if "name" in metadata:
                    symbols.add(metadata["name"])
                if "type" in metadata:
                    types.add(metadata["type"])

        # Apply type filter if specified
        if type_filter and type_filter != "all":
            if type_filter not in types:
                continue

        # Get file stats if possible
        settings = get_settings()
        full_path = settings.codebase_root / file_path_str

        line_count = 0
        if full_path.exists():
            try:
                content = full_path.read_text(encoding="utf-8")
                line_count = len(content.splitlines())
            except Exception:
                pass

        result = {
            "path": file_path_str,
            "symbols": sorted(symbols),
            "types": sorted(types),
            "line_count": line_count,
            "chunk_count": len(file_results["ids"]),
        }

        results.append(result)

    return sorted(results, key=lambda x: x["path"])
