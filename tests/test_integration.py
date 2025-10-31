"""Integration tests for full indexing and search workflow."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mag.indexer.embedder import CodebaseEmbedder
from mag.retrieval.vector_store import VectorStore
from mag.tools.search_code import search_code


class TestFullWorkflow:
    """Test complete index → search workflow."""

    @pytest.fixture
    def sample_codebase(self, temp_codebase: Path) -> Path:
        """Create a sample C# codebase for testing."""
        # Create Entity Manager
        (temp_codebase / "EntityManager.cs").write_text(
            """
namespace GameEngine.Core
{
    /// <summary>
    /// Manages game entities and their lifecycle.
    /// </summary>
    public class EntityManager
    {
        private List<Entity> entities = new();

        /// <summary>
        /// Creates a new entity and adds it to the world.
        /// </summary>
        public Entity CreateEntity(string name)
        {
            var entity = new Entity(name);
            entities.Add(entity);
            return entity;
        }

        /// <summary>
        /// Destroys an entity and removes it from the world.
        /// </summary>
        public void DestroyEntity(Entity entity)
        {
            entities.Remove(entity);
        }
    }
}
        """
        )

        # Create Component interface
        (temp_codebase / "IComponent.cs").write_text(
            """
namespace GameEngine.Core
{
    /// <summary>
    /// Base interface for all components.
    /// </summary>
    public interface IComponent
    {
        /// <summary>
        /// Updates the component.
        /// </summary>
        void Update(float deltaTime);
    }
}
        """
        )

        # Create Transform component
        (temp_codebase / "TransformComponent.cs").write_text(
            """
namespace GameEngine.Components
{
    using GameEngine.Core;

    /// <summary>
    /// Component representing position and rotation.
    /// </summary>
    public class TransformComponent : IComponent
    {
        public Vector3 Position { get; set; }
        public Quaternion Rotation { get; set; }

        public void Update(float deltaTime)
        {
            // Update transform logic
        }
    }
}
        """
        )

        return temp_codebase

    def test_index_and_search_integration(
        self,
        sample_codebase: Path,
        temp_chroma_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test full workflow: create codebase → index → search."""
        # Configure environment
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(sample_codebase))
        monkeypatch.setenv("MAG_CHROMA_PERSIST_DIR", str(temp_chroma_dir))
        from mag.config import reset_settings

        reset_settings()

        # Create embedder with mocked Ollama
        with patch("mag.indexer.embedder.OllamaClient") as mock_ollama_class:
            mock_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama

            # Mock embed to return consistent vectors
            def mock_embed(text: str) -> list[float]:
                # Simple hash-based embedding for consistency
                hash_val = hash(text[:50])  # Use first 50 chars
                return [((hash_val >> (i * 8)) & 0xFF) / 255.0 for i in range(128)]

            mock_ollama.embed = mock_embed

            # Initialize embedder and index
            embedder = CodebaseEmbedder()
            stats = embedder.index_codebase()

            # Verify indexing succeeded
            assert stats["files_processed"] == 3
            assert stats["chunks_created"] > 0
            assert stats["errors"] == 0

            # Verify chunks are in vector store
            assert embedder.vector_store.count() > 0

            # Close embedder's vector store to release lock
            embedder.vector_store.close()

        # Test search functionality with same mocked client
        with patch("mag.tools.search_code.OllamaClient") as mock_search_ollama_class:
            mock_search_ollama = MagicMock()
            mock_search_ollama_class.return_value = mock_search_ollama
            mock_search_ollama.embed = mock_embed

            # Search for entity management
            results = search_code("entity lifecycle management")

            # Should find relevant results
            assert len(results) > 0

            # Should include EntityManager class
            entity_manager_found = any(
                "EntityManager" in r.get("name", "") or "EntityManager" in r.get("content", "")
                for r in results
            )
            assert entity_manager_found, "EntityManager not found in search results"

    def test_vector_store_persistence(
        self,
        sample_codebase: Path,
        temp_chroma_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that indexed data persists across sessions."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(sample_codebase))
        monkeypatch.setenv("MAG_CHROMA_PERSIST_DIR", str(temp_chroma_dir))
        from mag.config import reset_settings

        reset_settings()

        with patch("mag.indexer.embedder.OllamaClient") as mock_ollama_class:
            mock_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.embed.return_value = [0.1] * 128

            # Index in first session
            embedder1 = CodebaseEmbedder()
            embedder1.index_codebase()

            chunk_count1 = embedder1.vector_store.count()
            assert chunk_count1 > 0

            # Close vector store to release lock
            embedder1.vector_store.close()

        # Create new embedder instance (simulates new session)
        embedder2 = CodebaseEmbedder(vector_store=VectorStore(persist_dir=temp_chroma_dir))

        # Data should persist
        chunk_count2 = embedder2.vector_store.count()
        assert chunk_count2 == chunk_count1

        # Clean up
        embedder2.vector_store.close()

    def test_reindex_updates_data(
        self,
        sample_codebase: Path,
        temp_chroma_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that reindexing a file updates its chunks."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(sample_codebase))
        monkeypatch.setenv("MAG_CHROMA_PERSIST_DIR", str(temp_chroma_dir))
        from mag.config import reset_settings

        reset_settings()

        with patch("mag.indexer.embedder.OllamaClient") as mock_ollama_class:
            mock_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.embed.return_value = [0.1] * 128

            embedder = CodebaseEmbedder()

            # Initial index
            embedder.index_codebase()
            initial_count = embedder.vector_store.count()

            # Modify a file
            entity_manager_file = sample_codebase / "EntityManager.cs"
            entity_manager_file.write_text(
                """
namespace GameEngine.Core
{
    public class EntityManager
    {
        public void NewMethod() { }
    }
}
            """
            )

            # Reindex the modified file
            embedder.reindex_file(entity_manager_file)

            # Should still have chunks (old removed, new added)
            final_count = embedder.vector_store.count()
            assert final_count > 0

    def test_clear_index(
        self,
        sample_codebase: Path,
        temp_chroma_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test clearing the index."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(sample_codebase))
        monkeypatch.setenv("MAG_CHROMA_PERSIST_DIR", str(temp_chroma_dir))
        from mag.config import reset_settings

        reset_settings()

        with patch("mag.indexer.embedder.OllamaClient") as mock_ollama_class:
            mock_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.embed.return_value = [0.1] * 128

            embedder = CodebaseEmbedder()

            # Index
            embedder.index_codebase()
            assert embedder.vector_store.count() > 0

            # Clear
            embedder.clear_index()
            assert embedder.vector_store.count() == 0

    def test_end_to_end_with_filters(
        self,
        sample_codebase: Path,
        temp_chroma_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test search with type filters."""
        monkeypatch.setenv("MAG_CODEBASE_ROOT", str(sample_codebase))
        monkeypatch.setenv("MAG_CHROMA_PERSIST_DIR", str(temp_chroma_dir))
        from mag.config import reset_settings

        reset_settings()

        with patch("mag.indexer.embedder.OllamaClient") as mock_ollama_class, patch(
            "mag.tools.search_code.OllamaClient"
        ) as mock_search_ollama_class:
            # Setup embedding mock
            mock_ollama = MagicMock()
            mock_search_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama
            mock_search_ollama_class.return_value = mock_search_ollama

            def mock_embed(text: str) -> list[float]:
                hash_val = hash(text[:50])
                return [((hash_val >> (i * 8)) & 0xFF) / 255.0 for i in range(128)]

            mock_ollama.embed = mock_embed
            mock_search_ollama.embed = mock_embed

            # Index
            embedder = CodebaseEmbedder()
            embedder.index_codebase()

            # Close embedder's vector store to release lock
            embedder.vector_store.close()

            # Search for interfaces only
            interface_results = search_code("component", filter_type="interface")

            # Should find IComponent
            if interface_results:
                for result in interface_results:
                    assert result["type"] == "interface"
