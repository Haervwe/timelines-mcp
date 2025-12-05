"""
Dependency Injection for Tools

Provides shared instances of services and repositories for tools to use.
"""

from .core.factories import get_storage_adapter, get_vector_adapter
from .domain.repository import TimelineRepository
from .services.timeline_service import TimelineService
from .settings.config import DatabaseConfig

# Global service instance (initialized on first use)
_service: TimelineService | None = None
_config: DatabaseConfig | None = None


def get_config() -> DatabaseConfig:
    """Get configuration singleton."""
    global _config
    if _config is None:
        _config = DatabaseConfig.from_env()
    return _config


async def get_service() -> TimelineService:
    """Get or initialize the service instance."""
    global _service
    if _service is None:
        config = get_config()
        storage = get_storage_adapter(config)
        vector = get_vector_adapter(config)
        repository = TimelineRepository(storage=storage, vector=vector)
        _service = TimelineService(repository=repository)
        await _service.initialize()
    return _service
