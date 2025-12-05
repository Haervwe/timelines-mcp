"""
Service Layer - High-level business operations

This layer orchestrates operations and can add:
- Validation
- Caching
- Transaction management
- Event publishing
- Complex business workflows

For now, it mostly delegates to TimelineRepository.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .domain.models import (
    Entity,
    EntityEventLink,
    EntityType,
    Event,
    EventType,
    Project,
    Relationship,
    RelationType,
    SourceType,
    Timeline,
    WorldState,
)
from .domain.repository import TimelineRepository


class TimelineService:
    """
    High-level business operations.
    Delegates to TimelineRepository for data access.
    """

    def __init__(self, repository: TimelineRepository):
        """Inject repository"""
        self._repo = repository

    async def initialize(self) -> None:
        """Initialize storage"""
        await self._repo.initialize()

    async def close(self) -> None:
        """Cleanup"""
        await self._repo.close()

    # === Project Operations ===

    async def create_project(
        self, user_id: UUID, name: str, description: str | None = None
    ) -> Project:
        """Create project"""
        return await self._repo.create_project(user_id, name, description)

    async def get_project(self, project_id: UUID) -> Project | None:
        """Get project"""
        return await self._repo.get_project(project_id)

    async def list_user_projects(self, user_id: UUID) -> list[Project]:
        """List user's projects"""
        return await self._repo.list_user_projects(user_id)

    # === Timeline Operations ===

    async def create_timeline(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None = None,
        parent_timeline_id: UUID | None = None,
    ) -> Timeline:
        """Create timeline"""
        return await self._repo.create_timeline(
            project_id, user_id, name, description, parent_timeline_id
        )

    async def get_timeline(self, timeline_id: UUID) -> Timeline | None:
        """Get timeline"""
        return await self._repo.get_timeline(timeline_id)

    async def list_timelines(
        self, project_id: UUID, parent_timeline_id: UUID | None = None
    ) -> list[Timeline]:
        """List timelines in project"""
        return await self._repo.list_timelines_in_project(project_id, parent_timeline_id)

    async def get_timeline_tree(self, root_id: UUID, max_depth: int = 10) -> list[Timeline]:
        """Get timeline hierarchy"""
        return await self._repo.get_timeline_tree(root_id, max_depth)

    async def fork_timeline(
        self, source_id: UUID, branch_name: str, from_timestamp: datetime
    ) -> Timeline:
        """Fork timeline at specific point"""
        return await self._repo.fork_timeline(source_id, branch_name, from_timestamp)

    # === Event Operations ===

    async def add_event(
        self,
        timeline_id: UUID,
        timestamp: datetime,
        event_type: EventType,
        description: str,
        importance_score: Decimal = Decimal("0.5"),
        embedding: list[float] | None = None,
    ) -> Event:
        """Add event to timeline, optionally index for search"""
        event = await self._repo.add_event(
            timeline_id, timestamp, event_type, description, importance_score=importance_score
        )

        # Index for semantic search if embedding provided
        if embedding:
            await self._repo.index_event(event.id, timeline_id, embedding)

        return event

    async def get_event(self, event_id: UUID) -> Event | None:
        """Get event"""
        return await self._repo.get_event(event_id)

    async def query_events(
        self,
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        event_types: list[EventType] | None = None,
        min_importance: Decimal = Decimal("0.0"),
        limit: int | None = None,
    ) -> list[Event]:
        """Query events with filters"""
        return await self._repo.query_events(
            timeline_id, start, end, event_types, min_importance, limit=limit
        )

    async def get_recent_events(
        self, timeline_id: UUID, before: datetime, limit: int = 50
    ) -> list[Event]:
        """Get recent events before timestamp"""
        return await self._repo.get_events_before(timeline_id, before, limit)

    # === State Reconstruction ===

    async def reconstruct_state(
        self, timeline_id: UUID, timestamp: datetime, entity_ids: list[UUID] | None = None
    ) -> WorldState:
        """Reconstruct world state at specific time"""
        return await self._repo.reconstruct_state_at(timeline_id, timestamp, entity_ids)

    async def save_checkpoint(self, timeline_id: UUID, timestamp: datetime) -> None:
        """Create state checkpoint for faster queries"""
        state = await self._repo.reconstruct_state_at(timeline_id, timestamp)
        await self._repo.save_state_snapshot(timeline_id, timestamp, state)

    # === Entity Operations ===

    async def create_entity(
        self,
        project_id: UUID,
        entity_type: EntityType,
        name: str,
        description: str,
        embedding: list[float] | None = None,
    ) -> Entity:
        """Create entity, optionally index for search"""
        entity = await self._repo.create_entity(project_id, entity_type, name, description)

        # Index if embedding provided
        if embedding:
            # Vector indexing would go here
            pass

        return entity

    async def get_entity(self, entity_id: UUID) -> Entity | None:
        """Get entity"""
        return await self._repo.get_entity(entity_id)

    async def list_entities(
        self, project_id: UUID, entity_type: EntityType | None = None
    ) -> list[Entity]:
        """List entities in project"""
        return await self._repo.list_entities(project_id, entity_type)

    # === Event-Entity Relationships ===

    async def link_event_entity(self, event_id: UUID, entity_id: UUID, role: str) -> None:
        """Link entity to event with role"""
        await self._repo.link_event_entity(event_id, entity_id, role)

    async def get_event_entities(self, event_id: UUID) -> list[EntityEventLink]:
        """Get entities involved in event"""
        return await self._repo.get_event_entities(event_id)

    async def get_entity_events(
        self,
        entity_id: UUID,
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Event]:
        """Get events involving entity"""
        return await self._repo.get_entity_events(entity_id, timeline_id, start, end)

    async def get_events_at_location(
        self,
        location_id: UUID,
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Event]:
        """Get events at location"""
        return await self._repo.get_events_at_location(location_id, timeline_id, start, end)

    async def get_character_interactions(
        self,
        character_ids: list[UUID],
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Event]:
        """Find events where characters interacted"""
        return await self._repo.get_events_with_entities(
            character_ids, timeline_id, match_all=True, start=start, end=end
        )

    # === Causality ===

    async def establish_causality(
        self, cause_event_id: UUID, effect_event_id: UUID, strength: Decimal = Decimal("1.0")
    ) -> Relationship:
        """Create causal relationship"""
        return await self._repo.create_relationship(
            cause_event_id,
            SourceType.EVENT,
            effect_event_id,
            SourceType.EVENT,
            RelationType.CAUSAL,
            strength,
        )

    async def trace_causal_chain(
        self, event_id: UUID, direction: str = "forward", max_depth: int = 5
    ) -> list:
        """Trace causal chains"""
        forward = direction.lower() in ("forward", "effects", "consequences")
        return await self._repo.trace_causality(event_id, max_depth, forward)

    # === Semantic Search ===

    async def search_similar_events(
        self,
        query_embedding: list[float],
        timeline_ids: list[UUID] | None = None,
        limit: int = 10,
    ) -> list[tuple[Event, float]]:
        """
        Semantic search for events.
        Requires embedding to be provided (from external LLM call).
        """
        results = await self._repo.search_similar_events(query_embedding, timeline_ids, limit)

        # Hydrate events
        events_with_scores = []
        for event_id, score in results:
            event = await self._repo.get_event(event_id)
            if event:
                events_with_scores.append((event, score))

        return events_with_scores


# === Context Manager ===


class TimelineContext:
    """Context manager for service lifecycle"""

    def __init__(self, service: TimelineService):
        self.service = service

    async def __aenter__(self) -> TimelineService:
        await self.service.initialize()
        return self.service

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.service.close()
