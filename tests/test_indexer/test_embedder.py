"""Tests for codebase embedder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mag.indexer.embedder import CodebaseEmbedder


class TestCodebaseEmbedder:
    """Test CodebaseEmbedder functionality."""

    @pytest.fixture
    def mock_vector_store(self) -> MagicMock:
        """Create a mock vector store."""
        store = MagicMock()
        store.count.return_value = 0
        store.get_stats.return_value = {"total_chunks": 0}
        return store

    @pytest.fixture
    def mock_ollama_client(self) -> MagicMock:
        """Create a mock Ollama client."""
        client = MagicMock()
        client.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        return client

    @pytest.fixture
    def embedder(
        self,
        mock_vector_store: MagicMock,
        mock_ollama_client: MagicMock,
        temp_codebase: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> CodebaseEmbedder:
        """Create embedder instance with mocks."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(temp_codebase))
        from mag.config import reset_settings

        reset_settings()

        return CodebaseEmbedder(
            vector_store=mock_vector_store,
            ollama_client=mock_ollama_client,
        )

    def test_initialization(
        self,
        mock_vector_store: MagicMock,
        mock_ollama_client: MagicMock,
    ) -> None:
        """Test embedder initialization."""
        embedder = CodebaseEmbedder(
            vector_store=mock_vector_store,
            ollama_client=mock_ollama_client,
        )

        assert embedder.vector_store == mock_vector_store
        assert embedder.ollama_client == mock_ollama_client
        assert embedder.parser is not None
        assert embedder.chunker is not None
        assert embedder.discovery is not None

    def test_initialization_with_defaults(self) -> None:
        """Test embedder initialization with default components."""
        with patch("mag.indexer.embedder.VectorStore"), patch(
            "mag.indexer.embedder.OllamaClient"
        ):
            embedder = CodebaseEmbedder()

            assert embedder.vector_store is not None
            assert embedder.ollama_client is not None

    def test_index_codebase_with_no_files(
        self,
        embedder: CodebaseEmbedder,
    ) -> None:
        """Test indexing empty codebase."""
        stats = embedder.index_codebase()

        assert stats["files_processed"] == 0
        assert stats["chunks_created"] == 0
        assert stats["errors"] == 0

    def test_index_codebase_with_single_file(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
        mock_ollama_client: MagicMock,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test indexing codebase with one file."""
        # Create a C# file
        cs_file = temp_codebase / "Test.cs"
        cs_file.write_text(
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

        stats = embedder.index_codebase()

        assert stats["files_processed"] == 1
        assert stats["chunks_created"] > 0
        assert stats["errors"] == 0

        # Verify embeddings were generated
        assert mock_ollama_client.embed.called

        # Verify data was added to vector store
        assert mock_vector_store.add_embeddings.called

    def test_index_codebase_with_multiple_files(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
    ) -> None:
        """Test indexing codebase with multiple files."""
        # Create multiple C# files
        for i in range(3):
            file_path = temp_codebase / f"File{i}.cs"
            file_path.write_text(f"public class Class{i} {{ }}")

        stats = embedder.index_codebase()

        assert stats["files_processed"] == 3
        assert stats["chunks_created"] >= 3  # At least one chunk per file
        assert stats["errors"] == 0

    def test_index_codebase_with_progress_callback(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
    ) -> None:
        """Test progress callback during indexing."""
        cs_file = temp_codebase / "Test.cs"
        cs_file.write_text("public class Test { }")

        progress_calls = []

        def progress_callback(message: str, current: int, total: int) -> None:
            progress_calls.append((message, current, total))

        embedder.index_codebase(progress_callback=progress_callback)

        # Should have progress updates
        assert len(progress_calls) > 0

        # First call should be discovery
        assert "Discovering" in progress_calls[0][0] or "Indexed" in progress_calls[0][0]

    def test_index_codebase_handles_parse_error(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
    ) -> None:
        """Test that indexing continues despite parse errors."""
        # Create a file that will cause issues
        bad_file = temp_codebase / "Bad.cs"
        bad_file.write_text("")  # Empty file

        good_file = temp_codebase / "Good.cs"
        good_file.write_text("public class Good { }")

        stats = embedder.index_codebase()

        # Should process files but may have errors
        assert stats["files_processed"] >= 1

    def test_index_codebase_error_with_progress_callback(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
        mock_ollama_client: MagicMock,
    ) -> None:
        """Test progress callback is called when indexing error occurs."""
        cs_file = temp_codebase / "Test.cs"
        cs_file.write_text("public class Test { }")

        # Make embedding fail to trigger error handling
        mock_ollama_client.embed.side_effect = Exception("Embedding failed")

        progress_calls = []

        def progress_callback(message: str, current: int, total: int) -> None:
            progress_calls.append((message, current, total))

        stats = embedder.index_codebase(progress_callback=progress_callback)

        # Should have called progress callback for error
        assert stats["errors"] > 0
        error_calls = [call for call in progress_calls if "Error" in call[0]]
        assert len(error_calls) > 0

    def test_index_file_empty_chunks(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
    ) -> None:
        """Test indexing file that produces no chunks."""
        from unittest.mock import patch

        file_path = temp_codebase / "Empty.cs"
        file_path.write_text("// Just a comment")

        # Mock chunker to return empty chunks
        with patch.object(embedder.chunker, "chunk_nodes", return_value=[]):
            chunks_count = embedder._index_file(file_path)

            assert chunks_count == 0

    def test_index_file(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
        mock_ollama_client: MagicMock,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test indexing a single file."""
        file_path = temp_codebase / "Test.cs"
        file_path.write_text(
            """
public class TestClass
{
    public void Method() { }
}
        """
        )

        chunks_count = embedder._index_file(file_path)

        assert chunks_count > 0
        assert mock_ollama_client.embed.called
        assert mock_vector_store.add_embeddings.called

        # Verify add_embeddings was called with correct arguments
        call_args = mock_vector_store.add_embeddings.call_args
        embeddings = call_args.kwargs["embeddings"]
        documents = call_args.kwargs["documents"]
        metadatas = call_args.kwargs["metadatas"]
        ids = call_args.kwargs["ids"]

        assert len(embeddings) == chunks_count
        assert len(documents) == chunks_count
        assert len(metadatas) == chunks_count
        assert len(ids) == chunks_count

    def test_index_file_returns_zero_for_no_nodes(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
    ) -> None:
        """Test that indexing empty file returns 0."""
        file_path = temp_codebase / "Empty.cs"
        file_path.write_text("")

        chunks_count = embedder._index_file(file_path)

        assert chunks_count == 0

    def test_reindex_file(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test reindexing a file."""
        file_path = temp_codebase / "Test.cs"
        file_path.write_text("public class Test { }")

        chunks_count = embedder.reindex_file(file_path)

        # Should delete old chunks first
        mock_vector_store.delete_by_file.assert_called_once_with(str(file_path))

        # Then add new chunks
        assert chunks_count > 0
        assert mock_vector_store.add_embeddings.called

    def test_clear_index(
        self,
        embedder: CodebaseEmbedder,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test clearing the index."""
        embedder.clear_index()

        mock_vector_store.clear.assert_called_once()

    def test_get_index_stats(
        self,
        embedder: CodebaseEmbedder,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test getting index statistics."""
        mock_vector_store.get_stats.return_value = {
            "total_chunks": 100,
            "unique_files": 10,
        }

        stats = embedder.get_index_stats()

        assert stats["total_chunks"] == 100
        assert stats["unique_files"] == 10
        mock_vector_store.get_stats.assert_called_once()

    def test_generate_chunk_id_consistency(self, embedder: CodebaseEmbedder) -> None:
        """Test that chunk IDs are consistent for same input."""
        id1 = embedder._generate_chunk_id("test.cs", "content")
        id2 = embedder._generate_chunk_id("test.cs", "content")

        assert id1 == id2
        assert id1.startswith("chunk_")

    def test_generate_chunk_id_uniqueness(self, embedder: CodebaseEmbedder) -> None:
        """Test that chunk IDs are unique for different inputs."""
        id1 = embedder._generate_chunk_id("test1.cs", "content")
        id2 = embedder._generate_chunk_id("test2.cs", "content")
        id3 = embedder._generate_chunk_id("test1.cs", "different")

        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_parallel_processing(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that files are processed in parallel."""
        # Set max_workers to ensure parallel execution
        monkeypatch.setenv("MAG_MAX_WORKERS", "2")
        from mag.config import reset_settings

        reset_settings()

        # Create multiple files
        for i in range(4):
            file_path = temp_codebase / f"File{i}.cs"
            file_path.write_text(f"public class Class{i} {{ }}")

        # Recreate embedder with new settings
        embedder = CodebaseEmbedder(
            vector_store=embedder.vector_store,
            ollama_client=embedder.ollama_client,
        )

        stats = embedder.index_codebase()

        assert stats["files_processed"] == 4

    def test_metadata_serialization(
        self,
        embedder: CodebaseEmbedder,
        temp_codebase: Path,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test that metadata is properly serialized."""
        file_path = temp_codebase / "Test.cs"
        file_path.write_text("public class Test { }")

        embedder._index_file(file_path)

        # Get the metadata that was passed to add_embeddings
        call_args = mock_vector_store.add_embeddings.call_args
        metadatas = call_args.kwargs["metadatas"]

        # Ensure all metadata values are JSON-serializable
        for metadata in metadatas:
            for value in metadata.values():
                assert not isinstance(value, Path)
                assert isinstance(value, (str, int, float, bool, list))
