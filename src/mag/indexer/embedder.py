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
        incremental: bool = True,
    ) -> dict[str, int]:
        """
        Index the entire codebase.

        Args:
            progress_callback: Optional callback function(message, current, total)
                             for progress reporting.
            incremental: If True, only re-index files that have changed since last indexing.
                        If False, re-index all files.

        Returns:
            Dictionary with indexing statistics (includes 'files_skipped' for incremental).
        """
        logger.info("Starting codebase indexing...")

        # Discover files
        files = self.discovery.discover_files()
        total_files = len(files)

        if total_files == 0:
            logger.warning("No files found to index")
            return {"files_processed": 0, "chunks_created": 0, "errors": 0, "files_skipped": 0}

        # Filter files for incremental indexing
        if incremental:
            files_to_index = []
            files_skipped = 0
            for file_path in files:
                if self._needs_reindexing(file_path):
                    files_to_index.append(file_path)
                else:
                    files_skipped += 1
                    logger.debug(f"Skipping unchanged file: {file_path}")
            logger.info(f"Found {total_files} files total, {len(files_to_index)} need indexing, {files_skipped} unchanged")
        else:
            files_to_index = files
            files_skipped = 0
            logger.info(f"Found {total_files} files to index (full reindex)")

        if len(files_to_index) == 0:
            logger.info("No files need indexing")
            return {"files_processed": 0, "chunks_created": 0, "errors": 0, "files_skipped": files_skipped}

        if progress_callback:
            progress_callback("Discovering files", 0, len(files_to_index))

        # Process files in parallel
        total_chunks = 0
        total_errors = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._index_file, file_path): file_path for file_path in files_to_index
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
                            len(files_to_index),
                        )

                    logger.info(f"Indexed {file_path}: {chunks_count} chunks")

                except Exception as e:
                    total_errors += 1
                    logger.error(f"Failed to index {file_path}: {e}")

                    if progress_callback:
                        progress_callback(
                            f"Error indexing {file_path.name}",
                            i,
                            len(files_to_index),
                        )

        logger.info(
            f"Indexing complete: {len(files_to_index)} files processed, {total_chunks} chunks, {total_errors} errors, {files_skipped} skipped"
        )

        return {
            "files_processed": len(files_to_index),
            "chunks_created": total_chunks,
            "errors": total_errors,
            "files_skipped": files_skipped,
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

        # Get file modification time for incremental indexing
        file_mtime = file_path.stat().st_mtime

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
            # Add modification time for incremental indexing
            metadata["file_mtime"] = file_mtime
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

    def _needs_reindexing(self, file_path: Path) -> bool:
        """
        Check if a file needs reindexing based on modification time.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if file needs reindexing, False otherwise.
        """
        try:
            # Get current file modification time
            current_mtime = file_path.stat().st_mtime

            # Query vector store for existing chunks from this file
            # Use the collection.get() compatibility method
            results = self.vector_store.collection.get(
                where={"file": str(file_path)},
                limit=1,
            )

            # If no chunks exist for this file, it needs indexing
            if not results["ids"] or len(results["ids"]) == 0:
                logger.debug(f"File {file_path} not found in index, needs indexing")
                return True

            # Check if stored modification time matches current
            if results["metadatas"] and len(results["metadatas"]) > 0:
                stored_mtime = results["metadatas"][0].get("file_mtime")
                if stored_mtime is None:
                    # No mtime stored, assume needs reindexing
                    logger.debug(f"File {file_path} has no stored mtime, needs reindexing")
                    return True

                # Compare modification times
                if current_mtime > stored_mtime:
                    logger.debug(f"File {file_path} has been modified, needs reindexing")
                    return True

                logger.debug(f"File {file_path} is up to date")
                return False

            # If we can't determine, assume needs reindexing
            return True

        except Exception as e:
            logger.warning(f"Error checking if file needs reindexing {file_path}: {e}, assuming yes")
            return True
