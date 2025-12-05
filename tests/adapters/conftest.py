"""
Adapter-specific test fixtures

Provides database adapter fixtures for SQLite and ChromaDB testing.
Also provides factory fixtures needed for adapter tests.
"""

import pytest

from timelines_mcp.adapters.chroma import ChromaAdapter
from timelines_mcp.adapters.sqlite import SQLiteAdapter


# ==========================================
# SQLite Adapter Fixtures
# ==========================================


@pytest.fixture
async def sqlite_adapter():
    """
    Provides an in-memory SQLite adapter with automatic cleanup
    
    Uses :memory: database so no filesystem cleanup needed.
    """
    adapter = SQLiteAdapter(":memory:")
    await adapter.initialize()
    
    yield adapter
    
    await adapter.close()


@pytest.fixture
async def sqlite_file_adapter(tmp_path):
    """
    Provides a file-based SQLite adapter with automatic cleanup
    
    Uses temporary directory that pytest automatically cleans up.
    """
    db_path = tmp_path / "test.db"
    adapter = SQLiteAdapter(str(db_path))
    await adapter.initialize()
    
    yield adapter
    
    await adapter.close()


# ==========================================
# Chroma Adapter Fixtures
# ==========================================


@pytest.fixture(scope="function")
async def chroma_adapter():
    """
    Provides an in-memory Chroma adapter for testing
    
    Uses EphemeralClient - no files created.
    Each test gets a unique collection to ensure isolation.
    """
    import uuid
    collection_name = f"test_{uuid.uuid4().hex[:8]}"
    
    adapter = ChromaAdapter(
        collection_name=collection_name,
        persist_directory=None  # In-memory for tests
    )
    await adapter.initialize()
    
    yield adapter
    
    # Cleanup using adapter's close method
    await adapter.close()


@pytest.fixture(scope="function")
async def chroma_persistent_adapter(tmp_path):
    """
    Provides a persistent Chroma adapter for testing persistence behavior
    
    Uses temporary directory that pytest automatically cleans up.
    Only use this fixture for tests that specifically test persistence.
    """
    import uuid
    persist_dir = tmp_path / "chroma_data"
    collection_name = f"test_{uuid.uuid4().hex[:8]}"
    
    adapter = ChromaAdapter(
        collection_name=collection_name,
        persist_directory=str(persist_dir)
    )
    await adapter.initialize()
    
    yield adapter
    
    # Cleanup using adapter's close method
    await adapter.close()


# ==========================================
# Factory Fixtures (for adapter tests)
# ==========================================


@pytest.fixture
def project_factory():
    """Provides ProjectFactory instance"""
    from tests.conftest import ProjectFactory
    return ProjectFactory


@pytest.fixture
def timeline_factory():
    """Provides TimelineFactory instance"""
    from tests.conftest import TimelineFactory
    return TimelineFactory


@pytest.fixture
def event_factory():
    """Provides EventFactory instance"""
    from tests.conftest import EventFactory
    return EventFactory


@pytest.fixture
def entity_factory():
    """Provides EntityFactory instance"""
    from tests.conftest import EntityFactory
    return EntityFactory


@pytest.fixture
def relationship_factory():
    """Provides RelationshipFactory instance"""
    from tests.conftest import RelationshipFactory
    return RelationshipFactory


@pytest.fixture
def snapshot_factory():
    """Provides StateSnapshotFactory instance"""
    from tests.conftest import StateSnapshotFactory
    return StateSnapshotFactory
