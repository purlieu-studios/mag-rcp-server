"""Get file tool for MCP."""

from pathlib import Path
from typing import Any

from mag.config import get_settings
from mag.indexer.parser import CSharpParser


def get_file(path: str, include_ast: bool = False) -> dict[str, Any]:
    """
    Retrieve full file contents with optional AST.

    Args:
        path: Relative path to file from codebase root.
        include_ast: Whether to include AST information.

    Returns:
        Dictionary with file information.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If path is outside codebase root.
    """
    settings = get_settings()
    codebase_root = settings.codebase_root

    # Resolve path relative to codebase root
    file_path = (codebase_root / path).resolve()

    # Security check: ensure path is within codebase root
    try:
        file_path.relative_to(codebase_root)
    except ValueError as e:
        msg = f"Path {path} is outside codebase root"
        raise ValueError(msg) from e

    # Check if file exists
    if not file_path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        msg = f"Failed to read file {path}: {e}"
        raise ValueError(msg) from e

    # Count lines
    line_count = len(content.splitlines())

    result: dict[str, Any] = {
        "path": path,
        "content": content,
        "language": "csharp",
        "line_count": line_count,
    }

    # Include AST if requested
    if include_ast:
        parser = CSharpParser()
        try:
            nodes = parser.parse_file(file_path)
            # Convert nodes to simple dict format
            ast_nodes = [
                {
                    "type": node.type,
                    "name": node.name,
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "parent": node.parent,
                    "namespace": node.namespace,
                    "has_docstring": node.docstring is not None,
                }
                for node in nodes
            ]
            result["ast"] = ast_nodes
        except Exception as e:
            result["ast_error"] = str(e)

    return result
