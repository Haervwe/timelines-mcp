"""
Repository test fixtures

Provides repository fixtures with configured adapters.
"""

import pytest

from timelines_mcp.domain.repository import TimelineRepository

# Import adapter fixtures so they're available to repository tests
from tests.adapters.conftest import (
    chroma_adapter,
    chroma_persistent_adapter,
    sqlite_adapter,
    sqlite_file_adapter,
)


# ==========================================
# Repository Fixtures
# ==========================================


@pytest.fixture
async def repository(sqlite_adapter):
    """Provides TimelineRepository with SQLite adapter"""
    repo = TimelineRepository(storage=sqlite_adapter)
    await repo.initialize()
    
    yield repo
    
    await repo.close()


@pytest.fixture
async def repository_with_vector(sqlite_adapter, chroma_adapter):
    """Provides TimelineRepository with both SQLite and Chroma adapters"""
    repo = TimelineRepository(storage=sqlite_adapter, vector=chroma_adapter)
    await repo.initialize()
    
    yield repo
    
    await repo.close()
