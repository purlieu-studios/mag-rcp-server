"""Tests for MCP tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mag.tools.explain_symbol import explain_symbol
from mag.tools.get_file import get_file
from mag.tools.list_files import list_files
from mag.tools.search_code import search_code


class TestSearchCode:
    """Test search_code tool."""

    @pytest.fixture
    def mock_components(self) -> tuple[MagicMock, MagicMock]:
        """Mock vector store and ollama client."""
        with patch("mag.tools.search_code.VectorStore") as mock_store_class, patch(
            "mag.tools.search_code.OllamaClient"
        ) as mock_ollama_class:
            mock_store = MagicMock()
            mock_ollama = MagicMock()

            mock_store_class.return_value = mock_store
            mock_ollama_class.return_value = mock_ollama

            mock_ollama.embed.return_value = [0.1, 0.2, 0.3]

            yield mock_store, mock_ollama

    def test_search_code_basic(self, mock_components: tuple[MagicMock, MagicMock]) -> None:
        """Test basic code search."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": ["chunk_1"],
            "documents": ["public class TestClass { }"],
            "metadatas": [
                {
                    "file": "Test.cs",
                    "lines": [1, 5],
                    "type": "class",
                    "name": "TestClass",
                    "hierarchy": "NS.TestClass",
                }
            ],
            "distances": [0.1],  # 0.9 relevance
        }

        results = search_code("test class")

        assert len(results) == 1
        result = results[0]
        assert result["name"] == "TestClass"
        assert result["type"] == "class"
        assert result["file"] == "Test.cs"
        assert result["relevance_score"] == 0.9

    def test_search_code_with_max_results(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test search with custom max_results."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        search_code("query", max_results=10)

        call_args = mock_store.search.call_args
        assert call_args.kwargs["n_results"] == 10

    def test_search_code_with_type_filter(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test search with type filter."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        search_code("query", filter_type="class")

        call_args = mock_store.search.call_args
        assert call_args.kwargs["where"] == {"type": "class"}

    def test_search_code_filters_low_relevance(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test that low relevance results are filtered out."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": ["chunk_1", "chunk_2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [
                {"file": "f1", "lines": [1, 2], "type": "class", "name": "C1", "hierarchy": "C1"},
                {"file": "f2", "lines": [1, 2], "type": "class", "name": "C2", "hierarchy": "C2"},
            ],
            "distances": [0.2, 0.5],  # 0.8 and 0.5 relevance
        }

        # Default threshold is 0.7
        results = search_code("query")

        # Should only include first result (0.8 relevance)
        assert len(results) == 1


class TestGetFile:
    """Test get_file tool."""

    def test_get_file_basic(self, temp_codebase: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test basic file retrieval."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        # Create a test file
        test_file = temp_codebase / "Test.cs"
        test_file.write_text("public class Test { }")

        result = get_file("Test.cs")

        assert result["path"] == "Test.cs"
        assert result["content"] == "public class Test { }"
        assert result["language"] == "csharp"
        assert result["line_count"] == 1

    def test_get_file_not_found(
        self,
        temp_codebase: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error when file doesn't exist."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        with pytest.raises(FileNotFoundError, match="not found"):
            get_file("nonexistent.cs")

    def test_get_file_with_ast(self, temp_codebase: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test file retrieval with AST."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        test_file = temp_codebase / "Test.cs"
        test_file.write_text(
            """
namespace Test
{
    public class TestClass
    {
        public void Method() { }
    }
}
        """
        )

        result = get_file("Test.cs", include_ast=True)

        assert "ast" in result
        assert len(result["ast"]) > 0

        # Should have class and method nodes
        types = [node["type"] for node in result["ast"]]
        assert "class" in types

    def test_get_file_security_check(
        self,
        temp_codebase: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that file outside codebase root is rejected."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        with pytest.raises(ValueError, match="outside codebase root"):
            get_file("../../etc/passwd")

    def test_get_file_read_error(
        self, temp_codebase: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error handling when file cannot be read."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        # Create a directory instead of a file to cause read error
        test_dir = temp_codebase / "Test.cs"
        test_dir.mkdir()

        with pytest.raises(ValueError, match="Failed to read file"):
            get_file("Test.cs")

    def test_get_file_ast_parse_error(
        self, temp_codebase: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test AST handling for unparseable files."""
        from unittest.mock import patch

        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        # Create file
        test_file = temp_codebase / "Test.cs"
        test_file.write_text("public class Test { }")

        # Mock parser to raise exception
        with patch("mag.tools.get_file.CSharpParser") as mock_parser_class:
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_file.side_effect = Exception("Parse error")

            result = get_file("Test.cs", include_ast=True)

            # Should have ast_error instead of ast
            assert "ast_error" in result
            assert "Parse error" in result["ast_error"]


class TestListFiles:
    """Test list_files tool."""

    @pytest.fixture
    def mock_vector_store(self) -> MagicMock:
        """Mock vector store for testing."""
        with patch("mag.tools.list_files.VectorStore") as mock_class:
            mock_store = MagicMock()
            mock_class.return_value = mock_store

            mock_store.list_files.return_value = ["File1.cs", "File2.cs", "Util/Helper.cs"]

            # Mock collection.get
            def mock_get(**kwargs: object) -> dict[str, list[object]]:
                file_path = kwargs.get("where", {}).get("file", "")
                if "File1.cs" in file_path:
                    return {
                        "ids": ["c1", "c2"],
                        "metadatas": [
                            {"name": "Class1", "type": "class"},
                            {"name": "Method1", "type": "method"},
                        ],
                    }
                if "File2.cs" in file_path:
                    return {
                        "ids": ["c3"],
                        "metadatas": [{"name": "Interface1", "type": "interface"}],
                    }
                return {"ids": ["c4"], "metadatas": [{"name": "Helper", "type": "class"}]}

            mock_store.collection.get = mock_get

            yield mock_store

    def test_list_files_basic(self, mock_vector_store: MagicMock) -> None:
        """Test basic file listing."""
        results = list_files()

        assert len(results) == 3
        assert all("path" in r for r in results)
        assert all("symbols" in r for r in results)
        assert all("types" in r for r in results)

    def test_list_files_with_pattern(self, mock_vector_store: MagicMock) -> None:
        """Test file listing with glob pattern."""
        results = list_files(pattern="**/File*.cs")

        # Should match File1.cs and File2.cs but not Util/Helper.cs
        paths = [r["path"] for r in results]
        assert "File1.cs" in paths
        assert "File2.cs" in paths

    def test_list_files_with_type_filter(self, mock_vector_store: MagicMock) -> None:
        """Test file listing with type filter."""
        results = list_files(type_filter="interface")

        # Should only include File2.cs which has an interface
        assert len(results) >= 1
        assert any(r["path"] == "File2.cs" for r in results)

    def test_list_files_empty_chunks(self) -> None:
        """Test listing when a file has no chunks."""
        with patch("mag.tools.list_files.VectorStore") as mock_class:
            mock_store = MagicMock()
            mock_class.return_value = mock_store

            # Return some files, but one has no chunks
            mock_store.list_files.return_value = ["HasChunks.cs", "NoChunks.cs"]

            def mock_get(**kwargs: object) -> dict[str, list[object]]:
                file_path = kwargs.get("where", {}).get("file", "")
                if "NoChunks.cs" in file_path:
                    # Empty results for this file
                    return {"ids": [], "metadatas": []}
                return {
                    "ids": ["c1"],
                    "metadatas": [{"name": "SomeClass", "type": "class"}],
                }

            mock_store.collection.get = mock_get

            results = list_files()

            # Should only return file with chunks
            assert len(results) == 1
            assert results[0]["path"] == "HasChunks.cs"

    def test_list_files_read_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test listing when file cannot be read."""
        from unittest.mock import mock_open, patch

        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(tmp_path))
        from mag.config import reset_settings

        reset_settings()

        # Create the file so it exists
        test_file = tmp_path / "Test.cs"
        test_file.write_text("class Test { }")

        with patch("mag.tools.list_files.VectorStore") as mock_class:
            mock_store = MagicMock()
            mock_class.return_value = mock_store

            mock_store.list_files.return_value = ["Test.cs"]

            def mock_get(**kwargs: object) -> dict[str, list[object]]:
                return {
                    "ids": ["c1"],
                    "metadatas": [{"name": "TestClass", "type": "class"}],
                }

            mock_store.collection.get = mock_get

            # Mock read_text to raise exception
            original_read_text = test_file.read_text

            def failing_read_text(*args: object, **kwargs: object) -> str:
                raise PermissionError("Access denied")

            with patch.object(test_file.__class__, "read_text", failing_read_text):
                results = list_files()

                # Should still return result with line_count=0 due to exception
                assert len(results) == 1
                assert results[0]["line_count"] == 0


class TestExplainSymbol:
    """Test explain_symbol tool."""

    @pytest.fixture
    def mock_components(self) -> tuple[MagicMock, MagicMock]:
        """Mock vector store and ollama client."""
        with patch("mag.tools.explain_symbol.VectorStore") as mock_store_class, patch(
            "mag.tools.explain_symbol.OllamaClient"
        ) as mock_ollama_class:
            mock_store = MagicMock()
            mock_ollama = MagicMock()

            mock_store_class.return_value = mock_store
            mock_ollama_class.return_value = mock_ollama

            mock_ollama.embed.return_value = [0.1, 0.2, 0.3]
            mock_ollama.explain_code.return_value = "This is a detailed explanation."

            yield mock_store, mock_ollama

    def test_explain_symbol_basic(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test basic symbol explanation."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": ["chunk_1"],
            "documents": ["public void CreateEntity() { }"],
            "metadatas": [{"file": "EntityManager.cs", "lines": [10, 15]}],
        }

        result = explain_symbol("EntityManager.CreateEntity")

        assert result["symbol"] == "EntityManager.CreateEntity"
        assert "explanation" in result
        assert result["definition_location"] is not None
        assert result["definition_location"]["file"] == "EntityManager.cs"

    def test_explain_symbol_not_found(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test explanation when symbol is not found."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        result = explain_symbol("NonExistent.Symbol")

        assert "not found" in result["explanation"].lower()

    def test_explain_symbol_with_usage(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test symbol explanation with usage examples."""
        mock_store, mock_ollama = mock_components

        # First search returns definition, second returns usage
        mock_store.search.side_effect = [
            {
                "ids": ["def_1"],
                "documents": ["public void Method() { }"],
                "metadatas": [{"file": "Class.cs", "lines": [10, 15]}],
            },
            {
                "ids": ["usage_1", "usage_2"],
                "documents": ["obj.Method();", "another.Method();"],
                "metadatas": [
                    {"file": "Usage1.cs", "lines": [5, 5]},
                    {"file": "Usage2.cs", "lines": [20, 20]},
                ],
            },
        ]

        result = explain_symbol("Class.Method", include_usage=True)

        assert result["usage_examples"] is not None
        assert len(result["usage_examples"]) > 0

    def test_explain_symbol_without_usage(
        self,
        mock_components: tuple[MagicMock, MagicMock],
    ) -> None:
        """Test symbol explanation without usage examples."""
        mock_store, mock_ollama = mock_components

        mock_store.search.return_value = {
            "ids": ["chunk_1"],
            "documents": ["code"],
            "metadatas": [{"file": "f.cs", "lines": [1, 1]}],
        }

        result = explain_symbol("Symbol", include_usage=False)

        assert result["usage_examples"] is None
