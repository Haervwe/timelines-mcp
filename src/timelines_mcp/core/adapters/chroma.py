"""
Chroma Vector Storage Adapter - Pure vector operations

Thin wrapper around ChromaDB with no embedding generation.
Embeddings are always provided externally (from LLM calls).
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings


class ChromaAdapter:
    """ChromaDB adapter implementing VectorAdapter protocol"""

    def __init__(
        self,
        collection_name: str = "timelines_events",
        persist_directory: str | None = "./chroma_data",
    ):
        """
        Initialize Chroma adapter
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist data, or None for in-memory (tests only)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client: chromadb.Client | None = None
        self.collection: chromadb.Collection | None = None

    async def initialize(self) -> None:
        """Setup vector collection"""
        if self.persist_directory is None:
            # In-memory for tests only
            self.client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            # Persistent storage for production
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def close(self) -> None:
        """Cleanup connections and release resources"""

        self.collection = None
        self.client = None

    async def insert_vector(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, str | int | float],
    ) -> None:
        """Store vector with metadata (NO embedding generation)"""
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")

        # Convert all metadata values to strings (Chroma requirement)
        str_metadata = {k: str(v) for k, v in metadata.items()}

        # Check if ID exists - if so, use upsert (update)
        try:
            existing = self.collection.get(ids=[id], include=[])
            if existing and existing["ids"]:
                # Update existing vector
                self.collection.update(
                    ids=[id],
                    embeddings=[embedding],
                    metadatas=[str_metadata],
                )
                return
        except Exception:  # pragma: no cover
            pass  # ID not found, will insert

        # Insert new vector
        self.collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[str_metadata],
        )

    async def search_vectors(
        self,
        query_embedding: list[float],
        limit: int = 10,
        metadata_filter: dict[str, str | int | float] | None = None,
    ) -> list[tuple[str, float]]:
        """Search by embedding - returns (id, score) tuples"""
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")

        # Convert metadata filter to Chroma format if provided
        where = None
        if metadata_filter:
            # Chroma uses string values in where clauses
            where = {k: str(v) for k, v in metadata_filter.items()}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
        )

        # Extract IDs and distances (convert distance to similarity score)
        if not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        distances = results["distances"][0]

        # Convert distance to similarity score (1 - distance for cosine)
        # Chroma returns cosine distance [0, 2], convert to similarity [0, 1]
        scores = [1.0 - (d / 2.0) for d in distances]

        return list(zip(ids, scores))

    async def get_vector_by_id(self, id: str) -> tuple[list[float], dict] | None:
        """Get vector and metadata by ID"""
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")

        try:
            results = self.collection.get(
                ids=[id],
                include=["embeddings", "metadatas"],
            )

            if not results["ids"]:
                return None

            embedding = results["embeddings"][0]
            metadata = results["metadatas"][0]

            return (embedding, metadata)
        except Exception:  # pragma: no cover
            # ID not found
            return None

    async def delete_vector(self, id: str) -> None:
        """Delete vector by ID"""
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")

        try:
            self.collection.delete(ids=[id])
        except Exception:  # pragma: no cover
            # ID not found - silently ignore
            pass
