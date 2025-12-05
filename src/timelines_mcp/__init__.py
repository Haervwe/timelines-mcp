"""
Timelines MCP Server

A FastMCP server for maintaining coherent long generations for time-dependent narratives.
This package helps LLMs keep track of timelines, events, and characters across fiction
and historical narratives.
"""

from .core import (
    close_storage,
    close_vector,
    get_storage_adapter,
    get_vector_adapter,
    initialize_storage,
    initialize_vector,
)
from .services import TimelineContext, TimelineService
from .settings import DatabaseConfig, StorageAdapter, VectorAdapter, config

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Services
    "TimelineService",
    "TimelineContext",
    # Core/Factories
    "get_storage_adapter",
    "get_vector_adapter",
    "initialize_storage",
    "initialize_vector",
    "close_storage",
    "close_vector",
    # Settings
    "DatabaseConfig",
    "StorageAdapter",
    "VectorAdapter",
    "config",
]
