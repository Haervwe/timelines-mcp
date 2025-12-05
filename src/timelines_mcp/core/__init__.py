"""
Core Infrastructure - Factories and foundational components
"""

from .factories import (
    close_storage,
    close_vector,
    get_storage_adapter,
    get_vector_adapter,
    initialize_storage,
    initialize_vector,
)

__all__ = [
    "get_storage_adapter",
    "get_vector_adapter",
    "initialize_storage",
    "initialize_vector",
    "close_storage",
    "close_vector",
]
