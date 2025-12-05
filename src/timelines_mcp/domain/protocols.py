"""
Pure CRUD Storage Protocol - Minimal database operations only

Adapters implement ONLY these basic operations.
Complex queries are built in the repository layer using these primitives.
"""

from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID

from .models import (
    Entity,
    EntityType,
    Event,
    EventType,
    Project,
    Relationship,
    RelationType,
    SourceType,
    StateDelta,
    StateSnapshot,
    Timeline,
    TimelineStatus,
    WorldState,
)


@runtime_checkable
class StorageAdapter(Protocol):
    """
    PURE CRUD interface - database adapters implement ONLY these methods.
    
    NO complex queries. NO joins. NO business logic.
    Just: Create, Read, Update, Delete for each entity type.
    """

    async def initialize(self) -> None:
        """Initialize database schema/connections"""
        ...

    async def close(self) -> None:
        """Cleanup connections"""
        ...

    # ==========================================
    # PROJECT - Basic CRUD
    # ==========================================

    async def insert_project(self, project: Project) -> None:
        """Insert project record"""
        ...

    async def get_project_by_id(self, project_id: UUID) -> Project | None:
        """Get single project by ID"""
        ...

    async def get_projects_by_user(self, user_id: UUID) -> list[Project]:
        """Get all projects for user (simple WHERE clause)"""
        ...

    async def update_project(self, project: Project) -> None:
        """Update project record"""
        ...

    async def delete_project(self, project_id: UUID) -> None:
        """Delete project record"""
        ...

    # ==========================================
    # TIMELINE - Basic CRUD
    # ==========================================

    async def insert_timeline(self, timeline: Timeline) -> None:
        """Insert timeline record"""
        ...

    async def get_timeline_by_id(self, timeline_id: UUID) -> Timeline | None:
        """Get single timeline by ID"""
        ...

    async def get_timelines_by_project(self, project_id: UUID) -> list[Timeline]:
        """Get all timelines in project (simple WHERE)"""
        ...

    async def get_timelines_by_parent(self, parent_timeline_id: UUID) -> list[Timeline]:
        """Get child timelines (simple WHERE parent_id = ?)"""
        ...

    async def update_timeline(self, timeline: Timeline) -> None:
        """Update timeline record"""
        ...

    async def delete_timeline(self, timeline_id: UUID) -> None:
        """Delete timeline record"""
        ...

    # ==========================================
    # EVENT - Basic CRUD
    # ==========================================

    async def insert_event(self, event: Event) -> None:
        """Insert event record"""
        ...

    async def get_event_by_id(self, event_id: UUID) -> Event | None:
        """Get single event by ID"""
        ...

    async def get_events_by_timeline(self, timeline_id: UUID) -> list[Event]:
        """Get ALL events for timeline (simple WHERE)"""
        ...

    async def update_event(self, event: Event) -> None:
        """Update event record"""
        ...

    async def delete_event(self, event_id: UUID) -> None:
        """Delete event record"""
        ...

    # ==========================================
    # ENTITY - Basic CRUD
    # ==========================================

    async def insert_entity(self, entity: Entity) -> None:
        """Insert entity record"""
        ...

    async def get_entity_by_id(self, entity_id: UUID) -> Entity | None:
        """Get single entity by ID"""
        ...

    async def get_entities_by_project(self, project_id: UUID) -> list[Entity]:
        """Get all entities in project (simple WHERE)"""
        ...

    async def update_entity(self, entity: Entity) -> None:
        """Update entity record"""
        ...

    async def delete_entity(self, entity_id: UUID) -> None:
        """Delete entity record"""
        ...

    # ==========================================
    # RELATIONSHIP - Basic CRUD
    # ==========================================

    async def insert_relationship(self, relationship: Relationship) -> None:
        """Insert relationship record"""
        ...

    async def get_relationship_by_id(self, relationship_id: UUID) -> Relationship | None:
        """Get single relationship by ID"""
        ...

    async def get_relationships_by_source(
        self, source_id: UUID, source_type: SourceType
    ) -> list[Relationship]:
        """Get relationships where this is the source (simple WHERE)"""
        ...

    async def get_relationships_by_target(
        self, target_id: UUID, target_type: SourceType
    ) -> list[Relationship]:
        """Get relationships where this is the target (simple WHERE)"""
        ...

    async def update_relationship(self, relationship: Relationship) -> None:
        """Update relationship record"""
        ...

    async def delete_relationship(self, relationship_id: UUID) -> None:
        """Delete relationship record"""
        ...

    # ==========================================
    # STATE SNAPSHOT - Basic CRUD
    # ==========================================

    async def insert_snapshot(self, snapshot: StateSnapshot) -> None:
        """Insert snapshot record"""
        ...

    async def get_snapshot_by_id(self, snapshot_id: UUID) -> StateSnapshot | None:
        """Get single snapshot by ID"""
        ...

    async def get_snapshots_by_timeline(self, timeline_id: UUID) -> list[StateSnapshot]:
        """Get all snapshots for timeline (simple WHERE)"""
        ...

    async def delete_snapshot(self, snapshot_id: UUID) -> None:
        """Delete snapshot record"""
        ...

    # ==========================================
    # EVENT-ENTITY LINKS (junction table)
    # ==========================================

    async def insert_event_entity_link(
        self, event_id: UUID, entity_id: UUID, role: str
    ) -> None:
        """Insert event-entity link"""
        ...

    async def get_event_entity_links_by_event(
        self, event_id: UUID
    ) -> list[tuple[UUID, str]]:
        """Get (entity_id, role) pairs for event"""
        ...

    async def get_event_entity_links_by_entity(
        self, entity_id: UUID
    ) -> list[tuple[UUID, str]]:
        """Get (event_id, role) pairs for entity"""
        ...

    async def delete_event_entity_link(
        self, event_id: UUID, entity_id: UUID, role: str | None = None
    ) -> None:
        """Delete event-entity link(s)"""
        ...


@runtime_checkable
class VectorAdapter(Protocol):
    """
    PURE vector operations - NO embedding generation.
    
    Embeddings are always provided externally (from LLM calls).
    Adapter just stores and retrieves vectors.
    """

    async def initialize(self) -> None:
        """Setup vector collection/index"""
        ...

    async def close(self) -> None:
        """Cleanup connections"""
        ...

    async def insert_vector(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, str | int | float],
    ) -> None:
        """Store vector with metadata (NO embedding generation)"""
        ...

    async def search_vectors(
        self,
        query_embedding: list[float],
        limit: int = 10,
        metadata_filter: dict[str, str | int | float] | None = None,
    ) -> list[tuple[str, float]]:
        """Search by embedding - returns (id, score) tuples"""
        ...

    async def get_vector_by_id(self, id: str) -> tuple[list[float], dict] | None:
        """Get vector and metadata by ID"""
        ...

    async def delete_vector(self, id: str) -> None:
        """Delete vector by ID"""
        ...
