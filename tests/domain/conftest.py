"""
Domain model test fixtures

Provides polyfactory factory fixtures for generating test domain models.
Also provides adapter fixtures needed for integration tests.
"""

import pytest


# ==========================================
# Adapter Fixtures (for domain integration tests)
# ==========================================


@pytest.fixture
async def sqlite_adapter():
    """Provides an in-memory SQLite adapter with automatic cleanup"""
    from timelines_mcp.core.adapters.sqlite import SQLiteAdapter
    
    adapter = SQLiteAdapter(":memory:")
    await adapter.initialize()
    
    yield adapter
    
    await adapter.close()


# ==========================================
# Factory Fixtures
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
