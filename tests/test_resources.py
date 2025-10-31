"""Tests for MCP resources."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mag.resources.codebase_indexed import get_codebase_indexed
from mag.resources.stats import get_stats


class TestCodebaseIndexedResource:
    """Test codebase://indexed resource."""

    def test_get_codebase_indexed_basic(self) -> None:
        """Test getting codebase indexed summary."""
        with patch("mag.resources.codebase_indexed.VectorStore") as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store

            mock_store.get_stats.return_value = {
                "total_chunks": 150,
                "unique_files_sampled": 12,
                "code_types": ["class", "method", "interface"],
                "collection_name": "test_collection",
            }

            result = get_codebase_indexed()

            assert isinstance(result, str)
            assert "total_chunks" in result
            assert "150" in result
            assert "code_types" in result
            assert "class" in result

    def test_get_codebase_indexed_json_format(self) -> None:
        """Test that result is valid JSON."""
        import json

        with patch("mag.resources.codebase_indexed.VectorStore") as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get_stats.return_value = {
                "total_chunks": 100,
                "unique_files_sampled": 10,
                "code_types": ["class"],
                "collection_name": "test",
            }

            result = get_codebase_indexed()

            # Should be valid JSON
            data = json.loads(result)
            assert "total_chunks" in data
            assert "languages" in data
            assert data["languages"] == ["csharp"]


class TestStatsResource:
    """Test codebase://stats resource."""

    def test_get_stats_basic(self, tmp_path: Path) -> None:
        """Test getting stats."""
        with patch("mag.resources.stats.get_settings") as mock_settings, patch(
            "mag.resources.stats.VectorStore"
        ) as mock_store_class:
            # Mock settings
            mock_config = MagicMock()
            mock_config.chroma_persist_dir = tmp_path / "chroma"
            mock_config.codebase_root = tmp_path
            mock_config.embedding_model = "test-embed"
            mock_config.llm_model = "test-llm"
            mock_config.chunk_size_tokens = 512
            mock_settings.return_value = mock_config

            # Mock vector store
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get_stats.return_value = {"total_chunks": 200}

            result = get_stats()

            assert isinstance(result, str)
            assert "embedding_model" in result
            assert "test-embed" in result
            assert "total_chunks" in result

    def test_get_stats_json_format(self) -> None:
        """Test that stats result is valid JSON."""
        import json

        with patch("mag.resources.stats.get_settings") as mock_settings, patch(
            "mag.resources.stats.VectorStore"
        ) as mock_store_class:
            mock_config = MagicMock()
            mock_config.chroma_persist_dir = Path("/test/chroma")
            mock_config.codebase_root = Path("/test/code")
            mock_config.embedding_model = "nomic-embed-text"
            mock_config.llm_model = "codestral"
            mock_config.chunk_size_tokens = 512
            mock_settings.return_value = mock_config

            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get_stats.return_value = {"total_chunks": 150}

            result = get_stats()

            # Should be valid JSON
            data = json.loads(result)
            assert "vector_db_size_mb" in data
            assert "total_chunks" in data
            assert data["total_chunks"] == 150
            assert "embedding_model" in data
            assert data["embedding_model"] == "nomic-embed-text"

    def test_get_stats_with_chroma_dir(self, tmp_path: Path) -> None:
        """Test stats calculation with actual chroma directory."""
        chroma_dir = tmp_path / "chroma"
        chroma_dir.mkdir()
        (chroma_dir / "test.db").write_bytes(b"0" * 1024 * 100)  # 100KB file

        with patch("mag.resources.stats.get_settings") as mock_settings, patch(
            "mag.resources.stats.VectorStore"
        ) as mock_store_class:
            mock_config = MagicMock()
            mock_config.chroma_persist_dir = chroma_dir
            mock_config.codebase_root = tmp_path
            mock_config.embedding_model = "nomic-embed-text"
            mock_config.llm_model = "codestral"
            mock_config.chunk_size_tokens = 512
            mock_settings.return_value = mock_config

            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get_stats.return_value = {"total_chunks": 50}

            result = get_stats()

            import json

            data = json.loads(result)
            # Should have calculated size
            assert data["vector_db_size_mb"] > 0

