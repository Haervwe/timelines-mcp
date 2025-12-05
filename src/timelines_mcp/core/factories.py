"""
Factory Functions - Instantiate adapters based on configuration

Clear, simple names. No abbreviations.
"""

from ..domain.protocols import StorageAdapter, VectorAdapter
from ..settings.config import (
    DatabaseConfig,
    StorageAdapter as StorageAdapterEnum,
    VectorAdapter as VectorAdapterEnum,
    config as default_config,
)


def get_storage_adapter(config: DatabaseConfig | None = None) -> StorageAdapter:
    """Factory for storage adapter based on config

    Returns:
        StorageAdapter implementation (SQLite or Postgres)
    """
    cfg = config or default_config

    if cfg.storage_adapter == StorageAdapterEnum.SQLITE:
        from .adapters.sqlite import SQLiteAdapter

        return SQLiteAdapter(db_path=cfg.sqlite_path)

    elif cfg.storage_adapter == StorageAdapterEnum.POSTGRES:
        # TODO: Implement PostgresAdapter when ready for production
        raise NotImplementedError(
            "PostgreSQL adapter not yet implemented. Set STORAGE_ADAPTER=sqlite in .env for now."
        )

    else:
        raise ValueError(f"Unknown storage adapter: {cfg.storage_adapter}")


def get_vector_adapter(config: DatabaseConfig | None = None) -> VectorAdapter:
    """Factory for vector adapter based on config

    Returns:
        VectorAdapter implementation (Chroma or Qdrant)
    """
    cfg = config or default_config

    if cfg.vector_adapter == VectorAdapterEnum.CHROMA:
        from .adapters.chroma import ChromaAdapter

        return ChromaAdapter(
            persist_directory=cfg.chroma_persist_dir,
            embedding_model=cfg.chroma_embedding_model,
        )

    elif cfg.vector_adapter == VectorAdapterEnum.QDRANT:
        # TODO: Implement QdrantAdapter when ready for production
        raise NotImplementedError(
            "Qdrant adapter not yet implemented. Set VECTOR_ADAPTER=chroma in .env for now."
        )

    else:
        raise ValueError(f"Unknown vector adapter: {cfg.vector_adapter}")


async def initialize_storage(storage: StorageAdapter) -> None:
    """Initialize storage adapter (creates schema/connections)"""
    await storage.initialize()


async def initialize_vector(vector: VectorAdapter) -> None:
    """Initialize vector adapter (creates collections/indexes)"""
    await vector.initialize()


async def close_storage(storage: StorageAdapter) -> None:
    """Cleanup storage adapter"""
    await storage.close()


async def close_vector(vector: VectorAdapter) -> None:
    """Cleanup vector adapter"""
    await vector.close()
