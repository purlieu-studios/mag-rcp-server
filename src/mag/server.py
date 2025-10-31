"""MAG MCP Server - Main entry point."""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ResourceTemplate,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from mag.config import get_settings
from mag.prompts.architecture import (
    architecture_analysis_prompt,
    get_architecture_analysis_arguments,
)
from mag.prompts.code_review import code_review_prompt, get_code_review_arguments
from mag.resources.codebase_indexed import get_codebase_indexed
from mag.resources.stats import get_stats
from mag.tools.explain_symbol import explain_symbol
from mag.tools.get_file import get_file
from mag.tools.list_files import list_files
from mag.tools.search_code import search_code

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mag.server")

# Create MCP server instance
app = Server("mag-csharp-server")


# Tool Definitions
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="search_code",
            description="Search for code chunks semantically similar to the query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                    },
                    "filter_type": {
                        "type": "string",
                        "enum": ["class", "method", "interface", "property", "all"],
                        "description": "Filter by code type",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_file",
            description="Retrieve full file contents with optional AST",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to file from codebase root",
                    },
                    "include_ast": {
                        "type": "boolean",
                        "description": "Whether to include AST information",
                        "default": False,
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="list_files",
            description="List all indexed files with metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files",
                    },
                    "type_filter": {
                        "type": "string",
                        "enum": ["class", "interface", "struct", "all"],
                        "description": "Filter by code type",
                    },
                },
            },
        ),
        Tool(
            name="explain_symbol",
            description="Use RAG to explain a specific symbol in context",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol to explain (e.g., 'EntityManager.CreateEntity')",
                    },
                    "include_usage": {
                        "type": "boolean",
                        "description": "Whether to include usage examples",
                        "default": True,
                    },
                },
                "required": ["symbol"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_code":
            results = search_code(
                query=arguments["query"],
                max_results=arguments.get("max_results"),
                filter_type=arguments.get("filter_type"),
            )
            import json

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "get_file":
            result = get_file(
                path=arguments["path"],
                include_ast=arguments.get("include_ast", False),
            )
            import json

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_files":
            results = list_files(
                pattern=arguments.get("pattern"),
                type_filter=arguments.get("type_filter"),
            )
            import json

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "explain_symbol":
            result = explain_symbol(
                symbol=arguments["symbol"],
                include_usage=arguments.get("include_usage", True),
            )
            import json

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Resource Definitions
@app.list_resources()
async def list_resources() -> list[Resource]:
    """List all available resources."""
    return [
        Resource(
            uri="codebase://indexed",
            name="Indexed Codebase Summary",
            description="JSON summary of the indexed C# codebase",
            mimeType="application/json",
        ),
        Resource(
            uri="codebase://stats",
            name="Server Statistics",
            description="Real-time server and index statistics",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Handle resource reads."""
    try:
        if uri == "codebase://indexed":
            return get_codebase_indexed()
        elif uri == "codebase://stats":
            return get_stats()
        else:
            raise ValueError(f"Unknown resource: {uri}")

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
        return f'{{"error": "{str(e)}"}}'


# Prompt Definitions
@app.list_prompts()
async def list_prompts() -> list[dict[str, Any]]:
    """List all available prompts."""
    return [
        {
            "name": "code_review",
            "description": "Template for reviewing code changes",
            "arguments": [
                {
                    "name": "file_path",
                    "description": "Path to file being reviewed",
                    "required": True,
                },
                {
                    "name": "change_description",
                    "description": "Description of what changed",
                    "required": True,
                },
            ],
        },
        {
            "name": "architecture_analysis",
            "description": "Template for analyzing system architecture",
            "arguments": [
                {
                    "name": "namespace",
                    "description": "Namespace to analyze",
                    "required": True,
                },
            ],
        },
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> str:
    """Handle prompt retrieval."""
    try:
        args = arguments or {}

        if name == "code_review":
            return code_review_prompt(
                file_path=args.get("file_path", ""),
                change_description=args.get("change_description", ""),
            )
        elif name == "architecture_analysis":
            return architecture_analysis_prompt(
                namespace=args.get("namespace", ""),
            )
        else:
            raise ValueError(f"Unknown prompt: {name}")

    except Exception as e:
        logger.error(f"Error getting prompt {name}: {e}", exc_info=True)
        return f"Error: {str(e)}"


async def main() -> None:
    """Run the MCP server."""
    settings = get_settings()

    logger.info("Starting MAG MCP Server")
    logger.info(f"Codebase root: {settings.codebase_root}")
    logger.info(f"Ollama host: {settings.ollama_host}")
    logger.info(f"ChromaDB: {settings.chroma_persist_dir}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
