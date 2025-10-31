"""Qdrant vector store wrapper for code embeddings."""

import threading
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from mag.config import get_settings

# Namespace UUID for generating deterministic UUIDs from string IDs
NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # Standard namespace UUID

# Global lock for thread-safe database access (SQLite in embedded mode)
_db_lock = threading.RLock()


class VectorStore:
    """Wrapper for Qdrant vector store operations."""

    def __init__(self, persist_dir: Path | None = None, collection_name: str | None = None) -> None:
        """
        Initialize vector store.

        Args:
            persist_dir: Directory for persistent storage. If None, uses settings.
            collection_name: Name of the collection. If None, uses settings.
        """
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name

        # Ensure persist directory exists
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Qdrant client in embedded mode
        self.client = QdrantClient(path=str(self.persist_dir))

        # Determine vector size from first embedding or use default
        self._vector_size = 384  # Default size, will be updated on first add

        # Create collection if it doesn't exist
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure collection exists, create if it doesn't."""
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)

        if not collection_exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )

    def close(self) -> None:
        """Close the Qdrant client and release resources."""
        try:
            self.client.close()
        except Exception:
            pass  # Ignore errors on close

    @staticmethod
    def _to_uuid(id_str: str) -> UUID:
        """Convert string ID to deterministic UUID."""
        return uuid5(NAMESPACE, id_str)

    @staticmethod
    def _from_uuid(uuid_val: UUID | str) -> str:
        """Convert UUID back to string ID (stored in metadata)."""
        return str(uuid_val)

    def add_embeddings(
        self,
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Add embeddings to the vector store.

        Args:
            embeddings: List of embedding vectors.
            documents: List of document texts.
            metadatas: List of metadata dictionaries.
            ids: List of unique IDs for each embedding.

        Raises:
            ValueError: If input lists have different lengths.
        """
        if not (len(embeddings) == len(documents) == len(metadatas) == len(ids)):
            msg = "All input lists must have the same length"
            raise ValueError(msg)

        if not embeddings:
            return

        # Use global lock for thread-safe database access
        with _db_lock:
            # Update vector size if needed and recreate collection
            if embeddings and len(embeddings[0]) != self._vector_size:
                self._vector_size = len(embeddings[0])
                # Delete and recreate collection with correct vector size
                try:
                    self.client.delete_collection(self.collection_name)
                except Exception:
                    pass  # Collection might not exist yet
                self._ensure_collection()

            # Create points
            points = []
            for i, (embedding, document, metadata, point_id) in enumerate(
                zip(embeddings, documents, metadatas, ids)
            ):
                # Ensure all metadata values are JSON-serializable
                # Store original ID in metadata for retrieval
                payload = {**metadata, "document": document, "_original_id": point_id}

                points.append(
                    PointStruct(
                        id=str(self._to_uuid(point_id)),
                        vector=embedding,
                        payload=payload,
                    )
                )

            # Upsert points - retry once if collection doesn't exist
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )
            except Exception as e:
                # Collection might have been deleted by another thread, recreate and retry
                if "not found" in str(e).lower():
                    self._ensure_collection()
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points,
                    )
                else:
                    raise

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search for similar code chunks.

        Args:
            query_embedding: Query embedding vector.
            n_results: Number of results to return.
            where: Optional metadata filter (e.g., {"type": "class"}).

        Returns:
            Dictionary with search results containing:
            - ids: List of result IDs
            - documents: List of matching documents
            - metadatas: List of metadata dicts
            - distances: List of distance scores
        """
        # Build filter if provided
        query_filter = None
        if where:
            must_conditions = []
            for key, value in where.items():
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )
            if must_conditions:
                query_filter = Filter(must=must_conditions)

        # Search using new query_points API
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=n_results,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            ).points
        except Exception:
            # Collection might not exist or be empty
            return {
                "ids": [],
                "documents": [],
                "metadatas": [],
                "distances": [],
            }

        # Format results
        ids = []
        documents = []
        metadatas = []
        distances = []

        for result in results:
            payload = result.payload or {}
            # Get original ID from metadata, fallback to UUID
            original_id = payload.pop("_original_id", str(result.id))
            ids.append(original_id)
            documents.append(payload.pop("document", ""))
            metadatas.append(payload)
            distances.append(result.score)  # Qdrant returns similarity score, not distance

        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
        }

    def get_by_id(self, chunk_id: str) -> dict[str, Any] | None:
        """
        Get a specific chunk by ID.

        Args:
            chunk_id: Chunk ID to retrieve.

        Returns:
            Dictionary with chunk data, or None if not found.
        """
        try:
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[str(self._to_uuid(chunk_id))],
                with_vectors=True,  # Include vectors in response
            )
        except Exception:
            return None

        if not results:
            return None

        result = results[0]
        payload = result.payload or {}
        original_id = payload.pop("_original_id", chunk_id)
        document = payload.pop("document", "")

        return {
            "id": original_id,
            "document": document,
            "metadata": payload,
            "embedding": result.vector,
        }

    def delete_by_file(self, file_path: str) -> int:
        """
        Delete all chunks from a specific file.

        Args:
            file_path: File path to delete chunks for.

        Returns:
            Number of chunks deleted.
        """
        with _db_lock:
            # Scroll through all points with this file
            try:
                # Get all points matching the file
                scroll_filter = Filter(
                    must=[FieldCondition(key="file", match=MatchValue(value=file_path))]
                )

                points, _ = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=scroll_filter,
                    limit=10000,  # Large limit to get all
                )

                if not points:
                    return 0

                # Delete by UUIDs
                uuids_to_delete = [p.id for p in points]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=uuids_to_delete,
                )

                return len(uuids_to_delete)

            except Exception:
                return 0

    def clear(self) -> None:
        """Delete all data from the collection."""
        with _db_lock:
            try:
                # Get all point IDs and delete them
                points, _ = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100000,  # Large limit to get all points
                )

                if points:
                    # Delete all points
                    point_ids = [p.id for p in points]
                    self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=point_ids,
                    )
            except Exception:
                # If collection doesn't exist or other error, try delete and recreate
                try:
                    self.client.delete_collection(self.collection_name)
                except Exception:
                    pass
                self._ensure_collection()

    def count(self) -> int:
        """
        Get total number of chunks in the store.

        Returns:
            Number of chunks.
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count or 0
        except Exception:
            return 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with statistics.
        """
        count = self.count()

        if count == 0:
            return {
                "total_chunks": 0,
                "unique_files_sampled": 0,
                "code_types": [],
                "collection_name": self.collection_name,
            }

        # Scroll through sample to get statistics
        sample_size = min(1000, count)
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=sample_size,
            )

            files = set()
            types = set()

            for point in points:
                payload = point.payload or {}
                if "file" in payload:
                    files.add(payload["file"])
                if "type" in payload:
                    types.add(payload["type"])

            return {
                "total_chunks": count,
                "unique_files_sampled": len(files),
                "code_types": list(types),
                "collection_name": self.collection_name,
            }

        except Exception:
            return {
                "total_chunks": count,
                "unique_files_sampled": 0,
                "code_types": [],
                "collection_name": self.collection_name,
            }

    def list_files(self, limit: int = 100) -> list[str]:
        """
        List files in the vector store.

        Args:
            limit: Maximum number of files to return.

        Returns:
            List of unique file paths.
        """
        try:
            # Scroll through points to collect file paths
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit * 10,  # Get more to ensure coverage
            )

            files = set()
            for point in points:
                payload = point.payload or {}
                if "file" in payload:
                    files.add(payload["file"])
                    if len(files) >= limit:
                        break

            return sorted(files)

        except Exception:
            return []

    def update_metadata(self, chunk_id: str, metadata: dict[str, Any]) -> None:
        """
        Update metadata for a specific chunk.

        Args:
            chunk_id: Chunk ID to update.
            metadata: New metadata dictionary.
        """
        with _db_lock:
            try:
                # Get current point
                uuid_id = str(self._to_uuid(chunk_id))
                results = self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[uuid_id],
                    with_vectors=True,  # Need vectors for upsert
                )

                if not results:
                    return

                point = results[0]
                payload = point.payload or {}
                document = payload.get("document", "")

                # Update payload, preserve original ID
                new_payload = {**metadata, "document": document, "_original_id": chunk_id}

                # Upsert with same vector but new payload
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=uuid_id,
                            vector=point.vector,
                            payload=new_payload,
                        )
                    ],
                )

            except Exception:
                pass  # Silently fail if update fails

    @property
    def collection(self) -> Any:
        """
        Compatibility property for tests that access collection directly.

        Returns:
            Self, allowing collection.get() style calls.
        """
        return self

    def get(self, **kwargs: Any) -> dict[str, list[Any]]:
        """
        Compatibility method for ChromaDB-style get() calls.

        This allows tests to call collection.get(where=...) directly.
        """
        where = kwargs.get("where", {})
        limit = kwargs.get("limit", 100)

        # Build filter
        query_filter = None
        if where:
            must_conditions = []
            for key, value in where.items():
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            if must_conditions:
                query_filter = Filter(must=must_conditions)

        try:
            # Scroll with filter
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
            )

            ids = []
            metadatas = []

            for point in points:
                payload = point.payload or {}
                # Get original ID from metadata
                original_id = payload.pop("_original_id", str(point.id))
                ids.append(original_id)
                payload.pop("document", None)  # Remove document from metadata
                metadatas.append(payload)

            return {
                "ids": ids,
                "metadatas": metadatas,
            }

        except Exception:
            return {
                "ids": [],
                "metadatas": [],
            }
