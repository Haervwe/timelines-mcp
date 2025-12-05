"""
Repository Layer - Complex queries built from basic CRUD operations

This layer uses ONLY the StorageAdapter protocol (basic CRUD).
All filtering, sorting, joining logic happens HERE in Python.
Database adapters stay thin - just insert/get/update/delete.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from .models import (
    CausalPath,
    Entity,
    EntityEventLink,
    EntityProperties,
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
    TimelineSummary,
    WorldState,
)
from .protocols import StorageAdapter, VectorAdapter


class TimelineRepository:
    """
    Implements complex operations using ONLY basic CRUD from StorageAdapter.
    
    NO database-specific code. ALL logic in Python.
    Works identically with SQLite, Postgres, or any adapter.
    """

    def __init__(self, storage: StorageAdapter, vector: VectorAdapter | None = None):
        """Inject CRUD adapter"""
        self._storage = storage
        self._vector = vector

    async def initialize(self) -> None:
        """Initialize storage"""
        await self._storage.initialize()
        if self._vector:
            await self._vector.initialize()

    async def close(self) -> None:
        """Cleanup"""
        await self._storage.close()
        if self._vector:
            await self._vector.close()

    # ==========================================
    # PROJECT - Composed Operations
    # ==========================================

    async def create_project(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Project:
        """Create project - uses basic CRUD"""
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
        )
        await self._storage.insert_project(project)
        return project

    async def get_project(self, project_id: UUID) -> Project | None:
        """Get project - direct CRUD call"""
        return await self._storage.get_project_by_id(project_id)

    async def list_user_projects(self, user_id: UUID) -> list[Project]:
        """List user's projects - direct CRUD call"""
        return await self._storage.get_projects_by_user(user_id)

    # ==========================================
    # TIMELINE - Composed Operations
    # ==========================================

    async def create_timeline(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None = None,
        parent_timeline_id: UUID | None = None,
        status: TimelineStatus = TimelineStatus.CANONICAL,
    ) -> Timeline:
        """Create timeline - uses basic CRUD"""
        timeline = Timeline(
            project_id=project_id,
            user_id=user_id,
            name=name,
            description=description,
            parent_timeline_id=parent_timeline_id,
            status=status,
        )
        await self._storage.insert_timeline(timeline)
        return timeline

    async def get_timeline(self, timeline_id: UUID) -> Timeline | None:
        """Get timeline - direct CRUD"""
        return await self._storage.get_timeline_by_id(timeline_id)

    async def list_timelines_in_project(
        self, project_id: UUID, parent_timeline_id: UUID | None = None
    ) -> list[Timeline]:
        """
        List timelines - filtering logic in Python, NOT in database.
        Uses basic get_timelines_by_project, filters in memory.
        """
        timelines = await self._storage.get_timelines_by_project(project_id)

        # Filter by parent in Python
        if parent_timeline_id is not None:
            timelines = [t for t in timelines if t.parent_timeline_id == parent_timeline_id]

        return timelines

    async def get_timeline_children(self, parent_id: UUID) -> list[Timeline]:
        """Get child timelines - direct CRUD call"""
        return await self._storage.get_timelines_by_parent(parent_id)

    async def get_timeline_tree(
        self, root_timeline_id: UUID, max_depth: int = 10
    ) -> list[Timeline]:
        """
        Build timeline hierarchy - uses ONLY basic CRUD.
        Recursion logic in Python, NOT database.
        """
        result = []

        async def traverse(timeline_id: UUID, depth: int):
            if depth > max_depth:
                return
            timeline = await self._storage.get_timeline_by_id(timeline_id)
            if timeline:
                result.append(timeline)
                children = await self._storage.get_timelines_by_parent(timeline_id)
                for child in children:
                    await traverse(child.id, depth + 1)

        await traverse(root_timeline_id, 0)
        return result

    async def fork_timeline(
        self,
        source_timeline_id: UUID,
        branch_name: str,
        from_timestamp: datetime,
        status: TimelineStatus = TimelineStatus.HYPOTHETICAL,
    ) -> Timeline:
        """
        Fork timeline - logic in Python using basic CRUD.
        No special database support needed.
        """
        source = await self._storage.get_timeline_by_id(source_timeline_id)
        if not source:
            raise ValueError(f"Timeline {source_timeline_id} not found")

        # Create new timeline
        forked = Timeline(
            project_id=source.project_id,
            user_id=source.user_id,
            name=branch_name,
            parent_timeline_id=source_timeline_id,
            status=status,
        )
        await self._storage.insert_timeline(forked)

        # Copy events up to fork point - uses basic CRUD
        events = await self._storage.get_events_by_timeline(source_timeline_id)
        events_to_copy = [e for e in events if e.timestamp <= from_timestamp]

        for event in events_to_copy:
            new_event = Event(
                timeline_id=forked.id,
                timestamp=event.timestamp,
                end_timestamp=event.end_timestamp,
                event_type=event.event_type,
                description=event.description,
                importance_score=event.importance_score,
                detail_level=event.detail_level,
                state_delta=event.state_delta,
            )
            await self._storage.insert_event(new_event)

        return forked

    # ==========================================
    # EVENT - Composed Operations
    # ==========================================

    async def add_event(
        self,
        timeline_id: UUID,
        timestamp: datetime,
        event_type: EventType,
        description: str,
        state_delta: StateDelta | None = None,
        importance_score: Decimal = Decimal("0.5"),
        end_timestamp: datetime | None = None,
    ) -> Event:
        """Add event - uses basic CRUD"""
        event = Event(
            timeline_id=timeline_id,
            timestamp=timestamp,
            event_type=event_type,
            description=description,
            state_delta=state_delta or StateDelta(),
            importance_score=importance_score,
            end_timestamp=end_timestamp,
        )
        await self._storage.insert_event(event)
        return event

    async def get_event(self, event_id: UUID) -> Event | None:
        """Get event - direct CRUD"""
        return await self._storage.get_event_by_id(event_id)

    async def query_events(
        self,
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        event_types: list[EventType] | None = None,
        min_importance: Decimal = Decimal("0.0"),
        detail_level: int | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        """
        Query events - filtering/sorting in Python, NOT database.
        Uses basic get_events_by_timeline, processes in memory.
        """
        # Get all events for timeline
        events = await self._storage.get_events_by_timeline(timeline_id)

        # Apply filters in Python
        if start:
            events = [e for e in events if e.timestamp >= start]
        if end:
            events = [e for e in events if e.timestamp <= end]
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        if min_importance:
            events = [e for e in events if e.importance_score >= min_importance]
        if detail_level is not None:
            events = [e for e in events if e.detail_level == detail_level]

        # Sort in Python
        events = sorted(events, key=lambda e: e.timestamp)

        # Limit in Python
        if limit:
            events = events[:limit]

        return events

    async def get_events_before(
        self, timeline_id: UUID, timestamp: datetime, limit: int = 100
    ) -> list[Event]:
        """Get recent events - filtering in Python"""
        events = await self._storage.get_events_by_timeline(timeline_id)
        events = [e for e in events if e.timestamp < timestamp]
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_events_after(
        self, timeline_id: UUID, timestamp: datetime, limit: int = 100
    ) -> list[Event]:
        """Get future events - filtering in Python"""
        events = await self._storage.get_events_by_timeline(timeline_id)
        events = [e for e in events if e.timestamp > timestamp]
        events = sorted(events, key=lambda e: e.timestamp)
        return events[:limit]

    # ==========================================
    # STATE RECONSTRUCTION - Pure Logic
    # ==========================================

    async def reconstruct_state_at(
        self,
        timeline_id: UUID,
        timestamp: datetime,
        entity_ids: list[UUID] | None = None,
    ) -> WorldState:
        """
        Reconstruct state - ALL logic in Python.
        Uses basic CRUD to get snapshots and events.
        """
        # Find nearest snapshot using basic CRUD
        snapshots = await self._storage.get_snapshots_by_timeline(timeline_id)
        snapshots = [s for s in snapshots if s.timestamp <= timestamp]

        if snapshots:
            nearest = max(snapshots, key=lambda s: s.timestamp)
            state = nearest.state
            start_time = nearest.timestamp
        else:
            state = WorldState()
            start_time = datetime.min.replace(tzinfo=UTC)

        # Get events to replay
        events = await self.query_events(
            timeline_id=timeline_id, start=start_time, end=timestamp
        )

        # Apply deltas in Python
        for event in events:
            if event.state_delta:
                state.global_properties.update(event.state_delta.global_changes)
                for entity_id, changes in event.state_delta.entity_changes.items():
                    if entity_ids is None or entity_id in entity_ids:
                        if entity_id not in state.entity_states:
                            state.entity_states[entity_id] = {}
                        state.entity_states[entity_id].update(changes)

        return state

    async def save_state_snapshot(
        self, timeline_id: UUID, timestamp: datetime, state: WorldState
    ) -> StateSnapshot:
        """Save snapshot - uses basic CRUD"""
        snapshot = StateSnapshot(timeline_id=timeline_id, timestamp=timestamp, state=state)
        await self._storage.insert_snapshot(snapshot)
        return snapshot

    # ==========================================
    # ENTITY - Composed Operations
    # ==========================================

    async def create_entity(
        self,
        project_id: UUID,
        entity_type: EntityType,
        name: str,
        description: str,
        properties: EntityProperties | None = None,
    ) -> Entity:
        """Create entity - uses basic CRUD"""
        entity = Entity(
            project_id=project_id,
            entity_type=entity_type,
            name=name,
            description=description,
            properties=properties or EntityProperties(),
        )
        await self._storage.insert_entity(entity)
        return entity

    async def get_entity(self, entity_id: UUID) -> Entity | None:
        """Get entity - direct CRUD"""
        return await self._storage.get_entity_by_id(entity_id)

    async def list_entities(
        self, project_id: UUID, entity_type: EntityType | None = None
    ) -> list[Entity]:
        """List entities - filtering in Python"""
        entities = await self._storage.get_entities_by_project(project_id)
        if entity_type:
            entities = [e for e in entities if e.entity_type == entity_type]
        return entities

    # ==========================================
    # EVENT-ENTITY RELATIONSHIPS
    # ==========================================

    async def link_event_entity(
        self, event_id: UUID, entity_id: UUID, role: str
    ) -> None:
        """Link event to entity - basic CRUD"""
        await self._storage.insert_event_entity_link(event_id, entity_id, role)

    async def get_event_entities(self, event_id: UUID) -> list[EntityEventLink]:
        """Get entities in event - uses basic CRUD"""
        links = await self._storage.get_event_entity_links_by_event(event_id)
        result = []
        for entity_id, role in links:
            entity = await self._storage.get_entity_by_id(entity_id)
            if entity:
                result.append(EntityEventLink(entity=entity, role=role))
        return result

    async def get_entity_events(
        self,
        entity_id: UUID,
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        role: str | None = None,
    ) -> list[Event]:
        """
        Get events involving entity - logic in Python.
        Uses basic CRUD + filtering.
        """
        # Get event IDs for entity
        links = await self._storage.get_event_entity_links_by_entity(entity_id)

        if role:
            links = [(eid, r) for eid, r in links if r == role]

        event_ids = {eid for eid, _ in links}

        # Get events and filter
        events = await self._storage.get_events_by_timeline(timeline_id)
        events = [e for e in events if e.id in event_ids]

        if start:
            events = [e for e in events if e.timestamp >= start]
        if end:
            events = [e for e in events if e.timestamp <= end]

        return sorted(events, key=lambda e: e.timestamp)

    async def get_events_at_location(
        self,
        location_id: UUID,
        timeline_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Event]:
        """Get events at location - uses basic operations"""
        return await self.get_entity_events(
            location_id, timeline_id, start, end, role="location"
        )

    async def get_events_with_entities(
        self,
        entity_ids: list[UUID],
        timeline_id: UUID,
        match_all: bool = False,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Event]:
        """
        Find events with multiple entities - logic in Python.
        Uses basic CRUD + set operations.
        """
        if match_all:
            # All entities must be present - intersection
            event_sets = []
            for entity_id in entity_ids:
                events = await self.get_entity_events(entity_id, timeline_id, start, end)
                event_sets.append({e.id for e in events})
            common_ids = set.intersection(*event_sets) if event_sets else set()
            events = await self._storage.get_events_by_timeline(timeline_id)
            result = [e for e in events if e.id in common_ids]
        else:
            # Any entity - union
            all_event_ids = set()
            for entity_id in entity_ids:
                events = await self.get_entity_events(entity_id, timeline_id, start, end)
                all_event_ids.update(e.id for e in events)
            events = await self._storage.get_events_by_timeline(timeline_id)
            result = [e for e in events if e.id in all_event_ids]

        return sorted(result, key=lambda e: e.timestamp)

    # ==========================================
    # RELATIONSHIPS & CAUSALITY
    # ==========================================

    async def create_relationship(
        self,
        source_id: UUID,
        source_type: SourceType,
        target_id: UUID,
        target_type: SourceType,
        relation_type: RelationType,
        strength: Decimal = Decimal("1.0"),
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> Relationship:
        """Create relationship - basic CRUD"""
        rel = Relationship(
            source_id=source_id,
            source_type=source_type,
            target_id=target_id,
            target_type=target_type,
            relation_type=relation_type,
            strength=strength,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        await self._storage.insert_relationship(rel)
        return rel

    async def get_relationships(
        self,
        entity_id: UUID,
        relation_type: RelationType | None = None,
        at_time: datetime | None = None,
        as_source: bool = True,
        as_target: bool = True,
    ) -> list[Relationship]:
        """
        Get relationships - uses basic CRUD + filtering in Python.
        """
        relationships = []

        if as_source:
            rels = await self._storage.get_relationships_by_source(
                entity_id, SourceType.EVENT
            )
            relationships.extend(rels)

        if as_target:
            rels = await self._storage.get_relationships_by_target(
                entity_id, SourceType.EVENT
            )
            relationships.extend(rels)

        # Filter in Python
        if relation_type:
            relationships = [r for r in relationships if r.relation_type == relation_type]

        if at_time:
            relationships = [
                r
                for r in relationships
                if (r.valid_from is None or r.valid_from <= at_time)
                and (r.valid_until is None or r.valid_until >= at_time)
            ]

        return relationships

    async def trace_causality(
        self, event_id: UUID, max_depth: int = 5, forward: bool = True
    ) -> list[CausalPath]:
        """
        Trace causal chains - BFS algorithm in Python.
        Uses ONLY basic CRUD for relationships.
        """
        visited = set()
        paths = []

        async def bfs(current_id: UUID, depth: int, path: list[Event]):
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)

            event = await self._storage.get_event_by_id(current_id)
            if not event:
                return

            current_path = path + [event]

            # Get relationships
            if forward:
                rels = await self._storage.get_relationships_by_source(
                    current_id, SourceType.EVENT
                )
            else:
                rels = await self._storage.get_relationships_by_target(
                    current_id, SourceType.EVENT
                )

            # Filter for causal relationships
            rels = [r for r in rels if r.relation_type == RelationType.CAUSAL]

            if not rels:
                # End of chain
                paths.append(CausalPath(events=current_path))
                return

            # Continue traversal
            for rel in rels:
                next_id = rel.target_id if forward else rel.source_id
                await bfs(next_id, depth + 1, current_path)

        await bfs(event_id, 0, [])
        return paths

    # ==========================================
    # COMPRESSION & SUMMARIZATION
    # ==========================================

    async def compress_events(
        self, timeline_id: UUID, before: datetime, min_importance: Decimal
    ) -> int:
        """
        Compress events - logic in Python using basic CRUD.
        """
        events = await self._storage.get_events_by_timeline(timeline_id)
        count = 0

        for event in events:
            if (
                event.timestamp < before
                and event.importance_score < min_importance
                and event.detail_level > 0
            ):
                event.detail_level -= 1
                await self._storage.update_event(event)
                count += 1

        return count

    async def get_timeline_summary(
        self,
        timeline_id: UUID,
        at_time: datetime,
        recency_window: int = 10,
        importance_threshold: Decimal = Decimal("0.7"),
    ) -> TimelineSummary:
        """Build summary - all logic in Python"""
        events = await self.query_events(timeline_id=timeline_id, end=at_time)

        if not events:
            return TimelineSummary()

        # Recent events (limited to window)
        _ = sorted(events, key=lambda e: e.timestamp, reverse=True)[:recency_window]

        # Important events (above threshold)
        _ = [e for e in events if e.importance_score >= importance_threshold]

        return TimelineSummary(
            recent_events=[],  # Simplified
            important_events=[],  # Simplified
            event_count=len(events),
            first_event=min(e.timestamp for e in events) if events else None,
            last_event=max(e.timestamp for e in events) if events else None,
        )

    # ==========================================
    # VECTOR OPERATIONS (if enabled)
    # ==========================================

    async def index_event(
        self, event_id: UUID, timeline_id: UUID, embedding: list[float]
    ) -> None:
        """Index event - embedding provided externally"""
        if not self._vector:
            return
        await self._vector.insert_vector(
            id=str(event_id),
            embedding=embedding,
            metadata={"timeline_id": str(timeline_id), "type": "event"},
        )

    async def search_similar_events(
        self, query_embedding: list[float], timeline_ids: list[UUID] | None = None, limit: int = 10
    ) -> list[tuple[UUID, float]]:
        """Semantic search - embedding provided externally"""
        if not self._vector:
            return []

        metadata_filter = {}
        if timeline_ids:
            # Note: simplified - real implementation might need multiple queries
            metadata_filter["type"] = "event"

        results = await self._vector.search_vectors(query_embedding, limit, metadata_filter)
        return [(UUID(id_str), score) for id_str, score in results]
