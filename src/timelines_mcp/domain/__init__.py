"""
Domain Objects

This module contains the core domain objects for the timelines application,
such as Timeline, Event, Entity, and other domain entities.
"""

from .models import (
    Entity,
    EntityType,
    Event,
    EventParticipation,
    EventType,
    ParticipationRole,
    Project,
    Relationship,
    RelationType,
    StateSnapshot,
    Timeline,
    TimelineStatus,
)
from .protocols import StorageAdapter, VectorAdapter

__all__ = [
    # Models
    "Entity",
    "EntityType",
    "Event",
    "EventParticipation",
    "EventType",
    "ParticipationRole",
    "Project",
    "Relationship",
    "RelationType",
    "StateSnapshot",
    "Timeline",
    "TimelineStatus",
    # Protocols
    "StorageAdapter",
    "VectorAdapter",
]
