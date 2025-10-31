"""Tests for MCP server handlers."""

import json
from unittest.mock import MagicMock, patch

import pytest

from mag.server import app, call_tool, get_prompt, list_prompts, list_resources, list_tools, read_resource


class TestToolHandlers:
    """Test MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_list_tools(self) -> None:
        """Test listing available tools."""
        tools = await list_tools()

        assert len(tools) == 4
        tool_names = {t.name for t in tools}
        assert tool_names == {"search_code", "get_file", "list_files", "explain_symbol"}

        # Verify each tool has required fields
        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_call_tool_search_code(self) -> None:
        """Test calling search_code tool."""
        with patch("mag.server.search_code") as mock_search:
            mock_search.return_value = [
                {"name": "EntityManager", "type": "class", "file": "EntityManager.cs"}
            ]

            result = await call_tool(
                "search_code",
                {"query": "entity management", "max_results": 5},
            )

            assert len(result) == 1
            assert result[0].type == "text"
            data = json.loads(result[0].text)
            assert len(data) == 1
            assert data[0]["name"] == "EntityManager"

            mock_search.assert_called_once_with(
                query="entity management",
                max_results=5,
                filter_type=None,
            )

    @pytest.mark.asyncio
    async def test_call_tool_get_file(self) -> None:
        """Test calling get_file tool."""
        with patch("mag.server.get_file") as mock_get_file:
            mock_get_file.return_value = {
                "path": "EntityManager.cs",
                "content": "public class EntityManager { }",
            }

            result = await call_tool(
                "get_file",
                {"path": "EntityManager.cs", "include_ast": True},
            )

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["path"] == "EntityManager.cs"

            mock_get_file.assert_called_once_with(
                path="EntityManager.cs",
                include_ast=True,
            )

    @pytest.mark.asyncio
    async def test_call_tool_list_files(self) -> None:
        """Test calling list_files tool."""
        with patch("mag.server.list_files") as mock_list_files:
            mock_list_files.return_value = [
                {"path": "EntityManager.cs"},
                {"path": "IRepository.cs"},
            ]

            result = await call_tool(
                "list_files",
                {"pattern": "*.cs", "type_filter": "class"},
            )

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert len(data) == 2

            mock_list_files.assert_called_once_with(
                pattern="*.cs",
                type_filter="class",
            )

    @pytest.mark.asyncio
    async def test_call_tool_explain_symbol(self) -> None:
        """Test calling explain_symbol tool."""
        with patch("mag.server.explain_symbol") as mock_explain:
            mock_explain.return_value = {
                "symbol": "EntityManager",
                "explanation": "Manages game entities",
            }

            result = await call_tool(
                "explain_symbol",
                {"symbol": "EntityManager", "include_usage": False},
            )

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["symbol"] == "EntityManager"

            mock_explain.assert_called_once_with(
                symbol="EntityManager",
                include_usage=False,
            )

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self) -> None:
        """Test calling unknown tool returns error."""
        result = await call_tool("unknown_tool", {})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "unknown_tool" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(self) -> None:
        """Test tool exception handling."""
        with patch("mag.server.search_code") as mock_search:
            mock_search.side_effect = Exception("Search failed")

            result = await call_tool("search_code", {"query": "test"})

            assert len(result) == 1
            assert "Error" in result[0].text


class TestResourceHandlers:
    """Test MCP resource handlers."""

    @pytest.mark.asyncio
    async def test_list_resources(self) -> None:
        """Test listing available resources."""
        resources = await list_resources()

        assert len(resources) == 2
        uris = {str(r.uri) for r in resources}
        assert uris == {"codebase://indexed", "codebase://stats"}

        # Verify each resource has required fields
        for resource in resources:
            assert resource.uri
            assert resource.name
            assert resource.description
            assert resource.mimeType == "application/json"

    @pytest.mark.asyncio
    async def test_read_resource_indexed(self) -> None:
        """Test reading indexed codebase resource."""
        with patch("mag.server.get_codebase_indexed") as mock_get:
            mock_get.return_value = '{"total_chunks": 100}'

            result = await read_resource("codebase://indexed")

            assert result == '{"total_chunks": 100}'
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_resource_stats(self) -> None:
        """Test reading stats resource."""
        with patch("mag.server.get_stats") as mock_get:
            mock_get.return_value = '{"embedding_model": "nomic-embed-text"}'

            result = await read_resource("codebase://stats")

            assert result == '{"embedding_model": "nomic-embed-text"}'
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_resource_unknown(self) -> None:
        """Test reading unknown resource returns error JSON."""
        result = await read_resource("codebase://unknown")

        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_read_resource_exception_handling(self) -> None:
        """Test resource exception handling."""
        with patch("mag.server.get_codebase_indexed") as mock_get:
            mock_get.side_effect = Exception("Failed to get data")

            result = await read_resource("codebase://indexed")

            assert "error" in result.lower()


class TestPromptHandlers:
    """Test MCP prompt handlers."""

    @pytest.mark.asyncio
    async def test_list_prompts(self) -> None:
        """Test listing available prompts."""
        prompts = await list_prompts()

        assert len(prompts) == 2
        prompt_names = {p["name"] for p in prompts}
        assert prompt_names == {"code_review", "architecture_analysis"}

        # Verify each prompt has required fields
        for prompt in prompts:
            assert prompt["name"]
            assert prompt["description"]
            assert "arguments" in prompt

    @pytest.mark.asyncio
    async def test_get_prompt_code_review(self) -> None:
        """Test getting code review prompt."""
        result = await get_prompt(
            "code_review",
            {
                "file_path": "EntityManager.cs",
                "change_description": "Added new method",
            },
        )

        assert isinstance(result, str)
        assert "EntityManager.cs" in result
        assert "Added new method" in result

    @pytest.mark.asyncio
    async def test_get_prompt_architecture_analysis(self) -> None:
        """Test getting architecture analysis prompt."""
        result = await get_prompt(
            "architecture_analysis",
            {"namespace": "GameEngine.Core"},
        )

        assert isinstance(result, str)
        assert "GameEngine.Core" in result

    @pytest.mark.asyncio
    async def test_get_prompt_unknown(self) -> None:
        """Test getting unknown prompt returns error."""
        result = await get_prompt("unknown_prompt", {})

        assert "Error" in result

    @pytest.mark.asyncio
    async def test_get_prompt_with_none_arguments(self) -> None:
        """Test getting prompt with None arguments."""
        result = await get_prompt("code_review", None)

        assert isinstance(result, str)
        # Should use empty strings as defaults


class TestServerApp:
    """Test server application."""

    def test_app_created(self) -> None:
        """Test that app instance is created."""
        assert app is not None
        assert app.name == "mag-csharp-server"


class TestMain:
    """Test main function."""

    @pytest.mark.asyncio
    async def test_main_function_setup(self) -> None:
        """Test main function sets up correctly."""
        from mag.server import main

        # We can't easily test the full main() since it runs forever,
        # but we can import it to ensure it's defined
        assert main is not None
        assert callable(main)
