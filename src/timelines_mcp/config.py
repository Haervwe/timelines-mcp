"""
Configuration - Load settings from environment
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class StorageAdapter(str, Enum):
    """Storage backend options"""

    SQLITE = "sqlite"
    POSTGRES = "postgres"


class VectorAdapter(str, Enum):
    """Vector backend options"""

    CHROMA = "chroma"
    QDRANT = "qdrant"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    # Storage backend
    storage_adapter: StorageAdapter = StorageAdapter.SQLITE

    # SQLite settings
    sqlite_path: Path = Path("./data/timelines.db")

    # PostgreSQL settings (for production)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "timelines"
    postgres_password: str = ""
    postgres_database: str = "timelines"

    # Vector backend
    vector_adapter: VectorAdapter = VectorAdapter.CHROMA

    # Chroma settings
    chroma_persist_dir: Path = Path("./data/chroma_db")
    chroma_embedding_model: str = "all-MiniLM-L6-v2"

    # Qdrant settings (for production)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables"""
        return cls(
            # Storage backend
            storage_adapter=StorageAdapter(
                os.getenv("STORAGE_ADAPTER", StorageAdapter.SQLITE.value)
            ),
            # SQLite
            sqlite_path=Path(os.getenv("SQLITE_PATH", "./data/timelines.db")),
            # PostgreSQL
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_user=os.getenv("POSTGRES_USER", "timelines"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            postgres_database=os.getenv("POSTGRES_DATABASE", "timelines"),
            # Vector backend
            vector_adapter=VectorAdapter(
                os.getenv("VECTOR_ADAPTER", VectorAdapter.CHROMA.value)
            ),
            # Chroma
            chroma_persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")),
            chroma_embedding_model=os.getenv("CHROMA_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            # Qdrant
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            qdrant_api_key=os.getenv("QDRANT_API_KEY", ""),
        )


# Global config instance
config = DatabaseConfig.from_env()
