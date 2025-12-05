"""
Root test configuration and shared fixtures

Provides shared Polyfactory factories and helper functions used across all tests.
Specific test fixtures are in subdirectory conftest.py files.
"""

import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from polyfactory.factories.pydantic_factory import ModelFactory

from timelines_mcp.domain.models import (
    Entity,
    EntityProperties,
    EntityProperty,
    EntityType,
    Event,
    EventType,
    Metadata,
    Project,
    PropertyValue,
    Relationship,
    StateDelta,
    StateSnapshot,
    Timeline,
    TimelineStatus,
    WorldState,
)



def pytest_unconfigure(config):  # type: ignore
    """Force exit after all plugins finish, including coverage reporting"""
    # ChromaDB background threads prevent clean exit
    # This runs after coverage plugin completes its reporting
    os._exit(0)


# ==========================================
# Polyfactory Factories for Test Data
# ==========================================


class PropertyValueFactory(ModelFactory[PropertyValue]):
    """Factory for PropertyValue with controlled randomization"""

    __model__ = PropertyValue

    @classmethod
    def build(cls, **kwargs):
        """Build with only one value set"""
        if not any(
            k in kwargs
            for k in ["string_val", "number_val", "boolean_val", "datetime_val"]
        ):
            # Default to string value if none specified
            kwargs["string_val"] = "test_value"
            kwargs["number_val"] = None
            kwargs["boolean_val"] = None
            kwargs["datetime_val"] = None
        return super().build(**kwargs)


class EntityPropertyFactory(ModelFactory[EntityProperty]):
    """Factory for EntityProperty"""

    __model__ = EntityProperty


class MetadataFactory(ModelFactory[Metadata]):
    """Factory for Metadata"""

    __model__ = Metadata


class EntityPropertiesFactory(ModelFactory[EntityProperties]):
    """Factory for EntityProperties"""

    __model__ = EntityProperties


class StateDeltaFactory(ModelFactory[StateDelta]):
    """Factory for StateDelta"""

    __model__ = StateDelta


class WorldStateFactory(ModelFactory[WorldState]):
    """Factory for WorldState"""

    __model__ = WorldState


class ProjectFactory(ModelFactory[Project]):
    """Factory for Project entities"""

    __model__ = Project


class TimelineFactory(ModelFactory[Timeline]):
    """Factory for Timeline entities"""

    __model__ = Timeline


class EventFactory(ModelFactory[Event]):
    """Factory for Event entities"""

    __model__ = Event

    @classmethod
    def build(cls, **kwargs):
        """Ensure end_timestamp is after timestamp if provided"""
        # Set end_timestamp to None by default if not specified
        if "end_timestamp" not in kwargs:
            kwargs["end_timestamp"] = None
        
        # If both are provided, validate before building
        if kwargs.get("end_timestamp") and "timestamp" in kwargs:
            if kwargs["end_timestamp"] <= kwargs["timestamp"]:
                from datetime import timedelta
                kwargs["end_timestamp"] = kwargs["timestamp"] + timedelta(hours=1)
        
        return super().build(**kwargs)


class EntityFactory(ModelFactory[Entity]):
    """Factory for Entity entities"""

    __model__ = Entity


class RelationshipFactory(ModelFactory[Relationship]):
    """Factory for Relationship entities"""

    __model__ = Relationship

    @classmethod
    def build(cls, **kwargs):
        """Ensure valid_until is after valid_from if both provided"""
        # First, build with polyfactory's default generation
        # Set valid_from and valid_until to None if not explicitly provided
        if "valid_from" not in kwargs:
            kwargs["valid_from"] = None
        if "valid_until" not in kwargs:
            kwargs["valid_until"] = None
        
        # If both are provided, validate before building
        if kwargs.get("valid_from") and kwargs.get("valid_until"):
            if kwargs["valid_until"] <= kwargs["valid_from"]:
                from datetime import timedelta
                kwargs["valid_until"] = kwargs["valid_from"] + timedelta(days=1)
        
        return super().build(**kwargs)


class StateSnapshotFactory(ModelFactory[StateSnapshot]):
    """Factory for StateSnapshot entities"""

    __model__ = StateSnapshot

# ==========================================
# Helper Functions
# ==========================================


def create_sample_project(user_id: UUID | None = None) -> Project:
    """Create a sample project for testing"""
    return Project(
        id=uuid4(),
        user_id=user_id or uuid4(),
        name="Test Project",
        description="A test project",
        metadata=Metadata(),
    )


def create_sample_timeline(project_id: UUID, user_id: UUID) -> Timeline:
    """Create a sample timeline for testing"""
    return Timeline(
        id=uuid4(),
        project_id=project_id,
        user_id=user_id,
        name="Test Timeline",
        description="A test timeline",
        status=TimelineStatus.CANONICAL,
        metadata=Metadata(),
    )


def create_sample_event(timeline_id: UUID) -> Event:
    """Create a sample event for testing"""
    return Event(
        id=uuid4(),
        timeline_id=timeline_id,
        timestamp=datetime.now(UTC),
        event_type=EventType.OBSERVATION,
        description="Test event description",
        importance_score=Decimal("0.8"),
        detail_level=1,
        state_delta=StateDelta(),
        metadata=Metadata(),
    )


def create_sample_entity(project_id: UUID) -> Entity:
    """Create a sample entity for testing"""
    return Entity(
        id=uuid4(),
        project_id=project_id,
        entity_type=EntityType.CHARACTER,
        name="Test Entity",
        description="A test entity",
        properties=EntityProperties(),
    )


# Export helper functions
__all__ = [
    "create_sample_project",
    "create_sample_timeline",
    "create_sample_event",
    "create_sample_entity",
]
