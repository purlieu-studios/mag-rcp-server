"""Code embedding and indexing orchestration."""

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from mag.config import get_settings
from mag.indexer.chunker import SemanticChunker
from mag.indexer.discovery import CodebaseDiscovery
from mag.indexer.parser import CSharpParser
from mag.llm.ollama_client import OllamaClient
from mag.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)


class CodebaseEmbedder:
    """Orchestrates the full indexing pipeline for a codebase."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        ollama_client: OllamaClient | None = None,
    ) -> None:
        """
        Initialize the embedder.

        Args:
            vector_store: Vector store instance. If None, creates new one.
            ollama_client: Ollama client instance. If None, creates new one.
        """
        self.vector_store = vector_store or VectorStore()
        self.ollama_client = ollama_client or OllamaClient()
        self.parser = CSharpParser()
        self.chunker = SemanticChunker()
        self.discovery = CodebaseDiscovery()

        settings = get_settings()
        self.max_workers = settings.max_workers

    def index_codebase(
        self,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, int]:
        """
        Index the entire codebase.

        Args:
            progress_callback: Optional callback function(message, current, total)
                             for progress reporting.

        Returns:
            Dictionary with indexing statistics.
        """
        logger.info("Starting codebase indexing...")

        # Discover files
        files = self.discovery.discover_files()
        total_files = len(files)

        if total_files == 0:
            logger.warning("No files found to index")
            return {"files_processed": 0, "chunks_created": 0, "errors": 0}

        logger.info(f"Found {total_files} files to index")

        if progress_callback:
            progress_callback("Discovering files", 0, total_files)

        # Process files in parallel
        total_chunks = 0
        total_errors = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._index_file, file_path): file_path for file_path in files
            }

            for i, future in enumerate(as_completed(future_to_file), 1):
                file_path = future_to_file[future]

                try:
                    chunks_count = future.result()
                    total_chunks += chunks_count

                    if progress_callback:
                        progress_callback(
                            f"Indexed {file_path.name}",
                            i,
                            total_files,
                        )

                    logger.info(f"Indexed {file_path}: {chunks_count} chunks")

                except Exception as e:
                    total_errors += 1
                    logger.error(f"Failed to index {file_path}: {e}")

                    if progress_callback:
                        progress_callback(
                            f"Error indexing {file_path.name}",
                            i,
                            total_files,
                        )

        logger.info(
            f"Indexing complete: {total_files} files, {total_chunks} chunks, {total_errors} errors"
        )

        return {
            "files_processed": total_files,
            "chunks_created": total_chunks,
            "errors": total_errors,
        }

    def _index_file(self, file_path: Path) -> int:
        """
        Index a single file.

        Args:
            file_path: Path to the file to index.

        Returns:
            Number of chunks created.

        Raises:
            Exception: If indexing fails.
        """
        # Parse the file
        nodes = self.parser.parse_file(file_path)

        if not nodes:
            return 0

        # Chunk the nodes
        chunks = self.chunker.chunk_nodes(nodes)

        if not chunks:
            return 0

        # Generate embeddings
        embeddings = []
        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            # Generate embedding
            embedding = self.ollama_client.embed(chunk.content)
            embeddings.append(embedding)

            # Prepare data
            documents.append(chunk.content)

            # Ensure metadata values are JSON-serializable
            metadata = {
                k: (str(v) if isinstance(v, Path) else v)
                for k, v in chunk.metadata.items()
            }
            metadatas.append(metadata)

            # Generate unique ID
            chunk_id = self._generate_chunk_id(str(file_path), chunk.content)
            ids.append(chunk_id)

        # Add to vector store
        self.vector_store.add_embeddings(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return len(chunks)

    def reindex_file(self, file_path: Path) -> int:
        """
        Reindex a specific file (delete old chunks and index new).

        Args:
            file_path: Path to the file to reindex.

        Returns:
            Number of new chunks created.
        """
        # Delete existing chunks for this file
        self.vector_store.delete_by_file(str(file_path))

        # Index the file
        return self._index_file(file_path)

    def clear_index(self) -> None:
        """Clear all indexed data from the vector store."""
        logger.info("Clearing index...")
        self.vector_store.clear()
        logger.info("Index cleared")

    def get_index_stats(self) -> dict[str, any]:
        """
        Get statistics about the current index.

        Returns:
            Dictionary with index statistics.
        """
        return self.vector_store.get_stats()

    def _generate_chunk_id(self, file_path: str, content: str) -> str:
        """
        Generate a unique ID for a chunk.

        Args:
            file_path: File path.
            content: Chunk content.

        Returns:
            Unique chunk ID.
        """
        # Create hash of file path + content
        hash_input = f"{file_path}:{content}"
        hash_digest = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        # Return first 16 characters for readability
        return f"chunk_{hash_digest[:16]}"
