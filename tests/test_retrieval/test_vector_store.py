"""Tests for vector store."""

from pathlib import Path

import pytest

from mag.retrieval.vector_store import VectorStore


class TestVectorStore:
    """Test VectorStore functionality."""

    @pytest.fixture
    def vector_store(self, temp_chroma_dir: Path) -> VectorStore:
        """Create a vector store instance with temporary storage."""
        return VectorStore(
            persist_dir=temp_chroma_dir,
            collection_name="test_collection",
        )

    @pytest.fixture
    def sample_embeddings(self) -> list[list[float]]:
        """Create sample embeddings."""
        return [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.5, 0.4, 0.3, 0.2, 0.1],
            [0.3, 0.3, 0.3, 0.3, 0.3],
        ]

    @pytest.fixture
    def sample_documents(self) -> list[str]:
        """Create sample documents."""
        return [
            "public class EntityManager { }",
            "public interface IRepository { }",
            "public struct Point { }",
        ]

    @pytest.fixture
    def sample_metadatas(self) -> list[dict[str, str]]:
        """Create sample metadata."""
        return [
            {"file": "EntityManager.cs", "type": "class", "name": "EntityManager"},
            {"file": "IRepository.cs", "type": "interface", "name": "IRepository"},
            {"file": "Point.cs", "type": "struct", "name": "Point"},
        ]

    @pytest.fixture
    def sample_ids(self) -> list[str]:
        """Create sample IDs."""
        return ["chunk_1", "chunk_2", "chunk_3"]

    def test_initialization(self, temp_chroma_dir: Path) -> None:
        """Test vector store initialization."""
        store = VectorStore(
            persist_dir=temp_chroma_dir,
            collection_name="test_init",
        )

        assert store.persist_dir == temp_chroma_dir
        assert store.collection_name == "test_init"
        assert store.collection is not None

    def test_initialization_creates_directory(self, tmp_path: Path) -> None:
        """Test that initialization creates persist directory."""
        new_dir = tmp_path / "new_chroma"
        assert not new_dir.exists()

        store = VectorStore(persist_dir=new_dir, collection_name="test")

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_add_embeddings(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test adding embeddings to the store."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        # Verify they were added
        assert vector_store.count() == 3

    def test_add_embeddings_validation(self, vector_store: VectorStore) -> None:
        """Test that add_embeddings validates input lengths."""
        with pytest.raises(ValueError, match="same length"):
            vector_store.add_embeddings(
                embeddings=[[0.1, 0.2]],
                documents=["doc1", "doc2"],  # Different length
                metadatas=[{"key": "value"}],
                ids=["id1"],
            )

    def test_add_empty_embeddings(self, vector_store: VectorStore) -> None:
        """Test adding empty list of embeddings."""
        vector_store.add_embeddings(
            embeddings=[],
            documents=[],
            metadatas=[],
            ids=[],
        )

        assert vector_store.count() == 0

    def test_search(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test searching for similar embeddings."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        # Search with first embedding (should match itself best)
        results = vector_store.search(query_embedding=sample_embeddings[0], n_results=2)

        assert len(results["ids"]) <= 2
        assert len(results["documents"]) == len(results["ids"])
        assert len(results["metadatas"]) == len(results["ids"])
        assert len(results["distances"]) == len(results["ids"])

        # First result should be the closest match
        assert results["ids"][0] in sample_ids

    def test_search_with_filter(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test searching with metadata filter."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        # Search only for classes
        results = vector_store.search(
            query_embedding=sample_embeddings[0],
            n_results=10,
            where={"type": "class"},
        )

        # Should only return class results
        for metadata in results["metadatas"]:
            assert metadata["type"] == "class"

    def test_search_empty_store(self, vector_store: VectorStore) -> None:
        """Test searching in empty store."""
        results = vector_store.search(query_embedding=[0.1, 0.2, 0.3], n_results=5)

        assert len(results["ids"]) == 0
        assert len(results["documents"]) == 0

    def test_get_by_id(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test retrieving chunk by ID."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        result = vector_store.get_by_id("chunk_1")

        assert result is not None
        assert result["id"] == "chunk_1"
        assert result["document"] == sample_documents[0]
        assert result["metadata"] == sample_metadatas[0]

    def test_get_by_id_not_found(self, vector_store: VectorStore) -> None:
        """Test retrieving non-existent chunk."""
        result = vector_store.get_by_id("nonexistent")
        assert result is None

    def test_delete_by_file(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test deleting chunks by file path."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        initial_count = vector_store.count()

        # Delete chunks from one file
        deleted = vector_store.delete_by_file("EntityManager.cs")

        assert deleted == 1
        assert vector_store.count() == initial_count - 1

        # Verify chunk is gone
        result = vector_store.get_by_id("chunk_1")
        assert result is None

    def test_delete_by_file_not_found(self, vector_store: VectorStore) -> None:
        """Test deleting from non-existent file."""
        deleted = vector_store.delete_by_file("nonexistent.cs")
        assert deleted == 0

    def test_clear(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test clearing all data from the store."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        assert vector_store.count() > 0

        vector_store.clear()

        assert vector_store.count() == 0

    def test_count(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test counting chunks in the store."""
        assert vector_store.count() == 0

        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        assert vector_store.count() == 3

    def test_get_stats(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test getting store statistics."""
        stats = vector_store.get_stats()

        assert stats["total_chunks"] == 0
        assert stats["unique_files_sampled"] == 0

        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        stats = vector_store.get_stats()

        assert stats["total_chunks"] == 3
        assert stats["unique_files_sampled"] > 0
        assert "class" in stats["code_types"]
        assert stats["collection_name"] == "test_collection"

    def test_list_files(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test listing files in the store."""
        files = vector_store.list_files()
        assert len(files) == 0

        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        files = vector_store.list_files()

        assert len(files) == 3
        assert "EntityManager.cs" in files
        assert "IRepository.cs" in files
        assert "Point.cs" in files
        assert files == sorted(files)  # Should be sorted

    def test_update_metadata(
        self,
        vector_store: VectorStore,
        sample_embeddings: list[list[float]],
        sample_documents: list[str],
        sample_metadatas: list[dict[str, str]],
        sample_ids: list[str],
    ) -> None:
        """Test updating metadata for a chunk."""
        vector_store.add_embeddings(
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas,
            ids=sample_ids,
        )

        # Update metadata
        new_metadata = {"file": "EntityManager.cs", "type": "class", "updated": "true"}
        vector_store.update_metadata("chunk_1", new_metadata)

        # Verify update
        result = vector_store.get_by_id("chunk_1")
        assert result is not None
        assert result["metadata"]["updated"] == "true"

    def test_persistence(self, temp_chroma_dir: Path) -> None:
        """Test that data persists across store instances."""
        # Create first store and add data
        store1 = VectorStore(persist_dir=temp_chroma_dir, collection_name="persist_test")
        store1.add_embeddings(
            embeddings=[[0.1, 0.2]],
            documents=["test"],
            metadatas=[{"key": "value"}],
            ids=["test_id"],
        )

        assert store1.count() == 1

        # Close first store to release lock
        store1.close()

        # Create second store with same directory
        store2 = VectorStore(persist_dir=temp_chroma_dir, collection_name="persist_test")

        # Should have the same data
        assert store2.count() == 1
        result = store2.get_by_id("test_id")
        assert result is not None
        assert result["metadata"]["key"] == "value"

        # Clean up
        store2.close()

    def test_collection_compatibility_property(self, vector_store: VectorStore) -> None:
        """Test collection property for compatibility."""
        # Should return self for compatibility
        assert vector_store.collection is vector_store

    def test_get_compatibility_method(self, vector_store: VectorStore) -> None:
        """Test get() compatibility method for ChromaDB-style calls."""
        vector_store.add_embeddings(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            documents=["doc1", "doc2"],
            metadatas=[{"type": "class"}, {"type": "method"}],
            ids=["id1", "id2"],
        )

        # Test get with where filter
        result = vector_store.get(where={"type": "class"})

        assert "ids" in result
        assert "metadatas" in result
        assert len(result["ids"]) >= 1

    def test_get_compatibility_with_limit(self, vector_store: VectorStore) -> None:
        """Test get() with limit parameter."""
        vector_store.add_embeddings(
            embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            documents=["doc1", "doc2", "doc3"],
            metadatas=[{"type": "class"}, {"type": "class"}, {"type": "class"}],
            ids=["id1", "id2", "id3"],
        )

        result = vector_store.get(where={"type": "class"}, limit=2)

        assert len(result["ids"]) <= 2

    def test_search_with_empty_results(self, vector_store: VectorStore) -> None:
        """Test searching when no results match."""
        # Don't add any data
        result = vector_store.search(query_embedding=[0.9, 0.9], n_results=5)

        assert result["ids"] == []
        assert result["documents"] == []
        assert result["metadatas"] == []
        assert result["distances"] == []

    def test_get_by_id_not_found(self, vector_store: VectorStore) -> None:
        """Test get_by_id when ID doesn't exist."""
        result = vector_store.get_by_id("nonexistent_id")

        assert result is None

    def test_delete_by_file_not_found(self, vector_store: VectorStore) -> None:
        """Test delete_by_file when file doesn't exist."""
        count = vector_store.delete_by_file("nonexistent.cs")

        assert count == 0

    def test_list_files_empty(self, vector_store: VectorStore) -> None:
        """Test list_files when store is empty."""
        files = vector_store.list_files()

        assert files == []

    def test_get_stats_empty_store(self, vector_store: VectorStore) -> None:
        """Test get_stats when store is empty."""
        stats = vector_store.get_stats()

        assert stats["total_chunks"] == 0
        assert stats["unique_files_sampled"] == 0
        assert stats["code_types"] == []

    def test_update_metadata_not_found(self, vector_store: VectorStore) -> None:
        """Test update_metadata when chunk doesn't exist."""
        # Should not raise, just fail silently
        vector_store.update_metadata("nonexistent", {"key": "value"})
